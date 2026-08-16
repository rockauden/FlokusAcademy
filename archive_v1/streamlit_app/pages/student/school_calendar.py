import streamlit as st
from datetime import date, datetime
import database
from ui.components import render_calendar_grid, render_countdown_hero, render_event_card

st.title("📅 School Calendar & Upcoming Academic Events")

next_event = database.get_next_major_school_event(date.today())
if next_event:
    render_countdown_hero(next_event)

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
    
    events_in_month = database.get_school_events(start_date=month_start, end_date=month_end)
    
    
    render_calendar_grid(view_year, view_month, events_in_month)
            
with cal_sub2:
    st.markdown("### 📋 All Scheduled School Events")
    cat_options = ["All Categories", "🎓 School Start / Term", "🎥 Live Class (Outschool)", "🛠️ Kit Delivery / Project", "🏛️ Field Trip", "💰 UFA Milestone", "📝 Exam / Assessment", "📌 General"]
    selected_cat_filter = st.selectbox("Filter by Category", cat_options, key="sonny_event_cat_filter")
    
    all_events = database.get_school_events(category_filter=selected_cat_filter)
    if not all_events:
        st.info("No events found matching this filter.")
    else:
        for ev in all_events:
            ev_id, ev_title, ev_date_str, ev_time, ev_cat, ev_imp, ev_rem, ev_desc, _ = ev
            ev_date_obj = datetime.strptime(ev_date_str, "%Y-%m-%d").date()
            render_event_card(ev_title, ev_date_obj, ev_time, ev_cat, ev_imp, ev_desc)
