> ## ⚠️ Superseded — history, not instructions
>
> **Written 17 August 2026. Its recommendations were built, and then removed.**
>
> This review designed a curriculum-ingest architecture: units, staged-and-released
> work, a CSV importer with `source_key` idempotency, and a rolling scheduler.
> All of it shipped between 17 and 25 August, and all of it was removed on 26–27
> August, because the household it was built for does not have the problem it
> solves — one student doing four or five things a day is fifteen lines of typing
> on a Sunday.
>
> Kept because it is the clearest account of *why* the domain model is shaped the
> way it is, and several decisions in it are still load-bearing: the
> template/instance split, the append-only XP ledger, tenant-scoped repositories,
> and the analysis of the v1 data in §7.
>
> **What is true now:** `docs/BUILD_LOG.md` and
> `.agents/skills/lms-architecture/SKILL.md`.

---

# Flokus Academy — Curriculum Ingest Review & Import Spec

**Reviewed:** backend `app/` (models, schemas, routers, repository, services), frontend `src/` (admin + student), legacy `flokus.db` and `archive_v1/`
**Date:** 17 August 2026 — day 1 of the 2026–27 year
**Scope:** how curriculum gets *into* Flokus Academy, and what happens to the student experience once it is there

---

## 1. The verdict up front

**The data model is right. The way in is missing.**

`Program → Unit → Lesson → Assignment` is the correct shape for what you are building, and the template/instance split is the hard part — you already did it. A lesson carries no student state; an assignment carries all of it. That is exactly what lets you reuse Beast Academy 2A next year for a sibling without last year's XP and completion dates following it around.

But there is currently **no path from "I have a curriculum" to "it is in the app"** except hand-typing JSON with database IDs in it. Specifically:

- You cannot create a Program from the UI. Not "it's awkward" — the route does not exist.
- You cannot create a Unit from the UI, and nothing in the frontend has ever set `unit_id`. The entire middle tier of your model is unreachable.
- The only bulk path is a `<textarea>` that takes raw JSON keyed on numeric `course_id`.

So the honest summary is: **you built a well-designed warehouse and there is no loading dock.** Everything below is about building the loading dock, and fixing the handful of things that will bite once real volume goes through it.

---

## 2. What is already good, and worth protecting

Worth naming, because several of the recommendations below are constrained by decisions I think you got right:

| Thing | Where | Why it matters for seeding |
|---|---|---|
| Template/instance split | `models.py:68–125` | One lesson, many students, independent progress. This is what makes multi-year and multi-child reuse possible. |
| XP as an append-only ledger | `models.py:212–230` | Balance is `SUM(delta)`, never a stored counter. Means a bad import can be reversed without corrupting the economy. |
| Tenant-scoped repository layer | `repository.py` | "The first `.where()` clause is the tenant." An importer written against the repositories inherits isolation for free. |
| Exact-pinned dependencies, deliberately minimal | `requirements.txt` | `pandas` and `aiofiles` were removed on purpose. The import design below respects that — it needs **zero new backend dependencies**. |
| Completion date vs. scheduled date, kept distinct | `repository.py:39–73` | Already handles the subtle case correctly. Don't let an importer undo this. |

---

## 3. What blocks you, in severity order

### Blockers — these stop curriculum getting in at all

---

**B1. There is no admin screen for Programs or Units.**

`router/index.js:22–32` defines eight admin routes: tasks, schedule, calendar, projects, portfolio, analytics, finances, settings. No courses. No units.
`stores/courses.js:23` exports exactly `{ courses, loading, fetchCourses }` — read-only.

The nine programs that exist came from `services/curriculum_seeder.py:68–78`, a hardcoded Python list. To add "Tuttle Twins American History" as a program today, you edit Python and redeploy.

The API is already there and complete — `routers/courses.py` and `routers/modules.py` both have full CRUD. **Nothing calls them.** `/api/modules` has zero frontend callers; the only reference to `module_id` anywhere in `frontend/src` is `stores/schedule.js:33`, and `ScheduleView.vue:45` calls `recalculate()` with no argument, so it is always `null`.

> This is the cheapest high-value fix in the whole review. The backend work is done. It needs a Vue view and two router entries.

---

**B2. Nothing ever sets `unit_id` — and the scheduler punishes that.**

`TaskForm.vue` has no unit/module field. The bulk import preview (`TaskManagerView.vue:108–129`) shows Title, Course ID, Type, Min, XP, Day Hint — no unit. So every lesson you create today has `unit_id = NULL`.

Now look at `rolling_scheduler.py:109–112`:

```python
key = (a.student_id, a.lesson.unit_id)
by_student_unit.setdefault(key, []).append(a)
```

Every unit-less lesson across every subject collapses into **one group**. Then `compute_rolling_schedule` advances one school day per lesson in the group (`rolling_scheduler.py:83`).

**Concrete consequence:** quick-add five tasks for tomorrow, hit "Recalculate Schedule", and they get spread across five consecutive school days — one per day, ignoring subject. Import a hundred and you have a hundred-day queue. The grouping logic is correct *if* units are populated. It is silently destructive when they are not, which is the only state the UI can currently produce.

---

**B3. Bulk import is a JSON textarea keyed on database IDs.**

`TaskManagerView.vue:34–50`. To import a Beast Academy chapter you must know that Beast Academy is `course_id: 1`. There is no lookup, no name resolution.

Beyond the ergonomics, four structural gaps:

- **No idempotency.** `create_tasks_bulk` (`tasks.py:167–188`) creates a new Lesson per row unconditionally. Import the same file twice, get every lesson twice. No natural key, no upsert, no "already imported" detection.
- **No server-side dry run.** The Preview button only re-renders what you pasted. The first time the server sees the data is the moment it commits it.
- **All-or-nothing failure, with no row attribution.** One bad row and the whole batch 422s. `client.js:149–166` will tell you `course_id: Input should be a valid integer` — but not *which of your 180 rows*.
- **N+1 flushes.** `tasks.py:170–181` does `await db.flush()` inside the loop, once per lesson. Fine at 10 rows, noticeable at 700.

---

**B4. Authoring a lesson and assigning it are welded together.**

`_assign_to_students` (`tasks.py:81–101`) hands every newly created lesson to **every student in the tenant**, immediately. There is no `POST /assignments`, no way to author curriculum without dispatching it, and no way to assign an existing lesson to a student later.

Your model separates these cleanly. Your API does not expose the separation. Two consequences:

1. **The moment there is a second child**, every lesson goes to both regardless of level. Sonny's Beast Academy 2A lands on a sibling doing 4B.
2. **You cannot stage a year.** Authoring 700 lessons in August means creating 700 assignments in August, which feeds directly into B7 below.

`create_task` also returns `assignments[0]` (`tasks.py:164`) — with two students, the admin UI is handed one child's assignment ID and doesn't know it.

---

### Defects that will bite once volume is real

---

**B5. `PUT /api/tasks/{id}` silently resets every field you don't send.**

`TaskUpdate` (`schemas.py:86`) inherits `TaskBase`, where every field except `title` has a default. `update_task` (`tasks.py:205–210`) does `model_dump()` — which returns **all** fields, defaults included — and writes each one onto the lesson.

Send `{"title": "Ch 4", "course_id": 1}` to update a title and you have just set `xp_reward = 10`, `estimated_minutes = 30`, `task_type = "reading"`, `medium = "offline"`, and `scheduled_date = None`. That last one removes the assignment from the student's day entirely (see B7).

This is a data-loss bug that gets much worse when you have a year of tuned lessons. `TaskUpdate` needs `Optional` fields and `model_dump(exclude_unset=True)`.

---

**B6. The rolling scheduler overwrites hand-placed dates, and runs far more often than you'd expect.**

`rolling_scheduler.py:57–76`: for `dependency_mode == 'independent'` — the default, and what every quick-add produces — `scheduled_date` is assigned **unconditionally**. Only `live_scheduled` checks whether a date already exists (`:79`).

And the recalculation is not just the button on the Schedule screen. `routers/schedule.py` fires a full-tenant `reschedule_from_today` on **add sick day** (`:26`), **add holiday** (`:34`), and **delete calendar entry** (`:54`). Marking one Tuesday as a sick day rewrites the date of every incomplete independent assignment in the database.

Related, same file: **`dependency_mode` values don't match between the UI and the scheduler.**

- `TaskForm.vue:100–101` offers `independent` and **`with_teacher`**
- `rolling_scheduler.py:57` handles `independent` and **`teacher_led`**; `:78` handles `live_scheduled`

`with_teacher` matches no branch. Such a lesson never gets a date assigned — but line 83 still advances `current_school_day`, so it burns a slot in the sequence anyway. `dependency_mode` is a bare `str` in `schemas.py:74` with no validation, so nothing catches the typo. Three vocabularies, no single source of truth.

---

**B7. The student's day has no ceiling.**

`repository.py:59–66` — the day view returns everything where `is_completed = False AND scheduled_date <= today`.

Nothing outstanding ever falls off. Miss three days in November and the app greets a nine-year-old with the accumulated backlog stacked on top of today's work. The rolling scheduler is the intended remedy, but it only runs when you press a button or edit the calendar — so between recalcs, the day grows without bound.

**This is the single biggest risk to "keeping the student side clean," and it only becomes visible after you seed a real year.** With 4 tasks/day × 180 days it is fine on day 1 and unusable by day 40 if the recalc discipline slips. It needs to be structural, not procedural — see §6.

---

**B8. Deleting a task deletes the curriculum for everyone, and scans the whole table to do it.**

`delete_task` (`tasks.py:272–293`) resolves the assignment, then deletes **the lesson**, cascading to every student's assignment. There is no unassign. Removing one child's work removes it from the sibling and from next year.

The XP reversal loop at `:281` calls `AssignmentRepository.list(db, tenant_id, unit_id=None)` — which, since `unit_id=None` means "no filter," loads **every assignment in the tenant** into memory and filters in Python. At 700 lessons × 2 students that is 1,400 rows joined to lessons and programs, to reverse XP on one.

---

**B9. `resource_path` exists but there is no upload path.**

`models.py:84` and `schemas.py:66` carry `resource_path`; `tasks.py:46` returns it. There is no `UploadFile` anywhere in the backend, no `StaticFiles` mount in `main.py`, and `uploads/` is empty. `requirements.txt` records that `aiofiles` and the upload mount were **deliberately removed in H-06**.

So the field is currently dead weight. Leave it that way for now: the ingest design (§5) deliberately needs no upload endpoint, so H-06 stays intact. `resource_path` only earns its keep the day you want worksheets attached to lessons, and that is a separate feature from curriculum ingest.

---

**B10. The calendar conflates "a day I schedule work on" with "a day work may exist on."** *(Resolved — see the rule below.)*

`rolling_scheduler.py:17` treats `weekday() >= 4` as weekend and refuses to place anything there. `schemas.py:73` constrains `day_of_week_hint` to `0..3` to match. Your v1 plan already contradicts this: **108 tasks sit on 36 Fridays.**

**The decision: Monday–Thursday are the core school days. Friday, Saturday and Sunday stay available for work when you need them, but nothing is ever scheduled there automatically.**

The code currently has one concept where it needs three:

| Day is… | Means | Auto-scheduler | Manual placement |
|---|---|---|---|
| **Core** | weekday ∈ `school_days` (Mon–Thu), not blocked | Places work here | Allowed |
| **Optional** | Fri/Sat/Sun, not blocked | **Never** places work here | Allowed — catch-up, a make-up day, a Saturday co-op |
| **Blocked** | `SchoolCalendar.day_type != 'school_day'` — holiday, sick day, break | Never | Warned, but permitted if you insist |

Three changes implement it:

1. `school_days` moves into `app_config` as `Mon,Tue,Wed,Thu`. `get_school_days` reads it instead of hardcoding `weekday() >= 4`. Changing your school week later becomes a settings edit, not a deploy.
2. `day_of_week_hint` widens from `0..3` to `0..6`. A hint of Fri/Sat/Sun is a deliberate statement — "this lesson belongs on a weekend" — not an error.
3. **A new `Assignment.date_locked` flag.** Set whenever you place a date by hand. The rolling scheduler skips locked assignments entirely.

That third one is doing double duty: without it, a Saturday catch-up assignment survives exactly until the next time you add a sick day, at which point the full-tenant recalc moves it back to a Monday. **It also fixes B6** — the date-stomping problem is the same problem, and one flag solves both. Auto-placed dates stay fluid and reschedule freely; hand-placed dates are promises the scheduler must keep.

One reporting note: weekend work still counts. `ufa_hours_credit` is a property of the lesson, not of the calendar, so a Saturday make-up session accrues instructional hours normally in the UFA record.

---

## 4. The workflow I'd recommend

The current mental model is one step: **create a task → it appears in the day.** That is right for a quick add and wrong for a curriculum.

Three stages instead, matching the model you already built:

```
   AUTHOR                    STAGE                      RELEASE
   ──────                    ─────                      ───────
   Program                   Assignment                 scheduled_date
     └ Unit                  created, but                set; appears in
        └ Lesson             undated                     the student's day

   "Beast Academy 2A         "Sonny is doing            "This is Sonny's
    Ch 3 exists"              Beast Academy 2A"          work for Tuesday"

   Bulk import,              Enroll student             Rolling scheduler,
   spreadsheet,              in a unit                   or teacher pins a
   TOC paste                 (one click)                 date by hand
```

The one change that makes this work: **an assignment with `scheduled_date = NULL` is staged, not scheduled.** It exists, it belongs to the student, it does not appear in their day. The day view already filters `scheduled_date <= today` and `NULL <= today` is `NULL` in SQL, so undated assignments are *already* excluded — the behaviour is there, it just isn't named or used deliberately. (There's a note in `TaskForm.vue:32–37` treating this as a hazard to work around. It's actually the feature.)

**Why this matters for your specific situation:** you can import all 700 lessons for the year in August, enroll Sonny in every unit, and have the student side show only what the scheduler has released — typically the current unit's next few days. Nothing else changes on the student side. The year is fully planned and the app stays a clean four-card morning.

---

## 5. The curriculum ingest spec

### 5.1 Design principle: one bulk path, one single-item path

An earlier draft of this spec proposed three ingest adapters — spreadsheet, pasted outline, and publisher PDF. **That was over-built, and it has been cut.** Three adapters means three parsers, three sets of edge cases, and three things to keep working, in service of one job that a spreadsheet already does well.

Two paths, and only two:

```
   BULK                                    SINGLE
   ────                                    ──────
   Spreadsheet ──▶ CSV ──▶ Validate        The existing task form,
                           ──▶ Preview     improved with unit + priority
                           ──▶ Commit
   Seeding a subject, a term, a year.      "Add one more thing this week."
```

Everything the outline parser was for — adding a handful of lessons to a subject mid-term — is better served by the single-assignment form, which has to exist anyway and which you can use without leaving the app.

**On publisher PDFs specifically:** the extraction is real work, but it does not belong *in the app*. A publisher's scope-and-sequence needs a human eye on the result no matter how it is parsed, and the app would be carrying a PDF pipeline to save typing that happens once per program per year. Hand the PDF to a Claude session instead and get a filled spreadsheet back — same outcome, nothing to build, nothing to maintain. This document's companion workbook was produced exactly that way.

### 5.2 The canonical row

One row = one lesson. Names match the existing API vocabulary so nothing has to be renamed later.

| Column | Required | Type | Notes |
|---|---|---|---|
| `program` | ✅ | text | Matched by **title or platform name**, case-insensitive. Not an ID. Unknown value → offered as "create new program" in preview. |
| `unit` | ✅ | text | Matched or created within the program. This is what fixes B2. |
| `unit_status` | | enum | `planned` \| `active` \| `completed` \| `abandoned`. Default `active`. Lets you import Beast Academy Level 3 now and release it only if you jump (§8.2). |
| `unit_week_start` | | int | Only read from the first row of each unit. |
| `unit_week_end` | | int | Same. |
| `title` | ✅ | text | The lesson. |
| `description` | | text | |
| `task_type` | | enum | `reading` \| `lesson` \| `practice` \| `quiz` \| `project` \| `build` \| `live` \| `review` |
| `priority` | | enum | `core` \| `standard` \| `optional`. Default `standard`. **This is what makes an accelerated path possible** — see §8.2. |
| `sequence_order` | | int | Blank → row order within the unit. |
| `estimated_minutes` | | int | Default 30. |
| `xp_reward` | | int | Default 10. |
| `is_boss_fight` | | bool | `yes`/`no`/`true`/`false`/`1`/`0`. |
| `medium` | | enum | `online` \| `offline` |
| `dependency_mode` | | enum | `independent` \| `teacher_led` \| `live_scheduled` — **the backend's spelling**, and this list becomes the single source of truth (fixes B6). |
| `day_of_week_hint` | | text | `Mon`–`Sun`, not an integer. Mon–Thu paces within the core week; Fri–Sun deliberately places on an optional day (B10). |
| `resource_url` | | url | |
| `workbook_pages` | | text | e.g. `pp. 24–31` |
| `ufa_eligible` | | bool | Default from the program. |
| `ufa_hours_credit` | | number | For state reporting. |
| `source_key` | | text | **Idempotency key** — see 5.4. Auto-derived if blank. |

Notably **absent: `scheduled_date`.** Importing curriculum should never place dates. That is the release stage's job. This alone prevents most of the B6 collisions.

### 5.3 The pipeline, as API

```
POST /api/curriculum/validate  → parses the CSV; returns row-level errors, resolved
                                  program/unit IDs, "will create N programs, M units,
                                  K lessons", and duplicate detection against source_key
POST /api/curriculum/commit    → single transaction, returns an import_id
POST /api/curriculum/rollback  → undo an import_id (lessons are new; XP ledger
                                  reversal already exists for anything completed)
```

Three endpoints, not four: with one input format there is nothing for a separate `/parse` step to do that `/validate` cannot do in the same pass.

The critical property, and the thing the current `/tasks/bulk` lacks: **validate returns errors keyed by row number**, so a 180-row import reports "row 47: unknown program 'Beast Acadmy'; row 92: day_of_week_hint 'Sat' is not a school day" instead of one opaque 422.

Commit in **one transaction with one flush**, not a flush per row.

### 5.4 Idempotency — `source_key`

The single most important field, and the one the current importer lacks entirely.

```
source_key = slug(program) + "|" + slug(unit) + "|" + slug(title)
             e.g.  "beast-academy|unit-1-trade-place-value|ba-2a-ch-1-place-value"
```

Store it on `Lesson`, unique per tenant. Then:

- Re-importing an unchanged file is a **no-op**, not a duplication
- Re-importing a *corrected* file becomes an **update** — fix a typo in your spreadsheet, re-import, and the lesson updates without losing the student's assignment or completion history
- The preview can honestly say "12 new, 168 unchanged, 3 updated"

This is what turns the spreadsheet from a one-shot seeding tool into the thing you actually maintain the curriculum in all year.

### 5.5 Wire format: CSV text inside JSON

Given `requirements.txt` explicitly removed `pandas` and the upload mount, the import needs **no new backend dependency**:

- The browser reads the file with `FileReader` and posts the text in a JSON body
- The backend parses with the standard library's `csv` module — the same module `expenses.py:2` already imports for its export
- No `multipart`, no `aiofiles`, no re-opening the H-06 decision

The `.xlsx` template (delivered alongside this document) is an **authoring convenience** — dropdowns, examples, colour-coded required columns. You fill it in Excel or Google Sheets and export one sheet as CSV. If you'd rather drop the `.xlsx` directly, that's a frontend-only addition (SheetJS in the browser, converting to CSV before it ever reaches the API) — still zero backend dependencies.

### 5.6 The single-assignment path

The other half of ingest, and the one you will use most often once the year is loaded: *"CrunchLabs box #4 arrived early, add a build day for Thursday."*

This is the existing `TaskForm` (`components/admin/TaskForm.vue`), which already works. It needs three additions, all in Phase 1:

- **Unit picker**, filtered by the selected program (item 3) — without it every quick-add lands with `unit_id = NULL` and the scheduler mis-paces it (B2)
- **`priority`**, so a one-off addition can be marked `optional` and skipped when the pace tightens
- **A date that sticks** — `date_locked` (item 6), so placing something on Saturday survives the next recalculation

Deliberately *not* added: a second bulk-ish paste box. If you are adding more than a handful of lessons, that is a spreadsheet job, and having two ways to do the same thing is how the two drift apart.

### 5.8 Schema additions required

Small, and all additive:

```python
# Lesson
source_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
import_id:  Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
priority:   Mapped[str] = mapped_column(String(12), default='standard')
            # 'core' | 'standard' | 'optional'  — drives accelerated paths (§8.2)
__table_args__ = (UniqueConstraint('tenant_id', 'source_key', name='uix_tenant_source_key'),)

# Unit — for §8, pivoting programs
status: Mapped[str] = mapped_column(String(20), default='active')
        # 'planned' | 'active' | 'completed' | 'abandoned'

# Assignment — release state, distinct from "has a date"
released_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
date_locked: Mapped[bool] = mapped_column(Boolean, default=False)
             # hand-placed; the rolling scheduler must not move it (B6, B10)
```

`app_config` (already exists) picks up:

| Key | Value | Replaces |
|---|---|---|
| `school_days` | `Mon,Tue,Wed,Thu` | the hardcoded `weekday() >= 4` at `rolling_scheduler.py:17` |
| `daily_task_cap` | `6` | nothing — new, see §6.1 |
| `academic_year_start` | `2026-08-17` | the `SchoolEvent.title.ilike('%First day%')` lookup at `rolling_scheduler.py:98` |
| `grade_level` | `5` | nothing — new, see §8.3 |

That third one is worth retiring on its own merits: an anchor date that depends on someone never renaming a calendar event is fragile in a way that fails silently and late.

`day_of_week_hint` also relaxes from `Field(None, ge=0, le=3)` to `ge=0, le=6` in `schemas.py:73`.

---

## 6. Keeping the student side clean once the year is loaded

You explicitly want the student side streamlined. Four changes, in order of impact:

**6.1 — Cap the day.** The day view should return today's released work plus *at most* N catch-up items, oldest first. `daily_task_cap` in config, default 6. The rest stays in the database and surfaces on the admin side as a backlog count. A child should never open the app to a wall. This directly answers B7 and it is the one I'd do first.

**6.2 — Separate routines from curriculum.** Your v1 data makes the case better than I can: 684 tasks, **341 distinct titles**. Chess.com is 89 rows across 14 distinct titles; Brilliant.org is 72 rows across 13. "Chess.com: Tactics & Play" is not curriculum — it is a recurring habit, and storing it as 89 near-identical lesson rows is what makes the day feel cluttered and the task list unmanageable.

The same is true of the Friday rhythms (§7): `Beast Academy & Brilliant Weekly Math Review` appears 36 times, `Chess.com: Weekly Challenge & Matches` 36 times, `Poetry Teatime` 26 times. Those are three habits, stored as 98 rows.

A `RecurringLesson` (a lesson + a cadence, materialised into an assignment on its day) collapses **412 rows of the v1 plan — 60% of it — into 14 definitions**. It also makes "swap Chess.com for something else" a one-row edit rather than 89, which is precisely the pivot flexibility you asked for.

**6.3 — Release by unit, not by year.** With staging in place (§4), the teacher's action is "start Unit 3," and the scheduler dates only that unit's lessons. The student's day never knows the other 33 units exist.

**6.4 — Fix the greeting.** `DailyQuestsView.vue:116` hardcodes `Good morning, Sonny! 🚀`. Small, but it is the first line the student reads and it says "afternoon" is impossible and a sibling doesn't exist.

---

## 7. Migrating the 684-task v1 plan

Worth doing — but selectively, because the corpus is not uniform in quality.

### What's actually in there

`flokus.db`, table `tasks`: **684 rows, 341 distinct titles, 180 school days, 2026-08-17 → 2027-04-23.** Plus `archive_v1/streamlit_app/curriculum_data.py`, which holds the structure the flat rows were generated from — `TIER_1_OVERVIEW` (4 quarters) and `TIER_2_UNITS` (36 weeks mapped to 9 four-week units). **That file is the more valuable artifact of the two**, because it is where the units live, and units are exactly what the v2 model has been missing.

| Program | Rows | Distinct titles | Fidelity | Recommendation |
|---|---|---|---|---|
| Social Studies (Tuttle Twins) | 72 | **72** | Fully authored | **Migrate as curriculum.** 1:1, chapter by chapter. |
| Math (Beast Academy) | 108 | 73 | High | **Migrate as curriculum.** Repeats are "Practice & Puzzlers" follow-ons — legitimate. |
| Critical Thinking Co. | 72 | 56 | High | **Migrate as curriculum.** |
| Language Arts (Brave Writer) | 179 | 49 | **High, once decomposed** | **Migrate as curriculum + routines.** The 49/179 ratio looks poor until you split it: 45 rows are fully-authored Dart lessons (45 distinct, 9 books × 5), and the other 134 are four weekly rhythms. Same quality tier as Tuttle Twins. |
| Science (CrunchLabs) | 37 | 32 | Good | **Migrate**, but see the box-delivery note below. |
| Logic (Synthesis) | 37 | 26 | Placeholder | **Convert to recurring routine, benched.** Same shape as Brilliant — a Mon/Tue online slot with rotating topics, no real sequence. It and Brilliant are a swap pair (§8.1). |
| **Logic (Chess.com)** | 89 | **14** | Placeholder | **Convert to recurring routine**, not 89 lessons. |
| **Logic (Brilliant.org)** | 72 | **13** | Placeholder | **Convert to recurring routine.** |
| **Science (Outschool)** | 18 | **6** | Placeholder | **Convert to recurring routine**, or drop. |

Migrating the placeholder programs as-is would put ~180 near-duplicate lesson rows into a clean database on day one. Don't.

**CrunchLabs deserves a second look too.** Its 37 rows are a clean four-week cycle — a 🛠️ Box Build Day, then three weeks of "Applied STEM / Project Tinkering", nine times over. Only the 9 builds and the 2 year-end expo sessions are real lessons; the 26 tinkering rows are one weekly Thursday habit whose v1 titles (`Applied STEM / Project Tinkering: Chess.com Openings + Outschool Class`) were the generator concatenating unrelated spokes. CrunchLabs is 11 lessons and 1 routine, not 37 lessons.

### The Friday question answers itself

Both open questions are now settled — Mon–Thu core with optional Fri/Sat/Sun (B10), and Grade 5 with Level 2 math by design (§8.3). But it's worth looking at what those 108 Friday tasks actually *are*, because the v1 plan turns out to already agree with the model:

**108 Friday rows across just 13 distinct titles.** They split cleanly in two:

| | Rows | Distinct | What it is |
|---|---|---|---|
| Weekly rhythms | **98** | 3 | `Beast Academy & Brilliant Weekly Math Review` ×36 · `Chess.com: Weekly Challenge & Matches` ×36 · `Brave Writer & History Review / Poetry Teatime` ×26 |
| Genuine milestones | **10** | 10 | 9 × 👑 Dart Book Party, 1 × 👑 Master Expo & Portfolio Presentation |

So Friday in your v1 plan was never a fifth teaching day — it was **a light review-and-celebrate day**, which is exactly what "Mon–Thu core, Friday optional" describes. The design and the existing plan were already in agreement; only the code disagreed.

The migration follows directly:

- The **98 rhythm rows become 3 recurring routine definitions** (weekly, Fri) — the same treatment as Chess.com and Brilliant, and the same 30:1 reduction.
- The **10 milestones become real lessons** with `day_of_week_hint: Fri`, `is_boss_fight: yes`, `priority: core`. They are the end-of-unit boss fights the model was built for, and they should stay in the curriculum.

108 rows collapse to 13. Between this, the placeholder programs and the CrunchLabs cycle, the migration resolves to an exact figure:

> **684 v1 tasks = 272 curriculum lessons + 412 routine occurrences (14 definitions).**

Every row is accounted for; nothing is silently dropped. 272 real lessons and 14 habits is a fair description of what the year actually contains — and it is a far more tractable thing to maintain than 684 flat dated rows.

The finished workbook carries this: five program sheets (Beast Academy 72, Brave Writer 45, Tuttle Twins 72, Critical Thinking Co. 72, CrunchLabs 11) across 30 program-native units, plus 14 routine definitions and a log of the four judgment calls made on ambiguous units.

### Suggested migration route

Rather than a bespoke DB-to-DB script, **run it through the importer you're building.** A one-time script reads `flokus.db` + `curriculum_data.py` and emits the canonical CSV — one file per program. Then you import them like any other curriculum.

Three reasons: it exercises the importer against real, messy data before you trust it with anything new; the CSVs become an editable record of the year you can fix by hand; and it needs no migration-specific code path to maintain.

The unit assignment comes from `TIER_2_UNITS` — week number → unit title is already mapped there, and `Unit.week_start` / `week_end` already exist to receive it. That is the 9-unit structure landing in the model that was built for it.

---

## 8. Changing course mid-year

Three different manoeuvres that look similar and should be built differently.

### 8.1 — Swapping one program for another

Dropping Synthesis in November and adding something else:

1. **Archive the program** — `Program.is_active = False`. `ProgramRepository.list` already filters on it (`repository.py:253–257`), so it disappears from pickers without deleting history. Completed work stays in the portfolio and stays UFA-countable. **This already works.**
2. **Abandon its open units** — `Unit.status = 'abandoned'`, dropping undated assignments out of the scheduler's consideration. *(Needs the `status` column from §5.8.)*
3. **Import the replacement** through the normal pipeline.
4. **Don't touch the XP ledger.** Earned XP stays earned; it is append-only for exactly this reason.

The one thing to avoid: deleting the program. `delete_course` correctly deactivates rather than deletes (`courses.py:42–48`) — but `delete_task` does *not* have the same discipline (B8), and a "clean up the old program's tasks" instinct would cascade through assignments and reverse XP for work genuinely done.

**Swapping a *routine* platform is cheaper still — and this is the case you actually have.** Synthesis and Brilliant were set up as interchangeable online platforms, and the v1 data confirms they are structurally identical: both are a recurring Mon/Tue online slot with rotating topics, neither has a real scope-and-sequence.

That points at a useful way to think about it: **a routine is a slot, and the platform is an attribute of the slot.** The pedagogical commitment is "30 minutes of online logic practice, twice a week." Which platform fills it is an implementation detail. So the swap is:

```
Routine: "Online Logic Practice"  ·  Tue + Thu  ·  30 min
   program: Brilliant.org     ← active
   program: Synthesis         ← benched
```

Change which one is active. **No re-authoring, no lost history, no gap in the student's rhythm** — the slot on their Tuesday stays put, the link behind it changes. Contrast that with the 37 separate Synthesis lesson rows the naive migration would have produced, every one of which would need deleting to make the same switch.

Worth designing the routine model with this in mind (Phase 3, item 14): give `RecurringLesson` an `is_active` flag and let two definitions share a slot. Trying a new platform for a month then reverting becomes two toggles instead of an import and a cleanup.

### 8.2 — Changing level *within* a program (Beast Academy 2 → 3)

**This is not a program swap, and modelling it as one would be a mistake.** If BA Level 3 becomes a second Program, your math analytics split in two mid-year, the portfolio shows two subjects where there is one, and the UFA record has to be reconciled by hand.

Model it as **new units under the same Program.** "Math — Beast Academy" is the program for the whole year; the level lives in the unit structure:

```
Program: Math — Beast Academy          (unchanged all year, is_active = True)
  ├─ Unit: BA 2A — Place Value & Comparing     status: completed
  ├─ Unit: BA 2B — Addition & Subtraction      status: active
  ├─ Unit: BA 2C — Measurement & Strategies    status: planned   ← may get abandoned
  ├─ Unit: BA 2D — Big Numbers                 status: planned   ← may get abandoned
  ├─ Unit: BA 3A — Shapes & Multiplication     status: planned   ← the jump
  └─ Unit: BA 3B — Perfect Squares             status: planned
```

The jump is then a **status change on units, not a migration**: mark the remaining Level 2 units `abandoned`, mark 3A `active`. No re-enrollment, no new program, no gap in analytics, and `Program.subject_area = "Math"` keeps grouping everything correctly through the transition.

Practical consequence for right now: **import Level 3 units alongside Level 2 when you seed, with `status: planned`.** They cost nothing sitting there unreleased, and the jump becomes a click rather than an import you have to do under time pressure in January.

**The accelerated path through Level 2** is what the `priority` column is for. Beast Academy maps onto it cleanly:

| Beast Academy material | `priority` | Released when |
|---|---|---|
| Guide chapter (the comic — the actual instruction) | `core` | Always |
| Practice book problems | `standard` | Normal pace |
| Puzzlers, challenge sets, Practice & Puzzlers follow-ons | `optional` | Only if pace allows or a concept needs reinforcing |

Accelerating means **releasing `core` only** and letting the rest sit unreleased. Slowing down for a concept that hasn't landed means releasing `optional` too. Same imported curriculum, three speeds, nothing deleted — and the skipped material is still there if you want to come back to it.

> This depends on the author/assign/release split (§4, Phase 3 item 11). If assignments are still created at import time, "accelerate" means *deleting* assignments, and under B8 that deletes the lesson for the sibling and for next year too. **The acceleration you described is the strongest argument for doing the release split.**

### 8.3 — Grade level is not program level

You're teaching 5th grade with Level 2 math while concepts consolidate. That is an ordinary and sensible thing to do, and nothing in the schema currently records it — there is no grade field anywhere, and `README.md` asserts "5th-grade instruction" in prose only.

It matters in one specific place: **the UFA / ESA proof-of-work report.** A portfolio that lists "Beast Academy 2A" with no grade context invites a question you'd rather not answer twice. Adding `grade_level` to `app_config` and surfacing it on the portfolio header — *Grade 5, 2026–27* — costs almost nothing and frames the record correctly: a fifth grader whose math program is deliberately consolidating fundamentals, not a second grader.

Worth doing before the first report, not after.

---

## 9. Build order

Sequenced so each step is useful on its own, and so you can seed real curriculum as early as possible.

**Phase 1 — unblock authoring (small, high leverage)**

1. Program manager view + route. The API already exists; this is a Vue view.
2. Unit manager, nested under program, with the `status` field. Same — `/api/modules` is complete and unused.
3. Add a unit picker to `TaskForm`. Kills B2's silent scheduler damage.
4. Fix `TaskUpdate` → `Optional` fields + `exclude_unset=True` (B5). One-line class of data-loss bug.
5. Reconcile `dependency_mode` to one enum across schema, scheduler and form (B6).
6. **Calendar model (B10):** `school_days` into `app_config`, `day_of_week_hint` widened to `0..6`, `Assignment.date_locked` added and respected by the scheduler. This is what makes optional Fri/Sat/Sun work stick.

**Phase 2 — the importer**

7. Canonical row schema + CSV parser + validator, with row-numbered errors.
8. `source_key` + `priority` + unique constraint + Alembic migration.
9. `/validate` and `/commit` endpoints; commit in one transaction.
10. Import screen: choose CSV → editable preview grid → commit.

**Phase 3 — protect the student experience**

11. Author/assign/release split: `POST /api/assignments`, remove the implicit fan-out in `_assign_to_students` (B4). **This is the prerequisite for accelerating through Beast Academy 2 without deleting anything (§8.2).**
12. Day cap + catch-up policy (B7, §6.1).
13. Recurring routines (§6.2) — this is where Chess.com, Brilliant, and the three Friday rhythms land.
14. Release-by-priority: `core` only / `core + standard` / everything (§8.2).
15. Unassign, distinct from delete-lesson (B8).

**Phase 4 — migration and extras**

16. Import Beast Academy **Level 3** units as `status: planned` alongside Level 2, so the mid-year jump is a click (§8.2).
17. `grade_level` on the portfolio header before the first UFA report (§8.3).

**If you only do one thing this week:** Phase 1, items 1–3. You cannot seed subject-by-subject until you can create a subject, and every lesson you author before item 3 lands in the database with a null unit that the scheduler will mishandle.

---

## Appendix — the columns, ready to fill

The companion file `Flokus_Curriculum_Template.xlsx` implements this: one sheet per program, dropdowns on every enum column, required columns marked, and a filled Beast Academy example to copy from. Export any sheet as CSV and it is a valid import file for the pipeline above.

Required: `program`, `unit`, `title`
Everything else has a sensible default. Two deliberate design choices worth restating:

- **`scheduled_date` is not a column.** Dates are assigned at release, not at import.
- **`priority` is how you change pace without changing curriculum.** Import everything once; release `core` only to accelerate, or release `optional` too when a concept needs more time.
