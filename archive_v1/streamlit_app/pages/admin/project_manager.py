import streamlit as st
import database

st.title("Creator Projects")

st.subheader("Launch a New Creator Block Project")
st.write("Deploy physical kits (like CrunchLabs or Build Box) here. These projects stay active on Sonny's dashboard until he officially marks them as fully built, granting him a massive XP bounty.")

with st.form("new_project_form"):
    proj_title = st.text_input("Project Name (e.g., 'Disc Launcher', 'Mars Rover')")
    proj_platform = st.selectbox("Platform / Kit Source", ["CrunchLabs", "Annual Build Box", "Tech Tails", "Custom Engineering Project"])
    proj_xp = st.number_input("Completion XP Bounty", min_value=50, max_value=5000, value=200, step=50)
    submitted_proj = st.form_submit_button("Deploy Project to Sonny's Dashboard")
    
    if submitted_proj:
        if proj_title.strip() == "":
            st.error("⚠️ Project Name cannot be empty!")
        else:
            database.add_creator_project(proj_title.strip(), proj_platform, proj_xp)
            st.success(f"Project '{proj_title}' successfully launched!")
            st.rerun()

st.divider()
st.subheader("🛠️ Manage Creator Projects")

all_projs = database.get_all_creator_projects()

if not all_projs:
    st.info("No creator projects found.")
else:
    for p in all_projs:
        p_id, p_title, p_platform, p_xp, p_status, p_comp_date, p_summary, p_attach = p
        
        col_p1, col_p2, col_p3 = st.columns([0.6, 0.2, 0.2])
        with col_p1:
            status_badge = "🟢 Completed" if p_status == "Completed" else "⏳ In Progress"
            st.markdown(f"**{p_title}** ({p_platform}) - 💎 {p_xp} XP  \n*Status: {status_badge}*")
            if p_status == "Completed":
                st.markdown(f"*Completed on: {p_comp_date}*")
        
        with col_p2:
            with st.popover("✏️ Edit"):
                edit_p_title = st.text_input("Project Name", value=p_title, key=f"edit_proj_title_{p_id}")
                edit_p_platform = st.selectbox(
                    "Platform / Kit Source",
                    options=["CrunchLabs", "Annual Build Box", "Tech Tails", "Custom Engineering Project"],
                    index=["CrunchLabs", "Annual Build Box", "Tech Tails", "Custom Engineering Project"].index(p_platform) if p_platform in ["CrunchLabs", "Annual Build Box", "Tech Tails", "Custom Engineering Project"] else 0,
                    key=f"edit_proj_plat_{p_id}"
                )
                edit_p_xp = st.number_input("XP Bounty", min_value=10, max_value=5000, value=int(p_xp), step=50, key=f"edit_proj_xp_{p_id}")
                edit_p_status = st.selectbox("Status", ["In Progress", "Completed"], index=0 if p_status == "In Progress" else 1, key=f"edit_proj_status_{p_id}")
                
                if st.button("Save Changes", key=f"save_proj_btn_{p_id}"):
                    if edit_p_title.strip() == "":
                        st.error("Project Name cannot be empty!")
                    else:
                        database.update_creator_project(
                            p_id, edit_p_title.strip(), edit_p_platform, edit_p_xp, 
                            status=edit_p_status, completion_date=p_comp_date if edit_p_status == "Completed" else "", 
                            project_summary=p_summary, project_attachment=p_attach
                        )
                        st.success("Project updated!")
                        st.rerun()
        
        with col_p3:
            with st.popover("❌ Delete"):
                st.write("Are you sure you want to delete this project?")
                if st.button("Confirm Delete", key=f"del_proj_btn_{p_id}"):
                    database.delete_creator_project(p_id)
                    st.success("Project deleted!")
                    st.rerun()
