# ==========================================
# FLOKUS ACADEMY — ADMIN AUTHENTICATION
# Session-state based auth with logout support.
# ==========================================

import streamlit as st


def render_login_sidebar():
    """Renders the admin login input in the sidebar. Returns True if authenticated."""
    if is_admin():
        st.sidebar.success("✅ Admin Authenticated")
        if st.sidebar.button("🔓 Logout", key="admin_logout_btn"):
            logout()
            st.rerun()
        return True

    admin_pin = st.sidebar.text_input("🔑 Enter Admin Passcode:", type="password", key="admin_pin_input")
    secure_pin = st.secrets.get("admin_pin", "1234")

    if admin_pin == secure_pin and admin_pin != "":
        st.session_state["_admin_authenticated"] = True
        st.rerun()
    elif admin_pin != "":
        st.sidebar.error("❌ Incorrect Passcode!")

    return False


def is_admin():
    """Returns True if the admin is currently authenticated via session state."""
    return st.session_state.get("_admin_authenticated", False)


def logout():
    """Clears admin authentication from session state."""
    st.session_state["_admin_authenticated"] = False
