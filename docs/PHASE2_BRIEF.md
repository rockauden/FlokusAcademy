# Phase 2 Implementation Brief — The Importer

**For:** Claude Code, working in the `flokus-academy` repo
**Companion doc:** `docs/Flokus_Academy_Curriculum_Review.md` — read §5 (the ingest spec) and §7 (what the workbook contains) before starting. This brief is the executable subset.
**Branch:** `feat/phase-2-curriculum-import`
**Written:** 2026-08-25, after the Pilot passed. Reviewed by the product owner before building — do not start until it has been.

---

## Why this phase exists

Curriculum can now be authored one lesson at a time, and the Pilot proved the release
gate holds. But the year is 272 lessons across 30 units, and the only way in is still
one form at a time. Phase 2 builds the loading dock: a CSV goes in, gets validated with
row-numbered errors, previewed, and committed in one transaction — idempotently, so the
spreadsheet becomes the thing the curriculum is *maintained* in, not a one-shot seed.

**Definition of done:** the teacher exports one sheet of
`research_and_development/Flokus_Curriculum_v1_Migrated.xlsx` as CSV, imports it through
the UI, sees "N new, 0 errors", commits — and the student's day does not change, because
everything arrives staged. Re-importing the same file reports "0 new, N unchanged" and
writes nothing.

---

## Ground rules

- Same as Phase 1: house comment style; tenant-first repository rule; **zero new
  dependencies, backend or frontend** — the CSV is parsed with the stdlib `csv` module
  (`routers/expenses.py:2` already imports it).
- Every schema change gets an Alembic migration. Current head: **`c3a91d4e2f70`**.
- `npm run test:e2e` must pass (67+ tests) before this is done.
- **Importing never sets dates.** There is no `scheduled_date` column in the format.
  Assignments created by an import are staged (`scheduled_date IS NULL`); dates belong
  to release. This is the phase's first principle, not a detail.

## Already done — do not redo

- `Lesson.priority` shipped in Phase 1 (`c3a91d4e2f70`). Review §9 item 8 is one-third
  done; what remains of it is `source_key`, `import_id` and the unique constraint.
- `dependency_mode` is a validated `Literal` — the CSV column inherits that for free.
- `Unit.status` exists, so `unit_status` in the CSV maps straight onto it.

---

## Item 1 — Schema: `source_key`, `import_id`, and the constraint

```python
# Lesson
source_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
import_id:  Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
__table_args__ = (UniqueConstraint('tenant_id', 'source_key', name='uix_tenant_source_key'),)
```

One migration, chained off `c3a91d4e2f70`, DDL-only — no data backfill, so no RLS
tenant-binding dance is needed this time. Existing hand-authored lessons keep
`source_key = NULL`, and both SQLite and Postgres allow any number of NULLs under a
unique constraint, so nothing existing can collide.

`source_key` derivation, when the CSV leaves it blank:

```
source_key = slug(program) + "|" + slug(unit) + "|" + slug(title)
```

This is the idempotency key (review §5.4): it is what makes re-import an update instead
of a duplication, and the preview honest ("12 new, 168 unchanged, 3 updated").

**Acceptance:** `alembic check` clean; the chain applies from empty; two lessons with
the same derived key in one file are refused at validation with both row numbers.

---

## Item 2 — The validate/commit service

A pure service module (`services/curriculum_import.py`), so the parsing and validation
are testable without HTTP.

**Canonical columns** — exactly review §5.2. Required: `program`, `unit`, `title`.
Everything else optional with defaults. Three behaviours worth restating:

- `program` matches an existing Program by **title or platform, case-insensitive** —
  never by ID. Unknown program → reported as "will create" in the preview, not an error.
- `unit_status` / `unit_week_start` / `unit_week_end` are read from the **first row of
  each unit** and ignored elsewhere. Default `unit_status`: **`planned`** — the review
  says `active`, but the Load step imports the whole year and the whole point is that
  imported units stay dark until released. Deviating from §5.2 here is deliberate;
  record it in BUILD_LOG when building.
- `day_of_week_hint` is `Mon`–`Sun` text in the file, converted to 0–6 at the boundary.

**Validation returns errors keyed by row number** — "row 47: unknown task_type
'reeding'" — plus the resolution summary: programs/units to create, lessons new /
unchanged / updated, duplicate keys. One malformed row never hides the report for the
rest.

**Commit** takes the validated payload and writes it in **one transaction with one
flush** — not a flush per row (`tasks.py:170–181` is the anti-pattern). Every created
lesson gets the same fresh `import_id` (uuid4). Assignments are created through the
existing fan-out path, **undated**. Returns the `import_id` and the same summary the
preview showed.

**Re-import semantics — the heart of the phase:** a row whose `source_key` already
exists *updates the Lesson's authoring fields only* (title, minutes, XP, type, priority,
sequence, resources). It must never touch Assignment state — `scheduled_date`,
`is_completed`, `focus_minutes`, `completion_notes`, `date_locked` all survive, and the
XP ledger is not consulted at all. A byte-identical row is a no-op and counts as
"unchanged".

**Acceptance:** importing a file twice produces identical database state to importing it
once; correcting one cell and re-importing updates that lesson and reports "1 updated,
N-1 unchanged"; a completed assignment's completion survives a re-import of its lesson.

---

## Item 3 — The endpoints

```
POST /api/curriculum/validate   body: {"csv_text": "..."}  → the report, no writes
POST /api/curriculum/commit     body: {"csv_text": "..."}  → validates again, then writes; returns import_id
POST /api/curriculum/rollback   body: {"import_id": "..."} → undoes one import
```

Three endpoints, not four — with one input format there is nothing for a separate
`/parse` to do (review §5.3). Teacher-only, same guard as the other admin routers.
Commit re-validates server-side rather than trusting a client-held report: the database
may have changed since the preview.

**Wire format is CSV text inside JSON** (review §5.5): the browser reads the file with
`FileReader` and posts the text. No multipart, no `aiofiles`, H-06 stays intact.

**Rollback** deletes the lessons carrying that `import_id` — which cascades to their
assignments, the exact B8 behaviour that is dangerous everywhere else and is the point
here. Two guards: it refuses if any assignment under the import is completed (report
which, by lesson title), unless `{"force": true}` — and with force it reverses the XP
through `xp_service.reverse_xp_for_source` *before* deleting, so the ledger stays
append-only and honest. Units and programs created by the import are left in place;
empty units are harmless and deleting them is the exact damage the unit manager
deliberately refuses.

**Acceptance:** rollback of a fresh import leaves the database as it was; rollback with
completed work refuses without `force` and reverses XP with it.

---

## Item 4 — The import screen

`frontend/src/views/admin/ImportView.vue`, route `/admin/import`, nav link under
"📝 Manage". The flow:

```
choose .csv → FileReader → POST /validate → preview → POST /commit → result + import_id
```

The preview shows the summary line ("will create 1 program, 4 units, 72 lessons — 0
errors"), the row-numbered errors when there are any, and the parsed rows in a grid.
Cells in error rows are editable in place; editing re-validates. **Commit stays disabled
while any error remains.** Keep the grid plain — this is a checkpoint, not a spreadsheet
editor; anything more than fixing a typo belongs back in the workbook.

After a successful commit, show the `import_id` with the rollback affordance next to it,
labelled for what it is: "Undo this import".

**Acceptance (e2e):** a fixture CSV with one bad row shows that row's number and refuses
commit; fixing the cell in the grid enables commit; after commit the lessons exist, the
assignments are undated, and the student's day is unchanged.

---

## Order of work

```
1  ──► schema + migration            (independent, small — do first)
2  ──► service: parse/validate/plan  (pure functions, testable without HTTP)
3  ──► endpoints                     (thin wrappers over 2)
4  ──► import screen                 (needs 3)
```

---

## Out of scope — do not build these here

- Recurring routines — the 14 definitions wait for Phase 3. Importing them as lessons
  is the 412-row clutter the migration analysis exists to prevent.
- The author/assign/release split, day cap, release-by-priority, unassign (Phase 3).
- `.xlsx` parsing anywhere — the workbook exports a sheet as CSV; that is the path.
- PDF parsing anywhere, ever (review §5.1 — cut as over-built, stays cut).
- Any renaming of `courses`/`modules` API paths.

---

## Known traps

1. **Excel's CSV export starts with a BOM** (`﻿`) and uses CRLF line endings. Parse
   with a BOM strip (or decode `utf-8-sig`) before `csv.reader`, or the first header
   reads as `﻿program` and every row fails with "unknown column". This will happen
   on the very first real file.
2. **Trailing slashes** on the new collection routes: `/api/curriculum/validate` etc.
   are actions, not collections — but be consistent and test through the proxy path the
   way `stores/tasks.js:60–66` documents.
3. **Blank CSV cells arrive as `''`**, the same trap as the form: normalise to `None`
   before Pydantic sees them.
4. **`slug()` collisions are a validation error, not a merge.** Two different lessons
   that slug identically ("Ch. 3: Review!" / "Ch 3 Review") must be reported with both
   row numbers, or the second silently overwrites the first on every re-import forever.
5. **Update means Lesson fields only.** The moment re-import touches an Assignment
   column, completion history dies on the next typo fix. Write the regression test
   before the update path.
6. **One transaction, one flush.** 272 rows with a flush per row is the N+1 the review
   called out; build commit around a single `flush()` from the start.

---

## Done when

- [ ] Migration lands `source_key` + `import_id` + the tenant/source_key constraint; `alembic check` clean
- [ ] A workbook sheet exported from Excel (BOM and all) validates with zero errors
- [ ] Errors come back keyed by row number — with a test malforming one row
- [ ] Re-importing an unchanged file is a no-op; a corrected file updates without touching completion history or XP — with tests
- [ ] Commit is one transaction, one flush, and returns an `import_id`
- [ ] Rollback undoes a fresh import; refuses completed work without `force`; reverses XP with it
- [ ] The import screen previews, blocks on errors, commits, and offers undo
- [ ] Imported assignments are undated and the student's day is unchanged — the staged year
- [ ] `npm run test:e2e` passes; `/health/ready` reports the new revision after deploy
