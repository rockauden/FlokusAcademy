"""One-off backfill: give the existing 'sonny' row a PIN hash.

The seeder only ever touches users that do not exist yet, so a database
created before STUDENT_PIN was introduced still has `pin_hash = NULL` for the
student — and since Sprint 2 that means "cannot log in at all".

    cd backend
    python -m scripts.backfill_student_pin

Safe by default: if the student already has a PIN it is left alone. Pass
--force to overwrite it (use this when resetting a forgotten PIN).

Requires STUDENT_PIN and the usual SECRET_KEY / ADMIN_PIN in the environment,
since importing app.config validates all of them.
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.auth import hash_pin
from app.config import settings
from app.database import async_session_maker, engine
from app.models import User

STUDENT_USERNAME = "sonny"


async def backfill(force: bool = False) -> int:
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.username == STUDENT_USERNAME)
        )
        student = result.scalars().first()

        if student is None:
            print(
                f"No '{STUDENT_USERNAME}' user found. Nothing to backfill — "
                f"run `python -m app.seed` to create the initial accounts."
            )
            return 1

        if student.pin_hash and not force:
            print(
                f"'{STUDENT_USERNAME}' already has a PIN set; leaving it unchanged.\n"
                f"Pass --force to overwrite it."
            )
            return 0

        action = "Reset" if student.pin_hash else "Set"
        student.pin_hash = hash_pin(settings.STUDENT_PIN.get_secret_value())
        await session.commit()
        print(f"{action} PIN for '{STUDENT_USERNAME}' from STUDENT_PIN.")
        return 0


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing PIN instead of skipping",
    )
    args = parser.parse_args()
    try:
        return await backfill(force=args.force)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
