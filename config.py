# ==========================================
# FLOKUS ACADEMY CONFIGURATION
# ==========================================

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

FALLBACK_QUESTIONS = {
    "Ruins": [
        {"question": "What is 3/4 of 24?", "choices": ["12", "18", "16"], "answer": "18", "hint": "Multiply 24 by 3, then divide by 4."},
        {"question": "Solve: 5x + 3 = 18. What is x?", "choices": ["3", "4", "5"], "answer": "3", "hint": "Subtract 3 from 18, then divide by 5."},
        {"question": "Which fraction is equivalent to 0.4?", "choices": ["1/4", "2/5", "4/5"], "answer": "2/5", "hint": "Remember that 0.4 is 4 tenths, which can be simplified."},
        {"question": "What is the value of 5 + 3 * 2?", "choices": ["16", "11", "13"], "answer": "11", "hint": "Follow the order of operations (PEMDAS): do multiplication first!"}
    ],
    "Canyon": [
        {"question": "Which state of matter is water vapor?", "choices": ["Solid", "Liquid", "Gas"], "answer": "Gas", "hint": "Think about steam rising from a kettle."},
        {"question": "How many vertices does a cube have?", "choices": ["6", "8", "12"], "answer": "8", "hint": "Count the corners of a 3D box."},
        {"question": "What kind of simple machine is a slide on a playground?", "choices": ["Lever", "Pulley", "Inclined Plane"], "answer": "Inclined Plane", "hint": "It is a flat surface tilted at an angle."},
        {"question": "Which of these is a primary producer in an ecosystem?", "choices": ["Grasshopper", "Green Plant", "Frog"], "answer": "Green Plant", "hint": "Producers make their own food using sunlight."}
    ],
    "Forge": [
        {"question": "What is the force that pulls objects toward Earth?", "choices": ["Friction", "Gravity", "Magnetism"], "answer": "Gravity", "hint": "It is what makes an apple fall from a tree."},
        {"question": "If a rectangle has length 8 and width 5, what is its perimeter?", "choices": ["40", "13", "26"], "answer": "26", "hint": "Add all four sides: 8 + 5 + 8 + 5."},
        {"question": "Which gas do plants absorb from the atmosphere for photosynthesis?", "choices": ["Oxygen", "Carbon Dioxide", "Nitrogen"], "answer": "Carbon Dioxide", "hint": "It is the gas humans breathe out."},
        {"question": "What is the freezing point of water in Celsius?", "choices": ["0 degrees", "32 degrees", "100 degrees"], "answer": "0 degrees", "hint": "Celsius is based on the properties of water: 0 is freezing, 100 is boiling."}
    ]
}
