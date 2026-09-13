# Member 3 Day 2 Handoff Document

**To:** Member 5 (Risk Engine), Member 6 (Dashboard)
**From:** Member 3 (Cost Modeling)
**Date:** July 2026 Snapshot context

## 1. Cost Model Definitions

I have developed a robust ML pipeline that predicts cost overruns using the `master_projects.csv` dataset. The pipeline strictly prevents target leakage by explicitly excluding features based on `revised_cost` or `cost_change`.

### Target Definitions
1.  **Classification Target (`cost_overrun_flag`)**: Predicts whether a project will have a cost overrun (`revised_cost > original_cost`).
2.  **Regression Target (`cost_overrun_percent`)**: Predicts the expected overrun percentage (`(revised_cost - original_cost) / original_cost * 100`).

### Feature List (Strictly Safe)
The following safe features are used for inference:
*   **Numeric**: `original_cost`, `project_age_days`, `physical_progress`, `cumulative_expenditure`, `safe_expenditure_percent`, `safe_progress_gap`, `original_duration_days`.
*   **Categorical**: `state`, `agency`, `sector`, `project_size_category`.

*Note: All leaky features like `expenditure_percent` and `revised_cost` were explicitly dropped during modeling.*

## 2. Best Models & Evaluation

Both Random Forest and XGBoost were tested against baselines (Logistic/Linear Regression). 
*   **Best Classifier**: Random Forest Classifier achieved the highest F1 score (0.687) with an Accuracy of 82.5% and ROC-AUC of 0.884.
*   **Best Regressor**: Random Forest Regressor achieved the best performance (R2: 0.218, MAE: 15.38). Note that the linear model performed very poorly (R2: -0.669), indicating complex non-linear interactions and potential massive outliers in the dataset.

The trained models are serialized as:
*   `models/cost_classifier.pkl`
*   `models/cost_regressor.pkl`
*   `models/cost_feature_columns.json`

## 3. Prediction Function (`predict_cost_risk`)

I have created a reusable API for you to generate cost risk profiles.

**Usage:**
```python
from src.models.cost_model import predict_cost_risk

project_data = {
    'original_cost': 1500.0,
    'project_age_days': 1200,
    'physical_progress': 45.0,
    'cumulative_expenditure': 800.0,
    'safe_expenditure_percent': 53.33,
    'safe_progress_gap': 8.33,
    'original_duration_days': 1000,
    'state': 'Maharashtra',
    'agency': 'NHAI',
    'sector': 'Roads & Highways',
    'project_size_category': 'Medium'
}

risk_profile = predict_cost_risk(project_data)
# Output:
# {
#   "risk_level": "MEDIUM",
#   "overrun_probability": 0.47,
#   "expected_overrun_percent": -0.88,
#   "is_cost_overrun": false
# }
```

## 4. Limitations (Important)

The current models are trained on a single snapshot of data (July 2026). They can correlate a project's *current* state to its *current* revised cost, but this is **not a true early-warning system** for future events. To predict future overruns authentically, we require multiple historical monthly snapshots so the model can learn temporal progression.
