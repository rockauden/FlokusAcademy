from datetime import date, timedelta
from typing import List, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Assignment, SchoolCalendar, SchoolEvent
from app.repository import AssignmentRepository

# Upper bound on the day-by-day search for a day_of_week_hint match.
MAX_HINT_SEARCH_DAYS = 365

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

def compute_rolling_schedule(assignments: List[Assignment], anchor_date: date, non_school_dates: Set[date], today: date):
    """
    Assigns scheduled_date to each assignment based on completion status,
    the lesson's dependency mode, and its sequence order.
    """
    if not assignments:
        return

    # Sort by the lesson's sequence order
    assignments = sorted(assignments, key=lambda a: a.lesson.sequence_order)

    # Find the waterline (last completed date or today)
    waterline = today
    for a in assignments:
        if a.is_completed and a.actual_completion_date:
            if a.actual_completion_date > waterline:
                waterline = a.actual_completion_date

    # Next available school day after waterline
    next_avail = get_school_days(waterline, 1, non_school_dates)[0]
    if next_avail < today:
        next_avail = get_school_days(today, 1, non_school_dates)[0]

    current_school_day = next_avail

    for assignment in assignments:
        lesson = assignment.lesson

        if assignment.is_completed:
            # Completed work keeps its actual completion date
            if assignment.actual_completion_date:
                assignment.scheduled_date = assignment.actual_completion_date
            continue

        if lesson.dependency_mode in ('independent', 'teacher_led'):
            if lesson.day_of_week_hint is not None:
                # Find the next school day that matches the hint.
                # Bounded: an out-of-range hint can never match, and without a
                # cap that search runs forever and hangs the worker.
                search_date = current_school_day
                for _ in range(MAX_HINT_SEARCH_DAYS):
                    if search_date.weekday() == lesson.day_of_week_hint and search_date not in non_school_dates:
                        assignment.scheduled_date = search_date
                        break
                    search_date += timedelta(days=1)
                else:
                    raise ValueError(
                        f"Could not schedule lesson {lesson.id!r} ({lesson.title!r}): no school day "
                        f"matching day_of_week_hint={lesson.day_of_week_hint} found within "
                        f"{MAX_HINT_SEARCH_DAYS} days of {current_school_day}. "
                        f"Valid hints are 0=Mon to 3=Thu."
                    )
            else:
                assignment.scheduled_date = current_school_day

        elif lesson.dependency_mode == 'live_scheduled':
            if not assignment.scheduled_date:
                assignment.scheduled_date = current_school_day

        # Advance the school day for the next sequential lesson
        current_school_day = get_school_days(current_school_day + timedelta(days=1), 1, non_school_dates)[0]

async def reschedule_from_today(db_session: AsyncSession, tenant_id: int, unit_id: int | None = None):
    # Fetch non-school dates
    result = await db_session.execute(
        select(SchoolCalendar.calendar_date).where(
            SchoolCalendar.tenant_id == tenant_id,
            SchoolCalendar.day_type != 'school_day',
        )
    )
    non_school_dates = set(result.scalars().all())

    # Get anchor date (First day of school)
    result = await db_session.execute(
        select(SchoolEvent)
        .where(SchoolEvent.tenant_id == tenant_id, SchoolEvent.title.ilike('%First day%'))
        .order_by(SchoolEvent.event_date)
    )
    first_day = result.scalars().first()
    anchor_date = first_day.event_date if first_day else date(2026, 8, 17)
    today = date.today()

    assignments = await AssignmentRepository.for_scheduling(db_session, tenant_id=tenant_id, unit_id=unit_id)

    # Schedule each student's work independently — two students working the
    # same unit progress at their own pace.
    by_student_unit: dict[tuple[int, int | None], list[Assignment]] = {}
    for a in assignments:
        key = (a.student_id, a.lesson.unit_id)
        by_student_unit.setdefault(key, []).append(a)

    for group in by_student_unit.values():
        compute_rolling_schedule(group, anchor_date, non_school_dates, today)

    await db_session.commit()
