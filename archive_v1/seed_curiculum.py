import sqlite3

# --- Your exact dictionary ---
sonny_curriculum_data = {
    "Core Academics": {
        "Mathematics": {
            "platform": "Beast Academy",
            "focus": "Advanced problem-solving & conceptual depth",
            "status": "Active (Mon-Thurs)",
            "badge_color": "green",
            "login_url": "https://beastacademy.com/"
        },
        "Language Arts": {
            "platform": "Brave Writer / Miacademy",
            "focus": "Literature comprehension, expression, and mechanics",
            "status": "Active (Mon-Thurs)",
            "badge_color": "green",
            "login_url": "https://miacademy.com/"
        },
        "Science & Social Studies": {
            "platform": "Miacademy / Outschool",
            "focus": "State benchmarks & specialized live classes",
            "status": "Active (Mon-Thurs)",
            "badge_color": "green",
            "login_url": "https://outschool.com/"
        }
    },
    "Cognitive & Logic": {
        "Strategic Thinking": {
            "platform": "Synthesis Tutor",
            "focus": "Mental models and complex decision-making",
            "status": "Active (Mon-Thurs)",
            "badge_color": "purple",
            "login_url": "https://www.synthesis.com/tutor"
        }
    },
    "Applied STEM": {
        "Software Engineering": {
            "platform": "Tech Tails",
            "focus": "1-on-1 Game Design, Minecraft Modding, and Coding",
            "status": "Active (Mon-Thurs)",
            "badge_color": "orange",
            "login_url": "https://techtails.com/"
        },
        "Hardware Engineering": {
            "platform": "Physical Robotics Kits",
            "focus": "Tactile builds, electronics, and circuitry (Mars Rover)",
            "status": "Weekend Flex (Fri-Sun)",
            "badge_color": "blue",
            "login_url": None
        }
    },
    "Assessments & Milestones": {
        "State Evaluations": {
            "platform": "NWEA MAP Growth",
            "focus": "Baseline and end-of-year scholarship compliance tracking",
            "status": "Milestone Pending (August / May)",
            "badge_color": "grey",
            "login_url": "https://homeschoolboss.com/"
        }
    }
}

def seed_database():
    print("Connecting to database...")
    conn = sqlite3.connect('flokus_academy.db')
    cursor = conn.cursor()

    # 1. Drop the old subjects table and create the new one with your updated columns
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

    # 2. Loop through your dictionary and insert the data into the database
    for pillar_name, subjects in sonny_curriculum_data.items():
        for subject_name, details in subjects.items():
            cursor.execute("""
                INSERT INTO subjects 
                (pillar, subject_name, platform, focus, schedule_status, badge_color, login_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                pillar_name,
                subject_name,
                details['platform'],
                details['focus'],
                details['status'],
                details['badge_color'],
                details['login_url']
            ))

    # 3. Save changes and close
    conn.commit()
    conn.close()
    print("Success! Sonny's 4 Pillars have been loaded into the database.")

if __name__ == '__main__':
    seed_database()