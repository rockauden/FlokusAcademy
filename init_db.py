import sqlite3
import os

# --- Database Setup ---
# This ensures the database is created in the same folder as this script
DB_PATH = os.path.join(os.path.dirname(__file__), "flokus_academy.db")

def init_database():
    print("Initializing Flokus Academy Database Blueprint...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ==========================================
    # 1. CREATE TABLES
    # ==========================================
    print("Building schema...")

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        role TEXT NOT NULL
    );
    """)

    # Subjects Table (UPDATED: 4 Pillars Architecture)
    # We drop it first to ensure the new columns are created safely
    cursor.execute("DROP TABLE IF EXISTS subjects;")
    cursor.execute("""
    CREATE TABLE subjects (
        subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
        pillar TEXT NOT NULL,
        subject_name TEXT NOT NULL,
        platform TEXT NOT NULL,
        focus TEXT,
        schedule_status TEXT,
        badge_color TEXT,
        login_url TEXT
    );
    """)

    # Units Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS units (
        unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER,
        unit_name TEXT NOT NULL,
        FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
    );
    """)

    # Assignments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER,
        unit_id INTEGER,
        title TEXT NOT NULL,
        url_link TEXT,
        status TEXT DEFAULT 'pending',
        due_date DATE,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
        FOREIGN KEY (unit_id) REFERENCES units(unit_id)
    );
    """)

    # Creatures Table (For the Bestiary)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS creatures (
        creature_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        stage TEXT DEFAULT 'Mystic Egg',
        health INTEGER DEFAULT 100,
        strength INTEGER DEFAULT 1,
        intelligence INTEGER DEFAULT 1,
        agility INTEGER DEFAULT 1,
        total_xp_invested INTEGER DEFAULT 0,
        last_interaction TIMESTAMP
    );
    """)

    # ==========================================
    # 2. INSERT STARTER DATA
    # ==========================================
    print("Inserting 5th Grade Curriculum and User data...")

    # Insert Default Users
    cursor.execute("INSERT OR IGNORE INTO users (username, role) VALUES ('Sonny', 'student')")
    cursor.execute("INSERT OR IGNORE INTO users (username, role) VALUES ('Admin', 'admin')")

    # Insert the 4 Pillars Curriculum Data
    starter_subjects = [
        # Core Academics
        ('Core Academics', 'Mathematics', 'Beast Academy', 'Advanced problem-solving & conceptual depth', 'Active (Mon-Thurs)', 'green', 'https://beastacademy.com/'),
        ('Core Academics', 'Language Arts', 'Brave Writer / Miacademy', 'Literature comprehension, expression, and mechanics', 'Active (Mon-Thurs)', 'green', 'https://miacademy.com/'),
        ('Core Academics', 'Science & Social Studies', 'Miacademy / Outschool', 'State benchmarks & specialized live classes', 'Active (Mon-Thurs)', 'green', 'https://outschool.com/'),

        # Cognitive & Logic
        ('Cognitive & Logic', 'Strategic Thinking', 'Synthesis Tutor', 'Mental models and complex decision-making', 'Active (Mon-Thurs)', 'purple', 'https://www.synthesis.com/tutor'),

        # Applied STEM
        ('Applied STEM', 'Software Engineering', 'Tech Tails', '1-on-1 Game Design, Minecraft Modding, and Coding', 'Active (Mon-Thurs)', 'orange', 'https://techtails.com/'),
        ('Applied STEM', 'Hardware Engineering', 'Physical Robotics Kits', 'Tactile builds, electronics, and circuitry (Mars Rover)', 'Weekend Flex (Fri-Sun)', 'blue', None),

        # Assessments & Milestones
        ('Assessments & Milestones', 'State Evaluations', 'NWEA MAP Growth', 'Baseline and end-of-year benchmarks', 'Periodic', 'red', None),
        ('Assessments & Milestones', 'Portfolio & Milestones', 'Internal', 'Project-based milestones and skill checklists', 'Ongoing', 'red', None),
    ]

    # Insert starter subjects into subjects table (use parameterized queries)
    cursor.executemany(
        "INSERT INTO subjects (pillar, subject_name, platform, focus, schedule_status, badge_color, login_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
        starter_subjects
    )

    # Finalize
    conn.commit()
    conn.close()
    print("Database initialized: {}".format(DB_PATH))