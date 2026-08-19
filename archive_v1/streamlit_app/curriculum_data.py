"""
RETIRED 2026-08-18 — this module no longer drives anything.

WHAT IT WAS
-----------
The Tier 1 / Tier 2 master curriculum tables plus `generate_tier_schedule()`,
behind the "1-Click Master Curriculum Batch Scheduler" in the Task Manager. One
click regenerated the whole year -- 677 assignments -- on top of whatever was
already scheduled.

WHY IT IS GONE
--------------
Two problems, and the second is the one that mattered.

It could not be edited without editing code. The actual plan for Sonny's year
lived in Python literals, so changing which chapter came in week 12 meant a
developer, not a parent with a spreadsheet.

And it had no idea what was already there. It appended rather than reconciled,
so firing it twice produced two of everything, and firing it after any hand
edit silently buried that edit under a fresh copy of the default plan.

WHAT REPLACED IT
----------------
    curriculum_io.py    import and export the 21-column spreadsheet format
                        (the same one V2 ingests), idempotent via source_key
    school_year.py      the single definition of which days are school days
    Task Manager        Import Curriculum / Quick Add / Schedule

NOTHING WAS LOST. The year this file used to generate now lives in flokus.db
and exports to Flokus_Curriculum_2026-27_EXPORT.xlsx, which re-imports cleanly.
To change the plan now: export, edit in Excel, import. The file is the source
of truth, and it is a file you can open.

This stub is kept only so that an old import of `curriculum_data` fails loudly
with an explanation rather than a bare ModuleNotFoundError.
"""

RETIRED = True
REPLACED_BY = "curriculum_io.py"


def _retired(*_args, **_kwargs):
    raise RuntimeError(
        "curriculum_data.generate_tier_schedule() was retired on 2026-08-18. "
        "Curriculum is now imported from a spreadsheet -- see curriculum_io.py, "
        "or use Task Manager -> Import Curriculum. The current year exports to "
        "Flokus_Curriculum_2026-27_EXPORT.xlsx and re-imports cleanly."
    )


generate_tier_schedule = _retired
TIER_1_OVERVIEW = {}
TIER_2_UNITS = []
