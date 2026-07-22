import sqlite3
import os
import time
import pandas as pd
from datetime import date, datetime, timedelta

def init_db():
    """Initializes the database structure if it does not exist."""
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        
        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                task_date TEXT NOT NULL,
                video_url TEXT,
                xp_reward INTEGER DEFAULT 10,
                is_completed INTEGER DEFAULT 0
            )
        ''')
        
        # Expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                cost REAL NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL
            )
        ''')
        
        # Rewards table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                xp_cost INTEGER NOT NULL
            )
        ''')
        
        # Purchases table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reward_name TEXT NOT NULL,
                xp_cost INTEGER NOT NULL,
                purchase_date TEXT NOT NULL
            )
        ''')
        
        conn.commit()
    finally:
        conn.close()
    
    # Run the schema verification to perform self-healing and updates
    verify_db_schema()

def verify_db_schema():
    """Verifies columns exist in the database tables and runs self-healing migrations if missing."""
    conn = sqlite3.connect('flokus.db')
    try:
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
        
        # Self-Healing Focus Minutes Tracker Column
        try:
            cursor.execute("SELECT focus_minutes FROM tasks LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE tasks ADD COLUMN focus_minutes INTEGER DEFAULT 0")
            conn.commit()
        
        # Self-Healing Actual Completion Date Stamp Column
        try:
            cursor.execute("SELECT actual_completion_date FROM tasks LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE tasks ADD COLUMN actual_completion_date TEXT DEFAULT ''")
            conn.commit()
        
        # Self-Healing Creator Projects Media Attachment Column
        try:
            cursor.execute("SELECT project_attachment FROM creator_projects LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE creator_projects ADD COLUMN project_attachment TEXT DEFAULT ''")
            conn.commit()
        
        # Digital Pet & AI Chat Tables Migration
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
        conn.commit()

        # 6. Seed Real-World Incentives
        real_world_rewards = [
            ("🪙 800 Minecoins (Minecraft)", 500, 5),
            ("🪨 1000 Shiny Rocks (Gorilla Tag)", 500, 5),
            ("🎮 1 Hour Gaming/YouTube Time", 100, 10),
            ("📅 1 Day Off Studies", 1000, 2),
            ("💵 $5 Cash Exchange", 250, 5),
            ("🕹️ New Game (Up to $20)", 1500, 1)
        ]
        for name, cost, qty in real_world_rewards:
            cursor.execute("SELECT id FROM rewards WHERE name = ?", (name,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO rewards (name, xp_cost, inventory_qty) VALUES (?, ?, ?)", (name, cost, qty))
        conn.commit()
                
        # 7. Create quest_completions table
        try:
            cursor.execute("SELECT id FROM quest_completions LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quest_completions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zone TEXT NOT NULL,
                    room INTEGER NOT NULL,
                    xp_reward INTEGER NOT NULL,
                    completion_date TEXT NOT NULL
                )
            """)
            conn.commit()

        # 8. Verify purchases table is_claimed column exists
        try:
            cursor.execute("SELECT is_claimed FROM purchases LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE purchases ADD COLUMN is_claimed INTEGER DEFAULT 0")
            conn.commit()

        # 9. Verify app_config table exists
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

        # 10. Verify school_events table exists & auto-seed starter events
        try:
            cursor.execute("SELECT id FROM school_events LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS school_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    event_date TEXT NOT NULL,
                    event_time TEXT DEFAULT '',
                    category TEXT NOT NULL,
                    importance TEXT DEFAULT 'Normal',
                    reminder_days INTEGER DEFAULT 3,
                    description TEXT DEFAULT '',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            
        # Check if school_events is empty and seed default events
        cursor.execute("SELECT COUNT(*) FROM school_events")
        if cursor.fetchone()[0] == 0:
            default_events = [
                ("🎉 First Day of School (5th Grade Kickoff)", "2026-08-17", "08:30 AM", "🎓 School Start / Term", "Urgent", 7, "Official start of the 2026-2027 school year! Get curriculum materials ready and kick off Day 1."),
                ("📚 UFA Q1 Grant Milestone Review", "2026-09-30", "05:00 PM", "💰 UFA Milestone", "Important", 5, "Quarterly Utah Fits All progress review & expense audit."),
                ("🧪 CrunchLabs STEM Box 1 Unboxing", "2026-08-21", "02:00 PM", "🛠️ Kit Delivery / Project", "Normal", 2, "First CrunchLabs engineering build kit assembly session."),
                ("🎥 Outschool Live Interactive Science Session", "2026-08-26", "10:00 AM", "🎥 Live Class (Outschool)", "Important", 1, "Live online science lab & group project.")
            ]
            cursor.executemany("""
                INSERT INTO school_events (title, event_date, event_time, category, importance, reminder_days, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, default_events)
            conn.commit()
            
    finally:
        conn.close()

# ==========================================
# CREATOR PROJECTS DATABASE OPERATIONS
# ==========================================

def add_creator_project(title, platform, xp_reward):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO creator_projects (title, platform, xp_reward) VALUES (?, ?, ?)", (title, platform, xp_reward))
        conn.commit()
    finally:
        conn.close()

def get_active_projects():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, platform, xp_reward FROM creator_projects WHERE status = 'In Progress'")
        projects = cursor.fetchall()
    finally:
        conn.close()
    return projects

def complete_creator_project(project_id, summary="", attachment=""):
    today_string = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        
        # 1. Fetch project details
        cursor.execute("SELECT xp_reward FROM creator_projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        
        cursor.execute("""
            UPDATE creator_projects 
            SET status = 'Completed', completion_date = ?, project_summary = ?, project_attachment = ? 
            WHERE id = ?
        """, (today_string, summary, attachment, project_id))
        
        # 2. Update pet XP & Stats if details found
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
    finally:
        conn.close()

def get_completed_projects(view_date):
    date_string = view_date.strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, platform, xp_reward, project_summary, project_attachment 
            FROM creator_projects 
            WHERE status = 'Completed' AND completion_date = ?
        """, (date_string,))
        projects = cursor.fetchall()
    finally:
        conn.close()
    return projects

def update_creator_project(project_id, title, platform, xp_reward, status="In Progress", completion_date="", project_summary="", project_attachment=""):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE creator_projects 
            SET title = ?, platform = ?, xp_reward = ?, status = ?, completion_date = ?, project_summary = ?, project_attachment = ?
            WHERE id = ?
        """, (title, platform, xp_reward, status, completion_date, project_summary, project_attachment, project_id))
        conn.commit()
    finally:
        conn.close()

def delete_creator_project(project_id):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM creator_projects WHERE id = ?", (project_id,))
        conn.commit()
    finally:
        conn.close()

# ==========================================
# DAILY QUESTS / TASKS DATABASE OPERATIONS
# ==========================================

def add_task_to_db(title, category, video_url, xp_reward, target_date, is_boss):
    date_string = target_date.strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (title, category, task_date, video_url, xp_reward, is_boss_fight) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, category, date_string, video_url, xp_reward, is_boss))
        conn.commit()
    finally:
        conn.close()

def get_pending_tasks(view_date):
    date_string = view_date.strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    try:
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
    finally:
        conn.close()
    return tasks

def complete_task(task_id, summary="", minutes=0):
    today_str = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        
        # 1. Fetch details of task before completing it
        cursor.execute("SELECT category, is_boss_fight, xp_reward FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        
        cursor.execute("""
            UPDATE tasks 
            SET is_completed = 1, task_summary = ?, focus_minutes = ?, actual_completion_date = ? 
            WHERE id = ?
        """, (summary, minutes, today_str, task_id))
        
        # 2. Update pet XP & Stats if task details are found
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
    finally:
        conn.close()

def get_completed_tasks(view_date):
    date_string = view_date.strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, category, video_url, xp_reward, is_boss_fight, task_summary 
            FROM tasks 
            WHERE is_completed = 1 AND task_date = ?
        """, (date_string,))
        tasks = cursor.fetchall()
    finally:
        conn.close()
    return tasks

def delete_task(task_id):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    finally:
        conn.close()

def update_task_details(task_id, title, category, video_url, xp_reward, target_date, is_boss):
    date_string = target_date.strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tasks 
            SET title = ?, category = ?, video_url = ?, xp_reward = ?, task_date = ?, is_boss_fight = ?
            WHERE id = ?
        """, (title, category, video_url, xp_reward, date_string, is_boss, task_id))
        conn.commit()
    finally:
        conn.close()

def get_all_pending_tasks():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, category, video_url, xp_reward, is_boss_fight, task_date 
            FROM tasks 
            WHERE is_completed = 0 
            ORDER BY task_date ASC, id ASC
        """)
        tasks = cursor.fetchall()
    finally:
        conn.close()
    return tasks

# ==========================================
# DIGITAL PET LOGIC & ACTIONS
# ==========================================

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
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, pet_name, level, current_xp, strength, intelligence, creativity, stamina, max_stamina, happiness, stage, form_name, accessory_parts 
            FROM pet_status LIMIT 1
        """)
        pet = cursor.fetchone()
    finally:
        conn.close()
    return pet

def use_pet_item(item_name):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        
        # Verify quantity
        cursor.execute("SELECT quantity FROM pet_inventory WHERE item_name = ?", (item_name,))
        row = cursor.fetchone()
        if not row or row[0] <= 0:
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
                cursor.execute("SELECT level, current_xp FROM pet_status WHERE id = ?", (p_id,))
                pet_lvl_xp = cursor.fetchone()
                if pet_lvl_xp:
                    lvl, cur_xp = pet_lvl_xp
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
            return f"🎉 Used {item_name}! ({stat_effect})"
    finally:
        conn.close()
    return "❌ Error using item!"

# ==========================================
# UFA FINANCES DATABASE OPERATIONS
# ==========================================

def add_expense(item_name, cost, category, status):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO expenses (item_name, cost, category, status) VALUES (?, ?, ?, ?)", 
                       (item_name, cost, category, status))
        conn.commit()
    finally:
        conn.close()

def get_all_expenses():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, item_name, cost, category, status FROM expenses")
        expenses = cursor.fetchall()
    finally:
        conn.close()
    return expenses

def update_expense_status(expense_id, new_status):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE expenses SET status = ? WHERE id = ?", (new_status, expense_id))
        conn.commit()
    finally:
        conn.close()

def update_expense_details(expense_id, item_name, cost, category, status):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE expenses 
            SET item_name = ?, cost = ?, category = ?, status = ?
            WHERE id = ?
        """, (item_name, cost, category, status, expense_id))
        conn.commit()
    finally:
        conn.close()

def delete_expense(expense_id):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
    finally:
        conn.close()

# ==========================================
# REWARDS STORE DATABASE OPERATIONS
# ==========================================

def add_reward(name, xp_cost, qty):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO rewards (name, xp_cost, inventory_qty) VALUES (?, ?, ?)", (name, xp_cost, qty))
        conn.commit()
    finally:
        conn.close()

def get_rewards():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, xp_cost, inventory_qty FROM rewards")
        rewards = cursor.fetchall()
    finally:
        conn.close()
    return rewards

def update_reward_details(reward_id, new_cost, new_qty):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE rewards 
            SET xp_cost = ?, inventory_qty = ? 
            WHERE id = ?
        """, (new_cost, new_qty, reward_id))
        conn.commit()
    finally:
        conn.close()

def delete_reward(reward_id):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rewards WHERE id = ?", (reward_id,))
        conn.commit()
    finally:
        conn.close()

def buy_reward(reward_id, reward_name, xp_cost):
    today_string = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO purchases (reward_name, xp_cost, purchase_date) VALUES (?, ?, ?)", 
                       (reward_name, xp_cost, today_string))
        cursor.execute("UPDATE rewards SET inventory_qty = MAX(0, inventory_qty - 1) WHERE id = ?", (reward_id,))
        
        # Route pet care items to pet inventory
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
        conn.commit()
    finally:
        conn.close()

# ==========================================
# CHAT HISTORY DATABASE OPERATIONS
# ==========================================

def add_chat_msg(session_id, sender, message):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_history (session_id, sender, message) 
            VALUES (?, ?, ?)
        """, (session_id, sender, message))
        conn.commit()
    finally:
        conn.close()

def get_chat_history(session_id):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sender, message, timestamp 
            FROM chat_history 
            WHERE session_id = ? 
            ORDER BY id ASC
        """, (session_id,))
        history = cursor.fetchall()
    finally:
        conn.close()
    return history

# ==========================================
# APP CONFIG DATABASE OPERATIONS
# ==========================================

def get_floki_persona():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_config WHERE key = 'floki_persona'")
        row = cursor.fetchone()
        val = row[0] if row else "Socratic Tutor"
    finally:
        conn.close()
    return val

def set_floki_persona(persona):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO app_config (key, value) VALUES ('floki_persona', ?)", (persona,))
        conn.commit()
    finally:
        conn.close()

# ==========================================
# METRICS & ANALYTICS DATA GENERATORS
# ==========================================

def get_xp_balance():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT SUM(CASE WHEN is_boss_fight = 1 THEN xp_reward * 2 ELSE xp_reward END) 
            FROM tasks 
            WHERE is_completed = 1
        """)
        earned_tasks = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(xp_reward) FROM creator_projects WHERE status = 'Completed'")
        earned_projects = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(xp_reward) FROM quest_completions")
        earned_quests = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(xp_cost) FROM purchases")
        spent = cursor.fetchone()[0] or 0
    finally:
        conn.close()
    return (earned_tasks + earned_projects + earned_quests) - spent

def get_purchase_history():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT reward_name, xp_cost, purchase_date FROM purchases ORDER BY id DESC")
        purchases = cursor.fetchall()
    finally:
        conn.close()
    return purchases

def get_task_completion_stats():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT category, COUNT(id) FROM tasks WHERE is_completed = 1 GROUP BY category")
        stats = cursor.fetchall()
    finally:
        conn.close()
    return stats

def get_xp_over_time():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT task_date, SUM(CASE WHEN is_boss_fight = 1 THEN xp_reward * 2 ELSE xp_reward END) 
            FROM tasks 
            WHERE is_completed = 1 
            GROUP BY task_date 
            ORDER BY task_date ASC
        """)
        data = cursor.fetchall()
    finally:
        conn.close()
    return data

def get_daily_streak():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT task_date FROM tasks WHERE is_completed = 1 ORDER BY task_date DESC")
        rows = cursor.fetchall()
    finally:
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
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status, SUM(cost) FROM expenses GROUP BY status")
        rows = cursor.fetchall()
    finally:
        conn.close()
    return dict(rows)

def get_full_portfolio_data(start_dt, end_dt):
    start_str = start_dt.strftime("%Y-%m-%d")
    end_str = end_dt.strftime("%Y-%m-%d")
    
    conn = sqlite3.connect('flokus.db')
    try:
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
    finally:
        conn.close()
    
    df_combined = pd.concat([df_tasks, df_projects], ignore_index=True)
    if not df_combined.empty:
        df_combined = df_combined.sort_values(by='Date', ascending=False)
        
    return df_combined

def get_pet_inventory():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT item_name, quantity FROM pet_inventory WHERE quantity > 0")
        pet_inv = cursor.fetchall()
    finally:
        conn.close()
    return pet_inv

def deduct_pet_stamina(pet_id, amount):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE pet_status SET stamina = MAX(0, stamina - ?) WHERE id = ?", (amount, pet_id))
        conn.commit()
    finally:
        conn.close()

def complete_quest_room(pet_id, active_room, zone):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        # Fetch pet details
        cursor.execute("SELECT level, current_xp, strength, intelligence, creativity, stage, form_name FROM pet_status WHERE id = ?", (pet_id,))
        pet = cursor.fetchone()
        if not pet:
            return "❌ Pet not found", 0
            
        pet_level, pet_xp, strength, intelligence, creativity, stage, form_name = pet
        is_boss = (active_room == 3)
        xp_gain = 50 if is_boss else 20
        
        # Award XP to pet
        new_xp = pet_xp + xp_gain
        next_lvl_xp = int(100 * (pet_level)**1.8)
        new_lvl = pet_level
        new_stage = stage
        new_form = form_name
        
        if new_xp >= next_lvl_xp:
            new_lvl += 1
            new_xp = max(0, new_xp - next_lvl_xp)
            new_stage, new_form = calculate_evolution_internal(new_lvl, strength, intelligence, creativity)
            
        stat_gain_str = ""
        if is_boss:
            # Increase all stats by 2
            cursor.execute("""
                UPDATE pet_status 
                SET level = ?, current_xp = ?, stage = ?, form_name = ?,
                    strength = strength + 2, intelligence = intelligence + 2, creativity = creativity + 2
                WHERE id = ?
            """, (new_lvl, new_xp, new_stage, new_form, pet_id))
            stat_gain_str = " +2 to all stats!"
            
            # Add bonus random item
            import random
            bonus_items = ["🥩 Cyber-Protein", "💾 Memory Chip", "⚡ Giga-Soda", "🔮 Omni-Treat"]
            won_item = random.choice(bonus_items)
            cursor.execute("""
                INSERT INTO pet_inventory (item_name, quantity) 
                VALUES (?, 1) 
                ON CONFLICT(item_name) DO UPDATE SET quantity = quantity + 1
            """, (won_item,))
            stat_gain_str += f" Also found 1x {won_item}!"
        else:
            # Increase active zone stat by 1
            stat_to_up = "intelligence" if "INT" in zone else ("creativity" if "CRT" in zone else "strength")
            cursor.execute(f"""
                UPDATE pet_status 
                SET level = ?, current_xp = ?, stage = ?, form_name = ?,
                    {stat_to_up} = {stat_to_up} + 1
                WHERE id = ?
            """, (new_lvl, new_xp, new_stage, new_form, pet_id))
            stat_gain_str = f" +1 {stat_to_up.upper()}!"
            
        # Record quest completion for Sonny's student XP balance
        today_str = date.today().strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT INTO quest_completions (zone, room, xp_reward, completion_date)
            VALUES (?, ?, ?, ?)
        """, (zone, active_room, xp_gain, today_str))
        
        conn.commit()
    finally:
        conn.close()
    return stat_gain_str, xp_gain

def fail_quest_room(pet_id):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE pet_status SET stamina = MAX(0, stamina - 1) WHERE id = ?", (pet_id,))
        conn.commit()
        cursor.execute("SELECT stamina FROM pet_status WHERE id = ?", (pet_id,))
        new_stam = cursor.fetchone()[0]
    finally:
        conn.close()
    return new_stam

def get_all_creator_projects():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, platform, xp_reward, status, completion_date, project_summary, project_attachment FROM creator_projects ORDER BY id DESC")
        projs = cursor.fetchall()
    finally:
        conn.close()
    return projs

def get_all_purchases():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, reward_name, xp_cost, purchase_date, is_claimed FROM purchases ORDER BY id DESC")
        purchases = cursor.fetchall()
    finally:
        conn.close()
    return purchases

def mark_purchase_claimed(purchase_id):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE purchases SET is_claimed = 1 WHERE id = ?", (purchase_id,))
        conn.commit()
    finally:
        conn.close()

def get_active_task_dates():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT task_date FROM tasks WHERE is_completed = 1")
        active_dates = {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()
    return active_dates

def get_completed_projects_by_platform():
    conn = sqlite3.connect('flokus.db')
    try:
        df_p = pd.read_sql_query("""
            SELECT platform as Subject, COUNT(id) as Completed 
            FROM creator_projects 
            WHERE status = 'Completed' 
            GROUP BY platform
        """, conn)
    finally:
        conn.close()
    return df_p

def get_total_focus_minutes():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(focus_minutes) FROM tasks WHERE is_completed = 1")
        val = cursor.fetchone()[0] or 0
    finally:
        conn.close()
    return val

def get_autonomy_metrics():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(id) FROM tasks WHERE is_completed = 1")
        total_done_tasks = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(id) FROM tasks WHERE is_completed = 1 AND actual_completion_date <= task_date")
        on_time_tasks = cursor.fetchone()[0] or 0
    finally:
        conn.close()
    return total_done_tasks, on_time_tasks

def clear_chat_history(session_id):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()

def override_pet_status(pet_id, pet_name, level, current_xp, strength, intelligence, creativity, stamina, max_stamina, stage, form_name):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE pet_status 
            SET pet_name = ?, level = ?, current_xp = ?, strength = ?, intelligence = ?, creativity = ?, stamina = ?, max_stamina = ?, stage = ?, form_name = ?
            WHERE id = ?
        """, (pet_name, level, current_xp, strength, intelligence, creativity, stamina, max_stamina, stage, form_name, pet_id))
        conn.commit()
    finally:
        conn.close()

def reset_all_test_data():
    """Wipes test activity data (tasks, projects, chat, purchases, quest logs, uploads) 
    and resets pet status and UFA financial expenses to baseline Odyssey seed data."""
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks")
        cursor.execute("DELETE FROM creator_projects")
        cursor.execute("DELETE FROM purchases")
        cursor.execute("DELETE FROM chat_history")
        cursor.execute("DELETE FROM quest_completions")
        
        # Reset Digital Pet status
        cursor.execute("DELETE FROM pet_status")
        cursor.execute("""
            INSERT INTO pet_status (pet_name, level, current_xp, strength, intelligence, creativity, stamina, max_stamina, happiness, stage, form_name, accessory_parts) 
            VALUES ('Sparky', 1, 0, 5, 5, 5, 10, 10, 100, 'Egg', 'Cosmic Egg', '[]')
        """)
        
        # Reset Pet Inventory
        cursor.execute("DELETE FROM pet_inventory")
        cursor.execute("INSERT INTO pet_inventory (item_name, quantity) VALUES ('🥩 Cyber-Protein', 2)")
        
        # Reset Expenses to Odyssey baseline
        cursor.execute("DELETE FROM expenses")
        odyssey_expenses = [
            ("Beast Academy Level 2 Bundle", 170.00, "Curriculum & Workbooks", "Approved & Direct Paid"),
            ("Free Market Rules: Economics Curriculum", 126.00, "Curriculum & Workbooks", "Approved & Direct Paid"),
            ("Americas History Bundle (Volumes 1-3)", 179.98, "Curriculum & Workbooks", "Approved & Direct Paid"),
            ("Annual Build Box Subscription", 329.40, "Supplies & Materials", "Approved & Direct Paid"),
            ("GoChess Lite Modern Interactive Chess", 309.90, "Supplies & Materials", "Approved & Direct Paid"),
            ("The Basics of Critical Thinking", 30.99, "Curriculum & Workbooks", "Approved & Direct Paid"),
            ("Emerging Writers Bundle Three", 247.00, "Curriculum & Workbooks", "Approved & Direct Paid")
        ]
        cursor.executemany("""
            INSERT INTO expenses (item_name, cost, category, status) 
            VALUES (?, ?, ?, ?)
        """, odyssey_expenses)
        
        conn.commit()
    finally:
        conn.close()

    # Clear uploads folder
    if os.path.exists("uploads"):
        for fname in os.listdir("uploads"):
            fpath = os.path.join("uploads", fname)
            if os.path.isfile(fpath):
                try:
                    os.remove(fpath)
                except Exception:
                    pass
    return True

# ==========================================
# SCHOOL EVENTS DATABASE OPERATIONS
# ==========================================

def add_school_event(title, event_date, event_time="", category="📌 General", importance="Normal", reminder_days=3, description=""):
    """Adds a new school event to the database."""
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO school_events (title, event_date, event_time, category, importance, reminder_days, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, event_date, event_time, category, importance, reminder_days, description))
        conn.commit()
        event_id = cursor.lastrowid
    finally:
        conn.close()
    return event_id

def get_school_events(start_date=None, end_date=None, category_filter=None):
    """Retrieves school events with optional date range and category filtering."""
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        query = "SELECT id, title, event_date, event_time, category, importance, reminder_days, description, created_at FROM school_events WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND event_date >= ?"
            params.append(str(start_date))
        if end_date:
            query += " AND event_date <= ?"
            params.append(str(end_date))
        if category_filter and category_filter != "All Categories":
            query += " AND category = ?"
            params.append(category_filter)
            
        query += " ORDER BY event_date ASC, event_time ASC"
        cursor.execute(query, params)
        events = cursor.fetchall()
    finally:
        conn.close()
    return events

def get_upcoming_event_notifications(as_of_date=None):
    """Returns active event notifications whose reminder window overlaps with as_of_date."""
    if as_of_date is None:
        as_of_date = date.today()
    elif isinstance(as_of_date, str):
        as_of_date = datetime.strptime(as_of_date, "%Y-%m-%d").date()

    conn = sqlite3.connect('flokus.db')
    notifications = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, event_date, event_time, category, importance, reminder_days, description FROM school_events WHERE event_date >= ? ORDER BY event_date ASC", (str(as_of_date),))
        events = cursor.fetchall()
        
        for ev in events:
            ev_id, title, ev_date_str, ev_time, cat, importance, reminder_days, desc = ev
            try:
                ev_date = datetime.strptime(ev_date_str, "%Y-%m-%d").date()
                days_left = (ev_date - as_of_date).days
                if 0 <= days_left <= reminder_days:
                    notifications.append({
                        "id": ev_id,
                        "title": title,
                        "event_date": ev_date,
                        "event_date_str": ev_date_str,
                        "event_time": ev_time,
                        "category": cat,
                        "importance": importance,
                        "days_left": days_left,
                        "description": desc
                    })
            except Exception:
                continue
    finally:
        conn.close()
    return notifications

def update_school_event(event_id, title, event_date, event_time, category, importance, reminder_days, description):
    """Updates an existing school event."""
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE school_events
            SET title = ?, event_date = ?, event_time = ?, category = ?, importance = ?, reminder_days = ?, description = ?
            WHERE id = ?
        """, (title, str(event_date), event_time, category, importance, reminder_days, description, event_id))
        conn.commit()
    finally:
        conn.close()

def delete_school_event(event_id):
    """Deletes a school event from the database."""
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM school_events WHERE id = ?", (event_id,))
        conn.commit()
    finally:
        conn.close()

def get_next_major_school_event(as_of_date=None):
    """Returns the next major school start or urgent event for countdown display."""
    if as_of_date is None:
        as_of_date = date.today()
    elif isinstance(as_of_date, str):
        as_of_date = datetime.strptime(as_of_date, "%Y-%m-%d").date()

    conn = sqlite3.connect('flokus.db')
    event_data = None
    try:
        cursor = conn.cursor()
        # Prioritize School Start or Urgent event >= as_of_date
        cursor.execute("""
            SELECT id, title, event_date, event_time, category, importance, description 
            FROM school_events 
            WHERE event_date >= ? AND (category LIKE '%School Start%' OR importance = 'Urgent')
            ORDER BY event_date ASC 
            LIMIT 1
        """, (str(as_of_date),))
        row = cursor.fetchone()
        if not row:
            # Fallback to any event >= as_of_date
            cursor.execute("""
                SELECT id, title, event_date, event_time, category, importance, description 
                FROM school_events 
                WHERE event_date >= ? 
                ORDER BY event_date ASC 
                LIMIT 1
            """, (str(as_of_date),))
            row = cursor.fetchone()
            
        if row:
            ev_date = datetime.strptime(row[2], "%Y-%m-%d").date()
            days_left = (ev_date - as_of_date).days
            event_data = {
                "id": row[0],
                "title": row[1],
                "event_date": ev_date,
                "event_date_str": row[2],
                "event_time": row[3],
                "category": row[4],
                "importance": row[5],
                "description": row[6],
                "days_left": days_left
            }
    finally:
        conn.close()
    return event_data