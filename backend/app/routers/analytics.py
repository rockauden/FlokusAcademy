from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from typing import Optional
from app.database import get_db
from app.schemas import ActivityResponse, AnalyticsSummary
from app.models import User
from app.auth import get_current_active_user
from app.repository import AssignmentRepository
from app.services import activity as activity_service
from app.services.xp_service import compute_xp_balance, compute_xp_over_time

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# How far back the streak may reach. Long enough to cover a real run, short
# enough that the query stays trivial.
STREAK_WINDOW_DAYS = 180


@router.get("/activity", response_model=ActivityResponse)
async def get_activity(
    student_id: Optional[int] = Query(None, description="Teachers only; students always get their own."),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """The current school week's completion counts, and the streak.

    Replaces the hardcoded week strip and the literal streak of 5 that used to
    sit on the student's dashboard.
    """
    if user.role == "student":
        # A student may only ever see themselves, whatever they ask for.
        target_id = user.id
    elif student_id is not None:
        target = (await db.execute(
            select(User).where(
                User.id == student_id,
                User.tenant_id == user.tenant_id,
                User.role == "student",
            )
        )).scalars().first()
        if not target:
            raise HTTPException(status_code=404, detail="Student not found")
        target_id = target.id
    else:
        raise HTTPException(status_code=400, detail="student_id is required for this role")

    today = date.today()
    week = activity_service.school_week(today)

    # The streak needs history well beyond the displayed week, so one query
    # covers both and the week is sliced out of it.
    start = min(week[0], today - timedelta(days=STREAK_WINDOW_DAYS))
    end = max(week[-1], today)

    assignments = await AssignmentRepository.in_day_range(
        db, tenant_id=user.tenant_id, student_id=target_id, start=start, end=end
    )

    days, streak = activity_service.summarise(assignments, week, today)
    return ActivityResponse(days=days, streak=streak)

@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    # XP is not recomputed here. The ledger is the single source of truth —
    # this endpoint used to sum tasks, projects and purchases itself and
    # disagreed with the balance the purchase gate enforced.
    xp_balance = await compute_xp_balance(db, tenant_id=user.tenant_id, student_id=user.id)
    xp_over_time = await compute_xp_over_time(db, tenant_id=user.tenant_id, student_id=user.id)

    # Everything below is activity reporting, not currency.
    tasks = await AssignmentRepository.list_completed(
        db, tenant_id=user.tenant_id, student_id=user.id
    )

    total_focus_minutes = sum(t.focus_minutes for t in tasks)
    total_completed_tasks = len(tasks)

    on_time_count = sum(
        1 for t in tasks
        if t.scheduled_date and t.actual_completion_date and t.actual_completion_date <= t.scheduled_date
    )
    on_time_rate = (on_time_count / total_completed_tasks) if total_completed_tasks > 0 else 0.0

    completion_by_subject = {}
    for t in tasks:
        subj = t.lesson.program.subject_area
        completion_by_subject[subj] = completion_by_subject.get(subj, 0) + 1

    # Streak: consecutive days with a completion, counting back from today.
    completion_dates = {t.actual_completion_date for t in tasks if t.actual_completion_date}
    daily_streak = 0
    curr_date = date.today()
    while curr_date in completion_dates:
        daily_streak += 1
        curr_date -= timedelta(days=1)

    today = date.today()
    recent_7_day_activity = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        count = sum(1 for t in tasks if t.actual_completion_date == d)
        recent_7_day_activity.append({"date": d.isoformat(), "completed_count": count})

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
