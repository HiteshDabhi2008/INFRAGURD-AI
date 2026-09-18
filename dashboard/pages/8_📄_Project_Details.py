import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Setup path for imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dashboard.auth_ui import require_auth, show_user_profile
from dashboard.data_loader import get_merged_data, apply_filters, get_risk_prediction, prepare_project_dict

st.set_page_config(
    page_title="Project Details | InfraGuard-AI",
    page_icon="📄",
    layout="wide",
)

# Enforce authentication
require_auth()
show_user_profile()

st.title("📄 Project Detail & AI Forecast")
st.markdown("In-depth analysis of a specific infrastructure project, including historical performance and AI-driven cost/time predictions.")

@st.cache_data(ttl=600)
def load_historical_data():
    hist_path = os.path.join(BASE_DIR, "data", "processed", "paimana_historical.csv")
    if os.path.exists(hist_path):
        return pd.read_csv(hist_path)
    return pd.DataFrame()

merged_data = get_merged_data()
historical_data = load_historical_data()

if merged_data.empty:
    st.warning("No project data available.")
    st.stop()

# Build search/select dropdown
st.markdown("### Select Project")
# Filter by user role if needed
user = st.session_state["user"]
df_filtered = merged_data.copy()
if user["authority_type"] == "Ministry Authority" and user.get("organization"):
    df_filtered = df_filtered[df_filtered["ministry"] == user["organization"]]
elif user["authority_type"] == "State Authority" and user.get("state_region"):
    df_filtered = df_filtered[df_filtered["state"] == user["state_region"]]
elif user["authority_type"] == "Agency / Project Authority" and user.get("organization"):
    df_filtered = df_filtered[df_filtered["agency"] == user["organization"]]

if df_filtered.empty:
    st.warning("No projects found matching your assigned role restrictions.")
    st.stop()

# Create a formatting string for dropdown
df_filtered["dropdown_label"] = df_filtered["project_code"].astype(str) + " - " + df_filtered["project_name"]
selected_label = st.selectbox("Search by Project Code or Name", df_filtered["dropdown_label"].tolist())

if selected_label:
    # Get the selected project row
    proj_code = selected_label.split(" - ")[0]
    project_row = df_filtered[df_filtered["project_code"].astype(str) == str(proj_code)].iloc[0]
    
    st.markdown("---")
    
    # Header KPIs
    st.subheader(f"{project_row['project_name']}")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Project Code", proj_code)
    col2.metric("Agency", project_row.get("agency", "N/A"))
    col3.metric("State", project_row.get("state", "N/A"))
    col4.metric("Sector", project_row.get("sector", "N/A"))
    
    st.markdown("---")
    
    # Get historical data for this project
    if not historical_data.empty:
        proj_hist = historical_data[historical_data["project_code"].astype(str) == str(proj_code)].copy()
        if not proj_hist.empty:
            proj_hist = proj_hist.sort_values(by="report_date")
            
            st.markdown("### 📊 4-Month Historical Performance")
            
            hc1, hc2 = st.columns(2)
            
            # Chart 1: Progress vs Month
            with hc1:
                fig_prog = px.line(
                    proj_hist, x="report_month", y="physical_progress",
                    markers=True, title="Physical Progress (%) Over Time",
                    labels={"report_month": "Month", "physical_progress": "Progress (%)"}
                )
                fig_prog.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig_prog, use_container_width=True)
                
            # Chart 2: Expenditure vs Month
            with hc2:
                fig_exp = px.bar(
                    proj_hist, x="report_month", y="cumulative_expenditure",
                    title="Cumulative Expenditure (₹ Cr) Over Time",
                    labels={"report_month": "Month", "cumulative_expenditure": "Expenditure (₹ Cr)"}
                )
                if "revised_cost" in proj_hist.columns:
                    latest_cost = proj_hist["revised_cost"].iloc[-1]
                    if pd.notna(latest_cost) and latest_cost > 0:
                        fig_exp.add_hline(y=latest_cost, line_dash="dash", line_color="red", annotation_text="Revised Cost")
                st.plotly_chart(fig_exp, use_container_width=True)
                
    else:
        st.info("No historical data available for charts.")
        
    st.markdown("---")
    
    # AI Predictions & Risk Engine
    st.markdown("### 🧠 AI Predictive Risk Engine")
    
    with st.spinner("Running AI models for risk forecasting..."):
        p_dict = prepare_project_dict(project_row)
        risk_res = get_risk_prediction(p_dict)
    
    rc1, rc2, rc3 = st.columns([1, 1, 1])
    
    with rc1:
        st.markdown("#### Cost Forecast")
        cost_out = risk_res.get("cost_model_output", {})
        c_risk = cost_out.get("risk_level", "UNKNOWN")
        c_prob = cost_out.get("overrun_probability", 0)
        c_overrun = cost_out.get("expected_overrun_percent", 0)
        
        st.metric("Cost Risk", c_risk)
        if c_prob is not None:
            st.write(f"**Overrun Probability:** {c_prob*100:.1f}%")
        if c_overrun is not None:
            st.write(f"**Expected Overrun:** {c_overrun:.1f}%")
            
    with rc2:
        st.markdown("#### Time Forecast")
        time_out = risk_res.get("time_model_output", {})
        t_risk = time_out.get("risk_level", "UNKNOWN")
        t_prob = time_out.get("overrun_probability", 0)
        t_overrun = time_out.get("expected_overrun_months", 0)
        
        st.metric("Time Risk", t_risk)
        if t_prob is not None:
            st.write(f"**Overrun Probability:** {t_prob*100:.1f}%")
        if t_overrun is not None:
            st.write(f"**Expected Overrun:** {t_overrun:.1f} months")
            
    with rc3:
        st.markdown("#### Overall Risk Assessment")
        overall = risk_res.get("overall_risk", "UNKNOWN")
        score = risk_res.get("risk_score", 0)
        
        color = "green"
        if overall == "MEDIUM": color = "orange"
        elif overall == "HIGH": color = "red"
        elif overall == "CRITICAL": color = "darkred"
        
        st.markdown(f"<h3 style='color: {color};'>{overall}</h3>", unsafe_allow_html=True)
        st.write(f"**Risk Score:** {score}/100")
        
    st.markdown("#### ⚠️ Early Warnings")
    warnings = risk_res.get("warnings", [])
    if warnings:
        for w in warnings:
            st.markdown(f"""<div class="warning-box">🔴 {w}</div>""", unsafe_allow_html=True)
    else:
        st.success("No early warnings detected for this project.")
        
    if risk_res.get("explanation"):
        with st.expander("View Risk Explanation"):
            st.write(risk_res["explanation"])
