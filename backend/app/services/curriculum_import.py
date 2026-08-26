"""The curriculum importer: CSV in, validated plan out, one-transaction commit.

Design constraints this module answers to (review doc §5, PHASE2_BRIEF):

- Parsed with the stdlib `csv` module — `pandas` was deliberately removed and
  stays removed. The text arrives inside a JSON body, never as an upload.
- Errors are keyed by *spreadsheet* row number. "Row 47: unknown task_type"
  is actionable; a bare 422 for a 180-row file is not. Row 1 is the header,
  so the first data row is 2 — the same number the row has in Excel.
- `source_key` makes the whole thing idempotent: an unchanged file is a
  no-op, a corrected file is an update, and the preview can honestly say
  "12 new, 168 unchanged, 3 updated".
- Importing never sets dates. There is no scheduled_date column, and every
  assignment this module creates is staged (`scheduled_date IS NULL`) —
  invisible to the student until a unit is activated and the schedule
  recalculated. Dates belong to release.
- An update touches Lesson authoring fields only. Assignment state —
  dates, pins, completion, notes, minutes — and the XP ledger are never
  written by a re-import. That is the property that makes re-importing safe
  enough to do casually, which is the entire point.
"""
import csv
import io
import re
from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Assignment, Lesson, Program, Unit
from app.repository import LessonRepository, ProgramRepository, UnitRepository
from app.services.xp_service import reverse_xp_for_source

# Same source_type the tasks router uses for awards, so a rollback reversal
# finds exactly the rows a completion wrote.
ASSIGNMENT_SOURCE_TYPE = 'assignment'

REQUIRED_COLUMNS = ('program', 'unit', 'title')

# The canonical row (review §5.2). Anything else in the header is refused by
# name — a misspelled optional column that was silently ignored would look
# exactly like data loss to the person who filled it in.
KNOWN_COLUMNS = REQUIRED_COLUMNS + (
    'unit_status', 'unit_week_start', 'unit_week_end',
    'description', 'task_type', 'priority', 'sequence_order',
    'estimated_minutes', 'xp_reward', 'is_boss_fight', 'medium',
    'dependency_mode', 'day_of_week_hint', 'resource_url',
    'workbook_pages', 'ufa_eligible', 'ufa_hours_credit', 'source_key',
)

TASK_TYPES = {'reading', 'lesson', 'practice', 'quiz', 'project', 'build', 'live', 'review'}
PRIORITIES = {'core', 'standard', 'optional'}
MEDIUMS = {'online', 'offline'}
DEPENDENCY_MODES = {'independent', 'teacher_led', 'live_scheduled'}
UNIT_STATUSES = {'planned', 'active', 'completed', 'abandoned'}
# Text in the file, integer in the model — Mon-Thu paces within the core
# week, Fri-Sun deliberately places on an optional day (B10).
DAY_HINTS = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}
TRUTHY = {'yes', 'true', '1', 'y'}
FALSY = {'no', 'false', '0', 'n', ''}

# The Lesson fields a re-import may overwrite. Everything else on the row —
# and everything on Assignment — is out of the importer's reach by
# construction: this tuple is the write-surface, not a convention.
LESSON_UPDATE_FIELDS = (
    'title', 'description', 'task_type', 'priority', 'sequence_order',
    'estimated_minutes', 'xp_reward', 'is_boss_fight', 'medium',
    'dependency_mode', 'day_of_week_hint', 'resource_url', 'workbook_pages',
    'ufa_eligible', 'ufa_hours_credit',
)


def slugify(text: str) -> str:
    """Lowercase, runs of non-alphanumerics collapsed to single hyphens.

    Stable across the punctuation people actually vary ("Ch. 3: Review!" and
    "Ch 3 Review" slug identically) — which is why two *different* lessons
    that collide is a validation error, not a merge: silence here would mean
    the second row overwrites the first on every re-import forever.
    """
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def derive_source_key(program: str, unit: str, title: str) -> str:
    return f"{slugify(program)}|{slugify(unit)}|{slugify(title)}"


@dataclass
class RowIssue:
    row: int
    message: str


@dataclass
class ParsedRow:
    row: int                 # spreadsheet row number (header = 1)
    values: dict             # normalised lesson fields, model vocabulary
    program: str
    unit: str
    unit_status: Optional[str]
    unit_week_start: Optional[int]
    unit_week_end: Optional[int]
    source_key: str
    action: str = 'new'      # 'new' | 'update' | 'unchanged'


@dataclass
class ImportPlan:
    errors: list[RowIssue] = field(default_factory=list)
    rows: list[ParsedRow] = field(default_factory=list)
    programs_to_create: list[str] = field(default_factory=list)
    units_to_create: list[str] = field(default_factory=list)
    new: int = 0
    updated: int = 0
    unchanged: int = 0

    @property
    def total_rows(self) -> int:
        return len(self.rows)


def _parse_int(raw: str, name: str, row: int, errors: list[RowIssue]) -> Optional[int]:
    try:
        return int(raw)
    except ValueError:
        errors.append(RowIssue(row, f"{name} must be a whole number, got '{raw}'"))
        return None


def _parse_rows(csv_text: str) -> tuple[list[ParsedRow], list[RowIssue]]:
    """CSV text → normalised rows + row-numbered problems. Pure, no database.

    lstrip('\\ufeff') strips the byte-order mark Excel writes at the start of
    every CSV it exports. Without it the first header parses as '\\ufeffprogram',
    the required-column check fails, and the very first real file anyone
    imports is rejected with an error that names a column they can see is
    there. CRLF line endings are the csv module's problem, and it handles them.
    """
    errors: list[RowIssue] = []
    reader = csv.DictReader(io.StringIO(csv_text.lstrip('\ufeff')))

    header = [h.strip() for h in (reader.fieldnames or [])]
    if not header or header == ['']:
        return [], [RowIssue(1, "The file is empty — no header row found.")]

    missing = [c for c in REQUIRED_COLUMNS if c not in header]
    if missing:
        errors.append(RowIssue(1, f"Missing required column(s): {', '.join(missing)}"))
    unknown = [c for c in header if c and c not in KNOWN_COLUMNS]
    if unknown:
        errors.append(RowIssue(
            1,
            f"Unknown column(s): {', '.join(unknown)} — a misspelled optional "
            f"column would otherwise be silently ignored.",
        ))
    if errors:
        return [], errors

    rows: list[ParsedRow] = []
    for index, raw in enumerate(reader):
        row_num = index + 2  # header is row 1; matches the spreadsheet's own numbering
        # Blank cells arrive as '' (or None for a short row) — normalise once,
        # the same trap the task form documents for the DOM.
        cell = {k: (v or '').strip() for k, v in raw.items() if k is not None}
        # Excel routinely leaves trailing blank lines on export. A fully empty
        # row is noise, not three "required and blank" errors.
        if not any(cell.values()):
            continue
        row_errors: list[RowIssue] = []

        program = cell.get('program', '')
        unit = cell.get('unit', '')
        title = cell.get('title', '')
        for name, value in (('program', program), ('unit', unit), ('title', title)):
            if not value:
                row_errors.append(RowIssue(row_num, f"{name} is required and is blank"))

        values: dict = {'title': title, 'description': cell.get('description', '')}

        task_type = cell.get('task_type', '') or 'lesson'
        if task_type not in TASK_TYPES:
            row_errors.append(RowIssue(
                row_num, f"unknown task_type '{task_type}' (one of: {', '.join(sorted(TASK_TYPES))})"
            ))
        values['task_type'] = task_type

        priority = cell.get('priority', '') or 'standard'
        if priority not in PRIORITIES:
            row_errors.append(RowIssue(
                row_num, f"unknown priority '{priority}' (one of: core, standard, optional)"
            ))
        values['priority'] = priority

        medium = cell.get('medium', '') or 'offline'
        if medium not in MEDIUMS:
            row_errors.append(RowIssue(row_num, f"unknown medium '{medium}' (online or offline)"))
        values['medium'] = medium

        mode = cell.get('dependency_mode', '') or 'independent'
        if mode not in DEPENDENCY_MODES:
            row_errors.append(RowIssue(
                row_num,
                f"unknown dependency_mode '{mode}' (one of: independent, teacher_led, live_scheduled)",
            ))
        values['dependency_mode'] = mode

        hint = cell.get('day_of_week_hint', '')
        if hint:
            key = hint[:3].lower()
            if key not in DAY_HINTS:
                row_errors.append(RowIssue(row_num, f"day_of_week_hint '{hint}' is not a weekday (Mon-Sun)"))
            else:
                values['day_of_week_hint'] = DAY_HINTS[key]
        else:
            values['day_of_week_hint'] = None

        values['sequence_order'] = (
            _parse_int(cell['sequence_order'], 'sequence_order', row_num, row_errors)
            if cell.get('sequence_order') else index  # blank → row order within the file
        )
        values['estimated_minutes'] = (
            _parse_int(cell['estimated_minutes'], 'estimated_minutes', row_num, row_errors)
            if cell.get('estimated_minutes') else 30
        )
        values['xp_reward'] = (
            _parse_int(cell['xp_reward'], 'xp_reward', row_num, row_errors)
            if cell.get('xp_reward') else 10
        )

        for name, default in (('is_boss_fight', False), ('ufa_eligible', True)):
            raw_bool = cell.get(name, '').lower()
            if raw_bool in TRUTHY:
                values[name] = True
            elif raw_bool in FALSY:
                values[name] = default if raw_bool == '' else False
            else:
                row_errors.append(RowIssue(row_num, f"{name} must be yes/no, got '{cell.get(name)}'"))

        hours = cell.get('ufa_hours_credit', '')
        if hours:
            try:
                values['ufa_hours_credit'] = float(hours)
            except ValueError:
                row_errors.append(RowIssue(row_num, f"ufa_hours_credit must be a number, got '{hours}'"))
        else:
            values['ufa_hours_credit'] = 0.0

        values['resource_url'] = cell.get('resource_url', '')
        values['workbook_pages'] = cell.get('workbook_pages', '')

        unit_status = cell.get('unit_status', '') or None
        if unit_status and unit_status not in UNIT_STATUSES:
            row_errors.append(RowIssue(
                row_num, f"unknown unit_status '{unit_status}' (one of: {', '.join(sorted(UNIT_STATUSES))})"
            ))

        week_start = (
            _parse_int(cell['unit_week_start'], 'unit_week_start', row_num, row_errors)
            if cell.get('unit_week_start') else None
        )
        week_end = (
            _parse_int(cell['unit_week_end'], 'unit_week_end', row_num, row_errors)
            if cell.get('unit_week_end') else None
        )

        source_key = cell.get('source_key', '') or (
            derive_source_key(program, unit, title) if not row_errors else ''
        )

        errors.extend(row_errors)
        if not row_errors:
            rows.append(ParsedRow(
                row=row_num, values=values, program=program, unit=unit,
                unit_status=unit_status, unit_week_start=week_start,
                unit_week_end=week_end, source_key=source_key,
            ))

    # Duplicate keys inside one file: report every colliding row, because the
    # alternative is that the last one silently wins on every future import.
    seen: dict[str, int] = {}
    for parsed in rows:
        if parsed.source_key in seen:
            errors.append(RowIssue(
                parsed.row,
                f"duplicate source_key '{parsed.source_key}' — same program/unit/title "
                f"as row {seen[parsed.source_key]}. Retitle one, or give them explicit "
                f"source_key values.",
            ))
        else:
            seen[parsed.source_key] = parsed.row

    return rows, errors


def _lessons_differ(lesson: Lesson, values: dict) -> bool:
    return any(getattr(lesson, name) != values[name] for name in LESSON_UPDATE_FIELDS)


async def build_plan(db: AsyncSession, tenant_id: int, csv_text: str) -> ImportPlan:
    """Parse, validate, and resolve against the database. Writes nothing."""
    rows, errors = _parse_rows(csv_text)
    plan = ImportPlan(errors=errors, rows=rows)

    # Programs are matched by title or platform, case-insensitively — never by
    # id. The person filling in the spreadsheet knows their program is called
    # "Beast Academy"; nobody should need to know it is course_id 1.
    programs = await ProgramRepository.list(db, tenant_id, active_only=False)
    by_name: dict[str, Program] = {}
    for p in programs:
        by_name[p.title.lower()] = p
        by_name.setdefault(p.platform.lower(), p)

    known_units: dict[tuple[str, str], Unit] = {}
    for p in programs:
        for u in await UnitRepository.list(db, tenant_id, program_id=p.id, active_only=False):
            known_units[(p.title.lower(), u.title.lower())] = u

    existing = await LessonRepository.list_by_source_keys(
        db, tenant_id, [r.source_key for r in rows]
    )
    by_key = {l.source_key: l for l in existing}

    new_programs: list[str] = []
    new_units: list[str] = []
    for parsed in rows:
        program = by_name.get(parsed.program.lower())
        program_title = program.title.lower() if program else parsed.program.lower()
        if program is None and parsed.program not in new_programs:
            new_programs.append(parsed.program)
        if (program_title, parsed.unit.lower()) not in known_units:
            label = f"{parsed.program} / {parsed.unit}"
            if label not in new_units:
                new_units.append(label)

        lesson = by_key.get(parsed.source_key)
        if lesson is None:
            parsed.action = 'new'
            plan.new += 1
        elif _lessons_differ(lesson, parsed.values):
            parsed.action = 'update'
            plan.updated += 1
        else:
            parsed.action = 'unchanged'
            plan.unchanged += 1

    plan.programs_to_create = new_programs
    plan.units_to_create = new_units
    return plan


async def commit_plan(db: AsyncSession, tenant_id: int, csv_text: str, students) -> tuple[ImportPlan, str]:
    """Validate again, then write everything in one transaction with one flush.

    Re-validating server-side rather than trusting a client-held plan: the
    database may have changed since the preview was rendered.

    New Lessons/Assignments are wired through relationships (lesson=,
    program=, unit=) rather than ids, which is what lets the whole graph go
    to the database in a single flush at the end — the N+1 flush-per-row of
    the old /tasks/bulk is the anti-pattern this replaces.

    Does not commit; the router owns the transaction, so an error anywhere
    rolls back everything and a half-imported year cannot exist.
    """
    plan = await build_plan(db, tenant_id, csv_text)
    if plan.errors:
        return plan, ''

    import_id = str(uuid4())

    programs = await ProgramRepository.list(db, tenant_id, active_only=False)
    by_name: dict[str, Program] = {}
    for p in programs:
        by_name[p.title.lower()] = p
        by_name.setdefault(p.platform.lower(), p)

    units: dict[tuple[str, str], Unit] = {}
    for p in programs:
        for u in await UnitRepository.list(db, tenant_id, program_id=p.id, active_only=False):
            units[(p.title.lower(), u.title.lower())] = u

    existing = await LessonRepository.list_by_source_keys(
        db, tenant_id, [r.source_key for r in plan.rows]
    )
    by_key = {l.source_key: l for l in existing}

    unit_order: dict[str, int] = {}
    for parsed in plan.rows:
        pkey = parsed.program.lower()
        program = by_name.get(pkey)
        if program is None:
            # A created program starts minimal — title everywhere text is
            # required — and gets its emoji, colour and subject area in the
            # Program manager, which exists for exactly this.
            program = Program(
                tenant_id=tenant_id,
                title=parsed.program,
                subject_area=parsed.program,
                platform=parsed.program,
            )
            db.add(program)
            by_name[pkey] = program
            pkey = parsed.program.lower()

        ukey = (program.title.lower(), parsed.unit.lower())
        unit = units.get(ukey)
        if unit is None:
            order = unit_order[pkey] = unit_order.get(pkey, 0) + 1
            unit = Unit(
                tenant_id=tenant_id,
                program=program,
                title=parsed.unit,
                # 'planned', not the model's 'active' default: the whole year
                # arrives dark, and releasing a unit is a deliberate act in
                # the unit manager. (Recorded deviation from review §5.2 —
                # see PHASE2_BRIEF item 2.)
                status=parsed.unit_status or 'planned',
                week_start=parsed.unit_week_start or 1,
                week_end=parsed.unit_week_end or 1,
                sort_order=order,
            )
            db.add(unit)
            units[ukey] = unit

        lesson = by_key.get(parsed.source_key)
        if parsed.action == 'new':
            lesson = Lesson(
                tenant_id=tenant_id,
                program=program,
                unit=unit,
                source_key=parsed.source_key,
                import_id=import_id,
                **parsed.values,
            )
            db.add(lesson)
            for student in students:
                # Staged, deliberately: no date, no pin. The student's day
                # selects scheduled_date <= today, and NULL is excluded — the
                # feature the whole release model hangs on.
                db.add(Assignment(
                    tenant_id=tenant_id,
                    student_id=student.id,
                    lesson=lesson,
                    scheduled_date=None,
                    date_locked=False,
                ))
        elif parsed.action == 'update':
            # Authoring fields only. import_id is left as the import that
            # created the lesson — this one corrected it, which is different.
            for name in LESSON_UPDATE_FIELDS:
                setattr(lesson, name, parsed.values[name])

    await db.flush()  # the one flush — resolves every FK in the graph at once
    return plan, import_id


@dataclass
class RollbackResult:
    lessons_deleted: int = 0
    assignments_deleted: int = 0
    xp_reversed: int = 0
    blocked_titles: list[str] = field(default_factory=list)


async def rollback_import(
    db: AsyncSession, tenant_id: int, import_id: str, force: bool = False
) -> RollbackResult:
    """Undo one import: delete the lessons it created, cascading to assignments.

    Deleting a lesson is the B8 hazard everywhere else in the app — here it is
    the point, and `import_id` is what keeps the blast radius exact: only rows
    this import created, never hand-authored work, never other imports, and
    never a lesson another import merely updated (updates do not rewrite
    import_id).

    Completed work is the line. Without `force`, any completion under the
    import blocks the whole rollback and the titles are reported so the
    teacher knows what is at stake. With it, each completion's XP is reversed
    through the ledger *before* the delete — a new negative row, never an
    edit — so the economy stays auditable and "earned XP stays earned" is
    violated only by the person entitled to violate it, on purpose.

    Programs and units the import created are left standing: empty units are
    harmless, and unit deletion returning lessons to the unit-less pool is
    the exact damage the unit manager refuses to allow.
    """
    lessons = await LessonRepository.list_by_import_id(db, tenant_id, import_id)
    result = RollbackResult()

    completed = [a for l in lessons for a in l.assignments if a.is_completed]
    if completed and not force:
        result.blocked_titles = sorted({a.lesson.title for a in completed})
        return result

    for a in completed:
        result.xp_reversed += await reverse_xp_for_source(
            db,
            tenant_id=tenant_id,
            source_type=ASSIGNMENT_SOURCE_TYPE,
            source_id=a.id,
            reason=f"Import rolled back: {a.lesson.title}",
        )

    for lesson in lessons:
        result.assignments_deleted += len(lesson.assignments)
        await db.delete(lesson)  # cascades to its assignments
        result.lessons_deleted += 1

    return result
