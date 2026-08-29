"""Report whether Postgres row-level security is actually in force.

WHY THIS EXISTS
---------------
Migration 7b3a32e71a94 enables RLS on every tenant table and applies FORCE ROW
LEVEL SECURITY, because plain ENABLE is bypassed by the table owner and the
application connects as the owner on most managed Postgres providers. That much
is in the schema and can be read in the migration.

What the migration cannot control is the *role the application connects as*.
Superusers bypass RLS regardless of ENABLE or FORCE -- and managed providers,
Railway included, commonly hand out a superuser by default. So the policies can
be perfectly correct and never apply to a single query, with nothing anywhere
reporting the discrepancy. This script is how you find out.

With one tenant and one family it changes nothing today. It matters the day
there is a second tenant, or the day a query somewhere loses its tenant filter
and the backstop that should have caught it was never running.

    python -m scripts.check_db_role

Run it in Railway's Console tab on the FlokusAcademy service, where
DATABASE_URL already points at production. Exit code 0 if RLS is in force,
1 if it is being bypassed or is missing from a table that should have it.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.database import async_session_maker, engine

# The tables whose contents would matter most if isolation silently failed.
# Not the full list -- enough to prove the policies were applied.
SAMPLE_TABLES = (
    "assignments",
    "lessons",
    "chat_history",
    "consent_records",
    "safety_events",
)


async def check() -> int:
    async with async_session_maker() as session:
        if session.bind.dialect.name != "postgresql":
            print("Not a Postgres database, so there is no row-level security to check.")
            print("Point DATABASE_URL at production and run this again.")
            return 1

        row = (
            await session.execute(
                text(
                    "SELECT current_user, usesuper FROM pg_user "
                    "WHERE usename = current_user"
                )
            )
        ).first()

        if row is None:
            print("Could not identify the connecting role. Unexpected; stopping here.")
            return 1

        role, is_super = row
        print(f"\nThe application connects as:  {role}")

        rows = (
            await session.execute(
                text(
                    "SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class "
                    "WHERE relname = ANY(:names) ORDER BY relname"
                ),
                {"names": list(SAMPLE_TABLES)},
            )
        ).all()

        print("\n  table              RLS enabled   FORCED")
        for name, enabled, forced in rows:
            flag = "" if (enabled and forced) else "   <-- not protected"
            print(f"  {name:<18} {str(enabled):<13} {forced}{flag}")

        missing = {t for t in SAMPLE_TABLES} - {r[0] for r in rows}
        for name in sorted(missing):
            print(f"  {name:<18} (table not found)")

        unprotected = [r[0] for r in rows if not (r[1] and r[2])] + sorted(missing)

        print()
        if is_super:
            print("SUPERUSER: yes.")
            print("  Superusers bypass row-level security entirely, so the policies below")
            print("  are not being applied to anything this application does.")
            print("  Fix: create a non-superuser role, grant it the table privileges it")
            print("  needs, and point DATABASE_URL at that role instead. Then re-run this.")
            return 1

        print("SUPERUSER: no -- so the policies below do apply to this connection.")
        if unprotected:
            print(f"\nBut these tables are not protected: {', '.join(unprotected)}")
            print("Every table carrying tenant_id should have RLS enabled AND forced.")
            return 1

        print("Row-level security is enabled and forced on every table checked.")
        return 0


async def main() -> int:
    try:
        return await check()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
