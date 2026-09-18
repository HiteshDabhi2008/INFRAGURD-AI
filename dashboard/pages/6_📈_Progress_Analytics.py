"""
Progress Analytics — Physical progress distribution, expenditure vs progress, gap analysis.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import get_merged_data, apply_filters

st.set_page_config(page_title="Progress Analytics | InfraGuard-AI", page_icon="📈", layout="wide")

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
selected_state = st.sidebar.selectbox("State", states, key="prog_state")
sectors = ["All"] + sorted(df["sector"].dropna().unique().tolist()) if "sector" in df.columns else ["All"]
selected_sector = st.sidebar.selectbox("Sector", sectors, key="prog_sector")

filters = {"state": selected_state, "sector": selected_sector}
filtered = apply_filters(df, filters)

# ── Page Header ─────────────────────────────────────────────────────────
st.markdown("""
<div style="background: linear-gradient(135deg, #e65100 0%, #ef6c00 50%, #f57c00 100%); color: white; padding: 1rem 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
    <h2 style="margin:0;">📈 Progress Analytics</h2>
    <p style="margin:0.2rem 0 0 0; opacity:0.85; font-size:0.9rem;">Physical progress tracking, expenditure patterns, and gap analysis</p>
</div>
""", unsafe_allow_html=True)

# ── KPIs ────────────────────────────────────────────────────────────────
avg_prog = filtered["physical_progress"].mean() if "physical_progress" in filtered.columns else 0
completed = len(filtered[filtered["physical_progress"] >= 100]) if "physical_progress" in filtered.columns else 0
below_50 = len(filtered[filtered["physical_progress"] < 50]) if "physical_progress" in filtered.columns else 0
avg_gap = filtered["progress_gap"].mean() if "progress_gap" in filtered.columns else (filtered["safe_progress_gap"].mean() if "safe_progress_gap" in filtered.columns else 0)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Average Progress", f"{avg_prog:.1f}%")
k2.metric("Completed (≥100%)", f"{completed}")
k3.metric("Below 50%", f"{below_50}")
k4.metric("Avg Progress Gap", f"{avg_gap:.1f}%")

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── Charts ──────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Physical Progress Distribution**")
    if "physical_progress" in filtered.columns:
        fig = px.histogram(
            filtered, x="physical_progress", nbins=20,
            color_discrete_sequence=["#e65100"],
            labels={"physical_progress": "Physical Progress (%)"},
        )
        fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
        st.plotly_chart(fig, width="stretch")

with col2:
    st.markdown("**Expenditure % vs Physical Progress**")
    exp_col = "safe_expenditure_percent" if "safe_expenditure_percent" in filtered.columns else "expenditure_percent"
    if exp_col in filtered.columns and "physical_progress" in filtered.columns:
        ep_df = filtered[[exp_col, "physical_progress"]].dropna()
        if not ep_df.empty:
            fig2 = px.scatter(
                ep_df, x=exp_col, y="physical_progress",
                labels={exp_col: "Expenditure %", "physical_progress": "Physical Progress %"},
                color_discrete_sequence=["#ef6c00"], opacity=0.5,
            )
            fig2.add_trace(go.Scatter(x=[0, 100], y=[0, 100], mode="lines", line=dict(dash="dash", color="red"), name="Ideal"))
            fig2.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig2, width="stretch")

# ── Progress Gap Analysis ───────────────────────────────────────────────
st.markdown("---")
col3, col4 = st.columns(2)

gap_col = "progress_gap" if "progress_gap" in filtered.columns else ("safe_progress_gap" if "safe_progress_gap" in filtered.columns else None)

with col3:
    st.markdown("**Progress Gap Distribution**")
    if gap_col:
        gap_data = filtered[gap_col].dropna()
        if not gap_data.empty:
            fig3 = px.histogram(
                gap_data, nbins=30,
                color_discrete_sequence=["#f57c00"],
                labels={"value": "Progress Gap (Expenditure% - Physical%)"},
            )
            fig3.add_vline(x=0, line_dash="dash", line_color="green")
            fig3.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
            st.plotly_chart(fig3, width="stretch")
    else:
        st.info("Progress gap data not available.")

with col4:
    st.markdown("**Average Progress by State (Top 15)**")
    if "physical_progress" in filtered.columns:
        state_prog = filtered.groupby("state")["physical_progress"].mean().sort_values().head(15).reset_index()
        state_prog.columns = ["State", "Avg Progress"]
        fig4 = px.bar(
            state_prog, x="Avg Progress", y="State", orientation="h",
            color="Avg Progress", color_continuous_scale="RdYlGn",
        )
        fig4.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False)
        st.plotly_chart(fig4, width="stretch")

# ── Progress by Sector ──────────────────────────────────────────────────
st.markdown("---")
st.markdown("**Average Progress by Sector**")
if "sector" in filtered.columns and "physical_progress" in filtered.columns:
    sec_prog = filtered.groupby("sector")["physical_progress"].mean().sort_values(ascending=False).reset_index()
    sec_prog.columns = ["Sector", "Avg Progress"]
    fig5 = px.bar(
        sec_prog, x="Sector", y="Avg Progress",
        color="Avg Progress", color_continuous_scale="RdYlGn",
    )
    fig5.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False, xaxis_tickangle=-45)
    st.plotly_chart(fig5, width="stretch")

st.markdown("---")
st.caption(f"Showing {len(filtered):,} projects | InfraGuard-AI Prototype")
