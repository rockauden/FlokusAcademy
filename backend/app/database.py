from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()

TENANT_SETTING = 'app.tenant_id'


async def set_session_tenant(session: AsyncSession, tenant_id: int) -> None:
    """Bind this session to a tenant for the Postgres RLS policies.

    Session-scoped (`set_config(..., is_local => false)`) rather than
    transaction-scoped on purpose: handlers commit part-way through a request
    and then keep querying, and a `SET LOCAL` would be discarded at that commit
    — every subsequent query would fail closed and the endpoint would break.
    get_db resets it when the session closes, so the value never rides a
    pooled connection into the next request.

    No-op on SQLite, which has no row-level security.
    """
    if session.bind.dialect.name != 'postgresql':
        return
    await session.execute(
        text("SELECT set_config(:name, :value, false)"),
        {"name": TENANT_SETTING, "value": str(tenant_id)},
    )


async def _clear_session_tenant(session: AsyncSession) -> None:
    if session.bind.dialect.name != 'postgresql':
        return
    try:
        await session.execute(
            text("SELECT set_config(:name, '', false)"), {"name": TENANT_SETTING}
        )
    except Exception:
        # The connection is going back to the pool either way; a failure here
        # must not mask the original error.
        pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            # Without this a handler that raises mid-flush returns a dirty
            # session to the pool.
            await session.rollback()
            raise
        finally:
            await _clear_session_tenant(session)
