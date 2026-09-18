"""
Portfolio Overview — KPI cards, risk distribution, and geographic analysis.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import get_merged_data, apply_filters

st.set_page_config(page_title="Portfolio Overview | InfraGuard-AI", page_icon="📊", layout="wide")

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


# ── Load Data ───────────────────────────────────────────────────────────
df = get_merged_data()

if df.empty:
    st.error("❌ No project data available. Please check data/processed/master_projects.csv")
    st.stop()

# ── Sidebar Filters ─────────────────────────────────────────────────────
st.sidebar.markdown("### 🔍 Filters")

states = ["All"] + sorted(df["state"].dropna().unique().tolist())
selected_state = st.sidebar.selectbox("State", states, key="ov_state")

agencies = ["All"] + sorted(df["agency"].dropna().unique().tolist())
selected_agency = st.sidebar.selectbox("Agency", agencies, key="ov_agency")

sectors = ["All"] + sorted(df["sector"].dropna().unique().tolist()) if "sector" in df.columns else ["All"]
selected_sector = st.sidebar.selectbox("Sector", sectors, key="ov_sector")

search = st.sidebar.text_input("🔎 Search Project ID / Name", key="ov_search")

filters = {
    "state": selected_state,
    "agency": selected_agency,
    "sector": selected_sector,
    "search": search,
}
filtered = apply_filters(df, filters)

# ── Page Header ─────────────────────────────────────────────────────────
st.markdown("""
<div style="background: linear-gradient(135deg, #1a237e 0%, #0d47a1 50%, #01579b 100%); color: white; padding: 1rem 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
    <h2 style="margin:0;">📊 Portfolio Overview</h2>
    <p style="margin:0.2rem 0 0 0; opacity:0.85; font-size:0.9rem;">Real-time infrastructure project monitoring dashboard</p>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards ───────────────────────────────────────────────────────────
total_projects = len(filtered)
ongoing = len(filtered[filtered["physical_progress"] < 100]) if "physical_progress" in filtered.columns else total_projects
orig_cost = filtered["original_cost"].sum() if "original_cost" in filtered.columns else 0
rev_cost = filtered["revised_cost"].sum() if "revised_cost" in filtered.columns else 0
expenditure = filtered["cumulative_expenditure"].sum() if "cumulative_expenditure" in filtered.columns else 0
avg_progress = filtered["physical_progress"].mean() if "physical_progress" in filtered.columns else 0

# Count high/critical risk from pre-computed early warning data
from data_loader import load_early_warnings
ew_df = load_early_warnings()
if not ew_df.empty and "overall_risk" in ew_df.columns:
    # Filter by the same project codes
    ew_filtered = ew_df[ew_df["project_code"].isin(filtered["project_code"])]
    high_risk = len(ew_filtered[ew_filtered["overall_risk"] == "HIGH"]) if "overall_risk" in ew_filtered.columns else 0
    critical = len(ew_filtered[ew_filtered["overall_risk"] == "CRITICAL"]) if "overall_risk" in ew_filtered.columns else 0
    medium_risk = len(ew_filtered[ew_filtered["overall_risk"] == "MEDIUM"]) if "overall_risk" in ew_filtered.columns else 0
else:
    high_risk = 0
    critical = 0
    medium_risk = 0

def kpi_html(label, value, color="#1a237e"):
    return f"""
    <div style="background:white; border-radius:12px; padding:1rem 1.2rem; box-shadow:0 2px 8px rgba(0,0,0,0.08); border-left:4px solid {color};">
        <div style="font-size:0.75rem; color:#666; text-transform:uppercase; letter-spacing:0.5px; font-weight:500;">{label}</div>
        <div style="font-size:1.6rem; font-weight:700; color:{color}; margin:0.2rem 0;">{value}</div>
    </div>
    """

row1 = st.columns(4)
with row1[0]:
    st.markdown(kpi_html("Total Projects", f"{total_projects:,}"), unsafe_allow_html=True)
with row1[1]:
    st.markdown(kpi_html("Ongoing Projects", f"{ongoing:,}", "#0d47a1"), unsafe_allow_html=True)
with row1[2]:
    st.markdown(kpi_html("High Risk Projects", f"{high_risk:,}", "#e65100"), unsafe_allow_html=True)
with row1[3]:
    st.markdown(kpi_html("Critical Projects", f"{critical:,}", "#b71c1c"), unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

row2 = st.columns(4)
with row2[0]:
    st.markdown(kpi_html("Original Cost (₹ Cr)", f"{orig_cost:,.2f}", "#2e7d32"), unsafe_allow_html=True)
with row2[1]:
    st.markdown(kpi_html("Revised Cost (₹ Cr)", f"{rev_cost:,.2f}", "#1565c0"), unsafe_allow_html=True)
with row2[2]:
    st.markdown(kpi_html("Expenditure (₹ Cr)", f"{expenditure:,.2f}", "#6a1b9a"), unsafe_allow_html=True)
with row2[3]:
    st.markdown(kpi_html("Avg Physical Progress", f"{avg_progress:.1f}%", "#00695c"), unsafe_allow_html=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── Charts ──────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.markdown('<div class="section-header">📍 Projects by State (Top 15)</div>', unsafe_allow_html=True)
    state_counts = filtered["state"].value_counts().head(15).reset_index()
    state_counts.columns = ["State", "Count"]
    fig_states = px.bar(
        state_counts, x="Count", y="State", orientation="h",
        color="Count", color_continuous_scale="Blues",
    )
    fig_states.update_layout(height=450, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig_states, width="stretch")

with col_right:
    st.markdown('<div class="section-header">🏢 Projects by Sector</div>', unsafe_allow_html=True)
    if "sector" in filtered.columns:
        sector_counts = filtered["sector"].value_counts().head(10).reset_index()
        sector_counts.columns = ["Sector", "Count"]
        fig_sector = px.pie(
            sector_counts, values="Count", names="Sector",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig_sector.update_layout(height=450, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_sector, width="stretch")
    else:
        st.info("Sector data not available.")

# ── Risk Distribution ───────────────────────────────────────────────────
st.markdown('<div class="section-header">⚠️ Risk Distribution</div>', unsafe_allow_html=True)
risk_col1, risk_col2 = st.columns(2)

with risk_col1:
    if not ew_df.empty and "overall_risk" in ew_df.columns:
        # Use full risk data — need to add projects with no warnings as LOW
        all_codes = set(filtered["project_code"].unique())
        warned_codes = set(ew_df["project_code"].unique())
        low_count = len(all_codes - warned_codes)
        
        risk_data = ew_df[ew_df["project_code"].isin(all_codes)]["overall_risk"].value_counts().to_dict()
        risk_data["LOW"] = risk_data.get("LOW", 0) + low_count
        
        risk_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        risk_colors = {"LOW": "#4caf50", "MEDIUM": "#ff9800", "HIGH": "#f44336", "CRITICAL": "#b71c1c"}
        
        fig_risk = go.Figure(data=[go.Bar(
            x=risk_order,
            y=[risk_data.get(r, 0) for r in risk_order],
            marker_color=[risk_colors[r] for r in risk_order],
            text=[risk_data.get(r, 0) for r in risk_order],
            textposition="auto",
        )])
        fig_risk.update_layout(
            height=350, margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="Risk Category", yaxis_title="Number of Projects",
        )
        st.plotly_chart(fig_risk, width="stretch")
    else:
        st.info("Risk data not yet computed. Run the risk engine first.")

with risk_col2:
    st.markdown("**Physical Progress Distribution**")
    if "physical_progress" in filtered.columns:
        fig_prog = px.histogram(
            filtered, x="physical_progress", nbins=20,
            color_discrete_sequence=["#1a237e"],
            labels={"physical_progress": "Physical Progress (%)"},
        )
        fig_prog.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
        st.plotly_chart(fig_prog, width="stretch")

# ── Footer ──────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(f"Showing {len(filtered):,} of {len(df):,} projects | Data: PAIMANA Flash Report July 2026 | Prototype thresholds")
