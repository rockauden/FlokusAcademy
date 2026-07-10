-- 1. Enforce foreign key constraints (required for SQLite)
PRAGMA foreign_keys = ON;

-- 2. Create the new units table
CREATE TABLE IF NOT EXISTS units (
    unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    unit_name TEXT NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE
);

-- 3. Create the updated assignments table (v2)
CREATE TABLE IF NOT EXISTS new_assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    unit_id INTEGER,
    title TEXT NOT NULL,
    url_link TEXT,
    status TEXT DEFAULT 'pending',
    due_date DATE,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE,
    FOREIGN KEY (unit_id) REFERENCES units(unit_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS creatures (
    creature_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    stage TEXT DEFAULT 'Egg', -- Egg, Baby, Teen, Adult, etc.
    health INTEGER DEFAULT 100,
    strength INTEGER DEFAULT 1,
    intelligence INTEGER DEFAULT 1,
    agility INTEGER DEFAULT 1,
    total_xp_invested INTEGER DEFAULT 0,
    last_interaction TIMESTAMP
);

-- 4. Copy existing data from the old table into the new one
-- (We map the existing columns and leave the new columns as NULL for now)
INSERT INTO new_assignments (
    assignment_id, 
    subject_id, 
    title, 
    url_link, 
    status, 
    due_date
)
SELECT 
    assignment_id, 
    subject_id, 
    title, 
    url_link, 
    status, 
    due_date
FROM assignments;

-- 5. Drop the old table
DROP TABLE assignments;

-- 6. Rename the new table to replace the old one
ALTER TABLE new_assignments RENAME TO assignments;