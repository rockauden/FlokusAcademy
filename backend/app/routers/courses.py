from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.schemas import ClearUnstartedResult, CourseCreate, CourseUpdate, CourseResponse
from app.models import Program, User
from app.auth import get_current_active_user, require_teacher_user
from app.repository import LessonRepository, ProgramRepository

router = APIRouter(prefix="/api/courses", tags=["courses"])

@router.get("/", response_model=List[CourseResponse])
async def list_courses(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Active programs by default — that is what every picker wants.

    The program manager asks for the inactive ones too. DELETE deactivates
    rather than deletes, so without this a deactivated program vanishes from
    the only screen that could bring it back, and the one-click undo becomes a
    database edit.
    """
    return await ProgramRepository.list(
        db, tenant_id=user.tenant_id, active_only=not include_inactive
    )

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


@router.post("/{id}/clear-unstarted", response_model=ClearUnstartedResult)
async def clear_unstarted(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    """Delete this class's planned-but-never-started work, keeping its history.

    The escape hatch for a plan that has been abandoned — a curriculum import
    that no longer fits, a unit dropped mid-year, a week typed up and then
    reconsidered. It removes only lessons where **no student has completed
    anything**, so what actually happened survives in the portfolio, in the
    UFA record and in the XP ledger. Nothing here touches the ledger at all,
    which is the point: there is no earned XP to reverse, because nothing
    deleted was ever earned.

    Not a general delete. Wiping a class outright would take real work away,
    and that decision should cost more than one button.
    """
    program = await ProgramRepository.get(db, tenant_id=user.tenant_id, program_id=id)
    if not program:
        raise HTTPException(status_code=404, detail="Class not found")

    lessons = await LessonRepository.list_for_program(db, tenant_id=user.tenant_id, program_id=id)

    deleted = 0
    kept = 0
    for lesson in lessons:
        if any(a.is_completed for a in lesson.assignments):
            kept += 1
            continue
        await db.delete(lesson)  # cascades to its assignments
        deleted += 1

    await db.commit()
    return ClearUnstartedResult(lessons_deleted=deleted, completed_kept=kept)
