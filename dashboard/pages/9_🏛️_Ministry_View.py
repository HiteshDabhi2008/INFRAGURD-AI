import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Setup path for imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dashboard.auth_ui import require_auth, show_user_profile
from dashboard.data_loader import get_merged_data

st.set_page_config(
    page_title="Ministry View | InfraGuard-AI",
    page_icon="🏛️",
    layout="wide",
)

require_auth()
show_user_profile()

user = st.session_state["user"]
allowed_roles = ["Super Admin", "Ministry Authority", "Viewer / Auditor"]

if user["authority_type"] not in allowed_roles:
    st.error("You do not have permission to view the Ministry Dashboard.")
    st.stop()

st.title("🏛️ Ministry / Sector Dashboard")

df = get_merged_data()
if df.empty:
    st.warning("No data available.")
    st.stop()

# Role-based restriction
if user["authority_type"] == "Ministry Authority" and user.get("organization"):
    df = df[df["ministry"] == user["organization"]]
    st.markdown(f"**Viewing Data For:** {user['organization']}")
else:
    ministry_filter = st.selectbox("Select Ministry", ["All"] + sorted(df["ministry"].dropna().unique().tolist()))
    if ministry_filter != "All":
        df = df[df["ministry"] == ministry_filter]

if df.empty:
    st.warning("No projects found for the selected Ministry.")
    st.stop()

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Projects", len(df))
col2.metric("Total Original Cost (₹ Cr)", f"{df['original_cost'].sum():,.2f}")
col3.metric("Total Revised Cost (₹ Cr)", f"{df.get('revised_cost', pd.Series([0])).sum():,.2f}")
col4.metric("Avg Physical Progress", f"{df['physical_progress'].mean():.1f}%")

st.markdown("---")
st.markdown("### 🏆 Best & Worst Performing Projects")

# Best performing (High progress, Low cost overrun)
# For simplicity, we just sort by physical progress descending
best_df = df.sort_values(by="physical_progress", ascending=False).head(5)
st.markdown("**Top 5 Projects by Physical Progress**")
st.dataframe(best_df[["project_code", "project_name", "agency", "physical_progress", "original_cost"]], use_container_width=True)

st.markdown("---")
st.markdown("### 📊 Sector-wise Breakdown")
sector_counts = df["sector"].value_counts().reset_index()
sector_counts.columns = ["Sector", "Count"]

fig = px.pie(sector_counts, names="Sector", values="Count", title="Projects by Sector")
st.plotly_chart(fig, use_container_width=True)
