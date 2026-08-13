from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskComplete, StudentDayView, StudentTaskExtended, StudentDayCourseInfo
from app.models import Task, Course
from app.auth import get_current_user, require_teacher

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    course_id: Optional[int] = None,
    module_id: Optional[int] = None,
    scheduled_date: Optional[date] = None,
    is_completed: Optional[bool] = None,
    dependency_mode: Optional[str] = None,
    db: AsyncSession = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    query = select(Task)
    if course_id is not None:
        query = query.where(Task.course_id == course_id)
    if module_id is not None:
        query = query.where(Task.module_id == module_id)
    if scheduled_date is not None:
        query = query.where(Task.scheduled_date == scheduled_date)
    if is_completed is not None:
        query = query.where(Task.is_completed == is_completed)
    if dependency_mode is not None:
        query = query.where(Task.dependency_mode == dependency_mode)
    
    query = query.order_by(Task.sequence_order)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/today", response_model=StudentDayView)
async def get_today_tasks(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    today = date.today()
    # All incomplete tasks where scheduled_date <= today, ordered by dependency_mode, course sort_order, sequence_order
    # 'independent' comes before others alphabetically
    query = (
        select(Task)
        .options(joinedload(Task.course))
        .join(Course)
        .where(Task.is_completed == False, Task.scheduled_date <= today)
        .order_by(Task.dependency_mode.asc(), Course.sort_order.asc(), Task.sequence_order.asc())
    )
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    student_tasks = []
    for t in tasks:
        course_info = StudentDayCourseInfo(
            id=t.course.id,
            title=t.course.title,
            emoji=t.course.emoji,
            color_hex=t.course.color_hex,
            platform_url=t.course.platform_url
        )
        task_dict = {c.name: getattr(t, c.name) for c in t.__table__.columns}
        st = StudentTaskExtended(**task_dict, course=course_info)
        student_tasks.append(st)
        
    return StudentDayView(date=today, tasks=student_tasks)

@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    new_task = Task(**task.model_dump())
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task

@router.post("/bulk", response_model=List[TaskResponse])
async def create_tasks_bulk(tasks: List[TaskCreate], db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    new_tasks = [Task(**t.model_dump()) for t in tasks]
    db.add_all(new_tasks)
    await db.commit()
    for t in new_tasks:
        await db.refresh(t)
    return new_tasks

@router.get("/{id}", response_model=TaskResponse)
async def get_task(id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(Task).where(Task.id == id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{id}", response_model=TaskResponse)
async def update_task(id: int, task_data: TaskUpdate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(Task).where(Task.id == id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in task_data.model_dump().items():
        setattr(task, key, value)
    await db.commit()
    await db.refresh(task)
    return task

@router.post("/{id}/complete", response_model=TaskResponse)
async def complete_task(id: int, completion: TaskComplete, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(Task).where(Task.id == id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.is_completed = True
    task.actual_completion_date = date.today()
    task.completion_notes = completion.completion_notes
    task.focus_minutes = completion.focus_minutes
    await db.commit()
    await db.refresh(task)
    return task

@router.post("/{id}/uncomplete", response_model=TaskResponse)
async def uncomplete_task(id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(Task).where(Task.id == id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.is_completed = False
    task.actual_completion_date = None
    task.completion_notes = ''
    task.focus_minutes = 0
    await db.commit()
    await db.refresh(task)
    return task

@router.delete("/{id}")
async def delete_task(id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(Task).where(Task.id == id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()
    return {"message": "Task deleted"}
