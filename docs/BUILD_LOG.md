# Flokus Academy — Build Log

**This file is the running state of the curriculum rebuild.** Every Claude Code session reads it first and updates it last. It is the only thing that survives between sessions — a session's own todo list does not.

- **Plan:** `docs/Flokus_Academy_Curriculum_Review.md` (defects are numbered B1–B10; build order is §9)
- **Project context:** `.agents/skills/lms-architecture/SKILL.md` — load before any change
- **Curriculum to load:** `research_and_development/Flokus_Curriculum_v1_Migrated.xlsx` — 272 lessons, 30 units, 14 routines

---

## How to use this file

**At the start of a session:** read this file, then the skill, then the brief for the phase you are on.

**At the end of a session:** update the phase table, and append to *Decisions changed in flight* anything you did differently from the plan and why. A deviation is fine; a silent deviation is not — the next session will read the plan and assume it still holds.

**When a phase completes:** write the next phase's brief into `docs/PHASE<N>_BRIEF.md` using the review doc §5–§9 as the source, and the Phase 1 brief as the format. Then stop and let it be reviewed before building. Writing the brief is a separate act from executing it, deliberately — the shape of each phase depends on what the last one turned up.

---

## Phase table

| Phase | What | Status | Branch | Brief |
|---|---|---|---|---|
| **1** | Unblock authoring — Program/Unit UI, unit picker, TaskUpdate fix, dependency_mode, calendar model, scheduler unit-status guard | ✅ Done | `feat/phase-1-curriculum-authoring` (merged) | `PHASE1_BRIEF.md` ✅ |
| **Pilot** | Hand-enter Tuttle Twins Vol 1 through the new UI; verify unit gating survives a sick day | ✅ Done 2026-08-25 | — | — |
| **2** | The importer — canonical CSV schema, `source_key`, validate/commit, preview screen | ✅ Done 2026-08-25 | `feat/phase-2-curriculum-import` | `PHASE2_BRIEF.md` ✅ |
| **Load** | Import the workbook subject by subject | ❌ Abandoned. One subject went in; the workflow was then removed entirely. See *one week at a time* below. |  — | — |
| **2** | The importer | ❌ **Removed 2026-08-26**, four days after it shipped. Working code, wrong product. | — | `PHASE2_BRIEF.md` (historical) |
| **3** | **The week planner** — type a week into a grid; nothing auto-places, nothing auto-moves | ✅ Done 2026-08-27 | `feat/weekly-planner` | `PHASE3_BRIEF.md` (superseded mid-flight — see below) |
| **4** | Sonny's side: the day cap he sees, and whatever the friction interview turns up | ⬜ Next | — | to write |

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

**Pilot** — run against production 2026-08-25, and it earned its keep twice.
- ✅ Tuttle Twins created with units; Vol 1 `active`, the rest `planned`
- ✅ A sick day moved only the active unit's dated work; staged lessons stayed `scheduled_date IS NULL`
- ✅ The student view showed only released work
- **Finding:** lessons authored into planned units *appeared in the student's day anyway*,
  because the task form's date field defaults to today and a form-set date bypasses the
  scheduler's unit-status gate entirely — two doors, one gate. Fixed in `91ad860`
  (see *Decisions changed in flight*), verified in production, covered by a new e2e spec.
- The `GET /api/config/` `school_days` check also passed implicitly: the scheduler used
  Mon–Thu placement and honoured the calendar, and the config API served the admin UI.

**Phase 2** — all met, 2026-08-25. `npm run test:e2e`: 71 passed, 5 new in `import.spec.js`.
- ✅ Re-importing an unchanged CSV is a no-op; a corrected one updates without touching completion history or XP — *re-importing an unchanged file is a no-op* and *a corrected re-import updates the lesson without touching completion history*
- ✅ A malformed row reports *its row number* — *a malformed row blocks commit, names its row, and is fixable in place*, driven through the real screen with an Excel-style BOM + CRLF fixture
- ✅ Commit is one transaction, one flush — new rows are wired through relationships (`lesson=`, `program=`, `unit=`) so the whole graph resolves in a single `flush()`; the router owns the commit
- ✅ Imported assignments arrive staged (`scheduled_date IS NULL`, unpinned) — *the year arrives staged*
- Rollback shipped alongside: refuses when completed work exists (409 naming the lessons), reverses XP through the ledger under `force` — *rollback undoes a fresh import, refuses completed work, reverses XP under force*
- The Load step remains: run the real workbook through it, subject by subject

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

### 2026-08-27 (later still) — Days off had nowhere left to live

Found by the owner within minutes of using the reset: a sick day from the
pilot survived it and could not be removed.

Two separate things, and only one was a bug.

**Not a bug:** the reset keeps `school_calendar` on purpose. Days off are
ordinarily real facts about the year — Thanksgiving, a trip — and a button
that clears student work should not also erase the calendar. That is what the
option said it would do, and it did it.

**The bug, and it was mine:** deleting `ScheduleView.vue` with the scheduler
took away the only place days off could be added or cleared, and the planner's
own footnote pointed at the Calendar screen — which manages `school_events`, a
different table entirely. So the UI described a route that had never existed.
A leftover pilot sick day was simply unreachable.

Fixed by putting days off where they are actually learned about: **click a
day's heading in the planner** to mark it off, with an optional reason, or to
make it a school day again. `/api/week` now returns each day-off's `id` so the
planner can clear one it is already showing.

Worth stating plainly, since it changes what the feature *is*: with the
scheduler gone, **a day off is a marker, not a mechanism.** It greys the
column and says why. Work sitting on that day stays exactly where it is, and
marking the day reports what is there rather than moving it — covered by
*marking a day off leaves the work sitting on it*.

### 2026-08-27 (later) — One screen: the class manager and task manager removed

Same day, same direction, one step further. Having planned in the grid, the
owner asked for the other two Manage pages to go: *"we no longer need these
pages, Classes and Task Manager."*

Both were right to remove, for the same reason: each existed to hold something
the planner can hold better in place.

- **Classes** became a `+ Add a class` row at the foot of the grid and a `-`
  on each class row. Hiding deactivates rather than deletes — a class the
  household stopped teaching still owns completed work the UFA record needs —
  and hidden classes stay one click from returning, since there is no longer a
  screen to go back to.
- **Task Manager** was three tabs: a quick-add form the grid replaced, a flat
  task list the grid replaced, and the legacy JSON bulk import that should have
  gone with the CSV importer. What it held that the grid did not was *editing*:
  minutes, XP, type, teacher-led, a link, notes. That is now the card editor —
  click any card in the grid. `TaskForm.vue` went with the page.

**The reset.** `POST /api/maintenance/reset-curriculum` deletes every lesson,
assignment, unit, XP entry and purchase in the tenant, keeping classes,
accounts, calendar, expenses and reward definitions. It exists because the
alternative was talking a first-time developer through Railway's CLI and psql
to run DELETEs against production by hand, which is the larger risk. Guarded by
a phrase typed in full and re-checked server-side; `reset.spec.js` asserts that
an almost-match ("delete all work") is as inert as nonsense.

Admin is now five screens: Plan the Week, Calendar, Creator Projects,
Portfolio, Analytics, UFA Finances, Settings — with Plan the Week the home.

### 2026-08-27 — One week at a time: the importer and the scheduler both removed

**The second redirect in two days, and the deeper one.** Yesterday's lesson was
that the importer served the migration rather than the loop. Today's is that
this household does not need the loop *automated* either:

> *"I am done trying to do whole curriculum and units and all of that. I would
> rather just input the classes and write a description of what needs to be
> done week by week… Sonny's workload is not large so I can easily hand enter
> the week ahead every Sunday."*

He is right, and the arithmetic is the argument: four or five items a day for
one student is about fifteen lines of typing on a Sunday. Every mechanism
built to avoid that typing — the CSV importer, `source_key` reconciliation,
unit staging and release, `day_of_week_hint`, the rolling scheduler itself —
cost more attention to operate than the typing it replaced. PHASE3_BRIEF's
paste-a-list and per-unit rhythm were the same mistake one size smaller, and
were never built.

**Removed:** `routers/curriculum.py`, `services/curriculum_import.py`, the
import screen and store, `import.spec.js`, the unit manager and its store, the
unit picker on the task form, `ScheduleView.vue`, `WeeklyGrid.vue`, and
`compute_rolling_schedule` / `reschedule_from_today` — with the module renamed
`school_days.py` for what honestly remains of it.

**Added:** `/api/week` and `WeekPlannerView.vue` — classes down the side, days
across the top, click a cell and type. Plus `POST /courses/{id}/clear-unstarted`
as the escape hatch for an abandoned plan, which keeps anything completed.

**The decision that matters most:** *nothing moves work any more.* Adding a
sick day used to fire a full-tenant reschedule; it now reports what falls on
that day and leaves it alone. Every entry the planner creates is
`date_locked`. A date the teacher typed is a decision, and an app that quietly
revises it is an app he cannot plan in. There is deliberately no
`/schedule/recalculate` left, and `scheduling.spec.js` asserts its absence so
reintroducing one has to be a conscious act.

**Kept deliberately, though now unused:** `Unit`, `Lesson.source_key`,
`Lesson.import_id` and the unit-status column. Ripping them out means a
migration against live data holding Sonny's completion history, for no
behaviour he would ever notice. Dead columns are cheap; a bad migration is
not. They are invisible in the UI, which is what he actually asked for.

**Process note, recorded rather than hidden:** the repo's rule is
brief-then-build. This change went straight to build. The four questions he
answered were a tighter specification than a brief would have produced, and he
had twice said the ceremony was the problem. Writing a document to describe
deleting documents' worth of machinery would have been the joke telling
itself. The rule stands for the next phase.

**The lesson, third time stated and hopefully last:** *ask what the household
actually does before building the thing that would help if it did something
else.* Volume justifies machinery. Fifteen items a week does not.

### 2026-08-26 — The loop, not the migration: Phase 3 redefined, the Load stopped

**The product owner rejected the seeding workflow after using it once, and he
was right.** Recorded in full because it invalidates a decision the review doc
states as settled.

Tuttle Twins imported cleanly — 72 lessons, correct staging, the whole Phase
1+2 machine proven on real curriculum. Then: *"This doesn't feel intuitive…
I should just do my full curriculum offline and then add a unit at a time,
and have more granular control over the lessons. Every weekend I'll make sure
the week ahead looks good."*

The diagnosis: **the importer was built for the migration, and handed over as
the everyday workflow.** Getting 272 legacy lessons out of V1 is a one-time
problem, and the ceremony that solves it well — build a workbook, export a
sheet, adjust unit statuses, import a whole subject — is far too heavy for the
thing he actually does fifty times a year, which is *add the next unit and
check the week*. Two different products; I conflated them.

Consequences:

- **The Load step is stopped at one subject.** Beast Academy, Brave Writer,
  Critical Thinking Co. and CrunchLabs will go in through Phase 3's front
  door, one unit at a time, by him. Cutting four more CSVs would have been
  four more units of the wrong workflow.
- **Phase 3 is now "the weekly loop"** (`PHASE3_BRIEF.md`), not "protect the
  student side". Most of the old Phase 3 survives inside it, reframed: the day
  cap and unassign are still there, now paired with the teacher-side backlog
  strip that makes them decisions rather than silent policy.
- **Review §5.1's "one bulk path, one single-item path" is preserved in
  substance, not in letter.** Paste-a-list is a new *front end* over the Phase
  2 validate/commit service — same parser, same validator, same `source_key`
  rule — so there is still one bulk pipe. The CSV screen stays behind a link
  as the migration escape hatch. This is the one place to be vigilant: if a
  second parser ever appears, the rule has actually been broken.
- **Recurring routines slip to Phase 4.** They are still needed and still
  right; the loop has to feel good before another concept enters it.

The general lesson, worth keeping: *a workflow that is correct for loading a
year is not automatically correct for running one.* Ask which of the two a
feature serves before designing it.

### 2026-08-25 — Phase 2 deviations, all small and all recorded

Three places the build read the brief's intent rather than its letter:

- **A unique INDEX, not a UniqueConstraint**, enforces `(tenant_id,
  source_key)`. SQLite cannot ALTER a constraint onto an existing table, so
  the constraint form would have forced a batch-mode rebuild of `lessons` for
  identical enforcement. Same rule, both engines, no rebuild (`e5a2b8d17c40`).
- **Unknown header columns are an error, not ignored.** A misspelled optional
  column (`prioirty`) that was silently dropped would look exactly like data
  loss to the person who filled it in. Refusing by name costs one fix-and-retry.
- **"Editable preview grid" is implemented as editable *error lines*.** Good
  rows preview read-only; a row with an error exposes its raw CSV line for an
  in-place fix, and every edit goes back through the server's validator. A
  full grid editor would be a second spreadsheet — the workbook stays the
  place curriculum is edited.

The brief's own recorded deviation stands: imported units default to
`planned`, so a loaded year arrives dark until released.

### 2026-08-25 — The pilot found the form's second door

The unit-status gate (§2b) guards only the dates the *scheduler* assigns. The
task form is the other door a date can come through: its field defaults to
today so a quick add reaches the student — so a lesson authored into a
`planned` unit was born already scheduled, gate or no gate. The teacher found
it on the first production pilot, exactly the way it would have bitten during
the year.

Fix (`91ad860`): choosing an unreleased unit clears the date and says why on
screen; a date typed back in is warned about, not blocked, matching the
calendar model's manual-placement philosophy. The clear fires only on a
*change* of unit — editing an existing lesson never strips the date it has —
and never re-fills a field the user emptied. Phase 3's release model still
owns the deeper question of whether the form should default the date at all.

### 2026-08-24 — Branches consolidated into `main`; Phase 1 deployed to production

A survey (see `docs/ROADMAP.md`) found production live at `api.flokusacademy.com` but
sitting at `17280a99fab3` — pre-Phase-1 — while all Phase 1 work sat unmerged.
`school-year-2026-27` was a strict superset of every branch, so `main` was
fast-forwarded to it, and `feat/phase-1-curriculum-authoring` and
`hardening/phase-1-2-production-readiness` (both fully contained) were deleted.
One branch is the truth now; feature branches stay short-lived against `main`.
The deploy that followed settled the Postgres question below.

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

- ~~**The Phase 1 migrations have never run on Postgres.**~~ **Settled
  2026-08-24.** The consolidation deploy ran `a1c4e7b9d203` → `b2f5083ac611` →
  `c3a91d4e2f70` against production Postgres via the pre-deploy
  `alembic upgrade head` step; `/health/ready` reports `c3a91d4e2f70`. The RLS
  reasoning (both data-writing migrations bind `app.tenant_id` first, because
  the policy doubles as the `WITH CHECK` on INSERT) held. Remaining sliver:
  confirm `GET /api/config/` returns `school_days` from the table rather than
  the Mon–Thu fallback — that check needs a teacher login, so it happens the
  first time the admin UI is opened against production (the Pilot covers it).

- **`completion.spec.js` *XP counts up to the amount actually awarded* flaked
  once.** One failure in nine full runs; the other eight were clean, including
  the last three at 65/65. It polls an animated counter with a 10s budget
  against a database every other spec writes to, which is enough to explain it,
  and nothing in Phase 1 touches completion or the XP ledger. Not chased down.
  If it recurs, the likely fix is to read the value only after the count-up
  settles rather than to widen the timeout — a longer timeout would hide a real
  regression in the same place. (The other failure seen during the work was a
  genuine race in a new spec of mine, fixed with `waitForResponse`, not a flake.)
