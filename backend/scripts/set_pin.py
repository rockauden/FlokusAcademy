"""Change the PIN for 'dad' or 'sonny', on whatever database DATABASE_URL points at.

WHY THIS EXISTS
---------------
Changing ADMIN_PIN or STUDENT_PIN in the environment does NOT change anybody's
PIN. The seeder (services/curriculum_seeder.py) only sets pin_hash when it is
*creating* a user that does not exist yet -- it deliberately leaves existing
accounts alone, so re-running it is safe. The consequence is a trap: you can
change the variable, redeploy, feel safer, and still be logging in with the old
PIN. This script is the thing that actually writes a new hash.

backfill_student_pin.py does a narrower version of this (student only, reading
STUDENT_PIN from the environment). This one covers both accounts and takes the
new PIN interactively, so it never lands in your shell history, in a Railway
variable, or in the process list where `ps` can see it.

WHERE TO RUN IT
---------------
Easiest is Railway's **Console** tab on the FlokusAcademy service: the
environment there already has DATABASE_URL and SECRET_KEY, so there is nothing
to configure and the database URL never touches your laptop.

    python -m scripts.set_pin dad

From your own machine instead, set DATABASE_URL to Railway's
DATABASE_PUBLIC_URL first (see docs/BACKUP_AND_RESTORE.md).

If the console is not interactive, put the new PIN in NEW_PIN instead:

    NEW_PIN=<the new pin> python -m scripts.set_pin dad

HOW LONG SHOULD A PIN BE
------------------------
The login endpoint is rate limited to 5 attempts a minute per address, so
length matters more than character variety here:

    4 digits  =     10,000 combinations  -- about 33 hours. Not enough.
    8 digits  =    100 million           -- about 38 years.
    10 digits = 10,000 million           -- longer than anyone will wait.

Eight digits is the floor this script enforces. The login field is
`inputmode="numeric"`, which means phones and tablets show a number keypad --
so digits keep the login usable for a child on a tablet. Letters work too on a
desktop keyboard if you would rather use a passphrase.
"""
import argparse
import asyncio
import os
import sys
from getpass import getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.auth import hash_pin
from app.database import async_session_maker, engine
from app.models import User

USERNAMES = ("dad", "sonny")
MIN_LENGTH = 8


def weak_reason(pin: str) -> str | None:
    """Reject the handful of choices that undo the length benefit entirely."""
    if len(pin) < MIN_LENGTH:
        return f"it is {len(pin)} characters; the minimum is {MIN_LENGTH}"
    if len(set(pin)) == 1:
        return "it is the same character repeated"
    digits = [int(c) for c in pin if c.isdigit()]
    if len(digits) == len(pin) >= 3:
        steps = {b - a for a, b in zip(digits, digits[1:])}
        if steps in ({1}, {-1}):
            return "it is a run of consecutive digits"
    return None


def read_new_pin(username: str) -> str | None:
    """Interactively, or from NEW_PIN when there is no terminal to prompt on."""
    from_env = os.environ.get("NEW_PIN")
    if from_env:
        problem = weak_reason(from_env)
        if problem:
            print(f"Refused: {problem}.")
            return None
        return from_env

    if not sys.stdin.isatty():
        print("No terminal to prompt on. Set NEW_PIN instead:")
        print(f"    NEW_PIN=<the new pin> python -m scripts.set_pin {username}")
        return None

    while True:
        first = getpass(f"New PIN for '{username}' (typing is hidden): ")
        problem = weak_reason(first)
        if problem:
            print(f"Refused: {problem}. Try again.\n")
            continue
        if first != getpass("Type it again to confirm: "):
            print("Those did not match. Try again.\n")
            continue
        return first


async def set_pin(username: str) -> int:
    async with async_session_maker() as session:
        # `users` is exempt from row-level security -- it is the table a tenant
        # is derived from, so it cannot also be gated on one. No tenant to bind.
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalars().first()

        if user is None:
            print(f"No '{username}' account on this database.")
            print("Check DATABASE_URL is pointing where you think it is.")
            return 1

        new_pin = read_new_pin(username)
        if new_pin is None:
            return 1

        user.pin_hash = hash_pin(new_pin)
        await session.commit()

        print(f"\nPIN changed for '{username}' ({user.display_name}).")
        print("The old PIN stops working immediately.")
        # Any signed-in session keeps its access token until it expires, which
        # is why this says what it says rather than claiming everything is
        # locked out. Sign out in the app to end an existing session now.
        print("Existing signed-in sessions last until their token expires (4 hours).")
        return 0


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Change a Flokus Academy login PIN.",
        epilog="The new PIN is never passed as an argument, so it stays out of your shell history.",
    )
    parser.add_argument("username", choices=USERNAMES, help="which account to change")
    args = parser.parse_args()
    try:
        return await set_pin(args.username)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
