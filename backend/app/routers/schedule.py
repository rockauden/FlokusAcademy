"""The school calendar: days off, and which weekdays are teaching days.

**Nothing here moves work any more.** Adding a sick day or a holiday used to
fire `reschedule_from_today` across the whole tenant, rewriting the date of
every incomplete assignment — and so did deleting a calendar entry. That was
the right behaviour when the app placed work itself. It is the wrong
behaviour now that the teacher enters a week by hand on Sunday: a date he
typed is a decision, and silently moving it is the app overruling him.

So marking a day off now *reports* what falls on it and leaves the work
alone. The week planner shows those items and he decides — move them, or let
them ride. See docs/BUILD_LOG.md, "one week at a time".
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List
from datetime import date
from app.database import get_db
from app.schemas import SchoolCalendarEntry, DayOffResult, AffectedAssignment
from app.models import Assignment, Lesson, SchoolCalendar
from app.auth import require_teacher_user
from app.models import User
from app.repository import AppConfigRepository
from app.services.school_days import get_school_days, parse_school_days

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


async def _affected_by(db: AsyncSession, tenant_id: int, day: date) -> List[AffectedAssignment]:
    """Unfinished work sitting on a date, so marking it off can say what it hit.

    Completed work is excluded on purpose: it happened, and a day marked off
    afterwards does not un-happen it.
    """
    result = await db.execute(
        select(Assignment)
        .options(joinedload(Assignment.lesson).joinedload(Lesson.program))
        .join(Lesson, Assignment.lesson_id == Lesson.id)
        .where(
            Assignment.tenant_id == tenant_id,
            Assignment.scheduled_date == day,
            Assignment.is_completed == False,
        )
    )
    return [
        AffectedAssignment(
            id=a.id,
            title=a.lesson.title,
            course_title=a.lesson.program.title,
            scheduled_date=a.scheduled_date,
        )
        for a in result.scalars().unique().all()
    ]


async def _mark_day(
    db: AsyncSession, tenant_id: int, day: date, day_type: str, label: str
) -> DayOffResult:
    existing = (
        await db.execute(
            select(SchoolCalendar).where(
                SchoolCalendar.tenant_id == tenant_id, SchoolCalendar.calendar_date == day
            )
        )
    ).scalars().first()

    if existing:
        # calendar_date is unique, so a second mark on the same day is an
        # edit rather than an error — the teacher changing "sick day" to
        # "holiday" should not have to delete the first one.
        existing.day_type = day_type
        existing.label = label
    else:
        db.add(SchoolCalendar(tenant_id=tenant_id, calendar_date=day, day_type=day_type, label=label))

    affected = await _affected_by(db, tenant_id, day)
    await db.commit()
    return DayOffResult(date=day, day_type=day_type, label=label, affected=affected)


@router.post("/sick-day", response_model=DayOffResult)
async def add_sick_day(
    date_val: date = Query(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    return await _mark_day(db, user.tenant_id, date_val, 'sick_day', 'Sick Day')


@router.post("/holiday", response_model=DayOffResult)
async def add_holiday(
    date_val: date = Query(...),
    label: str = Query("Holiday"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    return await _mark_day(db, user.tenant_id, date_val, 'holiday', label)


@router.get("/calendar", response_model=List[SchoolCalendarEntry])
async def get_calendar(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    result = await db.execute(
        select(SchoolCalendar)
        .where(
            SchoolCalendar.tenant_id == user.tenant_id,
            SchoolCalendar.calendar_date >= start_date,
            SchoolCalendar.calendar_date <= end_date,
        )
        .order_by(SchoolCalendar.calendar_date)
    )
    return result.scalars().all()


@router.delete("/calendar/{id}")
async def remove_calendar_entry(
    id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)
):
    result = await db.execute(
        select(SchoolCalendar).where(
            SchoolCalendar.tenant_id == user.tenant_id, SchoolCalendar.id == id
        )
    )
    entry = result.scalars().first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    await db.delete(entry)
    await db.commit()
    return {"message": "Entry removed"}


@router.get("/school-days")
async def list_school_days(
    start_date: date = Query(...),
    count: int = Query(10),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    result = await db.execute(
        select(SchoolCalendar.calendar_date).where(
            SchoolCalendar.tenant_id == user.tenant_id, SchoolCalendar.day_type != 'school_day'
        )
    )
    non_school_dates = set(result.scalars().all())
    school_weekdays = parse_school_days(
        await AppConfigRepository.get(db, tenant_id=user.tenant_id, key='school_days')
    )
    return {"school_days": get_school_days(start_date, count, non_school_dates, school_weekdays)}
