# Member 5 - Day 3 Handoff (Risk Engine to Dashboard)

This document provides instructions for Member 6 (Dashboard) on how to integrate the finalized Risk Engine.

## Risk Engine Location & Main Function
* **Module:** `src/risk/risk_engine.py`
* **Main Function:** `predict_project_risk(project_data: dict) -> dict`

## Input Format
The `predict_project_risk` function expects a single Python dictionary representing one project's record. It must contain the features required by the underlying Cost (M3) and Time (M4) models, plus raw progress metrics:
* `original_cost`, `project_age_days`, `physical_progress`, `cumulative_expenditure`, `safe_expenditure_percent`, `original_duration_days`.
* Categoricals: `state`, `agency`, `sector`, `project_size_category`.

## Output Format
The function returns a dictionary with the following keys, which can be directly parsed and rendered on the frontend:

```python
{
    "project_code": "12345",
    "risk_score": 5,                     # Integer point score
    "overall_risk": "CRITICAL",          # LOW, MEDIUM, HIGH, CRITICAL
    "warnings": [                        # List of strings
        "High predicted cost risk (85.2% probability).",
        "Significant expenditure-progress mismatch. Expenditure is 60.0% but physical progress is only 15.0% (Gap: 45.0%)."
    ],
    "explanation": "Overall Risk: CRITICAL\n\nReasons:\n* High predicted cost risk...\n\nEarly Warning:\nProject requires closer monitoring due to financial/physical progress divergence.",
    "cost_model_output": { ... },        # M3 outputs (risk_level, expected_overrun)
    "time_model_output": { ... }         # M4 outputs (risk_level, expected_overrun)
}
```

## Risk Methodology & Warning Rules
1. **Cost & Time Models:** ML probabilities >70% generate HIGH warnings.
2. **Financial-Physical Mismatch:** When expenditure outpaces actual physical progress by >20 percentage points, an `EXPENDITURE_MISMATCH` warning fires.
3. **Stalled Progress:** If >80% of scheduled time is gone but physical progress is <50%, a `STAGNATION_NEAR_DEADLINE` warning fires.
4. **Scoring:** Warnings grant points. 0-1 pt = LOW, 2 pts = MEDIUM, 3-4 pts = HIGH, 5+ pts = CRITICAL.

## Integration Instructions for M6
* **For Portfolio Overviews:** Read `outputs/member5/risk_summary.csv` or `early_warning_results.csv` to quickly populate high-level dashboard metrics without running the models live.
* **For Individual Project Views:** If a user clicks on a specific project, fetch its record from the database/CSV, pass it through `predict_project_risk()`, and render the resulting `overall_risk` (e.g. as a colored badge) and the `explanation` string (as a text panel). You do not need to recalculate or parse any thresholds on the frontend.

## Known Limitations
* Prototype Thresholds: The point-scoring thresholds are designed for proof-of-concept demonstration and should be marked as "Prototype" on the dashboard UI.
* Single-Snapshot Dependencies: Predictions and warnings operate solely on the most recent data submission, without analyzing historical rate-of-change.
