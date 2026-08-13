# ==========================================
# FLOKUS ACADEMY — GAMIFICATION DATABASE STUBS
# Extracted from database.py on 2026-08-12.
#
# These functions are quarantined from the main app.
# To reactivate, merge this file back into database.py.
# All SQLite tables remain intact in flokus.db.
# ==========================================

import sqlite3
import random
from datetime import date


# ---------------------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------------------

def _get_active_pet_id(cursor, pet_id):
    if pet_id is not None:
        cursor.execute("SELECT id FROM pet_status WHERE id = ?", (pet_id,))
        if cursor.fetchone():
            return pet_id
    cursor.execute("SELECT id FROM pet_status LIMIT 1")
    row = cursor.fetchone()
    return row[0] if row else 1


# ---------------------------------------------------------------------------
# SPORE EVOLUTION ENGINE
# ---------------------------------------------------------------------------

def calculate_evolution_internal(level, strength, intelligence, creativity):
    if level >= 51:
        return "Cosmic Sovereign", "Aether-Wyrm 🌌"
    elif level >= 31:
        top_stat = max(strength, intelligence, creativity)
        if top_stat == intelligence:
            return "Apex Titan", "Chrono-Sphinx 🦅"
        elif top_stat == creativity:
            return "Apex Titan", "Matrix-Colossus 🐲"
        else:
            return "Apex Titan", "Mecha-Behemoth 🦣"
    elif level >= 16:
        top_stat = max(strength, intelligence, creativity)
        if top_stat == intelligence:
            return "Land Crawler", "Cyber-Drake 🐉"
        elif top_stat == creativity:
            return "Land Crawler", "Chameleon-Drake 🦎"
        else:
            return "Land Crawler", "Armored-Pangolin 🐊"
    elif level >= 6:
        top_stat = max(strength, intelligence, creativity)
        if top_stat == intelligence:
            return "Multicellular Organism", "Techno-Hydra 🐙"
        elif top_stat == creativity:
            return "Multicellular Organism", "Bioluminescent Jellyfish 🪼"
        else:
            return "Multicellular Organism", "Cyber-Trilobite 🦑"
    elif level >= 2:
        return "Single Celled Organism", "Omni-Protozoan 🦠"
    else:
        return "Primordial Spore", "Cosmic Spore 🧫"


# ---------------------------------------------------------------------------
# PET XP & LEVELING ENGINE
# ---------------------------------------------------------------------------

def process_pet_xp_and_leveling(pet_id=1, xp_to_add=0, stat_category=None):
    """
    Centralized pet XP gain & leveling engine.
    Processes XP additions, handles multi-level overflow, awards +2 Skill Points per Level Up,
    updates stats (INT/CRT/STR), and recalculates Spore Evolution Stage & Form.
    """
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT level, current_xp, strength, intelligence, creativity, skill_points, stage, form_name 
            FROM pet_status WHERE id = ?
        """, (pet_id,))
        row = cursor.fetchone()
        if not row:
            return

        level, current_xp, str_val, int_val, crt_val, sp_val, stage, form_name = row
        if sp_val is None:
            sp_val = 3

        if stat_category:
            cat_str = str(stat_category).lower()
            if "math" in cat_str or "logic" in cat_str or "intellect" in cat_str:
                int_val += 1
            elif "stem" in cat_str or "art" in cat_str or "creator" in cat_str or "mutation" in cat_str:
                crt_val += 1
            else:
                str_val += 1

        current_xp += xp_to_add

        # Robust multi-level overflow loop
        while True:
            next_level_xp = int(100 * (level)**1.5)
            if current_xp >= next_level_xp and level < 100:
                current_xp -= next_level_xp
                level += 1
                sp_val += 2  # +2 Skill Points on EVERY Level Up!
                str_val += 1
                int_val += 1
                crt_val += 1
            else:
                break

        new_stage, new_form = calculate_evolution_internal(level, str_val, int_val, crt_val)

        cursor.execute("""
            UPDATE pet_status 
            SET level = ?, current_xp = ?, strength = ?, intelligence = ?, creativity = ?, skill_points = ?, stage = ?, form_name = ?
            WHERE id = ?
        """, (level, current_xp, str_val, int_val, crt_val, sp_val, new_stage, new_form, pet_id))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# PET STATUS & INVENTORY
# ---------------------------------------------------------------------------

def get_pet_status():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, pet_name, level, current_xp, strength, intelligence, creativity, stamina, max_stamina, happiness, stage, form_name, accessory_parts 
            FROM pet_status LIMIT 1
        """)
        pet = cursor.fetchone()

        # Auto-process pending level ups if current_xp exceeds next_level_xp
        if pet:
            p_id, _, level, current_xp, _, _, _, _, _, _, _, _, _ = pet
            next_level_xp = int(100 * (level)**1.5)
            if current_xp >= next_level_xp:
                conn.close()
                process_pet_xp_and_leveling(p_id, 0)
                conn = sqlite3.connect('flokus.db')
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, pet_name, level, current_xp, strength, intelligence, creativity, stamina, max_stamina, happiness, stage, form_name, accessory_parts 
                    FROM pet_status LIMIT 1
                """)
                pet = cursor.fetchone()
    finally:
        conn.close()
    return pet


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


# ---------------------------------------------------------------------------
# DUNGEON QUEST ENGINE
# ---------------------------------------------------------------------------

def complete_quest_room(pet_id, active_room, zone):
    conn = sqlite3.connect('flokus.db')
    stat_gain_str = ""
    try:
        cursor = conn.cursor()
        p_id = _get_active_pet_id(cursor, pet_id)
        is_boss = (active_room == 3)
        xp_gain = 50 if is_boss else 20

        if is_boss:
            cursor.execute("""
                UPDATE pet_status 
                SET strength = strength + 2, intelligence = intelligence + 2, creativity = creativity + 2
                WHERE id = ?
            """, (p_id,))
            stat_gain_str = " +2 to all stats!"

            bonus_items = ["🥩 Cyber-Protein", "💾 Memory Chip", "⚡ Giga-Soda", "🔮 Omni-Treat"]
            won_item = random.choice(bonus_items)
            cursor.execute("""
                INSERT INTO pet_inventory (item_name, quantity) 
                VALUES (?, 1) 
                ON CONFLICT(item_name) DO UPDATE SET quantity = quantity + 1
            """, (won_item,))
            stat_gain_str += f" Also found 1x {won_item}!"
        else:
            stat_to_up = "intelligence" if "INT" in zone else ("creativity" if "CRT" in zone else "strength")
            cursor.execute(f"UPDATE pet_status SET {stat_to_up} = {stat_to_up} + 1 WHERE id = ?", (p_id,))
            stat_gain_str = f" +1 {stat_to_up.upper()}!"

        cursor.execute("UPDATE side_quests SET current_count = MIN(target_count, current_count + 1) WHERE is_claimed = 0 AND (category = 'Dungeon' OR category = 'General')")
        today_str = date.today().strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT INTO quest_completions (zone, room, xp_reward, completion_date)
            VALUES (?, ?, ?, ?)
        """, (zone, active_room, xp_gain, today_str))
        conn.commit()
    finally:
        conn.close()

    process_pet_xp_and_leveling(p_id, xp_gain, zone)
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


# ---------------------------------------------------------------------------
# PET SKILL TREE
# ---------------------------------------------------------------------------

def get_pet_skill_points(pet_id=None):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        p_id = _get_active_pet_id(cursor, pet_id)
        cursor.execute("SELECT skill_points FROM pet_status WHERE id = ?", (p_id,))
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else 3
    finally:
        conn.close()


def get_unlocked_skills(pet_id=None):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        p_id = _get_active_pet_id(cursor, pet_id)
        cursor.execute("SELECT skill_id FROM pet_unlocked_skills WHERE pet_id = ?", (p_id,))
        rows = cursor.fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


def unlock_pet_skill(skill_id, sp_cost, pet_id=None):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        p_id = _get_active_pet_id(cursor, pet_id)
        cursor.execute("SELECT skill_points FROM pet_status WHERE id = ?", (p_id,))
        row = cursor.fetchone()
        sp = row[0] if row and row[0] is not None else 0
        if sp < sp_cost:
            return False, f"⚠️ Not enough Skill Points! (Available: {sp} SP, Cost: {sp_cost} SP)"

        cursor.execute("INSERT OR IGNORE INTO pet_unlocked_skills (pet_id, skill_id) VALUES (?, ?)", (p_id, skill_id))
        cursor.execute("UPDATE pet_status SET skill_points = MAX(0, skill_points - ?) WHERE id = ?", (sp_cost, p_id))
        conn.commit()
        return True, f"🎉 Skill '{skill_id}' unlocked successfully!"
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


# ---------------------------------------------------------------------------
# SIDE QUESTS
# ---------------------------------------------------------------------------

def get_side_quests():
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, description, category, reward_xp, reward_sp, target_count, current_count, is_claimed FROM side_quests ORDER BY id ASC")
        return cursor.fetchall()
    finally:
        conn.close()


def claim_side_quest_reward(quest_id, pet_id=None):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        p_id = _get_active_pet_id(cursor, pet_id)
        cursor.execute("SELECT reward_xp, reward_sp, is_claimed, current_count, target_count FROM side_quests WHERE id = ?", (quest_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Side quest not found."
        rxp, rsp, is_claimed, cur_c, tgt_c = row
        if is_claimed == 1:
            return False, "Reward already claimed!"
        if cur_c < tgt_c:
            return False, "Side quest target not met yet!"

        cursor.execute("UPDATE side_quests SET is_claimed = 1 WHERE id = ?", (quest_id,))
        cursor.execute("UPDATE pet_status SET skill_points = skill_points + ? WHERE id = ?", (rsp, p_id))
        conn.commit()
    finally:
        conn.close()

    process_pet_xp_and_leveling(p_id, rxp, 'General')
    return True, f"🎉 Claimed +{rxp} XP and +{rsp} Skill Point(s)!"


def update_side_quest_progress(category_or_type, increment=1):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE side_quests SET current_count = MIN(target_count, current_count + ?) WHERE is_claimed = 0 AND (category = ? OR category = 'General')", (increment, category_or_type))
        conn.commit()
    finally:
        conn.close()


def record_trivia_victory(pet_id=None, xp_won=30, sp_won=1):
    conn = sqlite3.connect('flokus.db')
    try:
        cursor = conn.cursor()
        p_id = _get_active_pet_id(cursor, pet_id)
        cursor.execute("UPDATE pet_status SET skill_points = skill_points + ? WHERE id = ?", (sp_won, p_id))
        conn.commit()
    finally:
        conn.close()

    process_pet_xp_and_leveling(p_id, xp_won, 'Logic')
    update_side_quest_progress('Trivia', 1)
