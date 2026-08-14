from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from app.database import get_db
from app.schemas import LoginRequest, TokenResponse
from app.models import User
from app.auth import (
    REFRESH_COOKIE_NAME,
    REFRESH_TOKEN_TYPE,
    clear_refresh_cookie,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    set_refresh_cookie,
    verify_pin,
)
from app.rate_limit import limiter

router = APIRouter(prefix="/api/auth", tags=["auth"])


async def _issue_session(response: Response, db: AsyncSession, user: User) -> TokenResponse:
    """Mint an access token and plant a rotated refresh cookie."""
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    refresh_token, token_id = create_refresh_token(data={"sub": user.username, "role": user.role})

    # Storing the jti is what invalidates the previous refresh token.
    user.refresh_token_id = token_id
    await db.commit()

    set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token, role=user.role, display_name=user.display_name)


# The body model is `credentials`, not `request` — slowapi resolves the client
# address from a parameter that must be named `request` and be a Starlette
# Request, so the two cannot share the name.
@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, response: Response, credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == credentials.username))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or PIN")

    # Every role must present a credential. An account with no PIN hash cannot
    # be logged into at all — it is not a pass-through.
    if not user.pin_hash:
        raise HTTPException(status_code=401, detail="Account not provisioned for login")

    if not credentials.pin or not verify_pin(credentials.pin, user.pin_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or PIN")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is deactivated")

    return await _issue_session(response, db, user)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
async def refresh_session(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    flokus_refresh: Optional[str] = Cookie(default=None),
):
    """Exchange the refresh cookie for a new access token, rotating the cookie.

    The cookie is HttpOnly, so this is the only way the browser can spend it —
    page JavaScript can neither read nor forge it.
    """
    if not flokus_refresh:
        raise HTTPException(status_code=401, detail="No refresh token")

    try:
        payload = decode_token(flokus_refresh, REFRESH_TOKEN_TYPE)
    except JWTError:
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    username = payload.get("sub")
    token_id = payload.get("jti")
    if not username or not token_id:
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if not user or not user.is_active:
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    # Only the most recently issued refresh token is accepted. A replayed older
    # one fails here even though its signature and expiry are still valid.
    if user.refresh_token_id != token_id:
        user.refresh_token_id = None  # treat replay as compromise: end the session
        await db.commit()
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Refresh token has already been used")

    return await _issue_session(response, db, user)


@router.post("/logout")
async def logout(response: Response, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(User).where(User.username == current_user["sub"]))
    user = result.scalars().first()
    if user:
        user.refresh_token_id = None  # the outstanding refresh token stops working
        await db.commit()
    clear_refresh_cookie(response)
    return {"message": "Logged out"}


@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == current_user["sub"]))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user.username, "display_name": user.display_name, "role": user.role}
