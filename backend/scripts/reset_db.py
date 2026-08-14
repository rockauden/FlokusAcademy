"""DESTROYS the entire database.

On Postgres this drops and recreates the `public` schema — every table,
sequence, view, and RLS policy goes with it, including `alembic_version`. On
SQLite it drops every table it finds, alembic_version included.

Why "drop the schema" rather than "drop the tables the models know about":
production was originally built by SQLAlchemy's create_all() before Alembic
existed, then later `alembic stamp head` marked the full migration chain as
already applied without ever running it. The live schema and the chain have
since diverged — stale tables (courses/modules/tasks) the chain would have
renamed away, and columns (rewards.description, users.tenant_id, ...) the
chain would have added, are both missing. A migration can only ever ADD to
what stamp already claims is done; it cannot make Alembic re-examine a schema
it believes it already built. The only way back to a state where the chain
and the database agree is to remove everything stamp lied about and let
`alembic upgrade head` build it for real.

Usage (from backend/):
    python -m scripts.reset_db

Interactive by default — you must type the database name shown to confirm.
For a non-interactive console that has no real stdin, set:
    RESET_DB_CONFIRM=<database name>
and pass --yes. The two must match or nothing happens.

After this runs the database is EMPTY. Rebuild it with:
    alembic upgrade head
    python -m app.seed

Do NOT run the backfill scripts afterward — seed.py creates both accounts
with correct PIN hashes directly, and a freshly reset database has no
historical completions or purchases for backfill_xp_ledger to find.
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.database import engine


def _target_description() -> tuple[str, str]:
    """Return (redacted connection string, database name) for display."""
    parts = urlsplit(engine.url.render_as_string(hide_password=False))
    db_name = (parts.path or "").lstrip("/") or "(unknown)"
    netloc = parts.hostname or "(unknown host)"
    if parts.port:
        netloc += f":{parts.port}"
    redacted = f"{parts.scheme}://{parts.username or ''}@{netloc}/{db_name}"
    return redacted, db_name


async def _table_count() -> int | None:
    dialect = engine.dialect.name
    async with engine.connect() as conn:
        if dialect == "postgresql":
            result = await conn.execute(
                text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'")
            )
        elif dialect == "sqlite":
            result = await conn.execute(text("SELECT count(*) FROM sqlite_master WHERE type='table'"))
        else:
            return None
        return result.scalar()


async def _reset_postgres() -> None:
    async with engine.begin() as conn:
        # DDL is transactional on Postgres: this either fully applies or
        # fully rolls back, never leaves a half-dropped schema. CASCADE takes
        # alembic_version with it, which is the entire point.
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))


async def _reset_sqlite() -> None:
    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        )
        # Table names come from sqlite_master itself, never from user input,
        # so interpolating them is safe — they cannot be bound as identifiers.
        for (name,) in result:
            await conn.execute(text(f'DROP TABLE IF EXISTS "{name}"'))


async def reset_database() -> None:
    dialect = engine.dialect.name
    if dialect == "postgresql":
        await _reset_postgres()
    elif dialect == "sqlite":
        await _reset_sqlite()
    else:
        raise SystemExit(f"reset_db.py has no logic for dialect {dialect!r} — refusing to guess.")


def _confirm(db_name: str, assume_yes: bool) -> bool:
    if assume_yes:
        if os.environ.get("RESET_DB_CONFIRM") == db_name:
            return True
        print(
            "--yes was passed but RESET_DB_CONFIRM does not match the target "
            "database name. Refusing to proceed non-interactively.",
            file=sys.stderr,
        )
        return False

    if not sys.stdin.isatty():
        print(
            "stdin is not a terminal and --yes was not passed with a matching "
            "RESET_DB_CONFIRM. Refusing to proceed.",
            file=sys.stderr,
        )
        return False

    print(f"Type the database name ({db_name}) to confirm, or anything else to abort:")
    return input("> ").strip() == db_name


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--yes",
        action="store_true",
        help="skip the interactive prompt (requires RESET_DB_CONFIRM=<db name> in the environment)",
    )
    args = parser.parse_args()

    redacted, db_name = _target_description()
    dialect = engine.dialect.name

    print("=" * 70)
    print("THIS WILL PERMANENTLY DELETE EVERY TABLE IN THIS DATABASE.")
    print("=" * 70)
    print(f"  Dialect: {dialect}")
    print(f"  Target : {redacted}")

    count = await _table_count()
    if count is not None:
        print(f"  Tables that will be destroyed: {count}")
    print()

    if not _confirm(db_name, args.yes):
        print("Aborted. Nothing was changed.")
        await engine.dispose()
        return 1

    print("Resetting...")
    await reset_database()
    print("Done. The database is now empty.")
    print()
    print("Next, from backend/:")
    print("  alembic upgrade head")
    print("  python -m app.seed")

    await engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
