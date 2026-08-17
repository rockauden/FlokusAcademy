import logging
from datetime import date, timedelta
from typing import Iterable, List, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Assignment, SchoolCalendar
from app.repository import AppConfigRepository, AssignmentRepository

logger = logging.getLogger(__name__)

# Upper bound on the day-by-day search for a day_of_week_hint match.
MAX_HINT_SEARCH_DAYS = 365

# Mon–Thu, which is what `app_config.school_days` is seeded with. Used when the
# key is missing or unreadable: a database that predates the key must still
# schedule, and refusing to would turn a settings problem into an outage.
DEFAULT_SCHOOL_WEEKDAYS: frozenset[int] = frozenset({0, 1, 2, 3})

# The academic year's first day, used when `app_config.academic_year_start` is
# missing. Was previously found by searching SchoolEvent for a title matching
# '%First day%' — a lookup that fails silently, and late, the moment anyone
# renames that calendar entry.
DEFAULT_ACADEMIC_YEAR_START = date(2026, 8, 17)

WEEKDAY_NUMBERS = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}

def parse_school_days(raw: str | None) -> frozenset[int]:
    """Turn `app_config.school_days` ("Mon,Tue,Wed,Thu") into weekday numbers.

    Tolerant on input and never returns an empty set: get_school_days searches
    day by day for a match, so no school day at all is an infinite loop that
    hangs the worker. A misconfigured week logs and falls back rather than
    taking the scheduler down with it.
    """
    if not raw:
        return DEFAULT_SCHOOL_WEEKDAYS

    parsed = {
        WEEKDAY_NUMBERS[token]
        for token in (part.strip().lower()[:3] for part in raw.split(','))
        if token in WEEKDAY_NUMBERS
    }
    if not parsed:
        logger.error(
            "app_config.school_days=%r names no recognisable weekday; falling back to Mon-Thu. "
            "Expected a comma-separated list like 'Mon,Tue,Wed,Thu'.",
            raw,
        )
        return DEFAULT_SCHOOL_WEEKDAYS
    return frozenset(parsed)


def get_school_days(
    start_date: date,
    count: int,
    non_school_dates: Set[date],
    school_weekdays: Iterable[int] = DEFAULT_SCHOOL_WEEKDAYS,
) -> List[date]:
    """Generate `count` core school days from `start_date`.

    A core day is one whose weekday is in `school_weekdays` and which is not
    blocked by the calendar. Fri/Sat/Sun are ordinarily *optional*, not
    forbidden — work may be placed there by hand, this function simply never
    chooses them on its own. That distinction is the whole point of B10: the
    code used to have one concept ("weekend") where it needed three.

    `school_weekdays` comes from `app_config.school_days` and is passed in
    rather than read here, so the config is fetched once per recalculation
    instead of once per lesson, and this stays a pure function.
    """
    weekdays = frozenset(school_weekdays) or DEFAULT_SCHOOL_WEEKDAYS
    days = []
    current_date = start_date
    while len(days) < count:
        # Weekday 0=Mon … 6=Sun.
        if current_date.weekday() in weekdays and current_date not in non_school_dates:
            days.append(current_date)
        current_date += timedelta(days=1)
    return days

def compute_rolling_schedule(
    assignments: List[Assignment],
    anchor_date: date,
    non_school_dates: Set[date],
    today: date,
    school_weekdays: Iterable[int] = DEFAULT_SCHOOL_WEEKDAYS,
):
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
    next_avail = get_school_days(waterline, 1, non_school_dates, school_weekdays)[0]
    if next_avail < today:
        next_avail = get_school_days(today, 1, non_school_dates, school_weekdays)[0]

    current_school_day = next_avail

    for assignment in assignments:
        lesson = assignment.lesson

        if assignment.is_completed:
            # Completed work keeps its actual completion date
            if assignment.actual_completion_date:
                assignment.scheduled_date = assignment.actual_completion_date
            continue

        if assignment.date_locked:
            # Placed by hand. Leave the date alone, and do not advance the
            # cursor: a Saturday catch-up sits outside the core-day sequence,
            # so consuming a Monday slot for it would push everything after it
            # a day later each time the calendar is touched.
            continue

        if lesson.dependency_mode in ('independent', 'teacher_led'):
            if lesson.day_of_week_hint is not None:
                # Find the next school day that matches the hint.
                #
                # The hint may name Fri/Sat/Sun — a deliberate "this belongs on
                # a weekend" — so the search looks at every day, not only core
                # days. Bounded: an out-of-range hint can never match, and
                # without a cap that search runs forever and hangs the worker.
                search_date = current_school_day
                for _ in range(MAX_HINT_SEARCH_DAYS):
                    if search_date.weekday() == lesson.day_of_week_hint and search_date not in non_school_dates:
                        assignment.scheduled_date = search_date
                        break
                    search_date += timedelta(days=1)
                else:
                    raise ValueError(
                        f"Could not schedule lesson {lesson.id!r} ({lesson.title!r}): no unblocked day "
                        f"matching day_of_week_hint={lesson.day_of_week_hint} found within "
                        f"{MAX_HINT_SEARCH_DAYS} days of {current_school_day}. "
                        f"Valid hints are 0=Mon to 6=Sun."
                    )
            else:
                assignment.scheduled_date = current_school_day

        elif lesson.dependency_mode == 'live_scheduled':
            if not assignment.scheduled_date:
                assignment.scheduled_date = current_school_day

        # Advance the school day for the next sequential lesson
        current_school_day = get_school_days(
            current_school_day + timedelta(days=1), 1, non_school_dates, school_weekdays
        )[0]

async def reschedule_from_today(db_session: AsyncSession, tenant_id: int, unit_id: int | None = None):
    # Fetch non-school dates
    result = await db_session.execute(
        select(SchoolCalendar.calendar_date).where(
            SchoolCalendar.tenant_id == tenant_id,
            SchoolCalendar.day_type != 'school_day',
        )
    )
    non_school_dates = set(result.scalars().all())

    # The school week and the year's anchor are settings, not code. Read once
    # per recalculation and threaded through, rather than queried per lesson.
    config = await AppConfigRepository.get_many(
        db_session, tenant_id=tenant_id, keys=('school_days', 'academic_year_start')
    )
    school_weekdays = parse_school_days(config.get('school_days'))
    anchor_date = _parse_anchor_date(config.get('academic_year_start'))
    today = date.today()

    assignments = await AssignmentRepository.for_scheduling(db_session, tenant_id=tenant_id, unit_id=unit_id)

    # Schedule each student's work independently — two students working the
    # same unit progress at their own pace.
    by_student_unit: dict[tuple[int, int | None], list[Assignment]] = {}
    for a in assignments:
        key = (a.student_id, a.lesson.unit_id)
        by_student_unit.setdefault(key, []).append(a)

    for group in by_student_unit.values():
        compute_rolling_schedule(group, anchor_date, non_school_dates, today, school_weekdays)

    await db_session.commit()


def _parse_anchor_date(raw: str | None) -> date:
    if not raw:
        return DEFAULT_ACADEMIC_YEAR_START
    try:
        return date.fromisoformat(raw)
    except ValueError:
        logger.error(
            "app_config.academic_year_start=%r is not an ISO date; falling back to %s.",
            raw, DEFAULT_ACADEMIC_YEAR_START,
        )
        return DEFAULT_ACADEMIC_YEAR_START
