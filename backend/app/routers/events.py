from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from datetime import date, timedelta
from app.database import get_db
from app.schemas import SchoolEventCreate, SchoolEventUpdate, SchoolEventResponse
from app.models import SchoolEvent
from app.auth import get_current_user, require_teacher

router = APIRouter(prefix="/api/events", tags=["events"])

@router.get("/", response_model=List[SchoolEventResponse])
async def list_events(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = select(SchoolEvent).order_by(SchoolEvent.event_date)
    if start_date:
        query = query.where(SchoolEvent.event_date >= start_date)
    if end_date:
        query = query.where(SchoolEvent.event_date <= end_date)
    if category:
        query = query.where(SchoolEvent.category == category)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/upcoming", response_model=List[SchoolEventResponse])
async def get_upcoming_events(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    today = date.today()
    # A simple way to get upcoming events within their reminder window
    # Wait, SQLite/Postgres date math differs. Since we fetch to python, let's just fetch future events and filter.
    query = select(SchoolEvent).where(SchoolEvent.event_date >= today).order_by(SchoolEvent.event_date)
    result = await db.execute(query)
    events = result.scalars().all()
    upcoming = []
    for e in events:
        if e.event_date <= today + timedelta(days=e.reminder_days):
            upcoming.append(e)
    return upcoming

@router.get("/next-major", response_model=Optional[SchoolEventResponse])
async def get_next_major_event(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    today = date.today()
    query = select(SchoolEvent).where(
        SchoolEvent.event_date >= today,
        SchoolEvent.importance.in_(['Important', 'Urgent'])
    ).order_by(SchoolEvent.event_date).limit(1)
    result = await db.execute(query)
    return result.scalars().first()

@router.post("/", response_model=SchoolEventResponse)
async def create_event(event: SchoolEventCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    new_event = SchoolEvent(**event.model_dump())
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)
    return new_event

@router.put("/{id}", response_model=SchoolEventResponse)
async def update_event(id: int, event_data: SchoolEventUpdate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(SchoolEvent).where(SchoolEvent.id == id))
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    for key, value in event_data.model_dump().items():
        setattr(event, key, value)
    await db.commit()
    await db.refresh(event)
    return event

@router.delete("/{id}")
async def delete_event(id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(SchoolEvent).where(SchoolEvent.id == id))
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.delete(event)
    await db.commit()
    return {"message": "Event deleted"}
