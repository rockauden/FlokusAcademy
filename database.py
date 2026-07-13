import sqlite3

conn = sqlite3.connect('flokus.db')
cursor = conn.cursor()

# 1. The Tasks Table (Already exists, but safe to keep here)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        is_completed BOOLEAN NOT NULL DEFAULT 0
    )
""")

# 2. NEW: The Expenses Table for the UFA Tracker
cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        cost REAL NOT NULL,
        category TEXT NOT NULL,
        status TEXT NOT NULL
    )
""")

conn.commit()
conn.close()

print("Database checked and Expenses table created successfully!")