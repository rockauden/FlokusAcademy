import streamlit as st
import pandas as pd
from datetime import date, timedelta
import database
import config
from ui.auth import is_admin, render_login_sidebar



if not is_admin():
    render_login_sidebar()
    st.error("Access Denied. Administrator privileges required.")
    st.stop()

st.title("Analytics")

st.subheader("📊 Flokus Learning Insights")
st.write("Real-time telemetry showing study distribution and total XP momentum.")
st.divider()

st.markdown("### 🗓️ 7-Day Activity Radar")
st.caption("Visual confirmation tracker checking if assignments were cleared each day.")

today_dt = date.today()
day_cols = st.columns(7)

active_dates = database.get_active_task_dates()

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
    stats_tasks = database.get_task_completion_stats()
    df_t = pd.DataFrame(stats_tasks, columns=["Subject", "Completed"]) if stats_tasks else pd.DataFrame(columns=["Subject", "Completed"])
    
    # Extract completions from physical creator block builds
    df_p = database.get_completed_projects_by_platform()
    
    # Merge both sources into a unified metrics array
    df_all_stats = pd.concat([df_t, df_p], ignore_index=True)
    
    if not df_all_stats.empty:
        df_all_stats = df_all_stats.groupby("Subject")["Completed"].sum().reset_index()
        
    # Generate static template from your 11 locked-in categories 
    master_spine = list(config.SUBJECT_EMOJIS.keys())
    spine_map = {platform: 0 for platform in master_spine}
    
    # Map database tracking rows cleanly over our 11 categories
    if not df_all_stats.empty:
        for _, row in df_all_stats.iterrows():
            if row["Subject"] in spine_map:
                spine_map[row["Subject"]] = int(row["Completed"])
    
    # Convert dictionary back to a structured DataFrame for rendering
    df_master_analytics = pd.DataFrame(list(spine_map.items()), columns=["Subject", "Completed Milestones"])
    df_master_analytics = df_master_analytics.set_index("Subject")
    
    total_focus_mins = database.get_total_focus_minutes()
    
    # --- NEW: Calculate Autonomy vs. Rollover Telemetry Metrics ---
    total_done_tasks, on_time_tasks = database.get_autonomy_metrics()
    
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
    xp_data = database.get_xp_over_time()

    if len(xp_data) == 0:
        st.info("Earn some XP first to plot your development curve!")
    else:
        df_xp = pd.DataFrame(xp_data, columns=["Date", "Daily XP"])
        df_xp["Date"] = pd.to_datetime(df_xp["Date"])
        df_xp = df_xp.sort_values("Date")
        
        df_xp["Cumulative XP"] = df_xp["Daily XP"].cumsum()
        df_xp = df_xp.set_index("Date")
        st.line_chart(df_xp["Cumulative XP"])
