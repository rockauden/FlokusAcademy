import streamlit as st
import time
from datetime import date, datetime, timedelta
import database
import config
from ui.components import (
    render_school_notifications_bar, 
    render_focus_timer,
    render_animated_progress,
    render_student_kpi_card,
    render_completed_mission_card,
    render_weekly_momentum_strip,
    trigger_completion_effect
)

# Handle session state for celebration balloons
if 'show_balloons' not in st.session_state:
    st.session_state.show_balloons = False

if st.session_state.show_balloons:
    st.balloons()
    st.session_state.show_balloons = False

# Render top notification banner
render_school_notifications_bar()

# 1. The "Backpack" (Sidebar for external links and non-daily tasks/events)
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 12px 0 8px;">
        <div style="font-size: 40px;">🧑‍🚀</div>
        <div style="font-size: 18px; font-weight: 700; color: #e2e8f0;">Sonny's Mission Control</div>
        <div style="font-size: 12px; color: #8c9bb4; margin-top: 2px;">Grade 5 Explorer</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    
    st.caption("🎒 Quick Links & Resources")
    
    # Featured Platform Links (filter out empty URLs and use custom CSS styling)
    for category, url in config.PLATFORM_LINKS.items():
        if not url:
            continue
        emoji = config.SUBJECT_EMOJIS.get(category, "🔗")
        parts = category.split("(")
        platform_name = parts[-1].replace(")", "").strip() if len(parts) > 1 else category
        st.markdown(
            f"<a href='{url}' target='_blank' class='backpack-link' style='display:flex; align-items:center; "
            f"gap:8px; padding:8px 10px; background:#161b2e; border:1px solid #283254; "
            f"border-radius:8px; text-decoration:none; color:#e2e8f0; margin-bottom:6px; "
            f"font-size:14px; transition:all 0.2s ease;'>"
            f"{emoji} {platform_name}</a>",
            unsafe_allow_html=True
        )
            
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

# 2. Today & Momentum Header
today = date.today()
current_weekday_idx = today.weekday() # 0 = Monday, 4 = Friday, 5 = Sat, 6 = Sun
day_name = today.strftime("%A")

pending_today = database.get_pending_tasks(today)
completed_today = database.get_completed_tasks(today)
total_today = len(pending_today) + len(completed_today)
progress_percentage = int((len(completed_today) / total_today) * 100) if total_today > 0 else 0
daily_xp_today = sum([t[4] * 2 if t[5] == 1 else t[4] for t in completed_today])
current_streak = database.get_daily_streak()

st.markdown(f"### Happy {day_name}, Sonny! 🚀")
st.caption(f"Today is {today.strftime('%B %d, %Y')}")

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    subtitle = "Keep going!" if len(completed_today) < total_today else "All done! 🎉"
    kpi_class = "kpi-complete" if len(completed_today) == total_today and total_today > 0 else ""
    render_student_kpi_card(
        "Tasks Completed", f"{len(completed_today)}/{total_today}",
        subtitle, "✅", "#22c55e" if len(completed_today) == total_today else "#63b3ed", extra_class=kpi_class
    )
with col2:
    render_student_kpi_card(
        "Today's XP", f"{daily_xp_today}",
        "Keep earning!", "💎", "#b794f4"
    )
with col3:
    render_student_kpi_card(
        "Daily Streak", f"{current_streak}",
        "Days in a row", "🔥", "#f6ad55"
    )

render_animated_progress(progress_percentage)

# 3. Weekly Momentum Strip
monday_start = today - timedelta(days=current_weekday_idx)
week_dates = [monday_start + timedelta(days=i) for i in range(5)]
render_weekly_momentum_strip(week_dates, database)
st.divider()

# 4. The "Today" Focus (Tabs for Mon-Fri of Current Week)
def day_label(d, today_dt):
    name = d.strftime('%a')
    short = d.strftime('%b %d')
    completed = database.get_completed_tasks(d)
    pending = database.get_pending_tasks(d)
    total = len(completed) + len(pending)
    done = len(completed)
    
    if d == today_dt:
        return f"📍 {name} ({short})"
    elif d < today_dt and done == total and total > 0:
        return f"✅ {name} ({short})"
    elif d < today_dt and total > 0:
        return f"⚠️ {name} ({short})"
    return f"{name} ({short})"

week_day_labels = [day_label(d, today) for d in week_dates]

# If weekend (Sat/Sun index 5-6), default to Monday (tab 0)
default_tab_index = current_weekday_idx if current_weekday_idx < 5 else 0

tabs = st.tabs(week_day_labels)

min_note_length = database.get_note_min_length()

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
                            
                        # Mission Header
                        col_exp1, col_exp2 = st.columns([0.7, 0.3])
                        with col_exp1:
                            st.write(f"**Mission:** {task_title}")
                        with col_exp2:
                            st.write(f"`{med_badge}`")
                            
                        # 4-step mission flow
                        s1, s2, s3, s4 = st.columns(4)
                        with s1: st.markdown("<span class='mission-step-active'>**① Learn**</span>", unsafe_allow_html=True)
                        with s2: st.markdown("<span class='mission-step-active'>**② Sprint**</span>", unsafe_allow_html=True)  
                        with s3: st.markdown("<span class='mission-step-active'>**③ Reflect**</span>", unsafe_allow_html=True)
                        with s4: st.markdown("<span class='mission-step-active'>**④ Complete**</span>", unsafe_allow_html=True)
                        st.divider()
                        
                        # Step 1 — Resource
                        launch_url = config.PLATFORM_LINKS.get(task_category, "")
                        parts = task_category.split("(")
                        platform_name = parts[-1].replace(")", "").strip() if len(parts) > 1 else task_category
                        
                        if task_video_url:
                            st.markdown("##### 📺 Step 1: Watch the Lesson")
                            st.video(task_video_url)
                        elif launch_url:
                            st.markdown(f"##### 🚀 Step 1: [Open {platform_name} →]({launch_url})")
                        else:
                            st.markdown("##### 📖 Step 1: Complete your offline assignment")
                            
                        st.markdown("---")
                        # Step 2 — Timer
                        st.markdown("##### ⏱️ Step 2: Start Your Focus Sprint")
                        render_focus_timer(task_id)
                        
                        st.markdown("---")
                        # Step 3 — Reflect
                        st.markdown("##### ✏️ Step 3: What Did You Learn?")
                        
                        note_input = st.text_area("Write your summary here...", 
                                                   key=f"beta_note_input_{task_id}", height=80)
                        note_chars = len(note_input.strip())
                        if note_input:
                            char_color = "#22c55e" if note_chars >= min_note_length else "#f6ad55"
                            st.markdown(f"<span style='font-size:11px; color:{char_color};'>"
                                        f"{note_chars}/{min_note_length} characters</span>", unsafe_allow_html=True)
                        
                        st.markdown("---")
                        # Step 4 — Complete
                        st.markdown("##### ✅ Step 4: Mark Mission Complete")
                        is_checked = st.checkbox("I finished this mission!", key=f"beta_task_chk_{task_id}")
                        
                        if is_checked:
                            if note_chars < min_note_length:
                                st.warning(f"⚠️ Note is too short! Write at least {min_note_length} characters about what you learned. (Current: {note_chars}/{min_note_length})")
                            else:
                                completed_mins = st.session_state.get(f"runtime_captured_{task_id}", 0)
                                database.complete_task(task_id, note_input, completed_mins)
                                if f"runtime_captured_{task_id}" in st.session_state:
                                    del st.session_state[f"runtime_captured_{task_id}"]
                                
                                # Set just completed flag for animation
                                st.session_state[f"just_completed_{task_id}"] = True
                                trigger_completion_effect(is_boss == 1, current_streak)
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
                    just_done = st.session_state.pop(f"just_completed_{task_id}", False)
                    render_completed_mission_card(task_title, task_category, task_xp * 2 if is_boss == 1 else task_xp, task_summary, emoji, just_done)
