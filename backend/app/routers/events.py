from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date, timedelta
from app.database import get_db
from app.schemas import SchoolEventCreate, SchoolEventUpdate, SchoolEventResponse
from app.models import SchoolEvent, User
from app.auth import get_current_active_user, require_teacher_user
from app.repository import EventRepository

router = APIRouter(prefix="/api/events", tags=["events"])

@router.get("/", response_model=List[SchoolEventResponse])
async def list_events(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    return await EventRepository.list(
        db, tenant_id=user.tenant_id, start_date=start_date, end_date=end_date, category=category
    )

@router.get("/upcoming", response_model=List[SchoolEventResponse])
async def get_upcoming_events(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    today = date.today()
    events = await EventRepository.list(db, tenant_id=user.tenant_id, start_date=today)
    # reminder_days is per-event, so the window is filtered in Python rather
    # than in SQL (date arithmetic differs across SQLite and Postgres).
    return [e for e in events if e.event_date <= today + timedelta(days=e.reminder_days)]

@router.get("/next-major", response_model=Optional[SchoolEventResponse])
async def get_next_major_event(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    return await EventRepository.next_major(db, tenant_id=user.tenant_id, today=date.today())

@router.post("/", response_model=SchoolEventResponse)
async def create_event(event: SchoolEventCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    new_event = SchoolEvent(**event.model_dump(), tenant_id=user.tenant_id)
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)
    return new_event

@router.put("/{id}", response_model=SchoolEventResponse)
async def update_event(id: int, event_data: SchoolEventUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    event = await EventRepository.get(db, tenant_id=user.tenant_id, event_id=id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    for key, value in event_data.model_dump().items():
        setattr(event, key, value)
    await db.commit()
    await db.refresh(event)
    return event

@router.delete("/{id}")
async def delete_event(id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    event = await EventRepository.get(db, tenant_id=user.tenant_id, event_id=id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.delete(event)
    await db.commit()
    return {"message": "Event deleted"}
