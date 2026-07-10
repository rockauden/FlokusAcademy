import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta, date
from fpdf import FPDF

# --- Database Setup ---
DB_PATH = os.path.join(os.path.dirname(__file__), "flokus_academy.db")

# --- Database Helper Functions ---
def run_query(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql(query, conn, params=params)

def execute_query(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

def generate_custom_report(start_date, end_date):
    # Extract: Query the database using our custom date range
    query = """
        SELECT a.title, s.subject_name, u.unit_name, a.start_time, a.end_time
        FROM assignments a
        JOIN subjects s ON a.subject_id = s.subject_id
        LEFT JOIN units u ON a.unit_id = u.unit_id
        WHERE a.status = 'completed' AND a.end_time >= ? AND a.end_time <= ?
    """
    
    # Format the dates so SQLite understands them (Start of day vs End of day)
    start_str = start_date.strftime("%Y-%m-%d 00:00:00")
    end_str = end_date.strftime("%Y-%m-%d 23:59:59")
    
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(query, conn, params=(start_str, end_str))
    
    if df.empty:
        return "No tasks completed in this date range.", None
        
    # Transform: Time Math
    df['start_time'] = pd.to_datetime(df['start_time'], errors='coerce')
    df['end_time'] = pd.to_datetime(df['end_time'], errors='coerce')
    df['duration'] = df['end_time'] - df['start_time']
    
    total_tasks = len(df)
    total_xp = total_tasks * FLAT_XP_RATE 
    
    total_seconds = df['duration'].sum().total_seconds()
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    total_time_str = f"{int(hours)}h {int(minutes)}m" if pd.notna(total_seconds) else "0h 0m"
    
    # Export 1: Build the Markdown String
    report_md = f"# Flokus Academy - Progress Report\n"
    report_md += f"**Date Range:** {start_date} to {end_date}\n\n"
    report_md += f"## Executive Summary\n"
    report_md += f"* **Tasks Completed:** {total_tasks}\n"
    report_md += f"* **XP Earned:** {total_xp} XP\n"
    report_md += f"* **Total Active Learning Time:** {total_time_str}\n\n"
    report_md += f"## Detailed Breakdown\n"
    
    # Export 2: Build the PDF Document
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Flokus Academy - Progress Report", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, f"Date Range: {start_date} to {end_date}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Executive Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 8, f"Tasks Completed: {total_tasks}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"XP Earned: {total_xp} XP", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Total Time: {total_time_str}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Detailed Breakdown", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    
    for index, row in df.iterrows():
        clean_date = str(row['end_time'])[:10] 
        unit_display = f" ({row['unit_name']})" if pd.notna(row['unit_name']) else ""
        
        task_time_str = ""
        if pd.notna(row['duration']):
            t_seconds = row['duration'].total_seconds()
            t_mins, t_secs = divmod(t_seconds, 60)
            task_time_str = f" | Time: {int(t_mins)}m {int(t_secs)}s"
            
        # Add to Markdown
        report_md += f"* **{row['subject_name']}**{unit_display}: {row['title']} - *{clean_date}*{task_time_str}\n"
        
        # Add to PDF (Cleaning special characters so FPDF doesn't crash)
        pdf_line = f"- {row['subject_name']}{unit_display}: {row['title']} [{clean_date}]{task_time_str}"
        pdf_line = pdf_line.encode('ascii', 'ignore').decode('ascii') 
        pdf.cell(0, 6, pdf_line, new_x="LMARGIN", new_y="NEXT")
        
    # The Fix: Convert the bytearray to bytes for Streamlit
    return report_md, bytes(pdf.output())

# --- UI Layout ---
st.set_page_config(page_title="Flokus Academy Dashboard", page_icon="🎓", layout="wide")
st.title("Flokus Academy Dashboard")

# --- GAMIFICATION ENGINE (Defined first to prevent errors!) ---
FLAT_XP_RATE = 100
XP_PER_LEVEL = 1000

# Calculate total XP safely
try:
    completed_data = run_query("SELECT COUNT(*) as count FROM assignments WHERE status = 'completed'")
    completed_count = completed_data.iloc[0]['count']
except Exception:
    completed_count = 0

total_xp = completed_count * FLAT_XP_RATE
current_level = (total_xp // XP_PER_LEVEL) + 1
xp_into_current_level = total_xp % XP_PER_LEVEL
progress_to_next = xp_into_current_level / XP_PER_LEVEL

# Sidebar Menu
role = st.sidebar.selectbox("Logged in as:", ["Sonny (Student)", "Admin (Dad)"])
st.sidebar.divider()
st.sidebar.subheader(f"🎮 Level {current_level}")
st.sidebar.metric("Total XP", f"{total_xp} XP")
st.sidebar.progress(progress_to_next, text=f"{xp_into_current_level} / {XP_PER_LEVEL} XP to Level {current_level + 1}")

# --- STUDENT VIEW ---
if role == "Sonny (Student)":
    st.header("🎓 Student Portal")
    
    # Create the two tabs for Sonny's view
    student_tab1, student_tab2 = st.tabs(["Active Assignments", "My Courses"])
    
    # --- TAB 1: Assignments (Your existing checklist) ---
    with student_tab1:
        st.subheader("Daily Checklist")
        
        # Fetch pending and in-progress tasks
        tasks = run_query("""
            SELECT a.assignment_id, a.title, a.url_link, a.status, s.subject_name, u.unit_name
            FROM assignments a
            JOIN subjects s ON a.subject_id = s.subject_id
            LEFT JOIN units u ON a.unit_id = u.unit_id
            WHERE a.status IN ('pending', 'in_progress')
        """)
        
        if tasks.empty:
            st.success("All caught up!")
            st.balloons()
        else:
            for _, row in tasks.iterrows():
                unit_display = f" - {row['unit_name']}" if pd.notna(row['unit_name']) else ""
                with st.expander(f"{row['subject_name']}{unit_display}: {row['title']}", expanded=True):
                    st.markdown(f"[Go to Lesson]({row['url_link']})")
                    
                    # Dynamic Button Logic
                    if row['status'] == 'pending':
                        if st.button("▶️ Start Task", key=f"start_{row['assignment_id']}"):
                            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            execute_query(
                                "UPDATE assignments SET status = 'in_progress', start_time = ? WHERE assignment_id = ?",
                                (current_time, row['assignment_id'])
                            )
                            st.rerun()
                            
                    elif row['status'] == 'in_progress':
                        if st.button("✅ Mark as Completed", key=f"complete_{row['assignment_id']}"):
                            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            execute_query(
                                "UPDATE assignments SET status = 'completed', end_time = ? WHERE assignment_id = ?",
                                (current_time, row['assignment_id'])
                            )
                            st.toast(f"Boom! +{FLAT_XP_RATE} XP Earned!", icon="🔥")
                            st.rerun()

    #--- TAB 2: Courses Overview (🗺️ Course Map)
    with student_tab2:
        st.subheader("🗺️ 5th Grade Curriculum Map")
        st.write("Track your subjects, focus goals, and daily schedules across your 4 learning pillars.")

        # Query to fetch all subjects with their pillar information ordered by pillar name
        course_data = run_query("""
            SELECT pillar, subject_name, platform, focus, schedule_status, badge_color, login_url 
            FROM subjects 
            ORDER BY pillar, subject_name
        """)

        if course_data.empty:
            st.info("No curriculum data loaded yet. Run your database seed script.")
        else:
            # Get a unique list of pillars present in the database
            pillars = course_data['pillar'].unique()
            
            # Loop through each Pillar (e.g., Core Academics, Applied STEM)
            for pillar in pillars:
                st.markdown(f"### {pillar}")
                
                # Filter rows that belong to this specific pillar
                pillar_df = course_data[course_data['pillar'] == pillar]
                
                # Display each course inside this pillar
                for _, row in pillar_df.iterrows():
                    # Format the expander title with the subject name and platform
                    expander_label = f"🔹 {row['subject_name']} ({row['platform']})"
                    
                    with st.expander(expander_label):
                        # Display the custom schedule status badge matching your curriculum requirements
                        st.markdown(f"**Schedule/Status:** :{row['badge_color']}[{row['schedule_status']}]")
                        st.markdown(f"**Focus Area:** {row['focus']}")
                        
                        # Render an interactive link button if an external login URL exists
                        if row['login_url']:
                            st.link_button(f"🚀 Launch {row['platform']}", row['login_url'])
                        else:
                            st.caption("📦 Offline Class / Physical Kit (No URL required)")
                
                st.divider()

# --- ADMIN VIEW ---
elif role == "Admin (Dad)":
    tab1, tab2, tab3 = st.tabs(["Admin Controls", "Progress Analytics", "Weekly Reporting"])
    
    with tab1:
        st.subheader("Assign a New Task")
        try:
            units_df = run_query("""
                SELECT u.unit_id, s.pillar || ' ➔ ' || s.subject_name || ' - ' || u.unit_name as full_name, u.subject_id
                FROM units u
                JOIN subjects s ON u.subject_id = s.subject_id
                ORDER BY s.pillar, s.subject_name, u.unit_name
            """)
        except Exception:
            units_df = pd.DataFrame()
        
        with st.form("assign_task_form"):
            if not units_df.empty:
                unit_selection = st.selectbox(
                    "Select Subject & Unit", 
                    options=units_df['unit_id'].tolist(),
                    format_func=lambda x: units_df.loc[units_df['unit_id'] == x, 'full_name'].values[0]
                )
            else:
                st.warning("No units found. Please add them via SQL first.")
                unit_selection = None
                
            title = st.text_input("Task Title")
            url = st.text_input("URL Link")
            
            submitted = st.form_submit_button("Assign Task")
            if submitted and unit_selection:
                subj_id = int(units_df.loc[units_df['unit_id'] == unit_selection, 'subject_id'].values[0])
                execute_query(
                    "INSERT INTO assignments (subject_id, unit_id, title, url_link, status) VALUES (?, ?, ?, ?, 'pending')",
                    (subj_id, unit_selection, title, url)
                )
                st.success("Task assigned successfully!")

    with tab2:
        st.subheader("Analytics Overview")
        completed_tasks = run_query("SELECT * FROM assignments WHERE status = 'completed'")
        st.metric("Total Completed Tasks", len(completed_tasks))

    with tab3:
        st.subheader("Automated Reports")
        st.write("Select a date range to generate a summary of Sonny's work.")
        
        # Create a side-by-side layout for our date pickers
        col1, col2 = st.columns(2)
        with col1:
            start_d = st.date_input("Start Date", date.today() - timedelta(days=7))
        with col2:
            end_d = st.date_input("End Date", date.today())
        
        if st.button("Generate Custom Report"):
            report_md, pdf_bytes = generate_custom_report(start_d, end_d)
            
            st.markdown(report_md)
            
            # If the PDF generated successfully, show the download buttons
            if pdf_bytes:
                st.divider()
                st.write("💾 **Export Options:**")
                btn_col1, btn_col2 = st.columns(2)
                
                with btn_col1:
                    st.download_button(
                        label="📄 Download as Markdown (.md)",
                        data=report_md,
                        file_name=f"Flokus_Report_{start_d}_to_{end_d}.md",
                        mime="text/markdown"
                    )
                with btn_col2:
                    st.download_button(
                        label="📑 Download as PDF (.pdf)",
                        data=pdf_bytes,
                        file_name=f"Flokus_Report_{start_d}_to_{end_d}.pdf",
                        mime="application/pdf"
                    )