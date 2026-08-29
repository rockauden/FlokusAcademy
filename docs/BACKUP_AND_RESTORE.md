# Backing up the school database, and proving the backup works

**The one rule: a backup you have never restored is a guess, not a backup.**
Everything below is written so that running the restore drill once, before the
school year starts, is a twenty-minute job rather than something you put off.

The database holds every completion, the XP ledger, the consent records, the
safety events and the UFA expenses. None of it can be regenerated, and it is
the compliance record for the scholarship. It is also the only part of Flokus
Academy that is not already on GitHub — code is backed up by pushing; a
database is not, deliberately, because a database does not belong in version
control.

---

## One-time setup

### 0. Find out what version Railway is running — do this first

`pg_dump` refuses to dump from a server newer than itself. So check the server
before you download a client, or you may install the wrong one and have to do
it twice.

In Railway, open the **FlokusAcademy** service, go to the **Console** tab, and
run:

```
python -c "import asyncio;from sqlalchemy import text;from app.database import async_session_maker,engine;asyncio.run((lambda: None)()) if 0 else None"
```

Simpler — in the **Postgres** service, open its **Data** or **Connect** tab and
read the version there. Or from the Console of the API service:

```
python - <<'EOF'
import asyncio
from sqlalchemy import text
from app.database import async_session_maker, engine
async def main():
    async with async_session_maker() as s:
        print((await s.execute(text("SHOW server_version"))).scalar())
    await engine.dispose()
asyncio.run(main())
EOF
```

Note the major number (the part before the first dot). Install a client that is
**that version or newer**. A newer client reading an older server is fine; the
reverse is not.

### 1. Install PostgreSQL's client tools

The backup script drives three programs: `pg_dump`, `pg_restore` and `psql`.
They come with PostgreSQL, but you do **not** need to run a database server on
your laptop to have them.

On Windows, use the EnterpriseDB installer from postgresql.org. During setup,
untick **PostgreSQL Server** and **Stack Builder**, and keep only **Command
Line Tools**. That installs the three programs and nothing else.

Check it worked — open a new terminal (a new one; PATH changes do not reach
windows that are already open) and run:

```
pg_dump --version
```

If that prints a version number you are done. If it says the command is not
recognised, the install directory is not on your PATH; it is usually
`C:\Program Files\PostgreSQL\17\bin`.

> **Version matters in one direction.** `pg_dump` will refuse to dump from a
> server newer than itself, and says so plainly if it happens. Installing the
> latest client version avoids the problem entirely — a newer client reading an
> older server is fine.

### 2. Find the database URL

In Railway, open the **Postgres** service → **Variables** tab. You want
`DATABASE_PUBLIC_URL`, not `DATABASE_URL`.

The difference matters: `DATABASE_URL` uses a `.railway.internal` hostname that
only resolves from inside Railway's own network, so it will simply fail to
connect from your laptop. The public one goes through `proxy.rlwy.net` and
works from anywhere.

It looks like `postgresql://postgres:LONGPASSWORD@shinkansen.proxy.rlwy.net:34567/railway`.

**Treat it as a password**, because it contains one. Do not paste it into a
chat, a commit, or a file inside the repo.

### 3. Make a one-line script to run it

Create `backup-flokus.bat` somewhere outside the repo — your Documents folder
is fine:

```bat
@echo off
set DATABASE_URL=postgresql://postgres:LONGPASSWORD@shinkansen.proxy.rlwy.net:34567/railway
set FLOKUS_BACKUP_DIR=G:\My Drive\Flokus_Backups\Academy_V2
cd /d D:\dev\flokus-academy\backend
.venv\Scripts\python.exe -m scripts.backup_db
```

Outside the repo on purpose: it holds the database password, and a file inside
the repo is one `git add -A` away from being published to GitHub.

Run it once by double-clicking. You should see something like:

```
Flokus Academy - database backup (V2 / Postgres)
  source      shinkansen.proxy.rlwy.net:34567/railway
  destination G:\My Drive\Flokus_Backups\Academy_V2
  created G:\My Drive\Flokus_Backups\Academy_V2
  live database has 143 assignments
  wrote flokus_v2_2026-08-28_2140.dump (0.3 MB)
  verified: 143 assignments readable in the archive
  1 backups kept
```

That last-but-one line is the whole point. It means the script opened the file
it had just written, pulled the assignment rows back out of it, and counted
them against the live database. A dump that was truncated, or taken against the
wrong database, fails there and **nothing gets pruned**.

### 4. Put it on a schedule

Windows Task Scheduler → **Create Basic Task**:

- Name: `Flokus Academy backup`
- Trigger: **Daily**, at a time the laptop is normally on — 8pm is better than
  3am, because a machine that is asleep does not run tasks.
- Action: **Start a program** → browse to `backup-flokus.bat`

Then open the task's properties and tick **Run task as soon as possible after a
scheduled start is missed**, so a night the laptop was off is caught up the
next day rather than silently skipped.

**Check it a week later.** Open the Google Drive folder and count the files.
This is the step everyone skips, and it is the one that catches a backup that
has been quietly failing since day two.

---

## The restore drill — do this once, before the school year

Restoring is the half nobody practises, which is why it is the half that goes
wrong. This takes about twenty minutes and it never touches production.

### 1. Make a scratch database to restore into

In Railway, in any project, click **New** → **Database** → **Add PostgreSQL**.
You now have a second, empty Postgres. Copy its `DATABASE_PUBLIC_URL`.

Using Railway rather than a local server is deliberate: it exercises the same
network path, the same Postgres version and the same permissions model as the
real thing, so a problem shows up here rather than on the day it matters.

### 2. Restore the newest backup into it

In a terminal, with `SCRATCH_URL` being the new database's public URL:

```
pg_restore --no-owner --no-privileges --dbname "SCRATCH_URL" "G:\My Drive\Flokus_Backups\Academy_V2\flokus_v2_2026-08-28_2140.dump"
```

`--no-owner` and `--no-privileges` tell it not to try to recreate the Railway
role names from the original database, which will not exist in the new one.
Without them you get a wall of harmless-looking permission errors.

### 3. Prove it is really there

```
psql "SCRATCH_URL" -c "SELECT COUNT(*) FROM assignments;"
psql "SCRATCH_URL" -c "SELECT COUNT(*) FROM xp_ledger;"
psql "SCRATCH_URL" -c "SELECT username, role FROM users;"
psql "SCRATCH_URL" -c "SELECT version_num FROM alembic_version;"
```

What you are checking:

- the assignment count matches what the backup script reported
- the XP ledger came across (the balance is the sum of these rows)
- both accounts are there
- **`alembic_version` matches what `/health/ready` reports** — this is the one
  people miss. A restored database whose migration state disagrees with the
  running code fails in confusing ways later.

### 4. Write down what you did

Add the date to the bottom of this file. "Restored successfully on
2026-08-29, 143 assignments, revision e5a2b8d17c40." That line is the
difference between having a backup and believing you have one.

### 5. Delete the scratch database

Railway bills for it. Delete the service when the drill is done.

---

## If the worst happens

Railway loses the database, or something deletes a year of work.

1. **Stop the app first** so nothing writes while you work — in Railway, pause
   the backend service. A restore racing a live app produces a mess that is
   harder to diagnose than the original problem.
2. Create a fresh Postgres service and restore the newest good dump into it,
   exactly as in the drill above.
3. Point the backend's `DATABASE_URL` at the new database and start it.
4. Check `/health/ready` reports the revision you expect.
5. Sign in and look at a week you know the shape of.

**How much would you lose?** At most one day, since the schedule is daily —
whatever happened between the last backup and the failure. If that is ever too
much, move the schedule to twice daily; the script and the retention policy
handle it without changes.

---

## Has any of this been tested?

The script and the restore procedure were exercised end to end on 2026-08-29
against a real PostgreSQL 16 server — not against production, and not by
reading the code:

- a database built by the real migration chain, seeded, and loaded with 23
  assignments; backup written and verified
- restored into a separate empty database with the exact `pg_restore` command
  in this document: 23 assignments, both accounts, revision `e5a2b8d17c40`,
  and the row-level-security policies intact after the restore
- verification refuses a truncated archive, a non-archive, a zero-byte file,
  and an archive whose row count disagrees with the live database
- the retention rule keeps 39 files in steady state after a year of daily
  backups: every one of the last 14 days, then one per week

What that does **not** prove is anything about *your* Railway database, your
Google Drive path, or your Postgres client version. That is what the drill
below is for. The script working is a precondition; your backup working is the
thing.

## Restore drill log

*Append a line each time you actually perform a restore. An empty list below
means the backups are still unproven.*

**2026-08-29** — first real backup and first restore, both performed.

Backup: `flokus_v2_2026-08-29_1308.dump` (0.1 MB), taken through a
`railway connect Postgres --tunnel-only` tunnel rather than over public
access. Live database reported 11 assignments; the script verified 11 readable
inside the archive before pruning.

Restore: into a `restore_test` database on the same server, with
`pg_restore --no-owner --no-privileges`. Verified 11 assignments, both accounts
(`dad`/teacher, `sonny`/student), and `alembic_version` = `e5a2b8d17c40`,
matching what `/health/ready` reports for production.

Two deviations from the procedure above, both deliberate:

- **The tunnel, not public access.** Railway's `railway connect --tunnel-only`
  prints a local host/port and holds an encrypted tunnel open, so the database
  never needs a public endpoint. This is better than what this document
  originally described and is now the recommended route. It does mean the
  connection details are different every time, which is why the `.bat` file no
  longer contains a database URL.
- **A second database on the same server, not a second service.** Cheaper and
  quicker, and it proves what matters: the archive is readable, the data is
  complete, the schema and migration state restore. What it does *not* exercise
  is restoring onto a brand-new server. `pg_restore` behaves the same either
  way, but if you ever want the fuller rehearsal, add a second Postgres service
  and restore into that.

**Known limitation of this arrangement:** the tunnel requires a logged-in
Railway CLI session, so this backup cannot run unattended from Task Scheduler
the way V1's did. It is a manual step. The plan is to run it each Sunday
alongside planning the week — an existing habit, which is the only kind that
survives. **A ritual that lapses is the main risk to this backup now**, not
anything technical. If several weeks pass with no new file in the Drive folder,
that is the signal to automate it properly or move to Railway's Pro-plan
scheduled backups as a second layer.
