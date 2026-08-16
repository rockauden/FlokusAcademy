# ==========================================
# FLOKUS ACADEMY — REUSABLE UI COMPONENTS
# Shared helpers used across multiple pages.
# ==========================================

import streamlit as st
import streamlit.components.v1 as components
import html
import time
from datetime import date, datetime

import database


def render_school_notifications_bar():
    """Renders the upcoming school alerts & notifications expander bar."""
    active_notifications = database.get_upcoming_event_notifications(date.today())
    role = st.session_state.get('active_role', 'student')
    if active_notifications:
        with st.expander(f"🔔 **Upcoming School Alerts & Notifications ({len(active_notifications)})**", expanded=True):
            for notif in active_notifications:
                render_notification_card(notif, role)


def render_notification_card(notif, role="student"):
    """Renders a single notification event card with urgency styling."""
    if role == "student":
        # Softer language for student view — hide admin action items
        if "curriculum" in notif.get("description", "").lower() or "audit" in notif.get("description", "").lower():
            return  # Skip admin-targeted notifications in student view
            
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


def render_event_card(ev_title, ev_date_obj, ev_time, ev_cat, ev_imp, ev_desc):
    """Renders a standalone event card with urgency styling (used in calendar event list)."""
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


def render_focus_timer(task_id):
    """Renders the focus sprint timer widget for a given task."""
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
            timer_html = f"""
            <div style="background-color: #1a2238; border: 1px solid #63b3ed; border-radius: 8px; padding: 15px; text-align: center; font-family: 'Outfit', sans-serif;">
                <div style="font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; color: #8c9bb4; margin-bottom: 5px;">⌛ Active Focus Window</div>
                <div id="countdown-val-{task_id}" style="font-size: 32px; font-weight: bold; color: #63b3ed;">00:00</div>
            </div>
            <script>
                let seconds = {remaining};
                function getColor(secs) {{
                    if (secs > 300) return '#63b3ed';
                    if (secs > 60)  return '#f6ad55';
                    return '#f56565';
                }}
                function updateTimer() {{
                    let el = document.getElementById('countdown-val-{task_id}');
                    if (!el) return;
                    
                    let mins = Math.floor(seconds / 60);
                    let secs = seconds % 60;
                    el.innerText = `${{mins.toString().padStart(2, '0')}}:${{secs.toString().padStart(2, '0')}}`;
                    el.style.color = getColor(seconds);
                    
                    if (seconds <= 0) {{
                        el.innerText = "🎉 Focus Sprint Complete! You crushed it!";
                        el.style.color = "#22c55e";
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


def render_calendar_grid(view_year, view_month, events_in_month):
    """Renders the interactive month calendar grid with event indicators."""
    import calendar as cal_mod

    _, num_days = cal_mod.monthrange(view_year, view_month)
    month_start = date(view_year, view_month, 1)

    st.markdown(f"### 🗓️ {month_start.strftime('%B %Y')} Calendar")

    # Group events by day
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

    # Weekday headers
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

    # Empty leading cells
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

    # Trailing empty cells
    if current_cell != 0:
        for fill_idx in range(current_cell, 7):
            row_cols[fill_idx].markdown(
                "<div style='background:rgba(18, 22, 38, 0.3); border:1px dashed rgba(40, 50, 84, 0.4); border-radius:8px; min-height:90px; margin-bottom:6px;'></div>",
                unsafe_allow_html=True
            )


def render_countdown_hero(next_event):
    """Renders the countdown hero banner for the next major school event."""
    if not next_event:
        return

    d_left = next_event['days_left']
    if d_left > 0:
        cd_subtitle = f"Countdown to **{next_event['title']}** ({next_event['event_date'].strftime('%b %d, %Y')})"
        cd_number = f"⏳ {d_left} Days Away"
    elif d_left == 0:
        cd_subtitle = "🎉 TODAY IS THE DAY!"
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

def trigger_completion_effect(is_boss: bool, streak: int):
    """Fires tiered visual feedback based on achievement tier."""
    if is_boss:
        st.snow()
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #2d164d, #170b29);
            border: 2px solid #9f7aea;
            border-radius: 14px;
            padding: 20px;
            text-align: center;
            animation: pulse 0.6s ease-in-out;
            box-shadow: 0 0 30px rgba(159, 122, 234, 0.5);
        ">
            <div style="font-size: 36px;">👑</div>
            <div style="font-size: 22px; font-weight: 800; color: #d6bcfa;">
                BOSS DEFEATED!
            </div>
            <div style="font-size: 15px; color: #b794f4; margin-top: 6px;">
                Double XP Awarded! You're unstoppable.
            </div>
        </div>
        <style>
            @keyframes pulse {{
                0% {{ transform: scale(0.9); opacity: 0; }}
                100% {{ transform: scale(1); opacity: 1; }}
            }}
        </style>
        """, unsafe_allow_html=True)
    elif streak > 0 and streak % 5 == 0:
        st.balloons()
        st.success(f"🔥 **{streak}-Day Streak!** You're on fire, Sonny!")
    else:
        st.balloons()

def render_animated_progress(progress_pct: int, label: str = "Daily Quest Progress"):
    """Renders a custom animated progress bar with glow effect."""
    bar_color = "#22c55e" if progress_pct == 100 else "#63b3ed"
    glow = "0 0 12px rgba(34, 197, 94, 0.5)" if progress_pct == 100 else "0 0 8px rgba(99, 179, 237, 0.3)"
    
    st.markdown(f"""
    <div style="margin: 8px 0 16px;">
        <div style="display:flex; justify-content:space-between; 
             font-size:13px; color:#8c9bb4; margin-bottom:6px;">
            <span>{label}</span>
            <span style="font-weight:700; color:{bar_color};">{progress_pct}%</span>
        </div>
        <div style="background:#1e2236; border-radius:999px; height:10px; 
             border:1px solid #283254; overflow:hidden;">
            <div style="
                width: {progress_pct}%;
                height: 100%;
                background: linear-gradient(90deg, #3b82f6, {bar_color});
                border-radius: 999px;
                box-shadow: {glow};
                transition: width 1.2s cubic-bezier(0.4, 0, 0.2, 1);
            "></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_student_kpi_card(label, value, subtitle, icon, color="#63b3ed", extra_class=""):
    """Renders a styled KPI card with contextual subtitle."""
    st.markdown(f"""
    <div class="{extra_class}" style="
        background: linear-gradient(135deg, #181c2e, #111422);
        border: 1px solid #232a45;
        border-radius: 14px;
        padding: 18px 20px;
        text-align: center;
        transition: all 0.25s ease;
    ">
        <div style="font-size: 28px;">{icon}</div>
        <div style="font-size: 28px; font-weight: 800; color:{color}; 
             line-height: 1.1; margin: 4px 0;">{value}</div>
        <div style="font-size: 12px; text-transform: uppercase; 
             letter-spacing: 0.8px; color: #8c9bb4; font-weight: 600;">{label}</div>
        <div style="font-size: 11px; color: #4a5568; margin-top: 4px;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def render_completed_mission_card(task_title, task_category, xp_earned, summary, emoji, just_done=False):
    """Renders a visually distinct completed mission card."""
    animation_style = "animation: slideIn 0.4s ease-out;" if just_done else ""
    st.markdown(f"""
    <div class="mission-complete-card" style="
        padding: 12px 16px;
        margin-bottom: 8px;
        {animation_style}
    ">
        <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:20px;">✅</span>
            <div>
                <div style="font-weight:700; color:#86efac; font-size:14px;">
                    {emoji} {task_title}
                </div>
                <div style="font-size:12px; color:#4ade80; margin-top:2px;">
                    {task_category} &nbsp;·&nbsp; +{xp_earned} XP earned
                </div>
                {f'<div style="font-size:11px; color:#6b7280; margin-top:4px; font-style:italic;">📝 {summary}</div>' if summary else ''}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_weekly_momentum_strip(week_dates, db):
    """Renders a horizontal week progress strip showing completion per day."""
    st.markdown("<div style='margin: 12px 0 8px; font-size:12px; color:#8c9bb4; "
                "text-transform:uppercase; letter-spacing:1px;'>This Week</div>",
                unsafe_allow_html=True)
    cols = st.columns(5)
    today = date.today()
    for i, (col, d) in enumerate(zip(cols, week_dates)):
        with col:
            pending = db.get_pending_tasks(d)
            completed = db.get_completed_tasks(d)
            total = len(pending) + len(completed)
            done = len(completed)
            is_today = (d == today)
            
            if total == 0:
                dot_color, label = "#2d3748", "—"
            elif done == total:
                dot_color, label = "#22c55e", "✓"
            elif done > 0:
                dot_color, label = "#f6ad55", f"{done}/{total}"
            else:
                dot_color, label = "#63b3ed", f"0/{total}"
                
            border = "2px solid #6366f1" if is_today else "1px solid #283254"
            st.markdown(f"""
            <div style="text-align:center; background:#121626; border:{border};
                 border-radius:10px; padding:8px 4px;">
                <div style="font-size:16px; font-weight:800; color:{dot_color};">{label}</div>
                <div style="font-size:10px; color:#4a5568; margin-top:2px;">
                    {d.strftime('%a')}
                </div>
            </div>
            """, unsafe_allow_html=True)

