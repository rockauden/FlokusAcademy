from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.database import get_db
from app.schemas import ModuleCreate, ModuleUpdate, ModuleResponse
from app.models import Module
from app.auth import get_current_user, require_teacher

router = APIRouter(prefix="/api/modules", tags=["modules"])

@router.get("/", response_model=List[ModuleResponse])
async def list_modules(course_id: Optional[int] = None, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    query = select(Module).where(Module.is_active == True)
    if course_id:
        query = query.where(Module.course_id == course_id)
    query = query.order_by(Module.sort_order)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=ModuleResponse)
async def create_module(module: ModuleCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    new_module = Module(**module.model_dump())
    db.add(new_module)
    await db.commit()
    await db.refresh(new_module)
    return new_module

@router.get("/{id}", response_model=ModuleResponse)
async def get_module(id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(Module).where(Module.id == id, Module.is_active == True))
    module = result.scalars().first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module

@router.put("/{id}", response_model=ModuleResponse)
async def update_module(id: int, module_data: ModuleUpdate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(Module).where(Module.id == id))
    module = result.scalars().first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    for key, value in module_data.model_dump().items():
        setattr(module, key, value)
    await db.commit()
    await db.refresh(module)
    return module

@router.delete("/{id}")
async def delete_module(id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(Module).where(Module.id == id))
    module = result.scalars().first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    await db.delete(module)
    await db.commit()
    return {"message": "Module deleted"}
