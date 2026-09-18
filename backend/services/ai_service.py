"""
AI Assistant service integrating Groq LLM with context grounding and RBAC.
"""

import os
import json
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from backend.models import User, Project, ProjectSnapshot, ProjectFeature, RiskAssessment
from backend.services.ml_service import build_project_model_dict, run_full_risk_assessment

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")

try:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except Exception:
    groq_client = None


def groq_health() -> Dict[str, Any]:
    if not GROQ_API_KEY or not GROQ_MODEL or groq_client is None:
        return {
            "configured": False,
            "model": GROQ_MODEL,
            "reachable": False,
            "status": "not_configured",
        }

    try:
        groq_client.models.list()
        return {
            "configured": True,
            "model": GROQ_MODEL,
            "reachable": True,
            "status": "healthy",
        }
    except Exception:
        return {
            "configured": True,
            "model": GROQ_MODEL,
            "reachable": False,
            "status": "error",
        }


def answer_user_query(
    query: str,
    user: User,
    db: Session,
    project_code: Optional[str] = None,
    state: Optional[str] = None,
    ministry: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an authoritative, factual answer grounded in real database records
    and ML risk predictions.
    """
    # 1. Retrieve authorized contextual facts based on the query and user scope
    context_data = _gather_context(db, user, query, project_code, state, ministry)

    # 2. Build structured system prompt
    system_prompt = f"""You are InfraGuard-AI, an expert AI monitoring assistant for the Government of India (MoSPI / IPMD).
Your mission is to provide accurate, proactive, data-grounded decision support on national infrastructure projects.

CURRENT USER CONTEXT:
- Official: {user.full_name} ({user.email})
- Role: {user.authority_type}
- Scope: {user.organization or 'National Portfolio'}, Region: {user.state_region or 'All India'}

FACTUAL DATA RETRIEVED FROM INFRAGUARD-AI DATABASE:
{json.dumps(context_data, indent=2, default=str)}

INSTRUCTIONS:
1. ONLY make claims supported by the factual data provided above.
2. If the user asks why a project is high or critical risk, cite the specific Cost Risk, Schedule Delay, Progress Gap, and Early Warnings.
3. For numerical values, state the exact numbers from the context (e.g. ₹ Crore, %, months).
4. If asked about something not in the context, clearly say: "Data not available in current PAIMANA report".
5. Provide crisp, structured, professional responses with bullet points where appropriate.
"""

    if not groq_client or not GROQ_API_KEY:
        raise RuntimeError("Groq AI is unavailable: GROQ_API_KEY is not configured")
    if not GROQ_MODEL:
        raise RuntimeError("Groq AI is unavailable: GROQ_MODEL is not configured")

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.2,
            max_tokens=800
        )
        answer = completion.choices[0].message.content
        return {
            "answer": answer,
            "context_used": context_data
        }
    except Exception as e:
        raise RuntimeError(f"Groq API request failed: {e}") from e


def _gather_context(
    db: Session,
    user: User,
    query: str,
    project_code: Optional[str],
    state: Optional[str],
    ministry: Optional[str]
) -> Dict[str, Any]:
    """Gather authorized facts from the database."""
    context = {}

    # If specific project is referenced
    target_code = project_code
    if not target_code:
        # Check if project code is mentioned in query (e.g. 612786, 400138)
        import re
        codes = re.findall(r'\b\d{6}\b', query)
        if codes:
            target_code = codes[0]

    if target_code:
        project = db.query(Project).filter(Project.project_code == target_code).first()
        if project:
            latest_snap = (
                db.query(ProjectSnapshot)
                .filter(ProjectSnapshot.project_code == target_code)
                .order_by(ProjectSnapshot.report_month.desc())
                .first()
            )
            feature = (
                db.query(ProjectFeature)
                .filter(ProjectFeature.project_code == target_code)
                .first()
            )
            # Run or get risk assessment
            p_dict = build_project_model_dict(project, latest_snap, feature)
            risk = run_full_risk_assessment(p_dict)

            # Get historical snapshots
            history = (
                db.query(ProjectSnapshot)
                .filter(ProjectSnapshot.project_code == target_code)
                .all()
            )

            context["focused_project"] = {
                "project_code": project.project_code,
                "project_name": project.project_name,
                "agency": project.agency,
                "state": project.state,
                "sector": project.sector,
                "original_cost_cr": project.original_cost,
                "revised_cost_cr": latest_snap.revised_cost if latest_snap else project.original_cost,
                "expenditure_cr": latest_snap.cumulative_expenditure if latest_snap else 0,
                "physical_progress_pct": latest_snap.physical_progress if latest_snap else 0,
                "progress_gap_pct": (latest_snap.cumulative_expenditure / (latest_snap.revised_cost or 1) * 100 - (latest_snap.physical_progress or 0)) if latest_snap else 0,
                "overall_risk": risk.get("overall_risk"),
                "risk_score": risk.get("risk_score"),
                "early_warnings": risk.get("warnings", []),
                "cost_model": risk.get("cost_model_output", {}),
                "time_model": risk.get("time_model_output", {}),
                "historical_months_available": [h.report_month for h in history]
            }
            return context

    # If general or regional query
    query_lower = query.lower()
    proj_query = db.query(Project)

    # Scoping
    if user.authority_type == "State Authority" and user.state_region:
        proj_query = proj_query.filter(Project.state.ilike(f"%{user.state_region}%"))
    elif state and state != "All":
        proj_query = proj_query.filter(Project.state.ilike(f"%{state}%"))

    if user.authority_type == "Ministry Authority" and user.organization:
        proj_query = proj_query.filter(Project.ministry.ilike(f"%{user.organization}%"))

    # Top high risk projects in scope
    high_risks = (
        db.query(Project, RiskAssessment, ProjectSnapshot)
        .join(RiskAssessment, Project.project_code == RiskAssessment.project_code)
        .join(ProjectSnapshot, (Project.project_code == ProjectSnapshot.project_code) & (ProjectSnapshot.report_month == RiskAssessment.report_month))
        .filter(RiskAssessment.overall_risk.in_(["CRITICAL", "HIGH"]))
        .limit(10)
        .all()
    )

    context["high_risk_projects_summary"] = [
        {
            "code": p.project_code,
            "name": p.project_name[:40] + "...",
            "agency": p.agency,
            "state": p.state,
            "risk": r.overall_risk,
            "score": r.risk_score,
            "cost_cr": s.revised_cost,
            "progress_pct": s.physical_progress,
            "warnings": json.loads(r.warnings_json) if r.warnings_json else []
        }
        for p, r, s in high_risks
    ]

    total_count = proj_query.count()
    context["portfolio_summary"] = {
        "total_projects_in_scope": total_count,
        "high_risk_count": db.query(RiskAssessment).filter(RiskAssessment.overall_risk == "HIGH").count(),
        "critical_count": db.query(RiskAssessment).filter(RiskAssessment.overall_risk == "CRITICAL").count(),
    }

    return context


def _generate_fallback_response(query: str, context: Dict[str, Any]) -> str:
    """Deterministic fallback answer based on structured context."""
    if "focused_project" in context:
        p = context["focused_project"]
        warnings_str = "\n".join([f"- {w}" for w in p.get("early_warnings", [])])
        return f"""### Project Analysis: {p['project_code']} — {p['project_name']}

- **State / Agency**: {p['state']} | {p['agency']}
- **Original Cost**: ₹{p.get('original_cost_cr', 0):,.2f} Cr | **Revised Cost**: ₹{p.get('revised_cost_cr', 0):,.2f} Cr
- **Cumulative Expenditure**: ₹{p.get('expenditure_cr', 0):,.2f} Cr
- **Physical Progress**: {p.get('physical_progress_pct', 0)}%
- **Overall Risk Category**: **{p.get('overall_risk', 'LOW')}** (Risk Score: {p.get('risk_score', 0)})

**Cost Model Output**:
- Risk Level: {p.get('cost_model', {}).get('risk_level', 'N/A')}
- Overrun Probability: {p.get('cost_model', {}).get('overrun_probability', 0)*100:.1f}%
- Expected Overrun: {p.get('cost_model', {}).get('expected_overrun_percent', 0)}%

**Time Model Output**:
- Risk Level: {p.get('time_model', {}).get('risk_level', 'N/A')}
- Delay Probability: {p.get('time_model', {}).get('overrun_probability', 0)*100:.1f}%
- Expected Delay: {p.get('time_model', {}).get('expected_overrun_months', 0)} months

**Triggered Early Warnings**:
{warnings_str or 'No severe early warnings active.'}
"""
    elif "high_risk_projects_summary" in context:
        summary = context.get("portfolio_summary", {})
        projects = context.get("high_risk_projects_summary", [])
        lines = [f"- **{p['code']}** ({p['name']}) — State: {p['state']}, Agency: {p['agency']}, Risk: **{p['risk']}**, Cost: ₹{p['cost_cr']} Cr, Progress: {p['progress_pct']}%" for p in projects[:5]]
        return f"""### Portfolio Risk Overview

- **Total Projects in Scope**: {summary.get('total_projects_in_scope', 0):,}
- **Critical Risk Projects**: {summary.get('critical_count', 0)}
- **High Risk Projects**: {summary.get('high_risk_count', 0)}

**Top Monitored High-Risk Projects**:
{chr(10).join(lines)}

*Ask about any specific project code (e.g., 'Why is 612786 high risk?') for a deep dive.*
"""
    return "InfraGuard-AI retrieved portfolio context. Please specify a project code or region for detailed risk analysis."
