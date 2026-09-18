import streamlit as st
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def require_auth():
    """
    Checks if a user is logged in. If not, displays the login form and stops execution.
    Should be called at the top of every Streamlit page.
    """
    if "user" not in st.session_state:
        # Prototype Mode: Auto-login as a mock admin user
        st.session_state["user"] = {
            "id": 1,
            "email": "prototype@infraguard.ai",
            "full_name": "Prototype User",
            "authority_type": "Admin",
            "state_region": "All Regions",
            "organization": "InfraGuard-AI",
            "role_id": 1
        }


def show_user_profile():
    """Displays user profile in the sidebar with a logout button."""
    if "user" in st.session_state:
        user = st.session_state["user"]
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**👤 {user['full_name']}**")
        st.sidebar.caption(f"Role: {user['authority_type']}")
        if user.get('state_region'):
            st.sidebar.caption(f"Region: {user['state_region']}")
        if user.get('organization'):
            st.sidebar.caption(f"Org: {user['organization']}")
        
        if st.sidebar.button("Logout"):
            del st.session_state["user"]
            st.rerun()
