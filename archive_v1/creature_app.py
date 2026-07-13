import streamlit as st
import sqlite3
import pandas as pd
import os

# --- Clear Streamlit Cache ---
st.cache_data.clear()

# --- Database Setup --- (Must match app.py!)
DB_PATH = os.path.join(os.path.dirname(__file__), "flokus_academy.db")

# --- Database Helpers ---
def run_query(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql(query, conn, params=params)

def execute_query(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

# --- App Layout ---
st.set_page_config(page_title="Flokus Bestiary", page_icon="🐉", layout="centered")
st.title("🐉 Flokus Bestiary")
st.markdown("Welcome to the Evolution Chamber. Spend your hard-earned Evolution Points (EP) to upgrade your companion!")

# --- The Game Economy Logic ---
# 1. Calculate Total EP Earned (1 EP per completed assignment)
completed_data = run_query("SELECT COUNT(*) as count FROM assignments WHERE status = 'completed'")
total_ep_earned = completed_data.iloc[0]['count']

# 2. Fetch Current Creature Stats
creature = run_query("SELECT * FROM creatures LIMIT 1").iloc[0]

# 3. Calculate EP Spent (Base stats start at 1, so we subtract 3)
ep_spent = (creature['strength'] - 1) + (creature['intelligence'] - 1) + (creature['agility'] - 1)

# 4. Calculate Available EP
available_ep = total_ep_earned - ep_spent

# --- UI: Dashboard ---
st.header(f"{creature['name']} - {creature['stage']}")
st.metric("Evolution Points (EP) Available", available_ep)

# --- UI: Upgrade Interface ---
col1, col2, col3 = st.columns(3)

def upgrade_stat(stat_name):
    if available_ep > 0:
        new_val = int(creature[stat_name]) + 1
        execute_query(f"UPDATE creatures SET {stat_name} = ? WHERE creature_id = ?", (new_val, int(creature['creature_id'])))
        # Simple evolution logic: Egg -> Hatchling after 5 total stats
        if (ep_spent + 1) >= 5 and creature['stage'] == 'Mystic Egg':
            execute_query("UPDATE creatures SET stage = 'Hatchling' WHERE creature_id = ?", (int(creature['creature_id']),))
            st.toast("🎉 Woah! Your Egg is evolving into a Hatchling!")
        st.rerun()
    else:
        st.error("Not enough EP! Complete more assignments on your dashboard.")

with col1:
    st.subheader("⚔️ Strength")
    st.title(creature['strength'])
    if st.button("Upgrade Strength (+1)"): upgrade_stat('strength')

with col2:
    st.subheader("🧠 Intelligence")
    st.title(creature['intelligence'])
    if st.button("Upgrade Intelligence (+1)"): upgrade_stat('intelligence')

with col3:
    st.subheader("⚡ Agility")
    st.title(creature['agility'])
    if st.button("Upgrade Agility (+1)"): upgrade_stat('agility')