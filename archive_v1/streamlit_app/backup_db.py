r"""
Back up the live school database, off this machine.

(The `r` on this docstring matters: the Windows paths below contain `\s` and
`\e`, which Python 3.12 reads as invalid escape sequences and warns about every
time the script runs. A raw string takes the backslashes literally.)

WHY THIS EXISTS
---------------
flokus.db holds a year of Sonny's schoolwork and it is the one file here that
cannot be regenerated. Code is backed up by pushing to GitHub; the database is
not, because it is gitignored -- deliberately, since a database does not belong
in version control.

Until August 2026 it happened to be inside a OneDrive folder, so it was being
backed up by accident. Moving the repo out of OneDrive removed that, which is
what this replaces. An accidental backup is not a backup: nobody knew it was
there, so nobody would have noticed it stop.

WHY THE SQLITE BACKUP API RATHER THAN COPYING THE FILE
------------------------------------------------------
Copying a SQLite file while something has it open can produce a torn copy --
the file is written in pages, and a plain copy can catch it mid-write. It looks
fine until the day you need it. `Connection.backup()` uses SQLite's online
backup API, which takes a consistent snapshot even while the app is running.
This script is normally called before Streamlit starts, so it would usually be
safe either way; doing it properly means it is also safe when it is not.

Every backup is verified before the old ones are pruned. A backup that has
never been read is a guess.

RETENTION
---------
Everything from the last 14 days, then one per week back to 180 days. The
school year is 38 weeks, so that keeps roughly the current term at full
resolution and the rest of the year in outline, in about 30 files.

USAGE
-----
    python backup_db.py                     # uses the default destination
    set FLOKUS_BACKUP_DIR=G:\somewhere\else # to override it
    python backup_db.py --dry-run           # show what would happen

Exit codes: 0 backed up, 2 nothing to do, 1 failed. The launcher warns on a
non-zero code and starts the school day anyway -- a missing backup drive is a
problem for this evening, not a reason to lose a school morning.
"""

import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB = HERE / "flokus.db"

# Google Drive for desktop mounts at G:\My Drive by default. Override with
# FLOKUS_BACKUP_DIR if yours is elsewhere, or to point at a second destination.
DEFAULT_DEST = r"G:\My Drive\Flokus_Backups\Academy"

KEEP_ALL_DAYS = 14       # every backup inside this window survives
KEEP_WEEKLY_DAYS = 180   # beyond it, keep the newest of each week
PREFIX = "flokus_"
STAMP = "%Y-%m-%d_%H%M"


def log(msg):
    print(f"  {msg}")


def parse_stamp(path):
    """The timestamp encoded in a backup's filename, or None if it isn't one."""
    name = path.stem
    if not name.startswith(PREFIX):
        return None
    try:
        return datetime.strptime(name[len(PREFIX):], STAMP)
    except ValueError:
        return None


def existing_backups(dest):
    found = []
    for p in dest.glob(f"{PREFIX}*.db"):
        when = parse_stamp(p)
        if when:
            found.append((when, p))
    return sorted(found, reverse=True)


def to_prune(backups, now):
    """
    Everything inside KEEP_ALL_DAYS survives. Past that, the newest backup of
    each ISO week survives and the rest go. Past KEEP_WEEKLY_DAYS, none survive.

    Written as "which ones go" rather than "which ones stay" on purpose -- the
    dangerous bug in a pruner is one that deletes something it meant to keep,
    and this way the keep-set is never implied.
    """
    doomed = []
    weeks_seen = set()
    for when, path in backups:                     # newest first
        age = (now - when).days
        if age <= KEEP_ALL_DAYS:
            continue
        if age > KEEP_WEEKLY_DAYS:
            doomed.append(path)
            continue
        week = when.isocalendar()[:2]
        if week in weeks_seen:
            doomed.append(path)
        else:
            weeks_seen.add(week)
    return doomed


def verify(path, expected_rows):
    """Open the backup and prove it is readable and complete before trusting it."""
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        result = con.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            return f"integrity_check said {result!r}"
        rows = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if rows != expected_rows:
            return f"{rows} assignments in the backup, {expected_rows} in the live file"
    finally:
        con.close()
    return None


def main():
    dry_run = "--dry-run" in sys.argv
    dest = Path(os.environ.get("FLOKUS_BACKUP_DIR", DEFAULT_DEST))

    print("Flokus Academy - database backup")

    if not DB.exists():
        log(f"FAILED: no database at {DB}")
        return 1

    # A missing drive letter and a missing folder are different problems, and
    # the message should say which. The folder we can create; the drive we can't.
    anchor = Path(dest.anchor)
    if str(anchor) and not anchor.exists():
        log(f"FAILED: {anchor} is not available -- is Google Drive running?")
        log(f"        (destination was {dest})")
        return 1

    try:
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        live_rows = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    except sqlite3.Error as e:
        log(f"FAILED: cannot read the live database -- {e}")
        return 1

    out = dest / f"{PREFIX}{datetime.now().strftime(STAMP)}.db"

    if dry_run:
        log(f"would write {out}")
        for p in to_prune(existing_backups(dest) if dest.exists() else [], datetime.now()):
            log(f"would prune {p.name}")
        con.close()
        return 2

    try:
        dest.mkdir(parents=True, exist_ok=True)
        target = sqlite3.connect(out)
        with target:
            con.backup(target)          # online backup API - safe with the app open
        target.close()
    except (OSError, sqlite3.Error) as e:
        log(f"FAILED: {e}")
        return 1
    finally:
        con.close()

    problem = verify(out, live_rows)
    if problem:
        log(f"FAILED verification: {problem}")
        log(f"        the bad copy is at {out} -- old backups were NOT pruned")
        return 1

    size_kb = out.stat().st_size // 1024
    log(f"wrote {out.name} ({size_kb} KB, {live_rows} assignments) to {dest}")

    # Pruning happens only after a verified good backup exists, so a bad run
    # can never be the thing that removes the last good copy.
    pruned = 0
    for path in to_prune(existing_backups(dest), datetime.now()):
        try:
            path.unlink()
            pruned += 1
        except OSError as e:
            log(f"could not prune {path.name}: {e}")
    kept = len(existing_backups(dest))
    log(f"{kept} backups kept" + (f", {pruned} pruned" if pruned else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
