import streamlit as st
from datetime import date
import database
from ui.auth import is_admin, render_login_sidebar



if not is_admin():
    render_login_sidebar()
    st.error("Access Denied. Administrator privileges required.")
    st.stop()

st.title("AI Safety & Settings")

st.markdown("### 📜 Sonny's Chat Transcripts")
st.caption("Review recent Socratic dialogues between Sonny and Floki.")

session_id = "sonny_study_session"
chat_logs = database.get_chat_history(session_id)
if len(chat_logs) == 0:
    st.info("No chat logs recorded yet.")
else:
    # Display chat logs in a scrollable container
    chat_text = ""
    for sender, msg, timestamp in chat_logs:
        chat_text += f"[{timestamp}] {sender}: {msg}\n"
        chat_text += "-" * 40 + "\n"
    st.text_area("Full Chat Transcript", chat_text, height=300, disabled=True)
    
    # Button to clear chat history
    if st.button("🧹 Clear Chat History", key="clear_chat_history_btn"):
        database.clear_chat_history(session_id)
        st.success("Chat history cleared!")
        st.rerun()
        
# --- NEW: Floki Persona Configuration ---
st.divider()
st.markdown("### 🎭 Floki Persona Configuration")
st.caption("Change Floki's personality to keep Sonny engaged with different teaching styles.")
current_p = database.get_floki_persona()
selected_p = st.selectbox(
    "Active Persona",
    ["Socratic Tutor", "Norse Boatbuilder", "Space Robot"],
    index=["Socratic Tutor", "Norse Boatbuilder", "Space Robot"].index(current_p) if current_p in ["Socratic Tutor", "Norse Boatbuilder", "Space Robot"] else 0
)
if selected_p != current_p:
    database.set_floki_persona(selected_p)
    st.success(f"Floki's persona updated to {selected_p}!")
    st.rerun()
# --- END NEW ---

# --- NEW: One-Click Database Backups & Reset ---
st.divider()
st.markdown("### 📦 Database Management & Go-Live Prep")
st.caption("Manage database backups or clear test data before launching.")

db_col1, db_col2 = st.columns(2)
with db_col1:
    try:
        with open("flokus.db", "rb") as f:
            db_bytes = f.read()
    except Exception:
        db_bytes = b""
        
    if db_bytes:
        st.download_button(
            label="📥 Backup flokus.db",
            data=db_bytes,
            file_name=f"flokus_backup_{date.today().strftime('%Y_%m_%d')}.db",
            mime="application/x-sqlite3",
            use_container_width=True
        )
    else:
        st.error("Failed to read database file.")
        
with db_col2:
    with st.popover("🧹 Clear Test Data & Go Live", use_container_width=True):
        st.warning("⚠️ **Warning:** This will permanently erase test tasks, test creator builds, purchase logs, chat history, and reset Sparky & UFA expenses back to baseline defaults!")
        if st.button("🔴 Confirm Reset All Data", key="confirm_reset_all_data_btn", use_container_width=True):
            database.reset_all_test_data()
            st.success("🎉 Database reset complete! App is ready for live use.")
            st.rerun()
# --- END NEW ---
        
st.divider()
st.markdown("### 🐾 Pet Override Console")
st.caption("Manually adjust Sparky's levels or statistics for testing or corrections.")

pet = database.get_pet_status()
if pet:
    pet_id, pet_name, pet_level, pet_xp, strength, intelligence, creativity, stamina, max_stamina, happiness, stage, form_name, accessory_parts = pet
    
    with st.form("pet_override_form"):
        new_name = st.text_input("Override Pet Name", value=pet_name)
        new_level = st.number_input("Override Level", min_value=1, max_value=100, value=pet_level)
        new_xp = st.number_input("Override Current XP", min_value=0, value=pet_xp)
        new_str = st.number_input("Override Strength", min_value=1, value=strength)
        new_int = st.number_input("Override Intelligence", min_value=1, value=intelligence)
        new_crt = st.number_input("Override Creativity", min_value=1, value=creativity)
        new_stamina = st.number_input("Override Stamina", min_value=0, max_value=100, value=stamina)
        new_max_stamina = st.number_input("Override Max Stamina", min_value=1, max_value=100, value=max_stamina)
        
        # Stage selection
        stage_options = ["Egg", "Baby", "Rookie", "Champion", "Ultimate", "Mega"]
        new_stage = st.selectbox("Override Stage", stage_options, index=stage_options.index(stage) if stage in stage_options else 0)
        new_form_name = st.text_input("Override Form Name", value=form_name)
        
        if st.form_submit_button("Save Override Changes"):
            database.override_pet_status(pet_id, new_name, new_level, new_xp, new_str, new_int, new_crt, new_stamina, new_max_stamina, new_stage, new_form_name)
            st.success("Pet overridden successfully!")
            st.rerun()
