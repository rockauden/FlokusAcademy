"""
Beast Academy Level 3 — the curriculum that fills the December-to-May math gap.

WHY THIS FILE EXISTS
--------------------
v1 front-loaded all 60 Beast Academy Level 2 lessons into the first fifteen
weeks. That acceleration is deliberate: Level 2 is a foundations catch-up and
the point is to get through it fast. The defect was that nothing was authored
to follow it, so from late November onward Sonny's only math was the Friday
review routine.

Level 3 is authored here and appended to the Beast stream, so math runs
continuously from the first day to the last.

CHAPTER TITLES ARE VERIFIED. The four books and their unit topics come from
Art of Problem Solving's own Level 3 pages (beastacademy.com/books/level-3),
cross-checked against Rainbow Resource's listing:

    3A  Shapes · Skip-Counting · Perimeter and Area
    3B  Multiplication · Perfect Squares · The Distributive Property
    3C  Variables · Division · Measurement
    3D  Fractions · Estimation · Area

THE WITHIN-CHAPTER SPLIT IS A PACING ESTIMATE, NOT PUBLISHER STRUCTURE.
Each chapter is laid out as three Guide-reading sittings, each followed by its
matching Practice sitting -- six tasks per chapter, about a week and a half at
four math days a week. That mirrors exactly how the Level 2 units are already
modelled in this database, and it is the shape Beast Academy is actually used
in. But the real Guide chapters do not divide into neat thirds, so once the
books are in hand these should be re-cut against the actual section breaks.
Renaming a task does not move it; the dates hold.
"""

# (book, chapter number, chapter title)
LEVEL3_CHAPTERS = [
    ("3A", 1,  "Shapes"),
    ("3A", 2,  "Skip-Counting"),
    ("3A", 3,  "Perimeter and Area"),
    ("3B", 4,  "Multiplication"),
    ("3B", 5,  "Perfect Squares"),
    ("3B", 6,  "The Distributive Property"),
    ("3C", 7,  "Variables"),
    ("3C", 8,  "Division"),
    ("3C", 9,  "Measurement"),
    ("3D", 10, "Fractions"),
    ("3D", 11, "Estimation"),
    ("3D", 12, "Area"),
]

SITTINGS_PER_CHAPTER = 3        # Guide reading + matching Practice, three times
LESSON_XP = 15
CAPSTONE_XP = 20


def _build():
    tasks = []
    for book, num, title in LEVEL3_CHAPTERS:
        label = f"BA {book} Ch {num} ({title})"
        for part in range(1, SITTINGS_PER_CHAPTER + 1):
            tasks.append({"title": f"{label} — Guide, part {part}",
                          "xp": LESSON_XP})
            tasks.append({"title": f"Practice & Puzzlers ({label} — part {part})",
                          "xp": LESSON_XP})

    # Twelve slots remain between the end of Level 3 and the last school day.
    # They are spent on review and portfolio work rather than new material, so
    # the year closes the way a year should close.
    for title in [
        "Beast Level 3 Comprehensive Review",
        "Practice & Puzzlers (Beast Level 3 Comprehensive Review)",
        "BA 3 Logic & Puzzle Challenges",
        "Practice & Puzzlers (BA 3 Logic & Puzzle Challenges)",
        "Applied Math Projects — Level 3",
        "Practice & Puzzlers (Applied Math Projects — Level 3)",
        "Advanced Mental Math — Level 3",
        "Practice & Puzzlers (Advanced Mental Math — Level 3)",
        "Year-End Math Mastery Assessment",
        "Practice & Puzzlers (Year-End Math Mastery Assessment)",
        "Annual Math Portfolio Presentation",
        "Practice & Puzzlers (Annual Math Portfolio Presentation)",
    ]:
        tasks.append({"title": title, "xp": CAPSTONE_XP})

    return tasks


LEVEL3_TASKS = _build()


# The Level 2 unit was named as though it closed the school year, because when
# it was written it did. It now finishes in early December with Level 3 to
# follow, so "Year-End" and "Annual" are simply false on these eight rows.
# The real year-end capstone lives at the end of Level 3, above.
LEVEL2_CAPSTONE_RENAMES = {
    "Year-End Math Mastery Assessment":
        "Beast Level 2 Mastery Check",
    "Practice & Puzzlers (Year-End Math Mastery Assessment)":
        "Practice & Puzzlers (Beast Level 2 Mastery Check)",
    "Student Individual Math Project":
        "Level 2 Individual Math Project",
    "Practice & Puzzlers (Student Individual Math Project)":
        "Practice & Puzzlers (Level 2 Individual Math Project)",
    "Annual Math Portfolio Presentation":
        "Level 2 Portfolio Check-In",
    "Practice & Puzzlers (Annual Math Portfolio Presentation)":
        "Practice & Puzzlers (Level 2 Portfolio Check-In)",
}


if __name__ == "__main__":
    print(f"{len(LEVEL3_TASKS)} Level 3 tasks "
          f"({len(LEVEL3_CHAPTERS)} chapters x "
          f"{SITTINGS_PER_CHAPTER * 2} + 12 capstone)")
    for t in LEVEL3_TASKS:
        print(f"  {t['xp']:>3} XP  {t['title']}")
