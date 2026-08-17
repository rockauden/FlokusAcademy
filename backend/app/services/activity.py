"""Per-day completion counts, and the streak derived from them.

The streak that already existed in /analytics/summary counted consecutive
*calendar* days containing any completion. That is close to meaningless for
this school: the week runs Monday to Thursday, so Friday always broke it and
the number could never exceed four. It also began counting at today, so it read
zero every morning before any work was done -- telling a child who had finished
ten school days in a row that his streak was nothing.

The definition here counts consecutive *school days that had work*, which is
the thing a child would actually recognise as "I haven't missed a day".
"""
from collections import defaultdict
from datetime import date
from typing import Iterable, Sequence

from app.models import Assignment


def day_for(assignment: Assignment) -> date | None:
    """The day an assignment belongs to: finished date if done, else scheduled."""
    if assignment.is_completed:
        return assignment.actual_completion_date
    return assignment.scheduled_date


def counts_by_day(assignments: Iterable[Assignment]) -> dict[date, dict[str, int]]:
    """{date: {'total': n, 'completed': m}} for every day that has any work."""
    buckets: dict[date, dict[str, int]] = defaultdict(lambda: {"total": 0, "completed": 0})

    for assignment in assignments:
        day = day_for(assignment)
        if day is None:
            # Undated and unfinished: real, but not part of any day yet.
            continue
        buckets[day]["total"] += 1
        if assignment.is_completed:
            buckets[day]["completed"] += 1

    return dict(buckets)


def compute_streak(counts: dict[date, dict[str, int]], today: date) -> int:
    """Consecutive fully-finished school days, most recent first.

    Two deliberate choices:

    * Days with no work are skipped entirely rather than breaking the run. A
      weekend, a holiday or a sick day is not a missed day, and a streak that
      collapses every Friday teaches a child to stop looking at it.

    * An unfinished *today* is skipped rather than counted as a break. The day
      is not over. Counting it would mean the streak reads zero every morning
      and only reappears once the last task is done, which is backwards --
      the streak should be what he is protecting, not something he re-earns
      from scratch daily.
    """
    days_with_work = sorted((d for d, c in counts.items() if c["total"] > 0 and d <= today), reverse=True)

    streak = 0
    for index, day in enumerate(days_with_work):
        finished = counts[day]["completed"] >= counts[day]["total"]
        if finished:
            streak += 1
            continue
        # The only unfinished day that does not end the run is today itself,
        # and only when it is the first one examined.
        if index == 0 and day == today:
            continue
        break

    return streak


def school_week(today: date, length: int = 5) -> list[date]:
    """The Monday-to-Friday week containing `today`.

    Five days, not four, even though get_school_days still treats Friday as a
    non-school day and will not place work there on its own. A week with
    Friday missing does not read as a week -- the row just looks truncated, and
    the reader is left working out why. Friday shows up as a real day that
    usually happens to be free, which is the truth, and work put there by hand
    still appears.

    On a Saturday or Sunday this returns the week just finished rather than
    jumping forward, so the strip keeps showing the week actually worked until
    the next one starts.
    """
    monday = today.fromordinal(today.toordinal() - today.weekday())
    return [monday.fromordinal(monday.toordinal() + offset) for offset in range(length)]


def summarise(
    assignments: Sequence[Assignment], week: Sequence[date], today: date
) -> tuple[list[dict], int]:
    """Week rows for the strip, plus the streak over the whole supplied range."""
    counts = counts_by_day(assignments)
    days = [
        {
            "date": day,
            "total": counts.get(day, {}).get("total", 0),
            "completed": counts.get(day, {}).get("completed", 0),
        }
        for day in week
    ]
    return days, compute_streak(counts, today)
