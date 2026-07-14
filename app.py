import streamlit as st
import sqlite3
from datetime import date, datetime, timedelta
import pandas as pd

# ==========================================
# DATABASE SETUP & HELPER FUNCTIONS
# ==========================================

def verify_db_schema():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    
    # Verify inventory_qty column in rewards table
    try:
        cursor.execute("SELECT inventory_qty FROM rewards LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE rewards ADD COLUMN inventory_qty INTEGER DEFAULT 1")
        conn.commit()
        
    # Verify is_boss_fight column in tasks table
    try:
        cursor.execute("SELECT is_boss_fight FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE tasks ADD COLUMN is_boss_fight INTEGER DEFAULT 0")
        conn.commit()
    
    conn.close()

verify_db_schema()

def add_task_to_db(title, category, video_url, xp_reward, target_date, is_boss):
    date_string = target_date.strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks (title, category, task_date, video_url, xp_reward, is_boss_fight) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, category, date_string, video_url, xp_reward, is_boss))
    conn.commit()
    conn.close()

def get_pending_tasks(view_date):
    date_string = view_date.strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    
    if view_date == date.today():
        cursor.execute("""
            SELECT id, title, category, video_url, xp_reward, is_boss_fight 
            FROM tasks 
            WHERE is_completed = 0 AND task_date <= ?
            ORDER BY task_date ASC
        """, (date_string,))
    else:
        cursor.execute("""
            SELECT id, title, category, video_url, xp_reward, is_boss_fight 
            FROM tasks 
            WHERE is_completed = 0 AND task_date = ?
        """, (date_string,))
        
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def complete_task(task_id):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET is_completed = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def get_completed_tasks(view_date):
    date_string = view_date.strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, category, video_url, xp_reward, is_boss_fight 
        FROM tasks 
        WHERE is_completed = 1 AND task_date = ?
    """, (date_string,))
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

def update_expense_status(expense_id, new_status):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE expenses SET status = ? WHERE id = ?", (new_status, expense_id))
    conn.commit()
    conn.close()

def delete_expense(expense_id):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()

def add_reward(name, xp_cost, qty):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO rewards (name, xp_cost, inventory_qty) VALUES (?, ?, ?)", (name, xp_cost, qty))
    conn.commit()
    conn.close()

def get_rewards():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, xp_cost, inventory_qty FROM rewards")
    rewards = cursor.fetchall()
    conn.close()
    return rewards

# --- NEW: Helper function to edit cost and stock details of an existing store item ---
def update_reward_details(reward_id, new_cost, new_qty):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE rewards 
        SET xp_cost = ?, inventory_qty = ? 
        WHERE id = ?
    """, (new_cost, new_qty, reward_id))
    conn.commit()
    conn.close()
# --- END NEW ---

def delete_reward(reward_id):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rewards WHERE id = ?", (reward_id,))
    conn.commit()
    conn.close()

def buy_reward(reward_id, reward_name, xp_cost):
    today_string = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO purchases (reward_name, xp_cost, purchase_date) VALUES (?, ?, ?)", 
                   (reward_name, xp_cost, today_string))
    cursor.execute("UPDATE rewards SET inventory_qty = MAX(0, inventory_qty - 1) WHERE id = ?", (reward_id,))
    conn.commit()
    conn.close()

def get_xp_balance():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(CASE WHEN is_boss_fight = 1 THEN xp_reward * 2 ELSE xp_reward END) 
        FROM tasks 
        WHERE is_completed = 1
    """)
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

def get_task_completion_stats():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT category, COUNT(id) FROM tasks WHERE is_completed = 1 GROUP BY category")
    stats = cursor.fetchall()
    conn.close()
    return stats

def get_xp_over_time():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT task_date, SUM(CASE WHEN is_boss_fight = 1 THEN xp_reward * 2 ELSE xp_reward END) 
        FROM tasks 
        WHERE is_completed = 1 
        GROUP BY task_date 
        ORDER BY task_date ASC
    """)
    data = cursor.fetchall()
    conn.close()
    return data

def get_daily_streak():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT task_date FROM tasks WHERE is_completed = 1 ORDER BY task_date DESC")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return 0
        
    completed_dates = set()
    for row in rows:
        try:
            completed_dates.add(datetime.strptime(row[0], "%Y-%m-%d").date())
        except ValueError:
            pass
            
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    if today not in completed_dates and yesterday not in completed_dates:
        return 0
        
    current_date = today if today in completed_dates else yesterday
    streak = 0
    
    while current_date in completed_dates:
        streak += 1
        current_date -= timedelta(days=1)
        
    return streak

def get_expense_totals_by_status():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT status, SUM(cost) FROM expenses GROUP BY status")
    rows = cursor.fetchall()
    conn.close()
    return dict(rows)

SUBJECT_EMOJIS = {
    "Math (Beast Academy)": "🧮",
    "Logic & Cognitive": "⚔️",
    "Language Arts (Brave Writer)": "✍️",
    "Science": "🧪",
    "Social Studies (Tuttle Twins)": "🗺️",
    "Applied STEM": "🛠️"
}

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

if 'show_balloons' not in st.session_state:
    st.session_state.show_balloons = False

st.sidebar.title("Navigation")
user_view = st.sidebar.radio("Who is using the dashboard?", ["Sonny (Student)", "Dad (Admin)"])

# ------------------------------------------
# SONNY'S VIEW
# ------------------------------------------
if user_view == "Sonny (Student)":
    
    if st.session_state.show_balloons:
        st.balloons()
        st.session_state.show_balloons = False

    col_date, _ = st.columns([0.25, 0.75])
    with col_date:
        selected_date = st.date_input("📅 Select Date:", value=date.today())

    day_display = selected_date.strftime("%A, %b %d")
    st.title(f"🎓 Sonny's Hub - {day_display}")
    
    tab_quests, tab_store = st.tabs(["📋 Daily Quests", "🛍️ Reward Store"])
    
    with tab_quests:
        pending_tasks = get_pending_tasks(selected_date)
        completed_tasks = get_completed_tasks(selected_date)
        
        daily_xp = sum([task[4] * 2 if task[5] == 1 else task[4] for task in completed_tasks])
        
        header_col1, header_col2, header_col3 = st.columns([0.5, 0.25, 0.25])
        with header_col1:
            total_tasks = len(pending_tasks) + len(completed_tasks)
            if total_tasks > 0:
                progress_decimal = len(completed_tasks) / total_tasks
                progress_percentage = int(progress_decimal * 100)
                st.write(f"**Daily Quest Progress: {progress_percentage}%**")
                st.progress(progress_decimal)
            else:
                st.write("**No active quests found.**")

        with header_col2:
            st.metric(label="🏆 XP Earned (This Day)", value=daily_xp)
            
        with header_col3:
            st.metric(label="🔥 Daily Streak", value=f"{get_daily_streak()} Days")
        
        st.divider()
        
        col_todo, col_done = st.columns(2)
        
        with col_todo:
            st.subheader("📝 Up Next")
            if len(pending_tasks) == 0:
                st.success("🎉 All caught up!")
            else:
                for task in pending_tasks:
                    task_id, task_title, task_category, task_video_url, task_xp, is_boss = task
                    emoji = SUBJECT_EMOJIS.get(task_category, "📋")
                    
                    inner_col1, inner_col2 = st.columns([0.8, 0.2])
                    with inner_col1:
                        if is_boss == 1:
                            st.markdown("👑 **DAILY BOSS FIGHT - DOUBLE XP CHALLENGE!** 👑")
                            label_text = f"🔥 **{emoji} {task_category}**: {task_title} (💎 {task_xp * 2} XP!!)"
                        else:
                            label_text = f"**{emoji} {task_category}**: {task_title} (💎 {task_xp} XP)"
                            
                        is_checked = st.checkbox(label_text, key=f"task_{task_id}")
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
                        st.session_state.show_balloons = True
                        st.rerun()

        with col_done:
            st.subheader("✅ Completed")
            if len(completed_tasks) == 0:
                st.info("Nothing completed yet.")
            else:
                for task in completed_tasks:
                    task_title = task[1]
                    task_category = task[2]
                    task_xp = task[4]
                    is_boss = task[5]
                    emoji = SUBJECT_EMOJIS.get(task_category, "📋")
                    
                    if is_boss == 1:
                        st.success(f"👑 **{emoji} {task_category}**: {task_title} (💎 {task_xp * 2} XP Earned!)")
                    else:
                        st.success(f"**{emoji} {task_category}**: {task_title} (💎 {task_xp} XP)")

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
                reward_id, reward_name, reward_cost, reward_qty = reward
                
                with cols[index % 3]:
                    st.markdown(f"### {reward_name}")
                    st.write(f"**Cost:** 💎 {reward_cost} XP")
                    
                    if reward_qty > 0:
                        st.write(f"🟢 **In Stock:** {reward_qty} available")
                        buy_disabled = False
                    else:
                        st.write("🔴 **OUT OF STOCK**")
                        buy_disabled = True
                    
                    if st.button("Buy", key=f"buy_{reward_id}", disabled=buy_disabled):
                        if bank_balance >= reward_cost:
                            buy_reward(reward_id, reward_name, reward_cost)
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
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Add Tasks", "🗂️ Portfolio", "💰 UFA Finances", "🎁 XP Store", "📊 Analytics"])
    
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
            scheduled_date = st.date_input("Scheduled Date", value=date.today())
            is_boss_fight = st.checkbox("⭐ Mark as Daily Boss Fight (Double XP Bonus!)", value=False)
            submitted = st.form_submit_button("Save Task")
            
            if submitted and task_title != "":
                boss_int = 1 if is_boss_fight else 0
                add_task_to_db(task_title, task_category, task_video, task_xp, scheduled_date, boss_int)
                st.success(f"Scheduled for {task_category} on {scheduled_date.strftime('%b %d')}.")
                st.rerun()
                
    with tab2:
        portfolio_date = st.date_input("📅 Select Date to Review:", value=date.today(), key="admin_portfolio_date")
        day_display = portfolio_date.strftime("%A, %b %d")
        
        st.subheader(f"Completed Tasks ({day_display})")
        
        admin_completed_tasks = get_completed_tasks(portfolio_date) 
        
        if len(admin_completed_tasks) == 0:
            st.info(f"No completed tasks found for {day_display}.")
        else:
            for task in admin_completed_tasks:
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    emoji = SUBJECT_EMOJIS.get(task[2], "📋")
                    if task[5] == 1:
                        st.markdown(f"👑 **{emoji} {task[2]}**: {task[1]} *(Boss Fight!)*")
                    else:
                        st.markdown(f"✅ **{emoji} {task[2]}**: {task[1]}")
                with col2:
                    if st.button("❌", key=f"del_task_{task[0]}"):
                        delete_task(task[0])
                        st.rerun()

    with tab3:
        st.subheader("Utah Fits All (UFA) Budget Tracker")
        expenses = get_all_expenses()
        total_budget = 4000.00
        
        total_spent = sum([expense[2] for expense in expenses if expense[4] != "Out of Pocket (Not UFA)"])
        remaining_budget = total_budget - total_spent
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total UFA Grant", f"${total_budget:,.2f}")
        col2.metric("Total Spent", f"${total_spent:,.2f}")
        col3.metric("Remaining Funds", f"${remaining_budget:,.2f}")
        st.sidebar.markdown("---")
        
        st.write("**UFA Pipeline Allocation Radar**")
        status_map = get_expense_totals_by_status()
        pending_odyssey = status_map.get("Pending Odyssey Approval", 0.0)
        direct_paid = status_map.get("Approved & Direct Paid", 0.0)
        reimbursed = status_map.get("Reimbursed", 0.0)
        out_of_pocket = status_map.get("Out of Pocket (Not UFA)", 0.0)
        
        radar_col1, radar_col2, radar_col3, radar_col4 = st.columns(4)
        radar_col1.metric("⏳ Pending Odyssey", f"${pending_odyssey:,.2f}")
        radar_col2.metric("🟢 Direct Paid", f"${direct_paid:,.2f}")
        radar_col3.metric("💰 Reimbursed", f"${reimbursed:,.2f}")
        radar_col4.metric("🛑 Out of Pocket", f"${out_of_pocket:,.2f}")
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
                col_exp1, col_exp2, col_exp3 = st.columns([0.5, 0.4, 0.1])
                with col_exp1:
                    st.markdown(f"📦 **{exp[1]}** | ${exp[2]:.2f}\n\n*Category: {exp[3]}*")
                with col_exp2:
                    status_options = [
                        "Pending Odyssey Approval", "Approved & Direct Paid", 
                        "Reimbursed", "Out of Pocket (Not UFA)"
                    ]
                    
                    try:
                        current_status_idx = status_options.index(exp[4])
                    except ValueError:
                        current_status_idx = 0
                        
                    chosen_status = st.selectbox(
                        f"Status Dropdown {exp[0]}",
                        options=status_options,
                        index=current_status_idx,
                        key=f"update_status_select_{exp[0]}",
                        label_visibility="collapsed"
                    )
                    
                    if chosen_status != exp[4]:
                        update_expense_status(exp[0], chosen_status)
                        st.rerun()
                with col_exp3:
                    if st.button("❌", key=f"del_exp_{exp[0]}"):
                        delete_expense(exp[0])
                        st.rerun()

    with tab4:
        st.subheader("Store Inventory Management")
        
        st.write("**Add a New Reward**")
        with st.form("new_reward_form"):
            reward_name = st.text_input("Reward Name (e.g., '1 Hour Screen Time', '$5 Robux')")
            reward_cost = st.number_input("XP Cost", min_value=10, max_value=5000, value=100, step=10)
            reward_qty = st.number_input("Quantity in Stock", min_value=1, max_value=100, value=5, step=1)
            submitted_reward = st.form_submit_button("Add to Store")
            
            if submitted_reward and reward_name != "":
                add_reward(reward_name, reward_cost, reward_qty)
                st.success(f"Added {reward_name} to the store!")
                st.rerun()
                
        st.divider()
        st.write("**Current Store Items**")
        rewards = get_rewards()
        if len(rewards) == 0:
            st.info("No rewards in the store yet.")
        else:
            for reward in rewards:
                # --- NEW: Replaced the static item line with an interactive inline editor row ---
                reward_id, reward_name, reward_cost, reward_qty = reward
                
                col_rew1, col_rew2, col_rew3, col_rew4 = st.columns([0.4, 0.2, 0.2, 0.2])
                with col_rew1:
                    st.markdown(f"🎁 **{reward_name}**")
                with col_rew2:
                    edited_cost = st.number_input(
                        "Cost", min_value=5, max_value=10000, value=int(reward_cost), step=5, 
                        key=f"edit_cost_{reward_id}", label_visibility="collapsed"
                    )
                with col_rew3:
                    edited_qty = st.number_input(
                        "Stock", min_value=0, max_value=500, value=int(reward_qty), step=1, 
                        key=f"edit_qty_{reward_id}", label_visibility="collapsed"
                    )
                with col_rew4:
                    # Render an actionable update button if changes are staged
                    if edited_cost != reward_cost or edited_qty != reward_qty:
                        if st.button("💾 Save", key=f"save_rew_{reward_id}"):
                            update_reward_details(reward_id, edited_cost, edited_qty)
                            st.rerun()
                    else:
                        if st.button("❌", key=f"del_reward_{reward_id}"):
                            delete_reward(reward_id)
                            st.rerun()
                # --- END NEW ---
                        
        st.divider()
        st.write("**Sonny's Purchase History (Receipt Ledger)**")
        purchase_history = get_purchase_history()
        
        if len(purchase_history) == 0:
            st.info("Sonny hasn't bought anything yet.")
        else:
            for purchase in purchase_history:
                st.markdown(f"🗓️ {purchase[2]} — **{purchase[0]}** (Spent 💎 {purchase[1]} XP)")

    with tab5:
        st.subheader("📊 Flokus Learning Insights")
        st.write("Real-time telemetry showing study distribution and total XP momentum.")
        st.divider()

        st.markdown("### 🗓️ 7-Day Activity Radar")
        st.caption("Visual confirmation tracker checking if assignments were cleared each day.")
        
        today_dt = date.today()
        day_cols = st.columns(7)
        
        conn = sqlite3.connect('flokus.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT task_date FROM tasks WHERE is_completed = 1")
        active_dates = {row[0] for row in cursor.fetchall()}
        conn.close()
        
        for i in range(7):
            check_date = today_dt - timedelta(days=6-i)
            date_str = check_date.strftime("%Y-%m-%d")
            day_label = check_date.strftime("%a\n%b %d")
            
            with day_cols[i]:
                if date_str in active_dates:
                    st.markdown("<div style='text-align: center; font-size: 26px;'>🟢</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='text-align: center; font-size: 26px;'>⚪</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: center; font-size: 13px; font-weight: bold; color: gray;'>{day_label}</div>", unsafe_allow_html=True)
        st.divider()

        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.markdown("### 📚 Subject Mastery")
            st.caption("Distribution of completed tasks across core categories.")
            stats = get_task_completion_stats()

            if len(stats) == 0:
                st.info("No tasks completed yet! Complete quests to activate telemetry.")
            else:
                df_stats = pd.DataFrame(stats, columns=["Subject", "Completed Tasks"])
                df_stats = df_stats.set_index("Subject")
                st.bar_chart(df_stats)

        with col_chart2:
            st.markdown("### 📈 All-Time XP Progress")
            st.caption("Sonny's cumulative milestone progress over time.")
            xp_data = get_xp_over_time()

            if len(xp_data) == 0:
                st.info("Earn some XP first to plot your development curve!")
            else:
                df_xp = pd.DataFrame(xp_data, columns=["Date", "Daily XP"])
                df_xp["Date"] = pd.to_datetime(df_xp["Date"])
                df_xp = df_xp.sort_values("Date")
                
                df_xp["Cumulative XP"] = df_xp["Daily XP"].cumsum()
                df_xp = df_xp.set_index("Date")
                st.line_chart(df_xp["Cumulative XP"])