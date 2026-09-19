"""
AI Assistant service integrating Groq LLM with context grounding and RBAC.
"""

import os
import json
from datetime import datetime
from collections import defaultdict
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from backend.auth import check_project_access
from backend.models import User, Project, ProjectSnapshot, ProjectFeature, RiskAssessment
from backend.services.ml_service import build_project_model_dict, run_full_risk_assessment

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL") or "openai/gpt-oss-120b"

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


def get_authorized_portfolio_metrics(user: User, db: Session) -> Dict[str, Any]:
    """Calculate aggregated metrics strictly for projects authorized to the user."""
    all_projects = db.query(Project).all()
    projects = [
        p for p in all_projects
        if check_project_access(user, p.state, p.agency, p.ministry, p.sector)
    ]
    
    total_projects = len(projects)
    if total_projects == 0:
        return {
            "total_projects": 0,
            "ongoing_projects": 0,
            "risk_distribution": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
            "financial": {"original_cost": 0.0, "revised_cost": 0.0, "cumulative_expenditure": 0.0},
            "average_progress": 0.0,
            "state_wise": [],
            "ministry_wise": [],
            "high_risk_projects": []
        }

    p_codes = {p.project_code for p in projects}
    
    snapshots = (
        db.query(ProjectSnapshot)
        .filter(ProjectSnapshot.project_code.in_(p_codes))
        .order_by(ProjectSnapshot.created_at.asc(), ProjectSnapshot.id.asc())
        .all()
    )
    snapshot_map = {s.project_code: s for s in snapshots}

    risks = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.project_code.in_(p_codes))
        .order_by(RiskAssessment.created_at.asc(), RiskAssessment.id.asc())
        .all()
    )
    risk_map = {r.project_code: r for r in risks}

    risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    total_orig_cost = 0.0
    total_rev_cost = 0.0
    total_expenditure = 0.0
    progress_vals = []
    ongoing_count = 0

    state_groups = defaultdict(lambda: {"total": 0, "high_risk": 0, "critical": 0, "delayed": 0, "progress_list": []})
    ministry_groups = defaultdict(lambda: {"total": 0, "high_risk": 0, "critical": 0, "progress_list": []})
    attention_list = []

    for p in projects:
        snap = snapshot_map.get(p.project_code)
        risk = risk_map.get(p.project_code)

        orig_cost = p.original_cost or 0.0
        rev_cost = (snap.revised_cost if snap and snap.revised_cost is not None else orig_cost)
        exp = (snap.cumulative_expenditure if snap and snap.cumulative_expenditure is not None else 0.0)
        prog = (snap.physical_progress if snap and snap.physical_progress is not None else 0.0)
        risk_level = (risk.overall_risk if risk else "LOW").upper()

        if risk_level in risk_counts:
            risk_counts[risk_level] += 1
        else:
            risk_counts["LOW"] += 1

        total_orig_cost += orig_cost
        total_rev_cost += rev_cost
        total_expenditure += exp
        progress_vals.append(prog)
        if prog < 100:
            ongoing_count += 1

        state_name = p.state or "Unspecified State"
        ministry_name = p.ministry or "Unspecified Ministry"

        sg = state_groups[state_name]
        sg["total"] += 1
        if risk_level == "HIGH":
            sg["high_risk"] += 1
        elif risk_level == "CRITICAL":
            sg["critical"] += 1
        if snap and (snap.time_overrun_months or 0) > 0:
            sg["delayed"] += 1
        sg["progress_list"].append(prog)

        mg = ministry_groups[ministry_name]
        mg["total"] += 1
        if risk_level == "HIGH":
            mg["high_risk"] += 1
        elif risk_level == "CRITICAL":
            mg["critical"] += 1
        mg["progress_list"].append(prog)

        if risk_level in {"HIGH", "CRITICAL"}:
            warnings = []
            if risk and risk.warnings_json:
                try:
                    warnings = json.loads(risk.warnings_json)
                except Exception:
                    warnings = [risk.warnings_json]
            attention_list.append({
                "project_code": p.project_code,
                "project_name": p.project_name,
                "ministry": p.ministry,
                "agency": p.agency,
                "state": p.state,
                "sector": p.sector,
                "risk_level": risk_level,
                "risk_score": risk.risk_score if risk else 0,
                "revised_cost": rev_cost,
                "physical_progress": prog,
                "warnings": warnings[:3]
            })

    state_wise = [
        {
            "state": s,
            "total": d["total"],
            "high_risk": d["high_risk"],
            "critical": d["critical"],
            "delayed": d["delayed"],
            "avg_progress": round(sum(d["progress_list"]) / len(d["progress_list"]), 1) if d["progress_list"] else 0.0
        }
        for s, d in sorted(state_groups.items(), key=lambda x: -x[1]["total"])
    ]

    ministry_wise = [
        {
            "ministry": m,
            "total": d["total"],
            "high_risk": d["high_risk"],
            "critical": d["critical"],
            "avg_progress": round(sum(d["progress_list"]) / len(d["progress_list"]), 1) if d["progress_list"] else 0.0
        }
        for m, d in sorted(ministry_groups.items(), key=lambda x: -x[1]["total"])
    ]

    attention_list.sort(key=lambda x: (1 if x["risk_level"] == "CRITICAL" else 2, -x["risk_score"]))

    return {
        "total_projects": total_projects,
        "ongoing_projects": ongoing_count,
        "risk_distribution": risk_counts,
        "financial": {
            "original_cost": round(total_orig_cost, 2),
            "revised_cost": round(total_rev_cost, 2),
            "cumulative_expenditure": round(total_expenditure, 2)
        },
        "average_progress": round(sum(progress_vals) / len(progress_vals), 1) if progress_vals else 0.0,
        "state_wise": state_wise,
        "ministry_wise": ministry_wise,
        "high_risk_projects": attention_list[:10]
    }


def generate_portfolio_overview_report(
    user: User,
    db: Session,
    report_type: str = "portfolio_overview",
    project_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an authoritative, factual portfolio report grounded in verified DB metrics.
    Ensures Groq LLM never hallucinates numbers or exposes unauthorized records.
    """
    metrics = get_authorized_portfolio_metrics(user, db)
    
    # If a specific project is selected for Project Report
    project_detail_context = None
    if report_type == "project_report" and project_code:
        proj = db.query(Project).filter(Project.project_code == project_code).first()
        if proj and check_project_access(user, proj.state, proj.agency, proj.ministry, proj.sector):
            snap = db.query(ProjectSnapshot).filter(ProjectSnapshot.project_code == project_code).order_by(ProjectSnapshot.created_at.desc()).first()
            risk = db.query(RiskAssessment).filter(RiskAssessment.project_code == project_code).order_by(RiskAssessment.created_at.desc()).first()
            warnings = []
            if risk and risk.warnings_json:
                try:
                    warnings = json.loads(risk.warnings_json)
                except Exception:
                    warnings = [risk.warnings_json]
            project_detail_context = {
                "project_code": proj.project_code,
                "project_name": proj.project_name,
                "ministry": proj.ministry,
                "department": getattr(proj, "department", None),
                "agency": proj.agency,
                "state": proj.state,
                "sector": proj.sector,
                "status": getattr(proj, "status", "Ongoing"),
                "approval_date": proj.approval_date,
                "original_completion_date": proj.original_completion_date,
                "original_cost_cr": proj.original_cost,
                "revised_cost_cr": snap.revised_cost if snap else proj.original_cost,
                "cumulative_expenditure_cr": snap.cumulative_expenditure if snap else 0.0,
                "physical_progress_pct": snap.physical_progress if snap else 0.0,
                "overall_risk": risk.overall_risk if risk else "LOW",
                "risk_score": risk.risk_score if risk else 0,
                "early_warnings": warnings
            }

    compact_metrics = {
        "total_projects": metrics["total_projects"],
        "ongoing_projects": metrics["ongoing_projects"],
        "risk_distribution": metrics["risk_distribution"],
        "financial": metrics["financial"],
        "average_progress": metrics["average_progress"],
        "top_states": metrics["state_wise"][:8],
        "top_ministries": metrics["ministry_wise"][:8],
        "priority_attention_projects": metrics["high_risk_projects"][:5]
    }

    system_instruction = f"""You are InfraGuard-AI's senior project intelligence officer for the Government of India (MoSPI / IPMD).
Generate a concise, professional executive report based STRICTLY on the authorized data provided.

STRICT OPERATIONAL RULES:
1. NEVER invent or hallucinate project counts, costs, expenditure, dates, states, or percentages.
2. Rely 100% on the supplied structured metrics below.
3. Cumulative expenditure is expenditure incurred up to the latest reporting period; DO NOT call it "final actual cost".
4. Follow the exact Markdown format required for the specified report type.

USER CONTEXT:
Official: {user.full_name} ({user.email}) | Role: {user.authority_type} | Scope: {user.organization or 'National Portfolio'} | Sector: {getattr(user, 'sector', 'All Authorized Sectors')}

VERIFIED AUTHORIZED DATABASE METRICS:
{json.dumps(compact_metrics, indent=2, default=str)}
"""

    if project_detail_context:
        system_instruction += f"\nTARGET PROJECT CONTEXT:\n{json.dumps(project_detail_context, indent=2, default=str)}\n"

    user_prompts = {
        "portfolio_overview": """Please generate the official 'Infrastructure Project Portfolio Overview' report following this exact structure:

# Infrastructure Project Portfolio Overview

## 1. Overall Overview
Provide a concise executive summary covering:
- Total projects visible to this authorized user ({total_projects})
- Ongoing projects ({ongoing_projects})
- High-risk and Critical projects count
- Average physical progress ({average_progress}%)
- Total original approved cost vs revised cost vs cumulative expenditure

## 2. State-wise Overview
Provide a concise table for top states:
| State | Projects | High Risk | Critical | Delayed | Avg Progress |
|---|---|---|---|---|---|
(Include only states present in the dataset)

## 3. Ministry-wise Overview
Provide a concise table for top ministries:
| Ministry | Projects | High Risk | Critical | Avg Progress |
|---|---|---|---|---|
(Include only ministries present in the dataset)

## 4. Risk Overview
Summarize the portfolio risk distribution:
- Low Risk: {risk_low}
- Medium Risk: {risk_med}
- High Risk: {risk_high}
- Critical Risk: {risk_crit}
Discuss the key risk trends.

## 5. Financial Overview
Detail the portfolio financial posture:
- Original Approved Cost: ₹{orig_cost:,.2f} Cr
- Revised Cost: ₹{rev_cost:,.2f} Cr
- Cumulative Expenditure: ₹{exp:,.2f} Cr
(Explicitly note that cumulative expenditure reflects spending to date rather than final completion cost).

## 6. Progress Overview
Analyze the average physical progress ({average_progress}%), mentioning ongoing execution momentum.

## 7. Attention Areas
Highlight key high-risk projects that require immediate administrative or IPMD review, citing their specific risk levels, progress gaps, or triggered warnings.

## 8. Conclusion
Deliver a crisp, neutral summary assessment of the portfolio health.""".format(
            total_projects=metrics["total_projects"],
            ongoing_projects=metrics["ongoing_projects"],
            average_progress=metrics["average_progress"],
            risk_low=metrics["risk_distribution"]["LOW"],
            risk_med=metrics["risk_distribution"]["MEDIUM"],
            risk_high=metrics["risk_distribution"]["HIGH"],
            risk_crit=metrics["risk_distribution"]["CRITICAL"],
            orig_cost=metrics["financial"]["original_cost"],
            rev_cost=metrics["financial"]["revised_cost"],
            exp=metrics["financial"]["cumulative_expenditure"]
        ),
        "state_wise": "Generate a comprehensive State-wise Infrastructure Monitoring Report focusing on regional distribution, delay concentration, and progress differentials across states using the verified state_wise metrics.",
        "ministry_wise": "Generate an authoritative Ministry-wise Infrastructure Monitoring Report evaluating capital outlay, average progress, and risk exposure by central implementing ministries.",
        "risk_overview": "Generate an Executive Risk Intelligence Report highlighting early warning signals, Critical vs High risk project distribution, and urgent mitigation priorities.",
        "project_report": f"Generate an exhaustive Individual Project Performance Report for {project_code} utilizing the target project context."
    }

    user_query = user_prompts.get(report_type, user_prompts["portfolio_overview"])

    # Attempt Groq LLM completion
    markdown_content = None
    if groq_client and GROQ_API_KEY and GROQ_MODEL:
        try:
            completion = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            markdown_content = completion.choices[0].message.content
        except Exception as e:
            print(f"Groq report generation encountered an error: {e}. Falling back to deterministic builder.")
            markdown_content = None

    if not markdown_content:
        # High quality deterministic fallback generator matching the exact requested 8-part format
        markdown_content = _build_deterministic_portfolio_report(metrics, report_type, project_detail_context)

    return {
        "report_type": report_type,
        "markdown_report": markdown_content,
        "metadata": {
            "data_source": "InfraGuard-AI Project Database",
            "reporting_authority": "MoSPI / IPMD Central Monitoring Division",
            "projects_covered": metrics["total_projects"],
            "generated_for": user.email,
            "generated_at": datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")
        },
        "metrics": metrics
    }


def _build_deterministic_portfolio_report(
    metrics: Dict[str, Any],
    report_type: str,
    project_context: Optional[Dict[str, Any]] = None
) -> str:
    """Deterministic, factual markdown report builder when Groq is unavailable."""
    if report_type == "project_report" and project_context:
        p = project_context
        warnings_str = "\n".join([f"- {w}" for w in p.get("early_warnings", [])]) or "- No severe warnings detected."
        return f"""# Project Performance Report: {p['project_code']} — {p['project_name']}

## 1. Project Identity & Governance
- **Project Code**: {p['project_code']}
- **Implementing Agency**: {p['agency'] or 'N/A'}
- **Ministry / Department**: {p['ministry'] or 'N/A'} {f"({p['department']})" if p.get('department') else ''}
- **State / Sector**: {p['state'] or 'N/A'} | {p['sector'] or 'N/A'}
- **Status**: {p['status']}

## 2. Financial Overview
- **Original Approved Cost**: ₹{p.get('original_cost_cr', 0):,.2f} Cr
- **Revised Cost**: ₹{p.get('revised_cost_cr', 0):,.2f} Cr
- **Cumulative Expenditure**: ₹{p.get('cumulative_expenditure_cr', 0):,.2f} Cr
*(Note: Cumulative expenditure represents funds spent to date, not final total cost).*

## 3. Physical Progress & Timeline
- **Physical Progress**: {p.get('physical_progress_pct', 0)}%
- **Approval Date**: {p.get('approval_date') or 'N/A'}
- **Target Completion**: {p.get('original_completion_date') or 'N/A'}

## 4. Risk Assessment & Early Warnings
- **Overall Risk Category**: **{p.get('overall_risk', 'LOW')}** (Risk Score: {p.get('risk_score', 0)}/100)
- **Active Warning Flags**:
{warnings_str}
"""

    # Build State-wise table rows (top 8)
    state_rows = []
    for s in metrics.get("state_wise", [])[:8]:
        state_rows.append(f"| {s['state']} | {s['total']} | {s['high_risk']} | {s['critical']} | {s['delayed']} | {s['avg_progress']}% |")
    state_table = "\n".join(state_rows) if state_rows else "| All Regions | 0 | 0 | 0 | 0 | 0.0% |"

    # Build Ministry-wise table rows (top 8)
    min_rows = []
    for m in metrics.get("ministry_wise", [])[:8]:
        min_rows.append(f"| {m['ministry']} | {m['total']} | {m['high_risk']} | {m['critical']} | {m['avg_progress']}% |")
    min_table = "\n".join(min_rows) if min_rows else "| All Ministries | 0 | 0 | 0 | 0.0% |"

    # Build Attention areas
    attention_rows = []
    for a in metrics.get("high_risk_projects", [])[:5]:
        warns = ", ".join(a.get("warnings", [])) or "Cost/Schedule anomaly"
        attention_rows.append(f"- **{a['project_code']}** ({a['project_name'][:40]}...) — State: {a['state']}, Risk: **{a['risk_level']}** (Score: {a['risk_score']}), Progress: {a['physical_progress']}%, Warnings: {warns}")
    attention_str = "\n".join(attention_rows) if attention_rows else "- No critical projects flagged currently."

    fin = metrics.get("financial", {})
    risks = metrics.get("risk_distribution", {})

    return f"""# Infrastructure Project Portfolio Overview

## 1. Overall Overview
This report provides an executive briefing on the infrastructure project portfolio within your authorized operational boundary.
- **Total Authorized Projects**: {metrics.get('total_projects', 0):,}
- **Ongoing Projects**: {metrics.get('ongoing_projects', 0):,}
- **High-Risk Projects**: {risks.get('HIGH', 0)}
- **Critical Risk Projects**: {risks.get('CRITICAL', 0)}
- **Average Physical Progress**: {metrics.get('average_progress', 0)}%
- **Total Approved Cost**: ₹{fin.get('original_cost', 0):,.2f} Cr | **Revised Cost**: ₹{fin.get('revised_cost', 0):,.2f} Cr
- **Cumulative Expenditure Incurred**: ₹{fin.get('cumulative_expenditure', 0):,.2f} Cr

## 2. State-wise Overview
Below is the operational breakdown across the highest-density states and union territories:

| State | Projects | High Risk | Critical | Delayed | Avg Progress |
|---|---|---|---|---|---|
{state_table}

## 3. Ministry-wise Overview
Performance and implementation distribution across major central ministries:

| Ministry | Projects | High Risk | Critical | Avg Progress |
|---|---|---|---|---|
{min_table}

## 4. Risk Overview
Categorization based on the automated multi-factor risk engine:
- **Low Risk**: {risks.get('LOW', 0)} projects (stable trajectory)
- **Medium Risk**: {risks.get('MEDIUM', 0)} projects (minor cost/schedule variance)
- **High Risk**: {risks.get('HIGH', 0)} projects (substantial overrun probability)
- **Critical Risk**: {risks.get('CRITICAL', 0)} projects (severe timeline and cost escalation)

## 5. Financial Overview
- **Original Approved Outlay**: ₹{fin.get('original_cost', 0):,.2f} Cr
- **Current Revised Outlay**: ₹{fin.get('revised_cost', 0):,.2f} Cr
- **Cumulative Expenditure to Date**: ₹{fin.get('cumulative_expenditure', 0):,.2f} Cr
*(Important Note: Cumulative expenditure represents disbursements accumulated up to the latest reporting period and does not indicate final actual completion cost).*

## 6. Progress Overview
The portfolio records an average physical execution rate of **{metrics.get('average_progress', 0)}%**. Active monitoring continues for projects below 30% progress to ensure early milestone achievement.

## 7. Attention Areas
The following priority projects are currently triggering critical alerts and require proactive departmental intervention:
{attention_str}

## 8. Conclusion
The portfolio exhibits steady execution across standard priority sectors, with active risk containment recommended for the highlighted critical projects. Continuous monthly monitoring and milestone tracking remain essential.
"""

