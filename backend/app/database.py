from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import settings

def _engine_options() -> dict:
    """Connection pool settings, which only make sense for a real server.

    This application is idle for most of the day and then used hard for a
    couple of hours -- a school morning. That is precisely the pattern that
    breaks a naive pool: Postgres (and anything proxying it) closes connections
    that have sat unused overnight, the pool keeps handing them out anyway, and
    the first request of the day fails on a socket that was closed hours ago.

    pool_pre_ping costs one trivial round trip per checkout and makes that
    impossible -- a dead connection is discovered and replaced before the query
    runs, rather than surfacing as an error to whoever opened the app first.

    pool_recycle retires connections well before any server or proxy idle
    timeout is likely to, so they are replaced on our schedule instead of being
    discovered dead on theirs.

    The size is deliberately small. One family generates a handful of
    concurrent requests, and a managed Postgres instance has a modest
    connection ceiling that a large pool would waste.
    """
    if settings.DATABASE_URL.startswith("sqlite"):
        # SQLite uses a pool implementation that accepts none of these, and
        # they would be meaningless against a local file anyway.
        return {}

    return {
        "pool_pre_ping": True,
        "pool_recycle": 1800,  # 30 minutes
        "pool_size": 5,
        "max_overflow": 5,
        # Fail fast rather than hanging a request behind an exhausted pool.
        "pool_timeout": 10,
    }


engine = create_async_engine(settings.DATABASE_URL, echo=False, **_engine_options())
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
