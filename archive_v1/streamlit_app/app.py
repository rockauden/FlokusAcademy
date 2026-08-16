# ==========================================
# FLOKUS ACADEMY — MAIN APPLICATION ROUTER
# Slim multi-page router using st.navigation().
# All page logic lives in pages/student/ and pages/admin/.
# ==========================================

import streamlit as st
import database
from ui.css import inject_css
from ui.auth import render_login_sidebar, is_admin

# ------------------------------------------
# INITIALIZATION
# ------------------------------------------

# Page configuration (must be first Streamlit command)
st.set_page_config(page_title="Flokus Academy", layout="wide")

# Initialize/verify database structure
database.init_db()

# Inject premium dark-theme CSS
inject_css()

# ------------------------------------------
# SESSION STATE DEFAULTS
# ------------------------------------------

if 'show_balloons' not in st.session_state:
    st.session_state.show_balloons = False

if 'active_role' not in st.session_state:
    st.session_state.active_role = "student"

# ------------------------------------------
# AUTHENTICATION & ROLE SELECTION
# ------------------------------------------

# Admin authentication (only when admin is selected)
admin_authenticated = False
if st.session_state.active_role == "admin":
    st.sidebar.markdown("""
    <div style='padding: 8px 0 4px;'>
        <div style='font-size:13px; text-transform:uppercase; 
            letter-spacing:1.5px; color:#f6ad55; font-weight:700;'>
            ⚙️ ADMIN MODE
        </div>
        <div style='font-size:11px; color:#8c9bb4; margin-top:2px;'>
            Full Curriculum Control Center
        </div>
    </div>
    """, unsafe_allow_html=True)
    admin_authenticated = render_login_sidebar()
else:
    # Force a student-specific theme class (CSS will use this if needed)
    st.markdown('<meta name="theme" content="student">', unsafe_allow_html=True)

# ------------------------------------------
# HELPER PAGES
# ------------------------------------------

def _render_lock_screen():
    """Displays the admin lock screen when not authenticated."""
    st.title("🔒 Admin Control Center")
    st.info("Please enter the correct passcode in the sidebar to access Dad's Admin Dashboard.")

# ------------------------------------------
# PAGE DEFINITIONS
# ------------------------------------------

# Student pages — always available
student_pages = [
    st.Page("pages/student/daily_quests.py", title="Daily Quests", icon="📋"),
    st.Page("pages/student/school_calendar.py", title="School Calendar", icon="📅"),
    st.Page("pages/student/creator_block.py", title="Creator Block", icon="🛠️"),
    st.Page("pages/student/ask_floki.py", title="Ask Floki", icon="💬"),
]

# Admin pages — only visible when authenticated
admin_manage_pages = [
    st.Page("pages/admin/task_manager.py", title="Task Manager", icon="📝"),
    st.Page("pages/admin/calendar_manager.py", title="Event Calendar", icon="📅"),
    st.Page("pages/admin/project_manager.py", title="Creator Projects", icon="🛠️"),
]

admin_monitor_pages = [
    st.Page("pages/admin/portfolio.py", title="Portfolio", icon="🗂️"),
    st.Page("pages/admin/analytics.py", title="Analytics", icon="📊"),
]

admin_ops_pages = [
    st.Page("pages/admin/finances.py", title="UFA Finances", icon="💰"),
    st.Page("pages/admin/settings.py", title="Settings", icon="⚙️"),
]

# ------------------------------------------
# NAVIGATION ASSEMBLY
# ------------------------------------------

if st.session_state.active_role == "student":
    # Student-only navigation
    nav = st.navigation({
        "🎓 Sonny's Hub": student_pages,
    })
elif admin_authenticated:
    # Full admin navigation with grouped sections
    nav = st.navigation({
        "📝 Manage": admin_manage_pages,
        "📊 Monitor": admin_monitor_pages,
        "💼 Operations": admin_ops_pages,
    })
else:
    # Admin selected but not authenticated — show lock screen
    nav = st.navigation([
        st.Page(_render_lock_screen, title="Admin Login", icon="🔒"),
    ])

nav.run()

if st.session_state.active_role == "student":
    st.sidebar.write("")
    st.sidebar.write("")
    if st.sidebar.button("⚙️", help="Admin Access", key="admin_access_btn"):
        st.session_state.active_role = "admin"
        st.rerun()