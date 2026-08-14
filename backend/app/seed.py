"""Standalone seed command.

Seeding used to run inside the FastAPI startup hook, which meant every replica
raced to write the same rows on every boot. It now runs explicitly:

    python -m app.seed

Run it once after `alembic upgrade head`. It is idempotent, so re-running it is
safe: existing users, rewards and courses are left untouched.
"""
import asyncio

from app.database import async_session_maker, engine, set_session_tenant
from app.services.curriculum_seeder import seed_initial_data

DEFAULT_TENANT_ID = 1


async def main() -> None:
    async with async_session_maker() as session:
        # Under Postgres RLS the seed rows would be rejected without this —
        # the policy doubles as the WITH CHECK on INSERT.
        await set_session_tenant(session, DEFAULT_TENANT_ID)
        await seed_initial_data(session)
    await engine.dispose()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
