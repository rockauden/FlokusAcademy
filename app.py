import streamlit as st
import sqlite3
from datetime import date

# ==========================================
# DATABASE HELPER FUNCTIONS
# ==========================================

def add_task_to_db(title, category, video_url, xp_reward):
    today_string = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (title, category, task_date, video_url, xp_reward) VALUES (?, ?, ?, ?, ?)", 
                   (title, category, today_string, video_url, xp_reward))
    conn.commit()
    conn.close()

def get_pending_tasks():
    today_string = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, category, video_url, xp_reward FROM tasks WHERE is_completed = 0 AND task_date = ?", (today_string,))
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
    today_string = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, category, video_url, xp_reward FROM tasks WHERE is_completed = 1 AND task_date = ?", (today_string,))
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

def add_reward(name, xp_cost):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO rewards (name, xp_cost) VALUES (?, ?)", (name, xp_cost))
    conn.commit()
    conn.close()

def get_rewards():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, xp_cost FROM rewards")
    rewards = cursor.fetchall()
    conn.close()
    return rewards

def delete_reward(reward_id):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rewards WHERE id = ?", (reward_id,))
    conn.commit()
    conn.close()

def buy_reward(reward_name, xp_cost):
    today_string = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO purchases (reward_name, xp_cost, purchase_date) VALUES (?, ?, ?)", 
                   (reward_name, xp_cost, today_string))
    conn.commit()
    conn.close()

def get_xp_balance():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(xp_reward) FROM tasks WHERE is_completed = 1")
    earned = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(xp_cost) FROM purchases")
    spent = cursor.fetchone()[0] or 0
    conn.close()
    return earned - spent

def get_purchase_history():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT reward_name, xp_cost, purchase_date FROM purchases ORDER BY id DESC")
    purchases = cursor.fetchall()
    conn.close()
    return purchases

PLATFORM_LINKS = {
    "Math (Beast Academy)": "https://beastacademy.com/login",
    "Logic & Cognitive": "https://brilliant.org/login",
    "Language Arts (Brave Writer)": "https://bravewriter.com/",
    "Science": "https://outschool.com/", 
    "Social Studies (Tuttle Twins)": "https://tuttletwins.com/",
    "Applied STEM": "" 
}

# ==========================================
# STREAMLIT DASHBOARD UI
# ==========================================

st.set_page_config(page_title="Flokus Academy", layout="wide")

# --- NEW: Initialize the balloon trigger state ---
if 'show_balloons' not in st.session_state:
    st.session_state.show_balloons = False

st.sidebar.title("Navigation")
user_view = st.sidebar.radio("Who is using the dashboard?", ["Sonny (Student)", "Dad (Admin)"])

# ------------------------------------------
# SONNY'S VIEW
# ------------------------------------------
if user_view == "Sonny (Student)":
    
    # --- NEW: Fire balloons and reset the trigger ---
    if st.session_state.show_balloons:
        st.balloons()
        st.session_state.show_balloons = False

    today_display = date.today().strftime("%A, %b %d")
    st.title(f"🎓 Sonny's Daily Hub - {today_display}")
    
    tab_quests, tab_store = st.tabs(["📋 Daily Quests", "🛍️ Reward Store"])
    
    with tab_quests:
        pending_tasks = get_pending_tasks()
        completed_tasks = get_completed_tasks()
        
        daily_xp = sum([task[4] for task in completed_tasks])
        
        header_col1, header_col2 = st.columns([0.7, 0.3])
        with header_col1:
            total_tasks = len(pending_tasks) + len(completed_tasks)
            if total_tasks > 0:
                progress_decimal = len(completed_tasks) / total_tasks
                progress_percentage = int(progress_decimal * 100)
                st.write(f"**Daily Quest Progress: {progress_percentage}%**")
                st.progress(progress_decimal)
        with header_col2:
            st.metric(label="🏆 XP Earned Today", value=daily_xp)
        
        st.divider()
        
        col_todo, col_done = st.columns(2)
        
        with col_todo:
            st.subheader("📝 Up Next")
            if len(pending_tasks) == 0:
                st.success("🎉 All caught up!")
            else:
                for task in pending_tasks:
                    task_id, task_title, task_category, task_video_url, task_xp = task
                    
                    inner_col1, inner_col2 = st.columns([0.8, 0.2])
                    with inner_col1:
                        is_checked = st.checkbox(f"**{task_category}**: {task_title} (💎 {task_xp} XP)", key=f"task_{task_id}")
                    with inner_col2:
                        url = PLATFORM_LINKS.get(task_category, "")
                        if url != "":
                            st.markdown(f"[🚀 Launch]({url})")
                    
                    if task_video_url:
                        with st.expander("📺 Watch Lesson Video"):
                            st.video(task_video_url)
                    
                    st.write("") 
                    
                    if is_checked:
                        complete_task(task_id)
                        # --- NEW: Set trigger to True before refreshing ---
                        st.session_state.show_balloons = True
                        st.rerun()

        with col_done:
            st.subheader("✅ Completed Today")
            if len(completed_tasks) == 0:
                st.info("Nothing completed yet. Time to get to work!")
            else:
                for task in completed_tasks:
                    task_title = task[1]
                    task_category = task[2]
                    task_xp = task[4] 
                    st.success(f"**{task_category}**: {task_title} (💎 {task_xp} XP)")

    with tab_store:
        st.subheader("Welcome to the XP Store!")
        
        bank_balance = get_xp_balance()
        st.metric(label="🏦 Total XP Bank (Available to Spend)", value=bank_balance)
        st.divider()
        
        rewards = get_rewards()
        if len(rewards) == 0:
            st.info("The store is currently empty. Dad needs to stock the shelves!")
        else:
            cols = st.columns(3)
            for index, reward in enumerate(rewards):
                reward_name = reward[1]
                reward_cost = reward[2]
                
                with cols[index % 3]:
                    st.markdown(f"### {reward_name}")
                    st.write(f"**Cost:** 💎 {reward_cost} XP")
                    
                    if st.button("Buy", key=f"buy_{reward[0]}"):
                        if bank_balance >= reward_cost:
                            buy_reward(reward_name, reward_cost)
                            st.success(f"Successfully bought {reward_name}!")
                            st.rerun()
                        else:
                            st.error(f"Not enough XP! You need {reward_cost - bank_balance} more.")

# ------------------------------------------
# ADMIN VIEW
# ------------------------------------------
elif user_view == "Dad (Admin)":
    st.title("⚙️ Admin Dashboard")
    st.write("Welcome to the control center.")
    st.divider()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Add Tasks", "🗂️ Portfolio", "💰 UFA Finances", "🎁 XP Store"])
    
    with tab1:
        st.subheader("Add a New Task for Sonny")
        with st.form("new_task_form"):
            task_title = st.text_input("Task Description")
            task_category = st.selectbox("Subject Category", [
                "Math (Beast Academy)", "Logic & Cognitive", "Language Arts (Brave Writer)", 
                "Science", "Social Studies (Tuttle Twins)", "Applied STEM"
            ])
            task_video = st.text_input("Optional: YouTube Video URL")
            task_xp = st.number_input("XP Reward", min_value=5, max_value=500, value=10, step=5)
            submitted = st.form_submit_button("Save Task")
            
            if submitted and task_title != "":
                add_task_to_db(task_title, task_category, task_video, task_xp)
                st.success(f"Added to {task_category} for {task_xp} XP.")
                st.rerun()
                
    with tab2:
        today_display = date.today().strftime("%A, %b %d")
        st.subheader(f"Completed Tasks ({today_display})")
        
        admin_completed_tasks = get_completed_tasks() 
        if len(admin_completed_tasks) == 0:
            st.info("No completed tasks yet for today.")
        else:
            for task in admin_completed_tasks:
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
        total_spent = sum([expense[2] for expenses in expenses]) 
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

    with tab4:
        st.subheader("Store Inventory Management")
        
        st.write("**Add a New Reward**")
        with st.form("new_reward_form"):
            reward_name = st.text_input("Reward Name (e.g., '1 Hour Screen Time', '$5 Robux')")
            reward_cost = st.number_input("XP Cost", min_value=10, max_value=5000, value=100, step=10)
            submitted_reward = st.form_submit_button("Add to Store")
            
            if submitted_reward and reward_name != "":
                add_reward(reward_name, reward_cost)
                st.success(f"Added {reward_name} to the store!")
                st.rerun()
                
        st.divider()
        st.write("**Current Store Items**")
        rewards = get_rewards()
        if len(rewards) == 0:
            st.info("No rewards in the store yet.")
        else:
            for reward in rewards:
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.markdown(f"🎁 **{reward[1]}** (Costs 💎 {reward[2]} XP)")
                with col2:
                    if st.button("❌", key=f"del_reward_{reward[0]}"):
                        delete_reward(reward[0])
                        st.rerun()
                        
        st.divider()
        st.write("**Sonny's Purchase History (Receipt Ledger)**")
        purchase_history = get_purchase_history()
        
        if len(purchase_history) == 0:
            st.info("Sonny hasn't bought anything yet.")
        else:
            for purchase in purchase_history:
                st.markdown(f"🗓️ {purchase[2]} — **{purchase[0]}** (Spent 💎 {purchase[1]} XP)")