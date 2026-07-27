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
    if active_notifications:
        with st.expander(f"🔔 **Upcoming School Alerts & Notifications ({len(active_notifications)})**", expanded=True):
            for notif in active_notifications:
                render_notification_card(notif)


def render_notification_card(notif):
    """Renders a single notification event card with urgency styling."""
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
