from datetime import datetime, date
from typing import Optional
from sqlalchemy import Integer, String, Boolean, Date, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    pin_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class Course(Base):
    __tablename__ = 'courses'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
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
    
    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="course", cascade="all, delete-orphan")

class Module(Base):
    __tablename__ = 'modules'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey('courses.id', ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, default='')
    week_start: Mapped[int] = mapped_column(Integer, default=1)
    week_end: Mapped[int] = mapped_column(Integer, default=1)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    course = relationship("Course", back_populates="modules")
    tasks = relationship("Task", back_populates="module")

class Task(Base):
    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('modules.id', ondelete="SET NULL"), nullable=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey('courses.id'), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, default='')
    task_type: Mapped[str] = mapped_column(String, default='reading')
    resource_url: Mapped[str] = mapped_column(String, default='')
    resource_path: Mapped[str] = mapped_column(String, default='')
    workbook_pages: Mapped[str] = mapped_column(String, default='')
    sequence_order: Mapped[int] = mapped_column(Integer, default=0)
    school_day_offset: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    scheduled_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    day_of_week_hint: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dependency_mode: Mapped[str] = mapped_column(String, default='independent')
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    actual_completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    completion_notes: Mapped[str] = mapped_column(String, default='')
    focus_minutes: Mapped[int] = mapped_column(Integer, default=0)
    xp_reward: Mapped[int] = mapped_column(Integer, default=10)
    is_boss_fight: Mapped[bool] = mapped_column(Boolean, default=False)
    medium: Mapped[str] = mapped_column(String, default='offline')
    ufa_eligible: Mapped[bool] = mapped_column(Boolean, default=True)
    ufa_hours_credit: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    course = relationship("Course", back_populates="tasks")
    module = relationship("Module", back_populates="tasks")

class SchoolCalendar(Base):
    __tablename__ = 'school_calendar'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    calendar_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    day_type: Mapped[str] = mapped_column(String, default='school_day')
    label: Mapped[str] = mapped_column(String, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class Expense(Base):
    __tablename__ = 'expenses'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
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
    name: Mapped[str] = mapped_column(String, nullable=False)
    xp_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    inventory_qty: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class Purchase(Base):
    __tablename__ = 'purchases'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reward_name: Mapped[str] = mapped_column(String, nullable=False)
    xp_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_claimed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class ChatMessage(Base):
    __tablename__ = 'chat_history'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, nullable=False)
    sender: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class AppConfig(Base):
    __tablename__ = 'app_config'
    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
