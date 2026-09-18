"""
risk_rules.py - Member 5
============================================================
Configurable rules for the Early Warning Engine.
"""

import pandas as pd

# Thresholds
RULES_CONFIG = {
    "COST_OVERRUN_HIGH": 20.0,
    "TIME_OVERRUN_HIGH": 20.0,
    "LOW_PROGRESS": 30.0,
    "EXPENDITURE_MISMATCH": 20.0
}

def generate_warnings(row):
    warnings = []
    
    # WARNING 1: Predicted cost overrun is high
    if row.get('cost_overrun_percent', 0) > RULES_CONFIG["COST_OVERRUN_HIGH"]:
        warnings.append("Predicted cost overrun is high.")
        
    # WARNING 2: Predicted completion is significantly later than planned
    if row.get('time_overrun_percent', 0) > RULES_CONFIG["TIME_OVERRUN_HIGH"]:
        warnings.append("Predicted completion is significantly later than planned.")
        
    # WARNING 3: Expenditure is high compared with physical progress
    exp = row.get('expenditure_percent', 0)
    prog = row.get('physical_progress', 0)
    if (exp - prog) > RULES_CONFIG["EXPENDITURE_MISMATCH"]:
        warnings.append("Expenditure is high compared with physical progress.")
        
    # WARNING 4: Physical progress is low despite high project age
    # (Assuming age in months; e.g. > 24 months and < 30% progress)
    age = row.get('project_age_months', 0)
    if pd.notna(age) and age > 24 and pd.notna(prog) and prog < RULES_CONFIG["LOW_PROGRESS"]:
        warnings.append("Physical progress is low despite high project age.")
        
    # WARNING 5: Multiple risk indicators are simultaneously high
    if len(warnings) >= 3:
        warnings.append("Multiple risk indicators are simultaneously high.")
        
    return warnings
