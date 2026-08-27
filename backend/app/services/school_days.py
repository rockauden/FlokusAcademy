"""The school-week calendar: which days are teaching days.

This module used to also contain the rolling scheduler — the thing that
assigned `scheduled_date` to every incomplete assignment and re-flowed the
whole tenant whenever a sick day was added. It was removed on 2026-08-26
along with the curriculum importer, because the workflow it served was
removed: work is now entered by hand, one week at a time, and a date the
teacher typed is a decision, not a suggestion. Auto-placement had exactly one
job left — moving work the teacher had already placed — and that is the one
thing it must never do. See docs/BUILD_LOG.md, "one week at a time".

What remains is the part that was always true regardless of who does the
placing: which weekdays are school days, and which dates are blocked.
"""
import logging
from datetime import date, timedelta
from typing import Iterable, List, Set

logger = logging.getLogger(__name__)

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
    by the caller, and this stays a pure function.
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
