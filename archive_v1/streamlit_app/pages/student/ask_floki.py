import streamlit as st
import os
import database
import ai_tutor

st.title("💬 Ask Floki: Your AI Learning Buddy")
st.markdown("*Floki is here to help you study, answer your questions, and coach you through quests!*")

# Display chat history
session_id = "sonny_study_session"
chat_logs = database.get_chat_history(session_id)

for sender, msg, timestamp in chat_logs:
    role = "assistant" if sender == "Floki" else "user"
    with st.chat_message(role):
        st.write(msg)
        
# API check
gemini_key = ""
try:
    if "GEMINI_API_KEY" in st.secrets:
        gemini_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass
if not gemini_key:
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    
# Quick chip buttons
st.write("💡 *Quick topics:*")
cols_chips = st.columns(4)
quick_prompts = [
    ("🧩 Math Helper", "Can you help me understand today's math quest using the Socratic method?"),
    ("🧬 Science Guide", "Tell me how a volcano erupts step-by-step without giving me direct answers!"),
    ("🐉 Boss Fight Tips", "I need coaching and encouragement for my boss fight quest today!"),
    ("🧠 Riddle Time", "Can you give me a Socratic logic riddle to solve?")
]

triggered_prompt = ""
for index, (lbl, text) in enumerate(quick_prompts):
    with cols_chips[index % 4]:
        if st.button(lbl, key=f"quick_prompt_btn_{index}", use_container_width=True):
            triggered_prompt = text
            
# Input Box
user_input = st.chat_input("Talk to Floki...")
if triggered_prompt:
    user_input = triggered_prompt
    
if user_input:
    # 1. Add user message to UI
    with st.chat_message("user"):
        st.write(user_input)
    database.add_chat_msg(session_id, "Sonny", user_input)
    
    # 2. Call Gemini
    active_persona = database.get_floki_persona()
    full_history = database.get_chat_history(session_id)
    
    with st.spinner("Floki is thinking..."):
        floki_reply = ai_tutor.generate_chat_response(full_history, active_persona)
                
    # 3. Add assistant message to UI
    with st.chat_message("assistant"):
        st.write(floki_reply)
    database.add_chat_msg(session_id, "Floki", floki_reply)
    st.rerun()
