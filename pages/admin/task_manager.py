import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import database
import config
from ai_tutor import parse_and_execute_schedule_command
import curriculum_data

st.title("📝 Task Management & Lesson Scheduler")
st.caption("Streamlined workflow for scheduling Sonny's homeschooling curriculum and quests.")

# --- THREE CLEAN WORKFLOW TABS ---
tab_quick, tab_weekly, tab_advanced = st.tabs([
    "⚡ Quick Add Lesson", 
    "📅 Weekly Visual Schedule", 
    "⚙️ Master Curriculum Scheduler (Tier 1 & Tier 2)"
])

# ==========================================
# TAB 1: QUICK ADD LESSON
# ==========================================
with tab_quick:
    st.subheader("⚡ Quick Add Single Lesson")
    st.write("Schedule an individual assignment for Sonny in seconds.")
    
    with st.form("quick_task_form", clear_on_submit=True):
        col_q1, col_q2 = st.columns([0.6, 0.4])
        with col_q1:
            task_title = st.text_input("Lesson / Task Description*", placeholder="e.g., Chapter 2 Pages 15-20 or Copywork passage")
        with col_q2:
            task_category = st.selectbox("Curriculum Spine / Subject*", list(config.SUBJECT_EMOJIS.keys()))
            
        col_q3, col_q4, col_q5, col_q6, col_q7 = st.columns([0.25, 0.25, 0.2, 0.15, 0.15])
        with col_q3:
            scheduled_date = st.date_input("Scheduled Date", value=date.today())
        with col_q4:
            task_medium = st.selectbox("Medium*", ["Offline", "Online"], help="Offline (Books, Kits, Paper) vs Online (Apps, Screen)")
        with col_q5:
            task_video = st.text_input("Optional Video URL", placeholder="https://youtube.com/...")
        with col_q6:
            task_xp = st.number_input("XP Reward", min_value=5, max_value=500, value=10, step=5)
        with col_q7:
            st.write("") # spacing
            st.write("")
            is_boss_fight = st.checkbox("⭐ Boss", value=False, help="Double XP Bonus")
            
        submitted_quick = st.form_submit_button("🚀 Schedule Lesson Now", use_container_width=True)
        
        if submitted_quick:
            if not task_title.strip():
                st.error("⚠️ Task Description cannot be empty!")
            else:
                boss_int = 1 if is_boss_fight else 0
                database.add_task_to_db(task_title.strip(), task_category, task_video.strip() if task_video else "", task_xp, scheduled_date, boss_int, task_medium)
                st.success(f"🎉 Scheduled **{task_title}** [{task_medium}] for {task_category} on {scheduled_date.strftime('%A, %b %d')}!")
                st.rerun()

    st.divider()
    st.subheader("📋 Upcoming Pending Tasks")
    pending_list = database.get_all_pending_tasks()
    if not pending_list:
        st.info("No pending tasks scheduled.")
    else:
        # Display top 15 pending tasks cleanly
        for t in pending_list[:15]:
            t_id, t_title, t_category, t_video, t_xp, t_boss, t_date_str = t[0:7]
            t_medium = t[7] if len(t) > 7 else "Offline"
            t_date = datetime.strptime(t_date_str, "%Y-%m-%d").date()
            
            col_t1, col_t2, col_t3 = st.columns([0.6, 0.2, 0.2])
            with col_t1:
                emoji = config.SUBJECT_EMOJIS.get(t_category, "📋")
                boss_label = " 👑 *(Boss Fight!)*" if t_boss == 1 else ""
                medium_badge = "📖 Offline" if t_medium == "Offline" else "💻 Online"
                st.markdown(f"**{emoji} {t_category}**: {t_title} (`{medium_badge}`) (💎 {t_xp} XP){boss_label}  \n*Scheduled: {t_date.strftime('%A, %b %d, %Y')}*")
            
            with col_t2:
                with st.popover("✏️ Edit"):
                    edit_title = st.text_input("Task Description", value=t_title, key=f"edit_task_title_{t_id}")
                    edit_category = st.selectbox(
                        "Curriculum Spine",
                        options=list(config.SUBJECT_EMOJIS.keys()),
                        index=list(config.SUBJECT_EMOJIS.keys()).index(t_category) if t_category in config.SUBJECT_EMOJIS else 0,
                        key=f"edit_task_cat_{t_id}"
                    )
                    edit_medium = st.selectbox("Medium", ["Offline", "Online"], index=0 if t_medium == "Offline" else 1, key=f"edit_task_med_{t_id}")
                    edit_video = st.text_input("YouTube Video URL", value=t_video or "", key=f"edit_task_vid_{t_id}")
                    edit_xp = st.number_input("XP Reward", min_value=5, max_value=500, value=int(t_xp), step=5, key=f"edit_task_xp_{t_id}")
                    edit_date = st.date_input("Scheduled Date", value=t_date, key=f"edit_task_date_{t_id}")
                    edit_boss = st.checkbox("Mark as Daily Boss Fight", value=(t_boss == 1), key=f"edit_task_boss_{t_id}")
                    
                    if st.button("Save Changes", key=f"save_task_btn_{t_id}"):
                        if not edit_title.strip():
                            st.error("Task Description cannot be empty!")
                        else:
                            database.update_task_details(t_id, edit_title.strip(), edit_category, edit_video.strip(), edit_xp, edit_date, 1 if edit_boss else 0, edit_medium)
                            st.success("Task updated successfully!")
                            st.rerun()
            
            with col_t3:
                with st.popover("❌ Delete"):
                    st.write("Are you sure you want to delete this task?")
                    if st.button("Confirm Delete", key=f"del_task_btn_{t_id}"):
                        database.delete_task(t_id)
                        st.success("Task deleted!")
                        st.rerun()


# ==========================================
# TAB 2: WEEKLY VISUAL SCHEDULE & SCREEN-TIME AUDIT
# ==========================================
with tab_weekly:
    st.subheader("📅 Weekly Schedule Grid & Screen-Time Audit")
    st.write("View and balance Sonny's weekly workload and audit Offline vs. Online screen time.")
    
    col_w_sel, _ = st.columns([0.4, 0.6])
    with col_w_sel:
        selected_week_start = st.date_input("Select Week Start Date (Monday)", value=date.today() - timedelta(days=date.today().weekday()))
        # Align to Monday
        monday_start = selected_week_start - timedelta(days=selected_week_start.weekday())
        
    st.caption(f"Showing Week of **{monday_start.strftime('%B %d, %Y')}**")
    
    # Audit screen time for the selected 5-day week
    week_all_pending = []
    for d_off in range(5):
        d_check = monday_start + timedelta(days=d_off)
        week_all_pending.extend(database.get_pending_tasks(d_check))
        week_all_pending.extend(database.get_completed_tasks(d_check))
        
    offline_count = sum(1 for t in week_all_pending if (len(t) > 6 and t[6] == "Offline") or (len(t) > 7 and t[7] == "Offline"))
    online_count = sum(1 for t in week_all_pending if (len(t) > 6 and t[6] == "Online") or (len(t) > 7 and t[7] == "Online"))
    total_week_tasks = len(week_all_pending)
    
    offline_pct = int((offline_count / total_week_tasks) * 100) if total_week_tasks > 0 else 50
    online_pct = 100 - offline_pct if total_week_tasks > 0 else 50
    
    col_aud1, col_aud2, col_aud3 = st.columns(3)
    with col_aud1:
        st.metric("Total Weekly Lessons", f"{total_week_tasks} Lessons")
    with col_aud2:
        st.metric("📖 Offline Medium", f"{offline_count} Tasks ({offline_pct}%)")
    with col_aud3:
        st.metric("💻 Online Medium", f"{online_count} Tasks ({online_pct}%)")
        
    if total_week_tasks > 0:
        st.progress(offline_pct / 100.0, text=f"Screen-Time Audit: {offline_pct}% Offline Books/Kits | {online_pct}% Online Apps")
        if online_pct > 60:
            st.warning("⚠️ High Screen-Time Warning: Over 60% of scheduled tasks this week are Online. Consider shifting some touchpoints to Offline hands-on work!")
        else:
            st.success("✅ Excellent Pacing Balance! Healthy mix of hands-on offline study and digital tools.")
    st.divider()

    week_cols = st.columns(5)
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    for idx in range(5):
        col_date = monday_start + timedelta(days=idx)
        is_today = (col_date == date.today())
        
        with week_cols[idx]:
            header_text = f"**{weekdays[idx]}**  \n*{col_date.strftime('%b %d')}*"
            if is_today:
                st.markdown(f"📌 {header_text}")
            else:
                st.markdown(header_text)
                
            st.divider()
            
            p_tasks = database.get_pending_tasks(col_date)
            c_tasks = database.get_completed_tasks(col_date)
            
            # Render pending tasks
            for pt in p_tasks:
                t_id, t_title, t_category, t_video, t_xp, t_boss = pt[0:6]
                t_med = pt[6] if len(pt) > 6 else "Offline"
                emoji = config.SUBJECT_EMOJIS.get(t_category, "📋")
                med_icon = "📖" if t_med == "Offline" else "💻"
                
                with st.container(border=True):
                    st.markdown(f"**{emoji} {t_title}**")
                    st.caption(f"{t_category} | {med_icon} {t_med} | 💎 {t_xp} XP")
                    
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        with st.popover("✏️"):
                            e_title = st.text_input("Title", value=t_title, key=f"grid_edit_title_{t_id}")
                            e_cat = st.selectbox("Category", list(config.SUBJECT_EMOJIS.keys()), index=list(config.SUBJECT_EMOJIS.keys()).index(t_category) if t_category in config.SUBJECT_EMOJIS else 0, key=f"grid_edit_cat_{t_id}")
                            e_med = st.selectbox("Medium", ["Offline", "Online"], index=0 if t_med == "Offline" else 1, key=f"grid_edit_med_{t_id}")
                            if st.button("Save", key=f"grid_save_btn_{t_id}"):
                                database.update_task_details(t_id, e_title, e_cat, t_video, t_xp, col_date, t_boss, e_med)
                                st.rerun()
                    with col_b2:
                        if st.button("🗑️", key=f"grid_del_btn_{t_id}"):
                            database.delete_task(t_id)
                            st.rerun()
                            
            # Render completed tasks
            for ct in c_tasks:
                t_id, t_title, t_category, t_video, t_xp, t_boss, _sum = ct[0:7]
                t_med = ct[7] if len(ct) > 7 else "Offline"
                emoji = config.SUBJECT_EMOJIS.get(t_category, "📋")
                med_icon = "📖" if t_med == "Offline" else "💻"
                st.markdown(f"✅ ~{emoji} {t_title}~ ({med_icon})")
                
            if len(p_tasks) == 0 and len(c_tasks) == 0:
                st.caption("No lessons scheduled.")
                
            st.write("")
            # Inline quick-add button for this specific day
            with st.popover(f"➕ Add to {weekdays[idx]}", use_container_width=True):
                st.markdown(f"**Add Lesson for {weekdays[idx]}, {col_date.strftime('%b %d')}**")
                pop_title = st.text_input("Lesson Title", key=f"pop_title_{idx}")
                pop_cat = st.selectbox("Category", list(config.SUBJECT_EMOJIS.keys()), key=f"pop_cat_{idx}")
                pop_med = st.selectbox("Medium", ["Offline", "Online"], key=f"pop_med_{idx}")
                pop_xp = st.number_input("XP", min_value=5, max_value=200, value=10, step=5, key=f"pop_xp_{idx}")
                if st.button("Add to Schedule", key=f"pop_submit_{idx}"):
                    if pop_title.strip():
                        database.add_task_to_db(pop_title.strip(), pop_cat, "", pop_xp, col_date, 0, pop_med)
                        st.success(f"Added to {weekdays[idx]}!")
                        st.rerun()


# ==========================================
# TAB 3: MASTER CURRICULUM SCHEDULER (TIER 1 & TIER 2)
# ==========================================
with tab_advanced:
    st.subheader("🎓 Flokus Academy Master Curriculum Scheduler (Tier 1 & Tier 2)")
    st.write("View the 36-week master plan and automatically batch-schedule Sonny's complete homeschooling curriculum.")
    
    # 1. Tier 1 Yearly Overview Expander
    with st.expander("🗺️ Tier 1: Yearly Overview (36 Weeks / 4 Quarters)", expanded=True):
        st.markdown("Annual map balancing Core Foundational Hubs (Math, ELA, History, Logic) with Applied Project Spokes (Engineering, AI, Interactive STEM, Chess, Outschool).")
        
        q_cols = st.columns(4)
        for q_idx in range(1, 5):
            q_info = curriculum_data.TIER_1_OVERVIEW[q_idx]
            with q_cols[q_idx - 1]:
                st.markdown(f"### {q_info['title']}")
                st.caption(f"**Scope:** {q_info['weeks']}")
                st.markdown(f"**🧮 Math & Logic:**  \n{q_info['math_logic']}")
                st.markdown(f"**✍️ ELA & Lit:**  \n{q_info['ela']}")
                st.markdown(f"**🗺️ History & Civics:**  \n{q_info['history']}")
                st.markdown(f"**🧠 Critical & Strategy:**  \n{q_info['critical_thinking']}")
                st.markdown(f"**🧪 Applied STEM:**  \n{q_info['stem_electives']}")
                
    # 2. Tier 2 Detailed Unit Increments Expander
    with st.expander("📦 Tier 2: Structured Unit Increments (36-Week Detailed Breakdown)", expanded=False):
        st.markdown("9 4-week unit blocks demonstrating the synchronization of Core Hub subjects with Supplemental Spoke programs.")
        
        df_tier2 = pd.DataFrame(curriculum_data.TIER_2_UNITS)
        df_tier2.columns = ["Wk", "Unit Theme", "Math & STEM (Beast & Brilliant)", "Language Arts (Brave Writer)", "History & Logic (Tuttle & Critical)", "Strategy & Engineering (Synthesis, Chess, CrunchLabs, Outschool)"]
        
        unit_filter = st.selectbox("Filter by Unit Block", ["All 36 Weeks"] + [f"Unit {u}" for u in range(1, 10)])
        if unit_filter != "All 36 Weeks":
            selected_u_num = int(unit_filter.split()[1])
            df_filtered = df_tier2[(df_tier2["Wk"] >= (selected_u_num - 1)*4 + 1) & (df_tier2["Wk"] <= selected_u_num * 4)]
        else:
            df_filtered = df_tier2
            
        st.dataframe(df_filtered, use_container_width=True, hide_index=True)

    st.divider()
    
    # 3. Batch Schedule Generator Form
    st.subheader("🚀 1-Click Master Curriculum Batch Scheduler")
    st.write("Select a scope (Full Year, Quarter, Unit, or Week) to generate and load scheduled assignments directly into Sonny's calendar.")
    
    with st.form("master_curriculum_batch_form"):
        col_gen1, col_gen2, col_gen3 = st.columns([0.35, 0.35, 0.3])
        
        with col_gen1:
            schedule_scope = st.selectbox(
                "Select Curriculum Scope*",
                [
                    "Full School Year (All 36 Weeks)",
                    "Quarter 1 (Weeks 1–9) - Foundations & Origins",
                    "Quarter 2 (Weeks 10–18) - Revolution & Reasoning",
                    "Quarter 3 (Weeks 19–27) - Nation Building & Logic",
                    "Quarter 4 (Weeks 28–36) - Expansion & Synthesis",
                    "Unit 1 (Weeks 1–4) - Trade & Place Value",
                    "Unit 2 (Weeks 5–8) - Empire & Addition",
                    "Unit 3 (Weeks 9–12) - Revolution & Robots",
                    "Unit 4 (Weeks 13–16) - Wilderlore & Guilds",
                    "Unit 5 (Weeks 17–20) - Odder & Ocean Verse",
                    "Unit 6 (Weeks 21–24) - Lemoncello Puzzles",
                    "Unit 7 (Weeks 25–28) - Camels & Flashbacks",
                    "Unit 8 (Weeks 29–32) - Thirst & Resource Logic",
                    "Unit 9 (Weeks 33–36) - Sidekicks & Capstones",
                    "Specific Week"
                ]
            )
            
        with col_gen2:
            if schedule_scope == "Specific Week":
                single_week_num = st.number_input("Select Week Number (1–36)", min_value=1, max_value=36, value=1)
            else:
                single_week_num = None
                st.info("Batching multi-week curriculum range")
                
        with col_gen3:
            start_monday_date = st.date_input("Start Date (Monday)*", value=date.today() - timedelta(days=date.today().weekday()))

        submitted_master_batch = st.form_submit_button("🚀 Generate & Load Master Curriculum Schedule", use_container_width=True)
        
        if submitted_master_batch:
            mon_start = start_monday_date - timedelta(days=start_monday_date.weekday())
            
            # Determine list of week numbers
            if schedule_scope == "Full School Year (All 36 Weeks)":
                target_weeks = list(range(1, 37))
            elif "Quarter 1" in schedule_scope:
                target_weeks = list(range(1, 10))
            elif "Quarter 2" in schedule_scope:
                target_weeks = list(range(10, 19))
            elif "Quarter 3" in schedule_scope:
                target_weeks = list(range(19, 28))
            elif "Quarter 4" in schedule_scope:
                target_weeks = list(range(28, 37))
            elif "Unit 1" in schedule_scope:
                target_weeks = list(range(1, 5))
            elif "Unit 2" in schedule_scope:
                target_weeks = list(range(5, 9))
            elif "Unit 3" in schedule_scope:
                target_weeks = list(range(9, 13))
            elif "Unit 4" in schedule_scope:
                target_weeks = list(range(13, 17))
            elif "Unit 5" in schedule_scope:
                target_weeks = list(range(17, 21))
            elif "Unit 6" in schedule_scope:
                target_weeks = list(range(21, 25))
            elif "Unit 7" in schedule_scope:
                target_weeks = list(range(25, 29))
            elif "Unit 8" in schedule_scope:
                target_weeks = list(range(29, 33))
            elif "Unit 9" in schedule_scope:
                target_weeks = list(range(33, 37))
            elif schedule_scope == "Specific Week" and single_week_num:
                target_weeks = [int(single_week_num)]
            else:
                target_weeks = [1]
                
            created_count = curriculum_data.generate_tier_schedule(target_weeks, mon_start)
            st.success(f"🎉 Successfully loaded **{len(target_weeks)} Weeks** of Flokus Academy Master Curriculum starting {mon_start.strftime('%b %d, %Y')}! Created **{created_count} lessons** across all 9 curriculum spokes!")
            st.rerun()
