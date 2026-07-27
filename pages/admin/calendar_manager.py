import streamlit as st
from datetime import date, datetime
import database

st.title("Event Calendar")

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
            database.add_school_event(
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

all_dad_events = database.get_school_events()
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
                        database.update_school_event(ev_id, e_title.strip(), e_date, e_time.strip(), e_cat, e_imp, e_rem, e_desc.strip())
                        st.success("Event updated!")
                        st.rerun()
                        
        with col_ev3:
            with st.popover("❌ Delete"):
                st.write("Delete this school event?")
                if st.button("Confirm Delete", key=f"del_ev_btn_{ev_id}"):
                    database.delete_school_event(ev_id)
                    st.success("Event deleted!")
                    st.rerun()
