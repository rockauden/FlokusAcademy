import sqlite3

def view_data():
    # Connect to the database you just made
    conn = sqlite3.connect('flokus_academy.db')
    cursor = conn.cursor()
    
    # Run a SQL SELECT query to get all users
    print("--- Flokus Academy Users ---")
    cursor.execute("SELECT * FROM users;")
    
    # Fetch all the results and print them one by one
    users = cursor.fetchall()
    for user in users:
        print(user)
        
    # Run another query to see the subjects
    print("\n--- Enrolled Subjects ---")
    cursor.execute("SELECT * FROM subjects;")
    
    subjects = cursor.fetchall()
    for subject in subjects:
        print(subject)

    # Close the connection
    conn.close()

if __name__ == "__main__":
    view_data()