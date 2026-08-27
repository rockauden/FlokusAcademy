> ## ⚠️ Stale — describes a version of V2 that no longer exists
>
> **Written 19 August 2026** for flokus.org. The V2 section describes curriculum
> import, units and automatic scheduling — all removed on 26–27 August 2026. V2
> is now a hand-planned weekly planner.
>
> Rewrite before publishing. The V1 section and the overall voice still stand.

---

# Flokus Academy — site copy

Copy only. Hand to the flokus.org agent for integration. Written to match the
existing site voice: first person, short declarative sentences, concrete over
abstract, no hype adjectives, limits stated plainly.

Structure assumes one Academy tab holding all versions in sequence.

---

## TAB FRAME

**Eyebrow:** ACADEMY

**Heading:** One classroom, three versions.

**Standfirst:**
A learning management system built for exactly one classroom: mine. It's on its
second version, with a third already implied by the first two. Every version has
the same job — run a real school year while the next one is being built.

---

## V1 — IN PRODUCTION

**Status badge:** IN PRODUCTION · RUNNING SINCE AUGUST 2026

**Heading:** The version that runs the school day.

**Body:**

V1 is a Streamlit app on a SQLite file. It isn't the codebase I'd lead with. It's
the one that was finished in time for the first day of school, and a school year
doesn't wait for the good version.

It carries the whole Grade 5 year: 817 assignments across eight subjects,
thirty-eight weeks, one nine-year-old.

Most of the work wasn't features. It was reading the calendar as a whole instead
of a week at a time — which is when two things surfaced. The year had no breaks
in it: 180 straight weekdays, seventy assignments landing on holidays, three of
them on Christmas Day. And every math lesson sat in the first fifteen weeks, so
after 26 November there were twenty-one weeks with no daily math at all. Neither
is a bug you hit by using the app. You'd have found the first one on Christmas
morning and the second some time in February.

**Highlights:**

- **Curriculum is a spreadsheet, not a code change.** Three ways to add work
  became one importer — validated before anything is written, errors reported by
  sheet and row, and safe to re-import without duplicating the year.
- **The file never sets a date.** It says what to teach and in what order; the app
  schedules it against the school calendar. An import can't land on Christmas.
- **Seventeen automated checks**, each one a bug that actually happened. No work
  on a break day, no day over five assignments, every week contains real math, and
  a chapter is always read before the discussion about it.
- **Subtraction.** A countdown timer, a four-step ritual, a minimum character
  count before the checkbox would unlock, double-XP boss fights — all removed. An
  assignment is now three things: where the work is, a box to say what you
  learned, and a checkbox.
- **A full economics course**, 30 units and 120 lessons, extracted from the
  publisher's PDFs and paced one lesson per school day in publisher order.

**Stack:** PYTHON · STREAMLIT · SQLITE

**What it isn't:** Single user by construction. A PIN on the parent view and
nothing more. No hosting, no accounts, no multi-student support. Those are the
reasons V2 exists. They aren't reasons to have waited.

---

## V2 — IN BUILD

**Status badge:** IN BUILD

**Heading:** The one built to still be here in five years.

**Body:**

V1 proved what the thing actually needs to do. V2 is that, built properly: a real
API, a real database, migrations, and a curriculum model that separates the
lesson plan from one student's progress through it — so a year can be reused
without last year's history following it.

The import format is already shared. A curriculum file that loads into V1 loads
into V2 unchanged, which is the whole migration path.

V1 keeps running until V2 can take over a school day without anyone noticing the
change.

**Stack:** PYTHON · FASTAPI · POSTGRESQL · RAILWAY

---

## V3 — NOT STARTED

**Status badge:** NOT STARTED

**Heading:** Whatever V2 turns out not to solve.

**Body:**

There's no V3 yet, and I'd rather say that than sketch a roadmap I haven't earned.
V1 taught me the domain. V2 is teaching me the architecture. The third version
starts when I can name what's still wrong.

---

## NOTES FOR INTEGRATION

**One correction to carry over.** The current `academy.html` lists the stack as
PYTHON · FASTAPI · POSTGRESQL · RAILWAY. That describes V2. What's actually
running the school day today is Streamlit on SQLite. On a site whose premise is
honest labelling, the systems-index card should either say V1's stack or say
"V1 in production, V2 in build" — not V2's stack under an IN PRODUCTION badge.

**Reusable verbatim from the current page.** These lines still work and belong at
the tab level rather than under any one version:

- "I homeschool my son. Every system I looked at was built for a district —
  enrollment, sections, staff roles, state reporting — and none of that applies to
  a house with one student in it."
- "One family's records sit in one database with nothing else in it."
- "Academy runs for exactly one household — mine. If you'd want it for yours,
  leave an email and I'll tell you when it's ready."

**Systems-index card**, if the short version is wanted there:

> A learning management system built for exactly one classroom: mine. V1 runs the
> school day today — 817 assignments, eight subjects, thirty-eight weeks — while
> V2 is built to replace it without anyone noticing. My son uses it every day,
> which is the only reason it works.

**Numbers are verified** against the live database as of 18 August 2026 and are
safe to publish: 817 assignments · 8 subjects · 38 instructional weeks · 184
school days · 24 days off · max 5 assignments per day · 30 economics units /
120 lessons · 17 automated checks. The "before" figures — 677 assignments, 180
straight weekdays, 70 on holidays, 3 on Christmas Day, 21 weeks without math —
come from the original database, which is kept as a backup.

**Screenshots available** if the design calls for them: the student's day, the
curriculum importer, and the weekly schedule grid.
