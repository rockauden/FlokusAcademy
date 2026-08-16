"""Parental rights over a child's data.

COPPA §312.6 gives a parent the right to review and to delete what has been
collected about their child; §312.5 requires recorded consent before it is
collected at all. Both are teacher/parent-only and scoped to the caller's own
tenant.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import List

from app.database import get_db
from app.models import Assignment, ChatMessage, ConsentRecord, Lesson, SafetyEvent, StuckFlag, User, XPLedger
from app.auth import require_teacher_user
from app.schemas import ConsentRecordCreate, ConsentRecordResponse, SafetyEventResponse, StuckFlagResponse

router = APIRouter(prefix="/api/students", tags=["students"])


async def _get_student(db: AsyncSession, tenant_id: int, student_id: int) -> User:
    result = await db.execute(
        select(User).where(
            User.id == student_id,
            User.tenant_id == tenant_id,
            User.role == 'student',
        )
    )
    student = result.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.post("/consent", response_model=ConsentRecordResponse)
async def record_consent(
    body: ConsentRecordCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    """Record that the parent granted or withdrew consent.

    Append-only: withdrawing writes a new row with is_granted=false rather than
    editing the original, so the audit trail survives.
    """
    record = ConsentRecord(
        tenant_id=user.tenant_id,
        parent_id=user.id,
        consent_version=body.consent_version,
        is_granted=body.is_granted,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/consent", response_model=List[ConsentRecordResponse])
async def list_consent(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    result = await db.execute(
        select(ConsentRecord)
        .where(ConsentRecord.tenant_id == user.tenant_id)
        .order_by(ConsentRecord.timestamp.desc())
    )
    return result.scalars().all()


@router.get("/{id}/export")
async def export_student_data(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    """Everything held about this child, as JSON."""
    student = await _get_student(db, user.tenant_id, id)

    assignments = (
        await db.execute(
            select(Assignment, Lesson)
            .join(Lesson, Assignment.lesson_id == Lesson.id)
            .where(Assignment.tenant_id == user.tenant_id, Assignment.student_id == student.id)
            .order_by(Assignment.id)
        )
    ).all()

    ledger = (
        await db.execute(
            select(XPLedger)
            .where(XPLedger.tenant_id == user.tenant_id, XPLedger.student_id == student.id)
            .order_by(XPLedger.id)
        )
    ).scalars().all()

    chat = (
        await db.execute(
            select(ChatMessage)
            .where(ChatMessage.tenant_id == user.tenant_id, ChatMessage.student_id == student.id)
            .order_by(ChatMessage.timestamp)
        )
    ).scalars().all()

    consent = (
        await db.execute(
            select(ConsentRecord)
            .where(ConsentRecord.tenant_id == user.tenant_id)
            .order_by(ConsentRecord.timestamp)
        )
    ).scalars().all()

    safety_events = (
        await db.execute(
            select(SafetyEvent)
            .where(SafetyEvent.tenant_id == user.tenant_id, SafetyEvent.student_id == student.id)
            .order_by(SafetyEvent.created_at)
        )
    ).scalars().all()

    stuck_flags = (
        await db.execute(
            select(StuckFlag)
            .where(StuckFlag.tenant_id == user.tenant_id, StuckFlag.student_id == student.id)
            .order_by(StuckFlag.created_at)
        )
    ).scalars().all()

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "student": {
            "id": student.id,
            "username": student.username,
            "display_name": student.display_name,
            "role": student.role,
            "created_at": student.created_at,
        },
        "assignments": [
            {
                "id": a.id,
                "lesson_title": lesson.title,
                "scheduled_date": a.scheduled_date,
                "is_completed": a.is_completed,
                "actual_completion_date": a.actual_completion_date,
                "focus_minutes": a.focus_minutes,
                "completion_notes": a.completion_notes,
            }
            for a, lesson in assignments
        ],
        "xp_ledger": [
            {
                "id": e.id,
                "delta": e.delta,
                "reason": e.reason,
                "source_type": e.source_type,
                "source_id": e.source_id,
                "created_at": e.created_at,
            }
            for e in ledger
        ],
        "chat_history": [
            {
                "id": m.id,
                "session_id": m.session_id,
                "sender": m.sender,
                "message": m.message,
                "timestamp": m.timestamp,
            }
            for m in chat
        ],
        "consent_records": [
            {
                "id": c.id,
                "parent_id": c.parent_id,
                "consent_version": c.consent_version,
                "is_granted": c.is_granted,
                "timestamp": c.timestamp,
            }
            for c in consent
        ],
        "safety_events": [
            {
                "id": s.id,
                "session_id": s.session_id,
                "category": s.category,
                "excerpt": s.excerpt,
                "created_at": s.created_at,
                "acknowledged_at": s.acknowledged_at,
            }
            for s in safety_events
        ],
        "stuck_flags": [
            {
                "id": f.id,
                "session_id": f.session_id,
                "topic": f.topic,
                "created_at": f.created_at,
                "resolved_at": f.resolved_at,
            }
            for f in stuck_flags
        ],
    }


@router.delete("/{id}")
async def delete_student_data(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    """Right to be forgotten: hard-delete the child and everything about them.

    Children are removed before the user row so the foreign keys stay valid at
    every step. This is irreversible — there is no soft-delete tombstone,
    because a tombstone would be retained personal data.
    """
    student = await _get_student(db, user.tenant_id, id)

    if student.id == user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    deleted = {}
    for label, stmt in (
        ("chat_history", delete(ChatMessage).where(
            ChatMessage.tenant_id == user.tenant_id, ChatMessage.student_id == student.id)),
        # Must be deleted with the rest: safety_events.student_id is a foreign
        # key to users.id, so leaving these behind would make the delete below
        # fail outright rather than merely leaving stray rows.
        ("safety_events", delete(SafetyEvent).where(
            SafetyEvent.tenant_id == user.tenant_id, SafetyEvent.student_id == student.id)),
        ("stuck_flags", delete(StuckFlag).where(
            StuckFlag.tenant_id == user.tenant_id, StuckFlag.student_id == student.id)),
        ("xp_ledger", delete(XPLedger).where(
            XPLedger.tenant_id == user.tenant_id, XPLedger.student_id == student.id)),
        ("assignments", delete(Assignment).where(
            Assignment.tenant_id == user.tenant_id, Assignment.student_id == student.id)),
    ):
        result = await db.execute(stmt)
        deleted[label] = result.rowcount or 0

    await db.delete(student)
    await db.commit()

    deleted["user"] = 1
    return {"message": f"Deleted all data for student {student.username}", "deleted": deleted}


@router.get("/safety-events", response_model=List[SafetyEventResponse])
async def list_safety_events(
    unacknowledged_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    """Alerts raised by the AI tutor's safety check, newest first.

    There is no push or email channel in this deployment, so this is how a
    parent finds out. That is a real limitation: an alert waits until the
    dashboard is next opened. It is recorded plainly rather than papered over,
    because a parent should know the delay exists.
    """
    query = select(SafetyEvent).where(SafetyEvent.tenant_id == user.tenant_id)
    if unacknowledged_only:
        query = query.where(SafetyEvent.acknowledged_at.is_(None))
    # id breaks ties: created_at is second-precision on SQLite, so two alerts
    # raised in the same second would otherwise come back in an arbitrary and
    # unstable order.
    result = await db.execute(query.order_by(SafetyEvent.created_at.desc(), SafetyEvent.id.desc()))
    return result.scalars().all()


@router.post("/safety-events/{id}/acknowledge", response_model=SafetyEventResponse)
async def acknowledge_safety_event(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    """Mark an alert as seen. Kept, not deleted -- the history is the point."""
    result = await db.execute(
        select(SafetyEvent).where(
            SafetyEvent.tenant_id == user.tenant_id,
            SafetyEvent.id == id,
        )
    )
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Safety event not found")

    event.acknowledged_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(event)
    return event


@router.get("/stuck-flags", response_model=List[StuckFlagResponse])
async def list_stuck_flags(
    unresolved_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    """Times the tutor judged the student to be stuck, newest first.

    Kept apart from the safety alerts on purpose. Struggling with fractions and
    disclosing that someone is hurting you are not the same news, and mixing
    them would cost the safety banner the weight it needs to keep.
    """
    query = select(StuckFlag).where(StuckFlag.tenant_id == user.tenant_id)
    if unresolved_only:
        query = query.where(StuckFlag.resolved_at.is_(None))
    # id breaks ties: created_at is second-precision on SQLite, so two flags in
    # the same second would otherwise come back in an unstable order.
    result = await db.execute(query.order_by(StuckFlag.created_at.desc(), StuckFlag.id.desc()))
    return result.scalars().all()


@router.post("/stuck-flags/{id}/resolve", response_model=StuckFlagResponse)
async def resolve_stuck_flag(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    """Mark that the parent has helped. Kept, not deleted -- three flags on one
    topic in a week is the useful signal, and it vanishes if each is erased."""
    result = await db.execute(
        select(StuckFlag).where(
            StuckFlag.tenant_id == user.tenant_id,
            StuckFlag.id == id,
        )
    )
    flag = result.scalars().first()
    if not flag:
        raise HTTPException(status_code=404, detail="Stuck flag not found")

    flag.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(flag)
    return flag
