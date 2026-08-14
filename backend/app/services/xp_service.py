"""The one place XP is awarded, spent, and totalled.

Before this existed the economy was computed in two places that disagreed with
each other (the purchase gate excluded creator-project XP, the analytics
summary included it). Everything that moves XP should go through award_xp, and
everything that reads it should go through compute_xp_balance.
"""
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import XPLedger


async def award_xp(
    db: AsyncSession,
    tenant_id: int,
    student_id: int,
    delta: int,
    reason: str,
    source_type: str,
    source_id: int,
) -> XPLedger:
    """Append one movement to the ledger.

    `delta` is positive for XP earned and negative for XP spent. The row is
    added to the session but not committed — the caller owns the transaction,
    so the award and whatever caused it land atomically.
    """
    entry = XPLedger(
        tenant_id=tenant_id,
        student_id=student_id,
        delta=delta,
        reason=reason,
        source_type=source_type,
        source_id=source_id,
    )
    db.add(entry)
    return entry


async def compute_xp_balance(db: AsyncSession, tenant_id: int, student_id: int) -> int:
    """Current balance: the sum of every movement for this student."""
    total = await db.scalar(
        select(func.coalesce(func.sum(XPLedger.delta), 0)).where(
            XPLedger.tenant_id == tenant_id,
            XPLedger.student_id == student_id,
        )
    )
    return int(total or 0)


PURCHASE_SOURCE = "purchase"


async def compute_xp_totals(db: AsyncSession, tenant_id: int, student_id: int) -> tuple[int, int]:
    """Return (earned, spent) as positive numbers, in a single query.

    Split by source, not by sign. A reversal is a negative delta against a
    task or project — it is un-earning, not spending, so it reduces `earned`.
    Only purchases count toward `spent`.

    Both sides are net sums, which keeps `earned - spent == balance` true even
    once refunds exist (a refund is a positive delta on a purchase).
    """
    row = (
        await db.execute(
            select(
                func.coalesce(
                    func.sum(case((XPLedger.source_type != PURCHASE_SOURCE, XPLedger.delta), else_=0)), 0
                ),
                func.coalesce(
                    func.sum(case((XPLedger.source_type == PURCHASE_SOURCE, -XPLedger.delta), else_=0)), 0
                ),
            ).where(
                XPLedger.tenant_id == tenant_id,
                XPLedger.student_id == student_id,
            )
        )
    ).one()
    return int(row[0] or 0), int(row[1] or 0)


async def reverse_xp_for_source(
    db: AsyncSession,
    tenant_id: int,
    source_type: str,
    source_id: int,
    reason: str,
) -> int:
    """Claw back whatever a source has awarded so far. Returns the amount reversed.

    Used when a completion is undone. Without it, un-completing and
    re-completing mints XP on every cycle. Reversal is always a new row, never
    a delete, so history stays intact — and it is idempotent, because a second
    call sees a net of zero and writes nothing.
    """
    rows = (
        await db.execute(
            select(XPLedger.student_id, func.sum(XPLedger.delta))
            .where(
                XPLedger.tenant_id == tenant_id,
                XPLedger.source_type == source_type,
                XPLedger.source_id == source_id,
            )
            .group_by(XPLedger.student_id)
        )
    ).all()

    reversed_total = 0
    for student_id, net in rows:
        if net:
            await award_xp(
                db,
                tenant_id=tenant_id,
                student_id=student_id,
                delta=-int(net),
                reason=reason,
                source_type=source_type,
                source_id=source_id,
            )
            reversed_total += int(net)
    return reversed_total


async def compute_xp_over_time(db: AsyncSession, tenant_id: int, student_id: int) -> list[dict]:
    """Cumulative balance per day, oldest first — for the analytics chart."""
    rows = (
        await db.execute(
            select(
                func.date(XPLedger.created_at).label("day"),
                func.sum(XPLedger.delta),
            )
            .where(XPLedger.tenant_id == tenant_id, XPLedger.student_id == student_id)
            .group_by(func.date(XPLedger.created_at))
            .order_by(func.date(XPLedger.created_at))
        )
    ).all()

    running = 0
    series = []
    for day, delta in rows:
        running += int(delta or 0)
        series.append({"date": str(day), "xp_earned": running})
    return series
