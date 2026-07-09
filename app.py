import streamlit as st
import sqlite3
import datetime
import pandas as pd

st.title("🏰 Flokus Academy Dashboard")

def get_assignments():
    conn = sqlite3.connect('flokus_academy.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.assignment_id, s.subject_name, u.unit_name, s.platform, a.title, a.url_link, a.status, a.start_time 
        FROM assignments a
        JOIN subjects s ON a.subject_id = s.subject_id
        JOIN units u ON a.unit_id = u.unit_id
        WHERE a.status IN ('pending', 'in_progress');
    """)
    data = cursor.fetchall()
    conn.close()
    return data

def get_units_for_admin():
    conn = sqlite3.connect('flokus_academy.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.unit_id, s.subject_name, u.unit_name 
        FROM units u
        JOIN subjects s ON u.subject_id = s.subject_id;
    """)
    data = cursor.fetchall()
    conn.close()
    return data

st.sidebar.header("User Profile")
user_role = st.sidebar.selectbox("Logged in as:", ["Sonny (Student)", "Admin (Dad)"])

if "Student" in user_role:
    st.header("📝 Sonny's Daily Tasks")
    tasks = get_assignments()
    
    if not tasks:
        st.success("🎉 All caught up!")
        st.balloons()
    else:
        for task in tasks:
            task_id, subject, unit, platform, title, url, status, start_time = task
            st.subheader(f"{subject}: {unit} ({platform})")
            st.write(f"**Task:** {title}")
            
            if status == 'pending':
                if st.button("▶️ Start Task", key=f"start_{task_id}"):
                    conn = sqlite3.connect('flokus_academy.db')
                    cursor = conn.cursor()
                    cursor.execute("UPDATE assignments SET status = 'in_progress', start_time = CURRENT_TIMESTAMP WHERE assignment_id = ?;", (task_id,))
                    conn.commit()
                    conn.close()
                    st.rerun()
            elif status == 'in_progress':
                if url:
                    st.link_button("Go to Lesson 🚀", url)
                if st.button("✅ Mark as Completed", key=f"comp_{task_id}"):
                    conn = sqlite3.connect('flokus_academy.db')
                    cursor = conn.cursor()
                    cursor.execute("UPDATE assignments SET status = 'completed', end_time = CURRENT_TIMESTAMP WHERE assignment_id = ?;", (task_id,))
                    conn.commit()
                    conn.close()
                    st.rerun()

else:
    st.header("⚙️ Admin Management")
    st.write("Assign new granular tasks:")
    
    units = get_units_for_admin()
    unit_options = {f"{u[1]} - {u[2]}": u[0] for u in units}
    
    with st.form("add_assignment_form"):
        selected_unit = st.selectbox("Select Unit:", options=list(unit_options.keys()))
        task_title = st.text_input("Task Title")
        task_url = st.text_input("Task Link (URL)")
        due_date = st.date_input("Due Date", min_value=datetime.date.today())
        
        if st.form_submit_button("Assign Task"):
            if task_title:
                unit_id = unit_options[selected_unit]
                
                conn = sqlite3.connect('flokus_academy.db')
                cursor = conn.cursor()
                # Get the subject_id mapped to this unit
                cursor.execute("SELECT subject_id FROM units WHERE unit_id = ?", (unit_id,))
                subject_id = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO assignments (subject_id, unit_id, title, url_link, status, due_date) 
                    VALUES (?, ?, ?, ?, 'pending', ?);
                """, (subject_id, unit_id, task_title, task_url, due_date))
                conn.commit()
                conn.close()
                st.success(f"Assigned: {task_title}")