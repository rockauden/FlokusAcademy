import sqlite3

def seed_odyssey_purchases():
    # Connect to your existing local database
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()

    # --- NEW: Odyssey Receipt Data Mapping ---
    # Format: (item_name, cost, category, status)
    new_expenses = [
        ("Beast Academy Level 2 Bundle", 170.00, "Curriculum & Workbooks", "Approved & Direct Paid"),
        ("Free Market Rules: Economics Curriculum", 126.00, "Curriculum & Workbooks", "Approved & Direct Paid"),
        ("Americas History Bundle (Volumes 1-3)", 179.98, "Curriculum & Workbooks", "Approved & Direct Paid"),
        ("Annual Build Box Subscription", 329.40, "Supplies & Materials", "Approved & Direct Paid"),
        ("GoChess Lite Modern Interactive Chess", 309.90, "Supplies & Materials", "Approved & Direct Paid"),
        ("The Basics of Critical Thinking", 30.99, "Curriculum & Workbooks", "Approved & Direct Paid"),
        ("Emerging Writers Bundle Three", 247.00, "Curriculum & Workbooks", "Approved & Direct Paid")
    ]
    
    # Bulk insert all items into the expenses table
    cursor.executemany("""
        INSERT INTO expenses (item_name, cost, category, status) 
        VALUES (?, ?, ?, ?)
    """, new_expenses)

    # Save changes and close the connection
    conn.commit()
    conn.close()
    
    print("✅ Odyssey funds successfully injected into flokus.db!")

if __name__ == "__main__":
    seed_odyssey_purchases()