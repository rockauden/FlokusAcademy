# Flokus Academy — Build Log

**This file is the running state of the curriculum rebuild.** Every Claude Code session reads it first and updates it last. It is the only thing that survives between sessions — a session's own todo list does not.

- **Plan:** `research_and_development/Flokus_Academy_Curriculum_Review.md` (defects are numbered B1–B10; build order is §9)
- **Project context:** `.agents/skills/lms-architecture/SKILL.md` — load before any change
- **Curriculum to load:** `research_and_development/Flokus_Curriculum_v1_Migrated.xlsx` — 272 lessons, 30 units, 14 routines

---

## How to use this file

**At the start of a session:** read this file, then the skill, then the brief for the phase you are on.

**At the end of a session:** update the phase table, and append to *Decisions changed in flight* anything you did differently from the plan and why. A deviation is fine; a silent deviation is not — the next session will read the plan and assume it still holds.

**When a phase completes:** write the next phase's brief into `research_and_development/PHASE<N>_BRIEF.md` using the review doc §5–§9 as the source, and the Phase 1 brief as the format. Then stop and let it be reviewed before building. Writing the brief is a separate act from executing it, deliberately — the shape of each phase depends on what the last one turned up.

---

## Phase table

| Phase | What | Status | Branch | Brief |
|---|---|---|---|---|
| **1** | Unblock authoring — Program/Unit UI, unit picker, TaskUpdate fix, dependency_mode, calendar model, scheduler unit-status guard | ✅ Done | `feat/phase-1-curriculum-authoring` | `PHASE1_BRIEF.md` ✅ |
| **Pilot** | Hand-enter Tuttle Twins Vol 1 through the new UI; verify unit gating survives a sick day | ⬜ Ready to start | — | — |
| **2** | The importer — canonical CSV schema, `source_key`, `priority`, validate/commit, preview screen | ⬜ Blocked on Pilot | `feat/phase-2-curriculum-import` | to write |
| **Load** | Import the workbook subject by subject, all units `planned` except the current one | ⬜ Blocked on 2 | — | — |
| **3** | Protect the student side — author/assign/release split, day cap, recurring routines, release-by-priority, unassign | ⬜ Blocked on Load | `feat/phase-3-release-model` | to write |
| **4** | Extras — BA Level 3 units as `planned`, `grade_level` on the portfolio | ⬜ | — | to write |

Status values: ⬜ Not started · 🟡 In progress · ✅ Done · ⚠️ Done with deviations (see below)

---

## Phase exit criteria

Do not mark a phase done until these hold. They are the things a later phase silently depends on.

**Phase 1** — all met, 2026-08-17.
- ✅ A program and its units can be created, edited and deactivated from the admin UI — `/admin/programs`, with the unit panel nested under it
- ✅ A lesson can be attached to a unit from the task form — `curriculum.spec.js` *a lesson created through the form carries its unit*
- ✅ A partial `PUT /api/tasks/{id}` leaves unsent fields untouched — `scheduling.spec.js` *sending only a title does not reset xp, duration or date*, plus *an explicit null still clears the date*
- ✅ The scheduler paces only `active` units, but still schedules unit-less quick-adds — `curriculum.spec.js` *planned units stay undated while the active one is scheduled*
- ✅ A hand-placed Saturday assignment survives a sick-day recalculation — `scheduling.spec.js` *a hand-placed Saturday survives a sick day*
- ✅ `school_days` reads from `app_config`; `day_of_week_hint` accepts 0–6 — `scheduling.spec.js` *the school week is configuration: adding Friday changes where work lands* and *a Saturday day_of_week_hint is honoured, not rejected*
- ✅ An unpinned quick add is still the scheduler's to move — `scheduling.spec.js` *an unpinned quick add is the scheduler's to move*
- ✅ `npm run test:e2e` passes — 65 tests, 14 of them new; `/health/ready` reports `c3a91d4e2f70`

Migrations added, chained off `17280a99fab3`:
`a1c4e7b9d203` calendar model (`assignments.date_locked`, the three `app_config` rows) →
`b2f5083ac611` dependency_mode data migration →
`c3a91d4e2f70` `units.status` + `lessons.priority`. `alembic check` is clean.

Both carried risks are recorded under *Known open questions* rather than here:
the migrations have never run on Postgres, and one completion spec flaked once.

**Pilot** *(no code — this is a manual check that Phase 1 actually works)*
- Tuttle Twins created with 4 units, Vol 1 `active`, Vols 2–3 `planned`
- Add a sick day. Only Vol 1's assignments moved. Vols 2–3 still have `scheduled_date IS NULL`
- The student view shows only Vol 1 work

**Phase 2**
- Re-importing an unchanged CSV is a no-op; re-importing a corrected one updates without touching completion history or XP
- A malformed row reports *its row number*, not a bare 422
- Commit is one transaction, one flush — not one flush per row
- Import of the full workbook completes and the student's day is still empty (everything `planned`)

**Phase 3**
- Authoring a lesson no longer auto-assigns it to every student
- The student's day is capped and shows oldest-first catch-up beyond the cap
- Releasing `core` only produces a shorter unit than releasing everything — the acceleration path works
- Unassigning a lesson from one student leaves the lesson and other students intact

---

## Decisions changed in flight

*Append here. Date, what changed, why. Empty is the correct state at the start.*

<!--
Example:
### 2026-08-22 — Unit.status gained a fifth value
Added `paused` alongside planned/active/completed/abandoned. `abandoned` implied
permanence and there was no way to say "stopped for now, may resume". Review doc
§5.8 and the skill both updated.
-->

### 2026-08-17 — `Lesson.priority` landed in Phase 1, so Phase 2 item 8 is now partly done

The phase table assigns `priority` to Phase 2 alongside `source_key`, but brief
item 3 says to add it to the task form. A form field posting a value the API
drops is worse than no field, so the column, the `LessonPriority` literal and
the migration came with it.

**Read Phase 2's item 8 as partly done when writing that brief.** Review §9 item
8 is "`source_key` + `priority` + unique constraint + Alembic migration"; the
`priority` third of it is shipped, in `c3a91d4e2f70`. What is left of item 8 is
`source_key`, `import_id` and `UniqueConstraint('tenant_id', 'source_key')` —
those only earn their keep with the importer, so they were deliberately not
pulled forward. Release-*by*-priority is still Phase 3 item 14, untouched.

### 2026-08-17 — A small `app_config` API, which the brief did not list

Item 6's last acceptance criterion is "changing `school_days` to include `Fri`
makes the scheduler use Fridays, with no code change". Nothing could change it:
`app_config` had no reader and no writer. Added `routers/app_config.py` —
`GET /api/config/` and `PUT /api/config/{key}`, teacher-only, restricted to the
three keys the review names rather than being a general key-value store.

Each key validates on write. `school_days` in particular *has* to: `get_school_days`
searches day by day for a match, so a week that parses to no days is an infinite
loop that hangs the worker. Refusing it at write time is the only place that
failure is cheap. The module is `app_config.py` rather than `config.py` because
`app/config.py` is already the environment-and-secrets module.

No settings screen yet — the API exists, the UI does not. Worth adding when
`grade_level` gets a reader in Phase 4.

### 2026-08-17 — `date_locked` is explicit, after a first attempt that inferred it

The brief says to set it "whenever a date is placed by hand" without saying how.
The first cut inferred it: any `scheduled_date` in a request body locked the
assignment. **That was wrong, and wrong in a way worth remembering.** `TaskForm`
defaults the date to today, so the inference pinned every quick add ever made —
the rolling scheduler could no longer place any new work at all, and nothing
would have said so. A default is not an intent.

Shipped instead: `date_locked` is an explicit field on `TaskCreate` and
`TaskUpdate`, defaulting to false, with a "📌 Pin to this date" checkbox on the
form that starts unticked. Two rules keep it coherent — a pin with no date to
pin to is dropped on create, and clearing a date unpins on update, because the
scheduler skips locked rows and would never place an undated locked one.

Covered from both sides now: *a pinned Saturday survives a sick day* and *an
unpinned quick add is the scheduler's to move*, the second driven through the
real form because the form's default is precisely what made the inference wrong.

Phase 3's release model still owns this properly, and should revisit whether the
form should default the date at all.

### 2026-08-17 — `include_inactive` on the courses and modules list endpoints

The brief says the programs backend is complete and needs no change. It is,
except for one gap the UI exposes: `DELETE /api/courses/{id}` deactivates rather
than deletes, and `GET /api/courses/` returns active rows only — so a
deactivated program vanished from the only screen that could bring it back, and
the undo became a database edit. Both list endpoints now take
`include_inactive`, defaulting to false so every picker is unchanged.

The unit manager deliberately has **no delete**. `DELETE /api/modules/{id}`
really deletes, and `Lesson.unit_id` is `ON DELETE SET NULL` — so removing a
unit silently returns its lessons to the unit-less pool the scheduler
mishandles, which is the exact damage item 2b exists to prevent. Deactivating is
offered instead.

### 2026-08-17 — Unknown `dependency_mode` logs rather than raises

Item 5 says the scheduler's `else` should "raise or log loudly". It logs, at
ERROR, naming the lesson, and skips the assignment **without advancing the
school-day cursor** — the cursor advance was the second half of the original bug,
where a `with_teacher` lesson got no date and still burned a slot. Raising would
abort the whole tenant's recalculation over one legacy row, and `reschedule_from_today`
is fired by adding a sick day, so that failure would surface as an unrelated
action breaking.

### 2026-08-17 — `get_school_days` takes the school week as an argument

The brief says `get_school_days` should read `school_days` from `app_config`. It
takes it as a parameter instead, defaulting to Mon–Thu; `reschedule_from_today`
and `/schedule/school-days` each read the config once and pass it down. Reading
it inside the function would mean a database round trip per lesson placed and
would make a pure function async. Same single source of truth, one read per
recalculation.

`academic_year_start` replaced the `SchoolEvent.title.ilike('%First day%')`
lookup as briefed. Worth knowing: **`anchor_date` is not actually used by
`compute_rolling_schedule`** — it takes the parameter and never reads it. Left
alone rather than removed, but the fragile lookup it came from is gone.

### 2026-08-17 — A `backend-throwaway` entry in `.claude/launch.json`

There is no `backend/.env`, so the API cannot be booted locally the ordinary
way, which makes the app impossible to click through. Added a launch entry that
runs `scripts/run_test_api.py` on :8000 — the same throwaway SQLite database the
e2e suite builds. It is not a development backend and holds no real data.

---

## Known open questions

Things deliberately left undecided. Answer them when they become blocking, not before.

- **Multi-student.** The model supports it; parts of the API do not (`_assign_to_students` fans out to everyone; `create_task` returns only the first assignment). Phase 3 fixes the fan-out. Full multi-student is not otherwise scheduled.
- **Routine cadence granularity.** The 14 migrated routines are all weekly on a fixed weekday. Whether `daily` and `biweekly` are needed is a Phase 3 question.
- **`resource_path` / file attachments.** Dead field, no upload endpoint by design. Only revisit if worksheets need attaching to lessons — and treat it as its own feature, not part of ingest.
- **Beast Academy Level 3 timing.** Units get imported as `planned` in Phase 4; when to activate them is a teaching decision, not a build one.

- **The Phase 1 migrations have never run on Postgres.** There is no local
  Postgres, so `a1c4e7b9d203` → `b2f5083ac611` → `c3a91d4e2f70` have only been
  exercised on SQLite (`alembic check` clean, chain applies from scratch). The
  two that write data bind `app.tenant_id` first, because `app_config` and
  `lessons` both carry `FORCE ROW LEVEL SECURITY` and the policy doubles as the
  `WITH CHECK` on INSERT — without it the inserts are rejected outright and the
  `dependency_mode` UPDATE matches zero rows *while still reporting success*.
  That reasoning is sound and untested. **Settle it the cheap way:**
  `curl -s https://api.flokusacademy.com/health/ready` after the deploy should
  report `c3a91d4e2f70`; then confirm `school_days` came back from
  `GET /api/config/` rather than falling through to the Mon–Thu default, which
  is what a silently-skipped insert would look like. Precedent says this is a
  real risk, not a theoretical one — commit `76ed5c9` fixed a Postgres-only
  `server_default` rejection that SQLite had happily accepted.

- **`completion.spec.js` *XP counts up to the amount actually awarded* flaked
  once.** One failure in nine full runs; the other eight were clean, including
  the last three at 65/65. It polls an animated counter with a 10s budget
  against a database every other spec writes to, which is enough to explain it,
  and nothing in Phase 1 touches completion or the XP ledger. Not chased down.
  If it recurs, the likely fix is to read the value only after the count-up
  settles rather than to widen the timeout — a longer timeout would hide a real
  regression in the same place. (The other failure seen during the work was a
  genuine race in a new spec of mine, fixed with `waitForResponse`, not a flake.)
