from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from datetime import date, timedelta
from app.database import get_db
from app.schemas import AnalyticsSummary
from app.models import Task, Purchase, CreatorProject, Course
from app.auth import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Total XP Earned (Tasks + Projects)
    tasks_query = select(Task).options(joinedload(Task.course)).where(Task.is_completed == True)
    tasks_result = await db.execute(tasks_query)
    tasks = tasks_result.scalars().all()
    
    projects_query = select(CreatorProject).where(CreatorProject.status == 'Completed')
    projects_result = await db.execute(projects_query)
    projects = projects_result.scalars().all()
    
    purchases_query = select(Purchase)
    purchases_result = await db.execute(purchases_query)
    purchases = purchases_result.scalars().all()
    
    total_task_xp = sum((t.xp_reward * 2 if t.is_boss_fight else t.xp_reward) for t in tasks)
    total_project_xp = sum(p.xp_reward for p in projects)
    xp_spent = sum(p.xp_cost for p in purchases)
    xp_balance = (total_task_xp + total_project_xp) - xp_spent
    
    # Total Focus Minutes & Completion Stats
    total_focus_minutes = sum(t.focus_minutes for t in tasks)
    total_completed_tasks = len(tasks)
    
    on_time_count = sum(1 for t in tasks if t.scheduled_date and t.actual_completion_date and t.actual_completion_date <= t.scheduled_date)
    on_time_rate = (on_time_count / total_completed_tasks) if total_completed_tasks > 0 else 0.0
    
    # Subject breakdown
    completion_by_subject = {}
    for t in tasks:
        subj = t.course.subject_area
        completion_by_subject[subj] = completion_by_subject.get(subj, 0) + 1
        
    # Streak calculation
    completion_dates = sorted(list(set(t.actual_completion_date for t in tasks if t.actual_completion_date)))
    daily_streak = 0
    curr_date = date.today()
    # Simple streak logic: check back day by day
    while curr_date in completion_dates:
        daily_streak += 1
        curr_date -= timedelta(days=1)
        
    # Recent 7-day activity
    recent_7_day_activity = []
    today = date.today()
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        count = sum(1 for t in tasks if t.actual_completion_date == d)
        recent_7_day_activity.append({"date": d.isoformat(), "completed_count": count})
        
    # XP over time (cumulative) - simplified by date of task completion
    xp_over_time = []
    current_xp = 0
    for d in completion_dates:
        day_tasks = [t for t in tasks if t.actual_completion_date == d]
        day_xp = sum((t.xp_reward * 2 if t.is_boss_fight else t.xp_reward) for t in day_tasks)
        current_xp += day_xp
        xp_over_time.append({"date": d.isoformat(), "xp_earned": current_xp})

    return AnalyticsSummary(
        xp_balance=xp_balance,
        daily_streak=daily_streak,
        total_completed_tasks=total_completed_tasks,
        total_focus_minutes=total_focus_minutes,
        on_time_rate=on_time_rate,
        completion_by_subject=completion_by_subject,
        xp_over_time=xp_over_time,
        recent_7_day_activity=recent_7_day_activity
    )
