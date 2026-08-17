"""Give a scheduled_date to assignments that have none, so students can see them.

Why this is needed: the student's day selects incomplete work with
`scheduled_date <= today`, and in SQL `NULL <= today` evaluates to NULL rather
than true. An assignment with no date is therefore excluded from that list
permanently, while every admin view -- which applies no date filter -- still
shows it. Tasks created through Quick Add before the date defaulted to today
are all in this state: visible to the teacher, invisible to the student.

Quick Add now defaults to today, so this is a one-shot repair of the backlog,
not something to run regularly.

Dates are allocated with the same `get_school_days` helper the rolling
scheduler uses, reading the same `app_config.school_days` — so non-core days
(ordinarily Fri/Sat/Sun) and anything marked as a holiday or sick day in
school_calendar are skipped. Work is spread `--per-day` at a time rather than
dumped on a single date, and each student is filled independently.

Backfilled dates are left unlocked. They are the scheduler's guesses, not a
teacher's placement, so a later recalculation is free to improve on them.

Usage (from backend/):
    python -m scripts.backfill_assignment_dates --dry-run
    python -m scripts.backfill_assignment_dates --start 2026-08-19 --per-day 4

Interactive by default -- type the database name to confirm. For a console with
no real stdin, set BACKFILL_CONFIRM=<database name> and pass --yes.

Only incomplete assignments with no date are touched. Completed work is left
alone: it is matched on actual_completion_date, so a date would change nothing.
"""
import argparse
import asyncio
import os
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session_maker, engine
from app.models import Assignment, SchoolCalendar, User
from app.repository import AppConfigRepository
from app.services.rolling_scheduler import get_school_days, parse_school_days


def _database_name() -> str:
    parts = urlsplit(engine.url.render_as_string(hide_password=False))
    return (parts.path or "").lstrip("/") or "(unknown)"


def _parse_start(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise SystemExit(f"--start must be YYYY-MM-DD, got {value!r}")


async def _non_school_dates(session, tenant_id: int) -> set[date]:
    """Holidays and sick days for this tenant, matching the schedule router."""
    result = await session.execute(
        select(SchoolCalendar.calendar_date).where(
            SchoolCalendar.tenant_id == tenant_id,
            SchoolCalendar.day_type != "school_day",
        )
    )
    return {row[0] for row in result}


async def _plan(session, start: date, per_day: int) -> dict[tuple[int, int], list[tuple[Assignment, date]]]:
    """Work out which date each undated assignment should get.

    Returns {(tenant_id, student_id): [(assignment, new_date), ...]}.
    """
    result = await session.execute(
        select(Assignment)
        .options(selectinload(Assignment.lesson))
        .where(
            Assignment.scheduled_date.is_(None),
            Assignment.is_completed.is_(False),
        )
    )
    undated = list(result.scalars())

    grouped: dict[tuple[int, int], list[Assignment]] = defaultdict(list)
    for assignment in undated:
        grouped[(assignment.tenant_id, assignment.student_id)].append(assignment)

    plan: dict[tuple[int, int], list[tuple[Assignment, date]]] = {}
    for key, assignments in grouped.items():
        tenant_id, _student_id = key
        # Sequence order is the teacher's intended teaching order; id breaks
        # ties so two runs over the same data produce the same result.
        assignments.sort(key=lambda a: ((a.lesson.sequence_order if a.lesson else 0), a.id))

        skip = await _non_school_dates(session, tenant_id)
        # The school week is configuration, so read it rather than relying on
        # the Mon-Thu default: this script's whole claim is that it places work
        # exactly where the rolling scheduler would.
        school_weekdays = parse_school_days(
            await AppConfigRepository.get(session, tenant_id=tenant_id, key='school_days')
        )
        days_needed = -(-len(assignments) // per_day)  # ceiling division
        school_days = get_school_days(start, days_needed, skip, school_weekdays)

        plan[key] = [
            (assignment, school_days[index // per_day])
            for index, assignment in enumerate(assignments)
        ]

    return plan


async def _student_names(session) -> dict[int, str]:
    result = await session.execute(select(User.id, User.display_name, User.username))
    return {row[0]: (row[1] or row[2]) for row in result}


def _confirm(db_name: str, assume_yes: bool) -> bool:
    if assume_yes:
        if os.environ.get("BACKFILL_CONFIRM") == db_name:
            return True
        print(
            "--yes was passed but BACKFILL_CONFIRM does not match the target "
            "database name. Refusing to proceed non-interactively.",
            file=sys.stderr,
        )
        return False

    if not sys.stdin.isatty():
        print(
            "stdin is not a terminal and --yes was not passed with a matching "
            "BACKFILL_CONFIRM. Refusing to proceed.",
            file=sys.stderr,
        )
        return False

    print(f"Type the database name ({db_name}) to confirm, or anything else to abort:")
    return input("> ").strip() == db_name


async def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--start", help="first school day to place work on (YYYY-MM-DD, default today)")
    parser.add_argument(
        "--per-day", type=int, default=4,
        help="how many assignments to place on each school day (default 4)",
    )
    parser.add_argument("--dry-run", action="store_true", help="show the plan and change nothing")
    parser.add_argument(
        "--yes", action="store_true",
        help="skip the interactive prompt (requires BACKFILL_CONFIRM=<db name>)",
    )
    args = parser.parse_args()

    if args.per_day < 1:
        raise SystemExit("--per-day must be at least 1")

    start = _parse_start(args.start)
    db_name = _database_name()

    async with async_session_maker() as session:
        plan = await _plan(session, start, args.per_day)
        names = await _student_names(session)

        total = sum(len(rows) for rows in plan.values())
        if total == 0:
            print("No undated incomplete assignments found -- nothing to do.")
            return 0

        print("=" * 70)
        print(f"Database : {db_name}")
        print(f"Start    : {start} ({start.strftime('%A')})")
        print(f"Per day  : {args.per_day}")
        print(f"Affected : {total} assignment(s)")
        print("=" * 70)

        for (tenant_id, student_id), rows in sorted(plan.items()):
            who = names.get(student_id, f"user {student_id}")
            # ASCII only: a Windows console defaults to cp1252 and mangles
            # anything outside it, which is a poor look for a script whose
            # whole job is to show you what it is about to change.
            print(f"\ntenant {tenant_id} / {who} - {len(rows)} assignment(s)")
            by_date: dict[date, list[str]] = defaultdict(list)
            for assignment, new_date in rows:
                title = assignment.lesson.title if assignment.lesson else f"assignment {assignment.id}"
                by_date[new_date].append(title)
            for day in sorted(by_date):
                print(f"  {day} ({day.strftime('%a')}):")
                for title in by_date[day]:
                    print(f"      - {title}")

        if args.dry_run:
            print("\n--dry-run: nothing was written.")
            return 0

        print()
        if not _confirm(db_name, args.yes):
            print("Aborted; nothing was written.")
            return 1

        for rows in plan.values():
            for assignment, new_date in rows:
                assignment.scheduled_date = new_date
        await session.commit()

    print(f"\nDone. {total} assignment(s) now have a scheduled date.")
    print("They will appear in the student's day on or after the date shown above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
