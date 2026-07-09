import sqlite3

def initialize_db():
    conn = sqlite3.connect('flokus_academy.db')
    cursor = conn.cursor()
    
    # Using DROP TABLE allows us to cleanly overwrite our V1 database with this V2 schema
    cursor.executescript("""
    DROP TABLE IF EXISTS assignments;
    DROP TABLE IF EXISTS units;
    DROP TABLE IF EXISTS subjects;
    DROP TABLE IF EXISTS users;
    """)

    # --- THE NEW PROFESSIONAL SCHEMA ---
    schema_script = """
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        role TEXT NOT NULL
    );

    CREATE TABLE subjects (
        subject_id INTEGER PRIMARY KEY,
        subject_name TEXT NOT NULL,
        platform TEXT
    );

    CREATE TABLE units (
        unit_id INTEGER PRIMARY KEY,
        subject_id INTEGER,
        unit_name TEXT NOT NULL,
        FOREIGN KEY(subject_id) REFERENCES subjects(subject_id)
    );

    CREATE TABLE assignments (
        assignment_id INTEGER PRIMARY KEY,
        subject_id INTEGER,
        unit_id INTEGER,
        title TEXT NOT NULL,
        url_link TEXT,
        status TEXT DEFAULT 'pending',
        due_date DATE,
        start_time TIMESTAMP, 
        end_time TIMESTAMP,
        FOREIGN KEY(subject_id) REFERENCES subjects(subject_id),
        FOREIGN KEY(unit_id) REFERENCES units(unit_id)
    );
    """
    
    cursor.executescript(schema_script)

    # --- SEEDING THE DATA ---
    starter_data = """
    INSERT INTO users (user_id, name, role) VALUES (1, 'Admin', 'admin'), (2, 'Sonny', 'student');
    
    -- High Level Subjects
    INSERT INTO subjects (subject_id, subject_name, platform) VALUES 
    (1, 'Math', 'Beast Academy'),
    (2, 'Computer Science', 'Datacamp'),
    (3, 'Critical Thinking', 'Physical Workbooks');

    -- Granular Units for Analytics
    INSERT INTO units (unit_id, subject_id, unit_name) VALUES 
    (1, 1, 'Fractions & Decimals'),
    (2, 1, 'Geometry'),
    (3, 2, 'Python Fundamentals'),
    (4, 2, 'Data Pipelines'),
    (5, 3, 'Formal Logic & Fallacies');
    """
    
    cursor.executescript(starter_data)
    conn.commit()
    conn.close()
    
    print("Flokus Academy Database v2.0 initialized successfully!")

if __name__ == "__main__":
    initialize_db()