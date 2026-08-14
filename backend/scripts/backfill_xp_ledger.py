"""One-off backfill: reconstruct the XP ledger from existing history.

Before the ledger existed, balance was derived on the fly from completed tasks
and purchases. Those rows have no ledger entries, so switching /balance over to
SUM(delta) without this would show every student a balance of 0.

    cd backend
    python -m scripts.backfill_xp_ledger            # dry run, prints what it would write
    python -m scripts.backfill_xp_ledger --commit   # actually write

Idempotent: a task or purchase that already has a ledger row is skipped, so
re-running never double-credits.
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.database import async_session_maker, engine, set_session_tenant
from app.models import Assignment, CreatorProject, Lesson, Purchase, User, XPLedger


async def resolve_student(session, tenant_id: int, explicit_id: int | None) -> User:
    if explicit_id is not None:
        user = (await session.execute(select(User).where(User.id == explicit_id))).scalars().first()
        if not user:
            raise SystemExit(f"No user with id {explicit_id}")
        return user

    students = (
        await session.execute(
            select(User).where(User.tenant_id == tenant_id, User.role == "student")
        )
    ).scalars().all()
    if len(students) != 1:
        raise SystemExit(
            f"Found {len(students)} students in tenant {tenant_id}; "
            f"pass --student-id to say who this history belongs to."
        )
    return students[0]


async def backfill(tenant_id: int, explicit_student_id: int | None, commit: bool) -> int:
    async with async_session_maker() as session:
        # Required under Postgres RLS: every read and write below is scoped.
        await set_session_tenant(session, tenant_id)
        student = await resolve_student(session, tenant_id, explicit_student_id)

        existing = {
            (source_type, source_id)
            for source_type, source_id in (
                await session.execute(
                    select(XPLedger.source_type, XPLedger.source_id).where(
                        XPLedger.tenant_id == tenant_id
                    )
                )
            ).all()
        }

        planned: list[tuple[str, int, int, str]] = []

        rows = (
            await session.execute(
                select(Assignment, Lesson)
                .join(Lesson, Assignment.lesson_id == Lesson.id)
                .where(Assignment.tenant_id == tenant_id, Assignment.is_completed == True)
            )
        ).all()
        for a, lesson in rows:
            if ("assignment", a.id) in existing:
                continue
            planned.append(("assignment", a.id, lesson.xp_reward * (2 if lesson.is_boss_fight else 1), f"Completed: {lesson.title}"))

        projects = (
            await session.execute(
                select(CreatorProject).where(
                    CreatorProject.tenant_id == tenant_id,
                    CreatorProject.status == "Completed",
                )
            )
        ).scalars().all()
        for pr in projects:
            if ("creator_project", pr.id) in existing:
                continue
            planned.append(("creator_project", pr.id, pr.xp_reward, f"Completed project: {pr.title}"))

        purchases = (
            await session.execute(select(Purchase).where(Purchase.tenant_id == tenant_id))
        ).scalars().all()
        for p in purchases:
            if ("purchase", p.id) in existing:
                continue
            planned.append(("purchase", p.id, -p.xp_cost, f"Purchased: {p.reward_name}"))

        earned = sum(d for _, _, d, _ in planned if d > 0)
        spent = -sum(d for _, _, d, _ in planned if d < 0)
        print(f"Tenant {tenant_id}, student '{student.username}' (id={student.id})")
        print(f"  {len(planned)} entries to write: +{earned} earned, -{spent} spent, net {earned - spent}")
        print(f"  ({len(existing)} ledger rows already present, skipped)")

        if not commit:
            print("\nDry run — nothing written. Re-run with --commit to apply.")
            return 0

        for source_type, source_id, delta, reason in planned:
            session.add(
                XPLedger(
                    tenant_id=tenant_id,
                    student_id=student.id,
                    delta=delta,
                    reason=reason,
                    source_type=source_type,
                    source_id=source_id,
                )
            )
        await session.commit()
        print(f"\nWrote {len(planned)} ledger entries.")
        return 0


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", type=int, default=1)
    parser.add_argument("--student-id", type=int, default=None)
    parser.add_argument("--commit", action="store_true", help="write (default is a dry run)")
    args = parser.parse_args()
    try:
        return await backfill(args.tenant_id, args.student_id, args.commit)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
