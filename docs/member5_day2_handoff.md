# Member 5 Day 2 Handoff Document

**To:** Member 6 (Dashboard)
**From:** Member 5 (Risk Engine)
**Date:** July 2026 Snapshot context

## 1. What I Built

I have implemented a comprehensive **Risk Scoring and Early Warning System** for the PAIMANA project dataset. This Risk Engine synthesizes the ML outputs from Member 3 (Cost Risk) and Member 4 (Time Risk), along with current financial and physical progress indicators, to generate a unified risk profile for each project.

## 2. Outputs Generated

The following files are available in `outputs/member5/`:
- `high_risk_projects.csv`: A filtered list of all projects flagged as HIGH or CRITICAL risk.
- `early_warning_results.csv`: All projects that triggered one or more early warning rules, along with their generated explanations.
- `risk_summary.csv`: Summary counts of projects by risk category.
- `risk_distribution.png`: A bar chart showing the distribution of portfolio risk.

## 3. How to Use the Risk Engine

The Risk Engine provides a clean, single-entry-point function for you to use in the backend API or dashboard data layer.

```python
from src.risk.risk_engine import predict_project_risk

project_data = {
    'project_code': 12345,
    'original_cost': 1500.0,
    'project_age_days': 1200,
    'physical_progress': 45.0,
    'cumulative_expenditure': 800.0,
    'safe_expenditure_percent': 53.33,
    'original_duration_days': 1000,
    'state': 'Maharashtra',
    'agency': 'NHAI',
    'sector': 'Roads & Highways',
    'project_size_category': 'Medium'
}

risk_profile = predict_project_risk(project_data)
```

### Output Structure

The function returns a JSON-serializable dictionary that you can easily surface in the UI:

```json
{
  "project_code": 12345,
  "risk_score": 3,
  "overall_risk": "HIGH",
  "warnings": [
    "High predicted schedule risk (74.2% probability).",
    "Significant expenditure-progress mismatch. Expenditure is 53.3% but physical progress is only 45.0% (Gap: 8.3%)."
  ],
  "explanation": "Overall Risk: HIGH\n\nReasons:\n* High predicted schedule risk (74.2% probability).\n* Significant expenditure-progress mismatch. Expenditure is 53.3% but physical progress is only 45.0% (Gap: 8.3%).\n\nEarly Warning:\nProject requires closer monitoring due to financial/physical progress divergence.",
  "cost_model_output": { ... },
  "time_model_output": { ... }
}
```

## 4. Key Documentation

Please review the following docs to understand the rules and methodology:
- `docs/member5_risk_engine.md`: Details the architectural components of the engine.
- `docs/member5_risk_thresholds.md`: Details the prototype point-scoring system used to derive the LOW/MEDIUM/HIGH/CRITICAL categories.

## 5. Important Limitations

1. **Prototype Thresholds**: The logic and thresholds used to calculate the composite risk score (e.g., >20% gap for expenditure mismatch) are **prototype heuristics designed for the hackathon**. They are **NOT** official MoSPI policy and should be labeled as experimental or AI-derived in the UI.
2. **Snapshot Data**: Like the underlying models, the Risk Engine currently operates on the July 2026 cross-sectional snapshot. A true early warning system requires historical time-series data to track velocity.
