---
name: lms-architecture
description: Project context for Flokus Academy — a homeschooling LMS built as a Vue 3 SPA on a FastAPI/Postgres backend. Load this before making any change to the repo. Covers what the app is, what was deliberately removed and why, repo conventions, and the traps that have already bitten once.
---

# Flokus Academy

A learning management system for exactly one classroom: one teacher (`dad`), one
student (`sonny`), Grade 5, 2026–27. It is a hub over third-party curricula —
Beast Academy, Brave Writer, Tuttle Twins, Critical Thinking Co., Chess.com,
CrunchLabs, Outschool — not a curriculum of its own.

**Stack:** Vue 3 + Vite + Pinia + Vue Router · FastAPI + SQLAlchemy 2.0 (async) +
asyncpg + Postgres · Alembic · Playwright e2e · Railway deploy · Gemini via
`google-genai` for the AI tutor.

---

## Read this before proposing anything

**This app got smaller on purpose, three times in three days, and the reasons
are the most important thing in this file.** An earlier version of this document
described a curriculum-management system: units, staged-and-released work, a CSV
importer with idempotency keys, per-unit pacing rhythms, and a rolling scheduler
that placed every lesson automatically. All of it was designed carefully, built,
tested, deployed — and then removed on 2026-08-26 and 2026-08-27, because the
household it was built for does not have the problem it solved.

The arithmetic that settled it: **one student doing four or five things a day is
about fifteen lines of typing on a Sunday.** Every mechanism that existed to
avoid that typing cost more attention to operate than the typing it replaced.

So the governing rule for this repo:

> **Volume justifies machinery. Fifteen items a week does not.**
> Before designing anything, ask what this household actually does — not what
> would help if it did ten times more.

Do not propose, and do not rebuild: a curriculum importer of any kind, unit
staging and release, per-unit rhythms or day-of-week pacing, or automatic
scheduling and rescheduling. They are not missing. They were removed. The full
account is in `docs/BUILD_LOG.md` under *one week at a time*, *one screen*, and
*days off had nowhere left to live*.

---

## How the app works now

The teacher plans **one week at a time, by hand**, on a Sunday. That is the whole
workflow, and `/admin/week` is very nearly the whole app.

```
Plan the Week  →  classes down the side, Mon–Fri across the top
                  click a cell, type what Sonny does, press Enter
                  click a card to edit it, click a day heading to mark it off
```

Everything else in the admin is monitoring or operations: Calendar (school
events), Creator Projects, Portfolio, Analytics, UFA Finances, Settings.

### The data model, and what is live in it

```
Program      a class — "Beast Academy". The teacher's word is "class";
             the API still says `courses`.
  └─ Lesson  one piece of work. Carries no student state.
       └─ Assignment   one row per (student, lesson). All student state.
```

**The template/instance split still matters and must be preserved.** `Lesson`
holds title, type, minutes, XP. `Assignment` holds `scheduled_date`,
`is_completed`, `focus_minutes`, `completion_notes`, `date_locked`. Never write
student state onto `Lesson` — it is shared, and in a multi-student future it
would leak one child's progress onto another's.

**`Unit` still exists in the database and is unused.** So are
`Lesson.source_key`, `Lesson.import_id` and their unique index, plus
`routers/modules.py`. They were kept rather than dropped because removing them
means a migration across live data holding real completion history, for no
behaviour anyone would notice. Leave them alone. Do not wire them back up.

Also dormant, for the same reason: `day_of_week_hint`, `priority`,
`school_day_offset`, `sequence_order`, `dependency_mode` beyond its label on the
card editor, and `resource_path` (which never had an upload endpoint —
`aiofiles` was deliberately removed in H-06).

**XP is an append-only ledger** (`models.py`). Balance is `SUM(delta)`, never a
stored counter. A reversal is a new row with the opposite delta — never an update
or a delete. `services/xp_service.py` has `award_xp`, `reverse_xp_for_source`,
`compute_xp_balance`.

---

## Decisions that are settled — do not relitigate

### Nothing moves work the teacher placed

There is no rolling scheduler, and `/api/schedule/recalculate` does not exist.
Marking a sick day or a holiday **reports** what unfinished work falls on that
day and changes nothing. Every entry the planner creates is `date_locked`.

A date the teacher typed is a decision; an app that quietly revises it is an app
he cannot plan in. `scheduling.spec.js` asserts that no recalculate endpoint
exists, precisely so that reintroducing one has to be a deliberate act with a
failing test in front of it.

A day off is therefore **a marker, not a mechanism**: it greys the column and
says why.

### One screen, and edits happen where the thing is

The class manager and task manager were removed because each held something the
planner holds better in place. Adding a class, renaming it, hiding it, editing a
lesson's details, marking a day off — all of it happens on the grid. **A feature
that would send the teacher to a second screen on a Sunday evening has failed.**

Corollary: a cell takes a title and nothing else. Minutes, XP and type have
defaults that are right often enough; the card editor exists for when they are
not.

### Hiding is not deleting

`DELETE /api/courses/{id}` deactivates. A class the household stopped teaching
still owns completed work the UFA record needs. Hidden classes stay one click
from returning on the planner, because there is no longer a screen to go back to.

`POST /api/courses/{id}/clear-unstarted` deletes only lessons where **no student
has completed anything** — the escape hatch for an abandoned plan that cannot
touch history.

### The reset is guarded, and keeps the calendar

`POST /api/maintenance/reset-curriculum` deletes every lesson, assignment, unit,
XP entry and purchase. It keeps classes, accounts, the school calendar, UFA
expenses and reward definitions. It requires the phrase `DELETE ALL WORK` typed
in full, re-checked server-side — a checkbox is one stray click from destroying a
year of records.

It exists because the alternative was talking a first-time developer through
Railway's CLI and psql to run DELETEs against production by hand.

### Gamification is parked

XP is still earned, tracked and shown. The store, the pet and the arena live in
`research_and_development/gamification/` and stay there until the owner asks.
When they come back: presentation only, no game-engine logic, and **earned XP
stays earned** — archiving, hiding or resetting a class must never reverse a
child's ledger for work genuinely done.

---

## Repo conventions

**Comment style.** This codebase explains *why*, not *what*, above anything
non-obvious — often several sentences naming the failure that motivated the
code. Match it. Terse code with no rationale is out of place here.

**Tenant isolation.** `repository.py` opens with: *"Rule for anything added here:
the first `.where()` clause is the tenant."* No bare `select(Model)` in routers —
everything goes through a repository method taking `tenant_id`. Postgres
row-level security is the backstop; the repository layer is the primary guard.

**Dependencies are pinned exactly and kept minimal.** `pandas` and `aiofiles`
were deliberately removed. Adding a dependency needs a real justification.

**Migrations.** Every schema change gets an Alembic migration. Current head is
`e5a2b8d17c40`. A boolean `server_default` must use the SQLAlchemy construct
(`sa.true()` / `sa.false()`), not a Python literal — commit `76ed5c9` fixed
exactly that Postgres rejection. Match the model's `server_default` so
`alembic check` stays clean. SQLite cannot ALTER a constraint onto an existing
table, so prefer a unique **index** where both engines must agree.

**Health endpoints are split on purpose.** `/health` is liveness and must never
touch the database — Railway restarts on failure, so a DB blip would become a
crash loop. `/health/ready` checks the database and reports the applied Alembic
revision.

**Errors.** Unhandled exceptions return a request id and nothing else; exception
text routinely carries connection strings. The client surfaces `X-Request-ID`.

**No `alert()` / `confirm()`.** Destructive actions arm on a first click and
confirm on a second, or require a typed phrase.

**Tests.** `npm run test:e2e` in `frontend/` (Playwright, builds a throwaway
SQLite database). 61 passing. Run it before declaring anything done.

---

## Traps that have already bitten

1. **Trailing slashes.** `/api/tasks/`, `/api/courses/`, `/api/week/`. Without
   one FastAPI 307s to an absolute URL; behind the TLS-terminating proxy that
   returned `http://` and the browser blocked it as mixed content. Quick-add
   silently did nothing. See `stores/tasks.js:60–66`.

2. **`toISOString()` for a local date** returns yesterday for anyone west of
   Greenwich in the evening. Use the `isoDate()` / `todayISO()` pattern. This
   shipped once in the old weekly grid.

3. **`model_dump()` returns defaults for unset fields.** This was live data loss
   in `update_task` — a partial PUT reset `xp_reward`, `estimated_minutes`,
   `task_type` and `scheduled_date`. Use `exclude_unset=True`, and distinguish
   "field absent" from "explicitly null".

4. **Blank form inputs arrive as `''`**, which fails `Optional[date]` /
   `Optional[int]` validation with a 422. Normalise before sending.

5. **A row locator that filters on text stops matching when that text becomes an
   input.** Bit the rename spec. Locate the input at page level when only one can
   be open.

6. **`/analytics/summary` always reports the calling user's own XP.** Read it as
   the student, or a teacher-side assertion passes while proving nothing. Switch
   roles with `logout()` first — the router sends an authenticated visitor
   straight past `/login`.

---

## Non-negotiables

- **The student side stays calm.** It is used by one nine-year-old. No wall of
  overdue cards, no jargon, no crash screen for an ordinary expired session.
  Loading states must not assert something false — "you have 0 tasks left"
  before the answer is known is worse than a skeleton.
- **Safety and stuck-flags are different things.** `SafetyEvent` is for
  disclosures needing a parent now; `StuckFlag` is for "stuck on long division".
  Never merge the lists — it blunts the one that must never be missed.
- **COPPA consent is a record, not a boolean.** Withdrawal is a new row.
- **Earned XP stays earned.**
- **Never put student state on `Lesson`.**

---

## Where the detail lives

- `docs/BUILD_LOG.md` — **the running state, and the only doc kept current.**
  Read it first. Its *Decisions changed in flight* section is the record of what
  changed and why.
- `CHANGELOG.md` — what shipped, dated, both versions.
- `README.md` — the front door: what runs where, and how to start it locally.
- `docs/` also holds superseded documents, each labelled as such at the top.
  They are history, not instructions — the curriculum review and the three phase
  briefs describe an architecture that was built and then removed.
