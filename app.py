import streamlit as st
import sqlite3
from datetime import date, datetime, timedelta
import pandas as pd
import time
import os

# ==========================================
# DATABASE SETUP & HELPER FUNCTIONS
# ==========================================

def verify_db_schema():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    
    # Verify inventory_qty column in rewards table
    try:
        cursor.execute("SELECT inventory_qty FROM rewards LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE rewards ADD COLUMN inventory_qty INTEGER DEFAULT 1")
        conn.commit()
        
    # Verify is_boss_fight column in tasks table
    try:
        cursor.execute("SELECT is_boss_fight FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE tasks ADD COLUMN is_boss_fight INTEGER DEFAULT 0")
        conn.commit()
        
    # Verify task_summary column in tasks table
    try:
        cursor.execute("SELECT task_summary FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE tasks ADD COLUMN task_summary TEXT DEFAULT ''")
        conn.commit()
        
    # Verify creator_projects table exists
    try:
        cursor.execute("SELECT id FROM creator_projects LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS creator_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                platform TEXT,
                status TEXT DEFAULT 'In Progress',
                xp_reward INTEGER
            )
        """)
        conn.commit()

    # Verify self-healing upgrade for Creator Projects Portfolio Tracking
    try:
        cursor.execute("SELECT completion_date FROM creator_projects LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE creator_projects ADD COLUMN completion_date TEXT DEFAULT ''")
        cursor.execute("ALTER TABLE creator_projects ADD COLUMN project_summary TEXT DEFAULT ''")
        conn.commit()
    
    # --- NEW: Self-Healing Focus Minutes Tracker Column ---
    try:
        cursor.execute("SELECT focus_minutes FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE tasks ADD COLUMN focus_minutes INTEGER DEFAULT 0")
        conn.commit()
    # --- END NEW ---
    
    # --- NEW: Self-Healing Actual Completion Date Stamp Column ---
    try:
        cursor.execute("SELECT actual_completion_date FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE tasks ADD COLUMN actual_completion_date TEXT DEFAULT ''")
        conn.commit()
    # --- END NEW ---
    
    # --- NEW: Self-Healing Creator Projects Media Attachment Column ---
    try:
        cursor.execute("SELECT project_attachment FROM creator_projects LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE creator_projects ADD COLUMN project_attachment TEXT DEFAULT ''")
        conn.commit()
    # --- END NEW ---
    
    # --- NEW: Digital Pet & AI Chat Tables Migration ---
    # 1. Verify pet_status table
    try:
        cursor.execute("SELECT id FROM pet_status LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pet_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pet_name TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                current_xp INTEGER DEFAULT 0,
                strength INTEGER DEFAULT 5,
                intelligence INTEGER DEFAULT 5,
                creativity INTEGER DEFAULT 5,
                stamina INTEGER DEFAULT 10,
                max_stamina INTEGER DEFAULT 10,
                happiness INTEGER DEFAULT 100,
                stage TEXT DEFAULT 'Egg',
                form_name TEXT DEFAULT 'Cosmic Egg',
                accessory_parts TEXT DEFAULT '[]'
            )
        """)
        cursor.execute("INSERT INTO pet_status (pet_name, stage, form_name) VALUES ('Sparky', 'Egg', 'Cosmic Egg')")
        conn.commit()

    # 2. Verify pet_inventory table
    try:
        cursor.execute("SELECT id FROM pet_inventory LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pet_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT UNIQUE,
                quantity INTEGER DEFAULT 0
            )
        """)
        cursor.execute("INSERT OR IGNORE INTO pet_inventory (item_name, quantity) VALUES ('🥩 Cyber-Protein', 2)")
        cursor.execute("INSERT OR IGNORE INTO pet_inventory (item_name, quantity) VALUES ('💾 Memory Chip', 2)")
        cursor.execute("INSERT OR IGNORE INTO pet_inventory (item_name, quantity) VALUES ('🖌️ Chameleon Ink', 2)")
        cursor.execute("INSERT OR IGNORE INTO pet_inventory (item_name, quantity) VALUES ('⚡ Giga-Soda', 1)")
        conn.commit()

    # 3. Verify pet_quests table
    try:
        cursor.execute("SELECT id FROM pet_quests LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pet_quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone_name TEXT NOT NULL,
                stage_progress INTEGER DEFAULT 1,
                active_quest_state TEXT DEFAULT NULL
            )
        """)
        conn.commit()

    # 4. Verify chat_history table
    try:
        cursor.execute("SELECT id FROM chat_history LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    # 5. Auto-seed XP Store with Pet Care items if missing
    pet_store_items = [
        ("🥩 Cyber-Protein", 25, 10),
        ("💾 Memory Chip", 25, 10),
        ("🖌️ Chameleon Ink", 25, 10),
        ("⚡ Giga-Soda", 15, 10),
        ("🔮 Omni-Treat", 35, 5),
        ("🗝️ Evolution Matrix", 100, 2)
    ]
    for name, cost, qty in pet_store_items:
        cursor.execute("SELECT id FROM rewards WHERE name = ?", (name,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO rewards (name, xp_cost, inventory_qty) VALUES (?, ?, ?)", (name, cost, qty))
    # 6. Verify purchases table is_claimed column exists
    try:
        cursor.execute("SELECT is_claimed FROM purchases LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE purchases ADD COLUMN is_claimed INTEGER DEFAULT 0")
        conn.commit()

    # 7. Verify app_config table exists
    try:
        cursor.execute("SELECT key FROM app_config LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_config (
                key TEXT UNIQUE,
                value TEXT
            )
        """)
        cursor.execute("INSERT OR IGNORE INTO app_config (key, value) VALUES ('floki_persona', 'Socratic Tutor')")
        conn.commit()
    # --- END NEW ---
    
    conn.close()

verify_db_schema()

def add_creator_project(title, platform, xp_reward):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO creator_projects (title, platform, xp_reward) VALUES (?, ?, ?)", (title, platform, xp_reward))
    conn.commit()
    conn.close()

def get_active_projects():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, platform, xp_reward FROM creator_projects WHERE status = 'In Progress'")
    projects = cursor.fetchall()
    conn.close()
    return projects

def complete_creator_project(project_id, summary="", attachment=""):
    today_string = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    
    # 1. Fetch project details
    cursor.execute("SELECT xp_reward FROM creator_projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    
    cursor.execute("""
        UPDATE creator_projects 
        SET status = 'Completed', completion_date = ?, project_summary = ?, project_attachment = ? 
        WHERE id = ?
    """, (today_string, summary, attachment, project_id))
    
    # 3. Update pet XP & Stats if details found
    if row:
        xp_earned = row[0]
        cursor.execute("SELECT id, level, current_xp, strength, intelligence, creativity, stage, form_name FROM pet_status LIMIT 1")
        pet = cursor.fetchone()
        if pet:
            p_id, level, current_xp, str_val, int_val, crt_val, stage, form_name = pet
            
            # Creator projects boost Creativity massively!
            new_crt = crt_val + 5
            new_str = str_val + 1
            new_int = int_val
            
            new_xp = current_xp + xp_earned
            next_level_xp = int(100 * (level)**1.8)
            new_level = level
            new_stage = stage
            new_form = form_name
            
            if new_xp >= next_level_xp:
                new_level += 1
                new_xp = max(0, new_xp - next_level_xp)
                new_stage, new_form = calculate_evolution_internal(new_level, new_str, new_int, new_crt)
                
            cursor.execute("""
                UPDATE pet_status 
                SET level = ?, current_xp = ?, strength = ?, intelligence = ?, creativity = ?, stage = ?, form_name = ?
                WHERE id = ?
            """, (new_level, new_xp, new_str, new_int, new_crt, new_stage, new_form, p_id))
            
    conn.commit()
    conn.close()

def get_completed_projects(view_date):
    date_string = view_date.strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, platform, xp_reward, project_summary, project_attachment 
        FROM creator_projects 
        WHERE status = 'Completed' AND completion_date = ?
    """, (date_string,))
    projects = cursor.fetchall()
    conn.close()
    return projects

def add_task_to_db(title, category, video_url, xp_reward, target_date, is_boss):
    date_string = target_date.strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks (title, category, task_date, video_url, xp_reward, is_boss_fight) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, category, date_string, video_url, xp_reward, is_boss))
    conn.commit()
    conn.close()

def get_pending_tasks(view_date):
    date_string = view_date.strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    
    if view_date == date.today():
        cursor.execute("""
            SELECT id, title, category, video_url, xp_reward, is_boss_fight 
            FROM tasks 
            WHERE is_completed = 0 AND task_date <= ?
            ORDER BY task_date ASC
        """, (date_string,))
    else:
        cursor.execute("""
            SELECT id, title, category, video_url, xp_reward, is_boss_fight 
            FROM tasks 
            WHERE is_completed = 0 AND task_date = ?
        """, (date_string,))
        
    tasks = cursor.fetchall()
    conn.close()
    return tasks

# --- NEW: Adapt complete_task to accept focus runtime metrics and update pet status ---
def complete_task(task_id, summary="", minutes=0):
    # --- NEW: Auto-stamp today's string on task completion ---
    today_str = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    
    # 1. Fetch details of task before completing it
    cursor.execute("SELECT category, is_boss_fight, xp_reward FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    
    cursor.execute("""
        UPDATE tasks 
        SET is_completed = 1, task_summary = ?, focus_minutes = ?, actual_completion_date = ? 
        WHERE id = ?
    """, (summary, minutes, today_str, task_id))
    
    # 3. Update pet XP & Stats if task details are found
    if row:
        category, is_boss, xp = row
        xp_earned = xp * 2 if is_boss == 1 else xp
        
        # Get pet status
        cursor.execute("SELECT id, level, current_xp, strength, intelligence, creativity, stage, form_name FROM pet_status LIMIT 1")
        pet = cursor.fetchone()
        if pet:
            p_id, level, current_xp, str_val, int_val, crt_val, stage, form_name = pet
            
            # Determine stat updates
            new_int = int_val
            new_str = str_val
            new_crt = crt_val
            
            if "Math" in category or "Logic" in category:
                new_int += 1
            elif "Language" in category or "Creator" in category or "STEM" in category:
                new_crt += 1
                
            if is_boss == 1:
                new_str += 2
            else:
                new_str += 1
                
            # Update XP
            new_xp = current_xp + xp_earned
            next_level_xp = int(100 * (level)**1.8)
            new_level = level
            new_stage = stage
            new_form = form_name
            
            if new_xp >= next_level_xp:
                new_level += 1
                new_xp = max(0, new_xp - next_level_xp)
                new_stage, new_form = calculate_evolution_internal(new_level, new_str, new_int, new_crt)
                
            cursor.execute("""
                UPDATE pet_status 
                SET level = ?, current_xp = ?, strength = ?, intelligence = ?, creativity = ?, stage = ?, form_name = ?
                WHERE id = ?
            """, (new_level, new_xp, new_str, new_int, new_crt, new_stage, new_form, p_id))
            
    conn.commit()
    conn.close()
    # --- END NEW ---

def get_completed_tasks(view_date):
    date_string = view_date.strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, category, video_url, xp_reward, is_boss_fight, task_summary 
        FROM tasks 
        WHERE is_completed = 1 AND task_date = ?
    """, (date_string,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def delete_task(task_id):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# --- NEW: Task management and database CRUD helper functions ---
def update_task_details(task_id, title, category, video_url, xp_reward, target_date, is_boss):
    date_string = target_date.strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tasks 
        SET title = ?, category = ?, video_url = ?, xp_reward = ?, task_date = ?, is_boss_fight = ?
        WHERE id = ?
    """, (title, category, video_url, xp_reward, date_string, is_boss, task_id))
    conn.commit()
    conn.close()

def get_all_pending_tasks():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, category, video_url, xp_reward, is_boss_fight, task_date 
        FROM tasks 
        WHERE is_completed = 0 
        ORDER BY task_date ASC, id ASC
    """)
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def update_creator_project(project_id, title, platform, xp_reward, status="In Progress", completion_date="", project_summary="", project_attachment=""):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE creator_projects 
        SET title = ?, platform = ?, xp_reward = ?, status = ?, completion_date = ?, project_summary = ?, project_attachment = ?
        WHERE id = ?
    """, (title, platform, xp_reward, status, completion_date, project_summary, project_attachment, project_id))
    conn.commit()
    conn.close()

def delete_creator_project(project_id):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM creator_projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

def update_expense_details(expense_id, item_name, cost, category, status):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE expenses 
        SET item_name = ?, cost = ?, category = ?, status = ?
        WHERE id = ?
    """, (item_name, cost, category, status, expense_id))
    conn.commit()
    conn.close()

# --- NEW: Digital Pet and AI Chat Helpers ---
def calculate_evolution_internal(level, strength, intelligence, creativity):
    if level >= 51:
        return "Mega", "Mecha-Wyrm 🐉"
    elif level >= 31:
        return "Ultimate", "Matrix-Colossus 🕷️"
    elif level >= 16:
        top_stat = max(strength, intelligence, creativity)
        if top_stat == intelligence:
            return "Champion", "Cyber-Drake 🐉"
        elif top_stat == creativity:
            return "Champion", "Origami-Phoenix 🐦"
        else:
            return "Champion", "Mecha-Gorilla 🦍"
    elif level >= 6:
        top_stat = max(strength, intelligence, creativity)
        if top_stat == intelligence:
            return "Rookie", "Techno-Mite 🐜"
        elif top_stat == creativity:
            return "Rookie", "Chalk-Pup 🎨"
        else:
            return "Rookie", "Brawn-Chimp 🐒"
    elif level >= 2:
        return "Baby", "Omni-Blob 🧬"
    else:
        return "Egg", "Cosmic Egg 🥚"

def get_pet_status():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, pet_name, level, current_xp, strength, intelligence, creativity, stamina, max_stamina, happiness, stage, form_name, accessory_parts 
        FROM pet_status LIMIT 1
    """)
    pet = cursor.fetchone()
    conn.close()
    return pet

def use_pet_item(item_name):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    
    # Verify quantity
    cursor.execute("SELECT quantity FROM pet_inventory WHERE item_name = ?", (item_name,))
    row = cursor.fetchone()
    if not row or row[0] <= 0:
        conn.close()
        return "⚠️ You don't have this item in stock!"
        
    # Deduct quantity
    cursor.execute("UPDATE pet_inventory SET quantity = quantity - 1 WHERE item_name = ?", (item_name,))
    
    # Get pet stats
    cursor.execute("SELECT id, strength, intelligence, creativity, stamina, max_stamina FROM pet_status LIMIT 1")
    pet = cursor.fetchone()
    if pet:
        p_id, str_val, int_val, crt_val, stam, max_stam = pet
        new_str = str_val
        new_int = int_val
        new_crt = crt_val
        new_stam = stam
        
        stat_effect = ""
        if "Cyber-Protein" in item_name:
            new_str += 3
            stat_effect = "Strength +3"
        elif "Memory Chip" in item_name:
            new_int += 3
            stat_effect = "Intelligence +3"
        elif "Chameleon Ink" in item_name:
            new_crt += 3
            stat_effect = "Creativity +3"
        elif "Giga-Soda" in item_name:
            new_stam = min(max_stam, new_stam + 5)
            stat_effect = "Stamina +5"
        elif "Omni-Treat" in item_name:
            new_str += 1
            new_int += 1
            new_crt += 1
            new_stam = min(max_stam, new_stam + 2)
            stat_effect = "All Stats +1, Stamina +2"
        elif "Evolution Matrix" in item_name:
            # Evolution matrix acts as a level up trigger / evolution force
            # Give enough XP to reach next level
            # Get current level and XP
            cursor.execute("SELECT level, current_xp FROM pet_status WHERE id = ?", (p_id,))
            pet_lvl_xp = cursor.fetchone()
            if pet_lvl_xp:
                lvl, cur_xp = pet_lvl_xp
                next_lvl_xp = int(100 * (lvl)**1.8)
                
                # Award this XP
                new_lvl = lvl + 1
                new_xp = 0
                new_stage, new_form = calculate_evolution_internal(new_lvl, new_str, new_int, new_crt)
                
                cursor.execute("""
                    UPDATE pet_status 
                    SET level = ?, current_xp = ?, stage = ?, form_name = ?
                    WHERE id = ?
                """, (new_lvl, new_xp, new_stage, new_form, p_id))
                stat_effect = f"Evolved to Level {new_lvl}!"
        
        if "Evolution Matrix" not in item_name:
            cursor.execute("""
                UPDATE pet_status 
                SET strength = ?, intelligence = ?, creativity = ?, stamina = ?
                WHERE id = ?
            """, (new_str, new_int, new_crt, new_stam, p_id))
            
        conn.commit()
        conn.close()
        return f"🎉 Used {item_name}! ({stat_effect})"
    
    conn.close()
    return "❌ Error using item!"

def add_chat_msg(session_id, sender, message):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_history (session_id, sender, message) 
        VALUES (?, ?, ?)
    """, (session_id, sender, message))
    conn.commit()
    conn.close()

def get_chat_history(session_id):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sender, message, timestamp 
        FROM chat_history 
        WHERE session_id = ? 
        ORDER BY id ASC
    """, (session_id,))
    history = cursor.fetchall()
    return history

def get_floki_persona():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_config WHERE key = 'floki_persona'")
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return "Socratic Tutor"

def set_floki_persona(persona):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO app_config (key, value) VALUES ('floki_persona', ?)", (persona,))
    conn.commit()
    conn.close()

def parse_and_execute_schedule_command(user_input):
    gemini_key = ""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            gemini_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    if not gemini_key:
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        
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
        import google.generativeai as genai
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
            
            add_task_to_db(t_title, t_category, "", t_xp, t_date, t_boss)
            return f"✅ **Scheduled!** Created task *'{t_title}'* under *'{t_category}'* for {t_date_str} (💎 {t_xp} XP)."
        else:
            return "⚠️ Action not supported yet. Currently, only CREATE actions are supported."
    except Exception as e:
        return f"❌ **Error parsing command:** {str(e)}"
# --- END NEW ---

def add_expense(item_name, cost, category, status):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO expenses (item_name, cost, category, status) VALUES (?, ?, ?, ?)", 
                   (item_name, cost, category, status))
    conn.commit()
    conn.close()

def get_all_expenses():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_name, cost, category, status FROM expenses")
    expenses = cursor.fetchall()
    conn.close()
    return expenses

def update_expense_status(expense_id, new_status):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE expenses SET status = ? WHERE id = ?", (new_status, expense_id))
    conn.commit()
    conn.close()

def delete_expense(expense_id):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()

def add_reward(name, xp_cost, qty):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO rewards (name, xp_cost, inventory_qty) VALUES (?, ?, ?)", (name, xp_cost, qty))
    conn.commit()
    conn.close()

def get_rewards():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, xp_cost, inventory_qty FROM rewards")
    rewards = cursor.fetchall()
    conn.close()
    return rewards

def update_reward_details(reward_id, new_cost, new_qty):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE rewards 
        SET xp_cost = ?, inventory_qty = ? 
        WHERE id = ?
    """, (new_cost, new_qty, reward_id))
    conn.commit()
    conn.close()

def delete_reward(reward_id):
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rewards WHERE id = ?", (reward_id,))
    conn.commit()
    conn.close()

def buy_reward(reward_id, reward_name, xp_cost):
    today_string = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO purchases (reward_name, xp_cost, purchase_date) VALUES (?, ?, ?)", 
                   (reward_name, xp_cost, today_string))
    cursor.execute("UPDATE rewards SET inventory_qty = MAX(0, inventory_qty - 1) WHERE id = ?", (reward_id,))
    
    # --- NEW: Route pet care items to pet inventory ---
    pet_items = [
        "🥩 Cyber-Protein", "💾 Memory Chip", "🖌️ Chameleon Ink", 
        "⚡ Giga-Soda", "🔮 Omni-Treat", "🗝️ Evolution Matrix"
    ]
    if reward_name in pet_items:
        cursor.execute("""
            INSERT INTO pet_inventory (item_name, quantity) 
            VALUES (?, 1) 
            ON CONFLICT(item_name) DO UPDATE SET quantity = quantity + 1
        """, (reward_name,))
    # --- END NEW ---
    
    conn.commit()
    conn.close()

def get_xp_balance():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT SUM(CASE WHEN is_boss_fight = 1 THEN xp_reward * 2 ELSE xp_reward END) 
        FROM tasks 
        WHERE is_completed = 1
    """)
    earned_tasks = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(xp_reward) FROM creator_projects WHERE status = 'Completed'")
    earned_projects = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(xp_cost) FROM purchases")
    spent = cursor.fetchone()[0] or 0
    
    conn.close()
    return (earned_tasks + earned_projects) - spent

def get_purchase_history():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT reward_name, xp_cost, purchase_date FROM purchases ORDER BY id DESC")
    purchases = cursor.fetchall()
    conn.close()
    return purchases

def get_task_completion_stats():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT category, COUNT(id) FROM tasks WHERE is_completed = 1 GROUP BY category")
    stats = cursor.fetchall()
    conn.close()
    return stats

def get_xp_over_time():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT task_date, SUM(CASE WHEN is_boss_fight = 1 THEN xp_reward * 2 ELSE xp_reward END) 
        FROM tasks 
        WHERE is_completed = 1 
        GROUP BY task_date 
        ORDER BY task_date ASC
    """)
    data = cursor.fetchall()
    conn.close()
    return data

def get_daily_streak():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT task_date FROM tasks WHERE is_completed = 1 ORDER BY task_date DESC")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return 0
        
    completed_dates = set()
    for row in rows:
        try:
            completed_dates.add(datetime.strptime(row[0], "%Y-%m-%d").date())
        except ValueError:
            pass
            
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    if today not in completed_dates and yesterday not in completed_dates:
        return 0
        
    current_date = today if today in completed_dates else yesterday
    streak = 0
    
    while current_date in completed_dates:
        streak += 1
        current_date -= timedelta(days=1)
        
    return streak

def get_expense_totals_by_status():
    conn = sqlite3.connect('flokus.db')
    cursor = conn.cursor()
    cursor.execute("SELECT status, SUM(cost) FROM expenses GROUP BY status")
    rows = cursor.fetchall()
    conn.close()
    return dict(rows)

# --- NEW: Update Data Fetcher to accept and process Date Boundaries ---
def get_full_portfolio_data(start_dt, end_dt):
    start_str = start_dt.strftime("%Y-%m-%d")
    end_str = end_dt.strftime("%Y-%m-%d")
    
    conn = sqlite3.connect('flokus.db')
    
    # Filter Daily Tasks within Range
    df_tasks = pd.read_sql_query("""
        SELECT task_date as Date, title as Activity, category as Subject, 
               xp_reward as XP_Earned, task_summary as Notes, 'Daily Task' as Type
        FROM tasks
        WHERE is_completed = 1 AND task_date >= ? AND task_date <= ?
    """, conn, params=(start_str, end_str))
    
    # Filter Creator Projects within Range
    df_projects = pd.read_sql_query("""
        SELECT completion_date as Date, title as Activity, platform as Subject, 
               xp_reward as XP_Earned, project_summary as Notes, 'Creator Project' as Type
        FROM creator_projects
        WHERE status = 'Completed' AND completion_date >= ? AND completion_date <= ?
    """, conn, params=(start_str, end_str))
    
    conn.close()
    
    df_combined = pd.concat([df_tasks, df_projects], ignore_index=True)
    
    if not df_combined.empty:
        df_combined = df_combined.sort_values(by='Date', ascending=False)
        
    return df_combined
# --- END NEW ---

SUBJECT_EMOJIS = {
    "Math (Beast Academy)": "🧮",
    "Language Arts (Brave Writer)": "✍️",
    "Science (CrunchLabs)": "🧪",
    "Science (Outschool)": "🏫",
    "Social Studies (Tuttle Twins)": "🗺️",
    "Logic (Brilliant.org)": "⚔️",
    "Logic (Synthesis)": "🤖",
    "Logic (Chess.com)": "♟️",
    "Logic (Critical Thinking Co.)": "🧠",
    "Applied STEM (Tech Tails)": "🛠️",
    "Applied STEM (Engineering Proj)": "⚙️"
}

PLATFORM_LINKS = {
    "Math (Beast Academy)": "https://beastacademy.com/login",
    "Language Arts (Brave Writer)": "https://bravewriter.com/",
    "Science (CrunchLabs)": "https://www.crunchlabs.com/",
    "Science (Outschool)": "https://outschool.com/", 
    "Social Studies (Tuttle Twins)": "https://tuttletwins.com/",
    "Logic (Brilliant.org)": "https://brilliant.org/login",
    "Logic (Synthesis)": "https://www.synthesis.com/",
    "Logic (Chess.com)": "https://www.chess.com/login",
    "Logic (Critical Thinking Co.)": "https://www.criticalthinking.com/",
    "Applied STEM (Tech Tails)": "",
    "Applied STEM (Engineering Proj)": "" 
}

# ==========================================
# STREAMLIT DASHBOARD UI
# ==========================================

st.set_page_config(page_title="Flokus Academy", layout="wide")

# --- NEW: Inject Premium Gamified CSS Aesthetics ---
st.markdown("""
<style>
    /* Import Outfit font */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

    /* Apply font globally */
    html, body, [class*="css"], .stMarkdown, p, div {
        font-family: 'Outfit', sans-serif !important;
    }

    /* Dark theme background styling */
    .stApp {
        background-color: #0c0e17 !important;
        color: #e2e8f0 !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #121420 !important;
        border-right: 1px solid #1f2336 !important;
    }

    /* Tab Custom Styling */
    button[data-baseweb="tab"] {
        font-size: 16px !important;
        font-weight: 600 !important;
        color: #8c9bb4 !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.3s ease !important;
        background-color: transparent !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #63b3ed !important;
        border-bottom: 2px solid #63b3ed !important;
    }

    /* Style Streamlit containers with borders as gamified cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(135deg, #181c2e 0%, #111422 100%) !important;
        border: 1px solid #232a45 !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1) !important;
        transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.2) !important;
        border-color: #404f85 !important;
    }

    /* Boss Fight Glowing Card */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(div.boss-fight-marker) {
        background: linear-gradient(135deg, #2d164d 0%, #170b29 100%) !important;
        border: 2px solid #9f7aea !important;
        box-shadow: 0 0 15px rgba(159, 122, 234, 0.2) !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(div.boss-fight-marker):hover {
        box-shadow: 0 0 25px rgba(159, 122, 234, 0.4) !important;
        border-color: #b794f4 !important;
    }

    /* Button Styling */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        background-color: #1b1e32 !important;
        color: #e2e8f0 !important;
        border: 1px solid #333b5c !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #2b3254 !important;
        border-color: #63b3ed !important;
        transform: scale(1.02) !important;
        color: #ffffff !important;
    }

    /* Metric Panels */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #181c2e 0%, #111422 100%) !important;
        border: 1px solid #232a45 !important;
        padding: 15px !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.15) !important;
    }
    div[data-testid="stMetricValue"] {
        color: #63b3ed !important;
        font-size: 32px !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #8c9bb4 !important;
        font-size: 13px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    /* Divider styling */
    /* Custom Chat Message Styling */
    div[data-testid="stChatMessage"] {
        background-color: #141724 !important;
        border: 1px solid #232a45 !important;
        border-radius: 12px !important;
        padding: 15px !important;
        margin-bottom: 12px !important;
    }
    div[data-testid="stChatMessage"]:has(img[src*="assistant"]) {
        background-color: #1a2238 !important;
        border-color: #63b3ed !important;
    }
    div[data-testid="stChatMessage"]:has(img[src*="user"]) {
        background-color: #1e1b2e !important;
        border-color: #9f7aea !important;
    }
</style>
""", unsafe_allow_html=True)

if 'show_balloons' not in st.session_state:
    st.session_state.show_balloons = False

st.sidebar.title("Navigation")
user_view = st.sidebar.radio("Who is using the dashboard?", ["Sonny (Student)", "Dad (Admin)"])

is_admin_authenticated = False
if user_view == "Dad (Admin)":
    admin_pin = st.sidebar.text_input("🔑 Enter Admin Passcode:", type="password")
    if admin_pin == "1234":
        is_admin_authenticated = True
    elif admin_pin != "":
        st.sidebar.error("❌ Incorrect Passcode!")

# ------------------------------------------
# SONNY'S VIEW
# ------------------------------------------
if user_view == "Sonny (Student)":
    
    if st.session_state.show_balloons:
        st.balloons()
        st.session_state.show_balloons = False

    col_date, _ = st.columns([0.25, 0.75])
    with col_date:
        selected_date = st.date_input("📅 Select Date:", value=date.today())

    day_display = selected_date.strftime("%A, %b %d")
    st.title(f"🎓 Sonny's Hub - {day_display}")
    
    tab_quests, tab_creator, tab_store, tab_pet, tab_ai = st.tabs(["📋 Daily Quests", "🛠️ Creator Block", "🛍️ Reward Store", "🐾 Digital Pet", "💬 Ask Floki"])
    
    with tab_quests:
        pending_tasks = get_pending_tasks(selected_date)
        completed_tasks = get_completed_tasks(selected_date)
        
        daily_xp = sum([task[4] * 2 if task[5] == 1 else task[4] for task in completed_tasks])
        
        header_col1, header_col2, header_col3 = st.columns([0.5, 0.25, 0.25])
        with header_col1:
            total_tasks = len(pending_tasks) + len(completed_tasks)
            if total_tasks > 0:
                progress_decimal = len(completed_tasks) / total_tasks
                progress_percentage = int(progress_decimal * 100)
                st.write(f"**Daily Quest Progress: {progress_percentage}%**")
                st.progress(progress_decimal)
            else:
                st.write("**No active quests found.**")

        with header_col2:
            st.metric(label="🏆 XP Earned (This Day)", value=daily_xp)
            
        with header_col3:
            st.metric(label="🔥 Daily Streak", value=f"{get_daily_streak()} Days")
        
        st.divider()
        
        col_todo, col_done = st.columns(2)
        
        with col_todo:
            st.subheader("📝 Up Next")
            if len(pending_tasks) == 0:
                st.success("🎉 All caught up!")
            else:
                for task in pending_tasks:
                    task_id, task_title, task_category, task_video_url, task_xp, is_boss = task
                    emoji = SUBJECT_EMOJIS.get(task_category, "📋")
                    
                    with st.container(border=True):
                        if is_boss == 1:
                            st.markdown('<div class="boss-fight-marker"></div>', unsafe_allow_html=True)
                            
                        inner_col1, inner_col2 = st.columns([0.8, 0.2])
                        with inner_col1:
                            if is_boss == 1:
                                st.markdown("👑 **DAILY BOSS FIGHT - DOUBLE XP CHALLENGE!** 👑")
                                label_text = f"🔥 **{emoji} {task_category}**: {task_title} (💎 {task_xp * 2} XP!!)"
                            else:
                                label_text = f"**{emoji} {task_category}**: {task_title} (💎 {task_xp} XP)"
                                
                            is_checked = st.checkbox(label_text, key=f"task_{task_id}")
                        with inner_col2:
                            url = PLATFORM_LINKS.get(task_category, "")
                            if url != "":
                                st.markdown(f"[🚀 Launch]({url})")
                        
                        if task_video_url:
                            with st.expander("📺 Watch Lesson Video"):
                                st.video(task_video_url)
                        
                        with st.expander("⏱️ Focus Sprint Timer"):
                            t_col1, t_col2 = st.columns([0.5, 0.5])
                            with t_col1:
                                focus_mins = st.number_input(
                                    "Sprint Minutes", min_value=1, max_value=60, value=15, 
                                    step=1, key=f"timer_input_{task_id}"
                                )
                            with t_col2:
                                st.write("") 
                                start_timer = st.button("🚀 Start Sprint", key=f"timer_btn_{task_id}")
                            
                            if start_timer:
                                countdown_placeholder = st.empty()
                                total_seconds = int(focus_mins * 60)
                                
                                while total_seconds > 0:
                                    mins, secs = divmod(total_seconds, 60)
                                    countdown_placeholder.metric(
                                        label="⌛ Active Focus Window", 
                                        value=f"{mins:02d}:{secs:02d}"
                                    )
                                    time.sleep(1)
                                    total_seconds -= 1
                                    
                                countdown_placeholder.success("🎉 Focus Sprint Complete! You crushed it!")
                                # --- NEW: Temporarily cache sprint runtime to carry over on check ---
                                st.session_state[f"runtime_captured_{task_id}"] = int(focus_mins)
                                # --- END NEW ---
                                st.balloons()
                        
                        note_input = st.text_input(
                            "✏️ What did you learn or read? (Add a summary note here before checking complete)",
                            key=f"note_input_{task_id}"
                        )
                        
                        st.write("") 
                        
                        if is_checked:
                            if len(note_input.strip()) < 15:
                                st.warning(f"⚠️ Note is too short! Write at least 15 characters about what you learned. (Current: {len(note_input.strip())}/15)")
                            else:
                                # --- NEW: Pass state session-held focus minutes into db logic ---
                                completed_mins = st.session_state.get(f"runtime_captured_{task_id}", 0)
                                complete_task(task_id, note_input, completed_mins)
                                # Clean up memory state flag
                                if f"runtime_captured_{task_id}" in st.session_state:
                                    del st.session_state[f"runtime_captured_{task_id}"]
                                # --- END NEW ---
                                st.session_state.show_balloons = True
                                st.rerun()

        with col_done:
            st.subheader("✅ Completed")
            if len(completed_tasks) == 0:
                st.info("Nothing completed yet.")
            else:
                for task in completed_tasks:
                    task_title = task[1]
                    task_category = task[2]
                    task_xp = task[4]
                    is_boss = task[5]
                    emoji = SUBJECT_EMOJIS.get(task_category, "📋")
                    
                    with st.container(border=True):
                        if is_boss == 1:
                            st.markdown('<div class="boss-fight-marker"></div>', unsafe_allow_html=True)
                            st.success(f"👑 **{emoji} {task_category}**: {task_title} (💎 {task_xp * 2} XP Earned!)")
                        else:
                            st.success(f"**{emoji} {task_category}**: {task_title} (💎 {task_xp} XP)")

    with tab_creator:
        st.subheader("🛠️ Active Creator Projects")
        st.write("Take your time. Physical builds require patience. Claim your massive XP reward only when the final project is fully functional!")
        st.divider()
        
        active_projects = get_active_projects()
        
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
                            safe_filename = f"{int(time.time())}_{uploaded_file.name}"
                            saved_path = os.path.join("uploads", safe_filename)
                            with open(saved_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                                
                        complete_creator_project(p_id, proj_note_input, saved_path)
                        st.session_state.show_balloons = True
                        st.success(f"Epic job! You successfully built the {p_title} and earned {p_xp} XP!")
                        st.rerun()
                    st.divider()

    with tab_store:
        st.subheader("Welcome to the XP Store!")
        
        bank_balance = get_xp_balance()
        st.metric(label="🏦 Total XP Bank (Available to Spend)", value=bank_balance)
        st.divider()
        
        rewards = get_rewards()
        if len(rewards) == 0:
            st.info("The store is currently empty. Dad needs to stock the shelves!")
        else:
            cols = st.columns(3)
            for index, reward in enumerate(rewards):
                reward_id, reward_name, reward_cost, reward_qty = reward
                
                with cols[index % 3]:
                    with st.container(border=True):
                        st.markdown(f"### {reward_name}")
                        st.write(f"**Cost:** 💎 {reward_cost} XP")
                        
                        if reward_qty > 0:
                            st.write(f"🟢 **In Stock:** {reward_qty} available")
                            buy_disabled = False
                        else:
                            st.write("🔴 **OUT OF STOCK**")
                            buy_disabled = True
                        
                        if buy_disabled:
                            st.button("Buy", key=f"buy_disabled_{reward_id}", disabled=True)
                        else:
                            with st.popover("🛍️ Buy"):
                                st.write(f"Spend 💎 {reward_cost} XP on {reward_name}?")
                                if st.button("Confirm Purchase", key=f"buy_conf_{reward_id}"):
                                    if bank_balance >= reward_cost:
                                        buy_reward(reward_id, reward_name, reward_cost)
                                        st.success(f"Successfully bought {reward_name}!")
                                        st.rerun()
                                    else:
                                        st.error(f"Not enough XP! You need {reward_cost - bank_balance} more.")

    # --- NEW: Digital Pet and AI Chat Views ---
    with tab_pet:
        pet = get_pet_status()
        if not pet:
            st.info("Sparky is sleeping. Check back later!")
        else:
            pet_id, pet_name, pet_level, pet_xp, strength, intelligence, creativity, stamina, max_stamina, happiness, stage, form_name, accessory_parts = pet
            
            # XP level calculations
            next_level_xp = int(100 * (pet_level)**1.8)
            xp_progress = pet_xp / next_level_xp if next_level_xp > 0 else 0.0
            
            st.subheader(f"🐾 Pet Status: {pet_name}")
            
            col_pet_card, col_pet_stats = st.columns([0.4, 0.6])
            
            # --- Dynamic Pet Theme Logic ---
            top_attr = max(strength, intelligence, creativity)
            if stage == "Egg":
                border_color = "#f59e0b"
                bg_style = "linear-gradient(135deg, #1e180d 0%, #0f0c07 100%)"
                glow_style = "box-shadow: 0 0 20px rgba(245, 158, 11, 0.3);"
                text_color = "#fbbf24"
            elif top_attr == intelligence:
                border_color = "#00f0ff"
                bg_style = "linear-gradient(135deg, #0c1b26 0%, #060e14 100%)"
                glow_style = "box-shadow: 0 0 20px rgba(0, 240, 255, 0.3);"
                text_color = "#00f0ff"
            elif top_attr == creativity:
                border_color = "#a855f7"
                bg_style = "linear-gradient(135deg, #200f35 0%, #0f071a 100%)"
                glow_style = "box-shadow: 0 0 20px rgba(168, 85, 247, 0.3);"
                text_color = "#c084fc"
            else: # Strength
                border_color = "#f97316"
                bg_style = "linear-gradient(135deg, #2b1104 0%, #160902 100%)"
                glow_style = "box-shadow: 0 0 20px rgba(249, 115, 22, 0.3);"
                text_color = "#ff983d"

            avatar_emoji = form_name[-1] if form_name and ord(form_name[-1]) > 127 else "🐾"
            clean_form_name = form_name[:-2].strip() if form_name and ord(form_name[-1]) > 127 else form_name

            with col_pet_card:
                # Custom styled avatar card with dynamic attributes theme
                st.markdown(
                    f"""
                    <div style="background: {bg_style}; padding: 25px; border-radius: 15px; border: 2px solid {border_color}; {glow_style} text-align: center;">
                        <span style="font-size: 72px;">{avatar_emoji}</span>
                        <h3 style="color: {text_color};">{clean_form_name}</h3>
                        <p style="color: #A6ADC8; margin-top: -5px;">Stage: <strong>{stage}</strong></p>
                        <div style="background-color: #313244; border-radius: 10px; height: 10px; width: 100%; margin-top: 15px;">
                            <div style="background-color: {border_color}; height: 100%; border-radius: 10px; width: {int(xp_progress * 100)}%;"></div>
                        </div>
                        <small style="color: #BAC2DE;">Level {pet_level} ({pet_xp} / {next_level_xp} XP)</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            with col_pet_stats:
                st.markdown("### Attributes & Energy")
                
                # Stamina
                st.write(f"🔋 **Stamina:** {stamina} / {max_stamina}")
                st.progress(stamina / max_stamina if max_stamina > 0 else 0.0)
                
                # Stats
                st.write(f"🧠 **Intelligence (INT):** {intelligence}")
                st.progress(min(intelligence / 100.0, 1.0))
                
                st.write(f"🎨 **Creativity (CRT):** {creativity}")
                st.progress(min(creativity / 100.0, 1.0))
                
                st.write(f"💪 **Strength (STR):** {strength}")
                st.progress(min(strength / 100.0, 1.0))

            st.divider()
            
            # --- FEED / CARE SECTION ---
            st.markdown("### 🎒 Pet Care & Feed")
            
            conn = sqlite3.connect('flokus.db')
            cursor = conn.cursor()
            cursor.execute("SELECT item_name, quantity FROM pet_inventory WHERE quantity > 0")
            pet_inv = cursor.fetchall()
            conn.close()
            
            if not pet_inv:
                st.info("Your pet inventory is empty. Buy care items (like Cyber-Protein or Memory Chips) from the XP Store!")
            else:
                inv_cols = st.columns(len(pet_inv))
                for idx, (item, qty) in enumerate(pet_inv):
                    with inv_cols[idx]:
                        with st.container(border=True):
                            st.write(f"**{item}**")
                            st.write(f"Qty: {qty}")
                            if st.button("Use Item", key=f"use_item_btn_{idx}", use_container_width=True):
                                res_msg = use_pet_item(item)
                                st.success(res_msg)
                                st.rerun()
                                
            st.divider()
            
            # --- QUEST ADVENTURE ENGINE ---
            st.markdown("### 🗺️ Choose-Your-Own-Adventure Quests")
            
            # Check if there is an active quest
            if "active_quest" not in st.session_state:
                st.session_state.active_quest = None
                
            if st.session_state.active_quest is None:
                st.write("Send Sparky on an exploration quest to earn extra XP and test its attributes!")
                quest_col1, quest_col2 = st.columns([0.7, 0.3])
                with quest_col1:
                    zone = st.selectbox(
                        "Choose Adventure Zone:",
                        [
                            "📐 The Algebra Ruins (Requires INT)", 
                            "🎨 Maker's Canyon (Requires CRT)", 
                            "🌋 Titan's Forge (Requires STR)"
                        ]
                    )
                with quest_col2:
                    st.write("")
                    st.write("")
                    if st.button("🚀 Embark! (Costs 2 Stamina)", use_container_width=True):
                        if stamina < 2:
                            st.error("Not enough Stamina! Restore stamina by maintaining a task streak or buying Giga-Soda!")
                        else:
                            # Deduct stamina
                            conn = sqlite3.connect('flokus.db')
                            cursor = conn.cursor()
                            cursor.execute("UPDATE pet_status SET stamina = MAX(0, stamina - 2) WHERE id = ?", (pet_id,))
                            conn.commit()
                            conn.close()
                            
                            # Initialize Quest encounter
                            encounters = [
                                {
                                    "zone": "📐 The Algebra Ruins (Requires INT)",
                                    "title": "📐 The Algebra Ruins: Ancient Logic Gate",
                                    "description": "You stand before a glowing security terminal blocking the tunnel. It requires solving a geometric equation to unlock.",
                                    "stat_req": "INT",
                                    "stat_val": 15,
                                    "action_desc": "Hack Terminal",
                                    "question": "Solve: 3x - 5 = 10. What is x?",
                                    "answer": "5"
                                },
                                {
                                    "zone": "🎨 Maker's Canyon (Requires CRT)",
                                    "title": "🎨 Maker's Canyon: The Suspension Bridge",
                                    "description": "A deep gorge separates you from the other side. You need to construct a suspension bridge from scattered branches.",
                                    "stat_req": "CRT",
                                    "stat_val": 15,
                                    "action_desc": "Build Bridge",
                                    "question": "What runs but never walks, has a mouth but never talks? (Hint: a r____)",
                                    "answer": "river"
                                },
                                {
                                    "zone": "🌋 Titan's Forge (Requires STR)",
                                    "title": "🌋 Titan's Forge: The Blocking Boulder",
                                    "description": "A massive volcanic stone has rolled down the slope, blocking the passage.",
                                    "stat_req": "STR",
                                    "stat_val": 15,
                                    "action_desc": "Smash Boulder",
                                    "question": "A rectangle has a width of 4 and a length of 6. What is its area?",
                                    "answer": "24"
                                }
                            ]
                            
                            selected_enc = [e for e in encounters if e["zone"] == zone][0]
                            st.session_state.active_quest = selected_enc
                            st.rerun()
            else:
                enc = st.session_state.active_quest
                st.info(f"📍 Current Zone: **{enc['zone']}**")
                with st.container(border=True):
                    st.subheader(enc["title"])
                    st.write(enc["description"])
                    st.write(f"**Stat Check:** {enc['stat_req']} >= {enc['stat_val']}")
                    
                    # Determine success based on pet stat
                    pet_stat_val = intelligence if enc["stat_req"] == "INT" else (creativity if enc["stat_req"] == "CRT" else strength)
                    can_bypass = pet_stat_val >= enc["stat_val"]
                    
                    col_opt_a, col_opt_b = st.columns(2)
                    
                    with col_opt_a:
                        st.markdown("#### Choice A: Stat Auto-Check")
                        if can_bypass:
                            st.success(f"Sparky is ready! ({enc['stat_req']} = {pet_stat_val} >= {enc['stat_val']})")
                            if st.button("Execute Option A", use_container_width=True):
                                # Award XP
                                conn = sqlite3.connect('flokus.db')
                                cursor = conn.cursor()
                                new_xp = pet_xp + 20
                                next_lvl_xp = int(100 * (pet_level)**1.8)
                                new_lvl = pet_level
                                new_stage = stage
                                new_form = form_name
                                if new_xp >= next_lvl_xp:
                                    new_lvl += 1
                                    new_xp = max(0, new_xp - next_lvl_xp)
                                    new_stage, new_form = calculate_evolution_internal(new_lvl, strength, intelligence, creativity)
                                cursor.execute("""
                                    UPDATE pet_status 
                                    SET level = ?, current_xp = ?, stage = ?, form_name = ? 
                                    WHERE id = ?
                                """, (new_lvl, new_xp, new_stage, new_form, pet_id))
                                conn.commit()
                                conn.close()
                                
                                st.session_state.active_quest = None
                                st.toast("🎉 Quest Completed! Sparky earned 20 XP!")
                                st.rerun()
                        else:
                            st.warning(f"Sparky is too weak! ({enc['stat_req']} = {pet_stat_val} < {enc['stat_val']})")
                            st.button("Execute Option A (Locked)", disabled=True, use_container_width=True)
                            
                    with col_opt_b:
                        st.markdown("#### Choice B: Real-World Power-up")
                        st.write("Help your pet bypass the challenge by answering this learning riddle:")
                        st.write(f"💬 **{enc['question']}**")
                        ans_input = st.text_input("Enter Answer:", key="riddle_answer_input")
                        if st.button("Submit Answer", use_container_width=True):
                            if ans_input.strip().lower() == enc["answer"]:
                                # Award XP + Bonus!
                                conn = sqlite3.connect('flokus.db')
                                cursor = conn.cursor()
                                new_xp = pet_xp + 40
                                next_lvl_xp = int(100 * (pet_level)**1.8)
                                new_lvl = pet_level
                                new_stage = stage
                                new_form = form_name
                                if new_xp >= next_lvl_xp:
                                    new_lvl += 1
                                    new_xp = max(0, new_xp - next_lvl_xp)
                                    new_stage, new_form = calculate_evolution_internal(new_lvl, strength, intelligence, creativity)
                                cursor.execute("""
                                    UPDATE pet_status 
                                    SET level = ?, current_xp = ?, stage = ?, form_name = ? 
                                    WHERE id = ?
                                """, (new_lvl, new_xp, new_stage, new_form, pet_id))
                                conn.commit()
                                conn.close()
                                
                                st.session_state.active_quest = None
                                st.toast("🎉 Correct! Academic powerup cleared the way! Earned 40 XP!")
                                st.rerun()
                            else:
                                st.error("Incorrect answer. Try again!")
                                
                if st.button("🏳️ Retreat from Quest", key="retreat_quest_btn"):
                    st.session_state.active_quest = None
                    st.rerun()

    with tab_ai:
        st.subheader("💬 Ask Floki: Your AI Learning Buddy")
        st.markdown("*Floki is here to help you study, answer your questions, and coach you through quests!*")
        
        # Display chat history
        session_id = "sonny_study_session"
        chat_logs = get_chat_history(session_id)
        
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
            add_chat_msg(session_id, "Sonny", user_input)
            
            # 2. Call Gemini
            # 2. Call Gemini with active persona
            active_persona = get_floki_persona()
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
                
            system_instruction = base_prompt + persona_guidelines
            
            # Fetch full conversation history from DB for LLM context
            full_history = get_chat_history(session_id)
            messages_context = []
            for sender, msg, _ in full_history:
                messages_context.append({
                    "role": "user" if sender == "Sonny" else "model",
                    "content": msg
                })
                
            if not gemini_key:
                floki_reply = "🤖 **[Offline/Demo Mode]** Hi Sonny! I am Floki. To activate me, please ask Dad to add a `GEMINI_API_KEY` to the Streamlit secrets! In the meantime, keep up the amazing learning! 🌟"
            else:
                with st.spinner("Floki is thinking..."):
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=gemini_key)
                        model = genai.GenerativeModel(
                            model_name="gemini-3.5-flash",
                            system_instruction=system_instruction
                        )
                        # Translate context to Gemini API format (ensuring alternating user/model sequence)
                        contents = []
                        for msg in messages_context:
                            role = "user" if msg["role"] == "user" else "model"
                            # If the list is empty or the last message has a different role, add a new turn
                            if not contents or contents[-1]["role"] != role:
                                contents.append({"role": role, "parts": [msg["content"]]})
                            else:
                                # Otherwise, append this text block to the previous turn of the same role
                                contents[-1]["parts"].append(msg["content"])
                            
                        response = model.generate_content(contents)
                        floki_reply = response.text
                    except Exception as e:
                        floki_reply = f"❌ **Error calling Gemini API:** {str(e)}"
                        
            # 3. Add assistant message to UI
            with st.chat_message("assistant"):
                st.write(floki_reply)
            add_chat_msg(session_id, "Floki", floki_reply)
            st.rerun()
    # --- END NEW ---

# ------------------------------------------
# ADMIN VIEW
# ------------------------------------------
elif user_view == "Dad (Admin)" and not is_admin_authenticated:
    st.title("🔒 Admin Control Center")
    st.info("Please enter the correct passcode in the sidebar to access Dad's Admin Dashboard.")

elif user_view == "Dad (Admin)" and is_admin_authenticated:
    st.title("⚙️ Admin Dashboard")
    
    # --- NEW: Local IP Address and Network Publishing Guidance ---
    import socket
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
            
    local_ip = get_local_ip()
    st.info(
        f"🌐 **Share with Sonny!** Sonny can access this dashboard from his own computer or tablet by opening "
        f"a web browser and going to: `http://{local_ip}:8501` \n\n"
        f"*(Note: Ensure both computers are on the same home Wi-Fi network. You may need to allow port 8501 through Windows Defender Firewall on this computer).* "
    )
    # --- END NEW ---

    st.write("Welcome to the control center.")
    st.divider()
    
    tab1, tab_proj, tab2, tab3, tab4, tab5, tab_safety = st.tabs(["📝 Add Tasks", "🛠️ Creator Projects", "🗂️ Portfolio", "💰 UFA Finances", "🎁 XP Store", "📊 Analytics", "🤖 AI Safety & Settings"])
    
    with tab1:
        st.subheader("Add a New Task for Sonny")
        
        # --- NEW: Quick AI Scheduler ---
        with st.expander("🎙️ Add Task with AI (Natural Language)"):
            st.write("Type your scheduling request below. E.g., *'Add Beast Academy math today for 15 xp'* or *'schedule Outschool Science for tomorrow'*")
            nl_command = st.text_input("AI Scheduler Command", key="nl_scheduler_command")
            if st.button("Schedule Task", key="nl_scheduler_submit"):
                if nl_command.strip() == "":
                    st.warning("Please type a command!")
                else:
                    res_msg = parse_and_execute_schedule_command(nl_command.strip())
                    st.success(res_msg)
                    st.rerun()
        st.write("")
        # --- END NEW ---
        
        with st.form("new_task_form"):
            task_title = st.text_input("Task Description")
            
            task_category = st.selectbox("Finalized 5th Grade Curriculum Spine Selection", [
                "Math (Beast Academy)",
                "Language Arts (Brave Writer)",
                "Science (CrunchLabs)",
                "Science (Outschool)",
                "Social Studies (Tuttle Twins)",
                "Logic (Brilliant.org)",
                "Logic (Synthesis)",
                "Logic (Chess.com)",
                "Logic (Critical Thinking Co.)",
                "Applied STEM (Tech Tails)",
                "Applied STEM (Engineering Proj)"
            ])
            
            task_video = st.text_input("Optional: YouTube Video URL")
            task_xp = st.number_input("XP Reward", min_value=5, max_value=500, value=10, step=5)
            scheduled_date = st.date_input("Scheduled Date", value=date.today())
            is_boss_fight = st.checkbox("⭐ Mark as Daily Boss Fight (Double XP Bonus!)", value=False)
            submitted = st.form_submit_button("Save Task")
            
            if submitted:
                if task_title.strip() == "":
                    st.error("⚠️ Task Description cannot be empty!")
                else:
                    boss_int = 1 if is_boss_fight else 0
                    add_task_to_db(task_title.strip(), task_category, task_video, task_xp, scheduled_date, boss_int)
                    st.success(f"Scheduled for {task_category} on {scheduled_date.strftime('%b %d')}.")
                    st.rerun()

        st.divider()
        st.subheader("📋 Manage Pending Tasks")
        pending_list = get_all_pending_tasks()
        if not pending_list:
            st.info("No pending tasks scheduled.")
        else:
            for t in pending_list:
                t_id, t_title, t_category, t_video, t_xp, t_boss, t_date_str = t
                t_date = datetime.strptime(t_date_str, "%Y-%m-%d").date()
                
                col_t1, col_t2, col_t3 = st.columns([0.6, 0.2, 0.2])
                with col_t1:
                    emoji = SUBJECT_EMOJIS.get(t_category, "📋")
                    boss_label = " 👑 *(Boss Fight!)*" if t_boss == 1 else ""
                    st.markdown(f"**{emoji} {t_category}**: {t_title} (💎 {t_xp} XP){boss_label}  \n*Scheduled Date: {t_date.strftime('%b %d, %Y')}*")
                
                with col_t2:
                    with st.popover("✏️ Edit"):
                        edit_title = st.text_input("Task Description", value=t_title, key=f"edit_task_title_{t_id}")
                        edit_category = st.selectbox(
                            "Curriculum Spine",
                            options=list(SUBJECT_EMOJIS.keys()),
                            index=list(SUBJECT_EMOJIS.keys()).index(t_category) if t_category in SUBJECT_EMOJIS else 0,
                            key=f"edit_task_cat_{t_id}"
                        )
                        edit_video = st.text_input("YouTube Video URL", value=t_video or "", key=f"edit_task_vid_{t_id}")
                        edit_xp = st.number_input("XP Reward", min_value=5, max_value=500, value=int(t_xp), step=5, key=f"edit_task_xp_{t_id}")
                        edit_date = st.date_input("Scheduled Date", value=t_date, key=f"edit_task_date_{t_id}")
                        edit_boss = st.checkbox("Mark as Daily Boss Fight", value=(t_boss == 1), key=f"edit_task_boss_{t_id}")
                        
                        if st.button("Save Changes", key=f"save_task_btn_{t_id}"):
                            if edit_title.strip() == "":
                                st.error("Task Description cannot be empty!")
                            else:
                                update_task_details(t_id, edit_title.strip(), edit_category, edit_video, edit_xp, edit_date, 1 if edit_boss else 0)
                                st.success("Task updated successfully!")
                                st.rerun()
                
                with col_t3:
                    with st.popover("❌ Delete"):
                        st.write("Are you sure you want to delete this task?")
                        if st.button("Confirm Delete", key=f"del_task_btn_{t_id}"):
                            delete_task(t_id)
                            st.success("Task deleted!")
                            st.rerun()
                
    with tab_proj:
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
                    add_creator_project(proj_title.strip(), proj_platform, proj_xp)
                    st.success(f"Project '{proj_title}' successfully launched!")
                    st.rerun()

        st.divider()
        st.subheader("🛠️ Manage Creator Projects")
        
        conn = sqlite3.connect('flokus.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, platform, xp_reward, status, completion_date, project_summary, project_attachment FROM creator_projects ORDER BY id DESC")
        all_projs = cursor.fetchall()
        conn.close()
        
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
                                update_creator_project(
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
                            delete_creator_project(p_id)
                            st.success("Project deleted!")
                            st.rerun()
                
    with tab2:
        portfolio_date = st.date_input("📅 Select Date to Review:", value=date.today(), key="admin_portfolio_date")
        day_display = portfolio_date.strftime("%A, %b %d")
        
        st.subheader(f"Completed Tasks ({day_display})")
        
        admin_completed_tasks = get_completed_tasks(portfolio_date) 
        
        if len(admin_completed_tasks) == 0:
            st.info(f"No completed tasks found for {day_display}.")
        else:
            for task in admin_completed_tasks:
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    emoji = SUBJECT_EMOJIS.get(task[2], "📋")
                    if task[5] == 1:
                        st.markdown(f"👑 **{emoji} {task[2]}**: {task[1]} *(Boss Fight!)*")
                    else:
                        st.markdown(f"✅ **{emoji} {task[2]}**: {task[1]}")
                    
                    if task[6] and task[6].strip() != "":
                        st.info(f"💭 **Sonny's Notes:** {task[6]}")
                    
                with col2:
                    if st.button("❌", key=f"del_task_{task[0]}"):
                        delete_task(task[0])
                        st.rerun()
                        
        admin_completed_projects = get_completed_projects(portfolio_date)
        if len(admin_completed_projects) > 0:
            st.markdown("### 🛠️ Completed Creator Projects")
            for proj in admin_completed_projects:
                st.markdown(f"✅ **{proj[2]}**: {proj[1]} *(💎 {proj[3]} XP)*")
                if proj[4] and proj[4].strip() != "":
                    st.info(f"💭 **Sonny's Project Notes:** {proj[4]}")
                
                # --- NEW: Render Attachment in Portfolio Review ---
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
        
        # --- NEW: Implement Date Range Calendar Layout selectors ---
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            export_start = st.date_input("📅 Report Start Date:", value=date.today() - timedelta(days=30))
        with r_col2:
            export_end = st.date_input("📅 Report End Date:", value=date.today())
            
        # Pass calendar choices into our updated range data-fetcher function
        portfolio_df = get_full_portfolio_data(export_start, export_end)
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

    with tab3:
        expenses = get_all_expenses()
        df_expenses_export = pd.DataFrame(expenses, columns=["ID", "Item Name", "Cost", "Category", "Status"])
        if not df_expenses_export.empty:
            df_expenses_export = df_expenses_export.drop(columns=["ID"])

        col_title, col_export = st.columns([0.7, 0.3])
        with col_title:
            st.subheader("Utah Fits All (UFA) Budget Tracker")
        with col_export:
            if not df_expenses_export.empty:
                csv_data = df_expenses_export.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Expenses to CSV",
                    data=csv_data,
                    file_name="Flokus_UFA_Expenses.csv",
                    mime="text/csv",
                    key="export_expenses_csv",
                    use_container_width=True
                )
                
        total_budget = 4000.00
        total_spent = sum([expense[2] for expense in expenses if expense[4] != "Out of Pocket (Not UFA)"])
        remaining_budget = total_budget - total_spent
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total UFA Grant", f"${total_budget:,.2f}")
        col2.metric("Total Spent", f"${total_spent:,.2f}")
        col3.metric("Remaining Funds", f"${remaining_budget:,.2f}")

        # --- NEW: Budget Alerts ---
        if remaining_budget < 600.00:
            st.error(f"⚠️ **Low Funds Warning!** Remaining UFA budget is ${remaining_budget:,.2f} (under 15%). Plan purchases carefully!")
        elif remaining_budget < 1200.00:
            st.warning(f"⚠️ **Budget Alert:** Remaining UFA budget is ${remaining_budget:,.2f} (under 30%).")
        # --- END NEW ---

        st.sidebar.markdown("---")
        
        st.write("**UFA Pipeline Allocation Radar**")
        status_map = get_expense_totals_by_status()
        pending_odyssey = status_map.get("Pending Odyssey Approval", 0.0)
        direct_paid = status_map.get("Approved & Direct Paid", 0.0)
        reimbursed = status_map.get("Reimbursed", 0.0)
        out_of_pocket = status_map.get("Out of Pocket (Not UFA)", 0.0)
        
        radar_col1, radar_col2, radar_col3, radar_col4 = st.columns(4)
        radar_col1.metric("⏳ Pending Odyssey", f"${pending_odyssey:,.2f}")
        radar_col2.metric("🟢 Direct Paid", f"${direct_paid:,.2f}")
        radar_col3.metric("💰 Reimbursed", f"${reimbursed:,.2f}")
        radar_col4.metric("🛑 Out of Pocket", f"${out_of_pocket:,.2f}")
        st.divider()

        # --- NEW: Financial Charts Section ---
        if not df_expenses_export.empty:
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                st.markdown("#### 📊 UFA Budget Spent by Category")
                df_cat_totals = df_expenses_export[df_expenses_export["Status"] != "Out of Pocket (Not UFA)"].groupby("Category")["Cost"].sum().reset_index()
                if not df_cat_totals.empty:
                    df_cat_totals = df_cat_totals.set_index("Category")
                    st.bar_chart(df_cat_totals)
                else:
                    st.info("No UFA expenses logged yet.")
            with chart_col2:
                st.markdown("#### ⏳ Spent by Status Pipeline")
                df_status_totals = df_expenses_export.groupby("Status")["Cost"].sum().reset_index()
                if not df_status_totals.empty:
                    df_status_totals = df_status_totals.set_index("Status")
                    st.bar_chart(df_status_totals)
                else:
                    st.info("No expenses logged yet.")
            st.divider()
        # --- END NEW ---
        
        st.write("**Log a New Purchase**")
        with st.form("expense_form"):
            item_name = st.text_input("Item/Service Name")
            cost = st.number_input("Cost ($)", min_value=0.00, format="%.2f")
            category = st.selectbox("Category", [
                "Curriculum & Workbooks", "Technology/Hardware", 
                "Extracurricular/Classes", "Supplies & Materials"
            ])
            status = st.selectbox("Status", [
                "Pending Odyssey Approval", "Approved & Direct Paid", 
                "Reimbursed", "Out of Pocket (Not UFA)"
            ])
            submit_expense = st.form_submit_button("Log Expense")
            if submit_expense:
                if item_name.strip() == "":
                    st.error("⚠️ Item/Service Name cannot be empty!")
                else:
                    add_expense(item_name.strip(), cost, category, status)
                    st.success("Expense logged successfully!")
                    st.rerun()

        st.write("**Expense History**")
        if len(expenses) == 0:
            st.info("No expenses logged yet.")
        else:
            for exp in expenses:
                col_exp1, col_exp2, col_exp3 = st.columns([0.5, 0.3, 0.2])
                with col_exp1:
                    st.markdown(f"📦 **{exp[1]}** | ${exp[2]:.2f}\n\n*Category: {exp[3]}*")
                with col_exp2:
                    status_options = [
                        "Pending Odyssey Approval", "Approved & Direct Paid", 
                        "Reimbursed", "Out of Pocket (Not UFA)"
                    ]
                    
                    try:
                        current_status_idx = status_options.index(exp[4])
                    except ValueError:
                        current_status_idx = 0
                        
                    chosen_status = st.selectbox(
                        f"Status Dropdown {exp[0]}",
                        options=status_options,
                        index=current_status_idx,
                        key=f"update_status_select_{exp[0]}",
                        label_visibility="collapsed"
                    )
                    
                    if chosen_status != exp[4]:
                        update_expense_status(exp[0], chosen_status)
                        st.rerun()
                with col_exp3:
                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        with st.popover("✏️"):
                            edit_exp_name = st.text_input("Item Name", value=exp[1], key=f"edit_exp_name_{exp[0]}")
                            edit_exp_cost = st.number_input("Cost ($)", min_value=0.00, value=float(exp[2]), format="%.2f", key=f"edit_exp_cost_{exp[0]}")
                            edit_exp_cat = st.selectbox(
                                "Category",
                                options=["Curriculum & Workbooks", "Technology/Hardware", "Extracurricular/Classes", "Supplies & Materials"],
                                index=["Curriculum & Workbooks", "Technology/Hardware", "Extracurricular/Classes", "Supplies & Materials"].index(exp[3]) if exp[3] in ["Curriculum & Workbooks", "Technology/Hardware", "Extracurricular/Classes", "Supplies & Materials"] else 0,
                                key=f"edit_exp_cat_{exp[0]}"
                            )
                            edit_exp_status = st.selectbox(
                                "Status",
                                options=status_options,
                                index=current_status_idx,
                                key=f"edit_exp_status_{exp[0]}"
                            )
                            if st.button("Save", key=f"save_exp_{exp[0]}"):
                                if edit_exp_name.strip() == "":
                                    st.error("Name cannot be empty!")
                                else:
                                    update_expense_details(exp[0], edit_exp_name.strip(), edit_exp_cost, edit_exp_cat, edit_exp_status)
                                    st.success("Expense updated!")
                                    st.rerun()
                    with col_del:
                        with st.popover("❌"):
                            st.write("Delete this expense?")
                            if st.button("Confirm", key=f"del_exp_confirm_{exp[0]}"):
                                delete_expense(exp[0])
                                st.rerun()

    with tab4:
        st.subheader("Store Inventory Management")
        
        st.write("**Add a New Reward**")
        with st.form("new_reward_form"):
            reward_name = st.text_input("Reward Name (e.g., '1 Hour Screen Time', '$5 Robux')")
            reward_cost = st.number_input("XP Cost", min_value=10, max_value=5000, value=100, step=10)
            reward_qty = st.number_input("Quantity in Stock", min_value=1, max_value=100, value=5, step=1)
            submitted_reward = st.form_submit_button("Add to Store")
            
            if submitted_reward and reward_name != "":
                add_reward(reward_name, reward_cost, reward_qty)
                st.success(f"Added {reward_name} to the store!")
                st.rerun()
                
        st.divider()
        st.write("**Current Store Items**")
        rewards = get_rewards()
        if len(rewards) == 0:
            st.info("No rewards in the store yet.")
        else:
            for reward in rewards:
                reward_id, reward_name, reward_cost, reward_qty = reward
                
                col_rew1, col_rew2, col_rew3, col_rew4 = st.columns([0.4, 0.2, 0.2, 0.2])
                with col_rew1:
                    st.markdown(f"🎁 **{reward_name}**")
                with col_rew2:
                    edited_cost = st.number_input(
                        "Cost", min_value=5, max_value=10000, value=int(reward_cost), step=5, 
                        key=f"edit_cost_{reward_id}", label_visibility="collapsed"
                    )
                with col_rew3:
                    edited_qty = st.number_input(
                        "Stock", min_value=0, max_value=500, value=int(reward_qty), step=1, 
                        key=f"edit_qty_{reward_id}", label_visibility="collapsed"
                    )
                with col_rew4:
                    if edited_cost != reward_cost or edited_qty != reward_qty:
                        if st.button("💾 Save", key=f"save_rew_{reward_id}"):
                            update_reward_details(reward_id, edited_cost, edited_qty)
                            st.rerun()
                    else:
                        if st.button("❌", key=f"del_reward_{reward_id}"):
                            delete_reward(reward_id)
                            st.rerun()
                        
        st.divider()
        st.subheader("🎟️ Claimed & Pending Rewards Log")
        st.caption("Approve and track Sonny's real-world reward claims.")
        
        conn = sqlite3.connect('flokus.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, reward_name, xp_cost, purchase_date, is_claimed FROM purchases ORDER BY id DESC")
        purchases_list = cursor.fetchall()
        conn.close()
        
        if len(purchases_list) == 0:
            st.info("Sonny hasn't purchased any rewards yet.")
        else:
            for p_id, r_name, cost, p_date, is_claimed in purchases_list:
                col_p1, col_p2, col_p3 = st.columns([0.5, 0.3, 0.2])
                with col_p1:
                    status_emoji = "✅" if is_claimed == 1 else "⏳"
                    st.markdown(f"{status_emoji} **{r_name}** — 💎 {cost} XP")
                    st.caption(f"Purchased: {p_date}")
                with col_p2:
                    if is_claimed == 1:
                        st.markdown("<span style='color: #48bb78; font-weight: bold;'>Claimed</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='color: #ed8936; font-weight: bold;'>Pending Claim</span>", unsafe_allow_html=True)
                with col_p3:
                    if is_claimed == 0:
                        if st.button("Mark Claimed", key=f"claim_btn_{p_id}", use_container_width=True):
                            conn = sqlite3.connect('flokus.db')
                            cursor = conn.cursor()
                            cursor.execute("UPDATE purchases SET is_claimed = 1 WHERE id = ?", (p_id,))
                            conn.commit()
                            conn.close()
                            st.success(f"Approved claim: {r_name}!")
                            st.rerun()

    with tab5:
        st.subheader("📊 Flokus Learning Insights")
        st.write("Real-time telemetry showing study distribution and total XP momentum.")
        st.divider()

        st.markdown("### 🗓️ 7-Day Activity Radar")
        st.caption("Visual confirmation tracker checking if assignments were cleared each day.")
        
        today_dt = date.today()
        day_cols = st.columns(7)
        
        conn = sqlite3.connect('flokus.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT task_date FROM tasks WHERE is_completed = 1")
        active_dates = {row[0] for row in cursor.fetchall()}
        conn.close()
        
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
            stats_tasks = get_task_completion_stats()
            df_t = pd.DataFrame(stats_tasks, columns=["Subject", "Completed"]) if stats_tasks else pd.DataFrame(columns=["Subject", "Completed"])
            
            # Extract completions from physical creator block builds
            conn = sqlite3.connect('flokus.db')
            df_p = pd.read_sql_query("""
                SELECT platform as Subject, COUNT(id) as Completed 
                FROM creator_projects 
                WHERE status = 'Completed' 
                GROUP BY platform
            """, conn)
            conn.close()
            
            # Merge both sources into a unified metrics array
            df_all_stats = pd.concat([df_t, df_p], ignore_index=True)
            
            if not df_all_stats.empty:
                df_all_stats = df_all_stats.groupby("Subject")["Completed"].sum().reset_index()
                
            # Generate static template from your 11 locked-in categories 
            master_spine = list(SUBJECT_EMOJIS.keys())
            spine_map = {platform: 0 for platform in master_spine}
            
            # Map database tracking rows cleanly over our 11 categories
            if not df_all_stats.empty:
                for _, row in df_all_stats.iterrows():
                    if row["Subject"] in spine_map:
                        spine_map[row["Subject"]] = int(row["Completed"])
            
            # Convert dictionary back to a structured DataFrame for rendering
            df_master_analytics = pd.DataFrame(list(spine_map.items()), columns=["Subject", "Completed Milestones"])
            df_master_analytics = df_master_analytics.set_index("Subject")
            
            # --- NEW: Gather and compute focus time KPI telemetry ---
            conn = sqlite3.connect('flokus.db')
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(focus_minutes) FROM tasks WHERE is_completed = 1")
            total_focus_mins = cursor.fetchone()[0] or 0
            conn.close()
            
            # --- NEW: Calculate Autonomy vs. Rollover Telemetry Metrics ---
            conn = sqlite3.connect('flokus.db')
            cursor = conn.cursor()
            
            # Fetch count of all completed tasks
            cursor.execute("SELECT COUNT(id) FROM tasks WHERE is_completed = 1")
            total_done_tasks = cursor.fetchone()[0] or 0
            
            # Fetch count of tasks completed exactly on or before their target scheduled date
            cursor.execute("SELECT COUNT(id) FROM tasks WHERE is_completed = 1 AND actual_completion_date <= task_date")
            on_time_tasks = cursor.fetchone()[0] or 0
            conn.close()
            
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
            xp_data = get_xp_over_time()

            if len(xp_data) == 0:
                st.info("Earn some XP first to plot your development curve!")
            else:
                df_xp = pd.DataFrame(xp_data, columns=["Date", "Daily XP"])
                df_xp["Date"] = pd.to_datetime(df_xp["Date"])
                df_xp = df_xp.sort_values("Date")
                
                df_xp["Cumulative XP"] = df_xp["Daily XP"].cumsum()
                df_xp = df_xp.set_index("Date")
                st.line_chart(df_xp["Cumulative XP"])
            # --- END NEW ---

    # --- NEW: Admin AI Safety & Settings Tab ---
    with tab_safety:
        st.subheader("🤖 AI Safety & Settings")
        
        st.markdown("### 📜 Sonny's Chat Transcripts")
        st.caption("Review recent Socratic dialogues between Sonny and Floki.")
        
        session_id = "sonny_study_session"
        chat_logs = get_chat_history(session_id)
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
                conn = sqlite3.connect('flokus.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
                conn.commit()
                conn.close()
                st.success("Chat history cleared!")
                st.rerun()
                
        # --- NEW: Floki Persona Configuration ---
        st.divider()
        st.markdown("### 🎭 Floki Persona Configuration")
        st.caption("Change Floki's personality to keep Sonny engaged with different teaching styles.")
        current_p = get_floki_persona()
        selected_p = st.selectbox(
            "Active Persona",
            ["Socratic Tutor", "Norse Boatbuilder", "Space Robot"],
            index=["Socratic Tutor", "Norse Boatbuilder", "Space Robot"].index(current_p) if current_p in ["Socratic Tutor", "Norse Boatbuilder", "Space Robot"] else 0
        )
        if selected_p != current_p:
            set_floki_persona(selected_p)
            st.success(f"Floki's persona updated to {selected_p}!")
            st.rerun()
        # --- END NEW ---

        # --- NEW: One-Click Database Backups ---
        st.divider()
        st.markdown("### 📦 Database Management & Backups")
        st.caption("Keep your academic data safe. Back up your Flokus Academy database locally.")
        try:
            with open("flokus.db", "rb") as f:
                db_bytes = f.read()
        except Exception:
            db_bytes = b""
            
        if db_bytes:
            st.download_button(
                label="📥 Download flokus.db Backup",
                data=db_bytes,
                file_name=f"flokus_backup_{date.today().strftime('%Y_%m_%d')}.db",
                mime="application/x-sqlite3",
                use_container_width=True
            )
        else:
            st.error("Failed to read database file for backup.")
        # --- END NEW ---
                
        st.divider()
        st.markdown("### 🐾 Pet Override Console")
        st.caption("Manually adjust Sparky's levels or statistics for testing or corrections.")
        
        pet = get_pet_status()
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
                    conn = sqlite3.connect('flokus.db')
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE pet_status 
                        SET pet_name = ?, level = ?, current_xp = ?, strength = ?, intelligence = ?, creativity = ?, stamina = ?, max_stamina = ?, stage = ?, form_name = ?
                        WHERE id = ?
                    """, (new_name, new_level, new_xp, new_str, new_int, new_crt, new_stamina, new_max_stamina, new_stage, new_form_name, pet_id))
                    conn.commit()
                    conn.close()
                    st.success("Pet overridden successfully!")
                    st.rerun()