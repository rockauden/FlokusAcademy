from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.database import get_db
from app.schemas import CourseCreate, CourseUpdate, CourseResponse
from app.models import Course
from app.auth import get_current_user, require_teacher

router = APIRouter(prefix="/api/courses", tags=["courses"])

@router.get("/", response_model=List[CourseResponse])
async def list_courses(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(Course).where(Course.is_active == True).order_by(Course.sort_order))
    return result.scalars().all()

@router.post("/", response_model=CourseResponse)
async def create_course(course: CourseCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    new_course = Course(**course.model_dump())
    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)
    return new_course

@router.get("/{id}", response_model=CourseResponse)
async def get_course(id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(Course).where(Course.id == id, Course.is_active == True))
    course = result.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.put("/{id}", response_model=CourseResponse)
async def update_course(id: int, course_data: CourseUpdate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(Course).where(Course.id == id))
    course = result.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    for key, value in course_data.model_dump().items():
        setattr(course, key, value)
    await db.commit()
    await db.refresh(course)
    return course

@router.delete("/{id}")
async def delete_course(id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(Course).where(Course.id == id))
    course = result.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course.is_active = False
    await db.commit()
    return {"message": "Course deactivated"}
