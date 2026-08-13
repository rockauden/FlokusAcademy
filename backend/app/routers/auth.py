from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.schemas import LoginRequest, TokenResponse
from app.models import User
from app.auth import verify_pin, create_access_token, hash_pin, get_current_user
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Check if users table is empty
    result = await db.execute(select(User))
    users = result.scalars().all()
    if not users:
        dad = User(username='dad', display_name='Dad', role='teacher', pin_hash=hash_pin(settings.ADMIN_PIN))
        sonny = User(username='sonny', display_name='Sonny', role='student', pin_hash=None)
        db.add_all([dad, sonny])
        await db.commit()
    
    # Authenticate
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or PIN")
    
    if user.role == 'teacher':
        if not request.pin or not verify_pin(request.pin, user.pin_hash):
            raise HTTPException(status_code=400, detail="Incorrect username or PIN")
    
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return TokenResponse(access_token=access_token, role=user.role, display_name=user.display_name)

@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == current_user["sub"]))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user.username, "display_name": user.display_name, "role": user.role}
