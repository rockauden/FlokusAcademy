"""Student-facing work.

The API vocabulary here is still "task" — the routes and JSON field names are
unchanged so the Vue client keeps working. Internally a "task" is now an
Assignment (student state) joined to a Lesson (curriculum template), and the
`id` the client sees and posts back is always the assignment id.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskComplete, StudentDayView, StudentTaskExtended, StudentDayCourseInfo
from app.models import Assignment, Lesson, User
from app.auth import get_current_active_user, require_teacher_user
from app.repository import AssignmentRepository, LessonRepository
from app.services.xp_service import award_xp, reverse_xp_for_source

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

SOURCE_TYPE = 'assignment'


def lesson_xp(lesson: Lesson) -> int:
    """Boss fights are worth double. Defined once so the award and the reversal
    can never use different arithmetic."""
    return lesson.xp_reward * (2 if lesson.is_boss_fight else 1)


def _merge(a: Assignment) -> dict:
    """Flatten Assignment + Lesson into the shape the client already expects.

    `id` is the assignment id — that is what /complete, PUT and DELETE take.
    `course_id`/`module_id` keep their old names in the payload; internally
    they are Lesson.program_id / Lesson.unit_id.
    """
    lesson = a.lesson
    return {
        "id": a.id,
        "course_id": lesson.program_id,
        "module_id": lesson.unit_id,
        "title": lesson.title,
        "description": lesson.description,
        "task_type": lesson.task_type,
        "resource_url": lesson.resource_url,
        "resource_path": lesson.resource_path,
        "workbook_pages": lesson.workbook_pages,
        "sequence_order": lesson.sequence_order,
        "school_day_offset": lesson.school_day_offset,
        "day_of_week_hint": lesson.day_of_week_hint,
        "dependency_mode": lesson.dependency_mode,
        "estimated_minutes": lesson.estimated_minutes,
        "xp_reward": lesson.xp_reward,
        "is_boss_fight": lesson.is_boss_fight,
        "medium": lesson.medium,
        "ufa_eligible": lesson.ufa_eligible,
        "ufa_hours_credit": lesson.ufa_hours_credit,
        "scheduled_date": a.scheduled_date,
        "date_locked": a.date_locked,
        "is_completed": a.is_completed,
        "actual_completion_date": a.actual_completion_date,
        "completion_notes": a.completion_notes,
        "focus_minutes": a.focus_minutes,
        "created_at": a.created_at,
    }


def _split_payload(task: TaskCreate) -> tuple[dict, Optional[date], bool]:
    """Separate curriculum fields (Lesson) from instance fields (Assignment).

    The client still speaks the old flat vocabulary, so course_id/module_id are
    translated here and scheduled_date is peeled off — Lesson has no such
    column any more and would reject it. date_locked comes off for the same
    reason: it belongs to the student's instance, not to the curriculum.
    """
    payload = task.model_dump()
    scheduled_date = payload.pop('scheduled_date', None)
    # A pin with no date to pin is meaningless — the scheduler skips locked
    # assignments, so an undated locked one would simply never be placed.
    date_locked = bool(payload.pop('date_locked', False)) and scheduled_date is not None
    payload['program_id'] = payload.pop('course_id')
    payload['unit_id'] = payload.pop('module_id')
    return payload, scheduled_date, date_locked


async def _assign_to_students(
    db: AsyncSession,
    tenant_id: int,
    lesson: Lesson,
    scheduled_date: Optional[date],
    date_locked: bool = False,
) -> list[Assignment]:
    """Hand a newly authored lesson to every student in the tenant.

    Authoring a lesson and a student receiving it are now separate facts, but
    the admin UI still expects "create a task and it shows up in the day", so
    this keeps that behaviour.
    """
    students = await LessonRepository.list_students(db, tenant_id=tenant_id)
    created = []
    for student in students:
        assignment = Assignment(
            tenant_id=tenant_id,
            student_id=student.id,
            lesson_id=lesson.id,
            scheduled_date=scheduled_date,
            date_locked=date_locked,
        )
        db.add(assignment)
        created.append(assignment)
    return created


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    course_id: Optional[int] = None,
    module_id: Optional[int] = None,
    scheduled_date: Optional[date] = None,
    is_completed: Optional[bool] = None,
    dependency_mode: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    # A teacher sees the whole tenant's assignments; a student only their own.
    student_filter = None if user.role == 'teacher' else user.id
    assignments = await AssignmentRepository.list(
        db,
        tenant_id=user.tenant_id,
        student_id=student_filter,
        program_id=course_id,
        unit_id=module_id,
        scheduled_date=scheduled_date,
        is_completed=is_completed,
        dependency_mode=dependency_mode,
    )
    return [TaskResponse(**_merge(a)) for a in assignments]

@router.get("/today", response_model=StudentDayView)
async def get_today_tasks(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    today = date.today()
    assignments = await AssignmentRepository.get_today(
        db, tenant_id=user.tenant_id, student_id=user.id, today=today
    )

    student_tasks = []
    for a in assignments:
        program = a.lesson.program
        course_info = StudentDayCourseInfo(
            id=program.id,
            title=program.title,
            emoji=program.emoji,
            color_hex=program.color_hex,
            platform_url=program.platform_url,
        )
        student_tasks.append(StudentTaskExtended(**_merge(a), course=course_info))

    return StudentDayView(date=today, tasks=student_tasks)

@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    payload, scheduled_date, date_locked = _split_payload(task)
    lesson = Lesson(**payload, tenant_id=user.tenant_id)
    db.add(lesson)
    await db.flush()

    assignments = await _assign_to_students(
        db, user.tenant_id, lesson, scheduled_date, date_locked
    )
    if not assignments:
        raise HTTPException(
            status_code=409,
            detail="No student in this tenant to assign the lesson to.",
        )
    await db.commit()

    created = await AssignmentRepository.get(db, tenant_id=user.tenant_id, assignment_id=assignments[0].id)
    return TaskResponse(**_merge(created))

@router.post("/bulk", response_model=List[TaskResponse])
async def create_tasks_bulk(tasks: List[TaskCreate], db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    first_ids = []
    for t in tasks:
        payload, scheduled_date, date_locked = _split_payload(t)
        lesson = Lesson(**payload, tenant_id=user.tenant_id)
        db.add(lesson)
        await db.flush()
        assignments = await _assign_to_students(
            db, user.tenant_id, lesson, scheduled_date, date_locked
        )
        if not assignments:
            raise HTTPException(
                status_code=409,
                detail="No student in this tenant to assign the lessons to.",
            )
        first_ids.append(assignments[0].id)
    await db.commit()

    out = []
    for aid in first_ids:
        a = await AssignmentRepository.get(db, tenant_id=user.tenant_id, assignment_id=aid)
        out.append(TaskResponse(**_merge(a)))
    return out

@router.get("/{id}", response_model=TaskResponse)
async def get_task(id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    a = await AssignmentRepository.get(db, tenant_id=user.tenant_id, assignment_id=id)
    if not a:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(**_merge(a))

@router.put("/{id}", response_model=TaskResponse)
async def update_task(id: int, task_data: TaskUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    a = await AssignmentRepository.get(db, tenant_id=user.tenant_id, assignment_id=id)
    if not a:
        raise HTTPException(status_code=404, detail="Task not found")

    # Editing a "task" edits the underlying lesson — it is curriculum content.
    # scheduled_date is the one field that belongs to this student's instance.
    #
    # exclude_unset is what keeps this from being a data-loss bug: without it,
    # model_dump() returns a default for every field the client did not send,
    # so renaming a lesson also reset its XP, its duration and its date.
    payload = task_data.model_dump(exclude_unset=True)

    # exclude_unset alone cannot tell "field absent" from "field explicitly
    # null", and both matter here: absent means leave the date alone, null
    # means clear it deliberately and hand the assignment back to the
    # scheduler. Checking for the key rather than the value is the difference.
    scheduled_date_provided = 'scheduled_date' in payload
    scheduled_date = payload.pop('scheduled_date', None)
    date_locked = payload.pop('date_locked', None)

    for key, value in payload.items():
        if hasattr(a.lesson, key):
            setattr(a.lesson, key, value)

    if scheduled_date_provided:
        a.scheduled_date = scheduled_date

    if date_locked is not None:
        a.date_locked = bool(date_locked)

    # A pin needs something to pin to. Clearing the date releases the
    # assignment back to the scheduler, so leaving the flag set would strand
    # it: the scheduler skips locked rows, and an undated locked row is one it
    # would never place and nobody would ever see.
    if a.scheduled_date is None:
        a.date_locked = False

    await db.commit()
    refreshed = await AssignmentRepository.get(db, tenant_id=user.tenant_id, assignment_id=id)
    return TaskResponse(**_merge(refreshed))

@router.post("/{id}/complete", response_model=TaskResponse)
async def complete_task(id: int, completion: TaskComplete, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    a = await AssignmentRepository.get(db, tenant_id=user.tenant_id, assignment_id=id)
    if not a:
        raise HTTPException(status_code=404, detail="Task not found")

    if a.is_completed:
        raise HTTPException(status_code=409, detail="Already completed")

    if a.scheduled_date is not None and a.scheduled_date > date.today():
        raise HTTPException(status_code=409, detail="That task isn't unlocked yet")

    a.is_completed = True
    a.actual_completion_date = date.today()
    a.completion_notes = completion.completion_notes
    a.focus_minutes = completion.focus_minutes

    # The XP belongs to whoever the work was assigned to, not to whoever
    # clicked the button. A teacher marking work done credits the student.
    await award_xp(
        db,
        tenant_id=a.tenant_id,
        student_id=a.student_id,
        delta=lesson_xp(a.lesson),
        reason=f"Completed: {a.lesson.title}",
        source_type=SOURCE_TYPE,
        source_id=a.id,
    )

    await db.commit()
    refreshed = await AssignmentRepository.get(db, tenant_id=user.tenant_id, assignment_id=id)
    return TaskResponse(**_merge(refreshed))

@router.post("/{id}/uncomplete", response_model=TaskResponse)
async def uncomplete_task(id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    a = await AssignmentRepository.get(db, tenant_id=user.tenant_id, assignment_id=id)
    if not a:
        raise HTTPException(status_code=404, detail="Task not found")

    a.is_completed = False
    a.actual_completion_date = None
    a.completion_notes = ''
    a.focus_minutes = 0

    await reverse_xp_for_source(
        db,
        tenant_id=a.tenant_id,
        source_type=SOURCE_TYPE,
        source_id=a.id,
        reason=f"Reverted: {a.lesson.title}",
    )

    await db.commit()
    refreshed = await AssignmentRepository.get(db, tenant_id=user.tenant_id, assignment_id=id)
    return TaskResponse(**_merge(refreshed))

@router.delete("/{id}")
async def delete_task(id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    a = await AssignmentRepository.get(db, tenant_id=user.tenant_id, assignment_id=id)
    if not a:
        raise HTTPException(status_code=404, detail="Task not found")

    lesson = a.lesson
    # Reverse every student's award for this lesson before the cascade removes
    # the assignments, or the XP outlives the work that earned it.
    for sibling in await AssignmentRepository.list(db, tenant_id=user.tenant_id, unit_id=None):
        if sibling.lesson_id == lesson.id:
            await reverse_xp_for_source(
                db,
                tenant_id=user.tenant_id,
                source_type=SOURCE_TYPE,
                source_id=sibling.id,
                reason=f"Deleted: {lesson.title}",
            )

    await db.delete(lesson)  # cascades to its assignments
    await db.commit()
    return {"message": "Task deleted"}
