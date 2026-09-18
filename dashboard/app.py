"""
InfraGuard-AI — Integrated Project Monitoring Dashboard
Main application entry point.
"""

import streamlit as st
import sys
import os

# Setup path for auth imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dashboard.auth_ui import require_auth, show_user_profile

st.set_page_config(
    page_title="InfraGuard-AI | PAIMANA Project Monitor",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Enforce authentication
require_auth()

# Show user profile in sidebar
show_user_profile()

# ── Custom CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Government-style professional theme */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1a237e 0%, #0d47a1 50%, #01579b 100%);
        color: white;
        padding: 1.2rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .main-header p {
        margin: 0.3rem 0 0 0;
        font-size: 0.9rem;
        opacity: 0.85;
    }

    /* KPI card styling */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #1a237e;
        transition: transform 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
    }
    .kpi-card .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1a237e;
        margin: 0.3rem 0;
    }
    .kpi-card .kpi-label {
        font-size: 0.8rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 500;
    }

    /* Risk badges */
    .risk-low { background: #e8f5e9; color: #2e7d32; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }
    .risk-medium { background: #fff3e0; color: #e65100; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }
    .risk-high { background: #ffebee; color: #c62828; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }
    .risk-critical { background: #b71c1c; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }

    /* Section headers */
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a237e;
        border-bottom: 2px solid #e3f2fd;
        padding-bottom: 0.5rem;
        margin: 1.5rem 0 1rem 0;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e8eaf6 100%);
    }
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #1a237e;
        font-size: 0.9rem;
        font-weight: 600;
    }

    /* Table improvements */
    .dataframe {
        font-size: 0.85rem !important;
    }

    /* Warning/Alert boxes */
    .warning-box {
        background: #fff8e1;
        border-left: 4px solid #ffa000;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🏗️ InfraGuard-AI</h1>
    <p>PAIMANA — Integrated Infrastructure Project Monitoring & AI-Powered Risk Intelligence Platform</p>
</div>
""", unsafe_allow_html=True)

# ── Landing page content ────────────────────────────────────────────────
st.markdown("### Welcome to InfraGuard-AI")
st.write(
    "Use the **sidebar navigation** (← pages listed on the left) to explore the platform. "
    "Select a page from the sidebar to get started."
)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-label">📊 Portfolio Overview</div>
        <div style="font-size:0.9rem; margin-top:0.5rem;">KPI dashboard with project statistics, risk distribution, and geographic analysis.</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-label">⚠️ Risk & Early Warnings</div>
        <div style="font-size:0.9rem; margin-top:0.5rem;">AI-powered risk scoring with cost overrun, time overrun, and progress mismatch detection.</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-label">🤖 AI Assistant</div>
        <div style="font-size:0.9rem; margin-top:0.5rem;">Ask natural language questions about projects, risks, and performance metrics.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.caption("InfraGuard-AI | SIH 2026 | Problem Statement 26103 | Prototype — All thresholds are proposed, not official MoSPI values.")
