# Flokus Academy — Consolidation Roadmap

**Written:** 24 August 2026, week 2 of the school year
**Question this answers:** how the code that exists today becomes one stable, simple LMS at app.flokusacademy.com
**Reads with:** `docs/BUILD_LOG.md` (per-session state — this file does not replace it) and `docs/Flokus_Academy_Curriculum_Review.md` (the plan the phases come from)

---

## 1. Where things actually stand

The feeling of "a mess of code" is mostly wrong, and it is worth saying why before listing the work.
There is one project in two versions, a written phase plan with exit criteria, a migrated
curriculum workbook, and a repo whose documentation is better than most commercial products'.
What *is* messy is small and specific: the work lives on four branches, production is running
older code than anyone realized, and three documents disagree with reality in one place each.

**V1** (`archive_v1/streamlit_app/`) is running the school year — 817 assignments, 184 school
days, audited by seventeen checks. It is doing its job. Sonny finding it dry is not a defect to
fix in V1: the fun was *deliberately removed* from it on 12 August for day-one stability, and
the plan was always that the good student experience arrives with V2. Section 5 below is the
student-experience track.

**V2 is already deployed, and the README is wrong about this.** Checked 24 August:

- `https://api.flokusacademy.com/health` → `{"status":"ok"}`
- `https://api.flokusacademy.com/health/ready` → `{"status":"ready","database":"ok","migration":"17280a99fab3"}`
- `https://app.flokusacademy.com` serves the Vue app

`README.md` says "those hosts serve nothing today." They serve something — but the migration
revision is the tell: **production is at `17280a99fab3` (stuck_flags), which is pre-Phase-1.**
Everything Phase 1 built — the program/unit managers, the calendar model, `date_locked`, the
TaskUpdate fix, the scheduler's unit-status guard — exists only on branches. Production has the
old data-loss and date-stomping bugs Phase 1 fixed.

**The branch picture** resolves cleanly. `school-year-2026-27` (the current branch) contains
*everything*: all of `main`, all 7 commits of `feat/phase-1-curriculum-authoring`, plus the V1
rebuild and the docs. Verified: `git rev-list --count school-year-2026-27..feat/phase-1-curriculum-authoring`
is 0, and `main..school-year-2026-27` is 11. `hardening/phase-1-2-production-readiness` is
already fully merged into `main`. So consolidation is one merge, not an archaeology project.

---

## 2. The path, in order

Each step is small, verifiable, and useful on its own. Steps 2–5 are the existing phase plan
from BUILD_LOG, unchanged — this roadmap adds steps 0, 1, 6 and 7 around them.

### Step 0 — Make `main` whole again *(one sitting)*

Merge `school-year-2026-27` into `main`. It is a superset of every branch, so this is
conflict-free by construction. Then delete `feat/phase-1-curriculum-authoring` and
`hardening/phase-1-2-production-readiness` (both fully contained in the new `main`) and keep
`school-year-2026-27` only if Railway or muscle memory still points at it. From here on, one
branch is the truth and short-lived feature branches come and go against it.

Also in this sitting, the three documentation corrections: README's "hosts serve nothing"
paragraph, the stale root `flokus.db` (nothing reads it — delete it or move it to `scratch/`),
and the two untracked walkthrough HTML files at the repo root (commit them under `docs/` or
move them to `scratch/`; untracked files at the root are how a repo starts feeling messy).

### Step 1 — Deploy, and settle the Postgres question *(one sitting, do it while fresh)*

The deploy of the new `main` is also the answer to the oldest open risk in BUILD_LOG: the three
Phase 1 migrations (`a1c4e7b9d203` → `b2f5083ac611` → `c3a91d4e2f70`) have only ever run on
SQLite. `railway.toml` already runs `alembic upgrade head` as a pre-deploy step that blocks the
release on failure, which is exactly right. The verification procedure is already written in
BUILD_LOG and takes two minutes:

1. `https://api.flokusacademy.com/health/ready` reports `c3a91d4e2f70`
2. `GET /api/config/` returns `school_days` — a silently-skipped RLS insert would look like
   the Mon–Thu fallback instead

If the migration step fails, Railway keeps serving the old version; fix and redeploy. Nothing
about this step touches V1 or the school day.

### Step 2 — The Pilot *(an evening; no code)*

Exactly as BUILD_LOG specifies: hand-enter Tuttle Twins Vol 1 through the new admin UI —
program, four units, Vol 1 `active`, Vols 2–3 `planned` — then add a sick day and confirm only
Vol 1's assignments moved and the student view shows only Vol 1 work. This is the manual proof
that Phase 1 actually works, and it is the gate the importer is waiting on. Run it against
production now that Step 1 is done — that way it also proves the deployed system, not just a
local one.

### Step 3 — Phase 2: the importer *(the next real build)*

The spec is complete in the review doc §5: canonical CSV row, `source_key` idempotency,
`/validate` with row-numbered errors, `/commit` in one transaction, editable preview. Write
`docs/PHASE2_BRIEF.md` first, per the BUILD_LOG process, reading the "decisions changed in
flight" section — `priority` already shipped in Phase 1, so item 8 is one-third done. Exit
criteria are already written: re-importing an unchanged CSV is a no-op; a corrected re-import
updates without touching completion history or XP; a malformed row reports its row number.

### Step 4 — Load the year *(a weekend)*

Import `research_and_development/Flokus_Curriculum_v1_Migrated.xlsx` — 272 lessons across 30
units — subject by subject, every unit `planned` except the current one per program. The
student's day stays empty throughout, which is the point: the exit criterion is "the full
workbook is in and Sonny's V2 day is still clean." The 14 routines wait for Step 5; do not
import them as lessons — that is precisely the 412-row clutter the migration analysis undid.

### Step 5 — Phase 3: protect the student *(the step that fixes "not intuitive")*

The release model (author/assign/release split), the day cap with oldest-first catch-up,
recurring routines, release-by-priority, and unassign-distinct-from-delete. This is where the
14 routines land, where Chess.com becomes a slot instead of 89 rows, and where the day view
becomes structurally incapable of greeting a nine-year-old with a wall of overdue work. Most of
what makes V1 feel unintuitive to Sonny is answered here, not by decorating V1.

### Step 6 — The parallel week, then cutover

The README's own bar: *V2 takes over when it can run a school day without anyone noticing the
change.* Make that a concrete test: pick one normal week, run it in V2 alongside V1 — same
lessons, Sonny works from the V2 day view, Dad marks completion in both — and log every point
of friction. If the week passes without reaching for V1, the next Monday is the cutover: V1
becomes read-only reference, `archive_v1/` finally earns its name, and the year's completion
history to date either stays in V1 as the record for those weeks or is imported as completed
assignments (decide then; the XP ledger makes either safe).

### Step 7 — Phase 4, and making it fun

BA Level 3 units imported as `planned` (the mid-year jump becomes a click), `grade_level` on
the portfolio header before the first UFA report — and then, with the core loop stable, the
gamification track: XP visibly earned with the existing celebration/count-up components,
streaks, and Sparky-style pet presentation rebuilt for Vue. The quarantined Streamlit code in
`research_and_development/gamification/` is the *design reference*, not code to port — the
non-negotiable stands: gamification is XP, streaks, pets and rewards, presentation only, and
earned XP stays earned.

---

## 3. The Sonny track (runs alongside, costs almost nothing)

"Not intuitive or fun" is the most valuable data the project has, and it deserves better than a
guess. Before Phase 3 is designed, sit with him for fifteen minutes and get three concrete
frictions — where he clicks and nothing happens, what he has to ask about, what he skips. Feed
those into the Phase 3 brief as acceptance criteria. The structural fixes are already planned
(the day cap, routines, a calm four-card morning); the interview is what catches the things a
plan can't see, like a confusing label or a completion flow with one step too many. The fun
returns in Step 7, on V2, where it can be built once and kept.

---

## 4. Guardrails — cheap to state, expensive to violate

- **V1 changes only when the school week needs them.** Everything else goes into V2.
- **No third ingest path.** Spreadsheet bulk + single form. PDFs get parsed outside the app.
- **No API renames** (`courses`/`modules` stay) as a drive-by; it is its own migration, later.
- **The XP ledger is append-only**, and archiving/abandoning/swapping never reverses earned XP.
- **Never put student state on `Lesson`.**
- **Importing never sets dates.** Dates belong to release.

---

## 5. Suggested pace

School is running, so the build happens in evenings and weekends. A realistic shape: Steps 0–2
this week (they are hours, not days, and Step 2 needs no code); Phase 2 over the next one to
two weeks; the load the weekend after; Phase 3 through late September; the parallel week in
early October, cutover after fall break at the latest. If it slips, it slips — V1 holds the
year, which is exactly what it is for. The one thing not to postpone is Step 1, because every
week of authoring into pre-Phase-1 production is a week of exposure to the update-resets-fields
bug Phase 1 already fixed.
