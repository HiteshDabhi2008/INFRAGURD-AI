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
    page_title="State / Region View | InfraGuard-AI",
    page_icon="🗺️",
    layout="wide",
)

require_auth()
show_user_profile()

user = st.session_state["user"]
allowed_roles = ["Super Admin", "State Authority", "Viewer / Auditor"]

if user["authority_type"] not in allowed_roles:
    st.error("You do not have permission to view the State / Region Dashboard.")
    st.stop()

st.title("🗺️ State / Region Dashboard")

df = get_merged_data()
if df.empty:
    st.warning("No data available.")
    st.stop()

# Role-based restriction
if user["authority_type"] == "State Authority" and user.get("state_region"):
    df = df[df["state"] == user["state_region"]]
    st.markdown(f"**Viewing Data For State:** {user['state_region']}")
else:
    state_filter = st.selectbox("Select State", ["All"] + sorted(df["state"].dropna().unique().tolist()))
    if state_filter != "All":
        df = df[df["state"] == state_filter]

if df.empty:
    st.warning("No projects found for the selected State.")
    st.stop()

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Projects", len(df))
col2.metric("Total Original Cost (₹ Cr)", f"{df['original_cost'].sum():,.2f}")
col3.metric("Total Revised Cost (₹ Cr)", f"{df.get('revised_cost', pd.Series([0])).sum():,.2f}")
col4.metric("Avg Physical Progress", f"{df['physical_progress'].mean():.1f}%")

st.markdown("---")
st.markdown("### 📈 Cost vs Progress Scatter")

fig_scatter = px.scatter(
    df, x="physical_progress", y="original_cost", 
    hover_name="project_name", color="sector",
    title="Project Cost vs Physical Progress",
    labels={"physical_progress": "Progress (%)", "original_cost": "Cost (₹ Cr)"}
)
st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("### 🏆 Top Projects in Region")
best_df = df.sort_values(by="physical_progress", ascending=False).head(5)
st.dataframe(best_df[["project_code", "project_name", "agency", "physical_progress", "original_cost"]], use_container_width=True)
