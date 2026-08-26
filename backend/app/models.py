from datetime import datetime, date
from typing import Optional
from sqlalchemy import Index, Integer, String, Boolean, Date, DateTime, Float, ForeignKey, UniqueConstraint, false, true
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base

# Every owned row carries a tenant_id. Today there is exactly one tenant (1),
# but the column is the isolation boundary the repository layer and Postgres
# row-level security will both key off in Phase 2. Adding it now keeps the
# backfill to a handful of rows.

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1', index=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    pin_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Deactivating an account revokes access on the next request, without
    # waiting for the token to expire.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    # jti of the one refresh token currently valid for this user. Rotating it
    # on every refresh means a replayed older token no longer matches and is
    # rejected — that is what makes rotation more than cosmetic.
    refresh_token_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

# --- Curriculum template: authored once, reusable across students and years ---

class Program(Base):
    """A subject/platform pairing, e.g. "Math — Beast Academy". Was: Course."""
    __tablename__ = 'programs'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1', index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    subject_area: Mapped[str] = mapped_column(String, nullable=False)
    platform: Mapped[str] = mapped_column(String, nullable=False)
    platform_url: Mapped[str] = mapped_column(String, default='')
    ufa_eligible: Mapped[bool] = mapped_column(Boolean, default=True)
    color_hex: Mapped[str] = mapped_column(String, default='#63b3ed')
    emoji: Mapped[str] = mapped_column(String, default='📚')
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    units = relationship("Unit", back_populates="program", cascade="all, delete-orphan")
    lessons = relationship("Lesson", back_populates="program", cascade="all, delete-orphan")

class Unit(Base):
    """A block of lessons within a program, e.g. "Unit 3: Fractions". Was: Module."""
    __tablename__ = 'units'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1', index=True)
    program_id: Mapped[int] = mapped_column(Integer, ForeignKey('programs.id', ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, default='')
    week_start: Mapped[int] = mapped_column(Integer, default=1)
    week_end: Mapped[int] = mapped_column(Integer, default=1)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    # 'planned' | 'active' | 'completed' | 'abandoned'.
    #
    # The rolling scheduler paces only 'active' units. That is what makes
    # releasing a real action rather than a wish: a whole year can be imported
    # with every unit 'planned', and the student's day stays empty until one is
    # flipped to 'active'. Without it, the first sick day — which triggers a
    # full-tenant recalculation — would date every lesson in the database at
    # once and fill a nine-year-old's morning with every subject's next lesson.
    #
    # It is also what makes a mid-year Beast Academy Level 2 → 3 jump a status
    # change instead of a migration: Level 3 units are imported ahead of time
    # as 'planned' and cost nothing sitting there.
    status: Mapped[str] = mapped_column(String(20), default='active', server_default='active')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    program = relationship("Program", back_populates="units")
    lessons = relationship("Lesson", back_populates="unit")

class Lesson(Base):
    """One unit of instruction. Was: Task.

    Carries no student state — no schedule, no completion, no focus time.
    Those live on Assignment, so one lesson can be assigned to several students
    or reused in a later academic year without its history following it.
    """
    __tablename__ = 'lessons'
    # A unique *index* rather than a UniqueConstraint, deliberately: SQLite
    # cannot ALTER a table to add a constraint, so the constraint form would
    # force a full table rebuild in the migration for no extra enforcement —
    # a unique index polices the same rule on both engines. NULLs never
    # collide under either engine, so hand-authored lessons (source_key NULL)
    # are untouched.
    __table_args__ = (Index('uix_tenant_source_key', 'tenant_id', 'source_key', unique=True),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1', index=True)
    unit_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('units.id', ondelete="SET NULL"), nullable=True)
    program_id: Mapped[int] = mapped_column(Integer, ForeignKey('programs.id'), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, default='')
    task_type: Mapped[str] = mapped_column(String, default='reading')
    resource_url: Mapped[str] = mapped_column(String, default='')
    resource_path: Mapped[str] = mapped_column(String, default='')
    workbook_pages: Mapped[str] = mapped_column(String, default='')
    sequence_order: Mapped[int] = mapped_column(Integer, default=0)
    school_day_offset: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # 0=Mon … 6=Sun. A Fri/Sat/Sun hint is a deliberate placement, not an error.
    day_of_week_hint: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # 'independent' | 'teacher_led' | 'live_scheduled' — see schemas.DependencyMode.
    dependency_mode: Mapped[str] = mapped_column(String, default='independent')
    # 'core' | 'standard' | 'optional'. Changes pace without changing
    # curriculum: accelerating releases `core` only and leaves the rest
    # unreleased, so the skipped material is still there to come back to.
    priority: Mapped[str] = mapped_column(String(12), default='standard', server_default='standard')
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30)
    xp_reward: Mapped[int] = mapped_column(Integer, default=10)
    is_boss_fight: Mapped[bool] = mapped_column(Boolean, default=False)
    medium: Mapped[str] = mapped_column(String, default='offline')
    ufa_eligible: Mapped[bool] = mapped_column(Boolean, default=True)
    ufa_hours_credit: Mapped[float] = mapped_column(Float, default=0.0)
    # Importer idempotency key: slug(program)|slug(unit)|slug(title), unique
    # per tenant. This is what turns re-importing a corrected spreadsheet into
    # an *update* instead of a duplication — the single property that makes
    # the spreadsheet the place curriculum is maintained all year rather than
    # a one-shot seed. NULL for lessons authored by hand through the form.
    source_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Which import created this lesson (uuid4), so one bad import can be
    # rolled back precisely without touching hand-authored work or other
    # imports. Never overwritten by a later update-import: it records origin.
    import_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    program = relationship("Program", back_populates="lessons")
    unit = relationship("Unit", back_populates="lessons")
    assignments = relationship("Assignment", back_populates="lesson", cascade="all, delete-orphan")

# --- Student instance: one row per (student, lesson) ---

class Assignment(Base):
    """A lesson handed to a particular student, and everything that happened to it.

    This is where XP ownership finally becomes unambiguous: awards credit
    assignment.student_id, so a teacher marking work complete on the student's
    behalf credits the student, not themselves.
    """
    __tablename__ = 'assignments'
    __table_args__ = (UniqueConstraint('student_id', 'lesson_id', name='uix_student_lesson'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey('lessons.id'), index=True)
    scheduled_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # This date is pinned and the rolling scheduler must not move it.
    #
    # Without the flag a Saturday catch-up survives exactly until the next sick
    # day: routers/schedule.py fires a full-tenant reschedule_from_today on add
    # sick day, add holiday and delete calendar entry, and the scheduler
    # assigns scheduled_date unconditionally for `independent` — the default
    # mode. So the Saturday silently became a Monday and nobody was told.
    #
    # Set only when the teacher explicitly asks for it, never inferred from
    # "a date was supplied". An earlier cut inferred it, which pinned every
    # quick add — the task form defaults the date to today — and left the
    # scheduler unable to place any of that work. Most dates are the
    # scheduler's to revise; a pin is the exception, and has to be said.
    date_locked: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    actual_completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    focus_minutes: Mapped[int] = mapped_column(Integer, default=0)
    completion_notes: Mapped[str] = mapped_column(String(2000), default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    lesson = relationship("Lesson", back_populates="assignments")

class SchoolCalendar(Base):
    __tablename__ = 'school_calendar'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1', index=True)
    calendar_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    day_type: Mapped[str] = mapped_column(String, default='school_day')
    label: Mapped[str] = mapped_column(String, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class Expense(Base):
    __tablename__ = 'expenses'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1', index=True)
    item_name: Mapped[str] = mapped_column(String, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    receipt_path: Mapped[str] = mapped_column(String, default='')
    purchase_date: Mapped[str] = mapped_column(String, default='')
    odyssey_ref: Mapped[str] = mapped_column(String, default='')
    notes: Mapped[str] = mapped_column(String, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class SchoolEvent(Base):
    __tablename__ = 'school_events'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1', index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_time: Mapped[str] = mapped_column(String, default='')
    category: Mapped[str] = mapped_column(String, nullable=False)
    importance: Mapped[str] = mapped_column(String, default='Normal')
    reminder_days: Mapped[int] = mapped_column(Integer, default=3)
    description: Mapped[str] = mapped_column(String, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class CreatorProject(Base):
    __tablename__ = 'creator_projects'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1', index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    platform: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default='In Progress')
    xp_reward: Mapped[int] = mapped_column(Integer, default=10)
    completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    project_summary: Mapped[str] = mapped_column(String, default='')
    project_attachment: Mapped[str] = mapped_column(String, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class Reward(Base):
    __tablename__ = 'rewards'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1', index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String(500), default='')
    emoji: Mapped[str] = mapped_column(String(16), default='🎁')
    category: Mapped[str] = mapped_column(String(60), default='General')
    xp_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    inventory_qty: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class Purchase(Base):
    __tablename__ = 'purchases'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1', index=True)
    reward_name: Mapped[str] = mapped_column(String, nullable=False)
    xp_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_claimed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class ChatMessage(Base):
    __tablename__ = 'chat_history'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1', index=True)
    # No server_default: these were only ever needed to backfill existing rows
    # in migration 99bd8a562d1a. Leaving them on would silently attribute any
    # insert that forgets student_id to user 2.
    student_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    sender: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class XPLedger(Base):
    """Append-only record of every XP movement.

    The single source of truth for the economy: balance is SUM(delta), never a
    stored counter. Rows are never updated or deleted — a reversal is a new row
    with the opposite delta, so history stays auditable.

    tenant_id is a plain Integer rather than a ForeignKey: users.tenant_id is
    not unique, so Postgres would reject an FK pointing at it.
    """
    __tablename__ = 'xp_ledger'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(60), nullable=False)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class ConsentRecord(Base):
    """Append-only record of COPPA verifiable parental consent.

    COPPA §312.5 requires consent before a child's data is collected or
    disclosed to a third party (here: the AI tutor). Storing it as rows rather
    than a boolean means a withdrawal is a new record, so the history of who
    consented to what, and when, survives.
    """
    __tablename__ = 'consent_records'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    consent_version: Mapped[str] = mapped_column(String(50), nullable=False)
    is_granted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

class SafetyEvent(Base):
    """Raised when a child's message to the tutor needs a parent's attention.

    Kept separate from chat_history so an alert can be listed, counted and
    acknowledged without reading the transcript, and so it survives the 90-day
    chat retention purge — a parent should still be able to see that something
    was flagged in March even once March's messages are gone. The excerpt is
    capped for the same reason the rest of this table is minimal: it exists to
    tell a parent where to look, not to become a second copy of the child's
    conversation.
    """
    __tablename__ = 'safety_events'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # 'self_harm' | 'abuse' | 'distress' -- see services/safety.py
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    excerpt: Mapped[str] = mapped_column(String(400), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    # Null until the parent marks it seen; this is what drives the unread count.
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class StuckFlag(Base):
    """Raised when the tutor understands the student to be stuck on something.

    Deliberately NOT a SafetyEvent. Being stuck on long division and disclosing
    that someone is hurting you are not the same kind of news, and putting them
    in one list would blunt the one that must never be missed. A parent should
    be able to glance at the safety banner and know that anything in it is
    serious.

    Resolved rather than deleted, so "he got stuck on fractions three times
    this week" stays visible -- that pattern is the genuinely useful signal,
    and it is invisible if each flag disappears once acknowledged.
    """
    __tablename__ = 'stuck_flags'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # What the tutor understood the difficulty to be, in its words.
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class AppConfig(Base):
    __tablename__ = 'app_config'
    key: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1', index=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
