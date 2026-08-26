"""Bulk curriculum ingest: validate, commit, rollback.

Three endpoints, not four — with a single input format there is nothing for a
separate /parse step to do that /validate cannot do in the same pass (review
§5.3). All teacher-only: a student has no business writing curriculum.

These are actions, not collections, so unlike /api/tasks/ there is no
trailing-slash form to get wrong — but they are still reached through the same
TLS-terminating proxy, and the e2e suite drives them through the app's own
client for the same reason every other spec does.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_teacher_user
from app.database import get_db
from app.models import User
from app.repository import LessonRepository
from app.schemas import (
    CurriculumImportRequest,
    CurriculumRollbackRequest,
    ImportCommitResult,
    ImportReport,
    ImportRowIssue,
    ImportRowPreview,
    RollbackResult,
)
from app.services.curriculum_import import build_plan, commit_plan, rollback_import

router = APIRouter(prefix="/api/curriculum", tags=["curriculum"])


def _report(plan) -> dict:
    return {
        "errors": [ImportRowIssue(row=e.row, message=e.message) for e in sorted(plan.errors, key=lambda e: e.row)],
        "programs_to_create": plan.programs_to_create,
        "units_to_create": plan.units_to_create,
        "new": plan.new,
        "updated": plan.updated,
        "unchanged": plan.unchanged,
        "total_rows": plan.total_rows,
        "rows": [
            ImportRowPreview(row=r.row, program=r.program, unit=r.unit, title=r.values['title'], action=r.action)
            for r in plan.rows
        ],
    }


@router.post("/validate", response_model=ImportReport)
async def validate_curriculum(
    body: CurriculumImportRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    """Parse and resolve the CSV against the database. Writes nothing.

    Errors come back as data with a 200, not as an exception: a file with two
    bad rows still has 270 previewable good ones, and the client needs both
    halves to render a useful screen.
    """
    plan = await build_plan(db, user.tenant_id, body.csv_text)
    return ImportReport(**_report(plan))


@router.post("/commit", response_model=ImportCommitResult)
async def commit_curriculum(
    body: CurriculumImportRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    """Validate again server-side, then write in one transaction.

    Re-validating rather than trusting the client's earlier report: the
    database may have changed between preview and commit. A file with errors
    is refused whole — there is no partial import to half-trust afterwards.
    """
    students = await LessonRepository.list_students(db, tenant_id=user.tenant_id)
    if not students:
        raise HTTPException(status_code=409, detail="No student in this tenant to assign lessons to.")

    plan, import_id = await commit_plan(db, user.tenant_id, body.csv_text, students)
    if plan.errors:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "The file has validation errors and nothing was imported.",
                "errors": [{"row": e.row, "message": e.message} for e in sorted(plan.errors, key=lambda e: e.row)],
            },
        )

    await db.commit()
    return ImportCommitResult(**_report(plan), import_id=import_id)


@router.post("/rollback", response_model=RollbackResult)
async def rollback_curriculum(
    body: CurriculumRollbackRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    result = await rollback_import(db, user.tenant_id, body.import_id, force=body.force)

    if result.blocked_titles:
        # 409, and the titles: the teacher deciding whether to force needs to
        # know exactly which completed work is on the line.
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Completed work exists under this import. Roll back with force to reverse its XP and delete it.",
                "completed_lessons": result.blocked_titles,
            },
        )

    if result.lessons_deleted == 0:
        raise HTTPException(status_code=404, detail="No lessons found for that import id.")

    await db.commit()
    return RollbackResult(
        lessons_deleted=result.lessons_deleted,
        assignments_deleted=result.assignments_deleted,
        xp_reversed=result.xp_reversed,
    )
