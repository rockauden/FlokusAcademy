import streamlit as st
import sqlite3

# ==========================================
# DATABASE HELPER FUNCTIONS
# ==========================================

def add_task_to_db(title, category):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (title, category) VALUES (?, ?)", (title, category))
    conn.commit()
    conn.close()

def get_pending_tasks():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, category FROM tasks WHERE is_completed = 0")
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def complete_task(task_id):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET is_completed = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def get_completed_tasks():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, category FROM tasks WHERE is_completed = 1")
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def delete_task(task_id):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def add_expense(item_name, cost, category, status):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO expenses (item_name, cost, category, status) VALUES (?, ?, ?, ?)", 
                   (item_name, cost, category, status))
    conn.commit()
    conn.close()

def get_all_expenses():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_name, cost, category, status FROM expenses")
    expenses = cursor.fetchall()
    conn.close()
    return expenses

def delete_expense(expense_id):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()

# --- NEW: The Dictionary Mapping Categories to URLs ---
PLATFORM_LINKS = {
    "Math (Beast Academy)": "https://beastacademy.com/login",
    "Logic & Cognitive": "https://brilliant.org/login",
    "Language Arts (Brave Writer)": "https://bravewriter.com/",
    "Science": "https://outschool.com/", 
    "Social Studies (Tuttle Twins)": "https://tuttletwins.com/",
    "Applied STEM": "" # Physical projects usually don't need a login!
}

# ==========================================
# STREAMLIT DASHBOARD UI
# ==========================================

st.set_page_config(page_title="Flokus Academy", layout="centered")

st.sidebar.title("Navigation")
user_view = st.sidebar.radio("Who is using the dashboard?", ["Sonny (Student)", "Dad (Admin)"])

# ------------------------------------------
# SONNY'S VIEW
# ------------------------------------------
if user_view == "Sonny (Student)":
    st.title("🎓 Sonny's Daily Hub")
    st.write("Welcome back! Here is your checklist for today.")
    st.divider()
    
    tasks = get_pending_tasks()
    
    if len(tasks) == 0:
        st.success("🎉 No tasks left! You are all caught up!")
    else:
        for task in tasks:
            task_id = task[0]
            task_title = task[1]
            task_category = task[2]
            
            # NEW: Using columns to put the checkbox on the left, and the link on the right!
            col1, col2 = st.columns([0.8, 0.2])
            
            with col1:
                is_checked = st.checkbox(f"**{task_category}**: {task_title}", key=f"task_{task_id}")
            
            with col2:
                # Look up the URL from our dictionary
                url = PLATFORM_LINKS.get(task_category, "")
                # If a URL exists, display a clickable Markdown link
                if url != "":
                    st.markdown(f"[🚀 Launch]({url})")
            
            if is_checked:
                complete_task(task_id)
                st.rerun()

# ------------------------------------------
# ADMIN VIEW
# ------------------------------------------
elif user_view == "Dad (Admin)":
    st.title("⚙️ Admin Dashboard")
    st.write("Welcome to the control center.")
    st.divider()
    
    tab1, tab2, tab3 = st.tabs(["📝 Add Tasks", "🗂️ Completed Portfolio", "💰 UFA Finances"])
    
    with tab1:
        st.subheader("Add a New Task for Sonny")
        with st.form("new_task_form"):
            task_title = st.text_input("Task Description")
            # These must match the dictionary keys exactly!
            task_category = st.selectbox("Subject Category", [
                "Math (Beast Academy)", "Logic & Cognitive", "Language Arts (Brave Writer)", 
                "Science", "Social Studies (Tuttle Twins)", "Applied STEM"
            ])
            submitted = st.form_submit_button("Save Task")
            
            if submitted and task_title != "":
                add_task_to_db(task_title, task_category)
                st.success(f"Added to {task_category}.")
                st.rerun()
                
    with tab2:
        st.subheader("Completed Tasks (Evidence Log)")
        completed_tasks = get_completed_tasks()
        if len(completed_tasks) == 0:
            st.info("No completed tasks yet.")
        else:
            for task in completed_tasks:
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.markdown(f"✅ **{task[2]}**: {task[1]}")
                with col2:
                    if st.button("❌", key=f"del_task_{task[0]}"):
                        delete_task(task[0])
                        st.rerun()

    with tab3:
        st.subheader("Utah Fits All (UFA) Budget Tracker")
        expenses = get_all_expenses()
        total_budget = 4000.00
        total_spent = sum([expense[2] for expense in expenses]) 
        remaining_budget = total_budget - total_spent
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total UFA Grant", f"${total_budget:,.2f}")
        col2.metric("Total Spent", f"${total_spent:,.2f}")
        col3.metric("Remaining Funds", f"${remaining_budget:,.2f}")
        st.divider()
        
        st.write("**Log a New Purchase**")
        with st.form("expense_form"):
            item_name = st.text_input("Item/Service Name")
            cost = st.number_input("Cost ($)", min_value=0.00, format="%.2f")
            category = st.selectbox("Category", [
                "Curriculum & Workbooks", "Technology/Hardware", 
                "Extracurricular/Classes", "Supplies & Materials"
            ])
            status = st.selectbox("Status", [
                "Pending Odyssey Approval", "Approved & Direct Paid", 
                "Reimbursed", "Out of Pocket (Not UFA)"
            ])
            submit_expense = st.form_submit_button("Log Expense")
            if submit_expense and item_name != "":
                add_expense(item_name, cost, category, status)
                st.success("Expense logged successfully!")
                st.rerun()

        st.write("**Expense History**")
        if len(expenses) == 0:
            st.info("No expenses logged yet.")
        else:
            for exp in expenses:
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.markdown(f"**{exp[1]}** | ${exp[2]:.2f} | *{exp[3]}* | 🏷️ {exp[4]}")
                with col2:
                    if st.button("❌", key=f"del_exp_{exp[0]}"):
                        delete_expense(exp[0])
                        st.rerun()