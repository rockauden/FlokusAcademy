"""
Schedule audit. Run after rebuild_schedule_2026_27.py.

Every check here corresponds to a defect that was actually present in the v1
calendar, so this doubles as a regression test: if a future scheduling change
reintroduces one of them, this fails loudly instead of quietly costing Sonny a
term of math or a Christmas morning.
"""

import sqlite3
import collections
import re
from datetime import date, timedelta

from rebuild_schedule_2026_27 import BREAK_WEEKS, HOLIDAYS, build_calendar

DB = "flokus.db"
MAX_TASKS_PER_DAY = 5

conn = sqlite3.connect(DB)
rows = list(conn.execute(
    "SELECT task_date, category, title, xp_reward FROM tasks ORDER BY task_date"))
school_days, week_starts = build_calendar()
valid = set(school_days)

by_day = collections.defaultdict(list)
for d, cat, t, xp in rows:
    by_day[date.fromisoformat(d)].append((cat, t, xp))

failures = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        failures.append(name)


print(f"\n{len(rows)} tasks across {len(by_day)} days "
      f"({min(by_day)} .. {max(by_day)})\n")

# 1 -------------------------------------------------------------------------
blocked = set()
for start in BREAK_WEEKS:
    blocked |= {start + timedelta(days=i) for i in range(5)}
blocked |= set(HOLIDAYS)
offenders = sorted(d for d in by_day if d in blocked)
check("no work scheduled on a break day or holiday", not offenders,
      f"{len(offenders)} offending days" if offenders else
      f"{len(blocked)} days off, all clear")

# 2 -------------------------------------------------------------------------
stray = sorted(d for d in by_day if d not in valid)
check("no work scheduled outside the school calendar", not stray,
      f"{stray[:3]}" if stray else "")

# 3 -------------------------------------------------------------------------
loads = {d: len(v) for d, v in by_day.items()}
over = {d: n for d, n in loads.items() if n > MAX_TASKS_PER_DAY}
counts = sorted(loads.values())
check(f"no day exceeds {MAX_TASKS_PER_DAY} tasks", not over,
      f"min {counts[0]}, median {counts[len(counts)//2]}, max {counts[-1]}"
      if not over else f"{len(over)} days over: {list(over.items())[:5]}")

# 4 -------------------------------------------------------------------------
# Friday is the review/catch-up day. Nothing that introduces new curriculum
# should land there -- only review routines, book parties and portfolio work.
FRIDAY_ALLOWED = re.compile(
    r"Weekly Math Review|Poetry Teatime|Weekly Challenge|Book Party|"
    r"Master Expo|Tuttle Series Synthesis|History Timeline|"
    r"History & Logic Annual Portfolios")
bad_friday = [(d, t) for d, v in by_day.items() if d.weekday() == 4
              for cat, t, xp in v if not FRIDAY_ALLOWED.search(t)]
check("Friday carries only review, parties and portfolio work", not bad_friday,
      f"{len(bad_friday)} offenders: {bad_friday[:3]}" if bad_friday else "")

# 5 -------------------------------------------------------------------------
# The original defect: math went dark from late November to April.
weeks_without_math = []
for i, monday in enumerate(week_starts):
    days = [monday + timedelta(days=n) for n in range(5)]
    lessons = [t for d in days for cat, t, xp in by_day.get(d, [])
               if cat == "Math (Beast Academy)" and "Weekly Math Review" not in t]
    if not lessons:
        weeks_without_math.append((i + 1, monday))
check("every instructional week contains real math lessons",
      not weeks_without_math,
      f"{len(weeks_without_math)} empty weeks: {weeks_without_math[:4]}"
      if weeks_without_math else f"{len(week_starts)} of {len(week_starts)} weeks")

# 6 -------------------------------------------------------------------------
prev = conn.execute(
    "SELECT COUNT(*) FROM tasks WHERE category='Math (Beast Academy)' "
    "AND title NOT LIKE '%Weekly Math Review%'").fetchone()[0]
check("Beast stream holds Level 2 (60) + Level 3 (84)", prev == 144,
      f"{prev} lessons")

l2_end = conn.execute(
    "SELECT MAX(task_date) FROM tasks WHERE title LIKE 'BA 2%' "
    "OR title LIKE '%Level 2%' OR title LIKE 'Check & fill%'").fetchone()[0]
l3_start = conn.execute(
    "SELECT MIN(task_date) FROM tasks WHERE title LIKE '%BA 3%'").fetchone()[0]
check("Level 3 begins after Level 2 ends", l2_end < l3_start,
      f"L2 ends {l2_end}, L3 starts {l3_start}")

# 7 -------------------------------------------------------------------------
pairs = collections.defaultdict(set)
for d, v in by_day.items():
    for cat, t, xp in v:
        m = re.search(r"Dart (\d+)", t)
        if m and "Book Party" in t:
            pairs[m.group(1)].add(d)
split = {k: sorted(v) for k, v in pairs.items() if len(v) > 1}
check("each book party activity and celebration share one day", not split,
      f"{len(pairs)} parties, all single-day" if not split else str(split))

# 8 -------------------------------------------------------------------------
dupes = collections.Counter()
for d, v in by_day.items():
    for cat, t, xp in v:
        dupes[(cat, t)] += 1
ROUTINE = re.compile(
    r"rotating|Weekly|Freewrite|Reverse Dictation|Big Juicy|Tactics & Play|"
    r"Interactive Practice|Live Class|Project Tinkering|Poetry Teatime")
ambiguous = [k for k, n in dupes.items() if n > 1 and not ROUTINE.search(k[1])]
check("no lesson title appears twice without a distinguishing part number",
      not ambiguous, f"{ambiguous[:4]}" if ambiguous else "")

# 7b ------------------------------------------------------------------------
# Nothing before the first day of school. Week one is a Wed-Fri three-day week,
# and the Monday and Tuesday that no longer exist must not still hold work.
import school_year
early = conn.execute("SELECT COUNT(*), MIN(task_date) FROM tasks WHERE task_date < ?",
                     (school_year.FIRST_DAY.isoformat(),)).fetchone()
check("nothing scheduled before the first day of school", early[0] == 0,
      f"school starts {school_year.FIRST_DAY:%a %d %b %Y}"
      if not early[0] else f"{early[0]} rows, earliest {early[1]}")

# 7c ------------------------------------------------------------------------
# A discussion is ABOUT a chapter and practice is FOR a chapter, so the leader
# has to come first. Starting the year on a Wednesday broke this once already:
# the leaders slid out of the short first week while the followers stayed.
# Pair by the parent named in the follower's own title -- "Tuttle Twins Civics
# & Discussion (TT Vol 1 Ch 3)" is about "TT Vol 1 Ch 3". Pairing by position
# instead looks right and is not: the Critical stream contains items like
# "Logic Review" that no prefix match would catch, so the two lists drift and
# the check reports failures that are really its own mis-alignment.
when = {t: d for t, d in conn.execute("SELECT title, task_date FROM tasks")}

for label, prefix in [
    ("Tuttle chapter is read before its civics discussion",
     "Tuttle Twins Civics & Discussion ("),
    ("Critical chapter is read before its exercises",
     "Chapter Exercises ("),
]:
    pairs, bad, orphans = 0, [], 0
    for title, day in conn.execute(
            "SELECT title, task_date FROM tasks WHERE title LIKE ?",
            (prefix.replace("(", "(") + "%",)):
        if not title.startswith(prefix):
            continue
        parent = title[len(prefix):].rstrip(")")
        if parent not in when:
            orphans += 1
            continue
        pairs += 1
        if day < when[parent]:
            bad.append((title, day, when[parent]))
    note = f"{pairs} pairs in order"
    if orphans:
        note += f", {orphans} with no matching parent lesson"
    check(label, not bad, note if not bad
          else f"{len(bad)} out of order, first: {bad[0][0]} on {bad[0][1]} "
               f"but its chapter is {bad[0][2]}")

# 8b ------------------------------------------------------------------------
import free_market_rules
econ = conn.execute(
    "SELECT COUNT(*), MIN(task_date), MAX(task_date) FROM tasks "
    "WHERE category = ?", (free_market_rules.CATEGORY,)).fetchone()
check("all 120 Free Market Rules lessons are scheduled", econ[0] == 120,
      f"{econ[0]} lessons, {econ[1]} .. {econ[2]}")

# The 30 units build on each other, so teaching order has to survive the
# holidays that shifted everything around them.
order = [t for (t,) in conn.execute(
    "SELECT title FROM tasks WHERE category = ? ORDER BY task_date, id",
    (free_market_rules.CATEGORY,))]
expected = [t["title"] for t in free_market_rules.TASKS]
check("economics is scheduled in publisher order", order == expected,
      "unit/lesson sequence intact" if order == expected else
      f"first divergence at #{next(i for i,(a,b) in enumerate(zip(order,expected)) if a!=b)}")

econ_fri = conn.execute(
    "SELECT COUNT(*) FROM tasks WHERE category = ? AND "
    "CAST(strftime('%w', task_date) AS INT) = 5", (free_market_rules.CATEGORY,)).fetchone()[0]
check("economics never lands on a Friday", econ_fri == 0, f"{econ_fri} on Fridays")

gone = conn.execute(
    "SELECT COUNT(*) FROM tasks WHERE category LIKE '%Brilliant%' "
    "OR title LIKE '%Brilliant%'").fetchone()[0]
check("Brilliant.org fully retired", gone == 0, f"{gone} rows remain")

# 9 -------------------------------------------------------------------------
boss = conn.execute("SELECT COUNT(*) FROM tasks WHERE is_boss_fight = 1").fetchone()[0]
check("boss-fight flag cleared everywhere", boss == 0, f"{boss} rows still flagged")

# 10 ------------------------------------------------------------------------
subjects = collections.Counter(cat for d, cat, t, xp in rows)
print("\n  Tasks per subject:")
for s, n in subjects.most_common():
    print(f"    {n:>4}  {s}")

print("\n  Load by weekday:")
wd = collections.defaultdict(list)
for d, v in by_day.items():
    wd[d.strftime("%a")].append(len(v))
for day in ("Mon", "Tue", "Wed", "Thu", "Fri"):
    v = wd[day]
    print(f"    {day}  {len(v):>3} days, avg {sum(v)/len(v):.1f}, max {max(v)}")

print(f"\n  Total XP available: {sum(xp for d, c, t, xp in rows):,}")
print(f"\n{'ALL CHECKS PASSED' if not failures else 'FAILURES: ' + str(failures)}\n")
raise SystemExit(1 if failures else 0)
