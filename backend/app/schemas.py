from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

# --- Auth ---
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    display_name: str

class LoginRequest(BaseModel):
    username: str
    pin: Optional[str] = None

# --- Course ---
class CourseBase(BaseModel):
    title: str
    subject_area: str
    platform: str
    platform_url: str = ''
    ufa_eligible: bool = True
    color_hex: str = '#63b3ed'
    emoji: str = '📚'
    sort_order: int = 0
    is_active: bool = True

class CourseCreate(CourseBase):
    pass

class CourseUpdate(CourseBase):
    pass

class CourseResponse(CourseBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Module ---
class ModuleBase(BaseModel):
    title: str
    description: str = ''
    week_start: int = 1
    week_end: int = 1
    sort_order: int = 0
    is_active: bool = True

class ModuleCreate(ModuleBase):
    course_id: int

class ModuleUpdate(ModuleBase):
    pass

class ModuleResponse(ModuleBase):
    id: int
    course_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Task ---
class TaskBase(BaseModel):
    title: str
    description: str = ''
    task_type: str = 'reading'
    resource_url: str = ''
    resource_path: str = ''
    workbook_pages: str = ''
    sequence_order: int = 0
    school_day_offset: Optional[int] = None
    scheduled_date: Optional[date] = None
    # 0=Mon … 3=Thu. get_school_days treats weekday() >= 4 as weekend, so a
    # hint of 4 (Fri) would place a lesson on a non-school day.
    day_of_week_hint: Optional[int] = Field(None, ge=0, le=3)
    dependency_mode: str = 'independent'
    estimated_minutes: int = 30
    xp_reward: int = 10
    is_boss_fight: bool = False
    medium: str = 'offline'
    ufa_eligible: bool = True
    ufa_hours_credit: float = 0.0

class TaskCreate(TaskBase):
    module_id: Optional[int] = None
    course_id: int

class TaskUpdate(TaskBase):
    pass

class TaskResponse(TaskBase):
    id: int
    module_id: Optional[int] = None
    course_id: int
    is_completed: bool
    actual_completion_date: Optional[date] = None
    completion_notes: str = ''
    focus_minutes: int = 0
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TaskComplete(BaseModel):
    completion_notes: str = ''
    focus_minutes: int = Field(0, ge=0, le=480)

# --- School Calendar ---
class SchoolCalendarEntryBase(BaseModel):
    calendar_date: date
    day_type: str = 'school_day'
    label: str = ''

class SchoolCalendarCreate(SchoolCalendarEntryBase):
    pass

class SchoolCalendarEntry(SchoolCalendarEntryBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Expense ---
class ExpenseBase(BaseModel):
    item_name: str
    cost: float
    category: str
    status: str
    receipt_path: str = ''
    purchase_date: str = ''
    odyssey_ref: str = ''
    notes: str = ''

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(ExpenseBase):
    pass

class ExpenseResponse(ExpenseBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Event ---
class SchoolEventBase(BaseModel):
    title: str
    event_date: date
    event_time: str = ''
    category: str
    importance: str = 'Normal'
    reminder_days: int = 3
    description: str = ''

class SchoolEventCreate(SchoolEventBase):
    pass

class SchoolEventUpdate(SchoolEventBase):
    pass

class SchoolEventResponse(SchoolEventBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Creator Project ---
class CreatorProjectBase(BaseModel):
    title: str
    platform: str
    status: str = 'In Progress'
    xp_reward: int = 10
    project_summary: str = ''
    project_attachment: str = ''

class CreatorProjectCreate(CreatorProjectBase):
    pass

class CreatorProjectUpdate(CreatorProjectBase):
    pass

class CreatorProjectComplete(BaseModel):
    project_summary: str = ''
    project_attachment: str = ''

class CreatorProjectResponse(CreatorProjectBase):
    id: int
    completion_date: Optional[date] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Reward ---
class RewardBase(BaseModel):
    name: str
    description: str = ''
    emoji: str = '🎁'
    category: str = 'General'
    xp_cost: int
    inventory_qty: int = 1
    is_active: bool = True

class RewardCreate(RewardBase):
    pass

class RewardResponse(RewardBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Purchase ---
class PurchaseBase(BaseModel):
    reward_name: str
    xp_cost: int
    purchase_date: date
    is_claimed: bool = False

class PurchaseCreate(BaseModel):
    """The client picks *which* reward. Price, name, date and claim state are
    server facts and are never accepted from the request body."""
    reward_id: int

class PurchaseResponse(PurchaseBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Chat ---
class ChatMessageBase(BaseModel):
    session_id: str
    sender: str
    message: str

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessageResponse(ChatMessageBase):
    id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

# --- COPPA consent ---
class ConsentRecordCreate(BaseModel):
    consent_version: str = Field(..., max_length=50)
    is_granted: bool = True

class ConsentRecordResponse(BaseModel):
    id: int
    tenant_id: int
    parent_id: int
    consent_version: str
    is_granted: bool
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Activity ---
class DayActivity(BaseModel):
    date: date
    total: int
    completed: int

class ActivityResponse(BaseModel):
    """Per-day counts for the week strip, plus the streak they imply."""
    days: List[DayActivity]
    streak: int

# --- Safety ---
class SafetyEventResponse(BaseModel):
    id: int
    student_id: int
    session_id: str
    category: str
    excerpt: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# --- Scheduling ---
class ScheduleRecalcRequest(BaseModel):
    module_id: Optional[int] = None

# --- Custom Responses ---
class StudentDayCourseInfo(BaseModel):
    id: int
    title: str
    emoji: str
    color_hex: str
    platform_url: str

class StudentTaskExtended(TaskResponse):
    course: StudentDayCourseInfo

class StudentDayView(BaseModel):
    date: date
    tasks: List[StudentTaskExtended]

class AnalyticsSummary(BaseModel):
    xp_balance: int
    daily_streak: int
    total_completed_tasks: int
    total_focus_minutes: int
    on_time_rate: float
    completion_by_subject: Dict[str, int]
    xp_over_time: List[Dict[str, Any]]
    recent_7_day_activity: List[Dict[str, Any]]

class UfaComplianceSummary(BaseModel):
    total_grant: float
    total_spent: float
    remaining: float
    by_category: Dict[str, float]
    by_status: Dict[str, float]
