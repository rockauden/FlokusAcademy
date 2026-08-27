"""Destructive maintenance the teacher can run without a database console.

There is exactly one action here and it is irreversible, so it is built to be
hard to fire by accident and honest about what it destroys: teacher-only, a
typed confirmation phrase that the client cannot supply on the user's behalf,
and a response that says exactly what went.

Why it exists at all: V2 accumulated pilot and import data while its workflow
was being worked out, and the alternative to a guarded button is talking a
first-time developer through Railway's CLI and psql to run DELETE statements
against production by hand. That is a worse risk than this endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_teacher_user
from app.database import get_db
from app.models import Assignment, Lesson, Purchase, Unit, User, XPLedger
from app.schemas import ResetCurriculumRequest, ResetCurriculumResult

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])

# Typed by hand, in full, or nothing happens. Not a checkbox: a checkbox is one
# stray click and this cannot be undone.
CONFIRM_PHRASE = "DELETE ALL WORK"


@router.post("/reset-curriculum", response_model=ResetCurriculumResult)
async def reset_curriculum(
    body: ResetCurriculumRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    """Delete every lesson, assignment, unit, XP entry and purchase in this tenant.

    Kept, deliberately: classes, both accounts, the school calendar, UFA
    expenses, reward definitions and creator projects. What goes is the student
    work and the economy that hangs off it — which is the pair that has to move
    together. Wiping completions while leaving the XP they minted would leave a
    balance no surviving row explains.

    Order matters: assignments reference lessons, and lessons reference units,
    so children go before parents or the foreign keys refuse. The XP ledger and
    purchases are deleted outright rather than reversed through the ledger —
    reversal exists to keep an auditable history, and there is no history to
    keep once the work it describes is gone.
    """
    if body.confirm != CONFIRM_PHRASE:
        raise HTTPException(
            status_code=400,
            detail=f'Type "{CONFIRM_PHRASE}" exactly to confirm. Nothing was deleted.',
        )

    tenant = user.tenant_id

    async def count(model) -> int:
        return int(await db.scalar(select(func.count()).select_from(model).where(model.tenant_id == tenant)) or 0)

    counts = {
        "assignments": await count(Assignment),
        "lessons": await count(Lesson),
        "units": await count(Unit),
        "xp_entries": await count(XPLedger),
        "purchases": await count(Purchase),
    }

    for model in (Assignment, Lesson, Unit, XPLedger, Purchase):
        await db.execute(delete(model).where(model.tenant_id == tenant))

    await db.commit()
    return ResetCurriculumResult(**counts)
