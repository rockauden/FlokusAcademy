import streamlit as st
import streamlit.components.v1 as components
import database
import config
import random
from ai_tutor import generate_quest_question

# Ensure database is initialized
database.init_db()

st.title("🐾 Sparky's Spore Evolution & Quest Arena")
st.caption("Evolve Sparky from a single-celled spore into a Cosmic Sovereign, unlock AC Valhalla constellation skills, and battle Knowledge Guardians!")

# Fetch Pet Status
pet = database.get_pet_status()
if not pet:
    st.info("Sparky is dormant in the primordial soup. Check back later!")
else:
    pet_id = pet[0]
    pet_name = pet[1]
    pet_level = pet[2]
    pet_xp = pet[3]
    strength = pet[4]
    intelligence = pet[5]
    creativity = pet[6]
    stamina = pet[7]
    max_stamina = pet[8]
    happiness = pet[9]
    stage = pet[10]
    form_name = pet[11]
    
    skill_points = database.get_pet_skill_points(pet_id)
    unlocked_skills = database.get_unlocked_skills(pet_id)
    
    # XP level calculations
    next_level_xp = int(100 * (pet_level)**1.8)
    xp_progress = min(pet_xp / next_level_xp, 1.0) if next_level_xp > 0 else 0.0
    
    # Helper to get exact spore evolutionary avatar (NEVER fall back to paw prints for microbes!)
    def get_spore_avatar(stage_str, form_str):
        if form_str and ord(form_str[-1]) > 127:
            return form_str[-1]
        stage_map = {
            "Primordial Spore": "🧫",
            "Single Celled Organism": "🦠",
            "Multicellular Organism": "🪼",
            "Land Crawler": "🦎",
            "Apex Titan": "🐲",
            "Cosmic Sovereign": "🌌"
        }
        return stage_map.get(stage_str, "🦠")

    avatar_emoji = get_spore_avatar(stage, form_name)
    clean_form_name = form_name[:-2].strip() if form_name and ord(form_name[-1]) > 127 else form_name

    # --- 5 RPG ADVENTURE TABS ---
    tab_status, tab_tree, tab_trivia, tab_dungeon, tab_sidequests = st.tabs([
        "🐾 Spore Status & Care", 
        "🌳 Constellation Skill Web", 
        "⚔️ Trivia Battle Arena", 
        "🗺️ Dungeon Expedition",
        "📜 Side Quests Board"
    ])
    
    # ==========================================
    # TAB 1: SPORE STATUS & CARE
    # ==========================================
    with tab_status:
        # Dynamic theme colors based on attribute or neon chameleon aura
        if "crt_2" in unlocked_skills:
            border_color = "#ec4899"
            bg_style = "linear-gradient(135deg, #3b0764 0%, #1e1b4b 100%)"
            glow_style = "box-shadow: 0 0 30px rgba(236, 72, 153, 0.6);"
            text_color = "#f472b6"
        elif stage == "Primordial Spore":
            border_color = "#f59e0b"
            bg_style = "linear-gradient(135deg, #1e180d 0%, #0f0c07 100%)"
            glow_style = "box-shadow: 0 0 20px rgba(245, 158, 11, 0.3);"
            text_color = "#fbbf24"
        elif stage == "Single Celled Organism":
            border_color = "#10b981"
            bg_style = "linear-gradient(135deg, #064e3b 0%, #022c22 100%)"
            glow_style = "box-shadow: 0 0 20px rgba(16, 185, 129, 0.4);"
            text_color = "#34d399"
        elif stage == "Multicellular Organism":
            border_color = "#00f0ff"
            bg_style = "linear-gradient(135deg, #0c1b26 0%, #060e14 100%)"
            glow_style = "box-shadow: 0 0 20px rgba(0, 240, 255, 0.4);"
            text_color = "#00f0ff"
        elif stage == "Land Crawler":
            border_color = "#a855f7"
            bg_style = "linear-gradient(135deg, #200f35 0%, #0f071a 100%)"
            glow_style = "box-shadow: 0 0 20px rgba(168, 85, 247, 0.4);"
            text_color = "#c084fc"
        else: # Apex Titan / Sovereign
            border_color = "#f97316"
            bg_style = "linear-gradient(135deg, #2b1104 0%, #160902 100%)"
            glow_style = "box-shadow: 0 0 25px rgba(249, 115, 22, 0.5);"
            text_color = "#ff983d"

        col_pet_card, col_pet_stats = st.columns([0.45, 0.55])
        with col_pet_card:
            st.markdown(
                f"""
                <div style="background: {bg_style}; padding: 25px; border-radius: 15px; border: 2px solid {border_color}; {glow_style} text-align: center;">
                    <span style="font-size: 85px;">{avatar_emoji}</span>
                    <h2 style="color: {text_color}; margin-top: 5px; margin-bottom: 0;">{clean_form_name}</h2>
                    <p style="color: #A6ADC8; margin-top: 2px;">Evolutionary Stage: <strong>{stage}</strong></p>
                    <p style="color: #fbbf24; font-weight: bold; margin-top: -5px;">⭐ {skill_points} Skill Points Available</p>
                    <div style="background-color: #313244; border-radius: 10px; height: 12px; width: 100%; margin-top: 15px;">
                        <div style="background-color: {border_color}; height: 100%; border-radius: 10px; width: {int(xp_progress * 100)}%;"></div>
                    </div>
                    <small style="color: #BAC2DE;">Level {pet_level} ({pet_xp} / {next_level_xp} XP)</small>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col_pet_stats:
            st.markdown("### 🧬 Evolutionary Attributes & Energy")
            
            effective_max_stamina = max_stamina + (5 if "int_2" in unlocked_skills else 0)
            st.write(f"🔋 **Stamina (Energy):** {stamina} / {effective_max_stamina}")
            st.progress(stamina / effective_max_stamina if effective_max_stamina > 0 else 0.0)
            
            st.write(f"🧠 **Intelligence (INT):** {intelligence}")
            st.progress(min(intelligence / 100.0, 1.0))
            
            st.write(f"🎨 **Creativity / Mutation (CRT):** {creativity}")
            st.progress(min(creativity / 100.0, 1.0))
            
            st.write(f"💪 **Strength / Adaptation (STR):** {strength}")
            st.progress(min(strength / 100.0, 1.0))

        st.divider()

        # --- SPORE EVOLUTION TIMELINE ---
        st.markdown("### 🧫 Spore Metamorphosis Path")
        spore_stages = [
            ("🧫 Spore", "Lvl 1", 1),
            ("🦠 Single Cell", "Lvl 2", 2),
            ("🪼 Multicellular", "Lvl 6", 6),
            ("🦎 Land Crawler", "Lvl 16", 16),
            ("🐲 Apex Titan", "Lvl 31", 31),
            ("🌌 Sovereign", "Lvl 51", 51)
        ]
        
        timeline_cols = st.columns(6)
        for s_i, (s_label, s_lvl_str, s_req_lvl) in enumerate(spore_stages):
            with timeline_cols[s_i]:
                if pet_level >= s_req_lvl:
                    st.markdown(
                        f"""
                        <div style="background-color: #064e3b; border: 2px solid #10b981; border-radius: 10px; padding: 8px; text-align: center; color: #34d399;">
                            <strong style="font-size: 13px;">{s_label}</strong><br>
                            <small style="color: #a7f3d0;">✓ {s_lvl_str}</small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div style="background-color: #1e1e2e; border: 1px dashed #45475a; border-radius: 10px; padding: 8px; text-align: center; color: #6c7086;">
                            <strong style="font-size: 13px;">{s_label}</strong><br>
                            <small style="color: #6c7086;">🔒 {s_lvl_str}</small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        st.divider()

        # --- CARE & FEEDING INVENTORY ---
        st.markdown("### 🎒 Spore Care & Feeding Inventory")
        pet_inv = database.get_pet_inventory()
        
        if not pet_inv:
            st.info("Your pet inventory is empty. Buy care items (like Cyber-Protein or Memory Chips) from the XP Store!")
        else:
            inv_cols = st.columns(len(pet_inv))
            for idx, (item, qty) in enumerate(pet_inv):
                with inv_cols[idx]:
                    with st.container(border=True):
                        st.write(f"**{item}**")
                        st.caption(f"Qty: {qty}")
                        if st.button("Use Item", key=f"use_item_btn_{idx}", use_container_width=True):
                            res_msg = database.use_pet_item(item)
                            st.success(res_msg)
                            st.rerun()


    # ==========================================
    # TAB 2: AC VALHALLA CONSTELLATION SKILL TREE
    # ==========================================
    with tab_tree:
        st.subheader("🌌 Constellation Mastery Skill Web")
        st.caption("AC Valhalla style skill tree node map. Connect skills across Intellect, Mutation, and Discipline constellations!")
        
        st.info(f"⭐ **Available Skill Points:** `{skill_points} SP` — Click any unlocked or available node below to inspect and upgrade!")

        # All Skill Definitions
        all_skills = {
            # Core Center Node
            "spore_core": {"title": "Spore Core", "branch": "Core", "cost": 0, "desc": "The primordial genetic core of Sparky.", "req": None, "icon": "💥"},
            
            # Intellect Constellation (Cyan)
            "int_1": {"title": "Quick Mind", "branch": "Intellect 🧠", "cost": 1, "desc": "+10% Bonus XP on Math & Logic Quests", "req": "spore_core", "icon": "🧠"},
            "int_2": {"title": "Memory Overclock", "branch": "Intellect 🧠", "cost": 2, "desc": "+5 Permanent Max Stamina Boost", "req": "int_1", "icon": "💾"},
            "int_3": {"title": "Socratic Scholar", "branch": "Intellect 🧠", "cost": 3, "desc": "Unlocks Floki's Socratic Hints in Trivia Battles", "req": "int_2", "icon": "📜"},

            # Mutation & Creativity Constellation (Purple)
            "crt_1": {"title": "Cyber Artisan", "branch": "Mutation 🎨", "cost": 1, "desc": "+10% Bonus XP on STEM & Art Quests", "req": "spore_core", "icon": "🎨"},
            "crt_2": {"title": "Neon Chameleon Aura", "branch": "Mutation 🎨", "cost": 2, "desc": "Unlocks Neon Chameleon Aura visual effects on Sparky's card", "req": "crt_1", "icon": "✨"},
            "crt_3": {"title": "Innovation Surge", "branch": "Mutation 🎨", "cost": 3, "desc": "Bonus Loot Drop chance in Exploration Dungeons", "req": "crt_2", "icon": "🧬"},

            # Discipline & Strength Constellation (Amber)
            "str_1": {"title": "Titan Discipline", "branch": "Discipline 💪", "cost": 1, "desc": "+10% Bonus XP on Daily Quests", "req": "spore_core", "icon": "💪"},
            "str_2": {"title": "Boss Slayer", "branch": "Discipline 💪", "cost": 2, "desc": "+50% Double XP Bonus on Daily Boss Fights", "req": "str_1", "icon": "⚔️"},
            "str_3": {"title": "Streak Shield", "branch": "Discipline 💪", "cost": 3, "desc": "Protects Daily Streak from resetting once per week", "req": "str_2", "icon": "🛡️"},
        }

        # Check unlocked state per skill
        int1_u = "int_1" in unlocked_skills
        int2_u = "int_2" in unlocked_skills
        int3_u = "int_3" in unlocked_skills
        
        crt1_u = "crt_1" in unlocked_skills
        crt2_u = "crt_2" in unlocked_skills
        crt3_u = "crt_3" in unlocked_skills
        
        str1_u = "str_1" in unlocked_skills
        str2_u = "str_2" in unlocked_skills
        str3_u = "str_3" in unlocked_skills

        # Dynamic SVG HTML
        svg_nodes_html = f"""
        <div style="background: radial-gradient(circle at center, #181825 0%, #09090e 100%); border-radius: 15px; border: 2px solid #313244; padding: 15px; text-align: center; font-family: sans-serif;">
            <svg viewBox="0 0 800 400" style="width: 100%; height: 390px;">
                <defs>
                    <filter id="glow-cyan" x="-20%" y="-20%" width="140%" height="140%">
                        <feGaussianBlur stdDeviation="5" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over" />
                    </filter>
                    <filter id="glow-purple" x="-20%" y="-20%" width="140%" height="140%">
                        <feGaussianBlur stdDeviation="5" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over" />
                    </filter>
                    <filter id="glow-amber" x="-20%" y="-20%" width="140%" height="140%">
                        <feGaussianBlur stdDeviation="5" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over" />
                    </filter>
                </defs>
                
                <!-- Background Constellation Stars -->
                <circle cx="100" cy="80" r="1.5" fill="#a6adc8" opacity="0.6" />
                <circle cx="250" cy="50" r="1.5" fill="#00f0ff" opacity="0.8" />
                <circle cx="600" cy="60" r="2" fill="#c084fc" opacity="0.5" />
                <circle cx="720" cy="180" r="1.5" fill="#fbbf24" opacity="0.7" />
                <circle cx="150" cy="350" r="1" fill="#ffffff" opacity="0.4" />
                <circle cx="680" cy="360" r="2" fill="#00f0ff" opacity="0.6" />
                
                <!-- CONSTELLATION CONNECTOR LINES -->
                <!-- Intellect Lines (Cyan) -->
                <line x1="400" y1="200" x2="260" y2="110" stroke="{ '#00f0ff' if int1_u else '#334155' }" stroke-width="{ '4' if int1_u else '2' }" { 'filter="url(#glow-cyan)"' if int1_u else 'stroke-dasharray="4,4"' } opacity="0.9" />
                <line x1="260" y1="110" x2="150" y2="80" stroke="{ '#00f0ff' if int2_u else '#334155' }" stroke-width="{ '4' if int2_u else '2' }" { 'filter="url(#glow-cyan)"' if int2_u else 'stroke-dasharray="4,4"' } opacity="0.8" />
                <line x1="150" y1="80" x2="60" y2="60" stroke="{ '#00f0ff' if int3_u else '#334155' }" stroke-width="{ '4' if int3_u else '2' }" { 'filter="url(#glow-cyan)"' if int3_u else 'stroke-dasharray="4,4"' } opacity="0.7" />
                
                <!-- Mutation Lines (Purple) -->
                <line x1="400" y1="200" x2="540" y2="110" stroke="{ '#c084fc' if crt1_u else '#334155' }" stroke-width="{ '4' if crt1_u else '2' }" { 'filter="url(#glow-purple)"' if crt1_u else 'stroke-dasharray="4,4"' } opacity="0.9" />
                <line x1="540" y1="110" x2="650" y2="80" stroke="{ '#c084fc' if crt2_u else '#334155' }" stroke-width="{ '4' if crt2_u else '2' }" { 'filter="url(#glow-purple)"' if crt2_u else 'stroke-dasharray="4,4"' } opacity="0.8" />
                <line x1="650" y1="80" x2="740" y2="60" stroke="{ '#c084fc' if crt3_u else '#334155' }" stroke-width="{ '4' if crt3_u else '2' }" { 'filter="url(#glow-purple)"' if crt3_u else 'stroke-dasharray="4,4"' } opacity="0.7" />
                
                <!-- Discipline Lines (Amber) -->
                <line x1="400" y1="200" x2="400" y2="300" stroke="{ '#fbbf24' if str1_u else '#334155' }" stroke-width="{ '4' if str1_u else '2' }" { 'filter="url(#glow-amber)"' if str1_u else 'stroke-dasharray="4,4"' } opacity="0.9" />
                <line x1="400" y1="300" x2="280" y2="360" stroke="{ '#fbbf24' if str2_u else '#334155' }" stroke-width="{ '4' if str2_u else '2' }" { 'filter="url(#glow-amber)"' if str2_u else 'stroke-dasharray="4,4"' } opacity="0.8" />
                <line x1="400" y1="300" x2="520" y2="360" stroke="{ '#fbbf24' if str3_u else '#334155' }" stroke-width="{ '4' if str3_u else '2' }" { 'filter="url(#glow-amber)"' if str3_u else 'stroke-dasharray="4,4"' } opacity="0.8" />

                <!-- CORE NODE -->
                <g transform="translate(400, 200)">
                    <circle r="26" fill="#181825" stroke="#f59e0b" stroke-width="4" filter="url(#glow-amber)" />
                    <text text-anchor="middle" dy="7" font-size="22">💥</text>
                    <text text-anchor="middle" dy="42" fill="#fbbf24" font-weight="bold" font-size="12">SPORE CORE</text>
                </g>

                <!-- INTELLECT NODES -->
                <g transform="translate(260, 110)">
                    <circle r="20" fill="{ '#0284c7' if int1_u else '#0f172a' }" stroke="#00f0ff" stroke-width="{ '4' if int1_u else '2' }" { 'filter="url(#glow-cyan)"' if int1_u else '' } />
                    <text text-anchor="middle" dy="6" font-size="16">🧠</text>
                    <text text-anchor="middle" dy="34" fill="{ '#00f0ff' if int1_u else '#94a3b8' }" font-weight="bold" font-size="11">Quick Mind</text>
                </g>
                <g transform="translate(150, 80)">
                    <circle r="18" fill="{ '#0284c7' if int2_u else '#0f172a' }" stroke="{ '#00f0ff' if int2_u else '#334155' }" stroke-width="{ '3' if int2_u else '1.5' }" { 'filter="url(#glow-cyan)"' if int2_u else '' } />
                    <text text-anchor="middle" dy="5" font-size="14">💾</text>
                    <text text-anchor="middle" dy="32" fill="{ '#38bdf8' if int2_u else '#64748b' }" font-size="10">Overclock</text>
                </g>
                <g transform="translate(60, 60)">
                    <circle r="16" fill="{ '#0284c7' if int3_u else '#0f172a' }" stroke="{ '#00f0ff' if int3_u else '#334155' }" stroke-width="{ '3' if int3_u else '1.5' }" { 'filter="url(#glow-cyan)"' if int3_u else '' } />
                    <text text-anchor="middle" dy="5" font-size="12">📜</text>
                    <text text-anchor="middle" dy="30" fill="{ '#38bdf8' if int3_u else '#64748b' }" font-size="10">Scholar</text>
                </g>

                <!-- MUTATION NODES -->
                <g transform="translate(540, 110)">
                    <circle r="20" fill="{ '#7e22ce' if crt1_u else '#1e102a' }" stroke="#c084fc" stroke-width="{ '4' if crt1_u else '2' }" { 'filter="url(#glow-purple)"' if crt1_u else '' } />
                    <text text-anchor="middle" dy="6" font-size="16">🎨</text>
                    <text text-anchor="middle" dy="34" fill="{ '#c084fc' if crt1_u else '#94a3b8' }" font-weight="bold" font-size="11">Artisan</text>
                </g>
                <g transform="translate(650, 80)">
                    <circle r="18" fill="{ '#7e22ce' if crt2_u else '#1e102a' }" stroke="{ '#c084fc' if crt2_u else '#334155' }" stroke-width="{ '3' if crt2_u else '1.5' }" { 'filter="url(#glow-purple)"' if crt2_u else '' } />
                    <text text-anchor="middle" dy="5" font-size="14">✨</text>
                    <text text-anchor="middle" dy="32" fill="{ '#e879f9' if crt2_u else '#64748b' }" font-size="10">Chameleon</text>
                </g>
                <g transform="translate(740, 60)">
                    <circle r="16" fill="{ '#7e22ce' if crt3_u else '#1e102a' }" stroke="{ '#c084fc' if crt3_u else '#334155' }" stroke-width="{ '3' if crt3_u else '1.5' }" { 'filter="url(#glow-purple)"' if crt3_u else '' } />
                    <text text-anchor="middle" dy="5" font-size="12">🧬</text>
                    <text text-anchor="middle" dy="30" fill="{ '#e879f9' if crt3_u else '#64748b' }" font-size="10">Surge</text>
                </g>

                <!-- DISCIPLINE NODES -->
                <g transform="translate(400, 300)">
                    <circle r="20" fill="{ '#b45309' if str1_u else '#2b1104' }" stroke="#fbbf24" stroke-width="{ '4' if str1_u else '2' }" { 'filter="url(#glow-amber)"' if str1_u else '' } />
                    <text text-anchor="middle" dy="6" font-size="16">💪</text>
                    <text text-anchor="middle" dy="34" fill="{ '#fbbf24' if str1_u else '#94a3b8' }" font-weight="bold" font-size="11">Titan Discipline</text>
                </g>
                <g transform="translate(280, 360)">
                    <circle r="18" fill="{ '#b45309' if str2_u else '#2b1104' }" stroke="{ '#fbbf24' if str2_u else '#334155' }" stroke-width="{ '3' if str2_u else '1.5' }" { 'filter="url(#glow-amber)"' if str2_u else '' } />
                    <text text-anchor="middle" dy="5" font-size="14">⚔️</text>
                    <text text-anchor="middle" dy="32" fill="{ '#fde047' if str2_u else '#64748b' }" font-size="10">Boss Slayer</text>
                </g>
                <g transform="translate(520, 360)">
                    <circle r="18" fill="{ '#b45309' if str3_u else '#2b1104' }" stroke="{ '#fbbf24' if str3_u else '#334155' }" stroke-width="{ '3' if str3_u else '1.5' }" { 'filter="url(#glow-amber)"' if str3_u else '' } />
                    <text text-anchor="middle" dy="5" font-size="14">🛡️</text>
                    <text text-anchor="middle" dy="32" fill="{ '#fde047' if str3_u else '#64748b' }" font-size="10">Streak Shield</text>
                </g>
            </svg>
        </div>
        """
        components.html(svg_nodes_html, height=440)
        st.divider()

        # --- INTERACTIVE CONSTELLATION NODE MAP (3 BRANCH CARDS) ---
        st.markdown("### ⚡ Interactive Skill Nodes (Select & Upgrade)")
        
        branch_groups = {
            "Intellect Constellation 🧠": ["int_1", "int_2", "int_3"],
            "Mutation Constellation 🎨": ["crt_1", "crt_2", "crt_3"],
            "Discipline Constellation 💪": ["str_1", "str_2", "str_3"]
        }
        
        node_cols = st.columns(3)
        for bg_idx, (b_name, n_ids) in enumerate(branch_groups.items()):
            with node_cols[bg_idx]:
                st.markdown(f"#### {b_name}")
                for nid in n_ids:
                    n_info = all_skills[nid]
                    n_title = n_info["title"]
                    n_cost = n_info["cost"]
                    n_desc = n_info["desc"]
                    n_req = n_info["req"]
                    n_icon = n_info["icon"]
                    
                    is_u = (nid in unlocked_skills)
                    req_ok = (n_req == "spore_core" or n_req in unlocked_skills)
                    
                    with st.container(border=True):
                        if is_u:
                            st.markdown(f"🟢 **{n_icon} {n_title}** *(Unlocked)*")
                            st.caption(n_desc)
                            st.success("✓ Active Perk")
                        elif req_ok:
                            st.markdown(f"✨ **{n_icon} {n_title}** (Cost: {n_cost} SP)")
                            st.caption(n_desc)
                            if skill_points >= n_cost:
                                if st.button(f"🚀 Unlock Node ({n_cost} SP)", key=f"direct_unlock_{nid}", use_container_width=True):
                                    ok, msg = database.unlock_pet_skill(nid, n_cost, pet_id=pet_id)
                                    if ok:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            else:
                                st.caption(f"⚠️ Need {n_cost - skill_points} more SP")
                        else:
                            st.markdown(f"🔒 **{n_icon} {n_title}** *(Locked)*")
                            st.caption(n_desc)
                            if n_req in all_skills:
                                st.caption(f"Requires: {all_skills[n_req]['title']}")


    # ==========================================
    # TAB 3: TRIVIA BATTLE ARENA
    # ==========================================
    with tab_trivia:
        st.subheader("⚔️ Knowledge Guardian Trivia Arena")
        st.write("Battle wild Knowledge Guardians by answering trivia challenges correctly. Build combo streaks for multiplied XP!")
        
        if "trivia_state" not in st.session_state:
            st.session_state.trivia_state = None
            
        if st.session_state.trivia_state is None:
            col_g1, col_g2 = st.columns([0.7, 0.3])
            with col_g1:
                guardian_choice = st.selectbox(
                    "Choose Knowledge Guardian:",
                    ["🤖 Quantum Sphinx (Math & Logic)", "🐉 Cyber Dragon (Science & STEM)", "🗿 Logic Golem (History & Humanities)"]
                )
            with col_g2:
                st.write("")
                st.write("")
                if st.button("⚔️ Challenge Guardian! (1 Energy)", use_container_width=True):
                    if stamina < 1:
                        st.error("Sparky needs at least 1 Energy (Stamina) to battle! Feed Sparky to restore energy.")
                    else:
                        database.deduct_pet_stamina(pet_id, 1)
                        category = "Math" if "Sphinx" in guardian_choice else ("Science" if "Dragon" in guardian_choice else "Social Studies")
                        zone_key = "Canyon" if "Science" in category else ("Forge" if "Social" in category else "Ruins")
                        
                        questions = []
                        for _ in range(3):
                            try:
                                q_data = generate_quest_question(category, pet_level)
                                if not isinstance(q_data, dict) or "question" not in q_data or "choices" not in q_data:
                                    q_data = random.choice(config.FALLBACK_QUESTIONS[zone_key])
                            except Exception:
                                q_data = random.choice(config.FALLBACK_QUESTIONS[zone_key])
                            questions.append(q_data)
                            
                        st.session_state.trivia_state = {
                            "guardian": guardian_choice,
                            "guardian_hp": 3,
                            "sparky_hp": 3,
                            "current_round": 0,
                            "combo_multiplier": 1.0,
                            "questions": questions,
                            "hint": None
                        }
                        st.rerun()
        else:
            tstate = st.session_state.trivia_state
            guardian_name = tstate["guardian"]
            round_idx = tstate["current_round"]
            
            if tstate["guardian_hp"] <= 0:
                total_xp = int(40 * tstate["combo_multiplier"])
                database.record_trivia_victory(pet_id, xp_won=total_xp, sp_won=1)
                st.balloons()
                st.success(f"🏆 VICTORY! Sparky defeated **{guardian_name}**! Earned +{total_xp} XP and +1 Skill Point!")
                if st.button("Collect Loot & Finish Battle", use_container_width=True):
                    st.session_state.trivia_state = None
                    st.rerun()
            elif tstate["sparky_hp"] <= 0 or round_idx >= len(tstate["questions"]):
                st.error(f"💥 Battle ended! {guardian_name} defended its realm. Try again!")
                if st.button("Return to Arena Hub", use_container_width=True):
                    st.session_state.trivia_state = None
                    st.rerun()
            else:
                st.markdown(f"#### 🤺 Battle in Progress: Sparky vs. {guardian_name}")
                col_hp1, col_hp2, col_combo = st.columns([0.4, 0.4, 0.2])
                with col_hp1:
                    st.write(f"🐾 **Sparky HP:** {'❤️' * tstate['sparky_hp']}")
                with col_hp2:
                    st.write(f"👾 **Guardian HP:** {'💜' * tstate['guardian_hp']}")
                with col_combo:
                    st.metric("Combo Streak", f"{tstate['combo_multiplier']}x")
                    
                st.divider()
                q = tstate["questions"][round_idx]
                st.markdown(f"**Question {round_idx + 1} of 3:**")
                st.subheader(f"💬 {q['question']}")
                
                if tstate["hint"]:
                    st.info(f"💡 **Floki's Hint:** {tstate['hint']}")
                    
                choices = q["choices"]
                cols_ans = st.columns(len(choices))
                user_choice = None
                
                for c_i, choice in enumerate(choices):
                    with cols_ans[c_i]:
                        if st.button(f"Option {c_i + 1}: {choice}", key=f"trivia_ans_{round_idx}_{c_i}", use_container_width=True):
                            user_choice = choice
                            
                if user_choice is not None:
                    if user_choice.strip().lower() == q["answer"].strip().lower():
                        tstate["guardian_hp"] -= 1
                        tstate["combo_multiplier"] += 0.5
                        tstate["current_round"] += 1
                        tstate["hint"] = None
                        st.toast("🎯 Direct Hit! Critical damage dealt!")
                        st.rerun()
                    else:
                        tstate["sparky_hp"] -= 1
                        tstate["combo_multiplier"] = 1.0
                        tstate["hint"] = q.get("hint", "Think carefully!")
                        st.toast("💥 Sparky took damage!")
                        st.rerun()
                        
                if st.button("🏳️ Retreat from Battle"):
                    st.session_state.trivia_state = None
                    st.rerun()


    # ==========================================
    # TAB 4: DUNGEON EXPEDITION
    # ==========================================
    with tab_dungeon:
        st.subheader("🗺️ Zone Crawler Dungeon Expedition")
        st.write("Explore mystery dungeon zones, solve challenge rooms, defeat zone guardians, and complete your **Zone Crawler** side quest!")
        
        col_dz1, col_dz2 = st.columns([0.65, 0.35])
        with col_dz1:
            dungeon_zone = st.selectbox(
                "Select Expedition Zone:",
                [
                    "📐 The Algebra Ruins (INT Focus)",
                    "🎨 Maker's Canyon (CRT Focus)",
                    "🌋 Titan's Forge (STR Focus)"
                ]
            )
        with col_dz2:
            st.write("")
            st.write("")
            if "dungeon_state" not in st.session_state:
                st.session_state.dungeon_state = None
                
            if st.session_state.dungeon_state is None:
                if st.button("🚀 Enter Dungeon Room (1 Energy)", use_container_width=True):
                    if stamina < 1:
                        st.error("Sparky needs at least 1 Energy (Stamina) to enter the dungeon! Feed Sparky in the care tab.")
                    else:
                        database.deduct_pet_stamina(pet_id, 1)
                        zone_cat = "Math" if "Algebra" in dungeon_zone else ("Science" if "Maker" in dungeon_zone else "Social Studies")
                        zone_key = "Canyon" if "Science" in zone_cat else ("Forge" if "Social" in zone_cat else "Ruins")
                        try:
                            q_data = generate_quest_question(zone_cat, pet_level)
                            if not isinstance(q_data, dict) or "question" not in q_data:
                                q_data = random.choice(config.FALLBACK_QUESTIONS[zone_key])
                        except Exception:
                            q_data = random.choice(config.FALLBACK_QUESTIONS[zone_key])
                        
                        st.session_state.dungeon_state = {
                            "zone": dungeon_zone,
                            "room": 1,
                            "question": q_data,
                            "completed": False
                        }
                        st.rerun()
                        
        if st.session_state.dungeon_state:
            dstate = st.session_state.dungeon_state
            r_num = dstate["room"]
            q_info = dstate["question"]
            
            st.divider()
            col_rm1, col_rm2, col_rm3 = st.columns(3)
            with col_rm1:
                st.markdown(f"🚪 **Room 1: Entrance** {'✅' if r_num > 1 else ('📍 Active' if r_num == 1 else '🔒')}")
            with col_rm2:
                st.markdown(f"🧬 **Room 2: Relic Chamber** {'✅' if r_num > 2 else ('📍 Active' if r_num == 2 else '🔒')}")
            with col_rm3:
                st.markdown(f"👑 **Room 3: Boss Lair** {'✅' if dstate['completed'] else ('📍 Active' if r_num == 3 else '🔒')}")
                
            with st.container(border=True):
                st.markdown(f"### 📍 Room {r_num} Challenge — {dstate['zone']}")
                st.subheader(f"💬 {q_info['question']}")
                
                choices = q_info.get("choices", [])
                c_cols = st.columns(len(choices))
                selected_ans = None
                for ci, ch in enumerate(choices):
                    with c_cols[ci]:
                        if st.button(f"{ch}", key=f"dungeon_ans_{r_num}_{ci}", use_container_width=True):
                            selected_ans = ch
                            
                if selected_ans:
                    if selected_ans.strip().lower() == q_info.get("answer", "").strip().lower():
                        msg, earned_xp = database.complete_quest_room(pet_id, r_num, dstate['zone'])
                        st.toast(f"🎉 Room cleared! Earned +{earned_xp} XP and {msg}!")
                        
                        if r_num < 3:
                            zone_cat = "Math" if "Algebra" in dstate['zone'] else ("Science" if "Maker" in dstate['zone'] else "Social Studies")
                            zone_key = "Canyon" if "Science" in zone_cat else ("Forge" if "Social" in zone_cat else "Ruins")
                            try:
                                next_q = generate_quest_question(zone_cat, pet_level)
                                if not isinstance(next_q, dict) or "question" not in next_q:
                                    next_q = random.choice(config.FALLBACK_QUESTIONS[zone_key])
                            except Exception:
                                next_q = random.choice(config.FALLBACK_QUESTIONS[zone_key])
                                
                            st.session_state.dungeon_state["room"] += 1
                            st.session_state.dungeon_state["question"] = next_q
                            st.rerun()
                        else:
                            st.session_state.dungeon_state["completed"] = True
                            st.balloons()
                            st.success("🏆 EXPEDITION COMPLETE! You cleared all 3 rooms and completed the Zone Crawler quest!")
                            if st.button("Collect Dungeon Treasure", use_container_width=True):
                                st.session_state.dungeon_state = None
                                st.rerun()
                    else:
                        st.error("❌ Incorrect answer! The dungeon trap triggered. Try again!")
                        
            if st.button("🏳️ Leave Dungeon"):
                st.session_state.dungeon_state = None
                st.rerun()


    # ==========================================
    # TAB 5: SIDE QUESTS BOARD
    # ==========================================
    with tab_sidequests:
        st.subheader("📜 Daily & Weekly Side Quests Board")
        st.write("Complete special side challenges to earn extra XP, Skill Points, and rare items!")
        
        sq_list = database.get_side_quests()
        if not sq_list:
            st.info("No side quests available right now.")
        else:
            for sq in sq_list:
                sq_id, sq_title, sq_desc, sq_cat, sq_rxp, sq_rsp, sq_tgt, sq_cur, sq_claimed = sq
                pct = min(sq_cur / sq_tgt, 1.0) if sq_tgt > 0 else 0.0
                is_ready = (sq_cur >= sq_tgt and sq_claimed == 0)
                
                with st.container(border=True):
                    col_sq1, col_sq2 = st.columns([0.7, 0.3])
                    with col_sq1:
                        st.markdown(f"#### {sq_title}")
                        st.write(sq_desc)
                        st.progress(pct, text=f"Progress: {sq_cur} / {sq_tgt}")
                        
                        # Actionable navigation hints
                        if "Zone Crawler" in sq_title:
                            st.caption("💡 **How to complete:** Open the **🗺️ Dungeon Expedition** tab above and clear 1 room!")
                        elif "Trivia Master" in sq_title:
                            st.caption("💡 **How to complete:** Open the **⚔️ Trivia Battle Arena** tab above and defeat 2 Guardians!")
                        elif "Daily Discipline" in sq_title:
                            st.caption("💡 **How to complete:** Finish 3 main daily quests on the **Daily Quests** page!")
                        elif "XP Collector" in sq_title:
                            st.caption("💡 **How to complete:** Earn XP across any lessons, trivia, or dungeon rooms!")
                            
                    with col_sq2:
                        st.markdown(f"**Loot Reward:**  \n💎 +{sq_rxp} XP  \n⭐ +{sq_rsp} SP")
                        if sq_claimed == 1:
                            st.success("✅ Claimed")
                        elif is_ready:
                            if st.button(f"🎁 Claim Reward", key=f"claim_sq_btn_{sq_id}", use_container_width=True):
                                ok, msg = database.claim_side_quest_reward(sq_id, pet_id)
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        else:
                            st.caption("🔒 In Progress")
