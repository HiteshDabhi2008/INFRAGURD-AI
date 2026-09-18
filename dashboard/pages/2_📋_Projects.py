"""
Projects — Searchable project table with detail view and ML risk predictions.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
from data_loader import get_merged_data, apply_filters, prepare_project_dict, get_risk_prediction

st.set_page_config(page_title="Projects | InfraGuard-AI", page_icon="📋", layout="wide")

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
    st.error("❌ No project data available.")
    st.stop()

# ── Sidebar Filters ─────────────────────────────────────────────────────
st.sidebar.markdown("### 🔍 Filters")

states = ["All"] + sorted(df["state"].dropna().unique().tolist())
selected_state = st.sidebar.selectbox("State", states, key="proj_state")

agencies = ["All"] + sorted(df["agency"].dropna().unique().tolist())
selected_agency = st.sidebar.selectbox("Agency", agencies, key="proj_agency")

sectors = ["All"] + sorted(df["sector"].dropna().unique().tolist()) if "sector" in df.columns else ["All"]
selected_sector = st.sidebar.selectbox("Sector", sectors, key="proj_sector")

search = st.sidebar.text_input("🔎 Search Project ID / Name", key="proj_search")

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
    <h2 style="margin:0;">📋 Projects</h2>
    <p style="margin:0.2rem 0 0 0; opacity:0.85; font-size:0.9rem;">Browse, filter, and inspect individual projects with ML-powered risk predictions</p>
</div>
""", unsafe_allow_html=True)

st.write(f"Showing **{len(filtered):,}** projects")

# ── Project Table ───────────────────────────────────────────────────────
display_cols = [
    "project_code", "project_name", "state", "agency",
    "original_cost", "revised_cost", "cumulative_expenditure",
    "physical_progress",
]
available_cols = [c for c in display_cols if c in filtered.columns]

table_df = filtered[available_cols].copy()
table_df.columns = [c.replace("_", " ").title() for c in available_cols]

st.dataframe(
    table_df,
    width="stretch",
    height=400,
    hide_index=True,
)

# ── Project Detail View ─────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div style="font-size:1.1rem; font-weight:600; color:#1a237e; margin-bottom:1rem;">🔍 Project Detail View</div>', unsafe_allow_html=True)

project_codes = filtered["project_code"].astype(str).unique().tolist()
selected_code = st.selectbox(
    "Select a Project Code to view details:",
    ["— Select —"] + project_codes,
    key="detail_select",
)

if selected_code != "— Select —":
    proj_row = filtered[filtered["project_code"].astype(str) == selected_code].iloc[0]

    # ── Project Information ──────────────────────────────────────────
    st.markdown("#### 📄 Project Information")
    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.markdown(f"**Project Code:** {proj_row.get('project_code', 'N/A')}")
        st.markdown(f"**Project Name:** {proj_row.get('project_name', 'N/A')}")
        st.markdown(f"**Agency:** {proj_row.get('agency', 'N/A')}")
        st.markdown(f"**State:** {proj_row.get('state', 'N/A')}")
    with info_col2:
        st.markdown(f"**Sector:** {proj_row.get('sector', 'N/A')}")
        st.markdown(f"**Report Month:** {proj_row.get('report_month', 'N/A')}")
        st.markdown(f"**Source Page:** {proj_row.get('source_page', 'N/A')}")

    st.markdown("---")

    # ── Financial Information ────────────────────────────────────────
    st.markdown("#### 💰 Financial Information")
    fin_c1, fin_c2, fin_c3, fin_c4 = st.columns(4)
    with fin_c1:
        oc = proj_row.get("original_cost")
        st.metric("Original Cost (₹ Cr)", f"{oc:,.2f}" if pd.notna(oc) else "N/A")
    with fin_c2:
        rc = proj_row.get("revised_cost")
        st.metric("Revised Cost (₹ Cr)", f"{rc:,.2f}" if pd.notna(rc) else "N/A")
    with fin_c3:
        exp = proj_row.get("cumulative_expenditure")
        st.metric("Expenditure (₹ Cr)", f"{exp:,.2f}" if pd.notna(exp) else "N/A")
    with fin_c4:
        exp_pct = proj_row.get("safe_expenditure_percent") or proj_row.get("expenditure_percent")
        st.metric("Expenditure %", f"{exp_pct:.1f}%" if pd.notna(exp_pct) else "N/A")

    # ── Progress ────────────────────────────────────────────────────
    st.markdown("#### 📈 Progress")
    prog_c1, prog_c2, prog_c3 = st.columns(3)
    with prog_c1:
        pp = proj_row.get("physical_progress")
        st.metric("Physical Progress", f"{pp:.1f}%" if pd.notna(pp) else "N/A")
    with prog_c2:
        gap = proj_row.get("progress_gap") or proj_row.get("safe_progress_gap")
        color = "normal" if pd.notna(gap) and gap <= 0 else "inverse"
        st.metric("Progress Gap", f"{gap:.1f}%" if pd.notna(gap) else "N/A")
    with prog_c3:
        cc = proj_row.get("cost_change_percent")
        st.metric("Cost Change", f"{cc:.1f}%" if pd.notna(cc) else "N/A")

    # ── Schedule ────────────────────────────────────────────────────
    st.markdown("#### 📅 Schedule")
    sch_c1, sch_c2, sch_c3 = st.columns(3)
    with sch_c1:
        st.markdown(f"**Approval Date:** {proj_row.get('approval_date', 'N/A')}")
        st.markdown(f"**Start Date:** {proj_row.get('start_date', 'N/A')}")
    with sch_c2:
        st.markdown(f"**Original Completion:** {proj_row.get('original_completion_date', 'N/A')}")
        st.markdown(f"**Revised Completion:** {proj_row.get('revised_completion_date', 'N/A')}")
    with sch_c3:
        age = proj_row.get("project_age_days")
        dur = proj_row.get("original_duration_days")
        st.markdown(f"**Project Age:** {int(age)} days" if pd.notna(age) else "**Project Age:** N/A")
        st.markdown(f"**Original Duration:** {int(dur)} days" if pd.notna(dur) else "**Original Duration:** N/A")

    st.markdown("---")

    # ── Risk Assessment (ML Integration) ────────────────────────────
    st.markdown("#### ⚠️ Risk Assessment (ML-Powered)")
    st.caption("Calling Member 3 (Cost), Member 4 (Time), and Member 5 (Risk Engine) models...")

    project_dict = prepare_project_dict(proj_row)

    with st.spinner("Running risk prediction..."):
        risk_result = get_risk_prediction(project_dict)

    if risk_result["overall_risk"] == "UNAVAILABLE":
        st.warning(f"⚠️ Risk engine returned an error: {risk_result.get('explanation', 'Unknown error')}")
    else:
        # Risk summary cards
        risk_colors = {
            "LOW": "#4caf50", "MEDIUM": "#ff9800",
            "HIGH": "#f44336", "CRITICAL": "#b71c1c",
        }
        overall = risk_result.get("overall_risk", "N/A")
        badge_color = risk_colors.get(overall, "#666")

        r_c1, r_c2, r_c3, r_c4 = st.columns(4)
        with r_c1:
            st.markdown(f"""
            <div style="background:white; border-radius:12px; padding:1rem; box-shadow:0 2px 8px rgba(0,0,0,0.08); border-left:4px solid {badge_color}; text-align:center;">
                <div style="font-size:0.75rem; color:#666; text-transform:uppercase;">Overall Risk</div>
                <div style="font-size:1.5rem; font-weight:700; color:{badge_color};">{overall}</div>
            </div>
            """, unsafe_allow_html=True)
        with r_c2:
            st.metric("Risk Score", risk_result.get("risk_score", "N/A"))
        with r_c3:
            cost_out = risk_result.get("cost_model_output", {})
            cost_lvl = cost_out.get("risk_level", "N/A")
            cost_prob = cost_out.get("overrun_probability")
            st.metric("Cost Risk", f"{cost_lvl} ({cost_prob*100:.1f}%)" if cost_prob else cost_lvl)
        with r_c4:
            time_out = risk_result.get("time_model_output", {})
            time_lvl = time_out.get("risk_level", "N/A")
            time_prob = time_out.get("overrun_probability")
            st.metric("Time Risk", f"{time_lvl} ({time_prob*100:.1f}%)" if time_prob else time_lvl)

        # Detailed risk info
        with st.expander("📋 Detailed Risk Information", expanded=True):
            det_c1, det_c2 = st.columns(2)
            with det_c1:
                st.markdown("**Cost Model Output (Member 3)**")
                cost_exp = cost_out.get("expected_overrun_percent")
                st.write(f"- Risk Level: **{cost_out.get('risk_level', 'N/A')}**")
                st.write(f"- Overrun Probability: **{cost_out.get('overrun_probability', 'N/A')}**")
                st.write(f"- Expected Overrun: **{cost_exp:.1f}%**" if cost_exp is not None else "- Expected Overrun: **N/A**")
            with det_c2:
                st.markdown("**Time Model Output (Member 4)**")
                time_months = time_out.get("expected_overrun_months")
                st.write(f"- Risk Level: **{time_out.get('risk_level', 'N/A')}**")
                st.write(f"- Overrun Probability: **{time_out.get('overrun_probability', 'N/A')}**")
                st.write(f"- Expected Overrun: **{time_months:.1f} months**" if time_months is not None else "- Expected Overrun: **N/A**")

        # Warnings
        warnings_list = risk_result.get("warnings", [])
        if warnings_list:
            st.markdown("**🚨 Early Warnings**")
            for w in warnings_list:
                st.markdown(f"""
                <div style="background:#fff8e1; border-left:4px solid #ffa000; padding:0.7rem 1rem; border-radius:6px; margin:0.4rem 0; font-size:0.9rem;">
                    ⚠️ {w}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No early warnings for this project.")

        # Explanation
        explanation = risk_result.get("explanation", "")
        if explanation:
            with st.expander("📝 Risk Explanation"):
                st.text(explanation)

# ── Footer ──────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("InfraGuard-AI | Prototype — Risk thresholds are proposed, not official MoSPI values.")
