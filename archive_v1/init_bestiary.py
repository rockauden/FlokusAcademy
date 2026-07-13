def run_query(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql(query, conn, params=params)

import sqlite3

def setup_bestiary(db_path="flokus_academy.db"):
    """Creates the creatures table and inserts the starting Egg."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the new table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS creatures (
            creature_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            stage TEXT DEFAULT 'Mystic Egg',
            strength INTEGER DEFAULT 1,
            intelligence INTEGER DEFAULT 1,
            agility INTEGER DEFAULT 1
        )
    ''')
    
    # Check if a creature already exists; if not, give him his first egg!
    cursor.execute("SELECT COUNT(*) FROM creatures")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO creatures (name) VALUES ('Sonny''s Companion')")
        print("A new Mystic Egg has appeared in the database!")
    else:
        print("Creature table already exists and is populated.")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_bestiary()