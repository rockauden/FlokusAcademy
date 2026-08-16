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

st.divider()
st.markdown("### 📝 Mission Settings")
st.caption("Configure requirements for student mission completion.")
current_min_length = database.get_note_min_length()
new_min_length = st.number_input(
    "Minimum Characters for Mission Notes", 
    min_value=0, max_value=500, value=current_min_length, step=5,
    help="The minimum number of characters required when Sonny writes what he learned to mark a mission complete."
)
if new_min_length != current_min_length:
    database.set_note_min_length(new_min_length)
    st.success(f"Minimum note length updated to {new_min_length} characters.")
    st.rerun()

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
        st.warning("⚠️ **Warning:** This will permanently erase test tasks, test creator builds, purchase logs, chat history, and reset UFA expenses back to baseline Odyssey defaults!")
        if st.button("🔴 Confirm Reset All Data", key="confirm_reset_all_data_btn", use_container_width=True):
            database.reset_all_test_data()
            st.success("🎉 Database reset complete! App is ready for live use.")
            st.rerun()
# --- END NEW ---
        
