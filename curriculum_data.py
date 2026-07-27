"""
FLOKUS ACADEMY — MASTER CURRICULUM DATA (TIER 1 & TIER 2)
Comprehensive 9-Program Suite: Beast Academy, Brave Writer, Tuttle Twins, Critical Thinking Co.,
Synthesis, Chess.com, Brilliant.org, CrunchLabs, Outschool.
"""

from datetime import date, datetime, timedelta
import database

# ==============================================================================
# TIER 1: YEARLY OVERVIEW (4 QUARTERS / 36 WEEKS)
# ==============================================================================
TIER_1_OVERVIEW = {
    1: {
        "title": "Quarter 1: Foundations & Origins",
        "weeks": "Weeks 1–9",
        "math_logic": "BA 2A (Place Value, Comparing, Addition) | Brilliant: Foundational Logic & Puzzles",
        "ela": "Dart 1: Wishtree | Dart 2: The Beatryce Prophecy | Dart 3: Maya & the Robot",
        "history": "Tuttle Twins Vol 1: Ch 1–6 (Trade, Settlement, Human Rights, Empire, King's Grip)",
        "critical_thinking": "Critical Thinking: Ch 1–5 (Evidence & Claims) | Synthesis: AI Mental Models | Chess.com: Opening Principles",
        "stem_electives": "CrunchLabs: Build Box #1 & #2 (Disc Launcher / Hardware) | Outschool: Specialty Group Elective"
    },
    2: {
        "title": "Quarter 2: Revolution & Reasoning",
        "weeks": "Weeks 10–18",
        "math_logic": "BA 2B (Subtraction, Expressions, Problem Solving) | Brilliant: Interactive Algebra & Code",
        "ela": "Dart 3: Maya & the Robot (Cont.) | Dart 4: Wilderlore | Dart 5: Odder",
        "history": "Tuttle Twins Vol 1 & 2: Vol 1 Ch 7–11 & Vol 2 Ch 1–3 (Boston, War, Liberty, 13 States)",
        "critical_thinking": "Critical Thinking: Ch 6–10 (Inferences & Truth) | Synthesis: Complex Team Simulations | Chess.com: Middle Game Tactics",
        "stem_electives": "CrunchLabs: Build Box #3 & #4 (Physics & Motion) | Outschool: Live Interactive Workshop"
    },
    3: {
        "title": "Quarter 3: Nation Building & Logic",
        "weeks": "Weeks 19–27",
        "math_logic": "BA 2C (Measurement, Strategies (+&-), Odds/Evens) | Brilliant: Mathematical Thinking",
        "ela": "Dart 5: Odder (Cont.) | Dart 6: Mr. Lemoncello | Dart 7: Once Upon a Camel",
        "history": "Tuttle Twins Vol 2: Ch 4–11 (Economic Winter, Loyalists, Treaty, Bill of Rights)",
        "critical_thinking": "Critical Thinking: Ch 11–15 (Diagrams & Fallacies) | Synthesis: Decision Frameworks | Chess.com: Endgame Strategies",
        "stem_electives": "CrunchLabs: Build Box #5 & #6 (Gear Dynamics) | Outschool: Interest-Led Deep Dive"
    },
    4: {
        "title": "Quarter 4: Expansion & Synthesis",
        "weeks": "Weeks 28–36",
        "math_logic": "BA 2D (Big Numbers, Algorithms, Problem Solving) | Brilliant: Advanced Problem Solving",
        "ela": "Dart 7: Once Upon a Camel (Cont.) | Dart 8: Thirst | Dart 9: Sidekicks",
        "history": "Tuttle Twins Vol 3: Ch 1–11 (Betrayal, Expansion, Flames, Debt, Railroads, Gold)",
        "critical_thinking": "Critical Thinking: Ch 16–20 (Arguments & Decisions) | Synthesis: Capstone Problem Solving | Chess.com: Tournament Play",
        "stem_electives": "CrunchLabs: Build Box #7–9 & Year-End Expo | Outschool: Portfolio Presentation"
    }
}

# ==============================================================================
# TIER 2: STRUCTURED UNIT INCREMENTS (36-WEEK DETAILED BREAKDOWN)
# 9 Units x 4 Weeks Each
# ==============================================================================
TIER_2_UNITS = [
    # Unit 1
    {"wk": 1, "unit": "Unit 1: Trade & Place Value", "math": "BA 2A Ch 1 (Place Value) + Brilliant Logic", "ela": "Dart 1: Wishtree (Ch 1–15)", "history": "TT Vol 1 Ch 1 / Critical Ch 1–2", "strategy": "Synthesis Mental Models + CrunchLabs Box #1"},
    {"wk": 2, "unit": "Unit 1: Trade & Place Value", "math": "BA 2A Ch 1 (Expanded) + Brilliant Puzzles", "ela": "Dart 1: Wishtree (Ch 16–31)", "history": "TT Vol 1 Ch 2 / Critical Ch 3", "strategy": "Chess.com Openings + Outschool Class"},
    {"wk": 3, "unit": "Unit 1: Trade & Place Value", "math": "BA 2A Ch 2 (Comparing) + Brilliant Math", "ela": "Dart 1: Wishtree (Ch 32–51)", "history": "TT Vol 1 Ch 3 / Critical Ch 4", "strategy": "Synthesis Simulation + CrunchLabs Testing"},
    {"wk": 4, "unit": "Unit 1: Trade & Place Value", "math": "BA 2A Ch 2 (Number Line) + Brilliant Review", "ela": "Dart 1: Wishtree (Book Party)", "history": "TT Vol 1 Ch 4 / Critical Ch 5", "strategy": "Chess.com Tactics + Outschool Presentation"},

    # Unit 2
    {"wk": 5, "unit": "Unit 2: Empire & Addition", "math": "BA 2A Ch 3 (Addition) + Brilliant Logic", "ela": "Dart 2: Beatryce Prophecy (p 1–83)", "history": "TT Vol 1 Ch 5 / Critical Ch 6", "strategy": "Synthesis Models + CrunchLabs Box #2"},
    {"wk": 6, "unit": "Unit 2: Empire & Addition", "math": "BA 2A Ch 3 (Strategies) + Brilliant Algebra", "ela": "Dart 2: Beatryce Prophecy (p 84–177)", "history": "TT Vol 1 Ch 6 / Critical Ch 7", "strategy": "Chess.com Puzzles + Outschool Class"},
    {"wk": 7, "unit": "Unit 2: Empire & Addition", "math": "BA 2B Ch 4 (Subtraction) + Brilliant Patterns", "ela": "Dart 2: Beatryce Prophecy (p 178–247)", "history": "TT Vol 1 Ch 7 / Critical Ch 8", "strategy": "Synthesis Team Challenge + CrunchLabs Mod"},
    {"wk": 8, "unit": "Unit 2: Empire & Addition", "math": "BA 2B Ch 4 (Puzzles) + Brilliant Review", "ela": "Dart 2: Beatryce Prophecy (Book Party)", "history": "TT Vol 1 Ch 8 / Critical Ch 9", "strategy": "Chess.com Matches + Outschool Review"},

    # Unit 3
    {"wk": 9, "unit": "Unit 3: Revolution & Robots", "math": "BA 2B Ch 5 (Expressions) + Brilliant Math", "ela": "Dart 3: Maya & Robot (Ch 1–5)", "history": "TT Vol 1 Ch 9 / Critical Ch 10", "strategy": "Synthesis AI Simulation + CrunchLabs Box #3"},
    {"wk": 10, "unit": "Unit 3: Revolution & Robots", "math": "BA 2B Ch 5 (Evaluation) + Brilliant Logic", "ela": "Dart 3: Maya & Robot (Ch 6–11)", "history": "TT Vol 1 Ch 10 / Logic Review", "strategy": "Chess.com Middle Game + Outschool Class"},
    {"wk": 11, "unit": "Unit 3: Revolution & Robots", "math": "BA 2B Ch 6 (Problem Solving) + Brilliant STEM", "ela": "Dart 3: Maya & Robot (Ch 12–17)", "history": "TT Vol 1 Ch 11 / Critical Ch 11", "strategy": "Synthesis Strategy + CrunchLabs Build"},
    {"wk": 12, "unit": "Unit 3: Revolution & Robots", "math": "BA 2B Ch 6 (Puzzles) + Brilliant Review", "ela": "Dart 3: Maya & Robot (Book Party)", "history": "TT Vol 2 Ch 1 / Critical Ch 11", "strategy": "Chess.com Analysis + Outschool Project"},

    # Unit 4
    {"wk": 13, "unit": "Unit 4: Wilderlore & Guilds", "math": "BA 2C Ch 7 (Measurement) + Brilliant Geometry", "ela": "Dart 4: Wilderlore (Ch 1–10)", "history": "TT Vol 2 Ch 2 / Critical Ch 12", "strategy": "Synthesis Models + CrunchLabs Box #4"},
    {"wk": 14, "unit": "Unit 4: Wilderlore & Guilds", "math": "BA 2C Ch 7 (Units) + Brilliant Measurements", "ela": "Dart 4: Wilderlore (Ch 11–19)", "history": "TT Vol 2 Ch 3 / Critical Ch 12", "strategy": "Chess.com Endgames + Outschool Class"},
    {"wk": 15, "unit": "Unit 4: Wilderlore & Guilds", "math": "BA 2C Ch 8 (Strategies) + Brilliant Logic", "ela": "Dart 4: Wilderlore (Ch 20–25)", "history": "TT Vol 2 Ch 4 / Critical Ch 13", "strategy": "Synthesis Simulation + CrunchLabs Testing"},
    {"wk": 16, "unit": "Unit 4: Wilderlore & Guilds", "math": "BA 2C Ch 8 (Mental Math) + Brilliant Review", "ela": "Dart 4: Wilderlore (Book Party)", "history": "TT Vol 2 Ch 5 / Critical Ch 14", "strategy": "Chess.com Tactics + Outschool Showcase"},

    # Unit 5
    {"wk": 17, "unit": "Unit 5: Odder & Ocean Verse", "math": "BA 2C Ch 9 (Odds/Evens) + Brilliant Patterns", "ela": "Dart 5: Odder (p 1–91)", "history": "TT Vol 2 Ch 6 / Critical Ch 15", "strategy": "Synthesis AI + CrunchLabs Box #5"},
    {"wk": 18, "unit": "Unit 5: Odder & Ocean Verse", "math": "BA 2C Ch 9 (Patterns) + Brilliant Logic", "ela": "Dart 5: Odder (p 92–178)", "history": "TT Vol 2 Ch 7 / Critical Ch 15", "strategy": "Chess.com Strategy + Outschool Class"},
    {"wk": 19, "unit": "Unit 5: Odder & Ocean Verse", "math": "BA 2D Ch 10 (Big Numbers) + Brilliant Math", "ela": "Dart 5: Odder (p 179–268)", "history": "TT Vol 2 Ch 8 / Critical Ch 16", "strategy": "Synthesis Simulation + CrunchLabs Build"},
    {"wk": 20, "unit": "Unit 5: Odder & Ocean Verse", "math": "BA 2D Ch 10 (Thousands) + Brilliant Review", "ela": "Dart 5: Odder (Book Party)", "history": "TT Vol 2 Ch 9 / Critical Ch 16", "strategy": "Chess.com Matches + Outschool Review"},

    # Unit 6
    {"wk": 21, "unit": "Unit 6: Lemoncello Puzzles", "math": "BA 2D Ch 11 (Algorithms) + Brilliant CS", "ela": "Dart 6: Mr. Lemoncello (Ch 1–20)", "history": "TT Vol 2 Ch 10 / Critical Ch 17", "strategy": "Synthesis Models + CrunchLabs Box #6"},
    {"wk": 22, "unit": "Unit 6: Lemoncello Puzzles", "math": "BA 2D Ch 11 (Multi-Digit) + Brilliant Logic", "ela": "Dart 6: Mr. Lemoncello (Ch 21–36)", "history": "TT Vol 2 Ch 11 / Critical Ch 17", "strategy": "Chess.com Defense + Outschool Class"},
    {"wk": 23, "unit": "Unit 6: Lemoncello Puzzles", "math": "BA 2D Ch 12 (Problem Solving) + Brilliant Math", "ela": "Dart 6: Mr. Lemoncello (Ch 37–Epilogue)", "history": "TT Vol 3 Ch 1 / Critical Ch 18", "strategy": "Synthesis Team Sim + CrunchLabs Mod"},
    {"wk": 24, "unit": "Unit 6: Lemoncello Puzzles", "math": "BA 2D Ch 12 (Word Problems) + Brilliant Review", "ela": "Dart 6: Mr. Lemoncello (Book Party)", "history": "TT Vol 3 Ch 2 / Critical Ch 18", "strategy": "Chess.com Analysis + Outschool Project"},

    # Unit 7
    {"wk": 25, "unit": "Unit 7: Camels & Flashbacks", "math": "Beast 2 Review + Brilliant Computer Science", "ela": "Dart 7: Once Upon a Camel (Ch 1–20)", "history": "TT Vol 3 Ch 3 / Critical Ch 19", "strategy": "Synthesis AI + CrunchLabs Box #7"},
    {"wk": 26, "unit": "Unit 7: Camels & Flashbacks", "math": "BA Logic Challenges + Brilliant Puzzles", "ela": "Dart 7: Once Upon a Camel (Ch 21–40)", "history": "TT Vol 3 Ch 4 / Critical Ch 19", "strategy": "Chess.com Tournaments + Outschool Class"},
    {"wk": 27, "unit": "Unit 7: Camels & Flashbacks", "math": "Applied Math Projects + Brilliant Math", "ela": "Dart 7: Once Upon a Camel (Ch 41–70)", "history": "TT Vol 3 Ch 5 / Critical Ch 20", "strategy": "Synthesis Simulation + CrunchLabs Build"},
    {"wk": 28, "unit": "Unit 7: Camels & Flashbacks", "math": "Advanced Mental Math + Brilliant Review", "ela": "Dart 7: Once Upon a Camel (Book Party)", "history": "TT Vol 3 Ch 6 / Critical Ch 20", "strategy": "Chess.com Matches + Outschool Showcase"},

    # Unit 8
    {"wk": 29, "unit": "Unit 8: Thirst & Resource Logic", "math": "Math & Problem Solving + Brilliant Logic", "ela": "Dart 8: Thirst (Ch 1–14)", "history": "TT Vol 3 Ch 7 / Critical Practice", "strategy": "Synthesis Models + CrunchLabs Box #8"},
    {"wk": 30, "unit": "Unit 8: Thirst & Resource Logic", "math": "Competition Math Prep + Brilliant CS", "ela": "Dart 8: Thirst (Ch 15–29)", "history": "TT Vol 3 Ch 8 / Critical Claims", "strategy": "Chess.com Analysis + Outschool Class"},
    {"wk": 31, "unit": "Unit 8: Thirst & Resource Logic", "math": "Game Logic & Math + Brilliant Math", "ela": "Dart 8: Thirst (Ch 30–45)", "history": "TT Vol 3 Ch 9 / Critical Assumptions", "strategy": "Synthesis Team Sim + CrunchLabs Mod"},
    {"wk": 32, "unit": "Unit 8: Thirst & Resource Logic", "math": "Practical Estimation + Brilliant Review", "ela": "Dart 8: Thirst (Book Party)", "history": "TT Vol 3 Ch 10 / Critical Contracts", "strategy": "Chess.com Tournament + Outschool Project"},

    # Unit 9
    {"wk": 33, "unit": "Unit 9: Sidekicks & Capstones", "math": "Beast Level 2 Comprehensive Review", "ela": "Dart 9: Sidekicks (p 1–67)", "history": "TT Vol 3 Ch 11 / Critical Review", "strategy": "Synthesis Capstone + CrunchLabs Box #9"},
    {"wk": 34, "unit": "Unit 9: Sidekicks & Capstones", "math": "Year-End Math Mastery Assessment", "ela": "Dart 9: Sidekicks (p 68–140)", "history": "Tuttle Series Synthesis / Case Study", "strategy": "Chess.com Championship + Outschool Class"},
    {"wk": 35, "unit": "Unit 9: Sidekicks & Capstones", "math": "Student Individual Math Project", "ela": "Dart 9: Sidekicks (p 141–225)", "history": "History Timeline / Logic Challenge", "strategy": "Synthesis Final Sim + CrunchLabs Expo Prep"},
    {"wk": 36, "unit": "Unit 9: Sidekicks & Capstones", "math": "Annual Math Portfolio Presentation", "ela": "Dart 9: Sidekicks (Book Party)", "history": "History & Logic Annual Portfolios", "strategy": "Flokus Academy Master Expo Presentation"}
]


def generate_tier_schedule(weeks_list, start_monday):
    """
    Generates structured lessons for Sonny across selected week numbers (e.g., 1..36).
    Distributes tasks Mon-Fri across all 9 curriculum spokes.
    """
    tasks_count = 0
    # Map weeks by week number for direct lookup
    week_map = {w["wk"]: w for w in TIER_2_UNITS}

    for idx, wk_num in enumerate(sorted(weeks_list)):
        if wk_num not in week_map:
            continue
            
        wk_info = week_map[wk_num]
        current_mon = start_monday + timedelta(weeks=idx)
        
        # Parse elements
        math_text = wk_info["math"]
        ela_text = wk_info["ela"]
        hist_text = wk_info["history"]
        strat_text = wk_info["strategy"]
        
        is_book_party = "Book Party" in ela_text
        is_crunch_box = "CrunchLabs Box" in strat_text
        is_expo = "Expo" in strat_text or "Presentation" in math_text
        
        # --- MONDAY ---
        d_mon = current_mon
        database.add_task_to_db(f"Beast Academy: {math_text.split('+')[0].strip()}", "Math (Beast Academy)", "", 15, d_mon, 0, "Offline")
        database.add_task_to_db(f"Brave Writer Dart: {ela_text}", "Language Arts (Brave Writer)", "", 10, d_mon, 0, "Offline")
        database.add_task_to_db(f"Tuttle Twins History: {hist_text.split('/')[0].strip()}", "Social Studies (Tuttle Twins)", "", 10, d_mon, 0, "Offline")
        
        if "Synthesis" in strat_text:
            database.add_task_to_db(f"Synthesis AI: {strat_text.split('+')[0].strip()}", "Logic (Synthesis)", "", 15, d_mon, 0, "Online")
        elif "Chess" in strat_text:
            database.add_task_to_db(f"Chess.com: {strat_text.split('+')[0].strip()}", "Logic (Chess.com)", "", 15, d_mon, 0, "Online")
        else:
            database.add_task_to_db(f"Outschool Elective: {strat_text}", "Science (Outschool)", "", 15, d_mon, 0, "Online")
        tasks_count += 4
        
        # --- TUESDAY ---
        d_tue = current_mon + timedelta(days=1)
        brilliant_topic = math_text.split('+')[1].strip() if '+' in math_text else "Logic & Math Puzzles"
        database.add_task_to_db(f"Brilliant.org STEM: {brilliant_topic}", "Logic (Brilliant.org)", "", 15, d_tue, 0, "Online")
        database.add_task_to_db(f"Brave Writer: Creative Freewrite & Discussion", "Language Arts (Brave Writer)", "", 10, d_tue, 0, "Offline")
        
        crit_topic = hist_text.split('/')[1].strip() if '/' in hist_text else "Logic & Reasoning"
        database.add_task_to_db(f"Critical Thinking Co.: {crit_topic}", "Logic (Critical Thinking Co.)", "", 10, d_tue, 0, "Offline")
        
        if "Outschool" in strat_text:
            database.add_task_to_db(f"Outschool Live Class: {strat_text.split('+')[-1].strip()}", "Science (Outschool)", "", 15, d_tue, 0, "Online")
        else:
            database.add_task_to_db(f"Synthesis / Strategy Workshop: {strat_text}", "Logic (Synthesis)", "", 15, d_tue, 0, "Online")
        tasks_count += 4

        # --- WEDNESDAY ---
        d_wed = current_mon + timedelta(days=2)
        database.add_task_to_db(f"Beast Academy: Practice & Puzzlers ({math_text.split('+')[0].strip()})", "Math (Beast Academy)", "", 15, d_wed, 0, "Offline")
        database.add_task_to_db(f"Brave Writer Dart: Reverse Dictation & Grammar", "Language Arts (Brave Writer)", "", 10, d_wed, 0, "Offline")
        database.add_task_to_db(f"Tuttle Twins Civics & Discussion ({hist_text.split('/')[0].strip()})", "Social Studies (Tuttle Twins)", "", 10, d_wed, 0, "Offline")
        database.add_task_to_db(f"Chess.com: Tactics & Play", "Logic (Chess.com)", "", 15, d_wed, 0, "Online")
        tasks_count += 4

        # --- THURSDAY ---
        d_thu = current_mon + timedelta(days=3)
        database.add_task_to_db(f"Brilliant.org: Interactive Practice", "Logic (Brilliant.org)", "", 15, d_thu, 0, "Online")
        database.add_task_to_db(f"Brave Writer: Big Juicy Questions & Reading", "Language Arts (Brave Writer)", "", 10, d_thu, 0, "Offline")
        database.add_task_to_db(f"Critical Thinking Co.: Chapter Exercises ({crit_topic})", "Logic (Critical Thinking Co.)", "", 10, d_thu, 0, "Offline")
        
        if is_crunch_box:
            database.add_task_to_db(f"🛠️ CrunchLabs STEM Box Build Day! ({strat_text})", "Science (CrunchLabs)", "", 50, d_thu, 1, "Offline")
        else:
            database.add_task_to_db(f"Applied STEM / Project Tinkering: {strat_text}", "Science (CrunchLabs)", "", 20, d_thu, 0, "Offline")
        tasks_count += 4

        # --- FRIDAY ---
        d_fri = current_mon + timedelta(days=4)
        database.add_task_to_db(f"Beast Academy & Brilliant Weekly Math Review", "Math (Beast Academy)", "", 20, d_fri, 0, "Offline")
        
        if is_book_party:
            database.add_task_to_db(f"👑 Dart Book Party & Celebration! ({ela_text})", "Language Arts (Brave Writer)", "", 50, d_fri, 1, "Offline")
        elif is_expo:
            database.add_task_to_db(f"👑 Master Expo & Portfolio Presentation! ({strat_text})", "Science (CrunchLabs)", "", 50, d_fri, 1, "Offline")
        else:
            database.add_task_to_db(f"Brave Writer & History Review / Poetry Teatime", "Language Arts (Brave Writer)", "", 15, d_fri, 0, "Offline")
            
        database.add_task_to_db(f"Chess.com: Weekly Challenge & Matches", "Logic (Chess.com)", "", 15, d_fri, 0, "Online")
        tasks_count += 3

    return tasks_count
