"""
Schedule Analytics — Duration analysis, time risk distribution, schedule concerns.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import get_merged_data, apply_filters, load_early_warnings

st.set_page_config(page_title="Schedule Analytics | InfraGuard-AI", page_icon="📅", layout="wide")

# Setup path for auth imports
import sys
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dashboard.auth_ui import require_auth, show_user_profile

# Enforce authentication
require_auth()

# Show user profile in sidebar
show_user_profile()


df = get_merged_data()

if df.empty:
    st.error("❌ No project data available.")
    st.stop()

# ── Sidebar Filters ─────────────────────────────────────────────────────
st.sidebar.markdown("### 🔍 Filters")
states = ["All"] + sorted(df["state"].dropna().unique().tolist())
selected_state = st.sidebar.selectbox("State", states, key="sched_state")
sectors = ["All"] + sorted(df["sector"].dropna().unique().tolist()) if "sector" in df.columns else ["All"]
selected_sector = st.sidebar.selectbox("Sector", sectors, key="sched_sector")

filters = {"state": selected_state, "sector": selected_sector}
filtered = apply_filters(df, filters)

# ── Page Header ─────────────────────────────────────────────────────────
st.markdown("""
<div style="background: linear-gradient(135deg, #4a148c 0%, #6a1b9a 50%, #7b1fa2 100%); color: white; padding: 1rem 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
    <h2 style="margin:0;">📅 Schedule Analytics</h2>
    <p style="margin:0.2rem 0 0 0; opacity:0.85; font-size:0.9rem;">Project duration analysis, time risk, and schedule performance</p>
</div>
""", unsafe_allow_html=True)

# ── KPIs ────────────────────────────────────────────────────────────────
avg_age = filtered["project_age_days"].mean() if "project_age_days" in filtered.columns else 0
avg_dur = filtered["original_duration_days"].mean() if "original_duration_days" in filtered.columns else 0

# Load time risk from early warnings
ew_df = load_early_warnings()
time_high = 0
if not ew_df.empty and "time_risk_level" in ew_df.columns:
    ew_filt = ew_df[ew_df["project_code"].isin(filtered["project_code"])]
    time_high = len(ew_filt[ew_filt["time_risk_level"] == "HIGH"])

# Projects past original completion
past_completion = 0
if "project_age_days" in filtered.columns and "original_duration_days" in filtered.columns:
    past_df = filtered.dropna(subset=["project_age_days", "original_duration_days"])
    past_completion = len(past_df[past_df["project_age_days"] > past_df["original_duration_days"]])

k1, k2, k3, k4 = st.columns(4)
k1.metric("Avg Project Age", f"{avg_age:.0f} days")
k2.metric("Avg Original Duration", f"{avg_dur:.0f} days")
k3.metric("Time-Risk HIGH", f"{time_high}")
k4.metric("Past Original Deadline", f"{past_completion}")

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── Charts ──────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Project Duration Distribution (days)**")
    if "original_duration_days" in filtered.columns:
        dur = filtered["original_duration_days"].dropna()
        if not dur.empty:
            fig = px.histogram(dur, nbins=25, color_discrete_sequence=["#4a148c"],
                               labels={"value": "Original Duration (days)"})
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
            st.plotly_chart(fig, width="stretch")

with col2:
    st.markdown("**Project Age vs Original Duration**")
    if "project_age_days" in filtered.columns and "original_duration_days" in filtered.columns:
        age_df = filtered[["project_code", "project_age_days", "original_duration_days"]].dropna()
        if not age_df.empty:
            fig2 = px.scatter(
                age_df, x="original_duration_days", y="project_age_days",
                labels={"original_duration_days": "Original Duration (days)", "project_age_days": "Actual Age (days)"},
                color_discrete_sequence=["#6a1b9a"], opacity=0.5,
            )
            max_val = max(age_df["original_duration_days"].max(), age_df["project_age_days"].max())
            fig2.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val], mode="lines", line=dict(dash="dash", color="red"), name="On Schedule"))
            fig2.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig2, width="stretch")

# ── Time Risk Distribution ──────────────────────────────────────────────
st.markdown("---")
col3, col4 = st.columns(2)

with col3:
    st.markdown("**Time Risk Distribution**")
    if not ew_df.empty and "time_risk_level" in ew_df.columns:
        ew_filt = ew_df[ew_df["project_code"].isin(filtered["project_code"])]
        tr_counts = ew_filt["time_risk_level"].value_counts().to_dict()
        # Projects not in warnings are LOW
        all_codes = set(filtered["project_code"].unique())
        warned_codes = set(ew_filt["project_code"].unique())
        tr_counts["LOW"] = tr_counts.get("LOW", 0) + len(all_codes - warned_codes)

        risk_order = ["LOW", "MEDIUM", "HIGH"]
        colors = {"LOW": "#4caf50", "MEDIUM": "#ff9800", "HIGH": "#f44336"}

        fig3 = go.Figure(data=[go.Bar(
            x=risk_order, y=[tr_counts.get(r, 0) for r in risk_order],
            marker_color=[colors[r] for r in risk_order],
            text=[tr_counts.get(r, 0) for r in risk_order], textposition="auto",
        )])
        fig3.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0),
                           xaxis_title="Time Risk Level", yaxis_title="Count")
        st.plotly_chart(fig3, width="stretch")
    else:
        st.info("Time risk data not available.")

with col4:
    st.markdown("**Schedule Concerns by State (Top 10)**")
    if "project_age_days" in filtered.columns and "original_duration_days" in filtered.columns:
        delayed = filtered.dropna(subset=["project_age_days", "original_duration_days"])
        delayed = delayed[delayed["project_age_days"] > delayed["original_duration_days"]]
        if not delayed.empty:
            state_delays = delayed["state"].value_counts().head(10).reset_index()
            state_delays.columns = ["State", "Delayed Projects"]
            fig4 = px.bar(state_delays, x="Delayed Projects", y="State", orientation="h",
                          color="Delayed Projects", color_continuous_scale="Reds")
            fig4.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False)
            st.plotly_chart(fig4, width="stretch")
        else:
            st.success("No projects past their original deadline in this filter.")

st.markdown("---")
st.caption(f"Showing {len(filtered):,} projects | InfraGuard-AI Prototype")
