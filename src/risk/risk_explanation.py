"""
risk_explanation.py - Member 5
============================================================
Generates human-readable explanations for project risks based on active warnings.
"""

def generate_explanation(row, warnings):
    project_name = row.get('project_code', 'Unknown Project')
    risk_category = row.get('risk_category', 'LOW')
    
    if risk_category == "LOW" or not warnings:
        return f"Project {project_name} is classified as LOW risk. Progress and expenditure appear to be within normal thresholds."
    
    explanation_parts = [
        f"Project {project_name} is classified as {risk_category} risk because"
    ]
    
    reasons = []
    # Parse warnings to human readable clauses
    if "Predicted cost overrun is high." in warnings:
        reasons.append("the predicted total cost is significantly above the baseline")
    if "Predicted completion is significantly later than planned." in warnings:
        reasons.append("the projected completion date exceeds the planned schedule")
    if "Expenditure is high compared with physical progress." in warnings:
        reasons.append("expenditure is high relative to the physical progress achieved")
    if "Physical progress is low despite high project age." in warnings:
        reasons.append("physical progress is severely lagging given the project's age")
        
    if not reasons:
        reasons.append("there are multiple underlying risk indicators")
        
    if len(reasons) == 1:
        explanation_parts.append(reasons[0] + ".")
    elif len(reasons) == 2:
        explanation_parts.append(reasons[0] + " and " + reasons[1] + ".")
    else:
        explanation_parts.append(", ".join(reasons[:-1]) + ", and " + reasons[-1] + ".")
        
    return " ".join(explanation_parts)
