import sqlite3

def run_v2_migration(db_path="flokus_academy.db", script_path="migration_v2.sql"):
    """Executes the V2 database schema migration safely."""
    
    # Read the SQL script
    with open(script_path, 'r') as file:
        migration_sql = file.read()

    # Connect to SQLite
    conn = sqlite3.connect(db_path)
    
    try:
        # executescript() automatically handles committing the entire block 
        # as a single transaction if successful.
        conn.executescript(migration_sql)
        print("Migration successful: V2 schema applied.")
    except sqlite3.Error as e:
        print(f"Migration failed! Rolling back changes. Error: {e}")
        conn.rollback()
    finally:
        conn.close()

# Execute the function
run_v2_migration()