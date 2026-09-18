"""
Cost Analytics — Cost overrun analysis, original vs revised cost, distribution charts.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import get_merged_data, apply_filters

st.set_page_config(page_title="Cost Analytics | InfraGuard-AI", page_icon="💰", layout="wide")

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
selected_state = st.sidebar.selectbox("State", states, key="cost_state")
sectors = ["All"] + sorted(df["sector"].dropna().unique().tolist()) if "sector" in df.columns else ["All"]
selected_sector = st.sidebar.selectbox("Sector", sectors, key="cost_sector")

filters = {"state": selected_state, "sector": selected_sector}
filtered = apply_filters(df, filters)

# ── Page Header ─────────────────────────────────────────────────────────
st.markdown("""
<div style="background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 50%, #388e3c 100%); color: white; padding: 1rem 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
    <h2 style="margin:0;">💰 Cost Analytics</h2>
    <p style="margin:0.2rem 0 0 0; opacity:0.85; font-size:0.9rem;">Budget analysis, cost overruns, and expenditure patterns</p>
</div>
""", unsafe_allow_html=True)

# ── KPI Row ─────────────────────────────────────────────────────────────
total_orig = filtered["original_cost"].sum()
total_rev = filtered["revised_cost"].sum()
total_exp = filtered["cumulative_expenditure"].sum()
cost_escalation = ((total_rev - total_orig) / total_orig * 100) if total_orig > 0 else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Original Cost (₹ Cr)", f"{total_orig:,.0f}")
k2.metric("Total Revised Cost (₹ Cr)", f"{total_rev:,.0f}")
k3.metric("Total Expenditure (₹ Cr)", f"{total_exp:,.0f}")
k4.metric("Overall Cost Escalation", f"{cost_escalation:.1f}%")

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── Charts ──────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Original vs Revised Cost**")
    # Scatter plot
    scatter_df = filtered[["project_code", "original_cost", "revised_cost"]].dropna()
    if not scatter_df.empty:
        fig = px.scatter(
            scatter_df, x="original_cost", y="revised_cost",
            labels={"original_cost": "Original Cost (₹ Cr)", "revised_cost": "Revised Cost (₹ Cr)"},
            color_discrete_sequence=["#1a237e"],
            opacity=0.6,
        )
        # Add diagonal reference line
        max_val = max(scatter_df["original_cost"].max(), scatter_df["revised_cost"].max())
        fig.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val], mode="lines", line=dict(dash="dash", color="red"), name="No Change"))
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, width="stretch")

with col2:
    st.markdown("**Cost Change Distribution (%)**")
    if "cost_change_percent" in filtered.columns:
        cc = filtered["cost_change_percent"].dropna()
        if not cc.empty:
            fig2 = px.histogram(
                cc, nbins=30,
                color_discrete_sequence=["#2e7d32"],
                labels={"value": "Cost Change (%)"},
            )
            fig2.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
            st.plotly_chart(fig2, width="stretch")
    else:
        st.info("Cost change data not available.")

# ── Cost by State ───────────────────────────────────────────────────────
st.markdown("---")
col3, col4 = st.columns(2)

with col3:
    st.markdown("**Total Cost by State (Top 15)**")
    state_cost = filtered.groupby("state")[["original_cost", "revised_cost"]].sum().sort_values("revised_cost", ascending=False).head(15).reset_index()
    if not state_cost.empty:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Original", x=state_cost["state"], y=state_cost["original_cost"], marker_color="#1a237e"))
        fig3.add_trace(go.Bar(name="Revised", x=state_cost["state"], y=state_cost["revised_cost"], marker_color="#e65100"))
        fig3.update_layout(barmode="group", height=400, margin=dict(l=0, r=0, t=10, b=0), xaxis_tickangle=-45)
        st.plotly_chart(fig3, width="stretch")

with col4:
    st.markdown("**Cost by Sector**")
    if "sector" in filtered.columns:
        sector_cost = filtered.groupby("sector")[["revised_cost"]].sum().sort_values("revised_cost", ascending=False).head(10).reset_index()
        if not sector_cost.empty:
            fig4 = px.bar(
                sector_cost, x="revised_cost", y="sector", orientation="h",
                color="revised_cost", color_continuous_scale="Greens",
                labels={"revised_cost": "Revised Cost (₹ Cr)"},
            )
            fig4.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False)
            st.plotly_chart(fig4, width="stretch")

# ── Expenditure vs Progress ─────────────────────────────────────────────
st.markdown("---")
st.markdown("**Expenditure % vs Physical Progress**")

if "safe_expenditure_percent" in filtered.columns and "physical_progress" in filtered.columns:
    ep_df = filtered[["project_code", "safe_expenditure_percent", "physical_progress"]].dropna()
    if not ep_df.empty:
        fig5 = px.scatter(
            ep_df, x="safe_expenditure_percent", y="physical_progress",
            labels={"safe_expenditure_percent": "Expenditure %", "physical_progress": "Physical Progress %"},
            color_discrete_sequence=["#6a1b9a"],
            opacity=0.5,
        )
        fig5.add_trace(go.Scatter(x=[0, 100], y=[0, 100], mode="lines", line=dict(dash="dash", color="red"), name="Ideal"))
        fig5.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig5, width="stretch")

st.markdown("---")
st.caption(f"Showing {len(filtered):,} projects | InfraGuard-AI Prototype")
