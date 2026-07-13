import sqlite3

def add_first_assignment():
    # 1. Connect to the database
    conn = sqlite3.connect('flokus_academy.db')
    cursor = conn.cursor()
    
    # 2. Write the SQL to insert a new pending assignment
    # We are using subject_id = 1 (Math - Beast Academy)
    insert_task = """
    INSERT INTO assignments (subject_id, title, url_link, status, due_date) 
    VALUES (1, 'Complete Chapter 1 Introduction', 'https://beastacademy.com', 'pending', '2026-07-09');
    """
    
    # 3. Execute and commit the changes
    cursor.execute(insert_task)
    conn.commit()
    conn.close()
    
    print("Success! New assignment added to Flokus Academy.")

if __name__ == "__main__":
    add_first_assignment()