from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import date
from app.database import get_db
from app.schemas import CreatorProjectCreate, CreatorProjectUpdate, CreatorProjectResponse, CreatorProjectComplete
from app.models import CreatorProject, User
from app.auth import get_current_active_user, require_teacher_user
from app.repository import CreatorProjectRepository
from app.services.xp_service import award_xp, reverse_xp_for_source

router = APIRouter(prefix="/api/projects", tags=["projects"])

COMPLETED = 'Completed'
SOURCE_TYPE = 'creator_project'

@router.get("/", response_model=List[CreatorProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    return await CreatorProjectRepository.list(db, tenant_id=user.tenant_id)

@router.get("/active", response_model=List[CreatorProjectResponse])
async def list_active_projects(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    return await CreatorProjectRepository.list(db, tenant_id=user.tenant_id, status='In Progress')

@router.post("/", response_model=CreatorProjectResponse)
async def create_project(project: CreatorProjectCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    new_project = CreatorProject(**project.model_dump(), tenant_id=user.tenant_id)
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return new_project

@router.post("/{id}/complete", response_model=CreatorProjectResponse)
async def complete_project(id: int, complete_data: CreatorProjectComplete, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    project = await CreatorProjectRepository.get(db, tenant_id=user.tenant_id, project_id=id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.status == COMPLETED:
        raise HTTPException(status_code=409, detail="Already completed")

    project.status = COMPLETED
    project.completion_date = date.today()
    project.project_summary = complete_data.project_summary
    project.project_attachment = complete_data.project_attachment

    # XP comes from the stored row, never the request body.
    await award_xp(
        db,
        tenant_id=user.tenant_id,
        student_id=user.id,
        delta=project.xp_reward,
        reason=f"Completed project: {project.title}",
        source_type=SOURCE_TYPE,
        source_id=project.id,
    )

    await db.commit()
    await db.refresh(project)
    return project

@router.post("/{id}/uncomplete", response_model=CreatorProjectResponse)
async def uncomplete_project(id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    project = await CreatorProjectRepository.get(db, tenant_id=user.tenant_id, project_id=id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.status = 'In Progress'
    project.completion_date = None
    await reverse_xp_for_source(
        db,
        tenant_id=user.tenant_id,
        source_type=SOURCE_TYPE,
        source_id=project.id,
        reason=f"Reverted project: {project.title}",
    )

    await db.commit()
    await db.refresh(project)
    return project

@router.put("/{id}", response_model=CreatorProjectResponse)
async def update_project(id: int, project_data: CreatorProjectUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    project = await CreatorProjectRepository.get(db, tenant_id=user.tenant_id, project_id=id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    was_completed = project.status == COMPLETED
    for key, value in project_data.model_dump().items():
        setattr(project, key, value)
    now_completed = project.status == COMPLETED

    # CreatorProjectUpdate carries `status`, so this endpoint can move a
    # project in or out of Completed. Both directions have to move the ledger,
    # otherwise editing status is a way to farm XP without touching /complete.
    if was_completed and not now_completed:
        project.completion_date = None
        await reverse_xp_for_source(
            db,
            tenant_id=user.tenant_id,
            source_type=SOURCE_TYPE,
            source_id=project.id,
            reason=f"Reverted project: {project.title}",
        )
    elif now_completed and not was_completed:
        project.completion_date = date.today()
        await award_xp(
            db,
            tenant_id=user.tenant_id,
            student_id=user.id,
            delta=project.xp_reward,
            reason=f"Completed project: {project.title}",
            source_type=SOURCE_TYPE,
            source_id=project.id,
        )

    await db.commit()
    await db.refresh(project)
    return project

@router.delete("/{id}")
async def delete_project(id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    project = await CreatorProjectRepository.get(db, tenant_id=user.tenant_id, project_id=id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Reverse before deleting, or the XP outlives the thing that earned it.
    await reverse_xp_for_source(
        db,
        tenant_id=user.tenant_id,
        source_type=SOURCE_TYPE,
        source_id=project.id,
        reason=f"Deleted project: {project.title}",
    )
    await db.delete(project)
    await db.commit()
    return {"message": "Project deleted"}
