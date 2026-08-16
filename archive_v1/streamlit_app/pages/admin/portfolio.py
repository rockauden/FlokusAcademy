import streamlit as st
from datetime import date, timedelta
import os
import database
import config

st.title("Portfolio")

portfolio_date = st.date_input("📅 Select Date to Review:", value=date.today(), key="admin_portfolio_date")
day_display = portfolio_date.strftime("%A, %b %d")

st.subheader(f"Completed Tasks ({day_display})")

admin_completed_tasks = database.get_completed_tasks(portfolio_date) 

if len(admin_completed_tasks) == 0:
    st.info(f"No completed tasks found for {day_display}.")
else:
    for task in admin_completed_tasks:
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            emoji = config.SUBJECT_EMOJIS.get(task[2], "📋")
            if task[5] == 1:
                st.markdown(f"👑 **{emoji} {task[2]}**: {task[1]} *(Boss Fight!)*")
            else:
                st.markdown(f"✅ **{emoji} {task[2]}**: {task[1]}")
            
            if task[6] and task[6].strip() != "":
                st.info(f"💭 **Sonny's Notes:** {task[6]}")
            
        with col2:
            if st.button("❌", key=f"del_task_{task[0]}"):
                database.delete_task(task[0])
                st.rerun()
                
admin_completed_projects = database.get_completed_projects(portfolio_date)
if len(admin_completed_projects) > 0:
    st.markdown("### 🛠️ Completed Creator Projects")
    for proj in admin_completed_projects:
        st.markdown(f"✅ **{proj[2]}**: {proj[1]} *(💎 {proj[3]} XP)*")
        if proj[4] and proj[4].strip() != "":
            st.info(f"💭 **Sonny's Project Notes:** {proj[4]}")
        
        # --- Render Attachment in Portfolio Review ---
        if len(proj) > 5 and proj[5] and proj[5].strip() != "":
            file_path = proj[5]
            if os.path.exists(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                if ext in [".png", ".jpg", ".jpeg"]:
                    st.image(file_path, caption=f"📸 Uploaded Image for {proj[1]}", use_container_width=True)
                elif ext in [".mp4", ".mov"]:
                    st.video(file_path)
                else:
                    try:
                        with open(file_path, "rb") as f:
                            file_bytes = f.read()
                        fn = os.path.basename(file_path)
                        st.download_button(
                            label=f"📎 Download Attachment: {fn}",
                            data=file_bytes,
                            file_name=fn,
                            key=f"download_attachment_{proj[0]}"
                        )
                    except Exception as e:
                        st.error(f"Could not load attachment file: {file_path}")
            else:
                st.warning(f"⚠️ Attachment file not found: {file_path}")
        # --- END NEW ---
            
st.divider()
st.markdown("### 🖨️ Official Portfolio Export")
st.write("Generate a complete, compliance-ready CSV report of all completed tasks and projects.")

# --- Date Range Calendar Layout selectors ---
r_col1, r_col2 = st.columns(2)
with r_col1:
    export_start = st.date_input("📅 Report Start Date:", value=date.today() - timedelta(days=30))
with r_col2:
    export_end = st.date_input("📅 Report End Date:", value=date.today())
    
# Pass calendar choices into our updated range data-fetcher function
portfolio_df = database.get_full_portfolio_data(export_start, export_end)
# --- END NEW ---

if portfolio_df.empty:
    st.info("No completed assignments found matching this specific date window.")
else:
    csv_data = portfolio_df.to_csv(index=False).encode('utf-8')
    
    # Dynamic naming maps window to filename for easy file tracking
    start_fn = export_start.strftime('%Y_%m_%d')
    end_fn = export_end.strftime('%Y_%m_%d')
    
    st.download_button(
        label=f"📥 Download Portfolio Range ({start_fn} to {end_fn})",
        data=csv_data,
        file_name=f"Flokus_Portfolio_{start_fn}_to_{end_fn}.csv",
        mime="text/csv",
        use_container_width=True
    )
