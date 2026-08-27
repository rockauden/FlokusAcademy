# Flokus Academy

A learning management system for exactly one classroom: one teacher, one student,
Grade 5, 2026–27. It is a hub over third-party curricula — Beast Academy, Brave
Writer, Tuttle Twins, Critical Thinking Co., Chess.com, CrunchLabs, Outschool —
not a curriculum of its own.

**This is one project in two versions, not two products.** V1 runs the school day
today. V2 is being built to replace it. Nothing here is a fork and nothing has
been abandoned; V2 is where this is going, and V1 is what works while it gets
there.

---

## What V2 is, in one paragraph

The teacher plans **one week at a time, by hand**. Classes down the side, Monday
to Friday across the top; click a cell and type what Sonny does for that class
that day. Nothing is imported, nothing is scheduled automatically, and nothing
moves work he has placed. That is the entire authoring model, and it arrived by
subtraction: V2 previously had a CSV curriculum importer, unit staging and
release, and a rolling scheduler, all of which were built, deployed and then
removed on 26–27 August 2026 because they solved a problem this household does
not have. **One student doing four or five things a day is fifteen lines of
typing on a Sunday.** The reasoning is in [`docs/BUILD_LOG.md`](docs/BUILD_LOG.md);
read it before adding anything back.

---

## Which version is which

|  | **V1 — running** | **V2 — in development** |
|---|---|---|
| Status | The only version that has run a school day. Carries the 2026–27 year. | Deployed and usable for planning; has not yet run a school day. |
| Where | `archive_v1/streamlit_app/` — the folder name is wrong, see below | `backend/` and `frontend/` |
| Stack | Python · Streamlit · SQLite | FastAPI · SQLAlchemy 2.0 async · Postgres · Alembic · Vue 3 · Vite · Pinia |
| Data | `archive_v1/streamlit_app/flokus.db`, untracked | Postgres, schema by Alembic migration |
| Deployed | Nowhere. It runs on the machine in the schoolroom. | Railway — `api.flokusacademy.com` / `app.flokusacademy.com` |
| Checked by | `audit_schedule.py`, run by hand after a rebuild | 61 Playwright e2e tests and the migration chain, in CI |
| Accounts | One parent PIN, one student. No hosting, no accounts. | Multi-student in the model, not yet in the API |

### Why V1 is still the one running

V1 was finished in time for the first day of school and V2 was not. That is the
whole reason.

V1 is not the codebase I would lead with — a Streamlit app talking straight to
SQLite, single user by construction, a PIN on the parent view and nothing more.
Those are exactly the reasons V2 exists. They are not reasons to have waited: a
school year does not wait for the good version.

**V1 keeps running until V2 can take over a school day without anyone noticing
the change.** Until that day, a change that has to reach Sonny this week goes
into V1. As of 27 August 2026 the workflow objection that kept V2 out of daily
use is gone, so the cutover is a live question rather than a distant one.

---

## Two things in this repo are misnamed

**`archive_v1/` is not an archive.** It holds the system that runs the school
day. The name is staying until V2 takes over, because the Windows launchers, the
database path, and a year of muscle memory all point at it. Read it as *"v1,
which is still in production"*.

The README inside that folder is older than this one and describes a deployment
story that was never true. Believe this file over that one.

**The API says `courses` and `modules`; the teacher says "class".** The UI was
renamed and the API paths were not, deliberately — renaming them is its own
migration, not a drive-by. `Unit` (`modules`) is dormant: still in the database,
used by nothing.

---

## Where everything lives

| Path | What it is |
|---|---|
| `archive_v1/streamlit_app/` | **V1 — the running system** |
| `backend/` | V2 API — FastAPI, SQLAlchemy, Alembic |
| `frontend/` | V2 client — Vue 3 SPA |
| `docs/` | Every document meant to be read. See the table below. |
| `research_and_development/` | Inputs and shelved code: the curriculum workbooks, the CSVs exported from them while the importer existed, and `gamification/` |
| `.agents/skills/lms-architecture/SKILL.md` | Project context for an AI agent working in this repo. **Load it before any change.** |
| `.github/workflows/ci.yml` | CI. Runs on `main` only, and covers V2 only — V1 has no CI. |
| `scratch/`, `uploads/`, `_to_delete/` | Untracked working space. Nothing here is load-bearing. |

### The documents

| Document | What it tells you | State |
|---|---|---|
| [`docs/BUILD_LOG.md`](docs/BUILD_LOG.md) | **The running state of V2, and the record of what changed and why.** The first thing to read. | Current |
| [`CHANGELOG.md`](CHANGELOG.md) | What shipped, dated, both versions | Current |
| [`docs/SCHEDULE_2026-27.md`](docs/SCHEDULE_2026-27.md) | V1's year as it stands — 38 weeks, 184 school days, 817 assignments | Current, and about V1 |
| [`docs/CURRICULUM.md`](docs/CURRICULUM.md) | Lesson-by-lesson listing of an earlier V1 year | Superseded |
| [`docs/Flokus_Academy_Curriculum_Review.md`](docs/Flokus_Academy_Curriculum_Review.md) | The architecture review V2's phases were drawn from | **Superseded.** Its recommendations were built, then removed. |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | The August consolidation roadmap | **Superseded.** Executed through step 4, then overtaken. |
| [`docs/PHASE1_BRIEF.md`](docs/PHASE1_BRIEF.md) | Curriculum authoring — programs, units, the calendar model | Delivered; mostly since removed |
| [`docs/PHASE2_BRIEF.md`](docs/PHASE2_BRIEF.md) | The CSV importer | Delivered 2026-08-25, removed 2026-08-27 |
| [`docs/PHASE3_BRIEF.md`](docs/PHASE3_BRIEF.md) | Paste-to-add, unit rhythms, the week planner | Superseded mid-flight; only the planner was built |
| [`docs/academy-site-copy.md`](docs/academy-site-copy.md) | Copy for the Academy page on flokus.org | **Stale** — describes V2 as a curriculum system |

Superseded documents are kept, each labelled at the top. They are the record of
how the design got here, and several of them explain decisions that are still
load-bearing. They are history, not instructions.

---

## Running it

### V2 — locally

Two programs: the API on port 8000, and the web client on 5173 which forwards
anything under `/api` to it. Both must be running.

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt          # .venv/bin/pip on macOS/Linux
.venv/Scripts/python scripts/run_test_api.py --port 8000
```

```bash
cd frontend
npm install
npm run dev                            # http://localhost:5173
npm run test:e2e                       # Playwright — 61 tests
```

`run_test_api.py` builds a **fresh throwaway SQLite database on every start**,
seeded with the two accounts and the nine original classes. It cannot reach
production data, and nothing typed into it survives a restart. Local PINs are
`1234` (Dad) and `4321` (Sonny).

Every schema change needs an Alembic migration; check
`backend/alembic/versions/` for the current head first (`e5a2b8d17c40`). CI
builds the migration chain from empty on every run, because incremental runs
hide bugs that a clean run catches.

### V1 — the school day

```bash
cd archive_v1/streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

On Windows, `run_flokus.bat` does the same and `create_shortcut.bat` puts it on
the desktop. It needs its own `requirements.txt`, not the backend's, and it reads
`flokus.db` from the directory it is launched in.

Curriculum goes in and comes out as a spreadsheet, through `curriculum_io.py`.
The year is laid out by `rebuild_schedule_2026_27.py` against the calendar in
`school_year.py`, then checked by `audit_schedule.py` — seventeen checks, each
one a defect that was actually present at some point, so the audit doubles as a
regression test.

---

## Status, plainly

- **V1** — in production, running the 2026–27 year since 19 August 2026. Single
  user, local, no hosting.
- **V2** — deployed at `app.flokusacademy.com`, on `main`. The week planner is in
  real use for planning; V2 has not yet run a school day.
- **The public page** — [flokus.org/academy](https://flokus.org/academy), written
  from [`docs/academy-site-copy.md`](docs/academy-site-copy.md), which now
  describes a version of V2 that no longer exists.

Built and run by one person, for one household, in Moab, Utah.
