"""
The 2026-27 school calendar: which days are school days, and which are not.

This lives on its own because two very different things need the same answer.
The yearly rebuild needs it to lay out the plan. The curriculum importer needs
it so that a program imported in February lands on real school days instead of
quietly scheduling a lesson on Christmas Day -- which is exactly what the
original v1 generator did, 16 times.

Change a date here and both agree. There is no second copy.
"""

from datetime import date, timedelta

MON, TUE, WED, THU, FRI = 0, 1, 2, 3, 4
WEEKDAY_NAMES = {"Mon": MON, "Tue": TUE, "Wed": WED, "Thu": THU, "Fri": FRI}

# The real first day of school. It is a WEDNESDAY, so week one is a three-day
# week -- Wed, Thu, Fri -- and every week after it is a normal Mon-Fri.
#
# WHY THIS IS NOT SIMPLY A MONDAY: the year was originally laid out from Mon
# 17 Aug because that was the placeholder. Starting two days later costs one
# Monday and one Tuesday, and the lesson streams are tight enough that those
# two openings matter -- Beast Academy needs 144 core-day slots and only 142
# survive in 37 weeks. INSTRUCTIONAL_WEEKS went to 38 to absorb it rather than
# quietly dropping two math lessons off the end of the year.
FIRST_DAY = date(2026, 8, 19)           # Wednesday
YEAR_START = FIRST_DAY                  # public alias; prefer FIRST_DAY
INSTRUCTIONAL_WEEKS = 38

# Mon-Thu carry new material. Friday is review, book parties and catch-up:
# a light Friday is the design, not a shortfall.
CORE_DAYS = (MON, TUE, WED, THU)
REVIEW_DAY = FRI

# The most assignments Sonny should ever open the app to. He is nine. The
# number lives here rather than in the scheduler because the importer has to
# respect it too -- a routine that repeats "every Thursday" will otherwise pile
# onto the Thursday that already holds a CrunchLabs build day, and the ceiling
# gets breached by a path that never thought about it.
MAX_TASKS_PER_DAY = 5

# Full weeks off. A week listed here is skipped entirely and does not count
# toward INSTRUCTIONAL_WEEKS.
BREAK_WEEKS = {
    date(2026, 11, 23): "Thanksgiving Break",
    date(2026, 12, 21): "Winter Break",
    date(2026, 12, 28): "Winter Break",
    date(2027, 3, 15):  "Spring Break",
}

# Single days off inside an otherwise normal week. The week still counts as
# instructional; that one day simply does not exist.
HOLIDAYS = {
    date(2026, 9, 7):   "Labor Day",
    date(2026, 11, 11): "Veterans Day",
    date(2027, 1, 18):  "Martin Luther King Jr. Day",
    date(2027, 2, 15):  "Presidents' Day",
}


def build_calendar():
    """Return (school_days, week_starts) for the whole year.

    week_starts holds the MONDAY of each instructional week even when school
    does not begin on one. Routine expansion and week numbering both count in
    whole weeks, so week one has to start where the calendar says it does; it
    simply contributes fewer school days than the weeks after it.
    """
    school_days, week_starts = [], []
    monday = FIRST_DAY - timedelta(days=FIRST_DAY.weekday())
    while len(week_starts) < INSTRUCTIONAL_WEEKS:
        if monday in BREAK_WEEKS:
            monday += timedelta(days=7)
            continue
        week_starts.append(monday)
        for offset in range(5):                      # Mon-Fri
            day = monday + timedelta(days=offset)
            if day < FIRST_DAY:
                continue                             # before school started
            if day not in HOLIDAYS:
                school_days.append(day)
        monday += timedelta(days=7)
    return school_days, week_starts


def is_school_day(day):
    return day in set(build_calendar()[0])


def day_off_reason(day):
    """Why `day` has no school, or None if it is a normal school day."""
    if day < FIRST_DAY:
        return "Before the first day of school"
    if day in HOLIDAYS:
        return HOLIDAYS[day]
    monday = day - timedelta(days=day.weekday())
    if monday in BREAK_WEEKS:
        return BREAK_WEEKS[monday]
    if day.weekday() > FRI:
        return "Weekend"
    days, _ = build_calendar()
    if day not in set(days):
        return "Outside the school year"
    return None


def slots(weekdays, start=None, limit=None):
    """School days falling on any of `weekdays`, in order, from `start` on.

    This is what the importer schedules against. Passing weekdays the program
    actually occupies -- rather than every day in a row -- is what keeps an
    imported course on its own rhythm instead of dumping it onto consecutive
    calendar days and blowing past the daily ceiling.
    """
    days, _ = build_calendar()
    want = set(weekdays)
    out = [d for d in days if d.weekday() in want and (start is None or d >= start)]
    return out[:limit] if limit else out


def summary():
    days, weeks = build_calendar()
    return {
        "start": days[0],              # the first day school actually happens
        "end": days[-1],
        "weeks": len(weeks),
        "school_days": len(days),
        "days_off": len(BREAK_WEEKS) * 5 + len(HOLIDAYS),
    }
