from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from datetime import date
from app.database import get_db
from app.schemas import CreatorProjectCreate, CreatorProjectUpdate, CreatorProjectResponse, CreatorProjectComplete
from app.models import CreatorProject
from app.auth import get_current_user, require_teacher

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.get("/", response_model=List[CreatorProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(CreatorProject).order_by(CreatorProject.created_at.desc()))
    return result.scalars().all()

@router.get("/active", response_model=List[CreatorProjectResponse])
async def list_active_projects(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(CreatorProject).where(CreatorProject.status == 'In Progress').order_by(CreatorProject.created_at.desc()))
    return result.scalars().all()

@router.post("/", response_model=CreatorProjectResponse)
async def create_project(project: CreatorProjectCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    new_project = CreatorProject(**project.model_dump())
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return new_project

@router.post("/{id}/complete", response_model=CreatorProjectResponse)
async def complete_project(id: int, complete_data: CreatorProjectComplete, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(CreatorProject).where(CreatorProject.id == id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.status = 'Completed'
    project.completion_date = date.today()
    project.project_summary = complete_data.project_summary
    project.project_attachment = complete_data.project_attachment
    await db.commit()
    await db.refresh(project)
    return project

@router.put("/{id}", response_model=CreatorProjectResponse)
async def update_project(id: int, project_data: CreatorProjectUpdate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(CreatorProject).where(CreatorProject.id == id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in project_data.model_dump().items():
        setattr(project, key, value)
    await db.commit()
    await db.refresh(project)
    return project

@router.delete("/{id}")
async def delete_project(id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(CreatorProject).where(CreatorProject.id == id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()
    return {"message": "Project deleted"}
