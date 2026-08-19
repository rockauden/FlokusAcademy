# Phase 1 Implementation Brief — Unblock Curriculum Authoring

**For:** Claude Code, working in the `Flokus_Academy` repo
**Companion doc:** `docs/Flokus_Academy_Curriculum_Review.md` — read §3 (B1, B2, B5, B6, B10), §4, and §5.8 before starting. This brief is the executable subset.
**Branch:** `feat/phase-1-curriculum-authoring`

---

## Why this phase exists

Curriculum cannot be entered into Flokus Academy at all right now. There is no UI to create a Program or a Unit, and nothing in the frontend has ever set `unit_id` — so the middle tier of the data model is unreachable, and the rolling scheduler silently mis-paces every lesson that lacks a unit.

Phase 1 does not build the importer. It makes the database able to *receive* curriculum correctly, and fixes four defects that would corrupt data once real volume arrives. **Everything here is small.** The backend APIs for programs and units already exist and are fully functional — they have simply never been called.

**Definition of done:** a teacher can create a program, create units inside it, create a lesson attached to a unit, place work on a Saturday, and have that Saturday survive a schedule recalculation.

---

## Ground rules

- Follow the conventions already in the repo. The codebase has a strong house style — dense explanatory comments above non-obvious decisions, explaining *why* rather than *what*. Match it.
- `repository.py` opens with "Rule for anything added here: the first `.where()` clause is the tenant." Obey it. No bare `select(Model)` in routers.
- Dependencies are pinned exactly and deliberately minimal — `pandas` and `aiofiles` were removed on purpose. **Phase 1 adds no new dependencies, backend or frontend.**
- Every schema change needs an Alembic migration. Check `alembic/versions/` for the current head first.
- `npm run test:e2e` in `frontend/` must pass before you call this done.

---

## Item 1 — Program manager (admin UI)

**Problem (B1).** `router/index.js:22–32` has eight admin routes. None is for programs. `stores/courses.js:23` exports only `{ courses, loading, fetchCourses }`. The nine existing programs came from a hardcoded Python list in `services/curriculum_seeder.py:68–78`; adding one today means editing Python and redeploying.

**The backend is already complete.** `routers/courses.py` has full CRUD — `GET /`, `POST /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}` (which correctly deactivates rather than deletes). Nothing needs to change there.

**Build:**

| File | Change |
|---|---|
| `frontend/src/views/admin/ProgramManagerView.vue` | New. List + create + edit + deactivate. |
| `frontend/src/stores/courses.js` | Add `createCourse`, `updateCourse`, `deactivateCourse`. |
| `frontend/src/router/index.js` | Add `{ path: 'programs', component: … }` under `/admin`. |
| `frontend/src/layouts/AdminLayout.vue` | Nav link under "📝 Manage", above Task Manager. |

Form fields, matching `CourseBase` in `schemas.py:17–26` exactly: `title`, `subject_area`, `platform`, `platform_url`, `emoji`, `color_hex`, `sort_order`, `ufa_eligible`, `is_active`.

**Watch for:** the API path is `/courses/` **with the trailing slash**. `stores/tasks.js:60–66` documents why at length — without it FastAPI 307s to an absolute URL, and behind the TLS-terminating proxy that came back as `http://`, which the browser blocked as mixed content. Quick-add silently did nothing. Do not reintroduce that.

**Naming:** the API vocabulary stays `courses` / `modules`; the UI says "Program" and "Unit". `routers/modules.py:14` documents this split. Do not rename API paths in this phase.

**Acceptance:** create a program from the UI, reload, see it in the list and in the Task Manager's course picker. Deactivate it, confirm it disappears from the picker but its existing lessons survive.

---

## Item 2 — Unit manager (admin UI), with `status`

**Problem (B1/B2).** `/api/modules` is complete and has **zero frontend callers**. The only reference to `module_id` in `frontend/src` is `stores/schedule.js:33`, and `ScheduleView.vue:45` calls `recalculate()` with no argument, so it is always `null`.

**Build:**

| File | Change |
|---|---|
| `frontend/src/views/admin/UnitManagerView.vue` | New, or a nested panel inside ProgramManagerView. Units listed under a selected program. |
| `frontend/src/stores/units.js` | New store wrapping `/api/modules`. |
| `backend/app/models.py` | Add `Unit.status` — `String(20)`, default `'active'`. Values: `planned` \| `active` \| `completed` \| `abandoned`. |
| `backend/app/schemas.py` | Add `status: str = 'active'` to `ModuleBase`. |
| `backend/app/routers/modules.py` | Add `status` to `_to_response` (`:13–25`). |
| Alembic | New migration adding the column with `server_default='active'`. |

Fields: `title`, `description`, `week_start`, `week_end`, `sort_order`, `status`, `is_active`.

**Why `status` matters now rather than later:** it is what makes a mid-year Beast Academy Level 2 → 3 jump a status change instead of a migration. Level 3 units get imported as `planned` and sit unreleased. See review §8.2.

### 2b — The scheduler must skip non-active units

**This is the safety valve for the whole migration, and it belongs in Phase 1.**

Once the importer lands (Phase 2), a full-year import creates ~300 lessons across ~26 units. Those assignments arrive undated, so the student's day stays empty — until someone presses Recalculate, or adds a sick day, which fires `reschedule_from_today` across the whole tenant automatically (`routers/schedule.py:26,34,54`). At that moment every unit gets paced at once and the student's day fills with every subject's next lesson simultaneously.

The fix is one clause. `AssignmentRepository.for_scheduling` (`repository.py:167–178`) currently joins only `Lesson`:

```python
query = (
    select(Assignment)
    .options(_WITH_LESSON)
    .join(Lesson, Assignment.lesson_id == Lesson.id)
    .outerjoin(Unit, Lesson.unit_id == Unit.id)          # add
    .where(
        Assignment.tenant_id == tenant_id,
        or_(Lesson.unit_id.is_(None), Unit.status == 'active'),   # add
    )
)
```

The outer join and the `is_(None)` branch both matter: a lesson with no unit — a quick-add — must still schedule normally, and an inner join would silently drop it.

With this in place the workflow is: import the year with every unit `planned`, flip the current unit to `active`, and only that unit gets dated. **Activating a unit becomes the "release" action**, which is a usable subset of Phase 3's release model available a phase early.

**Acceptance:** create three units under a program, one `active` and two `planned`, each with lessons. Run Recalculate. Assert only the active unit's assignments received dates, that the planned units' assignments still have `scheduled_date IS NULL`, and that a unit-less quick-add lesson was still scheduled.

---

## Item 3 — Unit picker on the task form

**Problem (B2).** `TaskForm.vue` has no unit field, so every lesson created through the UI has `unit_id = NULL`. `rolling_scheduler.py:109–112` keys its grouping on `(student_id, lesson.unit_id)`, so **every unit-less lesson across every subject collapses into one group**, and `:83` advances one school day per lesson within a group. Quick-add five tasks, hit Recalculate, and they spread across five consecutive school days ignoring subject.

**Build:** in `frontend/src/components/admin/TaskForm.vue`, add a unit `<select>` that populates from the units store, **filtered by the selected `course_id`** and reset when the course changes. `TaskCreate` already accepts `module_id: Optional[int]` (`schemas.py:83`) — no backend change.

Also add `priority` (`core` | `standard` | `optional`) and `sequence_order` while you are in this form.

**Acceptance:** create a lesson with a unit, confirm `unit_id` is populated in the database, and confirm Recalculate paces it within its unit rather than in the global queue.

---

## Item 4 — `TaskUpdate` must not reset omitted fields

**Problem (B5), a live data-loss bug.** `TaskUpdate` (`schemas.py:86`) inherits `TaskBase`, where every field except `title` has a default. `update_task` (`tasks.py:205–210`) calls `model_dump()` — which returns *all* fields including defaults — and writes each onto the lesson.

Sending `{"title": "Ch 4", "course_id": 1}` to change a title also sets `xp_reward = 10`, `estimated_minutes = 30`, `task_type = "reading"`, `medium = "offline"`, and `scheduled_date = None`. That last one removes the assignment from the student's day entirely, because `repository.py:63` filters `scheduled_date <= today` and `NULL <= today` is `NULL` in SQL.

**Fix:**

```python
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    # … every field Optional, defaulting to None
```

and in `update_task`:

```python
payload = task_data.model_dump(exclude_unset=True)
scheduled_date_provided = 'scheduled_date' in payload
scheduled_date = payload.pop('scheduled_date', None)
for key, value in payload.items():
    if hasattr(a.lesson, key):
        setattr(a.lesson, key, value)
if scheduled_date_provided:
    a.scheduled_date = scheduled_date
```

Note the `scheduled_date_provided` check: `exclude_unset` alone cannot distinguish "field absent" from "field explicitly set to null", and clearing a date deliberately must stay possible. Line `tasks.py:210` currently assigns unconditionally.

**Acceptance:** a regression test. Create a lesson with `xp_reward=50`, PUT only `{"title": "new"}`, assert `xp_reward` is still 50 and `scheduled_date` unchanged. Then PUT `{"scheduled_date": null}` explicitly and assert it clears.

---

## Item 5 — One `dependency_mode` vocabulary

**Problem (B6).** Three vocabularies, no single source of truth:

- `TaskForm.vue:100–101` offers `independent` and **`with_teacher`**
- `rolling_scheduler.py:57` handles `independent` and **`teacher_led`**; `:78` handles `live_scheduled`
- `schemas.py:74` types it as a bare `str` with no validation, so nothing catches the mismatch

A lesson created as `with_teacher` matches no scheduler branch — it never gets a date assigned, but `:83` still advances `current_school_day`, so it burns a slot in the sequence anyway.

**Fix:** `independent` | `teacher_led` | `live_scheduled` is canonical.

- `schemas.py` — make it a `Literal["independent","teacher_led","live_scheduled"]` so a bad value is a 422, not a silent no-op.
- `TaskForm.vue` — change the `with_teacher` option value to `teacher_led`. Keep the label "With Teacher (Dad)".
- **Data migration:** `UPDATE lessons SET dependency_mode = 'teacher_led' WHERE dependency_mode = 'with_teacher'`. Check production for existing rows.
- `rolling_scheduler.py` — add an explicit `else` that raises or logs loudly on an unknown mode. Silent fall-through is what hid this.

---

## Item 6 — The calendar model: core vs optional vs blocked

**Problem (B10, B6).** `rolling_scheduler.py:17` hardcodes `weekday() >= 4` as weekend. `schemas.py:73` constrains `day_of_week_hint` to `0..3` to match. The code has one concept where it needs three.

**The decision, from the product owner:** Monday–Thursday are core school days. Friday, Saturday and Sunday remain available for work when needed, but nothing is ever auto-scheduled there.

| Day is | Definition | Auto-scheduler | Manual placement |
|---|---|---|---|
| **Core** | weekday ∈ `app_config.school_days`, not blocked | Places work | Allowed |
| **Optional** | weekday ∉ `school_days`, not blocked | **Never** | Allowed |
| **Blocked** | `SchoolCalendar.day_type != 'school_day'` | Never | Permitted, warn |

**Build:**

1. **`app_config` keys** (the table already exists, `models.py:294`):
   - `school_days` = `Mon,Tue,Wed,Thu`
   - `academic_year_start` = `2026-08-17` — replaces the `SchoolEvent.title.ilike('%First day%')` lookup at `rolling_scheduler.py:98`, which fails silently and late if anyone renames that calendar event
   - `grade_level` = `5`

2. **`get_school_days`** (`rolling_scheduler.py:11–21`) reads `school_days` instead of hardcoding. Keep the `MAX_HINT_SEARCH_DAYS` bound — it exists because an unmatched hint otherwise loops forever and hangs the worker.

3. **`day_of_week_hint`** widens from `Field(None, ge=0, le=3)` to `ge=0, le=6` in `schemas.py:73`. A Fri/Sat/Sun hint is a deliberate statement, not an error. Update the error message at `rolling_scheduler.py:69–74`, which currently says "Valid hints are 0=Mon to 3=Thu."

4. **`Assignment.date_locked`** — new `Boolean`, default `False`, plus migration. Set whenever a date is placed by hand (the task form, or a future drag on the weekly grid). `compute_rolling_schedule` **skips locked assignments entirely** — do not reassign `scheduled_date`, and do not advance `current_school_day` past them incorrectly.

**Why `date_locked` is not optional.** `routers/schedule.py` fires a full-tenant `reschedule_from_today` on **add sick day** (`:26`), **add holiday** (`:34`) and **delete calendar entry** (`:54`) — not just the Recalculate button. And `rolling_scheduler.py:57–76` assigns `scheduled_date` unconditionally for `independent`, the default mode. So without this flag, a Saturday catch-up assignment survives exactly until the next sick day, then silently moves to a Monday. One flag fixes both B6 and B10.

**Acceptance:**
- Place a lesson on a Saturday. Add a sick day for the following Tuesday. Assert the Saturday assignment still has its Saturday date.
- Assert the auto-scheduler never assigns a Fri/Sat/Sun date to a lesson with no `day_of_week_hint`.
- Assert a lesson with `day_of_week_hint = 5` (Sat) is placed on a Saturday.
- Assert changing `school_days` to include `Fri` makes the scheduler use Fridays, with no code change.

---

## Order of work

```
6  ──► calendar model + date_locked      (independent, do first — the migrations)
4  ──► TaskUpdate                        (independent, one file, ship it early)
5  ──► dependency_mode                   (independent, needs the data migration)
2b ──► scheduler skips non-active units  (backend, needs Unit.status from item 2)
1  ──► Program manager        ─┐
2  ──► Unit manager (+status)  ├─ sequential, share the store/router work
3  ──► Unit picker on the form ┘
```

Items 4, 5 and 6 are backend-only and mergeable on their own. Items 1–3 are one coherent frontend feature and are easiest as a single reviewable chunk. Item 2b needs the column from item 2 but is otherwise independent of the UI.

---

## Out of scope — do not build these here

- The importer, `source_key`, `/parse` `/validate` `/commit` (Phase 2)
- The author/assign/release split, `POST /api/assignments` (Phase 3, item 12)
- The daily task cap (Phase 3, item 13)
- Recurring routines (Phase 3, item 14)
- Unassign-vs-delete (Phase 3, item 16)
- Any renaming of `courses`/`modules` API paths

If you find yourself touching `_assign_to_students` or `AssignmentRepository.get_today`, stop — that is Phase 3.

---

## Known traps

1. **Trailing slashes.** `/api/tasks/`, `/api/courses/`, `/api/modules/`. See `stores/tasks.js:60–66`.
2. **`AssignmentRepository.list(db, tenant_id, unit_id=None)`** means "no unit filter", not "unit is null". `tasks.py:281` relies on this to scan every assignment in the tenant. Do not mistake it for a null filter.
3. **Blank form inputs come out of the DOM as `''`**, which fails validation against `Optional[date]` / `Optional[int]` with a 422. `TaskForm.vue:48` keeps a `NULL_WHEN_BLANK` list — extend it if you add nullable fields.
4. **`Lesson` is shared curriculum.** Anything written to `a.lesson` affects every student and every future year. Only `scheduled_date`, `is_completed`, `focus_minutes`, `completion_notes` and `date_locked` belong to the assignment.
5. **The XP ledger is append-only.** Never update or delete a row; a reversal is a new row with the opposite delta. `services/xp_service.py` has the helpers.
6. **Migrations:** the current head is **`17280a99fab3`** (`stuck_flags`) — chain your first migration off it. A boolean `server_default` must use the SQLAlchemy construct, not a Python literal: commit `76ed5c9` fixed exactly this Postgres rejection in `add_user_is_active`, landing on `server_default=sa.true()` (see `cd43933858c0:29`, which also notes that matching the model's `server_default` keeps `alembic check` clean). `date_locked` wants `server_default=sa.false()`, and `Unit.status` wants `server_default='active'`.

---

## Done when

- [ ] A program can be created, edited and deactivated from the admin UI
- [ ] Units can be created under a program, with `status`
- [ ] The scheduler skips `planned` / `completed` / `abandoned` units but still schedules unit-less lessons — with a test
- [ ] A lesson can be attached to a unit from the task form
- [ ] `PUT /api/tasks/{id}` with a partial body leaves unsent fields untouched — with a test
- [ ] `dependency_mode` is validated, consistent across all three layers, and existing rows migrated
- [ ] `school_days` lives in `app_config`; `day_of_week_hint` accepts 0–6
- [ ] A hand-placed Saturday assignment survives a sick-day recalculation — with a test
- [ ] `npm run test:e2e` passes
- [ ] `/health/ready` reports the new Alembic revision
