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
from app.models import Assignment, ChatMessage, ConsentRecord, Lesson, User, XPLedger
from app.auth import require_teacher_user
from app.schemas import ConsentRecordCreate, ConsentRecordResponse

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
