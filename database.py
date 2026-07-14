import sqlite3

def init_db():
    # Connect to database (creates flokus.db if it doesn't exist)
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    
    # --- NEW: Tasks table configuration for tasks, dates, and XP rewards ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            task_date TEXT NOT NULL,
            video_url TEXT,
            xp_reward INTEGER DEFAULT 10,
            is_completed INTEGER DEFAULT 0
        )
    ''')
    
    # --- NEW: Expenses table configuration for UFA financial tracking ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            cost REAL NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    
    # --- NEW: Rewards table configuration for the XP store inventory ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            xp_cost INTEGER NOT NULL
        )
    ''')
    
    # --- NEW: Purchases table configuration for Sonny's buying ledger ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reward_name TEXT NOT NULL,
            xp_cost INTEGER NOT NULL,
            purchase_date TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("🎯 Database flokus.db successfully initialized with all tables!")

if __name__ == "__main__":
    init_db()