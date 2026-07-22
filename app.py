import streamlit as st
import pandas as pd
import time
import os
import socket
import json
from datetime import date, datetime, timedelta
import html

# Import custom refactored modules
import config
import database
import ai_tutor

# Initialize/verify database structure
database.init_db()

# Global database compatibility wrappers to preserve existing UI code without prefixing
verify_db_schema = database.verify_db_schema
add_creator_project = database.add_creator_project
get_active_projects = database.get_active_projects
complete_creator_project = database.complete_creator_project
get_completed_projects = database.get_completed_projects
add_task_to_db = database.add_task_to_db
get_pending_tasks = database.get_pending_tasks
complete_task = database.complete_task
get_completed_tasks = database.get_completed_tasks
delete_task = database.delete_task
update_task_details = database.update_task_details
get_all_pending_tasks = database.get_all_pending_tasks
update_creator_project = database.update_creator_project
delete_creator_project = database.delete_creator_project
update_expense_details = database.update_expense_details
get_pet_status = database.get_pet_status
use_pet_item = database.use_pet_item
add_chat_msg = database.add_chat_msg
get_chat_history = database.get_chat_history
get_floki_persona = database.get_floki_persona
set_floki_persona = database.set_floki_persona
add_expense = database.add_expense
get_all_expenses = database.get_all_expenses
update_expense_status = database.update_expense_status
delete_expense = database.delete_expense
add_reward = database.add_reward
get_rewards = database.get_rewards
update_reward_details = database.update_reward_details
delete_reward = database.delete_reward
buy_reward = database.buy_reward
get_xp_balance = database.get_xp_balance
get_purchase_history = database.get_purchase_history
get_task_completion_stats = database.get_task_completion_stats
get_xp_over_time = database.get_xp_over_time
get_daily_streak = database.get_daily_streak
get_expense_totals_by_status = database.get_expense_totals_by_status
get_full_portfolio_data = database.get_full_portfolio_data
get_pet_inventory = database.get_pet_inventory
deduct_pet_stamina = database.deduct_pet_stamina
complete_quest_room = database.complete_quest_room
fail_quest_room = database.fail_quest_room
get_all_creator_projects = database.get_all_creator_projects
get_all_purchases = database.get_all_purchases
mark_purchase_claimed = database.mark_purchase_claimed
get_active_task_dates = database.get_active_task_dates
get_completed_projects_by_platform = database.get_completed_projects_by_platform
get_total_focus_minutes = database.get_total_focus_minutes
get_autonomy_metrics = database.get_autonomy_metrics
clear_chat_history = database.clear_chat_history
override_pet_status = database.override_pet_status

add_school_event = database.add_school_event
get_school_events = database.get_school_events
get_upcoming_event_notifications = database.get_upcoming_event_notifications
update_school_event = database.update_school_event
delete_school_event = database.delete_school_event
get_next_major_school_event = database.get_next_major_school_event

# Configurations
SUBJECT_EMOJIS = config.SUBJECT_EMOJIS
PLATFORM_LINKS = config.PLATFORM_LINKS

# ==========================================
# STREAMLIT DASHBOARD UI
# ==========================================

st.set_page_config(page_title="Flokus Academy", layout="wide")

# --- NEW: Inject Premium Gamified CSS Aesthetics ---
st.markdown("""
<style>
    /* Import Outfit font */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

    /* Apply font globally */
    html, body, [class*="css"], .stMarkdown, p, div {
        font-family: 'Outfit', sans-serif !important;
    }

    /* Dark theme background styling */
    .stApp {
        background-color: #0c0e17 !important;
        color: #e2e8f0 !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #121420 !important;
        border-right: 1px solid #1f2336 !important;
    }

    /* Tab Custom Styling */
    button[data-baseweb="tab"] {
        font-size: 16px !important;
        font-weight: 600 !important;
        color: #8c9bb4 !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.3s ease !important;
        background-color: transparent !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #63b3ed !important;
        border-bottom: 2px solid #63b3ed !important;
    }

    /* Style Streamlit containers with borders as gamified cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(135deg, #181c2e 0%, #111422 100%) !important;
        border: 1px solid #232a45 !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1) !important;
        transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.2) !important;
        border-color: #404f85 !important;
    }

    /* Boss Fight Glowing Card */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(div.boss-fight-marker) {
        background: linear-gradient(135deg, #2d164d 0%, #170b29 100%) !important;
        border: 2px solid #9f7aea !important;
        box-shadow: 0 0 15px rgba(159, 122, 234, 0.2) !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(div.boss-fight-marker):hover {
        box-shadow: 0 0 25px rgba(159, 122, 234, 0.4) !important;
        border-color: #b794f4 !important;
    }

    /* Button Styling */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        background-color: #1b1e32 !important;
        color: #e2e8f0 !important;
        border: 1px solid #333b5c !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #2b3254 !important;
        border-color: #63b3ed !important;
        transform: scale(1.02) !important;
        color: #ffffff !important;
    }

    /* Metric Panels */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #181c2e 0%, #111422 100%) !important;
        border: 1px solid #232a45 !important;
        padding: 15px !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.15) !important;
    }
    div[data-testid="stMetricValue"] {
        color: #63b3ed !important;
        font-size: 32px !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #8c9bb4 !important;
        font-size: 13px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    /* Divider styling */
    /* Custom Chat Message Styling */
    div[data-testid="stChatMessage"] {
        background-color: #141724 !important;
        border: 1px solid #232a45 !important;
        border-radius: 12px !important;
        padding: 15px !important;
        margin-bottom: 12px !important;
    }
    div[data-testid="stChatMessage"]:has(img[src*="assistant"]) {
        background-color: #1a2238 !important;
        border-color: #63b3ed !important;
    }
    div[data-testid="stChatMessage"]:has(img[src*="user"]) {
        background-color: #1e1b2e !important;
        border-color: #9f7aea !important;
    }

    /* Event Urgency & Calendar Styling */
    .event-card {
        background: linear-gradient(135deg, #161b2e 0%, #0f1220 100%);
        border: 1px solid #283254;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .event-card.urgent {
        border-left: 5px solid #f56565 !important;
        box-shadow: 0 0 10px rgba(245, 101, 101, 0.2);
    }
    .event-card.important {
        border-left: 5px solid #ed8936 !important;
        box-shadow: 0 0 10px rgba(237, 137, 54, 0.2);
    }
    .event-card.normal {
        border-left: 5px solid #4299e1 !important;
    }
    .badge-urgent {
        background-color: #742a2a;
        color: #feb2b2;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 700;
    }
    .badge-important {
        background-color: #7b341e;
        color: #fbd38d;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 700;
    }
    .badge-normal {
        background-color: #2a4365;
        color: #90cdf4;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 700;
    }
    .countdown-hero {
        background: linear-gradient(135deg, #1e2640 0%, #11162b 100%);
        border: 2px solid #63b3ed;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 0 20px rgba(99, 179, 237, 0.25);
    }
    .countdown-number {
        font-size: 44px;
        font-weight: 800;
        color: #63b3ed;
        line-height: 1.1;
    }
</style>
""", unsafe_allow_html=True)

def render_school_notifications_bar():
    active_notifications = get_upcoming_event_notifications(date.today())
    if active_notifications:
        with st.expander(f"🔔 **Upcoming School Alerts & Notifications ({len(active_notifications)})**", expanded=True):
            for notif in active_notifications:
                urgency = notif['importance'].lower()
                badge_class = f"badge-{urgency}" if urgency in ['urgent', 'important', 'normal'] else "badge-normal"
                
                if notif['days_left'] == 0:
                    time_label = "🚨 **TODAY!**"
                elif notif['days_left'] == 1:
                    time_label = "⚠️ **TOMORROW!**"
                else:
                    time_label = f"⏳ In **{notif['days_left']} days** ({notif['event_date'].strftime('%b %d')})"
                    
                desc_html = f'<div style="margin-top: 4px; font-size: 13px; color: #cbd5e0;">📝 {notif["description"]}</div>' if notif['description'] else ''
                time_str = f"🕒 {notif['event_time']}" if notif['event_time'] else ""
                
                st.markdown(f"""
                <div class="event-card {urgency}">
                    <span class="{badge_class}">{notif['importance'].upper()}</span> &nbsp;
                    <span style="font-weight: 700; font-size: 16px; color: #ffffff;">{notif['title']}</span>
                    <div style="margin-top: 6px; font-size: 14px; color: #a0aec0;">
                        🏷️ {notif['category']} | 📅 Date: <strong>{notif['event_date'].strftime('%A, %b %d, %Y')}</strong> {time_str} | {time_label}
                    </div>
                    {desc_html}
                </div>
                """, unsafe_allow_html=True)

if 'show_balloons' not in st.session_state:
    st.session_state.show_balloons = False

st.sidebar.title("Navigation")
user_view = st.sidebar.radio("Who is using the dashboard?", ["Sonny (Student)", "Dad (Admin)"])

is_admin_authenticated = False
if user_view == "Dad (Admin)":
    admin_pin = st.sidebar.text_input("🔑 Enter Admin Passcode:", type="password")
    secure_pin = st.secrets.get("admin_pin", "1234")
    if admin_pin == secure_pin:
        is_admin_authenticated = True
    elif admin_pin != "":
        st.sidebar.error("❌ Incorrect Passcode!")

# ------------------------------------------
# SONNY'S VIEW
# ------------------------------------------
if user_view == "Sonny (Student)":
    
    if st.session_state.show_balloons:
        st.balloons()
        st.session_state.show_balloons = False

    render_school_notifications_bar()

    col_date, _ = st.columns([0.25, 0.75])
    with col_date:
        selected_date = st.date_input("📅 Select Date:", value=date.today())

    day_display = selected_date.strftime("%A, %b %d")
    st.title(f"🎓 Sonny's Hub - {day_display}")
    
    tab_quests, tab_calendar, tab_creator, tab_store, tab_pet, tab_ai = st.tabs(["📋 Daily Quests", "📅 School Calendar", "🛠️ Creator Block", "🛍️ Reward Store", "🐾 Digital Pet", "💬 Ask Floki"])
    
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
                    
                    with st.container(border=True):
                        if is_boss == 1:
                            st.markdown('<div class="boss-fight-marker"></div>', unsafe_allow_html=True)
                            
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
                        
                        with st.expander("⏱️ Focus Sprint Timer"):
                            t_col1, t_col2 = st.columns([0.5, 0.5])
                            with t_col1:
                                focus_mins = st.number_input(
                                    "Sprint Minutes", min_value=1, max_value=60, value=15, 
                                    step=1, key=f"timer_input_{task_id}"
                                )
                            with t_col2:
                                st.write("") 
                                start_timer = st.button("🚀 Start Sprint", key=f"timer_btn_{task_id}")
                            
                            # Cache target focus time when start button is pressed
                            if start_timer:
                                st.session_state[f"runtime_captured_{task_id}"] = int(focus_mins)
                                st.session_state[f"timer_started_{task_id}"] = time.time()
                                st.session_state[f"timer_duration_{task_id}"] = int(focus_mins) * 60
                                st.rerun()
                                
                            # Check and render countdown widget
                            if f"timer_started_{task_id}" in st.session_state:
                                start_time = st.session_state[f"timer_started_{task_id}"]
                                duration = st.session_state[f"timer_duration_{task_id}"]
                                elapsed = time.time() - start_time
                                remaining = max(0, int(duration - elapsed))
                                
                                if remaining > 0:
                                    import streamlit.components.v1 as components
                                    timer_html = f"""
                                    <div style="background-color: #1a2238; border: 1px solid #63b3ed; border-radius: 8px; padding: 15px; text-align: center; font-family: 'Outfit', sans-serif;">
                                        <div style="font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; color: #8c9bb4; margin-bottom: 5px;">⌛ Active Focus Window</div>
                                        <div id="countdown-val" style="font-size: 32px; font-weight: bold; color: #63b3ed;">00:00</div>
                                    </div>
                                    <script>
                                        let seconds = {remaining};
                                        function updateTimer() {{
                                            let mins = Math.floor(seconds / 60);
                                            let secs = seconds % 60;
                                            document.getElementById('countdown-val').innerText = 
                                                `${{mins.toString().padStart(2, '0')}}:${{secs.toString().padStart(2, '0')}}`;
                                            if (seconds <= 0) {{
                                                document.getElementById('countdown-val').innerText = "🎉 Focus Sprint Complete! You crushed it!";
                                                document.getElementById('countdown-val').style.color = "#22c55e";
                                            }} else {{
                                                seconds--;
                                                setTimeout(updateTimer, 1000);
                                            }}
                                        }}
                                        updateTimer();
                                    </script>
                                    """
                                    components.html(timer_html, height=100)
                                    if st.button("🔄 Sync/Refresh Timer", key=f"timer_refresh_{task_id}"):
                                        st.rerun()
                                else:
                                    st.success("🎉 Focus Sprint Complete! You crushed it!")
                        
                        note_input = st.text_input(
                            "✏️ What did you learn or read? (Add a summary note here before checking complete)",
                            key=f"note_input_{task_id}"
                        )
                        
                        st.write("") 
                        
                        if is_checked:
                            if len(note_input.strip()) < 15:
                                st.warning(f"⚠️ Note is too short! Write at least 15 characters about what you learned. (Current: {len(note_input.strip())}/15)")
                            else:
                                # --- NEW: Pass state session-held focus minutes into db logic ---
                                completed_mins = st.session_state.get(f"runtime_captured_{task_id}", 0)
                                complete_task(task_id, note_input, completed_mins)
                                # Clean up memory state flag
                                if f"runtime_captured_{task_id}" in st.session_state:
                                    del st.session_state[f"runtime_captured_{task_id}"]
                                # --- END NEW ---
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
                    
                    with st.container(border=True):
                        if is_boss == 1:
                            st.markdown('<div class="boss-fight-marker"></div>', unsafe_allow_html=True)
                            st.success(f"👑 **{emoji} {task_category}**: {task_title} (💎 {task_xp * 2} XP Earned!)")
    with tab_calendar:
        st.subheader("📅 School Calendar & Upcoming Academic Events")
        
        # --- Hero Countdown Box ---
        next_event = get_next_major_school_event(date.today())
        if next_event:
            d_left = next_event['days_left']
            if d_left > 0:
                cd_subtitle = f"Countdown to **{next_event['title']}** ({next_event['event_date'].strftime('%b %d, %Y')})"
                cd_number = f"⏳ {d_left} Days Away"
            elif d_left == 0:
                cd_subtitle = f"🎉 TODAY IS THE DAY!"
                cd_number = f"🚨 {next_event['title']}"
            else:
                cd_subtitle = "School Semester in Progress"
                cd_number = "Academic Year 2026-2027"
                
            time_str = f"🕒 {next_event['event_time']}" if next_event['event_time'] else ""
            desc_html = f'<div style="margin-top: 6px; font-size: 13px; color: #cbd5e0;">📝 {next_event["description"]}</div>' if next_event['description'] else ''
            
            st.markdown(f"""
            <div class="countdown-hero">
                <div style="font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: #a0aec0; margin-bottom: 5px;">
                    {cd_subtitle}
                </div>
                <div class="countdown-number">{cd_number}</div>
                <div style="font-size: 14px; color: #e2e8f0; margin-top: 8px;">
                    🏷️ Category: <strong>{next_event['category']}</strong> | Importance: <strong>{next_event['importance']}</strong> {time_str}
                </div>
                {desc_html}
            </div>
            """, unsafe_allow_html=True)

        # Calendar View Subtabs
        cal_sub1, cal_sub2 = st.tabs(["🗓️ Interactive Month View", "📋 Upcoming Events List"])
        
        with cal_sub1:
            col_m1, col_m2 = st.columns([0.4, 0.6])
            with col_m1:
                selected_month_year = st.date_input("Select Month/Year to View", value=date(2026, 8, 1), key="sonny_cal_month_picker")
            
            view_year = selected_month_year.year
            view_month = selected_month_year.month
            
            import calendar
            _, num_days = calendar.monthrange(view_year, view_month)
            month_start = date(view_year, view_month, 1)
            month_end = date(view_year, view_month, num_days)
            
            events_in_month = get_school_events(start_date=month_start, end_date=month_end)
            
            st.markdown(f"### 🗓️ {month_start.strftime('%B %Y')} Calendar")
            
            events_by_day = {}
            for ev in events_in_month:
                ev_id, ev_title, ev_date_str, ev_time, ev_cat, ev_imp, ev_rem, ev_desc, _ = ev
                try:
                    d_obj = datetime.strptime(ev_date_str, "%Y-%m-%d").date()
                    day_num = d_obj.day
                    if day_num not in events_by_day:
                        events_by_day[day_num] = []
                    events_by_day[day_num].append({
                        "title": ev_title,
                        "time": ev_time,
                        "category": ev_cat,
                        "importance": ev_imp,
                        "desc": ev_desc
                    })
                except Exception:
                    pass

            days_header = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            cols_head = st.columns(7)
            for idx, hname in enumerate(days_header):
                cols_head[idx].markdown(
                    f"<div style='text-align:center; font-weight:700; font-size:12px; text-transform:uppercase; letter-spacing:1px; color:#63b3ed; background:#161c2e; padding:6px 0; border-radius:6px; border:1px solid #283254; margin-bottom:4px;'>{hname}</div>",
                    unsafe_allow_html=True
                )
                
            first_weekday = (month_start.weekday() + 1) % 7
            
            day_counter = 1
            row_cols = st.columns(7)
            
            for cell_idx in range(first_weekday):
                row_cols[cell_idx].markdown(
                    "<div style='background:rgba(18, 22, 38, 0.3); border:1px dashed rgba(40, 50, 84, 0.4); border-radius:8px; min-height:90px; margin-bottom:6px;'></div>",
                    unsafe_allow_html=True
                )
                
            current_cell = first_weekday
            
            while day_counter <= num_days:
                cell_col = row_cols[current_cell]
                c_date = date(view_year, view_month, day_counter)
                is_today = (c_date == date.today())
                
                day_border = "2px solid #6366f1" if is_today else "1px solid #283254"
                day_bg = "linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(18, 22, 38, 0.95) 100%)" if is_today else "#121626"
                num_color = "#818cf8" if is_today else "#e2e8f0"
                today_badge = "<span style='font-size:9px; background:#4f46e5; color:#ffffff; padding:1px 5px; border-radius:4px; font-weight:600;'>TODAY</span>" if is_today else ""
                
                events_html = ""
                if day_counter in events_by_day:
                    for item in events_by_day[day_counter]:
                        imp = item.get('importance', 'Normal')
                        if imp == 'Urgent':
                            imp_color = "#ef4444"
                            badge_bg = "rgba(239, 68, 68, 0.18)"
                        elif imp == 'Important':
                            imp_color = "#f59e0b"
                            badge_bg = "rgba(245, 158, 11, 0.18)"
                        else:
                            imp_color = "#3b82f6"
                            badge_bg = "rgba(59, 130, 246, 0.18)"
                            
                        title_escaped = html.escape(item['title'])
                        desc_escaped = html.escape(item.get('desc', ''))
                        tooltip = f"{title_escaped} - {desc_escaped}" if desc_escaped else title_escaped
                        
                        time_html = f"<div style='font-size:9px; color:#a0aec0; font-weight:600;'>⏱️ {html.escape(item['time'])}</div>" if item.get('time') else ""
                        
                        events_html += (
                            f"<div style='background:{badge_bg}; border-left:3px solid {imp_color}; border-radius:5px; padding:4px 6px; margin-top:4px; font-size:11px; line-height:1.2; color:#ffffff;' title='{tooltip}'>"
                            f"{time_html}"
                            f"<div style='font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{title_escaped}</div>"
                            f"</div>"
                        )
                        
                cell_html = (
                    f"<div style='background:{day_bg}; border:{day_border}; border-radius:8px; padding:6px 8px; min-height:90px; margin-bottom:6px;'>"
                    f"<div style='font-weight:700; font-size:13px; color:{num_color}; display:flex; align-items:center; justify-content:space-between;'>"
                    f"<span>{day_counter}</span>{today_badge}"
                    f"</div>"
                    f"{events_html}"
                    f"</div>"
                )
                
                cell_col.markdown(cell_html, unsafe_allow_html=True)
                
                day_counter += 1
                current_cell += 1
                if current_cell == 7 and day_counter <= num_days:
                    current_cell = 0
                    row_cols = st.columns(7)
                    
            if current_cell != 0:
                for fill_idx in range(current_cell, 7):
                    row_cols[fill_idx].markdown(
                        "<div style='background:rgba(18, 22, 38, 0.3); border:1px dashed rgba(40, 50, 84, 0.4); border-radius:8px; min-height:90px; margin-bottom:6px;'></div>",
                        unsafe_allow_html=True
                    )
                    
        with cal_sub2:
            st.markdown("### 📋 All Scheduled School Events")
            cat_options = ["All Categories", "🎓 School Start / Term", "🎥 Live Class (Outschool)", "🛠️ Kit Delivery / Project", "🏛️ Field Trip", "💰 UFA Milestone", "📝 Exam / Assessment", "📌 General"]
            selected_cat_filter = st.selectbox("Filter by Category", cat_options, key="sonny_event_cat_filter")
            
            all_events = get_school_events(category_filter=selected_cat_filter)
            if not all_events:
                st.info("No events found matching this filter.")
            else:
                for ev in all_events:
                    ev_id, ev_title, ev_date_str, ev_time, ev_cat, ev_imp, ev_rem, ev_desc, _ = ev
                    ev_date_obj = datetime.strptime(ev_date_str, "%Y-%m-%d").date()
                    d_left = (ev_date_obj - date.today()).days
                    
                    urgency_class = ev_imp.lower()
                    badge_style = f"badge-{urgency_class}" if urgency_class in ['urgent', 'important', 'normal'] else "badge-normal"
                    
                    if d_left == 0:
                        status_str = "🚨 **TODAY!**"
                    elif d_left > 0:
                        status_str = f"⏳ **{d_left} days away**"
                    else:
                        status_str = "✅ **Completed / Past**"
                        
                    time_str = f"🕒 {ev_time}" if ev_time else ""
                    desc_html = f'<div style="margin-top:4px; font-size:13px; color:#cbd5e0;">📝 {ev_desc}</div>' if ev_desc else ''
                    
                    st.markdown(f"""
                    <div class="event-card {urgency_class}">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:700; font-size:16px; color:#ffffff;">{ev_title}</span>
                            <span class="{badge_style}">{ev_imp.upper()}</span>
                        </div>
                        <div style="margin-top:6px; font-size:14px; color:#a0aec0;">
                            🏷️ Category: <strong>{ev_cat}</strong> | 📅 Date: <strong>{ev_date_obj.strftime('%A, %b %d, %Y')}</strong> {time_str} | {status_str}
                        </div>
                        {desc_html}
                    </div>
                    """, unsafe_allow_html=True)

    with tab_creator:
        st.subheader("🛠️ Active Creator Projects")
        st.write("Take your time. Physical builds require patience. Claim your massive XP reward only when the final project is fully functional!")
        st.divider()
        
        active_projects = get_active_projects()
        
        if len(active_projects) == 0:
            st.info("No active building projects right now. Time to ask Dad for a new CrunchLab!")
        else:
            for proj in active_projects:
                p_id, p_title, p_platform, p_xp = proj
                
                with st.container(border=True):
                    st.markdown(f"### ⚙️ {p_title}")
                    st.write(f"**Platform:** {p_platform}  |  **Bounty:** 💎 {p_xp} XP")
                    
                    proj_note_input = st.text_area(
                        "📝 Project Report: What did you build, and how does it work?", 
                        key=f"proj_note_input_{p_id}"
                    )
                    
                    uploaded_file = st.file_uploader(
                        "📎 Upload photo, video, or document evidence:",
                        type=["png", "jpg", "jpeg", "mp4", "mov", "pdf", "docx"],
                        key=f"file_uploader_{p_id}"
                    )
                    
                    note_len = len(proj_note_input.strip())
                    btn_disabled = note_len < 30
                    
                    if btn_disabled:
                        st.warning(f"⚠️ Report must be at least 30 characters. (Current: {note_len}/30)")
                    
                    if st.button(f"✅ Mark Build Complete & Claim {p_xp} XP", key=f"complete_proj_{p_id}", disabled=btn_disabled):
                        saved_path = ""
                        if uploaded_file is not None:
                            os.makedirs("uploads", exist_ok=True)
                            base_fn = os.path.basename(uploaded_file.name)
                            sanitized_fn = "".join(c for c in base_fn if c.isalnum() or c in "._- ")
                            safe_filename = f"{int(time.time())}_{sanitized_fn}"
                            saved_path = os.path.join("uploads", safe_filename)
                            with open(saved_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                                
                        complete_creator_project(p_id, proj_note_input, saved_path)
                        st.session_state.show_balloons = True
                        st.success(f"Epic job! You successfully built the {p_title} and earned {p_xp} XP!")
                        st.rerun()
                    st.divider()

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
                    with st.container(border=True):
                        st.markdown(f"### {reward_name}")
                        st.write(f"**Cost:** 💎 {reward_cost} XP")
                        
                        if reward_qty > 0:
                            st.write(f"🟢 **In Stock:** {reward_qty} available")
                            buy_disabled = False
                        else:
                            st.write("🔴 **OUT OF STOCK**")
                            buy_disabled = True
                        
                        if buy_disabled:
                            st.button("Buy", key=f"buy_disabled_{reward_id}", disabled=True)
                        else:
                            with st.popover("🛍️ Buy"):
                                st.write(f"Spend 💎 {reward_cost} XP on {reward_name}?")
                                if st.button("Confirm Purchase", key=f"buy_conf_{reward_id}"):
                                    if bank_balance >= reward_cost:
                                        buy_reward(reward_id, reward_name, reward_cost)
                                        st.success(f"Successfully bought {reward_name}!")
                                        st.rerun()
                                    else:
                                        st.error(f"Not enough XP! You need {reward_cost - bank_balance} more.")

    # --- NEW: Digital Pet and AI Chat Views ---
    with tab_pet:
        pet = get_pet_status()
        if not pet:
            st.info("Sparky is sleeping. Check back later!")
        else:
            pet_id, pet_name, pet_level, pet_xp, strength, intelligence, creativity, stamina, max_stamina, happiness, stage, form_name, accessory_parts = pet
            
            # XP level calculations
            next_level_xp = int(100 * (pet_level)**1.8)
            xp_progress = pet_xp / next_level_xp if next_level_xp > 0 else 0.0
            
            st.subheader(f"🐾 Pet Status: {pet_name}")
            
            col_pet_card, col_pet_stats = st.columns([0.4, 0.6])
            
            # --- Dynamic Pet Theme Logic ---
            top_attr = max(strength, intelligence, creativity)
            if stage == "Egg":
                border_color = "#f59e0b"
                bg_style = "linear-gradient(135deg, #1e180d 0%, #0f0c07 100%)"
                glow_style = "box-shadow: 0 0 20px rgba(245, 158, 11, 0.3);"
                text_color = "#fbbf24"
            elif top_attr == intelligence:
                border_color = "#00f0ff"
                bg_style = "linear-gradient(135deg, #0c1b26 0%, #060e14 100%)"
                glow_style = "box-shadow: 0 0 20px rgba(0, 240, 255, 0.3);"
                text_color = "#00f0ff"
            elif top_attr == creativity:
                border_color = "#a855f7"
                bg_style = "linear-gradient(135deg, #200f35 0%, #0f071a 100%)"
                glow_style = "box-shadow: 0 0 20px rgba(168, 85, 247, 0.3);"
                text_color = "#c084fc"
            else: # Strength
                border_color = "#f97316"
                bg_style = "linear-gradient(135deg, #2b1104 0%, #160902 100%)"
                glow_style = "box-shadow: 0 0 20px rgba(249, 115, 22, 0.3);"
                text_color = "#ff983d"

            avatar_emoji = form_name[-1] if form_name and ord(form_name[-1]) > 127 else "🐾"
            clean_form_name = form_name[:-2].strip() if form_name and ord(form_name[-1]) > 127 else form_name

            with col_pet_card:
                # Custom styled avatar card with dynamic attributes theme
                st.markdown(
                    f"""
                    <div style="background: {bg_style}; padding: 25px; border-radius: 15px; border: 2px solid {border_color}; {glow_style} text-align: center;">
                        <span style="font-size: 72px;">{avatar_emoji}</span>
                        <h3 style="color: {text_color};">{clean_form_name}</h3>
                        <p style="color: #A6ADC8; margin-top: -5px;">Stage: <strong>{stage}</strong></p>
                        <div style="background-color: #313244; border-radius: 10px; height: 10px; width: 100%; margin-top: 15px;">
                            <div style="background-color: {border_color}; height: 100%; border-radius: 10px; width: {int(xp_progress * 100)}%;"></div>
                        </div>
                        <small style="color: #BAC2DE;">Level {pet_level} ({pet_xp} / {next_level_xp} XP)</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            with col_pet_stats:
                st.markdown("### Attributes & Energy")
                
                # Stamina
                st.write(f"🔋 **Stamina:** {stamina} / {max_stamina}")
                st.progress(stamina / max_stamina if max_stamina > 0 else 0.0)
                
                # Stats
                st.write(f"🧠 **Intelligence (INT):** {intelligence}")
                st.progress(min(intelligence / 100.0, 1.0))
                
                st.write(f"🎨 **Creativity (CRT):** {creativity}")
                st.progress(min(creativity / 100.0, 1.0))
                
                st.write(f"💪 **Strength (STR):** {strength}")
                st.progress(min(strength / 100.0, 1.0))

            st.divider()
            
            # --- FEED / CARE SECTION ---
            st.markdown("### 🎒 Pet Care & Feed")
            
            pet_inv = get_pet_inventory()
            
            if not pet_inv:
                st.info("Your pet inventory is empty. Buy care items (like Cyber-Protein or Memory Chips) from the XP Store!")
            else:
                inv_cols = st.columns(len(pet_inv))
                for idx, (item, qty) in enumerate(pet_inv):
                    with inv_cols[idx]:
                        with st.container(border=True):
                            st.write(f"**{item}**")
                            st.write(f"Qty: {qty}")
                            if st.button("Use Item", key=f"use_item_btn_{idx}", use_container_width=True):
                                res_msg = use_pet_item(item)
                                st.success(res_msg)
                                st.rerun()
                                
            st.divider()
            
            # --- QUEST ADVENTURE ENGINE ---
            st.markdown("### 🗺️ Choose-Your-Own-Adventure Quests")
            
            # Check if there is an active quest
            if "active_quest" not in st.session_state:
                st.session_state.active_quest = None
            if "quest_hint" not in st.session_state:
                st.session_state.quest_hint = None
                
            if st.session_state.active_quest is None:
                st.write("Send Sparky on an exploration quest to earn extra XP and test its attributes!")
                quest_col1, quest_col2 = st.columns([0.7, 0.3])
                with quest_col1:
                    zone = st.selectbox(
                        "Choose Adventure Zone:",
                        [
                            "📐 The Algebra Ruins (Requires INT)", 
                            "🎨 Maker's Canyon (Requires CRT)", 
                            "🌋 Titan's Forge (Requires STR)"
                        ]
                    )
                with quest_col2:
                    st.write("")
                    st.write("")
                    if st.button("🚀 Embark! (Costs 2 Stamina)", use_container_width=True):
                        if stamina < 2:
                            st.error("Not enough Stamina! Restore stamina by maintaining a task streak or buying Giga-Soda!")
                        else:
                            # Deduct stamina
                            deduct_pet_stamina(pet_id, 2)
                            
                            # Initialize Quest map crawler state
                            st.session_state.active_quest = {
                                "zone": zone,
                                "stat_req": "INT" if "INT" in zone else ("CRT" if "CRT" in zone else "STR"),
                                "stat_val": 15,
                                "current_room": 1,
                                "room_states": {1: "Active", 2: "Locked", 3: "Locked"},
                                "questions": {1: None, 2: None, 3: None}
                            }
                            st.session_state.quest_hint = None
                            st.rerun()
            else:
                quest = st.session_state.active_quest
                st.info(f"📍 Current Zone: **{quest['zone']}**")
                
                # Render Visual Map Grid
                cols_map = st.columns(3)
                room_names = {
                    1: "🚪 Entrance",
                    2: "🧬 Chamber of Trials",
                    3: "👑 Boss Lair"
                }
                
                for r in [1, 2, 3]:
                    state = quest["room_states"][r]
                    with cols_map[r - 1]:
                        if state == "Cleared":
                            st.markdown(
                                f"""
                                <div style="background-color: #0e2b17; border: 2px solid #22c55e; box-shadow: 0 0 10px rgba(34, 197, 94, 0.2); border-radius: 10px; padding: 12px; text-align: center; color: #22c55e; height: 95px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                                    <strong style="font-size: 14px; margin: 0;">✅ Cleared</strong>
                                    <span style="font-size: 12px; color: #a3e635; margin: 0;">{room_names[r]}</span>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        elif state == "Active":
                            st.markdown(
                                f"""
                                <div style="background: linear-gradient(135deg, #1e1e3f 0%, #111126 100%); border: 2px solid #6366f1; box-shadow: 0 0 15px rgba(99, 102, 241, 0.4); border-radius: 10px; padding: 12px; text-align: center; color: #a5b4fc; height: 95px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                                    <strong style="font-size: 14px; margin: 0;">📍 Active</strong>
                                    <span style="font-size: 12px; color: #c7d2fe; margin: 0;">{room_names[r]}</span>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        else: # Locked
                            st.markdown(
                                f"""
                                <div style="background-color: #161622; border: 2px dashed #4b5563; border-radius: 10px; padding: 12px; text-align: center; color: #4b5563; height: 95px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                                    <strong style="font-size: 14px; color: #4b5563; margin: 0;">🔒 Locked</strong>
                                    <span style="font-size: 12px; color: #4b5563; margin: 0;">{room_names[r]}</span>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            
                active_room = quest["current_room"]
                
                # Fetch question dynamically if not cached
                if quest["questions"][active_room] is None:
                    with st.spinner("Floki is crafting a learning challenge for this room... ⚡"):
                        quest["questions"][active_room] = generate_quest_question(quest["zone"], pet_level)
                        
                q_data = quest["questions"][active_room]
                
                room_descriptions = {
                    1: "You push open the heavy stone double doors and step into the entry corridor. A glowing logic barrier blocks the path.",
                    2: "You enter the Chamber of Trials. Swirling elemental energy currents surround a locked vault in the center.",
                    3: "The ground shakes! You face the mighty Guardian of the Zone in the Boss Lair. Solve this final query to conquer the quest!"
                }
                
                st.write("")
                with st.container(border=True):
                    st.subheader(f"{room_names[active_room]}: Encounter")
                    st.write(room_descriptions[active_room])
                    
                    st.divider()
                    st.markdown("#### 🧠 Challenge Question:")
                    st.write(f"💬 **{q_data['question']}**")
                    
                    if st.session_state.quest_hint:
                         st.info(f"💡 **Floki's Socratic Hint:** {st.session_state.quest_hint}")
                         
                    st.write("")
                    
                    choices = q_data["choices"]
                    while len(choices) < 3:
                        choices.append("Option")
                        
                    col_c1, col_c2, col_c3 = st.columns(3)
                    selected_ans = None
                    
                    with col_c1:
                        if st.button(f"🅰️ {choices[0]}", key=f"q_choice_0_{active_room}", use_container_width=True):
                            selected_ans = choices[0]
                    with col_c2:
                        if st.button(f"🅱️ {choices[1]}", key=f"q_choice_1_{active_room}", use_container_width=True):
                            selected_ans = choices[1]
                    with col_c3:
                        if st.button(f"🆃 {choices[2]}", key=f"q_choice_2_{active_room}", use_container_width=True):
                            selected_ans = choices[2]
                            
                    if selected_ans is not None:
                        if selected_ans.strip().lower() == q_data["answer"].strip().lower():
                            # CORRECT ANSWER
                            st.session_state.quest_hint = None
                            
                            stat_gain_str, xp_gain = complete_quest_room(pet_id, active_room, quest["zone"])
                            
                            # Advance Quest Map state
                            quest["room_states"][active_room] = "Cleared"
                            
                            if active_room < 3:
                                quest["current_room"] += 1
                                quest["room_states"][quest["current_room"]] = "Active"
                                st.toast(f"🎉 Correct! Room {active_room} cleared! Sparky gained {xp_gain} XP & {stat_gain_str}")
                                st.rerun()
                            else:
                                st.session_state.active_quest = None
                                st.success(f"🏆 QUEST COMPLETED! Sparky conquered the dungeon and gained {xp_gain} XP!{stat_gain_str}")
                                if st.button("Collect Loot & Finish", use_container_width=True):
                                    st.rerun()
                        else:
                            # INCORRECT ANSWER
                            new_stam = fail_quest_room(pet_id)
                            
                            if new_stam <= 0:
                                st.session_state.active_quest = None
                                st.session_state.quest_hint = None
                                st.error("💥 Sparky ran out of Stamina and became exhausted! The quest failed. Feed Sparky to restore energy.")
                                if st.button("Return to Hub", use_container_width=True):
                                    st.rerun()
                            else:
                                st.session_state.quest_hint = q_data.get("hint", "Try another guess!")
                                st.error(f"❌ Incorrect! Sparky lost 1 energy (Stamina remaining: {new_stam}). Review Floki's hint and try again!")
                                st.rerun()
                                
                if st.button("🏳️ Retreat from Quest", key="retreat_quest_btn", use_container_width=True):
                    st.session_state.active_quest = None
                    st.session_state.quest_hint = None
                    st.rerun()

    with tab_ai:
        st.subheader("💬 Ask Floki: Your AI Learning Buddy")
        st.markdown("*Floki is here to help you study, answer your questions, and coach you through quests!*")
        
        # Display chat history
        session_id = "sonny_study_session"
        chat_logs = get_chat_history(session_id)
        
        for sender, msg, timestamp in chat_logs:
            role = "assistant" if sender == "Floki" else "user"
            with st.chat_message(role):
                st.write(msg)
                
        # API check
        gemini_key = ""
        try:
            if "GEMINI_API_KEY" in st.secrets:
                gemini_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass
        if not gemini_key:
            gemini_key = os.environ.get("GEMINI_API_KEY", "")
            
        # Quick chip buttons
        st.write("💡 *Quick topics:*")
        cols_chips = st.columns(4)
        quick_prompts = [
            ("🧩 Math Helper", "Can you help me understand today's math quest using the Socratic method?"),
            ("🧬 Science Guide", "Tell me how a volcano erupts step-by-step without giving me direct answers!"),
            ("🐉 Boss Fight Tips", "I need coaching and encouragement for my boss fight quest today!"),
            ("🧠 Riddle Time", "Can you give me a Socratic logic riddle to solve?")
        ]
        
        triggered_prompt = ""
        for index, (lbl, text) in enumerate(quick_prompts):
            with cols_chips[index % 4]:
                if st.button(lbl, key=f"quick_prompt_btn_{index}", use_container_width=True):
                    triggered_prompt = text
                    
        # Input Box
        user_input = st.chat_input("Talk to Floki...")
        if triggered_prompt:
            user_input = triggered_prompt
            
        if user_input:
            # 1. Add user message to UI
            with st.chat_message("user"):
                st.write(user_input)
            add_chat_msg(session_id, "Sonny", user_input)
            
            # 2. Call Gemini
            # 2. Call Gemini
            active_persona = get_floki_persona()
            full_history = get_chat_history(session_id)
            
            with st.spinner("Floki is thinking..."):
                floki_reply = ai_tutor.generate_chat_response(full_history, active_persona)
                        
            # 3. Add assistant message to UI
            with st.chat_message("assistant"):
                st.write(floki_reply)
            add_chat_msg(session_id, "Floki", floki_reply)
            st.rerun()
    # --- END NEW ---

# ------------------------------------------
# ADMIN VIEW
# ------------------------------------------
elif user_view == "Dad (Admin)" and not is_admin_authenticated:
    st.title("🔒 Admin Control Center")
    st.info("Please enter the correct passcode in the sidebar to access Dad's Admin Dashboard.")

elif user_view == "Dad (Admin)" and is_admin_authenticated:
    st.title("⚙️ Admin Dashboard")
    
    # --- NEW: Local IP Address and Network Publishing Guidance ---
    import socket
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
            
    local_ip = get_local_ip()
    st.info(
        f"🌐 **Share with Sonny!** Sonny can access this dashboard from his own computer or tablet by opening "
        f"a web browser and going to: `http://{local_ip}:8501` \n\n"
        f"*(Note: Ensure both computers are on the same home Wi-Fi network. You may need to allow port 8501 through Windows Defender Firewall on this computer).* "
    )
    # --- END NEW ---

    render_school_notifications_bar()
    st.write("Welcome to the control center.")
    st.divider()
    
    tab1, tab_cal, tab_proj, tab2, tab3, tab4, tab5, tab_safety = st.tabs(["📝 Add Tasks", "📅 Event Calendar", "🛠️ Creator Projects", "🗂️ Portfolio", "💰 UFA Finances", "🎁 XP Store", "📊 Analytics", "🤖 AI Safety & Settings"])
    
    with tab1:
        st.subheader("Add a New Task for Sonny")
        
        # --- NEW: Quick AI Scheduler ---
        with st.expander("🎙️ Add Task with AI (Natural Language)"):
            st.write("Type your scheduling request below. E.g., *'Add Beast Academy math today for 15 xp'* or *'schedule Outschool Science for tomorrow'*")
            nl_command = st.text_input("AI Scheduler Command", key="nl_scheduler_command")
            if st.button("Schedule Task", key="nl_scheduler_submit"):
                if nl_command.strip() == "":
                    st.warning("Please type a command!")
                else:
                    res_msg = parse_and_execute_schedule_command(nl_command.strip())
                    st.success(res_msg)
                    st.rerun()
        st.write("")
        # --- END NEW ---
        
        with st.form("new_task_form"):
            task_title = st.text_input("Task Description")
            
            task_category = st.selectbox("Finalized 5th Grade Curriculum Spine Selection", [
                "Math (Beast Academy)",
                "Language Arts (Brave Writer)",
                "Science (CrunchLabs)",
                "Science (Outschool)",
                "Social Studies (Tuttle Twins)",
                "Logic (Brilliant.org)",
                "Logic (Synthesis)",
                "Logic (Chess.com)",
                "Logic (Critical Thinking Co.)",
                "Applied STEM (Tech Tails)",
                "Applied STEM (Engineering Proj)"
            ])
            
            task_video = st.text_input("Optional: YouTube Video URL")
            task_xp = st.number_input("XP Reward", min_value=5, max_value=500, value=10, step=5)
            scheduled_date = st.date_input("Scheduled Date", value=date.today())
            is_boss_fight = st.checkbox("⭐ Mark as Daily Boss Fight (Double XP Bonus!)", value=False)
            submitted = st.form_submit_button("Save Task")
            
            if submitted:
                if task_title.strip() == "":
                    st.error("⚠️ Task Description cannot be empty!")
                else:
                    boss_int = 1 if is_boss_fight else 0
                    add_task_to_db(task_title.strip(), task_category, task_video, task_xp, scheduled_date, boss_int)
                    st.success(f"Scheduled for {task_category} on {scheduled_date.strftime('%b %d')}.")
                    st.rerun()

        st.divider()
        st.subheader("📋 Manage Pending Tasks")
        pending_list = get_all_pending_tasks()
        if not pending_list:
            st.info("No pending tasks scheduled.")
        else:
            for t in pending_list:
                t_id, t_title, t_category, t_video, t_xp, t_boss, t_date_str = t
                t_date = datetime.strptime(t_date_str, "%Y-%m-%d").date()
                
                col_t1, col_t2, col_t3 = st.columns([0.6, 0.2, 0.2])
                with col_t1:
                    emoji = SUBJECT_EMOJIS.get(t_category, "📋")
                    boss_label = " 👑 *(Boss Fight!)*" if t_boss == 1 else ""
                    st.markdown(f"**{emoji} {t_category}**: {t_title} (💎 {t_xp} XP){boss_label}  \n*Scheduled Date: {t_date.strftime('%b %d, %Y')}*")
                
                with col_t2:
                    with st.popover("✏️ Edit"):
                        edit_title = st.text_input("Task Description", value=t_title, key=f"edit_task_title_{t_id}")
                        edit_category = st.selectbox(
                            "Curriculum Spine",
                            options=list(SUBJECT_EMOJIS.keys()),
                            index=list(SUBJECT_EMOJIS.keys()).index(t_category) if t_category in SUBJECT_EMOJIS else 0,
                            key=f"edit_task_cat_{t_id}"
                        )
                        edit_video = st.text_input("YouTube Video URL", value=t_video or "", key=f"edit_task_vid_{t_id}")
                        edit_xp = st.number_input("XP Reward", min_value=5, max_value=500, value=int(t_xp), step=5, key=f"edit_task_xp_{t_id}")
                        edit_date = st.date_input("Scheduled Date", value=t_date, key=f"edit_task_date_{t_id}")
                        edit_boss = st.checkbox("Mark as Daily Boss Fight", value=(t_boss == 1), key=f"edit_task_boss_{t_id}")
                        
                        if st.button("Save Changes", key=f"save_task_btn_{t_id}"):
                            if edit_title.strip() == "":
                                st.error("Task Description cannot be empty!")
                            else:
                                update_task_details(t_id, edit_title.strip(), edit_category, edit_video, edit_xp, edit_date, 1 if edit_boss else 0)
                                st.success("Task updated successfully!")
                                st.rerun()
                
                with col_t3:
                    with st.popover("❌ Delete"):
                        st.write("Are you sure you want to delete this task?")
                        if st.button("Confirm Delete", key=f"del_task_btn_{t_id}"):
                            delete_task(t_id)
                            st.success("Task deleted!")
                            st.rerun()
                
    with tab_cal:
        st.subheader("📅 School Event & Academic Calendar Manager")
        st.write("Schedule upcoming school start dates, live online classes, kit delivery dates, field trips, and UFA compliance milestones.")
        
        with st.form("new_school_event_form"):
            col_e1, col_e2 = st.columns([0.6, 0.4])
            with col_e1:
                ev_title_in = st.text_input("Event Title (e.g. 'First Day of School', 'Science Fair Prep')")
            with col_e2:
                ev_category_in = st.selectbox("Category", [
                    "🎓 School Start / Term",
                    "🎥 Live Class (Outschool)",
                    "🛠️ Kit Delivery / Project",
                    "🏛️ Field Trip",
                    "💰 UFA Milestone",
                    "📝 Exam / Assessment",
                    "📌 General"
                ])
                
            col_e3, col_e4, col_e5 = st.columns([0.35, 0.35, 0.3])
            with col_e3:
                ev_date_in = st.date_input("Event Date", value=date.today())
            with col_e4:
                ev_time_in = st.text_input("Optional Time (e.g. '08:30 AM')", value="")
            with col_e5:
                ev_importance_in = st.selectbox("Importance / Priority", ["Normal", "Important", "Urgent"], index=0)
                
            col_e6, col_e7 = st.columns([0.3, 0.7])
            with col_e6:
                ev_reminder_in = st.selectbox("Notification Lead Time", [
                    (0, "Day of Event (0 days)"),
                    (1, "1 Day Before"),
                    (2, "2 Days Before"),
                    (3, "3 Days Before"),
                    (5, "5 Days Before"),
                    (7, "1 Week Before"),
                    (14, "2 Weeks Before")
                ], format_func=lambda x: x[1], index=3)[0]
            with col_e7:
                ev_desc_in = st.text_input("Description / Notes (Optional)", value="")
                
            submitted_event = st.form_submit_button("➕ Schedule Event")
            if submitted_event:
                if ev_title_in.strip() == "":
                    st.error("⚠️ Event Title cannot be empty!")
                else:
                    add_school_event(
                        title=ev_title_in.strip(),
                        event_date=ev_date_in,
                        event_time=ev_time_in.strip(),
                        category=ev_category_in,
                        importance=ev_importance_in,
                        reminder_days=ev_reminder_in,
                        description=ev_desc_in.strip()
                    )
                    st.success(f"Event '{ev_title_in}' scheduled for {ev_date_in.strftime('%b %d, %Y')}!")
                    st.rerun()

        st.divider()
        st.subheader("📋 Manage Scheduled Events")
        
        all_dad_events = get_school_events()
        if not all_dad_events:
            st.info("No school events currently scheduled.")
        else:
            for ev in all_dad_events:
                ev_id, ev_title, ev_date_str, ev_time, ev_cat, ev_imp, ev_rem, ev_desc, _ = ev
                ev_date_obj = datetime.strptime(ev_date_str, "%Y-%m-%d").date()
                
                col_ev1, col_ev2, col_ev3 = st.columns([0.65, 0.18, 0.17])
                with col_ev1:
                    imp_badge = "🔴 Urgent" if ev_imp == "Urgent" else ("🟠 Important" if ev_imp == "Important" else "🔵 Normal")
                    time_info = f" at {ev_time}" if ev_time else ""
                    st.markdown(f"**{ev_title}** ({ev_cat}) - {imp_badge}  \n*Date: {ev_date_obj.strftime('%b %d, %Y')}{time_info} (Alert {ev_rem} days before)*")
                    if ev_desc:
                        st.caption(f"📝 {ev_desc}")
                        
                with col_ev2:
                    with st.popover("✏️ Edit"):
                        e_title = st.text_input("Title", value=ev_title, key=f"edit_ev_title_{ev_id}")
                        cat_opts = [
                            "🎓 School Start / Term",
                            "🎥 Live Class (Outschool)",
                            "🛠️ Kit Delivery / Project",
                            "🏛️ Field Trip",
                            "💰 UFA Milestone",
                            "📝 Exam / Assessment",
                            "📌 General"
                        ]
                        e_cat = st.selectbox("Category", cat_opts, index=cat_opts.index(ev_cat) if ev_cat in cat_opts else 0, key=f"edit_ev_cat_{ev_id}")
                        e_date = st.date_input("Date", value=ev_date_obj, key=f"edit_ev_date_{ev_id}")
                        e_time = st.text_input("Time", value=ev_time or "", key=f"edit_ev_time_{ev_id}")
                        imp_opts = ["Normal", "Important", "Urgent"]
                        e_imp = st.selectbox("Importance", imp_opts, index=imp_opts.index(ev_imp) if ev_imp in imp_opts else 0, key=f"edit_ev_imp_{ev_id}")
                        e_rem = st.number_input("Reminder Lead Days", min_value=0, max_value=30, value=int(ev_rem), step=1, key=f"edit_ev_rem_{ev_id}")
                        e_desc = st.text_area("Description", value=ev_desc or "", key=f"edit_ev_desc_{ev_id}")
                        
                        if st.button("Save Changes", key=f"save_ev_btn_{ev_id}"):
                            if e_title.strip() == "":
                                st.error("Title cannot be empty!")
                            else:
                                update_school_event(ev_id, e_title.strip(), e_date, e_time.strip(), e_cat, e_imp, e_rem, e_desc.strip())
                                st.success("Event updated!")
                                st.rerun()
                                
                with col_ev3:
                    with st.popover("❌ Delete"):
                        st.write("Delete this school event?")
                        if st.button("Confirm Delete", key=f"del_ev_btn_{ev_id}"):
                            delete_school_event(ev_id)
                            st.success("Event deleted!")
                            st.rerun()

    with tab_proj:
        st.subheader("Launch a New Creator Block Project")
        st.write("Deploy physical kits (like CrunchLabs or Build Box) here. These projects stay active on Sonny's dashboard until he officially marks them as fully built, granting him a massive XP bounty.")
        
        with st.form("new_project_form"):
            proj_title = st.text_input("Project Name (e.g., 'Disc Launcher', 'Mars Rover')")
            proj_platform = st.selectbox("Platform / Kit Source", ["CrunchLabs", "Annual Build Box", "Tech Tails", "Custom Engineering Project"])
            proj_xp = st.number_input("Completion XP Bounty", min_value=50, max_value=5000, value=200, step=50)
            submitted_proj = st.form_submit_button("Deploy Project to Sonny's Dashboard")
            
            if submitted_proj:
                if proj_title.strip() == "":
                    st.error("⚠️ Project Name cannot be empty!")
                else:
                    add_creator_project(proj_title.strip(), proj_platform, proj_xp)
                    st.success(f"Project '{proj_title}' successfully launched!")
                    st.rerun()

        st.divider()
        st.subheader("🛠️ Manage Creator Projects")
        
        all_projs = get_all_creator_projects()
        
        if not all_projs:
            st.info("No creator projects found.")
        else:
            for p in all_projs:
                p_id, p_title, p_platform, p_xp, p_status, p_comp_date, p_summary, p_attach = p
                
                col_p1, col_p2, col_p3 = st.columns([0.6, 0.2, 0.2])
                with col_p1:
                    status_badge = "🟢 Completed" if p_status == "Completed" else "⏳ In Progress"
                    st.markdown(f"**{p_title}** ({p_platform}) - 💎 {p_xp} XP  \n*Status: {status_badge}*")
                    if p_status == "Completed":
                        st.markdown(f"*Completed on: {p_comp_date}*")
                
                with col_p2:
                    with st.popover("✏️ Edit"):
                        edit_p_title = st.text_input("Project Name", value=p_title, key=f"edit_proj_title_{p_id}")
                        edit_p_platform = st.selectbox(
                            "Platform / Kit Source",
                            options=["CrunchLabs", "Annual Build Box", "Tech Tails", "Custom Engineering Project"],
                            index=["CrunchLabs", "Annual Build Box", "Tech Tails", "Custom Engineering Project"].index(p_platform) if p_platform in ["CrunchLabs", "Annual Build Box", "Tech Tails", "Custom Engineering Project"] else 0,
                            key=f"edit_proj_plat_{p_id}"
                        )
                        edit_p_xp = st.number_input("XP Bounty", min_value=10, max_value=5000, value=int(p_xp), step=50, key=f"edit_proj_xp_{p_id}")
                        edit_p_status = st.selectbox("Status", ["In Progress", "Completed"], index=0 if p_status == "In Progress" else 1, key=f"edit_proj_status_{p_id}")
                        
                        if st.button("Save Changes", key=f"save_proj_btn_{p_id}"):
                            if edit_p_title.strip() == "":
                                st.error("Project Name cannot be empty!")
                            else:
                                update_creator_project(
                                    p_id, edit_p_title.strip(), edit_p_platform, edit_p_xp, 
                                    status=edit_p_status, completion_date=p_comp_date if edit_p_status == "Completed" else "", 
                                    project_summary=p_summary, project_attachment=p_attach
                                )
                                st.success("Project updated!")
                                st.rerun()
                
                with col_p3:
                    with st.popover("❌ Delete"):
                        st.write("Are you sure you want to delete this project?")
                        if st.button("Confirm Delete", key=f"del_proj_btn_{p_id}"):
                            delete_creator_project(p_id)
                            st.success("Project deleted!")
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
                    
                    if task[6] and task[6].strip() != "":
                        st.info(f"💭 **Sonny's Notes:** {task[6]}")
                    
                with col2:
                    if st.button("❌", key=f"del_task_{task[0]}"):
                        delete_task(task[0])
                        st.rerun()
                        
        admin_completed_projects = get_completed_projects(portfolio_date)
        if len(admin_completed_projects) > 0:
            st.markdown("### 🛠️ Completed Creator Projects")
            for proj in admin_completed_projects:
                st.markdown(f"✅ **{proj[2]}**: {proj[1]} *(💎 {proj[3]} XP)*")
                if proj[4] and proj[4].strip() != "":
                    st.info(f"💭 **Sonny's Project Notes:** {proj[4]}")
                
                # --- NEW: Render Attachment in Portfolio Review ---
                if len(proj) > 5 and proj[5] and proj[5].strip() != "":
                    file_path = proj[5]
                    if os.path.exists(file_path):
                        ext = os.path.splitext(file_path)[1].lower()
                        if ext in [".png", ".jpg", ".jpeg"]:
                            st.image(file_path, caption=f"📸 Uploaded Image for {proj[1]}", use_container_width=True)
                        elif ext in [".mp4", ".mov"]:
                            st.video(file_path)
                        else:
                            try:
                                with open(file_path, "rb") as f:
                                    file_bytes = f.read()
                                fn = os.path.basename(file_path)
                                st.download_button(
                                    label=f"📎 Download Attachment: {fn}",
                                    data=file_bytes,
                                    file_name=fn,
                                    key=f"download_attachment_{proj[0]}"
                                )
                            except Exception as e:
                                st.error(f"Could not load attachment file: {file_path}")
                    else:
                        st.warning(f"⚠️ Attachment file not found: {file_path}")
                # --- END NEW ---
                    
        st.divider()
        st.markdown("### 🖨️ Official Portfolio Export")
        st.write("Generate a complete, compliance-ready CSV report of all completed tasks and projects.")
        
        # --- NEW: Implement Date Range Calendar Layout selectors ---
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            export_start = st.date_input("📅 Report Start Date:", value=date.today() - timedelta(days=30))
        with r_col2:
            export_end = st.date_input("📅 Report End Date:", value=date.today())
            
        # Pass calendar choices into our updated range data-fetcher function
        portfolio_df = get_full_portfolio_data(export_start, export_end)
        # --- END NEW ---
        
        if portfolio_df.empty:
            st.info("No completed assignments found matching this specific date window.")
        else:
            csv_data = portfolio_df.to_csv(index=False).encode('utf-8')
            
            # Dynamic naming maps window to filename for easy file tracking
            start_fn = export_start.strftime('%Y_%m_%d')
            end_fn = export_end.strftime('%Y_%m_%d')
            
            st.download_button(
                label=f"📥 Download Portfolio Range ({start_fn} to {end_fn})",
                data=csv_data,
                file_name=f"Flokus_Portfolio_{start_fn}_to_{end_fn}.csv",
                mime="text/csv",
                use_container_width=True
            )

    with tab3:
        expenses = get_all_expenses()
        df_expenses_export = pd.DataFrame(expenses, columns=["ID", "Item Name", "Cost", "Category", "Status"])
        if not df_expenses_export.empty:
            df_expenses_export = df_expenses_export.drop(columns=["ID"])

        col_title, col_export = st.columns([0.7, 0.3])
        with col_title:
            st.subheader("Utah Fits All (UFA) Budget Tracker")
        with col_export:
            if not df_expenses_export.empty:
                csv_data = df_expenses_export.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Expenses to CSV",
                    data=csv_data,
                    file_name="Flokus_UFA_Expenses.csv",
                    mime="text/csv",
                    key="export_expenses_csv",
                    use_container_width=True
                )
                
        total_budget = 4000.00
        total_spent = sum([expense[2] for expense in expenses if expense[4] != "Out of Pocket (Not UFA)"])
        remaining_budget = total_budget - total_spent
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total UFA Grant", f"${total_budget:,.2f}")
        col2.metric("Total Spent", f"${total_spent:,.2f}")
        col3.metric("Remaining Funds", f"${remaining_budget:,.2f}")

        # --- NEW: Budget Alerts ---
        if remaining_budget < 600.00:
            st.error(f"⚠️ **Low Funds Warning!** Remaining UFA budget is ${remaining_budget:,.2f} (under 15%). Plan purchases carefully!")
        elif remaining_budget < 1200.00:
            st.warning(f"⚠️ **Budget Alert:** Remaining UFA budget is ${remaining_budget:,.2f} (under 30%).")
        # --- END NEW ---

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

        # --- NEW: Financial Charts Section ---
        if not df_expenses_export.empty:
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                st.markdown("#### 📊 UFA Budget Spent by Category")
                df_cat_totals = df_expenses_export[df_expenses_export["Status"] != "Out of Pocket (Not UFA)"].groupby("Category")["Cost"].sum().reset_index()
                if not df_cat_totals.empty:
                    df_cat_totals = df_cat_totals.set_index("Category")
                    st.bar_chart(df_cat_totals)
                else:
                    st.info("No UFA expenses logged yet.")
            with chart_col2:
                st.markdown("#### ⏳ Spent by Status Pipeline")
                df_status_totals = df_expenses_export.groupby("Status")["Cost"].sum().reset_index()
                if not df_status_totals.empty:
                    df_status_totals = df_status_totals.set_index("Status")
                    st.bar_chart(df_status_totals)
                else:
                    st.info("No expenses logged yet.")
            st.divider()
        # --- END NEW ---
        
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
            if submit_expense:
                if item_name.strip() == "":
                    st.error("⚠️ Item/Service Name cannot be empty!")
                else:
                    add_expense(item_name.strip(), cost, category, status)
                    st.success("Expense logged successfully!")
                    st.rerun()

        st.write("**Expense History**")
        if len(expenses) == 0:
            st.info("No expenses logged yet.")
        else:
            for exp in expenses:
                col_exp1, col_exp2, col_exp3 = st.columns([0.5, 0.3, 0.2])
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
                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        with st.popover("✏️"):
                            edit_exp_name = st.text_input("Item Name", value=exp[1], key=f"edit_exp_name_{exp[0]}")
                            edit_exp_cost = st.number_input("Cost ($)", min_value=0.00, value=float(exp[2]), format="%.2f", key=f"edit_exp_cost_{exp[0]}")
                            edit_exp_cat = st.selectbox(
                                "Category",
                                options=["Curriculum & Workbooks", "Technology/Hardware", "Extracurricular/Classes", "Supplies & Materials"],
                                index=["Curriculum & Workbooks", "Technology/Hardware", "Extracurricular/Classes", "Supplies & Materials"].index(exp[3]) if exp[3] in ["Curriculum & Workbooks", "Technology/Hardware", "Extracurricular/Classes", "Supplies & Materials"] else 0,
                                key=f"edit_exp_cat_{exp[0]}"
                            )
                            edit_exp_status = st.selectbox(
                                "Status",
                                options=status_options,
                                index=current_status_idx,
                                key=f"edit_exp_status_{exp[0]}"
                            )
                            if st.button("Save", key=f"save_exp_{exp[0]}"):
                                if edit_exp_name.strip() == "":
                                    st.error("Name cannot be empty!")
                                else:
                                    update_expense_details(exp[0], edit_exp_name.strip(), edit_exp_cost, edit_exp_cat, edit_exp_status)
                                    st.success("Expense updated!")
                                    st.rerun()
                    with col_del:
                        with st.popover("❌"):
                            st.write("Delete this expense?")
                            if st.button("Confirm", key=f"del_exp_confirm_{exp[0]}"):
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
                    if edited_cost != reward_cost or edited_qty != reward_qty:
                        if st.button("💾 Save", key=f"save_rew_{reward_id}"):
                            update_reward_details(reward_id, edited_cost, edited_qty)
                            st.rerun()
                    else:
                        if st.button("❌", key=f"del_reward_{reward_id}"):
                            delete_reward(reward_id)
                            st.rerun()
                        
        st.divider()
        st.subheader("🎟️ Claimed & Pending Rewards Log")
        st.caption("Approve and track Sonny's real-world reward claims.")
        
        purchases_list = get_all_purchases()
        
        if len(purchases_list) == 0:
            st.info("Sonny hasn't purchased any rewards yet.")
        else:
            for p_id, r_name, cost, p_date, is_claimed in purchases_list:
                col_p1, col_p2, col_p3 = st.columns([0.5, 0.3, 0.2])
                with col_p1:
                    status_emoji = "✅" if is_claimed == 1 else "⏳"
                    st.markdown(f"{status_emoji} **{r_name}** — 💎 {cost} XP")
                    st.caption(f"Purchased: {p_date}")
                with col_p2:
                    if is_claimed == 1:
                        st.markdown("<span style='color: #48bb78; font-weight: bold;'>Claimed</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='color: #ed8936; font-weight: bold;'>Pending Claim</span>", unsafe_allow_html=True)
                with col_p3:
                    if is_claimed == 0:
                        if st.button("Mark Claimed", key=f"claim_btn_{p_id}", use_container_width=True):
                            mark_purchase_claimed(p_id)
                            st.success(f"Approved claim: {r_name}!")
                            st.rerun()

    with tab5:
        st.subheader("📊 Flokus Learning Insights")
        st.write("Real-time telemetry showing study distribution and total XP momentum.")
        st.divider()

        st.markdown("### 🗓️ 7-Day Activity Radar")
        st.caption("Visual confirmation tracker checking if assignments were cleared each day.")
        
        today_dt = date.today()
        day_cols = st.columns(7)
        
        active_dates = get_active_task_dates()
        
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
            st.caption("Distribution of completed milestones across all 11 curriculum platforms.")
            
            # --- NEW: Integrated Multi-Table Curriculum Analytics Engine ---
            # Extract completions from standard daily tasks
            stats_tasks = get_task_completion_stats()
            df_t = pd.DataFrame(stats_tasks, columns=["Subject", "Completed"]) if stats_tasks else pd.DataFrame(columns=["Subject", "Completed"])
            
            # Extract completions from physical creator block builds
            df_p = get_completed_projects_by_platform()
            
            # Merge both sources into a unified metrics array
            df_all_stats = pd.concat([df_t, df_p], ignore_index=True)
            
            if not df_all_stats.empty:
                df_all_stats = df_all_stats.groupby("Subject")["Completed"].sum().reset_index()
                
            # Generate static template from your 11 locked-in categories 
            master_spine = list(SUBJECT_EMOJIS.keys())
            spine_map = {platform: 0 for platform in master_spine}
            
            # Map database tracking rows cleanly over our 11 categories
            if not df_all_stats.empty:
                for _, row in df_all_stats.iterrows():
                    if row["Subject"] in spine_map:
                        spine_map[row["Subject"]] = int(row["Completed"])
            
            # Convert dictionary back to a structured DataFrame for rendering
            df_master_analytics = pd.DataFrame(list(spine_map.items()), columns=["Subject", "Completed Milestones"])
            df_master_analytics = df_master_analytics.set_index("Subject")
            
            total_focus_mins = get_total_focus_minutes()
            
            # --- NEW: Calculate Autonomy vs. Rollover Telemetry Metrics ---
            total_done_tasks, on_time_tasks = get_autonomy_metrics()
            
            # Compute operational percentage rating
            autonomy_score = int((on_time_tasks / total_done_tasks) * 100) if total_done_tasks > 0 else 100
            
            # Render side-by-side behavioral metrics
            kpi_col1, kpi_col2 = st.columns(2)
            with kpi_col1:
                st.metric(label="⌛ Total Deep Work Focus Time", value=f"{total_focus_mins} Minutes")
            with kpi_col2:
                st.metric(label="🎯 On-Schedule Completion Rating", value=f"{autonomy_score}%")
            st.write("")
            # --- END NEW ---
            
            # Plot the finalized telemetry bar chart
            if df_master_analytics["Completed Milestones"].sum() == 0:
                st.info("📊 Telemetry offline. Complete daily quests or building projects to activate tracking!")
            else:
                st.bar_chart(df_master_analytics)
                
                # --- NEW: Live Rank Progression Leaderboard ---
                st.write("")
                st.markdown("#### 🏆 Platform Mastery Ranks")
                
                # Iterate through the calculated rows to assign gamified ranks
                for platform, row in df_master_analytics.iterrows():
                    count = int(row["Completed Milestones"])
                    
                    if count == 0:
                        rank_title = "Locked"
                        badge = "⚪"
                    elif count < 10:
                        rank_title = "Apprentice"
                        badge = "🥉"
                    elif count < 30:
                        rank_title = "Journeyman"
                        badge = "🥈"
                    elif count < 50:
                        rank_title = "Expert"
                        badge = "🥇"
                    else:
                        rank_title = "Grandmaster"
                        badge = "👑"
                        
                    # Draw a nice scannable status line for each platform
                    st.markdown(f"{badge} **{platform}** — {rank_title} *(Total: {count} Milestones)*")
                # --- END NEW ---

        with col_chart2:
            st.markdown("### 🧭 Maturity Block Balance")
            st.caption("Volume split of completed milestones across daily learning blocks.")
            
            # --- NEW: Maturity Block Distribution Chart Logic ---
            if df_master_analytics["Completed Milestones"].sum() == 0:
                st.info("🧭 Balance metrics offline until milestones are checked.")
            else:
                # Map our 11 platforms into their specific structural modes
                block_mapping = {
                    "Math (Beast Academy)": "Deep Work 🧠",
                    "Language Arts (Brave Writer)": "Deep Work 🧠",
                    "Logic (Brilliant.org)": "Deep Work 🧠",
                    "Logic (Synthesis)": "Deep Work 🧠",
                    "Logic (Chess.com)": "Deep Work 🧠",
                    "Logic (Critical Thinking Co.)": "Deep Work 🧠",
                    "Science (CrunchLabs)": "Creator Block 🛠️",
                    "Applied STEM (Tech Tails)": "Creator Block 🛠️",
                    "Applied STEM (Engineering Proj)": "Creator Block 🛠️",
                    "Science (Outschool)": "World Discovery 🗺️",
                    "Social Studies (Tuttle Twins)": "World Discovery 🗺️"
                }
                
                # Copy our main dataset and map categories over to their parent blocks
                df_balance = df_master_analytics.reset_index()
                df_balance["Block"] = df_balance["Subject"].map(block_mapping)
                
                # Aggregate total completions for each parent block grouping
                df_block_totals = df_balance.groupby("Block")["Completed Milestones"].sum().reset_index()
                df_block_totals = df_block_totals.set_index("Block")
                
                # Render a balanced pie/bar representation of our parent educational tracking modes
                st.bar_chart(df_block_totals)
                
            st.divider()
            st.markdown("### 📈 All-Time XP Progress")
            st.caption("Sonny's cumulative milestone progress curve over time.")
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
            # --- END NEW ---

    # --- NEW: Admin AI Safety & Settings Tab ---
    with tab_safety:
        st.subheader("🤖 AI Safety & Settings")
        
        st.markdown("### 📜 Sonny's Chat Transcripts")
        st.caption("Review recent Socratic dialogues between Sonny and Floki.")
        
        session_id = "sonny_study_session"
        chat_logs = get_chat_history(session_id)
        if len(chat_logs) == 0:
            st.info("No chat logs recorded yet.")
        else:
            # Display chat logs in a scrollable container
            chat_text = ""
            for sender, msg, timestamp in chat_logs:
                chat_text += f"[{timestamp}] {sender}: {msg}\n"
                chat_text += "-" * 40 + "\n"
            st.text_area("Full Chat Transcript", chat_text, height=300, disabled=True)
            
            # Button to clear chat history
            if st.button("🧹 Clear Chat History", key="clear_chat_history_btn"):
                clear_chat_history(session_id)
                st.success("Chat history cleared!")
                st.rerun()
                
        # --- NEW: Floki Persona Configuration ---
        st.divider()
        st.markdown("### 🎭 Floki Persona Configuration")
        st.caption("Change Floki's personality to keep Sonny engaged with different teaching styles.")
        current_p = get_floki_persona()
        selected_p = st.selectbox(
            "Active Persona",
            ["Socratic Tutor", "Norse Boatbuilder", "Space Robot"],
            index=["Socratic Tutor", "Norse Boatbuilder", "Space Robot"].index(current_p) if current_p in ["Socratic Tutor", "Norse Boatbuilder", "Space Robot"] else 0
        )
        if selected_p != current_p:
            set_floki_persona(selected_p)
            st.success(f"Floki's persona updated to {selected_p}!")
            st.rerun()
        # --- END NEW ---

        # --- NEW: One-Click Database Backups & Reset ---
        st.divider()
        st.markdown("### 📦 Database Management & Go-Live Prep")
        st.caption("Manage database backups or clear test data before launching.")
        
        db_col1, db_col2 = st.columns(2)
        with db_col1:
            try:
                with open("flokus.db", "rb") as f:
                    db_bytes = f.read()
            except Exception:
                db_bytes = b""
                
            if db_bytes:
                st.download_button(
                    label="📥 Backup flokus.db",
                    data=db_bytes,
                    file_name=f"flokus_backup_{date.today().strftime('%Y_%m_%d')}.db",
                    mime="application/x-sqlite3",
                    use_container_width=True
                )
            else:
                st.error("Failed to read database file.")
                
        with db_col2:
            with st.popover("🧹 Clear Test Data & Go Live", use_container_width=True):
                st.warning("⚠️ **Warning:** This will permanently erase test tasks, test creator builds, purchase logs, chat history, and reset Sparky & UFA expenses back to baseline defaults!")
                if st.button("🔴 Confirm Reset All Data", key="confirm_reset_all_data_btn", use_container_width=True):
                    database.reset_all_test_data()
                    st.success("🎉 Database reset complete! App is ready for live use.")
                    st.rerun()
        # --- END NEW ---
                
        st.divider()
        st.markdown("### 🐾 Pet Override Console")
        st.caption("Manually adjust Sparky's levels or statistics for testing or corrections.")
        
        pet = get_pet_status()
        if pet:
            pet_id, pet_name, pet_level, pet_xp, strength, intelligence, creativity, stamina, max_stamina, happiness, stage, form_name, accessory_parts = pet
            
            with st.form("pet_override_form"):
                new_name = st.text_input("Override Pet Name", value=pet_name)
                new_level = st.number_input("Override Level", min_value=1, max_value=100, value=pet_level)
                new_xp = st.number_input("Override Current XP", min_value=0, value=pet_xp)
                new_str = st.number_input("Override Strength", min_value=1, value=strength)
                new_int = st.number_input("Override Intelligence", min_value=1, value=intelligence)
                new_crt = st.number_input("Override Creativity", min_value=1, value=creativity)
                new_stamina = st.number_input("Override Stamina", min_value=0, max_value=100, value=stamina)
                new_max_stamina = st.number_input("Override Max Stamina", min_value=1, max_value=100, value=max_stamina)
                
                # Stage selection
                stage_options = ["Egg", "Baby", "Rookie", "Champion", "Ultimate", "Mega"]
                new_stage = st.selectbox("Override Stage", stage_options, index=stage_options.index(stage) if stage in stage_options else 0)
                new_form_name = st.text_input("Override Form Name", value=form_name)
                
                if st.form_submit_button("Save Override Changes"):
                    override_pet_status(pet_id, new_name, new_level, new_xp, new_str, new_int, new_crt, new_stamina, new_max_stamina, new_stage, new_form_name)
                    st.success("Pet overridden successfully!")
                    st.rerun()