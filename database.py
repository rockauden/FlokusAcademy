import sqlite3

conn = sqlite3.connect('flokus.db')
cursor = conn.cursor()

# 1. Tasks Table (Already exists)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        task_date TEXT NOT NULL,
        video_url TEXT, 
        xp_reward INTEGER NOT NULL DEFAULT 10,
        is_completed BOOLEAN NOT NULL DEFAULT 0
    )
""")

# 2. Expenses Table (Already exists)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        cost REAL NOT NULL,
        category TEXT NOT NULL,
        status TEXT NOT NULL
    )
""")

# --- NEW: The Store Inventory Table ---
cursor.execute("""
    CREATE TABLE IF NOT EXISTS rewards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        xp_cost INTEGER NOT NULL
    )
""")

# --- NEW: The Receipt Book (Purchases) Table ---
cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reward_name TEXT NOT NULL,
        xp_cost INTEGER NOT NULL,
        purchase_date TEXT NOT NULL
    )
""")

conn.commit()
conn.close()

print("Database checked and Store tables created successfully!")