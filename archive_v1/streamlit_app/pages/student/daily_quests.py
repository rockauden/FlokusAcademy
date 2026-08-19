import streamlit as st
from datetime import date, datetime, timedelta
import database
import config
from ui.components import (
    render_school_notifications_bar,
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
daily_xp_today = sum(t[4] for t in completed_today)
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

# Today first, then the rest of the week in order.
#
# WHY NOT PLAIN MON-FRI: st.tabs always opens on the first tab and offers no way
# to preselect one. The old code computed a `default_tab_index` and then never
# used it, so by Thursday Sonny opened the app to Monday -- three days of
# finished work -- and had to hunt for the day he was actually on. The date is
# on every tab and today's carries a 📍, so leading with it costs no clarity.
if today in week_dates:
    ordered = [today] + [d for d in week_dates if d != today]
else:
    ordered = week_dates                       # weekend: plain Mon-Fri

week_day_labels = [day_label(d, today) for d in ordered]
tabs = st.tabs(week_day_labels)

for i, tab in enumerate(tabs):
    tab_date = ordered[i]
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
                    task_id, task_title, task_category, task_video_url, task_xp = task[0:5]
                    task_medium = task[6] if len(task) > 6 else "Offline"
                    own_date = task[7] if len(task) > 7 else None
                    emoji = config.SUBJECT_EMOJIS.get(task_category, "📋")
                    med_badge = "📖 Offline" if task_medium == "Offline" else "💻 Online"

                    # Today's tab also lists anything still unfinished from an
                    # earlier day, so one assignment can be drawn twice in one
                    # render -- once here and once in its own day's tab. Keying
                    # the widgets on task_id alone made Streamlit raise
                    # DuplicateElementKey, which put a red traceback in front of
                    # a nine-year-old the first morning he ran a day behind.
                    # The tab's own date namespaces the keys.
                    wkey = f"{task_id}_{tab_date.isoformat()}"
                    carried = own_date and own_date != tab_date.isoformat()

                    # One card, three things: where the work is, a place to say
                    # what you learned, and the checkbox. The old card wrapped
                    # this in a four-step Learn/Sprint/Reflect/Complete ritual
                    # with a countdown timer and a minimum character count on
                    # the note. That is a lot of ceremony to stand between a
                    # nine-year-old and twenty minutes of Beast Academy.
                    with st.expander(
                        f"{'↩️ ' if carried else ''}{emoji} {task_category}: "
                        f"{task_title} [{med_badge}] (💎 {task_xp} XP)",
                        expanded=is_today_tab and not carried
                    ):
                        if carried:
                            st.caption(
                                f"Carried over from "
                                f"{datetime.strptime(own_date, '%Y-%m-%d'):%A, %b %d}."
                                " No rush — finish it when you get to it.")

                        launch_url = config.PLATFORM_LINKS.get(task_category, "")
                        parts = task_category.split("(")
                        platform_name = parts[-1].replace(")", "").strip() if len(parts) > 1 else task_category

                        # Only hand st.video() something that is actually a
                        # video. Sixteen rows had a platform HOMEPAGE stored in
                        # video_url (beastacademy.com/login, bravewriter.com),
                        # and st.video() renders those as an empty black player
                        # with a dead 0:00 scrubber -- so the card looked broken
                        # and the real link never appeared.
                        is_video = task_video_url and any(
                            h in task_video_url
                            for h in ("youtube.com", "youtu.be", "vimeo.com",
                                      ".mp4", ".webm", ".mov")
                        )
                        if is_video:
                            st.video(task_video_url)
                        elif task_video_url:
                            st.markdown(f"##### 🚀 [Open the link →]({task_video_url})")
                        elif launch_url:
                            st.markdown(f"##### 🚀 [Open {platform_name} →]({launch_url})")
                        else:
                            st.markdown("##### 📖 Offline assignment — grab your book.")

                        # The note stays because writing down what you learned
                        # is the point. The blocking character count does not:
                        # it turned a reflection into a toll gate, and the way
                        # past a toll gate is to type filler.
                        note_input = st.text_area(
                            "What did you learn? (optional)",
                            key=f"note_input_{wkey}", height=80
                        )

                        if st.checkbox("I finished this!", key=f"task_chk_{wkey}"):
                            database.complete_task(task_id, note_input)
                            st.session_state[f"just_completed_{task_id}"] = True
                            trigger_completion_effect(current_streak)
                            st.rerun()
            else:
                st.success("🎉 All missions for this day are completed!")
                
            if len(completed_list) > 0:
                st.divider()
                st.markdown("#### ✅ Completed Missions")
                for task in completed_list:
                    task_id, task_title, task_category, task_video_url, task_xp = task[0:5]
                    task_summary = task[6]
                    emoji = config.SUBJECT_EMOJIS.get(task_category, "📋")
                    just_done = st.session_state.pop(f"just_completed_{task_id}", False)
                    render_completed_mission_card(task_title, task_category, task_xp, task_summary, emoji, just_done)
