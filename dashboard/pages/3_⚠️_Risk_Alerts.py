"""
Risk & Alerts — Risk monitoring page with categorized project lists and early warnings.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data_loader import get_merged_data, load_early_warnings, apply_filters

st.set_page_config(page_title="Risk & Alerts | InfraGuard-AI", page_icon="⚠️", layout="wide")

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
ew_df = load_early_warnings()

if df.empty:
    st.error("❌ No project data available.")
    st.stop()

# ── Sidebar Filters ─────────────────────────────────────────────────────
st.sidebar.markdown("### 🔍 Filters")

states = ["All"] + sorted(df["state"].dropna().unique().tolist())
selected_state = st.sidebar.selectbox("State", states, key="risk_state")

agencies = ["All"] + sorted(df["agency"].dropna().unique().tolist())
selected_agency = st.sidebar.selectbox("Agency", agencies, key="risk_agency")

sectors = ["All"] + sorted(df["sector"].dropna().unique().tolist()) if "sector" in df.columns else ["All"]
selected_sector = st.sidebar.selectbox("Sector", sectors, key="risk_sector")

risk_levels = ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"]
selected_risk = st.sidebar.selectbox("Risk Level", risk_levels, key="risk_level")

filters = {"state": selected_state, "agency": selected_agency, "sector": selected_sector}
filtered = apply_filters(df, filters)

# ── Page Header ─────────────────────────────────────────────────────────
st.markdown("""
<div style="background: linear-gradient(135deg, #b71c1c 0%, #c62828 50%, #e53935 100%); color: white; padding: 1rem 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
    <h2 style="margin:0;">⚠️ Risk & Alerts</h2>
    <p style="margin:0.2rem 0 0 0; opacity:0.85; font-size:0.9rem;">Real-time risk monitoring and early warning system</p>
</div>
""", unsafe_allow_html=True)

# ── Merge risk data with master for display ──────────────────────────────
if ew_df.empty or "overall_risk" not in ew_df.columns:
    st.warning("⚠️ Pre-computed risk data not found. Run `python src/risk/run_risk_engine.py` first.")
    st.info("The early warning results CSV should be at `outputs/member5/early_warning_results.csv`.")
    st.stop()

# Join risk data with project data
risk_merged = pd.merge(
    filtered[["project_code", "project_name", "state", "agency", "original_cost", "revised_cost", "physical_progress"]].drop_duplicates(subset=["project_code"]),
    ew_df[["project_code", "risk_score", "overall_risk", "cost_risk_level", "time_risk_level", "num_warnings", "explanation"]].drop_duplicates(subset=["project_code"]),
    on="project_code",
    how="left",
)
# Projects not in early warnings are LOW risk
risk_merged["overall_risk"] = risk_merged["overall_risk"].fillna("LOW")
risk_merged["risk_score"] = risk_merged["risk_score"].fillna(0)
risk_merged["num_warnings"] = risk_merged["num_warnings"].fillna(0)

# Apply risk level filter
if selected_risk != "All":
    risk_merged = risk_merged[risk_merged["overall_risk"] == selected_risk]

# ── Risk Category Summary ───────────────────────────────────────────────
risk_counts = risk_merged["overall_risk"].value_counts().to_dict()

kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)

def risk_kpi(label, count, color, emoji):
    return f"""
    <div style="background:white; border-radius:12px; padding:1rem; box-shadow:0 2px 8px rgba(0,0,0,0.08); border-left:4px solid {color}; text-align:center;">
        <div style="font-size:0.75rem; color:#666; text-transform:uppercase;">{emoji} {label}</div>
        <div style="font-size:2rem; font-weight:700; color:{color};">{count}</div>
    </div>
    """

with kpi_c1:
    st.markdown(risk_kpi("Low Risk", risk_counts.get("LOW", 0), "#4caf50", "🟢"), unsafe_allow_html=True)
with kpi_c2:
    st.markdown(risk_kpi("Medium Risk", risk_counts.get("MEDIUM", 0), "#ff9800", "🟡"), unsafe_allow_html=True)
with kpi_c3:
    st.markdown(risk_kpi("High Risk", risk_counts.get("HIGH", 0), "#f44336", "🔴"), unsafe_allow_html=True)
with kpi_c4:
    st.markdown(risk_kpi("Critical", risk_counts.get("CRITICAL", 0), "#b71c1c", "⛔"), unsafe_allow_html=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── Risk Distribution Chart ─────────────────────────────────────────────
risk_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
risk_colors = {"LOW": "#4caf50", "MEDIUM": "#ff9800", "HIGH": "#f44336", "CRITICAL": "#b71c1c"}

fig = go.Figure(data=[go.Bar(
    x=risk_order,
    y=[risk_counts.get(r, 0) for r in risk_order],
    marker_color=[risk_colors[r] for r in risk_order],
    text=[risk_counts.get(r, 0) for r in risk_order],
    textposition="auto",
)])
fig.update_layout(
    title="Risk Category Distribution",
    height=300, margin=dict(l=20, r=20, t=40, b=20),
    xaxis_title="Risk Category", yaxis_title="Count",
)
st.plotly_chart(fig, width="stretch")

# ── High Risk & Critical Projects ───────────────────────────────────────
high_critical = risk_merged[risk_merged["overall_risk"].isin(["HIGH", "CRITICAL"])].sort_values("risk_score", ascending=False)

if not high_critical.empty:
    st.markdown(f'<div style="font-size:1.1rem; font-weight:600; color:#c62828; margin:1rem 0;">🚨 High Risk & Critical Projects ({len(high_critical)})</div>', unsafe_allow_html=True)

    for _, row in high_critical.head(20).iterrows():
        risk_color = risk_colors.get(row["overall_risk"], "#666")
        exp_text = str(row.get("explanation", "")).replace("\n", " | ")[:200]
        st.markdown(f"""
        <div style="background:white; border-radius:10px; padding:1rem; margin:0.5rem 0; box-shadow:0 2px 6px rgba(0,0,0,0.08); border-left:5px solid {risk_color};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <strong>{row.get('project_name', 'N/A')[:80]}</strong>
                    <span style="color:#666; margin-left:1rem;">Code: {row['project_code']}</span>
                </div>
                <span style="background:{risk_color}; color:white; padding:3px 12px; border-radius:20px; font-weight:600; font-size:0.8rem;">{row['overall_risk']}</span>
            </div>
            <div style="font-size:0.85rem; color:#555; margin-top:0.5rem;">
                State: {row.get('state','N/A')} | Progress: {row.get('physical_progress','N/A')}% | Cost Risk: {row.get('cost_risk_level','N/A')} | Time Risk: {row.get('time_risk_level','N/A')} | Warnings: {int(row.get('num_warnings',0))}
            </div>
            <div style="font-size:0.8rem; color:#888; margin-top:0.3rem; font-style:italic;">{exp_text}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.success("✅ No HIGH or CRITICAL risk projects found in the current filter.")

# ── Early Warnings Table ────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div style="font-size:1.1rem; font-weight:600; color:#1a237e; margin:1rem 0;">📋 All Projects with Warnings</div>', unsafe_allow_html=True)

warned = risk_merged[risk_merged["num_warnings"] > 0].sort_values("num_warnings", ascending=False)

if not warned.empty:
    display = warned[["project_code", "project_name", "state", "overall_risk", "risk_score", "cost_risk_level", "time_risk_level", "num_warnings"]].copy()
    display.columns = ["Code", "Name", "State", "Risk", "Score", "Cost Risk", "Time Risk", "Warnings"]
    st.dataframe(display, width="stretch", height=400, hide_index=True)
else:
    st.info("No projects with active warnings in the current filter.")

st.markdown("---")
st.caption("InfraGuard-AI | Prototype — Risk thresholds are proposed, not official MoSPI values.")
