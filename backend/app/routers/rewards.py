from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import date
from app.database import get_db
from app.schemas import RewardCreate, RewardResponse, PurchaseCreate, PurchaseResponse
from app.models import Reward, Purchase, User
from app.auth import get_current_active_user, require_teacher_user
from app.repository import PurchaseRepository, RewardRepository
from app.services.xp_service import award_xp, compute_xp_balance, compute_xp_totals

router = APIRouter(prefix="/api/rewards", tags=["rewards"])

@router.get("/", response_model=List[RewardResponse])
async def list_rewards(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    return await RewardRepository.list(db, tenant_id=user.tenant_id)

@router.post("/", response_model=RewardResponse)
async def create_reward(reward: RewardCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    new_reward = Reward(**reward.model_dump(), tenant_id=user.tenant_id)
    db.add(new_reward)
    await db.commit()
    await db.refresh(new_reward)
    return new_reward

@router.put("/{id}", response_model=RewardResponse)
async def update_reward(id: int, reward: RewardCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    existing = await RewardRepository.get(db, tenant_id=user.tenant_id, reward_id=id)
    if not existing:
        raise HTTPException(status_code=404, detail="Reward not found")
    for key, value in reward.model_dump().items():
        setattr(existing, key, value)
    await db.commit()
    await db.refresh(existing)
    return existing

@router.delete("/{id}")
async def delete_reward(id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    existing = await RewardRepository.get(db, tenant_id=user.tenant_id, reward_id=id)
    if not existing:
        raise HTTPException(status_code=404, detail="Reward not found")
    await db.delete(existing)
    await db.commit()
    return {"message": "Reward deleted"}

@router.get("/balance")
async def get_xp_balance(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    """Get current XP balance: total earned minus total spent, from the ledger."""
    xp_earned, xp_spent = await compute_xp_totals(db, tenant_id=user.tenant_id, student_id=user.id)
    balance = await compute_xp_balance(db, tenant_id=user.tenant_id, student_id=user.id)
    return {"xp_earned": xp_earned, "xp_spent": xp_spent, "xp_balance": balance}

@router.post("/purchase", response_model=PurchaseResponse)
async def purchase_reward(purchase: PurchaseCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    # No explicit db.begin() here: the get_current_db_user dependency has
    # already issued a SELECT, so the session has autobegun and opening a
    # second transaction raises. Everything below still runs inside that one
    # transaction — the row lock holds and the commit is atomic. Every
    # rejection happens before any mutation, so a raise leaves nothing behind.
    reward = await RewardRepository.get(
        db,
        tenant_id=user.tenant_id,
        reward_id=purchase.reward_id,
        active_only=True,
        for_update=True,
    )
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")

    if reward.inventory_qty <= 0:
        raise HTTPException(status_code=409, detail=f"'{reward.name}' is out of stock")

    balance = await compute_xp_balance(db, tenant_id=user.tenant_id, student_id=user.id)
    if balance < reward.xp_cost:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough XP. Balance: {balance}, Cost: {reward.xp_cost}",
        )

    reward.inventory_qty -= 1

    # Name and cost are snapshotted from the server's row so purchase
    # history survives a later price change — and so the client cannot
    # dictate either one.
    new_purchase = Purchase(
        tenant_id=user.tenant_id,
        reward_name=reward.name,
        xp_cost=reward.xp_cost,
        purchase_date=date.today(),
        is_claimed=False,
    )
    db.add(new_purchase)
    await db.flush()  # assign new_purchase.id before referencing it

    await award_xp(
        db,
        tenant_id=user.tenant_id,
        student_id=user.id,
        delta=-reward.xp_cost,
        reason=f"Purchased: {reward.name}",
        source_type="purchase",
        source_id=new_purchase.id,
    )

    await db.commit()
    await db.refresh(new_purchase)
    return new_purchase

@router.get("/purchases", response_model=List[PurchaseResponse])
async def list_purchases(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    return await PurchaseRepository.list(db, tenant_id=user.tenant_id)
