from datetime import date, timedelta
from typing import List, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Task, SchoolCalendar, SchoolEvent

def get_school_days(start_date: date, count: int, non_school_dates: Set[date]) -> List[date]:
    """Generate `count` school days starting from `start_date`, skipping non-school dates and weekends (Fri/Sat/Sun)."""
    days = []
    current_date = start_date
    while len(days) < count:
        # Weekday 0=Mon, 1=Tue, 2=Wed, 3=Thu. 4=Fri, 5=Sat, 6=Sun
        is_weekend = current_date.weekday() >= 4
        if not is_weekend and current_date not in non_school_dates:
            days.append(current_date)
        current_date += timedelta(days=1)
    return days

def compute_rolling_schedule(tasks: List[Task], anchor_date: date, non_school_dates: Set[date], today: date):
    """
    Assigns scheduled_date to each task based on completion status, dependency mode, and sequence order.
    """
    if not tasks:
        return
        
    # Sort tasks by sequence order
    tasks = sorted(tasks, key=lambda t: t.sequence_order)
    
    # Find the waterline (last completed task date or today)
    waterline = today
    for t in tasks:
        if t.is_completed and t.actual_completion_date:
            if t.actual_completion_date > waterline:
                waterline = t.actual_completion_date
                
    # Next available school day after waterline
    next_avail = get_school_days(waterline, 1, non_school_dates)[0]
    if next_avail < today:
        next_avail = get_school_days(today, 1, non_school_dates)[0]
        
    current_school_day = next_avail
    
    for task in tasks:
        if task.is_completed:
            # Completed tasks keep their actual completion date (if none, just skip or use actual)
            if task.actual_completion_date:
                task.scheduled_date = task.actual_completion_date
            continue
            
        if task.dependency_mode == 'independent' or task.dependency_mode == 'teacher_led':
            # Place it on the current_school_day, but respect day_of_week_hint if possible
            if task.day_of_week_hint is not None:
                # Find the next school day that matches the hint
                search_date = current_school_day
                while True:
                    if search_date.weekday() == task.day_of_week_hint and search_date not in non_school_dates:
                        task.scheduled_date = search_date
                        # We don't advance current_school_day here, we just place it.
                        # (A more complex engine would advance, but keeping it simple)
                        break
                    search_date += timedelta(days=1)
            else:
                task.scheduled_date = current_school_day
                
        elif task.dependency_mode == 'live_scheduled':
            # Live scheduled tasks should probably just keep their existing date or be handled specially.
            # If they don't have one, just put them on next_avail.
            if not task.scheduled_date:
                task.scheduled_date = current_school_day
                
        # Advance current school day for the next sequential task
        current_school_day = get_school_days(current_school_day + timedelta(days=1), 1, non_school_dates)[0]

async def reschedule_from_today(db_session: AsyncSession, module_id: int | None = None):
    # Fetch non-school dates
    result = await db_session.execute(select(SchoolCalendar.calendar_date).where(SchoolCalendar.day_type != 'school_day'))
    non_school_dates = set(result.scalars().all())
    
    # Get anchor date (First day of school)
    result = await db_session.execute(select(SchoolEvent).where(SchoolEvent.title.ilike('%First day%')).order_by(SchoolEvent.event_date))
    first_day = result.scalars().first()
    anchor_date = first_day.event_date if first_day else date(2026, 8, 17)
    today = date.today()
    
    # Fetch tasks
    query = select(Task)
    if module_id:
        query = query.where(Task.module_id == module_id)
    result = await db_session.execute(query)
    tasks = result.scalars().all()
    
    # Group by module to compute schedule
    tasks_by_module = {}
    for t in tasks:
        if t.module_id not in tasks_by_module:
            tasks_by_module[t.module_id] = []
        tasks_by_module[t.module_id].append(t)
        
    for mod_id, mod_tasks in tasks_by_module.items():
        compute_rolling_schedule(mod_tasks, anchor_date, non_school_dates, today)
        
    await db_session.commit()
