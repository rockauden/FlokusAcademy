---
name: lms-architecture
description: Project context for Flokus Academy — a homeschooling LMS built as a Vue 3 SPA on a FastAPI/Postgres backend. Load this before making any change to the repo. Covers the domain model, the decisions already made and why, repo conventions, and the traps that have already bitten once.
---

# Flokus Academy

A homeschool learning management system for a single family, built to be a hub over many third-party curricula — Beast Academy, Tuttle Twins, Brave Writer, Critical Thinking Co., CrunchLabs, Brilliant.org, Chess.com — with the explicit requirement that programs can be swapped in and out mid-year without losing history.

**Stack:** Vue 3 + Vite + Pinia + Vue Router · FastAPI + SQLAlchemy 2.0 (async) + asyncpg + Postgres · Alembic · Playwright e2e · Railway deploy · Gemini via `google-genai` for the AI tutor.

**Users:** one teacher (`dad`, role `teacher`) and one student (`sonny`, role `student`), Grade 5, 2026–27. Multi-student is designed for but not yet exercised — the model supports it, some of the API does not yet.

---

## The domain model, and why it is shaped this way

```
Program          a subject/platform pairing — "Math — Beast Academy"
  └─ Unit        a block of lessons — "BA 2A", "Dart 3: Maya & Robot", "Build Boxes 1-3"
       └─ Lesson curriculum template. Carries NO student state.
            └─ Assignment   one row per (student, lesson). All student state lives here.
```

**The template/instance split is the most important thing in this codebase.** `Lesson` holds title, type, resources, XP value, estimated minutes. `Assignment` holds `scheduled_date`, `is_completed`, `focus_minutes`, `completion_notes`. That separation is what lets one lesson be assigned to two children at different paces, and reused next year without last year's completion history following it.

**Never put student state on `Lesson`.** Anything written to `assignment.lesson` changes shared curriculum for every student and every future year.

**API vocabulary lags the model deliberately.** The routes still say `courses` (= Program) and `modules` (= Unit), and the client still calls an Assignment a "task". This is documented at `routers/tasks.py:1–7` and `routers/modules.py:14`. Do not rename API paths as a drive-by; it is a separate, deliberate migration.

**XP is an append-only ledger** (`models.py:212`). Balance is `SUM(delta)`, never a stored counter. A reversal is a new row with the opposite delta — never an update or delete. `services/xp_service.py` has `award_xp`, `reverse_xp_for_source`, `compute_xp_balance`.

---

## Decisions already made — do not relitigate these

### The school week: Mon–Thu core, Fri/Sat/Sun optional

Three distinct concepts, not one:

| Day is | Definition | Auto-scheduler | Manual placement |
|---|---|---|---|
| **Core** | weekday ∈ `app_config.school_days` (Mon–Thu) | Places work | Allowed |
| **Optional** | Fri/Sat/Sun, not blocked | **Never** | Allowed — catch-up, make-up, Saturday co-op |
| **Blocked** | `SchoolCalendar.day_type != 'school_day'` | Never | Warn, but permit |

`school_days` belongs in `app_config`, not in code. `day_of_week_hint` accepts 0–6; a Fri/Sat/Sun hint is a deliberate statement, not an error. Hand-placed dates are marked `Assignment.date_locked` and the scheduler must skip them — without that flag a Saturday assignment silently moves to Monday the next time anyone adds a sick day.

`app_config` is read and written through `AppConfigRepository` and exposed at `/api/config/` (teacher-only, restricted to `school_days`, `academic_year_start`, `grade_level` — deliberately not a general key-value store). Each key validates on write; `school_days` **must**, because `get_school_days` searches day by day and a week with no days in it is an infinite loop.

`get_school_days` takes the week as an argument rather than reading it — the config is fetched once per recalculation and threaded down, so placing a lesson is not a database round trip.

**`date_locked` is explicit, never inferred.** It is a field on `TaskCreate`/`TaskUpdate` defaulting to false, driven by a "📌 Pin to this date" checkbox that starts unticked. Do not be tempted to infer it from "a `scheduled_date` was supplied" — that was tried and it pinned every quick add, because `TaskForm` defaults the date to today, leaving the scheduler unable to place any new work. A default is not an intent. Two invariants hold it together: a pin with no date is dropped on create, and clearing a date unpins on update, since the scheduler skips locked rows and would never place an undated locked one.

### Curriculum is authored, then staged, then released

```
AUTHOR  →  Program / Unit / Lesson exist
STAGE   →  Assignment exists, scheduled_date IS NULL, invisible to the student
RELEASE →  scheduled_date set; it appears in the student's day
```

An assignment with `scheduled_date = NULL` is *staged, not broken*. The day view already excludes it (`NULL <= today` is `NULL` in SQL). This is the feature that lets a full year be imported in August while the student's day stays a clean four cards.

The scheduler must only pace units with `status = 'active'`. That is what makes "release" a real action: import the year with every unit `planned`, flip one to `active`.

### A level change is new units, not a new program

Beast Academy Level 2 → 3 mid-year stays inside one "Beast Academy" Program, with Level 3 units imported ahead of time as `status: planned`. Splitting it into two Programs would fracture analytics, the portfolio, and the UFA record mid-year. `Unit.status` values: `planned` | `active` | `completed` | `abandoned`.

### `priority` changes pace without changing curriculum

`Lesson.priority` is `core` | `standard` | `optional` (default `standard`). Accelerating means **releasing `core` only** and leaving the rest unreleased — never deleting. For Beast Academy: guide chapter = core, practice book = standard, puzzlers = optional.

The column, the `LessonPriority` literal and the task-form field landed in Phase 1 so the form could offer it; release-*by* priority is Phase 3. `source_key` and `import_id` are still to come with the importer.

### A routine is a slot; the platform is an attribute of the slot

Anything that repeats weekly with the same title is a *routine*, not curriculum. In the v1 data, 412 of 684 rows were 14 habits. Chess.com appeared as 89 near-identical lesson rows; Brilliant.org as 72.

Synthesis and Brilliant are an explicit swap pair — same Tue/Thu online slot, different platform behind it. Model routines so two definitions can share a slot with one active: switching platforms is then a toggle, not a re-authoring.

### One bulk ingest path, one single-item path

**Bulk:** a CSV exported from a per-program spreadsheet → server-side validate with row-numbered errors → editable preview → atomic commit. Idempotent via `Lesson.source_key` = `slug(program)|slug(unit)|slug(title)`, unique per tenant, so re-importing a corrected file *updates* rather than duplicating.

**Single:** the existing task form, plus unit picker, `priority`, and a date that sticks.

An earlier draft proposed also parsing pasted outlines and publisher PDFs. **Both were cut as over-built.** PDF extraction needs human review regardless, so it happens outside the app and arrives as a spreadsheet. Do not add a third ingest path.

**Importing never sets dates.** There is no `scheduled_date` column in the import format. Dates belong to release.

---

## Repo conventions

**Comment style.** This codebase explains *why*, not *what*, above anything non-obvious — often several sentences naming the failure that motivated the code. Match it. Terse code with no rationale is out of place here.

**Tenant isolation.** `repository.py` opens with: *"Rule for anything added here: the first `.where()` clause is the tenant."* No bare `select(Model)` in routers — everything goes through a repository method taking `tenant_id`. Postgres row-level security is the backstop; the repository layer is the primary guard.

**Dependencies are pinned exactly and kept minimal.** `pandas` and `aiofiles` were deliberately removed (`requirements.txt` explains why). Parse CSV with the stdlib `csv` module — `routers/expenses.py:2` already does. Adding a dependency needs a real justification.

**Migrations.** Every schema change gets an Alembic migration. A boolean `server_default` must use the SQLAlchemy construct (`sa.true()` / `sa.false()`), not a Python literal — commit `76ed5c9` fixed exactly that Postgres rejection. Match the model's `server_default` so `alembic check` stays clean.

**Health endpoints are split on purpose.** `/health` is liveness and must never touch the database — Railway restarts on failure, so a DB blip would become a crash loop. `/health/ready` checks the database and reports the applied Alembic revision.

**Errors.** Unhandled exceptions return a request id and nothing else; exception text routinely carries connection strings. The client surfaces `X-Request-ID` so a user-visible failure can be found in the logs.

**Tests.** `npm run test:e2e` in `frontend/` (Playwright, builds a throwaway SQLite database). Run it before declaring anything done.

---

## Traps that have already bitten

1. **Trailing slashes.** `/api/tasks/`, `/api/courses/`, `/api/modules/`. Without one FastAPI 307s to an absolute URL; behind the TLS-terminating proxy that returned `http://` and the browser blocked it as mixed content. Quick-add silently did nothing. See `stores/tasks.js:60–66`.

2. **`AssignmentRepository.list(..., unit_id=None)` means "no filter", not "unit is null".** `tasks.py:281` relies on this to scan every assignment in the tenant.

3. **Blank form inputs arrive as `''`**, which fails `Optional[date]` / `Optional[int]` validation with a 422. `TaskForm.vue:48` keeps a `NULL_WHEN_BLANK` list.

4. **`model_dump()` returns defaults for unset fields.** *Fixed in Phase 1.* This was live data loss in `update_task` — a partial PUT reset `xp_reward`, `estimated_minutes`, `task_type` and `scheduled_date`. `TaskUpdate` no longer inherits `TaskBase` and the router uses `exclude_unset=True`. The distinction that still needs care anywhere this pattern recurs: "field absent" is not "explicitly null", and `exclude_unset` alone cannot tell them apart — check for the key, not the value.

5. **`dependency_mode` has three spellings across three layers.** *Fixed in Phase 1.* The form said `with_teacher`, the scheduler handled `teacher_led`, and the schema typed it as a bare `str` so nothing caught it. Now a `Literal` in `schemas.py` (`DependencyMode`), migrated in `b2f5083ac611`, with a loud `else` in the scheduler. Canonical: `independent` | `teacher_led` | `live_scheduled`.

6. **The rolling scheduler runs more often than you think.** `routers/schedule.py` fires a full-tenant `reschedule_from_today` on add-sick-day (`:26`), add-holiday (`:34`) and delete-calendar-entry (`:54`) — not only on the Recalculate button.

7. **The student's day has no ceiling.** `repository.py:59–66` returns everything where `is_completed = False AND scheduled_date <= today`. Nothing outstanding ever falls off. Needs a configurable cap plus a catch-up policy.

8. **`resource_path` is dead weight.** There is no upload endpoint and no `StaticFiles` mount; `aiofiles` was removed in H-06. Don't wire it up incidentally.

---

## Non-negotiables

- **The student side stays calm.** It is used by one nine-year-old. No wall of overdue cards, no jargon, no crash screen for an ordinary expired session. Loading states must not assert something false — "you have 0 tasks left" before the answer is known is worse than a skeleton.
- **Safety and stuck-flags are different things.** `SafetyEvent` is for disclosures needing a parent now; `StuckFlag` is for "stuck on long division". Never merge the lists — it blunts the one that must never be missed.
- **COPPA consent is a record, not a boolean.** Withdrawal is a new row.
- **No 3D rendering or game-engine logic.** Gamification is XP, streaks, pets and rewards — presentation only.
- **Earned XP stays earned.** Archiving a program, abandoning a unit or swapping a platform must never reverse a child's ledger for work genuinely done.

---

## Where the detail lives

- `docs/Flokus_Academy_Curriculum_Review.md` — full architecture review, the ingest spec, the phased build order (B1–B10 are the numbered defects)
- `docs/PHASE1_BRIEF.md` — the current work: six items with acceptance criteria
- `research_and_development/Flokus_Curriculum_v1_Migrated.xlsx` — the 2026–27 curriculum, migrated from v1: 272 lessons + 14 routines
