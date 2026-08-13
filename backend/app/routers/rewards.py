from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from datetime import date
from app.database import get_db
from app.schemas import RewardCreate, RewardResponse, PurchaseCreate, PurchaseResponse
from app.models import Reward, Purchase, Task
from app.auth import get_current_user, require_teacher

router = APIRouter(prefix="/api/rewards", tags=["rewards"])

@router.get("/", response_model=List[RewardResponse])
async def list_rewards(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(Reward).order_by(Reward.xp_cost))
    return result.scalars().all()

@router.post("/", response_model=RewardResponse)
async def create_reward(reward: RewardCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    new_reward = Reward(**reward.model_dump())
    db.add(new_reward)
    await db.commit()
    await db.refresh(new_reward)
    return new_reward

@router.put("/{id}", response_model=RewardResponse)
async def update_reward(id: int, reward: RewardCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(Reward).where(Reward.id == id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=404, detail="Reward not found")
    for key, value in reward.model_dump().items():
        setattr(existing, key, value)
    await db.commit()
    await db.refresh(existing)
    return existing

@router.delete("/{id}")
async def delete_reward(id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(Reward).where(Reward.id == id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=404, detail="Reward not found")
    await db.delete(existing)
    await db.commit()
    return {"message": "Reward deleted"}

@router.get("/balance")
async def get_xp_balance(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Get current XP balance: total earned minus total spent."""
    # XP earned from completed tasks (boss fights count double)
    result = await db.execute(select(Task).where(Task.is_completed == True))
    tasks = result.scalars().all()
    xp_earned = sum(t.xp_reward * (2 if t.is_boss_fight else 1) for t in tasks)

    # XP spent on purchases
    result = await db.execute(select(Purchase))
    purchases = result.scalars().all()
    xp_spent = sum(p.xp_cost for p in purchases)

    return {"xp_earned": xp_earned, "xp_spent": xp_spent, "xp_balance": xp_earned - xp_spent}

@router.post("/purchase", response_model=PurchaseResponse)
async def purchase_reward(purchase: PurchaseCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Check balance
    result = await db.execute(select(Task).where(Task.is_completed == True))
    tasks = result.scalars().all()
    xp_earned = sum(t.xp_reward * (2 if t.is_boss_fight else 1) for t in tasks)

    result = await db.execute(select(Purchase))
    purchases = result.scalars().all()
    xp_spent = sum(p.xp_cost for p in purchases)

    balance = xp_earned - xp_spent
    if balance < purchase.xp_cost:
        raise HTTPException(status_code=400, detail=f"Not enough XP. Balance: {balance}, Cost: {purchase.xp_cost}")

    new_purchase = Purchase(**purchase.model_dump())
    db.add(new_purchase)
    await db.commit()
    await db.refresh(new_purchase)
    return new_purchase

@router.get("/purchases", response_model=List[PurchaseResponse])
async def list_purchases(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(Purchase).order_by(Purchase.purchase_date.desc()))
    return result.scalars().all()
