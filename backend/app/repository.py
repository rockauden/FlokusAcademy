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
    async def for_scheduling(db: AsyncSession, tenant_id: int, unit_id: Optional[int] = None) -> Sequence[Assignment]:
        """Open + completed assignments with their lesson, for the rolling scheduler."""
        query = (
            select(Assignment)
            .options(_WITH_LESSON)
            .join(Lesson, Assignment.lesson_id == Lesson.id)
            .where(Assignment.tenant_id == tenant_id)
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


class PurchaseRepository:
    @staticmethod
    async def list(db: AsyncSession, tenant_id: int) -> Sequence[Purchase]:
        result = await db.execute(
            select(Purchase)
            .where(Purchase.tenant_id == tenant_id)
            .order_by(Purchase.purchase_date.desc())
        )
        return result.scalars().all()
