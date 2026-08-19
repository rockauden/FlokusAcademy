import streamlit as st
import pandas as pd
from datetime import date, timedelta
import database
import config
from ui.auth import is_admin, render_login_sidebar



import plotly.express as px
import plotly.graph_objects as go

if not is_admin():
    render_login_sidebar()
    st.error("Access Denied. Administrator privileges required.")
    st.stop()

col_h1, col_h2 = st.columns([0.7, 0.3])
with col_h1:
    st.title("📊 Learning Intelligence Dashboard")
    st.caption(f"Curriculum telemetry for Sonny's 5th Grade Program — "
               f"Updated {date.today().strftime('%A, %B %d, %Y')}")
with col_h2:
    total_xp = database.get_xp_balance()
    st.metric("Total XP Earned", f"💎 {total_xp}")

st.divider()

st.markdown("### 🗓️ 7-Day Activity Radar")
st.caption("Visual confirmation tracker checking if assignments were cleared each day.")

today_dt = date.today()
day_cols = st.columns(7)

active_dates = database.get_active_task_dates()

for i in range(7):
    check_date = today_dt - timedelta(days=6-i)
    date_str = check_date.strftime("%Y-%m-%d")
    
    pending = database.get_pending_tasks(check_date)
    completed = database.get_completed_tasks(check_date)
    total = len(pending) + len(completed)
    done = len(completed)
    
    with day_cols[i]:
        if total == 0:
            color, icon = "#4a5568", "—"
        elif done == total and done > 0:
            color, icon = "#22c55e", "✓"
        elif done > 0:
            color, icon = "#f6ad55", f"{done}/{total}"
        else:
            color, icon = "#f56565", f"0/{total}"
            
        st.markdown(f"""
        <div style="text-align:center; background:#121626; border:1px solid #283254;
             border-radius:10px; padding:10px 4px;">
            <div style="font-size:20px; font-weight:800; color:{color};">{icon}</div>
            <div style="font-size:11px; color:#8c9bb4; margin-top:4px; font-weight:600;">
                {check_date.strftime('%a')}<br>
                <span style="font-size:10px; color:#4a5568;">
                    {check_date.strftime('%b %d')}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
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
    
    # "Total Deep Work Focus Time" was dropped with the focus-sprint timer
    # (2026-08-18). It summed the durations Sonny had punched into a countdown,
    # so it measured button presses rather than work, and reporting it as
    # "deep work" gave a false number a lot of authority.
    total_done_tasks, on_time_tasks = database.get_autonomy_metrics()
    autonomy_score = int((on_time_tasks / total_done_tasks) * 100) if total_done_tasks > 0 else 100

    st.metric(label="🎯 On-Schedule Completion Rating", value=f"{autonomy_score}%")
    st.write("")
    # --- END NEW ---
    
    # Plot the finalized telemetry bar chart
    if df_master_analytics["Completed Milestones"].sum() == 0:
        st.info("📊 Telemetry offline. Complete daily quests or building projects to activate tracking!")
    else:
        df_plot = df_master_analytics.reset_index()
        df_plot.columns = ["Subject", "Count"]
        df_plot["Short"] = df_plot["Subject"].str.extract(r'\(([^)]+)\)')
        df_plot["Short"] = df_plot["Short"].fillna(df_plot["Subject"])
        df_plot = df_plot.sort_values("Count", ascending=True)

        fig = go.Figure(go.Bar(
            x=df_plot["Count"],
            y=df_plot["Short"],
            orientation='h',
            marker=dict(
                color=df_plot["Count"],
                colorscale=[[0, "#1e2236"], [0.5, "#3b82f6"], [1.0, "#22c55e"]],
                line=dict(color="#283254", width=1)
            ),
            text=df_plot["Count"],
            textposition="outside",
            textfont=dict(color="#e2e8f0", size=12)
        ))
        fig.update_layout(
            paper_bgcolor="#0c0e17",
            plot_bgcolor="#0c0e17",
            font=dict(color="#e2e8f0", family="Outfit"),
            xaxis=dict(gridcolor="#1f2336", color="#8c9bb4"),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", color="#e2e8f0"),
            margin=dict(l=10, r=30, t=10, b=10),
            height=320
        )
        st.plotly_chart(fig, use_container_width=True)
        
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
