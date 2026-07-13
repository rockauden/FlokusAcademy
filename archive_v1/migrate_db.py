import sqlite3
import os

# Ensure we are targeting the correct database file
DB_PATH = os.path.join(os.path.dirname(__file__), "flokus_academy.db")

def upgrade_database():
    try:
        # Connect to your existing database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Execute the SQL command to add the new column
        cursor.execute("ALTER TABLE assignments ADD COLUMN standard_tag TEXT;")
        conn.commit()

        print("✅ SUCCESS: 'standard_tag' column successfully added to the assignments table!")

    except sqlite3.OperationalError as e:
        # SQLite throws an error if the column is already there, which makes this script safe to run multiple times
        if "duplicate column name" in str(e).lower():
            print("⚠️ The 'standard_tag' column already exists. You are good to go!")
        else:
            print(f"❌ An error occurred: {e}")

    finally:
        conn.close()

if __name__ == "__main__":
    upgrade_database()