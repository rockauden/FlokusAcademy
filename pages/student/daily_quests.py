import streamlit as st
import time
from datetime import date, datetime, timedelta
import database
import config
from ui.components import render_school_notifications_bar, render_focus_timer

# Handle session state for celebration balloons
if 'show_balloons' not in st.session_state:
    st.session_state.show_balloons = False

if st.session_state.show_balloons:
    st.balloons()
    st.session_state.show_balloons = False

# Render top notification banner
render_school_notifications_bar()

# UI View Mode (Beta Progressive Disclosure vs Classic)
if "quest_view_mode" not in st.session_state:
    # Default to beta if query param ui=beta, else beta view by default for clean UX
    url_ui = st.query_params.get("ui")
    st.session_state.quest_view_mode = "Beta Focus UI" if (url_ui == "beta" or url_ui is None) else "Classic View"

def render_beta_dashboard():
    """Experimental UI testing progressive disclosure and tabbed daily focus."""
    
    # 1. The "Backpack" (Sidebar for external links and non-daily tasks/events)
    with st.sidebar:
        st.header("🎒 Sonny's Backpack")
        st.caption("Quick Links & Resources")
        
        # Featured Platform Links
        for category, url in config.PLATFORM_LINKS.items():
            if url:
                emoji = config.SUBJECT_EMOJIS.get(category, "🔗")
                platform_name = category.split("(")[-1].replace(")", "") if "(" in category else category
                st.markdown(f"[{emoji} {platform_name}]({url})")
                
        st.divider()
        
        # Next major school event notification
        next_event = database.get_next_major_school_event()
        if next_event:
            ev_title = next_event.get("title", "")
            ev_date_str = next_event.get("event_date_str", "")
            days_left = next_event.get("days_left", 0)
            try:
                dt_obj = datetime.strptime(str(ev_date_str), "%Y-%m-%d").date()
                formatted_ev_date = dt_obj.strftime("%b %d")
            except Exception:
                formatted_ev_date = str(ev_date_str)
            st.markdown(f"**Upcoming Event:**  \n📅 **{ev_title}** ({formatted_ev_date} - {days_left}d left)")
        else:
            st.markdown("**Upcoming:** CrunchLabs Build Day (This Friday!)")
            
        st.divider()
        st.caption("UI Preferences")
        if st.button("Switch to Classic View"):
            st.session_state.quest_view_mode = "Classic View"
            st.query_params["ui"] = "classic"
            st.rerun()

    # 2. Today & Momentum Header
    today = date.today()
    current_weekday_idx = today.weekday() # 0 = Monday, 4 = Friday, 5 = Sat, 6 = Sun
    day_name = today.strftime("%A")
    
    pending_today = database.get_pending_tasks(today)
    completed_today = database.get_completed_tasks(today)
    total_today = len(pending_today) + len(completed_today)
    progress_percentage = (len(completed_today) / total_today) if total_today > 0 else 0.0
    daily_xp_today = sum([t[4] * 2 if t[5] == 1 else t[4] for t in completed_today])

    st.title("🎓 Sonny's Learning Hub")
    
    col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1])
    with col1:
        st.subheader(f"Happy {day_name}, Sonny! 🚀")
        st.caption(f"Today is {today.strftime('%B %d, %Y')}")
    with col2:
        st.metric("Tasks Completed", f"{len(completed_today)} / {total_today}")
    with col3:
        st.metric("Today's XP", f"💎 {daily_xp_today}")
    with col4:
        st.metric("Daily Streak", f"🔥 {database.get_daily_streak()} Days")
        
    st.progress(progress_percentage, text=f"Daily Quest Progress ({int(progress_percentage * 100)}%)")
    st.divider()

    # 3. The "Today" Focus (Tabs for Mon-Fri of Current Week)
    monday_start = today - timedelta(days=current_weekday_idx)
    week_dates = [monday_start + timedelta(days=i) for i in range(5)]
    week_day_labels = [
        f"Monday ({week_dates[0].strftime('%b %d')})",
        f"Tuesday ({week_dates[1].strftime('%b %d')})",
        f"Wednesday ({week_dates[2].strftime('%b %d')})",
        f"Thursday ({week_dates[3].strftime('%b %d')})",
        f"Friday ({week_dates[4].strftime('%b %d')})"
    ]
    
    # If weekend (Sat/Sun index 5-6), default to Monday (tab 0)
    default_tab_index = current_weekday_idx if current_weekday_idx < 5 else 0
    
    tabs = st.tabs(week_day_labels)
    
    for i, tab in enumerate(tabs):
        tab_date = week_dates[i]
        is_today_tab = (tab_date == today)
        
        with tab:
            st.markdown(f"### 📋 Missions for {tab_date.strftime('%A, %B %d')}")
            
            pending_list = database.get_pending_tasks(tab_date)
            completed_list = database.get_completed_tasks(tab_date)
            
            if len(pending_list) == 0 and len(completed_list) == 0:
                st.info(f"🎉 No missions scheduled for {tab_date.strftime('%A')}! Enjoy your free time or add a new task.")
            else:
                if len(pending_list) > 0:
                    st.write("**Up Next:**")
                    for task in pending_list:
                        task_id, task_title, task_category, task_video_url, task_xp, is_boss = task[0:6]
                        task_medium = task[6] if len(task) > 6 else "Offline"
                        emoji = config.SUBJECT_EMOJIS.get(task_category, "📋")
                        med_badge = "📖 Offline" if task_medium == "Offline" else "💻 Online"
                        
                        expander_title = f"{emoji} {task_category}: {task_title} [{med_badge}] (💎 {task_xp * 2 if is_boss == 1 else task_xp} XP)"
                        if is_boss == 1:
                            expander_title = f"👑 BOSS FIGHT: {expander_title}"
                            
                        # Progressive disclosure expander
                        with st.expander(expander_title, expanded=is_today_tab):
                            if is_boss == 1:
                                st.markdown('<div class="boss-fight-marker"></div>', unsafe_allow_html=True)
                                st.markdown("👑 **DAILY BOSS FIGHT - DOUBLE XP CHALLENGE!** 👑")
                                
                            st.write(f"**Mission:** {task_title}")
                            
                            col_exp1, col_exp2 = st.columns([0.7, 0.3])
                            with col_exp1:
                                st.write(f"**Category:** {task_category} | **Medium:** `{med_badge}`")
                            with col_exp2:
                                launch_url = config.PLATFORM_LINKS.get(task_category, "")
                                if launch_url:
                                    st.markdown(f"[🚀 Launch {task_category.split('(')[0]}]({launch_url})")
                                    
                            if task_video_url:
                                st.markdown("##### 📺 Lesson Video")
                                st.video(task_video_url)
                                
                            render_focus_timer(task_id)
                            
                            note_input = st.text_input(
                                "✏️ What did you learn or read? (Add a summary note here before checking complete)",
                                key=f"beta_note_input_{task_id}"
                            )
                            
                            is_checked = st.checkbox("Mark Mission Complete", key=f"beta_task_chk_{task_id}")
                            
                            if is_checked:
                                if len(note_input.strip()) < 15:
                                    st.warning(f"⚠️ Note is too short! Write at least 15 characters about what you learned. (Current: {len(note_input.strip())}/15)")
                                else:
                                    completed_mins = st.session_state.get(f"runtime_captured_{task_id}", 0)
                                    database.complete_task(task_id, note_input, completed_mins)
                                    if f"runtime_captured_{task_id}" in st.session_state:
                                        del st.session_state[f"runtime_captured_{task_id}"]
                                    st.session_state.show_balloons = True
                                    st.rerun()
                else:
                    st.success("🎉 All missions for this day are completed!")
                    
                if len(completed_list) > 0:
                    st.divider()
                    st.markdown("#### ✅ Completed Missions")
                    for task in completed_list:
                        task_id, task_title, task_category, task_video_url, task_xp, is_boss, task_summary = task[0:7]
                        task_medium = task[7] if len(task) > 7 else "Offline"
                        emoji = config.SUBJECT_EMOJIS.get(task_category, "📋")
                        med_badge = "📖 Offline" if task_medium == "Offline" else "💻 Online"
                        st.write(f"✅ {emoji} **{task_title}** (`{med_badge}`) (+{task_xp * 2 if is_boss == 1 else task_xp} XP)")
                        if task_summary:
                            st.caption(f"↳ *Note: {task_summary}*")


def render_standard_dashboard():
    """Existing V2 Classic layout with date picker."""
    col_date, col_toggle = st.columns([0.6, 0.4])
    with col_date:
        selected_date = st.date_input("📅 Select Date:", value=date.today())
    with col_toggle:
        if st.button("🚀 Switch to Simplified Beta View"):
            st.session_state.quest_view_mode = "Beta Focus UI"
            st.query_params["ui"] = "beta"
            st.rerun()

    day_display = selected_date.strftime("%A, %b %d")
    st.title(f"🎓 Sonny's Hub - {day_display}")
    st.header("📋 Daily Quests")

    pending_tasks = database.get_pending_tasks(selected_date)
    completed_tasks = database.get_completed_tasks(selected_date)

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
        st.metric(label="🔥 Daily Streak", value=f"{database.get_daily_streak()} Days")

    st.divider()

    col_todo, col_done = st.columns(2)

    with col_todo:
        st.subheader("📝 Up Next")
        if len(pending_tasks) == 0:
            st.success("🎉 All caught up!")
        else:
            for task in pending_tasks:
                task_id, task_title, task_category, task_video_url, task_xp, is_boss = task[0:6]
                task_medium = task[6] if len(task) > 6 else "Offline"
                emoji = config.SUBJECT_EMOJIS.get(task_category, "📋")
                med_badge = "📖 Offline" if task_medium == "Offline" else "💻 Online"
                
                with st.container(border=True):
                    if is_boss == 1:
                        st.markdown('<div class="boss-fight-marker"></div>', unsafe_allow_html=True)
                        
                    inner_col1, inner_col2 = st.columns([0.8, 0.2])
                    with inner_col1:
                        if is_boss == 1:
                            st.markdown("👑 **DAILY BOSS FIGHT - DOUBLE XP CHALLENGE!** 👑")
                            label_text = f"🔥 **{emoji} {task_category}**: {task_title} (`{med_badge}`) (💎 {task_xp * 2} XP!!)"
                        else:
                            label_text = f"**{emoji} {task_category}**: {task_title} (`{med_badge}`) (💎 {task_xp} XP)"
                            
                        is_checked = st.checkbox(label_text, key=f"task_{task_id}")
                    with inner_col2:
                        url = config.PLATFORM_LINKS.get(task_category, "")
                        if url != "":
                            st.markdown(f"[🚀 Launch]({url})")
                    
                    if task_video_url:
                        with st.expander("📺 Watch Lesson Video"):
                            st.video(task_video_url)
                    
                    render_focus_timer(task_id)
                    
                    note_input = st.text_input(
                        "✏️ What did you learn or read? (Add a summary note here before checking complete)",
                        key=f"note_input_{task_id}"
                    )
                    
                    st.write("") 
                    
                    if is_checked:
                        if len(note_input.strip()) < 15:
                            st.warning(f"⚠️ Note is too short! Write at least 15 characters about what you learned. (Current: {len(note_input.strip())}/15)")
                        else:
                            completed_mins = st.session_state.get(f"runtime_captured_{task_id}", 0)
                            database.complete_task(task_id, note_input, completed_mins)
                            if f"runtime_captured_{task_id}" in st.session_state:
                                del st.session_state[f"runtime_captured_{task_id}"]
                            st.session_state.show_balloons = True
                            st.rerun()

    with col_done:
        st.subheader("✅ Completed")
        if len(completed_tasks) == 0:
            st.info("No completed tasks yet. Time to get to work!")
        else:
            for task in completed_tasks:
                task_id, task_title, task_category, task_video_url, task_xp, is_boss, _task_summary = task
                emoji = config.SUBJECT_EMOJIS.get(task_category, "📋")
                st.write(f"✅ {emoji} **{task_title}** (+{task_xp * 2 if is_boss == 1 else task_xp} XP)")

# --- ROUTER ---
if st.session_state.quest_view_mode == "Beta Focus UI":
    render_beta_dashboard()
else:
    render_standard_dashboard()
