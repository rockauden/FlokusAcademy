from datetime import datetime, timedelta, timezone
import secrets
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_db, set_session_tenant
from app.models import User
from typing import Optional, Dict, Any

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_pin(pin: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pin.encode('utf-8'), salt).decode('utf-8')

def verify_pin(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except ValueError:
        return False

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

REFRESH_COOKIE_NAME = "flokus_refresh"
# Scoped to the auth endpoints so the browser does not attach it to every
# ordinary API call.
REFRESH_COOKIE_PATH = "/api/auth"


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": ACCESS_TOKEN_TYPE})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY.get_secret_value(), algorithm="HS256")
    return encoded_jwt


def create_refresh_token(data: dict) -> tuple[str, str]:
    """Return (token, jti). The jti is stored on the user row so that only the
    most recently issued refresh token is accepted."""
    token_id = secrets.token_urlsafe(32)
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": REFRESH_TOKEN_TYPE, "jti": token_id})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY.get_secret_value(), algorithm="HS256")
    return encoded_jwt, token_id


def decode_token(token: str, expected_type: str) -> Dict[str, Any]:
    """Decode and assert the token is the kind the caller expects.

    Without the type check a refresh token — which lives far longer — would be
    accepted anywhere an access token is, defeating the short access lifetime.
    """
    payload = jwt.decode(token, settings.SECRET_KEY.get_secret_value(), algorithms=["HS256"])
    if payload.get("type") != expected_type:
        raise JWTError(f"Expected a {expected_type} token")
    return payload


def set_refresh_cookie(response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
    )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token, ACCESS_TOKEN_TYPE)
        username: Optional[str] = payload.get("sub")
        role: Optional[str] = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
        return {"sub": username, "role": role}
    except JWTError:
        raise credentials_exception

async def get_current_db_user(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> User:
    """Resolve the JWT subject to the actual user row.

    get_current_user only decodes the token, so it carries no primary key and
    no tenant — both of which are needed to scope queries and ledger writes.
    Re-reading the row also means a token for a deleted account stops working
    immediately rather than at natural expiry.
    """
    result = await db.execute(select(User).where(User.username == current_user["sub"]))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    # Bind the session to this user's tenant so the Postgres RLS policies
    # apply to everything the handler goes on to query. `users` is exempt from
    # RLS precisely so this lookup can happen before a tenant is known.
    await set_session_tenant(db, user.tenant_id)
    return user

async def get_current_active_user(user: User = Depends(get_current_db_user)) -> User:
    """The dependency routers should use.

    A short token expiry limits how long a stolen token is useful; this closes
    the other half — a deactivated account loses access on its very next
    request rather than whenever its token happens to expire.
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def require_teacher(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Teacher role required."
        )
    return current_user

async def require_teacher_user(user: User = Depends(get_current_active_user)) -> User:
    """Teacher guard that yields the user row, so handlers can scope by tenant."""
    if user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Teacher role required."
        )
    return user
