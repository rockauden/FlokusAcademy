from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.schemas import CourseCreate, CourseUpdate, CourseResponse
from app.models import Program, User
from app.auth import get_current_active_user, require_teacher_user
from app.repository import ProgramRepository

router = APIRouter(prefix="/api/courses", tags=["courses"])

@router.get("/", response_model=List[CourseResponse])
async def list_courses(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    return await ProgramRepository.list(db, tenant_id=user.tenant_id)

@router.post("/", response_model=CourseResponse)
async def create_course(course: CourseCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    new_course = Program(**course.model_dump(), tenant_id=user.tenant_id)
    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)
    return new_course

@router.get("/{id}", response_model=CourseResponse)
async def get_course(id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    course = await ProgramRepository.get(db, tenant_id=user.tenant_id, program_id=id, active_only=True)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.put("/{id}", response_model=CourseResponse)
async def update_course(id: int, course_data: CourseUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    course = await ProgramRepository.get(db, tenant_id=user.tenant_id, program_id=id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    for key, value in course_data.model_dump().items():
        setattr(course, key, value)
    await db.commit()
    await db.refresh(course)
    return course

@router.delete("/{id}")
async def delete_course(id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    course = await ProgramRepository.get(db, tenant_id=user.tenant_id, program_id=id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course.is_active = False
    await db.commit()
    return {"message": "Course deactivated"}
