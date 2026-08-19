# Flokus Academy

A learning management system for exactly one classroom: one teacher, one student, Grade 5,
2026–27. It is a hub over third-party curricula — Beast Academy, Brave Writer, Tuttle Twins,
Critical Thinking Co., Chess.com, CrunchLabs, Outschool — not a curriculum of its own.

**This is one project in two versions, not two products.** V1 runs the school day today. V2 is
being built to replace it and cannot do the job yet. Nothing here is a fork and nothing has been
abandoned; V2 is where this is going, and V1 is what works while it gets there.

---

## Which version is which

|  | **V1 — running** | **V2 — in development** |
|---|---|---|
| Status | The only working version. Carries the 2026–27 school year. | Not usable yet. One phase of four is done. |
| Where | `archive_v1/streamlit_app/` — the folder name is wrong, see below | `backend/` and `frontend/` |
| Stack | Python · Streamlit · SQLite | Python · FastAPI · SQLAlchemy 2.0 async · Postgres · Alembic · Vue 3 · Vite · Pinia |
| Data | `archive_v1/streamlit_app/flokus.db`, untracked | Postgres, schema by Alembic migration |
| Deployed | Nowhere. It runs on the machine in the schoolroom. | Nowhere yet. Railway is the target. |
| Checked by | `audit_schedule.py`, run by hand after a rebuild | Playwright e2e and the migration chain, in CI |
| Accounts | One parent PIN, one student. No hosting, no accounts. | Multi-student in the model, not yet in the API |

### Why V1 is the one running

V1 was finished in time for the first day of school and V2 was not. That is the whole reason.

V1 is not the codebase I would lead with — a Streamlit app talking straight to SQLite, single
user by construction, a PIN on the parent view and nothing more. No hosting, no accounts, no
multi-student support. Those are exactly the reasons V2 exists. They are not reasons to have
waited: a school year does not wait for the good version.

**V1 keeps running until V2 can take over a school day without anyone noticing the change.**
Until that day, a change that has to reach Sonny this week goes into V1.

### What V2 changes

A real API, a real database, migrations, and a curriculum model that separates the lesson plan
from one student's progress through it — so a year can be reused without last year's history
following it. The import format is already shared: a curriculum file that loads into V1 loads
into V2 unchanged, which is the whole migration path.

Where V2 stands, phase by phase, is [`docs/BUILD_LOG.md`](docs/BUILD_LOG.md). It is the file a
working session should read first and update last.

---

## Two things in this repo are misnamed

**`archive_v1/` is not an archive.** It holds the system that runs the school day. The name is
staying until V2 takes over, because the Windows launchers, the database path, and a year of
muscle memory all point at it, and renaming a running system mid-year buys nothing. Read it as
*"v1, which is still in production"*.

The README inside that folder is older than this one and still says the app is "not deployed and
not maintained" and that the live system is V2 at `api.flokusacademy.com` / `app.flokusacademy.com`.
That was an intention, not a fact — those hosts serve nothing today. Believe this file over that one.

**There are two `flokus.db` files.** The live one is `archive_v1/streamlit_app/flokus.db`. The one
at the repository root is a stale copy from 13 August 2026, taken before the year was rebuilt.
Nothing reads it. Do not point anything at it.

Three point-in-time backups sit beside the live database, all untracked:

| File | What it holds |
|---|---|
| `flokus.db.original-677-backup` | The year as first generated — 677 assignments over 180 consecutive weekdays. Every "before" figure quoted anywhere comes from here. |
| `flokus.db.pre-rebuild-backup` | The state immediately before `rebuild_schedule_2026_27.py` ran |
| `flokus.db.empty-backup` | Schema, no rows |

---

## Where everything lives

| Path | What it is |
|---|---|
| `archive_v1/streamlit_app/` | **V1 — the running system** |
| `backend/` | V2 API — FastAPI, SQLAlchemy, Alembic |
| `frontend/` | V2 client — Vue 3 SPA |
| `docs/` | Every document meant to be read. See the table below. |
| `research_and_development/` | Inputs and shelved code, not prose: the curriculum workbooks, and `gamification/` |
| `.agents/skills/lms-architecture/SKILL.md` | Project context for an AI agent working in this repo. Describes V2's domain model and the traps in it. |
| `.github/workflows/ci.yml` | CI. Runs on `main` only, and covers V2 only — V1 has no CI. |
| `scratch/`, `uploads/`, `_to_delete/` | Untracked working space. Nothing here is load-bearing. |

### The documents

| Document | What it tells you | State |
|---|---|---|
| [`docs/SCHEDULE_2026-27.md`](docs/SCHEDULE_2026-27.md) | The year as it now stands — 38 weeks, 184 school days, 817 assignments, 24 days off, and the weekly rhythm | Current |
| [`docs/CURRICULUM.md`](docs/CURRICULUM.md) | Lesson-by-lesson listing of the year | **Superseded.** Describes the 677-assignment year from before the rebuild. Kept because it is the only prose record of that state. |
| [`docs/BUILD_LOG.md`](docs/BUILD_LOG.md) | Running state of the V2 build — phase table, exit criteria, decisions changed in flight | Current for V2. Says nothing about V1. |
| [`docs/PHASE1_BRIEF.md`](docs/PHASE1_BRIEF.md) | The V2 Phase 1 specification | Delivered 2026-08-17 |
| [`docs/Flokus_Academy_Curriculum_Review.md`](docs/Flokus_Academy_Curriculum_Review.md) | The architecture review the V2 phases are drawn from; defects numbered B1–B10 | Current |
| [`docs/academy-site-copy.md`](docs/academy-site-copy.md) | Copy for the Academy page on flokus.org | Current |
| [`CHANGELOG.md`](CHANGELOG.md) | What shipped, dated, both versions | Current |

---

## Running it

### V1 — the school day

```bash
cd archive_v1/streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

On Windows, `run_flokus.bat` does the same and `create_shortcut.bat` puts it on the desktop.
It needs its own `requirements.txt`, not the backend's, and it reads `flokus.db` from the
directory it is launched in.

Curriculum goes in and comes out as a spreadsheet, through `curriculum_io.py`. Nothing else
writes curriculum — that is deliberate, and it replaced three separate ways of adding work, one
of which regenerated the whole year from hardcoded Python. The year is laid out by
`rebuild_schedule_2026_27.py` against the calendar in `school_year.py`, then checked by
`audit_schedule.py` — seventeen checks, each one a defect that was actually present at some
point, so the audit doubles as a regression test.

The file the importer reads never sets a date. It says what to teach and in what order; the app
schedules it against the school calendar. An import cannot land on Christmas.

### V2 — in development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000
```

```bash
cd frontend
npm install
npm run dev                            # http://localhost:5173
npm run test:e2e                       # Playwright
```

Every schema change needs an Alembic migration; check `backend/alembic/versions/` for the current
head first. CI builds the migration chain from empty on every run, because incremental runs have
hidden bugs that a clean run catches.

---

## What was taken out, and where it went

The XP economy, the digital pet, and the battle/quest arena were pulled out of V1 on 2026-08-12,
before the school year started, and moved to `research_and_development/gamification/` with a note
on how to put them back. The reason was stability on day one, not a change of heart.

Smaller subtractions went with them: a countdown timer, a four-step completion ritual, a minimum
character count that had to be met before the checkbox would unlock, and double-XP boss fights.
An assignment in V1 is now three things — where the work is, a box to say what you learned, and a
checkbox.

No data was dropped. The `pet_status`, `pet_inventory`, `pet_unlocked_skills`, `pet_quests`,
`side_quests` and `quest_completions` tables are all still in `flokus.db`, and XP is still carried
on every lesson and still totals in the parent view.

---

## Status, plainly

- **V1** — in production, running the 2026–27 year since 19 August 2026. Single user, local, no
  hosting. The work that made it fit for the year is on the `school-year-2026-27` branch.
- **V2** — in development on `feat/phase-1-curriculum-authoring`. Phase 1 done, the manual pilot
  next, then the importer, then the release model. It has never run a school day.
- **The public page** — [flokus.org/academy](https://flokus.org/academy), written from
  [`docs/academy-site-copy.md`](docs/academy-site-copy.md).

Built and run by one person, for one household, in Moab, Utah.
