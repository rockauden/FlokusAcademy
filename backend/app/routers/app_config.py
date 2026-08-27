"""Settings that are data, not deployment configuration.

The school week used to be `weekday() >= 4` in the scheduler and the academic
year's first day was found by searching the calendar for an event whose title
matched '%First day%' — a lookup that fails silently, and late, the moment
someone renames it. Both are now rows in `app_config`, which means changing
them is an edit rather than a deploy.

Deliberately not a general key-value store. Only the keys in EDITABLE_KEYS can
be read or written here, and each is validated on the way in: a school week
that parses to no days at all would hang the scheduler's day-by-day search, so
that has to be refused at write time rather than absorbed at read time.

Named app_config after the table rather than `config`, which is already taken
by app/config.py — the environment-and-secrets module. These are two different
kinds of setting: one changes with a deploy, the other with an edit.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_teacher_user
from app.database import get_db
from app.models import User
from app.repository import AppConfigRepository
from app.schemas import AppConfigValue
from app.services.school_days import DEFAULT_ACADEMIC_YEAR_START, WEEKDAY_NUMBERS

router = APIRouter(prefix="/api/config", tags=["config"])


def _validate_school_days(value: str) -> None:
    tokens = [part.strip() for part in value.split(',') if part.strip()]
    unknown = [t for t in tokens if t.lower()[:3] not in WEEKDAY_NUMBERS]
    if unknown or not tokens:
        raise HTTPException(
            status_code=422,
            detail=(
                f"school_days must be a comma-separated list of weekday names, e.g. "
                f"'Mon,Tue,Wed,Thu'. Not recognised: {', '.join(unknown) or '(empty)'}"
            ),
        )


def _validate_iso_date(value: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=422, detail=f"academic_year_start must be an ISO date (YYYY-MM-DD), got {value!r}"
        )


def _validate_grade_level(value: str) -> None:
    if not value.isdigit():
        raise HTTPException(status_code=422, detail=f"grade_level must be a whole number, got {value!r}")


# The defaults are what the migration seeds, repeated here so a key deleted by
# hand still reads as something sensible rather than as absent.
EDITABLE_KEYS: dict[str, tuple[str, object]] = {
    'school_days': ('Mon,Tue,Wed,Thu', _validate_school_days),
    'academic_year_start': (DEFAULT_ACADEMIC_YEAR_START.isoformat(), _validate_iso_date),
    'grade_level': ('5', _validate_grade_level),
}


@router.get("/")
async def get_config(db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    stored = await AppConfigRepository.get_many(db, tenant_id=user.tenant_id, keys=tuple(EDITABLE_KEYS))
    return {key: stored.get(key, default) for key, (default, _) in EDITABLE_KEYS.items()}


@router.put("/{key}")
async def set_config(
    key: str,
    body: AppConfigValue,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_teacher_user),
):
    if key not in EDITABLE_KEYS:
        raise HTTPException(
            status_code=404,
            detail=f"{key!r} is not an editable setting. Editable: {', '.join(EDITABLE_KEYS)}",
        )

    _, validate = EDITABLE_KEYS[key]
    validate(body.value)

    await AppConfigRepository.set(db, tenant_id=user.tenant_id, key=key, value=body.value)
    await db.commit()

    # Echo the whole map back: the settings screen shows all three, and one
    # response beats a write followed by a read.
    stored = await AppConfigRepository.get_many(db, tenant_id=user.tenant_id, keys=tuple(EDITABLE_KEYS))
    return {k: stored.get(k, default) for k, (default, _) in EDITABLE_KEYS.items()}
