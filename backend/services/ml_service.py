"""
ML Service connecting Member 3 (Cost), Member 4 (Time), and Member 5 (Risk Engine).
"""

import os
import sys
from typing import Dict, Any

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.models.cost_model import predict_project_cost_risk
from src.models.time_model import predict_time_risk

def build_project_model_dict(project, snapshot, feature) -> Dict[str, Any]:
    """Assemble a unified dictionary matching the ML models' expected schema."""
    d = {
        "project_code": project.project_code,
        "project_name": project.project_name,
        "agency": project.agency,
        "state": project.state,
        "sector": project.sector or "Other",
        "original_cost": project.original_cost,
        "revised_cost": snapshot.revised_cost if snapshot else project.original_cost,
        "cumulative_expenditure": snapshot.cumulative_expenditure if snapshot else 0.0,
        "physical_progress": snapshot.physical_progress if snapshot else 0.0,
        "project_age_days": feature.project_age_days if feature else 365,
        "original_duration_days": feature.original_duration_days if feature else 730,
        "revised_duration_days": feature.revised_duration_days if feature else 730,
        "expenditure_percent": feature.expenditure_percent if feature else 0.0,
        "progress_gap": feature.progress_gap if feature else 0.0,
        "cost_change": feature.cost_change if feature else 0.0,
        "cost_change_percent": feature.cost_change_percent if feature else 0.0,
        "project_size_category": feature.project_size_category if feature else "Medium",
        "progress_change_1m": 0.0,
        "expenditure_change_1m": 0.0,
        "expenditure_per_progress": 0.0
    }

    # Safe expenditure percent: cumulative_expenditure / revised_cost * 100
    rev_cost = d["revised_cost"]
    cum_exp = d["cumulative_expenditure"]
    if rev_cost and rev_cost > 0 and cum_exp is not None:
        d["safe_expenditure_percent"] = (cum_exp / rev_cost) * 100
    else:
        d["safe_expenditure_percent"] = d.get("expenditure_percent", 0.0)

    # Safe progress gap: safe_expenditure_percent - physical_progress
    d["safe_progress_gap"] = (d["safe_expenditure_percent"] or 0.0) - (d["physical_progress"] or 0.0)
    return d

def predict_project_risk(project_dict: Dict[str, Any]) -> Dict[str, Any]:
    score = 0
    warnings_list = []
    
    # Run Cost Model
    cost_res = predict_project_cost_risk(project_dict)
    cost_overrun_pct = cost_res.get("cost_overrun_percent", 0.0)
    
    cost_risk_level = "LOW"
    if cost_overrun_pct > 50:
        score += 40
        warnings_list.append("Critical Cost Overrun Predicted")
        cost_risk_level = "HIGH"
    elif cost_overrun_pct > 20:
        score += 30
        warnings_list.append("High Cost Overrun Predicted")
        cost_risk_level = "HIGH"
    elif cost_overrun_pct > 5:
        score += 15
        cost_risk_level = "MEDIUM"
        
    # Run Time Model
    time_res = predict_time_risk(project_dict)
    time_overrun_pct = 0.0
    if time_res.get("is_time_overrun"):
        time_overrun_pct = 25.0
        
    time_risk_level = time_res.get("risk_level", "LOW")
    if time_risk_level == "HIGH":
        score += 30
        warnings_list.append("High Time Overrun Predicted")
    elif time_risk_level == "MEDIUM":
        score += 15

    # Progress Mismatch
    exp_pct = project_dict.get("safe_expenditure_percent", 0)
    prog = project_dict.get("physical_progress", 0)
    gap = exp_pct - prog
    if gap > 40:
        score += 20
        warnings_list.append("Severe Expenditure/Progress Mismatch")
    elif gap > 20:
        score += 10
        warnings_list.append("High Expenditure relative to Progress")
        
    score = min(score, 100)
    
    if score >= 75: overall = "CRITICAL"
    elif score >= 50: overall = "HIGH"
    elif score >= 25: overall = "MEDIUM"
    else: overall = "LOW"
    
    return {
        "project_code": project_dict.get("project_code"),
        "risk_score": score,
        "overall_risk": overall,
        "warnings": warnings_list,
        "explanation": "Calculated based on real-time cost and time models.",
        "cost_model_output": {
            "risk_level": cost_risk_level,
            "expected_overrun_percent": round(float(cost_overrun_pct), 1),
            "is_cost_overrun": bool(cost_overrun_pct > 0),
            "predicted_total_cost": round(float(cost_res.get("predicted_total_cost", 0.0)), 2)
        },
        "time_model_output": time_res
    }

def run_full_risk_assessment(project_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Execute M3, M4, and M5 pipeline on a project dictionary."""
    return predict_project_risk(project_dict)
