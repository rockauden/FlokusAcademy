"""Tenant-scoped data access.

Routers should not build bare `select(Model)` statements. Every read goes
through a repository method that takes tenant_id and applies the filter, so
isolation is enforced in one auditable place instead of being re-remembered at
each call site. This is the application-level half of H-01; Postgres row-level
security is the backstop that makes a forgotten filter fail closed.

Rule for anything added here: the first `.where()` clause is the tenant.
"""
from datetime import date
from typing import Optional, Sequence

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import (
    AppConfig,
    Assignment,
    ChatMessage,
    CreatorProject,
    Expense,
    Lesson,
    Program,
    Purchase,
    Reward,
    SchoolEvent,
    Unit,
    User,
)

_WITH_LESSON = joinedload(Assignment.lesson).joinedload(Lesson.program)


class AssignmentRepository:
    """Student instances. Every method scopes by tenant, and most by student."""

    @staticmethod
    async def get_today(
        db: AsyncSession,
        tenant_id: int,
        student_id: int,
        today: date | None = None,
    ) -> Sequence[Assignment]:
        """The student's day: everything still outstanding, plus today's finishes.

        Completed work is matched on actual_completion_date rather than
        scheduled_date — a finished assignment keeps a past scheduled_date (the
        rolling scheduler rewrites it to the completion date), so filtering
        those on `scheduled_date <= today` would return everything ever
        completed and turn "XP Earned Today" into an all-time total.
        """
        today = today or date.today()
        query = (
            select(Assignment)
            .options(_WITH_LESSON)
            .join(Lesson, Assignment.lesson_id == Lesson.id)
            .join(Program, Lesson.program_id == Program.id)
            .where(
                Assignment.tenant_id == tenant_id,
                Assignment.student_id == student_id,
                or_(
                    and_(Assignment.is_completed == False, Assignment.scheduled_date <= today),
                    and_(Assignment.is_completed == True, Assignment.actual_completion_date == today),
                ),
            )
            .order_by(
                Lesson.dependency_mode.asc(),
                Program.sort_order.asc(),
                Lesson.sequence_order.asc(),
            )
        )
        return (await db.execute(query)).scalars().all()

    @staticmethod
    async def list(
        db: AsyncSession,
        tenant_id: int,
        student_id: Optional[int] = None,
        program_id: Optional[int] = None,
        unit_id: Optional[int] = None,
        scheduled_date: Optional[date] = None,
        is_completed: Optional[bool] = None,
        dependency_mode: Optional[str] = None,
    ) -> Sequence[Assignment]:
        query = (
            select(Assignment)
            .options(_WITH_LESSON)
            .join(Lesson, Assignment.lesson_id == Lesson.id)
            .where(Assignment.tenant_id == tenant_id)
        )
        if student_id is not None:
            query = query.where(Assignment.student_id == student_id)
        if program_id is not None:
            query = query.where(Lesson.program_id == program_id)
        if unit_id is not None:
            query = query.where(Lesson.unit_id == unit_id)
        if scheduled_date is not None:
            query = query.where(Assignment.scheduled_date == scheduled_date)
        if is_completed is not None:
            query = query.where(Assignment.is_completed == is_completed)
        if dependency_mode is not None:
            query = query.where(Lesson.dependency_mode == dependency_mode)
        return (await db.execute(query.order_by(Lesson.sequence_order))).scalars().all()

    @staticmethod
    async def get(db: AsyncSession, tenant_id: int, assignment_id: int) -> Assignment | None:
        result = await db.execute(
            select(Assignment)
            .options(_WITH_LESSON)
            .where(Assignment.tenant_id == tenant_id, Assignment.id == assignment_id)
        )
        return result.scalars().first()

    @staticmethod
    async def list_completed(db: AsyncSession, tenant_id: int, student_id: int) -> Sequence[Assignment]:
        """Completed assignments with lesson and program eager-loaded, for analytics."""
        result = await db.execute(
            select(Assignment)
            .options(_WITH_LESSON)
            .where(
                Assignment.tenant_id == tenant_id,
                Assignment.student_id == student_id,
                Assignment.is_completed == True,
            )
        )
        return result.scalars().all()

    @staticmethod
    async def in_day_range(
        db: AsyncSession,
        tenant_id: int,
        student_id: int,
        start: date,
        end: date,
    ) -> Sequence[Assignment]:
        """Assignments belonging to each day between start and end inclusive.

        Which date an assignment "belongs to" depends on whether it is done,
        exactly as the student's day view decides it: outstanding work belongs
        to the day it is scheduled for, finished work to the day it was
        actually finished. The rolling scheduler rewrites scheduled_date on
        completion, so using it for both would attribute finished work to
        whatever date the scheduler last moved it to.
        """
        result = await db.execute(
            select(Assignment)
            .where(
                Assignment.tenant_id == tenant_id,
                Assignment.student_id == student_id,
                or_(
                    and_(
                        Assignment.is_completed == False,
                        Assignment.scheduled_date >= start,
                        Assignment.scheduled_date <= end,
                    ),
                    and_(
                        Assignment.is_completed == True,
                        Assignment.actual_completion_date >= start,
                        Assignment.actual_completion_date <= end,
                    ),
                ),
            )
        )
        return result.scalars().all()

    @staticmethod
    async def for_scheduling(db: AsyncSession, tenant_id: int, unit_id: Optional[int] = None) -> Sequence[Assignment]:
        """Open + completed assignments with their lesson, for the rolling scheduler.

        Only units with status 'active' are paced. This is the safety valve for
        the whole curriculum migration: a full-year import creates hundreds of
        undated assignments across ~26 units, and adding a single sick day
        fires reschedule_from_today across the entire tenant. Without this
        clause that one click would date every unit at once and hand a
        nine-year-old every subject's next lesson on the same morning.

        The outer join and the is_(None) branch are both load-bearing. A lesson
        with no unit — a quick add — has nothing to check a status against, and
        an inner join would silently drop it from scheduling altogether.
        """
        query = (
            select(Assignment)
            .options(_WITH_LESSON)
            .join(Lesson, Assignment.lesson_id == Lesson.id)
            .outerjoin(Unit, Lesson.unit_id == Unit.id)
            .where(
                Assignment.tenant_id == tenant_id,
                or_(Lesson.unit_id.is_(None), Unit.status == 'active'),
            )
        )
        if unit_id is not None:
            query = query.where(Lesson.unit_id == unit_id)
        return (await db.execute(query)).scalars().all()


class LessonRepository:
    """Curriculum templates."""

    @staticmethod
    async def get(db: AsyncSession, tenant_id: int, lesson_id: int) -> Lesson | None:
        result = await db.execute(
            select(Lesson).where(Lesson.tenant_id == tenant_id, Lesson.id == lesson_id)
        )
        return result.scalars().first()

    @staticmethod
    async def list_by_source_keys(
        db: AsyncSession, tenant_id: int, source_keys: Sequence[str]
    ) -> Sequence[Lesson]:
        """Existing lessons matching the importer's idempotency keys.

        One query for the whole file rather than one per row — a 272-row
        import should not be 272 round trips just to learn what it already
        knows.
        """
        if not source_keys:
            return []
        result = await db.execute(
            select(Lesson).where(
                Lesson.tenant_id == tenant_id, Lesson.source_key.in_(source_keys)
            )
        )
        return result.scalars().all()

    @staticmethod
    async def list_by_import_id(
        db: AsyncSession, tenant_id: int, import_id: str
    ) -> Sequence[Lesson]:
        """Every lesson a single import created — the unit of rollback.

        Assignments are eager-loaded because rollback must inspect completion
        before deleting, and lazy-loading inside an async session raises.
        """
        result = await db.execute(
            select(Lesson)
            .options(joinedload(Lesson.assignments))
            .where(Lesson.tenant_id == tenant_id, Lesson.import_id == import_id)
        )
        return result.scalars().unique().all()

    @staticmethod
    async def list_students(db: AsyncSession, tenant_id: int) -> Sequence[User]:
        """Students in the tenant — who a newly authored lesson gets assigned to."""
        result = await db.execute(
            select(User).where(User.tenant_id == tenant_id, User.role == 'student')
        )
        return result.scalars().all()


class RewardRepository:
    @staticmethod
    async def list(db: AsyncSession, tenant_id: int, active_only: bool = True) -> Sequence[Reward]:
        query = select(Reward).where(Reward.tenant_id == tenant_id)
        if active_only:
            query = query.where(Reward.is_active == True)
        result = await db.execute(query.order_by(Reward.xp_cost))
        return result.scalars().all()

    @staticmethod
    async def get(
        db: AsyncSession,
        tenant_id: int,
        reward_id: int,
        active_only: bool = False,
        for_update: bool = False,
    ) -> Reward | None:
        query = select(Reward).where(Reward.tenant_id == tenant_id, Reward.id == reward_id)
        if active_only:
            query = query.where(Reward.is_active == True)
        if for_update:
            # Held until commit, so a concurrent purchase cannot pass the same
            # stock/balance check. No-op on SQLite; real on Postgres.
            query = query.with_for_update()
        result = await db.execute(query)
        return result.scalars().first()


class CreatorProjectRepository:
    @staticmethod
    async def list(
        db: AsyncSession, tenant_id: int, status: Optional[str] = None
    ) -> Sequence[CreatorProject]:
        query = select(CreatorProject).where(CreatorProject.tenant_id == tenant_id)
        if status is not None:
            query = query.where(CreatorProject.status == status)
        result = await db.execute(query.order_by(CreatorProject.created_at.desc()))
        return result.scalars().all()

    @staticmethod
    async def get(db: AsyncSession, tenant_id: int, project_id: int) -> CreatorProject | None:
        result = await db.execute(
            select(CreatorProject).where(
                CreatorProject.tenant_id == tenant_id, CreatorProject.id == project_id
            )
        )
        return result.scalars().first()


class ProgramRepository:
    """Curriculum programs (the API still calls these "courses")."""

    @staticmethod
    async def list(db: AsyncSession, tenant_id: int, active_only: bool = True) -> Sequence[Program]:
        query = select(Program).where(Program.tenant_id == tenant_id)
        if active_only:
            query = query.where(Program.is_active == True)
        return (await db.execute(query.order_by(Program.sort_order))).scalars().all()

    @staticmethod
    async def get(
        db: AsyncSession, tenant_id: int, program_id: int, active_only: bool = False
    ) -> Program | None:
        query = select(Program).where(Program.tenant_id == tenant_id, Program.id == program_id)
        if active_only:
            query = query.where(Program.is_active == True)
        return (await db.execute(query)).scalars().first()


class UnitRepository:
    """Curriculum units (the API still calls these "modules")."""

    @staticmethod
    async def list(
        db: AsyncSession, tenant_id: int, program_id: Optional[int] = None, active_only: bool = True
    ) -> Sequence[Unit]:
        query = select(Unit).where(Unit.tenant_id == tenant_id)
        if active_only:
            query = query.where(Unit.is_active == True)
        if program_id is not None:
            query = query.where(Unit.program_id == program_id)
        return (await db.execute(query.order_by(Unit.sort_order))).scalars().all()

    @staticmethod
    async def get(
        db: AsyncSession, tenant_id: int, unit_id: int, active_only: bool = False
    ) -> Unit | None:
        query = select(Unit).where(Unit.tenant_id == tenant_id, Unit.id == unit_id)
        if active_only:
            query = query.where(Unit.is_active == True)
        return (await db.execute(query)).scalars().first()


class EventRepository:
    @staticmethod
    async def list(
        db: AsyncSession,
        tenant_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[str] = None,
    ) -> Sequence[SchoolEvent]:
        query = select(SchoolEvent).where(SchoolEvent.tenant_id == tenant_id)
        if start_date:
            query = query.where(SchoolEvent.event_date >= start_date)
        if end_date:
            query = query.where(SchoolEvent.event_date <= end_date)
        if category:
            query = query.where(SchoolEvent.category == category)
        return (await db.execute(query.order_by(SchoolEvent.event_date))).scalars().all()

    @staticmethod
    async def get(db: AsyncSession, tenant_id: int, event_id: int) -> SchoolEvent | None:
        result = await db.execute(
            select(SchoolEvent).where(SchoolEvent.tenant_id == tenant_id, SchoolEvent.id == event_id)
        )
        return result.scalars().first()

    @staticmethod
    async def next_major(db: AsyncSession, tenant_id: int, today: date) -> SchoolEvent | None:
        result = await db.execute(
            select(SchoolEvent)
            .where(
                SchoolEvent.tenant_id == tenant_id,
                SchoolEvent.event_date >= today,
                SchoolEvent.importance.in_(['Important', 'Urgent']),
            )
            .order_by(SchoolEvent.event_date)
            .limit(1)
        )
        return result.scalars().first()


class ExpenseRepository:
    @staticmethod
    async def list(db: AsyncSession, tenant_id: int) -> Sequence[Expense]:
        result = await db.execute(
            select(Expense)
            .where(Expense.tenant_id == tenant_id)
            .order_by(Expense.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get(db: AsyncSession, tenant_id: int, expense_id: int) -> Expense | None:
        result = await db.execute(
            select(Expense).where(Expense.tenant_id == tenant_id, Expense.id == expense_id)
        )
        return result.scalars().first()


class ChatRepository:
    @staticmethod
    async def list_for_session(
        db: AsyncSession, tenant_id: int, student_id: int, session_id: str
    ) -> Sequence[ChatMessage]:
        result = await db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.tenant_id == tenant_id,
                ChatMessage.student_id == student_id,
                ChatMessage.session_id == session_id,
            )
            .order_by(ChatMessage.timestamp)
        )
        return result.scalars().all()


class AppConfigRepository:
    """Settings that are data rather than deployment configuration.

    The school week, the academic year's first day and the grade level all
    change without a release, and all of them were previously either hardcoded
    or inferred from something fragile. They live here so changing them is an
    edit, not a deploy.
    """

    @staticmethod
    async def get(db: AsyncSession, tenant_id: int, key: str, default: str | None = None) -> str | None:
        result = await db.execute(
            select(AppConfig.value).where(AppConfig.tenant_id == tenant_id, AppConfig.key == key)
        )
        value = result.scalars().first()
        return default if value is None else value

    @staticmethod
    async def get_many(db: AsyncSession, tenant_id: int, keys: Sequence[str]) -> dict[str, str]:
        result = await db.execute(
            select(AppConfig.key, AppConfig.value).where(
                AppConfig.tenant_id == tenant_id, AppConfig.key.in_(keys)
            )
        )
        return {row.key: row.value for row in result}

    @staticmethod
    async def set(db: AsyncSession, tenant_id: int, key: str, value: str) -> AppConfig:
        """Upsert one key. Does not commit — the caller owns the transaction."""
        result = await db.execute(
            select(AppConfig).where(AppConfig.tenant_id == tenant_id, AppConfig.key == key)
        )
        row = result.scalars().first()
        if row is None:
            row = AppConfig(tenant_id=tenant_id, key=key, value=value)
            db.add(row)
        else:
            row.value = value
        return row


class PurchaseRepository:
    @staticmethod
    async def list(db: AsyncSession, tenant_id: int) -> Sequence[Purchase]:
        result = await db.execute(
            select(Purchase)
            .where(Purchase.tenant_id == tenant_id)
            .order_by(Purchase.purchase_date.desc())
        )
        return result.scalars().all()
