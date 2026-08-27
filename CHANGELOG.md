# Changelog

What shipped in Flokus Academy, newest first. Both versions are logged here, because there is one
project and two versions of it — see [`README.md`](README.md).

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). Version headings are the
app's own; nothing here is a published package, so semantic versioning is a label rather than a
contract.

**Read this first:** V1 is the version that runs the school day. V2 is in development and has
never run one. An earlier revision of this file recorded V2 as a `2.0.0` release and V1 as
deprecated. Neither was true. That entry is kept below, corrected, with its date intact — see
*Corrections to this file* at the end.

---

## V1 — 2026-08-19 — the 2026–27 school year

The rebuild that made V1 fit to carry a real school year. Ran against the live database on
18 August; first day of school was 19 August 2026.

### Added

- **One way to get curriculum in and out** (`curriculum_io.py`). A spreadsheet goes in, a
  spreadsheet comes out. Validated before anything is written, errors reported by sheet and row,
  and safe to re-import without duplicating the year.
- **The school calendar in one place** (`school_year.py`), so the yearly rebuild and the importer
  cannot disagree about which days are school days. The import format never sets a date — it says
  what to teach and in what order, and the app places it.
- **A schedule audit** (`audit_schedule.py`), run after a rebuild — seventeen checks. Every one
  corresponds to a defect that was actually present, so it doubles as a regression test: no work
  on a break day, no day over five assignments, every week contains real math, a chapter is
  always read before the discussion about it.
- **Free Market Rules — economics**, 30 units and 120 lessons (`free_market_rules.py`), taken
  from the publisher PDFs with unit and lesson titles verbatim, paced one lesson per school day
  Mon–Thu.
- **Beast Academy Level 3** (`beast_level3.py`) — twelve chapters across books 3A–3D, six
  sittings each plus twelve capstones, 84 assignments in all. Authored to follow Level 2 so that
  math runs from the first day of the year to the last. Chapter titles are verified against Art
  of Problem Solving's own listing.

### Changed

- **Curriculum is data, not code.** It previously lived in hardcoded Python tables and could only
  be changed by editing source and redeploying.
- **The year is laid out against a calendar** rather than onto consecutive weekdays
  (`rebuild_schedule_2026_27.py`). 817 assignments across 38 instructional weeks, 184 school days,
  19 August 2026 → 4 June 2027, with 24 days off.
- **Friday is a review day**, distinct from the Mon–Thu core days: review, book parties and
  catch-up, never new material.
- **An assignment is three things** — where the work is, a box to say what you learned, and a
  checkbox.
- **Brilliant.org retired.** It held Tuesday and Thursday, the two heaviest days; freeing them is
  what let the 120-lesson economics course in without pushing the daily load past five.

### Removed

- A countdown timer, a four-step completion ritual, a minimum character count that had to be met
  before the checkbox would unlock, and double-XP boss fights.
- Three separate ways of adding work, replaced by the single importer above. The dangerous one
  regenerated the entire year in one click, on top of whatever was already there.

### Fixed

Three defects that only surface when you read the whole year at once rather than a week at a
time. All figures below are from `flokus.db.original-677-backup`.

- **The year had no breaks in it.** 677 assignments laid onto 180 consecutive weekdays from
  17 August 2026. Every one of the 24 days that are now breaks carried work — 87 assignments in
  total, three of them on Christmas Day.
- **Math stopped in November.** Every Beast Academy lesson sat in the first fifteen weeks. After
  26 November the only math left was the Friday review routine.
- **Friday was indistinguishable from a core day**, so new material landed on it.

---

## V1 — 2026-08-12 — gamification quarantined

### Removed

- The XP economy store, the digital pet (Sparky) and the battle/quest arena were extracted from
  the main app flow and moved to `research_and_development/gamification/`, ahead of the school
  year, for stability on day one. That directory documents how to put them back.

### Notes

- No data was dropped. `pet_status`, `pet_inventory`, `pet_unlocked_skills`, `pet_quests`,
  `side_quests` and `quest_completions` remain in `flokus.db`. XP is still carried on every lesson
  and still totals in the parent view; real-world reward claiming still works through the Finances
  admin view.

---

## V2 — unreleased

In development. Has never run a school day. V1 keeps running until V2 can take one over without
anyone noticing the change.

### 2026-08-27 (later still) — Days off, from the day itself

#### Added

- **Mark a day off from the planner**: click a day's heading to mark it off
  with an optional reason, or to turn it back into a school day. This had no
  home at all after the schedule screen was removed — the Calendar screen
  manages school events, a different thing — so a leftover sick day could not
  be cleared.

#### Fixed

- The planner's footnote claimed days off were set on the Calendar screen.
  They never were.

#### Notes

- A day off is now a marker, not a mechanism: it labels the column, and the
  work on that day stays put. Marking one tells you what is already there.
- **Start over** deliberately keeps the school calendar — days off are usually
  real facts about the year, and clearing student work should not erase them.

60 e2e tests pass.

### 2026-08-27 (later) — One screen to plan from

#### Added

- **Add and retire classes from the planner**: a `+ Add a class` row at the
  foot of the grid, a `-` on each class row, and hidden classes one click from
  coming back. Hiding deactivates, so finished work still counts.
- **Card editor**: click any card in the grid to set minutes, XP, type,
  whether it needs Dad, a link and notes. A partial update, so it cannot reset
  anything it does not show.
- **Start over** (Settings): `POST /api/maintenance/reset-curriculum` deletes
  every lesson, assignment, unit, XP entry and purchase, keeping classes,
  accounts, the calendar, UFA expenses and reward definitions. Requires the
  phrase `DELETE ALL WORK` typed in full, re-checked server-side.

#### Removed

- The **Classes** page and the **Task Manager** page, and `TaskForm.vue` with
  them — including the last legacy JSON bulk-import tab.

58 e2e tests pass.

### 2026-08-27 — The week planner; the importer and the rolling scheduler removed

The app stopped trying to manage curriculum and started helping plan a week.
One student with four or five items a day is fifteen lines of typing on a
Sunday — every mechanism built to avoid that typing cost more to operate than
the typing itself.

#### Added

- **Plan the Week** (`/admin/week`) — classes down the side, days across the
  top. Click a cell, type what Sonny does for that class that day. Days show
  their item count and total minutes, and mark themselves when overloaded.
- Unfinished work from before today appears in a strip above the grid, to be
  moved up or dropped — surfaced to an adult rather than piling up on a
  nine-year-old's morning.
- `POST /api/courses/{id}/clear-unstarted` and a **Clear unstarted** button:
  removes a class's planned-but-never-started work and keeps everything with
  completed history, XP included.
- `/api/week` — read a week, add an entry, move one, remove one.

#### Changed

- **Marking a day off no longer reschedules anything.** It reports what
  unfinished work falls on that day and leaves it where it is.
- Everything the planner creates is pinned to the day it was typed on.
- "Programs & Units" is now **Classes**; the admin home is the week planner.

#### Removed

- The curriculum importer: `/api/curriculum/*`, the import screen, the CSV
  pipeline and its `source_key` reconciliation. Four days old, and the wrong
  product.
- The rolling scheduler: `/api/schedule/recalculate`, `compute_rolling_schedule`
  and `reschedule_from_today`. What remains of the module is the school-week
  calendar, renamed `school_days.py`.
- The unit manager, the units store, and the unit picker on the task form.
  `Unit` stays in the database, unused and invisible — removing it would mean
  a migration across live completion history for no visible gain.

63 e2e tests pass, including one asserting that no recalculate endpoint exists.

### 2026-08-25 — Phase 2: the importer

The loading dock. A CSV exported from the curriculum workbook goes through
validate → preview → one-transaction commit, idempotently, so the spreadsheet
is now the thing the curriculum is maintained in all year.

- `POST /api/curriculum/validate` — parses with the stdlib `csv` module (BOM
  and CRLF from Excel handled), resolves programs and units **by name**, and
  reports errors keyed by spreadsheet row number. Zero new dependencies.
- `POST /api/curriculum/commit` — re-validates server-side, writes the whole
  file in one transaction with one flush, returns an `import_id`. Every
  assignment arrives staged: importing never sets dates.
- `POST /api/curriculum/rollback` — undoes one import exactly. Refuses if
  completed work exists under it; with `force`, reverses the earned XP through
  the append-only ledger before deleting.
- `Lesson.source_key` (unique per tenant, migration `e5a2b8d17c40`) makes
  re-import an update: an unchanged file is a no-op, a corrected one updates
  lessons without touching completion history, pins, or XP.
- The Import Curriculum screen: choose a CSV, preview with row-numbered
  errors fixable in place, commit disabled until clean, undo offered after.
- Also: choosing an unreleased unit on the task form now clears the default
  date (found by the production pilot on 2026-08-25 — see BUILD_LOG).
- 71 e2e tests pass; 5 new in `import.spec.js`, 1 in `curriculum.spec.js`.

### 2026-08-24 — Phase 1 reaches production; the repo becomes one branch

- All branches consolidated into `main`: `school-year-2026-27` already contained every commit
  from `main`, `feat/phase-1-curriculum-authoring` and the (already-merged)
  `hardening/phase-1-2-production-readiness`, so `main` was fast-forwarded to it and the two
  contained branches deleted.
- Deployed to Railway. The three Phase 1 migrations ran against Postgres for the first time —
  the oldest carried risk in `docs/BUILD_LOG.md` — via the pre-deploy `alembic upgrade head`
  step; `/health/ready` confirms `c3a91d4e2f70`.
- `docs/ROADMAP.md` added: the consolidation path from here to V2 running the school day.
- README corrected: the app hosts were serving V2 (pre-Phase-1) all along, not "nothing".
  Stale root `flokus.db` and two untracked walkthrough HTML files moved to `scratch/`.

### 2026-08-17 — Phase 1: curriculum authoring unblocked

- Program and unit managers in the admin UI, and a unit picker on the task form. The backend CRUD
  had existed for some time with no frontend caller.
- A partial `PUT /api/tasks/{id}` no longer resets the fields it did not mention.
- One `dependency_mode` vocabulary across all three layers.
- Calendar model: core, optional and blocked days, with hand-placed dates that stay put
  (`Assignment.date_locked`).
- The scheduler paces only `active` units, while still scheduling unit-less quick adds.
- Three Alembic migrations, chained off `17280a99fab3`; `alembic check` clean. 65 e2e tests pass.
- Carried risks recorded in [`docs/BUILD_LOG.md`](docs/BUILD_LOG.md): the migrations have never
  run against Postgres, and one completion spec flaked once.

Still to come: the manual pilot, the importer (Phase 2), the release model (Phase 3), extras
(Phase 4). The phase table in [`docs/BUILD_LOG.md`](docs/BUILD_LOG.md) is the live version of this.

### 2026-08-13 — the architecture

Originally logged as a `2.0.0` release. It was not a release — it was the point at which the V2
architecture existed and could be built on.

- A decoupled stack: Vue 3 frontend (Vite, Pinia, Vue Router) and FastAPI backend.
- Asynchronous endpoints, SQLAlchemy models, structured routing (`/auth`, `/courses`, `/tasks`,
  `/schedule`, `/ai_tutor`).
- Async PostgreSQL via `asyncpg`.
- Alembic migrations, CI that builds the migration chain from empty, Playwright e2e.

---

## Corrections to this file

- **2026-08-19.** The entry previously published as `[2.0.0] - 2026-08-13` described the V2
  architecture as a released version and listed the V1 Streamlit codebase as deprecated. V2 has
  not been released and V1 is not deprecated — it is the only version that works. The entry is
  preserved above under *V2 — unreleased*, with its date and contents intact and its status
  corrected. The V1 work for the 2026–27 school year had never been logged at all and has been
  added.
