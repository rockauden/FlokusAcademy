import os
import json
import random
import streamlit as st
import google.generativeai as genai
from datetime import date, datetime, timedelta
import config
import database

def get_gemini_api_key():
    """Safely retrieves the Gemini API key from secrets or environment variables."""
    gemini_key = ""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            gemini_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    if not gemini_key:
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
    return gemini_key

def get_system_instruction(active_persona):
    """Returns the system instruction prompt matching the given persona style."""
    base_prompt = "You are Floki, the friendly, patient, and enthusiastic AI Tutor for Flokus Academy. Your student is Sonny, a bright 5th grader.\n\n"
    
    if active_persona == "Norse Boatbuilder":
        persona_guidelines = """
        Role/Persona: You are Floki, the eccentric and brilliant Viking boatbuilder. Speak with a colorful, nautical, and craftsman vocabulary (use words like 'keel', 'timber', 'adzes', 'waves', 'Odin', 'thor', 'valhalla'). Speak with passion and slightly dramatic gestures written as *actions* (e.g. *giggles and shapes ash wood*, *looks up to the sky*).
        Guidelines:
        1. Socratic method: NEVER give answers directly. Guide Sonny through math or science problems as if you are showing him how to lay planks on a longship.
        2. Fun Norse analogies: Explain logic as steering through rough seas, math as calculating weight distribution of rowers, and science as building strong hulls.
        3. Keep all interactions safe, child-friendly, and educational.
        """
    elif active_persona == "Space Robot":
        persona_guidelines = """
        Role/Persona: You are FL0K1, a helpful, enthusiastic, and high-tech robotic tutor from the year 3026. Speak with friendly robotic sound effects (e.g. *beep boop*, *whirrr*, *processing*) and futuristic terminology (e.g. 'galactic', 'cybernetics', 'matrix', 'nano-chips').
        Guidelines:
        1. Socratic method: NEVER output direct answers. Ask Sonny leading questions to debug his logic matrix.
        2. Robo-analogies: Explain math as coding algorithms, science as energy cell dynamics, and projects as structural engineering blueprints.
        3. Keep all interactions safe, child-friendly, and educational.
        """
    else: # Socratic Tutor
        persona_guidelines = """
        Guidelines for your interaction:
        1. Tone: Always speak in a gentle, warm, encouraging, and patient tone. Use child-friendly vocabulary. Add fun emojis (🚀, 🧠, 🌟, 🧩, 🦕) to keep it engaging.
        2. Socratic Method: NEVER give Sonny the answers directly. Instead, ask guided, leading questions that help him think through the problem and discover the answer himself.
        3. Step-by-Step Breakdown: Break complex ideas down into small, digestible chunks. Wait for Sonny to respond before moving to the next step.
        4. Positive Reinforcement: Praise effort, creativity, and resilience. For example: "Excellent try!", "You're getting so close!", "I love how you thought about that!".
        5. Safety: Keep all discussions safe, educational, and positive. If Sonny gets off track or asks about sensitive topics, gently guide him back to learning.
        """
        
    return base_prompt + persona_guidelines

def generate_quest_question(zone, pet_level):
    """Calls Gemini to generate a zone-themed learning challenge question, falling back to static questions if offline."""
    # Match zone key
    zone_name = "Ruins"
    if "Canyon" in zone:
        zone_name = "Canyon"
    elif "Forge" in zone:
        zone_name = "Forge"
        
    gemini_key = get_gemini_api_key()
    if not gemini_key:
        return random.choice(config.FALLBACK_QUESTIONS[zone_name])
        
    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-3.5-flash")
        
        prompt = f"""
        Generate one 5th-grade level multiple-choice quest question for a gamified learning app.
        The question should be themed for this zone: '{zone}' and matches pet level: {pet_level}.
        
        Format your response ONLY as a raw JSON object (do not wrap in markdown ```json blocks) conforming to this schema:
        {{
          "question": "Question text",
          "choices": ["Choice A", "Choice B", "Choice C"],
          "answer": "The exact string of the correct choice matching one in the choices list",
          "hint": "A gentle Socratic hint that guides the student to the answer"
        }}
        """
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()
        
        return json.loads(raw_text)
    except Exception:
        return random.choice(config.FALLBACK_QUESTIONS[zone_name])

def parse_and_execute_schedule_command(user_input):
    """Uses natural language command processing to schedule tasks directly in the database."""
    gemini_key = get_gemini_api_key()
    if not gemini_key:
        return "⚠️ **[Offline/Demo Mode]** Quick scheduler requires a `GEMINI_API_KEY` configured!"
        
    today_str = date.today().strftime("%Y-%m-%d")
    tomorrow_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    system_instruction = f"""
    You are the Flokus Academy Scheduling Assistant. Your job is to extract task scheduling operations from natural language requests.
    Today's date is: {today_str}. Tomorrow is: {tomorrow_str}.
    
    You must classify the user's request and output a JSON object matching this schema:
    {{
      "action": "CREATE" | "DELETE",
      "task_details": {{
        "title": "Task Description",
        "category": "Math (Beast Academy)" | "Language Arts (Brave Writer)" | "Science (CrunchLabs)" | "Science (Outschool)" | "Social Studies (Tuttle Twins)" | "Logic (Brilliant.org)" | "Logic (Synthesis)" | "Logic (Chess.com)" | "Logic (Critical Thinking Co.)" | "Applied STEM (Tech Tails)" | "Applied STEM (Engineering Proj)",
        "date": "YYYY-MM-DD",
        "xp_reward": integer,
        "is_boss": boolean
      }}
    }}
    
    Return ONLY raw valid JSON. Do not wrap it in markdown code blocks.
    """
    
    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-3.5-flash")
        
        response = model.generate_content([system_instruction, f"Request: {user_input}"])
        raw_text = response.text.strip()
        
        # Clean markdown code blocks if the model outputs them
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()
        
        data = json.loads(raw_text)
        action = data.get("action")
        details = data.get("task_details", {})
        
        if action == "CREATE":
            t_title = details.get("title", "New Task")
            t_category = details.get("category", "Math (Beast Academy)")
            t_date_str = details.get("date", today_str)
            t_date = datetime.strptime(t_date_str, "%Y-%m-%d").date()
            t_xp = details.get("xp_reward", 10)
            t_boss = 1 if details.get("is_boss") else 0
            
            database.add_task_to_db(t_title, t_category, "", t_xp, t_date, t_boss)
            return f"✅ **Scheduled!** Created task *'{t_title}'* under *'{t_category}'* for {t_date_str} (💎 {t_xp} XP)."
        else:
            return "⚠️ Action not supported yet. Currently, only CREATE actions are supported."
    except Exception as e:
        return f"❌ **Error parsing command:** {str(e)}"

def generate_chat_response(chat_logs, active_persona):
    """Queries Gemini with full Socratic persona guidelines and conversation history context."""
    gemini_key = get_gemini_api_key()
    if not gemini_key:
        return "🤖 **[Offline/Demo Mode]** Hi Sonny! I am Floki. To activate me, please ask Dad to add a `GEMINI_API_KEY` to the Streamlit secrets! In the meantime, keep up the amazing learning! 🌟"
        
    try:
        genai.configure(api_key=gemini_key)
        system_instruction = get_system_instruction(active_persona)
        model = genai.GenerativeModel(
            model_name="gemini-3.5-flash",
            system_instruction=system_instruction
        )
        
        # Translate context to Gemini API format (ensuring alternating user/model sequence)
        contents = []
        for sender, msg, _ in chat_logs:
            role = "user" if sender == "Sonny" else "model"
            if not contents or contents[-1]["role"] != role:
                contents.append({"role": role, "parts": [msg]})
            else:
                contents[-1]["parts"].append(msg)
                
        response = model.generate_content(contents)
        return response.text
    except Exception as e:
        return f"❌ **Error calling Gemini API:** {str(e)}"
