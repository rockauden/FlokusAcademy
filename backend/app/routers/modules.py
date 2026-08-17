from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db
from app.schemas import ModuleCreate, ModuleUpdate, ModuleResponse
from app.models import Unit, User
from app.auth import get_current_active_user, require_teacher_user
from app.repository import UnitRepository

router = APIRouter(prefix="/api/modules", tags=["modules"])


def _to_response(unit: Unit) -> ModuleResponse:
    """The API still says course_id; internally it is program_id."""
    return ModuleResponse(
        id=unit.id,
        course_id=unit.program_id,
        title=unit.title,
        description=unit.description,
        week_start=unit.week_start,
        week_end=unit.week_end,
        sort_order=unit.sort_order,
        status=unit.status,
        is_active=unit.is_active,
        created_at=unit.created_at,
    )


@router.get("/", response_model=List[ModuleResponse])
async def list_modules(
    course_id: Optional[int] = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Active units by default; the unit manager asks for the rest. Same reason
    as courses.list_courses — a deactivated unit must stay reachable from the
    screen that deactivated it."""
    units = await UnitRepository.list(
        db, tenant_id=user.tenant_id, program_id=course_id, active_only=not include_inactive
    )
    return [_to_response(u) for u in units]

@router.post("/", response_model=ModuleResponse)
async def create_module(module: ModuleCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    payload = module.model_dump()
    payload['program_id'] = payload.pop('course_id')
    new_unit = Unit(**payload, tenant_id=user.tenant_id)
    db.add(new_unit)
    await db.commit()
    await db.refresh(new_unit)
    return _to_response(new_unit)

@router.get("/{id}", response_model=ModuleResponse)
async def get_module(id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    unit = await UnitRepository.get(db, tenant_id=user.tenant_id, unit_id=id, active_only=True)
    if not unit:
        raise HTTPException(status_code=404, detail="Module not found")
    return _to_response(unit)

@router.put("/{id}", response_model=ModuleResponse)
async def update_module(id: int, module_data: ModuleUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    unit = await UnitRepository.get(db, tenant_id=user.tenant_id, unit_id=id)
    if not unit:
        raise HTTPException(status_code=404, detail="Module not found")
    for key, value in module_data.model_dump().items():
        setattr(unit, key, value)
    await db.commit()
    await db.refresh(unit)
    return _to_response(unit)

@router.delete("/{id}")
async def delete_module(id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    unit = await UnitRepository.get(db, tenant_id=user.tenant_id, unit_id=id)
    if not unit:
        raise HTTPException(status_code=404, detail="Module not found")
    await db.delete(unit)
    await db.commit()
    return {"message": "Module deleted"}
