import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "flokus_academy.db")

def setup_core_curriculum():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Clear out old subjects and units to start fresh and clean
    # (If you have active assignments tied to these, they will remain but their subject definitions will update)
    cursor.execute("DROP TABLE IF EXISTS units;")
    cursor.execute("DROP TABLE IF EXISTS subjects;")
    
    # 2. Re-create the tables cleanly
    cursor.execute("""
        CREATE TABLE subjects (
            subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pillar TEXT NOT NULL,
            subject_name TEXT NOT NULL
        );
    """)
    
    cursor.execute("""
        CREATE TABLE units (
            unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            unit_name TEXT NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES subjects (subject_id)
        );
    """)
    
    # 3. Insert the exact core subjects that map to our Utah auto-mapper
    core_subjects = [
        ("Core Academics", "Language Arts"),
        ("Core Academics", "Mathematics"),
        ("Core Academics", "Science"),
        ("Core Academics", "Social Studies"),
        ("Applied STEM", "Applied STEM")
    ]
    
    cursor.executemany("INSERT INTO subjects (pillar, subject_name) VALUES (?, ?);", core_subjects)
    conn.commit()
    
    # Fetch the generated IDs so we map units to the correct subject rows
    cursor.execute("SELECT subject_id, subject_name FROM subjects;")
    subj_map = {name: id for id, name in cursor.fetchall()}
    
    # 4. Define your actual units, properly categorized!
    # Moving Python and Data Pipelines to Applied STEM, and splitting Science/Social Studies
    units_to_insert = [
        # Language Arts Units
        (subj_map["Language Arts"], "Literature & Creative Writing"),
        (subj_map["Language Arts"], "Grammar & Mechanics"),
        
        # Mathematics Units
        (subj_map["Mathematics"], "Fractions & Decimals"),
        (subj_map["Mathematics"], "Geometry & Measurement"),
        (subj_map["Mathematics"], "Advanced Problem Solving"),
        
        # Science Units (CrunchLabs alignment)
        (subj_map["Science"], "Properties of Matter"),
        (subj_map["Science"], "Forces, Motion & Energy"),
        (subj_map["Science"], "Ecosystems & Earth Systems"),
        
        # Social Studies Units (New specialized pillars)
        (subj_map["Social Studies"], "History & Westward Expansion"),
        (subj_map["Social Studies"], "Civics & The Constitution"),
        (subj_map["Social Studies"], "Financial Literacy & Economics"),
        
        # Applied STEM Units (Moved from Language Arts to their rightful home!)
        (subj_map["Applied STEM"], "Python Fundamentals"),
        (subj_map["Applied STEM"], "Data Pipelines & Architecture"),
        (subj_map["Applied STEM"], "Formal Logic & Fallacies")
    ]
    
    cursor.executemany("INSERT INTO units (subject_id, unit_name) VALUES (?, ?);", units_to_insert)
    conn.commit()
    conn.close()
    print("🚀 Flokus Academy subjects and units have been successfully re-mapped!")

if __name__ == "__main__":
    setup_core_curriculum()