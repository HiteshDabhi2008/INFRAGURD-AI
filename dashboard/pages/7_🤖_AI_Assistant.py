"""
AI Assistant — Data-grounded chatbot using Groq LLM for project monitoring questions.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import json
import warnings
warnings.filterwarnings("ignore")

from data_loader import get_merged_data, load_early_warnings

st.set_page_config(page_title="AI Assistant | InfraGuard-AI", page_icon="🤖", layout="wide")

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


# ── Page Header ─────────────────────────────────────────────────────────
st.markdown("""
<div style="background: linear-gradient(135deg, #283593 0%, #3949ab 50%, #5c6bc0 100%); color: white; padding: 1rem 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
    <h2 style="margin:0;">🤖 AI Assistant</h2>
    <p style="margin:0.2rem 0 0 0; opacity:0.85; font-size:0.9rem;">Ask questions about infrastructure projects, risks, and performance — powered by real data</p>
</div>
""", unsafe_allow_html=True)

# ── Load Data ───────────────────────────────────────────────────────────
df = get_merged_data()
ew_df = load_early_warnings()

if df.empty:
    st.error("❌ No project data available.")
    st.stop()

# ── Check for Groq API ──────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

groq_key = os.environ.get("GROQ_API_KEY", "")

if not groq_key:
    st.warning("⚠️ GROQ_API_KEY not found in environment. Set it in the `.env` file.")
    st.info("The AI Assistant requires a Groq API key to function. Add `GROQ_API_KEY=your_key` to the `.env` file in the project root.")
    st.stop()


def build_data_context(question: str, df: pd.DataFrame, ew_df: pd.DataFrame) -> str:
    """
    Build a data context string based on the user's question.
    Retrieves real data to ground the LLM's response.
    """
    context_parts = []
    q = question.lower()

    # Portfolio summary (always included)
    context_parts.append(f"PORTFOLIO SUMMARY:")
    context_parts.append(f"- Total projects: {len(df)}")
    context_parts.append(f"- Total original cost: ₹{df['original_cost'].sum():,.2f} Cr")
    context_parts.append(f"- Total revised cost: ₹{df['revised_cost'].sum():,.2f} Cr")
    context_parts.append(f"- Total expenditure: ₹{df['cumulative_expenditure'].sum():,.2f} Cr")
    context_parts.append(f"- Average physical progress: {df['physical_progress'].mean():.1f}%")
    context_parts.append(f"- Number of states: {df['state'].nunique()}")
    context_parts.append(f"- Number of agencies: {df['agency'].nunique()}")

    # Risk info
    if not ew_df.empty and "overall_risk" in ew_df.columns:
        all_codes = set(df["project_code"].unique())
        warned_codes = set(ew_df["project_code"].unique())

        risk_counts = ew_df["overall_risk"].value_counts().to_dict()
        low_count = len(all_codes - warned_codes) + risk_counts.get("LOW", 0)
        context_parts.append(f"\nRISK DISTRIBUTION:")
        context_parts.append(f"- LOW: {low_count}")
        context_parts.append(f"- MEDIUM: {risk_counts.get('MEDIUM', 0)}")
        context_parts.append(f"- HIGH: {risk_counts.get('HIGH', 0)}")
        context_parts.append(f"- CRITICAL: {risk_counts.get('CRITICAL', 0)}")

    # If asking about high risk
    if any(term in q for term in ["high risk", "critical", "risky", "danger", "warning", "alert"]):
        if not ew_df.empty and "overall_risk" in ew_df.columns:
            high = ew_df[ew_df["overall_risk"].isin(["HIGH", "CRITICAL"])]
            if not high.empty:
                high_merged = pd.merge(high[["project_code", "overall_risk", "cost_risk_level", "time_risk_level", "explanation"]],
                                       df[["project_code", "project_name", "state", "physical_progress"]].drop_duplicates(subset=["project_code"]),
                                       on="project_code", how="left")
                context_parts.append(f"\nHIGH/CRITICAL RISK PROJECTS ({len(high_merged)}):")
                for _, r in high_merged.head(10).iterrows():
                    context_parts.append(f"  - {r.get('project_name','N/A')[:60]} (Code: {r['project_code']}, State: {r.get('state','N/A')}, Risk: {r['overall_risk']}, Progress: {r.get('physical_progress','N/A')}%)")

    # If asking about a specific state
    for state_name in df["state"].dropna().unique():
        if state_name.lower() in q:
            state_df = df[df["state"] == state_name]
            context_parts.append(f"\nSTATE: {state_name}")
            context_parts.append(f"- Projects: {len(state_df)}")
            context_parts.append(f"- Avg Progress: {state_df['physical_progress'].mean():.1f}%")
            context_parts.append(f"- Total Revised Cost: ₹{state_df['revised_cost'].sum():,.2f} Cr")
            # Top projects
            for _, r in state_df.head(5).iterrows():
                context_parts.append(f"  - {r.get('project_name','N/A')[:60]} (Code: {r['project_code']}, Progress: {r.get('physical_progress','N/A')}%)")
            break

    # If asking about a specific project
    if any(term in q for term in ["project code", "project id"]):
        # Try to extract a number
        import re
        codes = re.findall(r'\d{5,7}', q)
        for code in codes:
            proj = df[df["project_code"].astype(str) == code]
            if not proj.empty:
                r = proj.iloc[0]
                context_parts.append(f"\nPROJECT {code}:")
                context_parts.append(f"- Name: {r.get('project_name', 'N/A')}")
                context_parts.append(f"- State: {r.get('state', 'N/A')}")
                context_parts.append(f"- Agency: {r.get('agency', 'N/A')}")
                context_parts.append(f"- Original Cost: ₹{r.get('original_cost', 'N/A')} Cr")
                context_parts.append(f"- Revised Cost: ₹{r.get('revised_cost', 'N/A')} Cr")
                context_parts.append(f"- Expenditure: ₹{r.get('cumulative_expenditure', 'N/A')} Cr")
                context_parts.append(f"- Physical Progress: {r.get('physical_progress', 'N/A')}%")
                
                # Check ew_df for predictions
                ew_proj = ew_df[ew_df["project_code"].astype(str) == code]
                if not ew_proj.empty:
                    er = ew_proj.iloc[0]
                    context_parts.append(f"- Risk Score: {er.get('risk_score', 'N/A')}/100")
                    context_parts.append(f"- Overall Risk Level: {er.get('overall_risk', 'N/A')}")
                    context_parts.append(f"- Cost Risk Level (ML): {er.get('cost_risk_level', 'N/A')}")
                    context_parts.append(f"- Time Risk Level (ML): {er.get('time_risk_level', 'N/A')}")
                    if pd.notna(er.get('explanation')):
                        context_parts.append(f"- Risk Explanation: {er.get('explanation')}")

    # If asking about expenditure vs progress mismatch
    if any(term in q for term in ["expenditure", "mismatch", "spending", "gap"]):
        exp_col = "safe_expenditure_percent" if "safe_expenditure_percent" in df.columns else "expenditure_percent"
        if exp_col in df.columns and "physical_progress" in df.columns:
            gap_df = df[[exp_col, "physical_progress", "project_code", "project_name", "state"]].dropna()
            gap_df["gap"] = gap_df[exp_col] - gap_df["physical_progress"]
            worst = gap_df.nlargest(5, "gap")
            context_parts.append(f"\nWORST EXPENDITURE-PROGRESS GAPS:")
            for _, r in worst.iterrows():
                context_parts.append(f"  - {r.get('project_name','N/A')[:50]} (Code: {r['project_code']}, Exp: {r[exp_col]:.1f}%, Progress: {r['physical_progress']:.1f}%, Gap: {r['gap']:.1f}%)")

    # If asking about sectors
    if any(term in q for term in ["sector", "industry", "category"]):
        if "sector" in df.columns:
            sec = df.groupby("sector").agg(
                count=("project_code", "count"),
                avg_progress=("physical_progress", "mean"),
                total_cost=("revised_cost", "sum"),
            ).sort_values("count", ascending=False).head(10)
            context_parts.append(f"\nSECTOR BREAKDOWN:")
            for sector, row in sec.iterrows():
                context_parts.append(f"  - {sector}: {row['count']} projects, {row['avg_progress']:.1f}% avg progress, ₹{row['total_cost']:,.0f} Cr")

    return "\n".join(context_parts)


def call_groq(question: str, data_context: str) -> str:
    """Call Groq API to generate a response."""
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)

        system_prompt = """You are InfraGuard-AI, an expert assistant for the PAIMANA infrastructure project monitoring platform.

CRITICAL RULES:
1. Answer ONLY based on the data context provided below. Never invent statistics, project names, or numbers.
2. If the data context does not contain information to answer the question, say "I don't have enough data to answer that question accurately."
3. All monetary values are in Indian Rupees (₹) Crores.
4. Risk thresholds are PROTOTYPE/PROPOSED — always mention this if discussing risk methodology.
5. Be concise and professional. Use bullet points for lists.
6. If asked about methodology, refer to the risk engine documentation, not your own knowledge.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"DATA CONTEXT:\n{data_context}\n\nUSER QUESTION: {question}"},
        ]

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )

        return response.choices[0].message.content

    except ImportError:
        return "❌ The `groq` Python package is not installed. Run: `pip install groq`"
    except Exception as e:
        return f"❌ Error calling Groq API: {str(e)}"


# ── Chat Interface ──────────────────────────────────────────────────────
st.markdown("**Ask me anything about the infrastructure projects:**")

# Example questions
with st.expander("💡 Example Questions"):
    st.markdown("""
    - Which projects are high risk?
    - Which state has the most projects?
    - Show me the projects with high expenditure but low physical progress
    - What is the overall cost escalation?
    - How many projects are in Maharashtra?
    - What sectors have the most projects?
    - Tell me about project code 612786
    """)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask about projects, risks, costs, or progress..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing data and generating response..."):
            data_context = build_data_context(prompt, df, ew_df)
            response = call_groq(prompt, data_context)
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

# ── Footer ──────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("InfraGuard-AI Assistant | Responses are grounded in actual project data. Prototype — not for official decision-making.")
