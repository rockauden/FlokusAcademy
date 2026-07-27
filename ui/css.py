# ==========================================
# FLOKUS ACADEMY — CSS INJECTION MODULE
# Extracted from monolithic app.py for clean separation.
# ==========================================

import streamlit as st


def inject_css():
    """Injects the premium gamified dark-theme CSS into the Streamlit app."""
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

        /* Event Urgency & Calendar Styling */
        .event-card {
            background: linear-gradient(135deg, #161b2e 0%, #0f1220 100%);
            border: 1px solid #283254;
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 12px;
        }
        .event-card.urgent {
            border-left: 5px solid #f56565 !important;
            box-shadow: 0 0 10px rgba(245, 101, 101, 0.2);
        }
        .event-card.important {
            border-left: 5px solid #ed8936 !important;
            box-shadow: 0 0 10px rgba(237, 137, 54, 0.2);
        }
        .event-card.normal {
            border-left: 5px solid #4299e1 !important;
        }
        .badge-urgent {
            background-color: #742a2a;
            color: #feb2b2;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 700;
        }
        .badge-important {
            background-color: #7b341e;
            color: #fbd38d;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 700;
        }
        .badge-normal {
            background-color: #2a4365;
            color: #90cdf4;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 700;
        }
        .countdown-hero {
            background: linear-gradient(135deg, #1e2640 0%, #11162b 100%);
            border: 2px solid #63b3ed;
            border-radius: 14px;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 0 20px rgba(99, 179, 237, 0.25);
        }
        .countdown-number {
            font-size: 44px;
            font-weight: 800;
            color: #63b3ed;
            line-height: 1.1;
        }
    </style>
    """, unsafe_allow_html=True)
