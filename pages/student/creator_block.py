import streamlit as st
import os
import time
import database

st.title("🛠️ Creator Block")
st.subheader("Active Creator Projects")
st.write("Take your time. Physical builds require patience. Claim your massive XP reward only when the final project is fully functional!")
st.divider()

active_projects = database.get_active_projects()

if len(active_projects) == 0:
    st.info("No active building projects right now. Time to ask Dad for a new CrunchLab!")
else:
    for proj in active_projects:
        p_id, p_title, p_platform, p_xp = proj
        
        with st.container(border=True):
            st.markdown(f"### ⚙️ {p_title}")
            st.write(f"**Platform:** {p_platform}  |  **Bounty:** 💎 {p_xp} XP")
            
            proj_note_input = st.text_area(
                "📝 Project Report: What did you build, and how does it work?", 
                key=f"proj_note_input_{p_id}"
            )
            
            uploaded_file = st.file_uploader(
                "📎 Upload photo, video, or document evidence:",
                type=["png", "jpg", "jpeg", "mp4", "mov", "pdf", "docx"],
                key=f"file_uploader_{p_id}"
            )
            
            note_len = len(proj_note_input.strip())
            btn_disabled = note_len < 30
            
            if btn_disabled:
                st.warning(f"⚠️ Report must be at least 30 characters. (Current: {note_len}/30)")
            
            if st.button(f"✅ Mark Build Complete & Claim {p_xp} XP", key=f"complete_proj_{p_id}", disabled=btn_disabled):
                saved_path = ""
                if uploaded_file is not None:
                    os.makedirs("uploads", exist_ok=True)
                    base_fn = os.path.basename(uploaded_file.name)
                    sanitized_fn = "".join(c for c in base_fn if c.isalnum() or c in "._- ")
                    safe_filename = f"{int(time.time())}_{sanitized_fn}"
                    saved_path = os.path.join("uploads", safe_filename)
                    with open(saved_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                        
                database.complete_creator_project(p_id, proj_note_input, saved_path)
                st.session_state.show_balloons = True
                st.success(f"Epic job! You successfully built the {p_title} and earned {p_xp} XP!")
                st.rerun()
            st.divider()
