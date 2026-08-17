from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.schemas import SchoolCalendarCreate, SchoolCalendarEntry, ScheduleRecalcRequest
from app.models import SchoolCalendar
from app.auth import require_teacher_user
from app.models import User
from app.repository import AppConfigRepository
from app.services.rolling_scheduler import reschedule_from_today, get_school_days, parse_school_days

router = APIRouter(prefix="/api/schedule", tags=["schedule"])

@router.post("/recalculate")
async def trigger_recalculate(request: Optional[ScheduleRecalcRequest] = None, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    unit_id = request.module_id if request else None
    await reschedule_from_today(db, tenant_id=user.tenant_id, unit_id=unit_id)
    return {"message": "Schedule recalculated successfully"}

@router.post("/sick-day")
async def add_sick_day(date_val: date = Query(...), db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    entry = SchoolCalendar(tenant_id=user.tenant_id, calendar_date=date_val, day_type='sick_day', label='Sick Day')
    db.add(entry)
    await db.commit()
    await reschedule_from_today(db, tenant_id=user.tenant_id)
    return {"message": "Sick day added and schedule recalculated"}

@router.post("/holiday")
async def add_holiday(date_val: date = Query(...), label: str = Query("Holiday"), db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    entry = SchoolCalendar(tenant_id=user.tenant_id, calendar_date=date_val, day_type='holiday', label=label)
    db.add(entry)
    await db.commit()
    await reschedule_from_today(db, tenant_id=user.tenant_id)
    return {"message": "Holiday added and schedule recalculated"}

@router.get("/calendar", response_model=List[SchoolCalendarEntry])
async def get_calendar(start_date: date = Query(...), end_date: date = Query(...), db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    result = await db.execute(
        select(SchoolCalendar)
        .where(SchoolCalendar.tenant_id == user.tenant_id, SchoolCalendar.calendar_date >= start_date, SchoolCalendar.calendar_date <= end_date)
        .order_by(SchoolCalendar.calendar_date)
    )
    return result.scalars().all()

@router.delete("/calendar/{id}")
async def remove_calendar_entry(id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    result = await db.execute(select(SchoolCalendar).where(SchoolCalendar.tenant_id == user.tenant_id, SchoolCalendar.id == id))
    entry = result.scalars().first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    await db.delete(entry)
    await db.commit()
    await reschedule_from_today(db, tenant_id=user.tenant_id)
    return {"message": "Entry removed and schedule recalculated"}

@router.get("/school-days")
async def list_school_days(start_date: date = Query(...), count: int = Query(10), db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    result = await db.execute(select(SchoolCalendar.calendar_date).where(SchoolCalendar.tenant_id == user.tenant_id, SchoolCalendar.day_type != 'school_day'))
    non_school_dates = set(result.scalars().all())
    # Same source of truth as the scheduler. Answering from a hardcoded Mon-Thu
    # here while the scheduler read app_config would mean this endpoint quietly
    # described a week nobody was working.
    school_weekdays = parse_school_days(
        await AppConfigRepository.get(db, tenant_id=user.tenant_id, key='school_days')
    )
    days = get_school_days(start_date, count, non_school_dates, school_weekdays)
    return {"school_days": days}
