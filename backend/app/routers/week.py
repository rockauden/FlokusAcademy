"""The week planner: hand-entered planning, one week at a time.

This is the teacher's Sunday screen and, since 2026-08-26, the only way
curriculum enters the app. The bulk importer and the rolling scheduler were
both removed with it — not because they did not work, but because they solved
a problem this household does not have. One student with four or five items a
day is fifteen lines of typing on a Sunday; a curriculum-management system to
avoid that typing was more machine than the job needed.

Two rules shape everything here:

1. **What the teacher types stays where he typed it.** Every entry is created
   with `date_locked = True`. Nothing in the app moves a dated assignment any
   more, but the flag says *why* the date is trustworthy, and it keeps that
   promise intact if any future feature is ever tempted to reflow work.

2. **A default should never be a reason to open a second screen.** A cell
   takes a title and nothing else; minutes, XP and type have defaults that are
   right often enough, and are editable on the card when they are not.
"""
from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_teacher_user
from app.database import get_db
from app.models import Assignment, Lesson, SchoolCalendar, User
from app.repository import AppConfigRepository, AssignmentRepository, LessonRepository
from app.schemas import TaskResponse, WeekEntryCreate, WeekEntryMove
from app.services.school_days import parse_school_days
from app.services.xp_service import reverse_xp_for_source
from sqlalchemy.future import select

router = APIRouter(prefix="/api/week", tags=["week"])

SOURCE_TYPE = 'assignment'


def _merge(a: Assignment) -> dict:
    """Assignment + Lesson flattened into the shape the client already speaks.

    Deliberately the same payload `routers/tasks.py` returns, so the planner
    and the task list describe an item identically and the client needs one
    mental model, not two.
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
        "priority": lesson.priority,
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


def monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())


@router.get("/")
async def get_week(
    start: date | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    """One week's grid, plus what is behind and which days are off.

    `start` is any date in the wanted week; it is snapped to that week's
    Monday, so the client can pass a day rather than having to know how to
    find a Monday.

    Omitted, it opens on the week the teacher is most likely to be planning:
    the current one from Monday to Thursday, and the *next* one from Friday
    onwards. Planning happens at the end of a week for the one after it, and
    an app that opens on a week already spent makes him navigate before he can
    start. "The week containing tomorrow" was the first cut and is wrong on a
    Friday, which lands on a week whose early days are already behind.
    """
    today = date.today()
    if start:
        week_start = monday_of(start)
    else:
        # weekday(): 0=Mon … 4=Fri.
        ahead = 7 if today.weekday() >= 4 else 0
        week_start = monday_of(today) + timedelta(days=ahead)
    week_end = week_start + timedelta(days=6)

    assignments = await AssignmentRepository.for_week(
        db, tenant_id=user.tenant_id, start=week_start, end=week_end
    )
    behind = await AssignmentRepository.list_before(db, tenant_id=user.tenant_id, before=today)

    days_off = (
        await db.execute(
            select(SchoolCalendar).where(
                SchoolCalendar.tenant_id == user.tenant_id,
                SchoolCalendar.calendar_date >= week_start,
                SchoolCalendar.calendar_date <= week_end,
                SchoolCalendar.day_type != 'school_day',
            )
        )
    ).scalars().all()

    config = await AppConfigRepository.get_many(
        db, tenant_id=user.tenant_id, keys=['school_days', 'daily_task_cap']
    )
    try:
        cap = int(config.get('daily_task_cap', '6'))
    except ValueError:
        cap = 6

    return {
        "week_start": week_start,
        "week_end": week_end,
        "school_weekdays": sorted(parse_school_days(config.get('school_days'))),
        "daily_task_cap": cap,
        # id travels with the day so the planner can clear one it is showing,
        # without a second round trip to find out which row it is.
        "days_off": [
            {"id": d.id, "date": d.calendar_date, "day_type": d.day_type, "label": d.label}
            for d in days_off
        ],
        "entries": [_merge(a) for a in assignments],
        "behind": [_merge(a) for a in behind],
    }


@router.post("/entries", response_model=TaskResponse)
async def create_entry(
    entry: WeekEntryCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    """One typed cell becomes a lesson and an assignment for each student.

    `date_locked` is True and not negotiable from here: the teacher typed a
    day, which is the strongest statement about placement the app can receive.
    """
    lesson = Lesson(
        tenant_id=user.tenant_id,
        program_id=entry.course_id,
        title=entry.title.strip(),
        description=entry.description,
        task_type=entry.task_type,
        resource_url=entry.resource_url,
        estimated_minutes=entry.estimated_minutes,
        xp_reward=entry.xp_reward,
    )
    db.add(lesson)
    await db.flush()

    students = await LessonRepository.list_students(db, tenant_id=user.tenant_id)
    if not students:
        raise HTTPException(status_code=409, detail="No student to assign this to.")

    created = []
    for student in students:
        assignment = Assignment(
            tenant_id=user.tenant_id,
            student_id=student.id,
            lesson_id=lesson.id,
            scheduled_date=entry.scheduled_date,
            date_locked=True,
        )
        db.add(assignment)
        created.append(assignment)

    await db.commit()
    refreshed = await AssignmentRepository.get(
        db, tenant_id=user.tenant_id, assignment_id=created[0].id
    )
    return TaskResponse(**_merge(refreshed))


@router.put("/entries/{id}/move", response_model=TaskResponse)
async def move_entry(
    id: int,
    move: WeekEntryMove,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    """Move one item to another day. Stays pinned; nothing else shifts."""
    a = await AssignmentRepository.get(db, tenant_id=user.tenant_id, assignment_id=id)
    if not a:
        raise HTTPException(status_code=404, detail="Not found")
    a.scheduled_date = move.scheduled_date
    a.date_locked = True
    await db.commit()
    refreshed = await AssignmentRepository.get(db, tenant_id=user.tenant_id, assignment_id=id)
    return TaskResponse(**_merge(refreshed))


@router.delete("/entries/{id}")
async def remove_entry(
    id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)
):
    """Remove one item from the plan — but only if nobody has finished it.

    Hand-entered work is authored per week, so a lesson here has exactly one
    assignment per student and no reuse to protect. Deleting the lesson is the
    honest thing for work that was planned and then reconsidered, and leaving
    orphans behind would slowly fill the portfolio with work nobody ever did.

    **Completed work is refused.** This used to delete regardless, which meant
    one click on a finished card destroyed the completion, the focus minutes
    and the notes, and reversed XP the student had genuinely earned — silently,
    with no confirmation and no undo. That is a hole in the compliance record
    and, from the child's side, points vanishing for work he actually did.

    The rule already existed elsewhere and this endpoint was the exception:
    `POST /courses/{id}/clear-unstarted` keeps anything completed, and the
    architecture note says earned XP stays earned. A 409 naming the item is the
    same shape that endpoint uses. The escape hatch is deliberate and visible —
    mark it not-done first, which is a decision the teacher takes on purpose,
    and then it can go.

    XP is still reversed for the uncompleted case. Nothing was earned there, so
    in practice the ledger has nothing to reverse; the call stays because a
    partially-completed multi-student lesson would otherwise leave a balance no
    surviving row explains.
    """
    a = await AssignmentRepository.get(db, tenant_id=user.tenant_id, assignment_id=id)
    if not a:
        raise HTTPException(status_code=404, detail="Not found")

    lesson = a.lesson
    siblings = await AssignmentRepository.list_for_lesson(
        db, tenant_id=user.tenant_id, lesson_id=lesson.id
    )

    if any(sibling.is_completed for sibling in siblings):
        raise HTTPException(
            status_code=409,
            detail=(
                f'"{lesson.title}" has already been marked done, so it is part of '
                "the school record and was not removed. Mark it as not done first "
                "if you really want it gone."
            ),
        )

    for sibling in siblings:
        await reverse_xp_for_source(
            db,
            tenant_id=user.tenant_id,
            source_type=SOURCE_TYPE,
            source_id=sibling.id,
            reason=f"Removed from the plan: {lesson.title}",
        )

    await db.delete(lesson)  # cascades to its assignments
    await db.commit()
    return {"message": "Removed"}
