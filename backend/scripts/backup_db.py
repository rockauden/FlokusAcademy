r"""
Back up the live school database, off Railway.

(The `r` on this docstring matters: the Windows paths below contain `\M` and
`\F`, which Python reads as invalid escape sequences and warns about on every
run. A raw string takes the backslashes literally. Same reason as V1's
backup_db.py, which this is deliberately modelled on.)

WHY THIS EXISTS
---------------
V2 keeps a year of Sonny's schoolwork in Railway's Postgres: every completion,
the XP ledger, the consent records, the safety events, the UFA expenses. None
of it can be regenerated, and it is also the state compliance record. Until
now there was no backup of it at all -- not in the code, not in railway.toml,
not documented anywhere. V1 had one; moving the school year onto V2 without one
would have been a step backwards in the only dimension that cannot be undone.

Railway may or may not be taking its own snapshots depending on the plan. That
is not a reason to skip this: a backup held by the same vendor as the live
database shares its failure modes, its billing, and its account. This one lands
in Google Drive, where V1's backups already live.

WHY pg_dump RATHER THAN COPYING ANYTHING
-----------------------------------------
There is no file to copy -- the database lives on Railway's machine, not this
one. pg_dump connects as a client and asks for a consistent snapshot, which it
takes inside a single transaction, so a dump taken while the app is serving is
still internally consistent.

The custom format (-Fc) is used rather than plain SQL because it is compressed,
and because pg_restore can read its table of contents without restoring
anything -- which is what makes the verification below cheap enough to run
every time.

Every backup is verified before the old ones are pruned. A backup that has
never been read is a guess. Verification here means three things: pg_restore
can parse the archive, the tables that must exist are in it, and the number of
assignment rows inside the archive matches the number in the live database.
That last one is the real check -- a readable archive of the wrong database, or
of a half-finished dump, fails it.

RETENTION
---------
Everything from the last 14 days, then one per week back to 180 days. Same
policy as V1: roughly the current term at full resolution and the rest of the
year in outline, in about 30 files.

REQUIREMENTS
------------
PostgreSQL's client tools must be installed, so that `pg_dump` and `pg_restore`
are on PATH. On Windows the usual route is the EnterpriseDB installer -- during
setup you can untick "PostgreSQL Server" and keep only "Command Line Tools".
The client version must be the same as, or newer than, the server's; pg_dump
refuses to dump from a newer server and says so.

USAGE
-----
    python -m scripts.backup_db                    # uses the default destination
    set FLOKUS_BACKUP_DIR=G:\somewhere\else        # to override it
    python -m scripts.backup_db --dry-run          # show what would happen

DATABASE_URL must point at the database to back up. Take the *public* URL from
Railway (Postgres service -> Variables -> DATABASE_PUBLIC_URL); the internal
`.railway.internal` hostname only resolves from inside Railway's network.

Exit codes: 0 backed up, 1 failed. A failure is loud on purpose -- a backup
that quietly does nothing is worse than no backup, because you stop checking.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# Google Drive for desktop mounts at G:\My Drive by default. Override with
# FLOKUS_BACKUP_DIR if yours is elsewhere, or to point at a second destination.
DEFAULT_DEST = r"G:\My Drive\Flokus_Backups\Academy_V2"

KEEP_ALL_DAYS = 14       # every backup inside this window survives
KEEP_WEEKLY_DAYS = 180   # beyond it, keep the newest of each week
PREFIX = "flokus_v2_"
SUFFIX = ".dump"
STAMP = "%Y-%m-%d_%H%M"

# Tables the archive must contain. Not the full list on purpose -- these are the
# ones whose absence would mean the dump is of the wrong database or a partial
# schema, and checking a handful is enough to prove that.
REQUIRED_TABLES = ("assignments", "lessons", "xp_ledger", "users", "consent_records")

# The table whose rows are counted on both sides. Assignments are the row that
# matters most: one per piece of work per student, and the thing the compliance
# record is built from.
COUNTED_TABLE = "assignments"


def log(msg):
    print(f"  {msg}")


def libpq_url(raw):
    """Turn the app's SQLAlchemy URL into one libpq tools understand.

    app/config.py rewrites whatever Railway provides into
    `postgresql+asyncpg://...` so SQLAlchemy picks the async driver. pg_dump has
    never heard of asyncpg and refuses the URL outright, so the driver suffix
    comes back off here.
    """
    parts = urlsplit(raw)
    scheme = parts.scheme.split("+", 1)[0]
    if scheme == "postgres":
        scheme = "postgresql"
    return urlunsplit((scheme, parts.netloc, parts.path, parts.query, parts.fragment))


def describe(url):
    """A URL safe to print: host, port and database, never the password."""
    parts = urlsplit(url)
    host = parts.hostname or "?"
    port = f":{parts.port}" if parts.port else ""
    return f"{host}{port}{parts.path}"


def live_row_count(url, table):
    """Count rows in the live database, for comparison against the archive.

    psql is used rather than the application's own SQLAlchemy engine so this
    script depends on nothing but the Postgres client tools it already needs.
    That matters if it is ever run from a machine that has no virtualenv.
    """
    result = subprocess.run(
        ["psql", url, "-tAc", f"SELECT COUNT(*) FROM {table}"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None, result.stderr.strip() or "psql failed"
    try:
        return int(result.stdout.strip()), None
    except ValueError:
        return None, f"unexpected psql output: {result.stdout.strip()!r}"


def parse_stamp(path):
    """The timestamp encoded in a backup's filename, or None if it isn't one."""
    name = path.name
    if not name.startswith(PREFIX) or not name.endswith(SUFFIX):
        return None
    try:
        return datetime.strptime(name[len(PREFIX):-len(SUFFIX)], STAMP)
    except ValueError:
        return None


def existing_backups(dest):
    found = []
    for p in dest.glob(f"{PREFIX}*{SUFFIX}"):
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
    and this way the keep-set is never implied. Lifted from V1's backup_db.py
    unchanged, because it was right there and is right here.
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
    """Read the archive back and prove it is what it claims to be.

    Returns None when the backup is trustworthy, or a sentence explaining why
    it is not. Nothing is pruned unless this returns None.
    """
    listing = subprocess.run(
        ["pg_restore", "--list", str(path)], capture_output=True, text=True,
    )
    if listing.returncode != 0:
        return f"pg_restore could not read the archive: {listing.stderr.strip()[:200]}"

    toc = listing.stdout
    missing = [t for t in REQUIRED_TABLES if f" {t} " not in toc]
    if missing:
        return f"tables missing from the archive: {', '.join(missing)}"

    # The real check: pull the counted table's data back out of the archive and
    # count it. A readable archive of the wrong database passes everything
    # above and fails here.
    data = subprocess.run(
        ["pg_restore", "--data-only", "--table", COUNTED_TABLE, "-f", "-", str(path)],
        capture_output=True, text=True,
    )
    if data.returncode != 0:
        return f"could not read {COUNTED_TABLE} out of the archive: {data.stderr.strip()[:200]}"

    rows = count_copy_rows(data.stdout)
    if rows is None:
        return f"no COPY block for {COUNTED_TABLE} in the archive"
    if expected_rows is not None and rows != expected_rows:
        return f"{rows} {COUNTED_TABLE} in the backup, {expected_rows} in the live database"

    return None


def count_copy_rows(sql):
    """Count the data lines in a pg_restore COPY block.

    pg_restore's data-only output is a COPY statement followed by one
    tab-separated line per row, terminated by a lone backslash-dot.
    """
    lines = sql.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^COPY .* FROM stdin;", line):
            count = 0
            for row in lines[i + 1:]:
                if row == r"\.":
                    return count
                count += 1
            return count       # truncated output; report what was there
    return None


def main():
    parser = argparse.ArgumentParser(description="Back up the Flokus Academy database.")
    parser.add_argument("--dry-run", action="store_true", help="show what would happen")
    args = parser.parse_args()

    print("Flokus Academy - database backup (V2 / Postgres)")

    for tool in ("pg_dump", "pg_restore", "psql"):
        if not shutil.which(tool):
            log(f"FAILED: {tool} is not on PATH.")
            log("Install PostgreSQL's command line tools and try again.")
            log("On Windows: the EnterpriseDB installer, unticking 'PostgreSQL Server'")
            log("so you get only the client tools.")
            return 1

    raw = os.environ.get("DATABASE_URL", "")
    if not raw:
        log("FAILED: DATABASE_URL is not set.")
        log(r"Set it to Railway's DATABASE_PUBLIC_URL, e.g.:")
        log(r'    set DATABASE_URL=postgresql://user:pass@host.proxy.rlwy.net:12345/railway')
        return 1
    if raw.startswith("sqlite"):
        log("FAILED: DATABASE_URL points at SQLite, which this script cannot back up.")
        log("It expects the production Postgres URL.")
        return 1

    url = libpq_url(raw)

    # Check the URL looks like a URL before handing it to psql. Without this,
    # an unedited placeholder or a half-pasted string is passed straight
    # through, and libpq falls back to its default of localhost:5432 -- so the
    # failure reads "connection to server at localhost ... Connection refused",
    # which sends you looking for a broken database instead of a broken
    # variable. Found the first time this script was run for real.
    parts = urlsplit(url)
    if parts.scheme not in ("postgresql", "postgres") or not parts.hostname:
        log("FAILED: DATABASE_URL does not look like a database URL.")
        log(f"        got: {raw[:60]}{'...' if len(raw) > 60 else ''}")
        log("")
        log("It should start with postgresql:// and contain a host, e.g.")
        log("    postgresql://postgres:PASSWORD@shinkansen.proxy.rlwy.net:34567/railway")
        log("")
        log("Copy DATABASE_PUBLIC_URL from Railway's Postgres service ->")
        log("Variables tab. If you are using a .bat file, check the placeholder")
        log("was actually replaced.")
        return 1

    dest = Path(os.environ.get("FLOKUS_BACKUP_DIR", DEFAULT_DEST))
    now = datetime.now()
    out = dest / f"{PREFIX}{now.strftime(STAMP)}{SUFFIX}"

    log(f"source      {describe(url)}")
    log(f"destination {dest}")

    if args.dry_run:
        log(f"would write {out.name}")
        for p in to_prune(existing_backups(dest) if dest.exists() else [], now):
            log(f"would prune {p.name}")
        return 0

    if not dest.exists():
        try:
            dest.mkdir(parents=True)
            log(f"created {dest}")
        except OSError as exc:
            log(f"FAILED: cannot create {dest} -- {exc}")
            log("Is Google Drive running and the drive letter mounted?")
            return 1

    # Counted before the dump, so a row added mid-dump shows up as a mismatch
    # rather than being silently tolerated. A one-row discrepancy on a busy
    # database would be noise; on a one-family database it means something.
    expected, count_error = live_row_count(url, COUNTED_TABLE)
    if count_error:
        log(f"FAILED: could not reach the database -- {count_error[:200]}")
        return 1
    log(f"live database has {expected} {COUNTED_TABLE}")

    dump = subprocess.run(
        ["pg_dump", "--format=custom", "--no-owner", "--no-privileges",
         "--file", str(out), url],
        capture_output=True, text=True,
    )
    if dump.returncode != 0:
        stderr = dump.stderr.strip()
        log(f"FAILED: pg_dump exited {dump.returncode}")
        log(stderr[:400] or "(no output)")
        if "server version" in stderr:
            log("")
            log("That is a version mismatch: your pg_dump is older than Railway's")
            log("server. Install a client at least as new as the server and retry.")
        out.unlink(missing_ok=True)
        return 1

    size_mb = out.stat().st_size / (1024 * 1024)
    log(f"wrote {out.name} ({size_mb:.1f} MB)")

    problem = verify(out, expected)
    if problem:
        log(f"FAILED verification: {problem}")
        log(f"        the bad copy is at {out} -- old backups were NOT pruned")
        return 1
    log(f"verified: {expected} {COUNTED_TABLE} readable in the archive")

    pruned = 0
    for path in to_prune(existing_backups(dest), now):
        path.unlink()
        pruned += 1

    kept = len(existing_backups(dest))
    log(f"{kept} backups kept" + (f", {pruned} pruned" if pruned else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
