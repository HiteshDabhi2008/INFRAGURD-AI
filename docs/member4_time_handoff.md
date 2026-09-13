# Member 4 Day 2 Handoff Document

**To:** Member 5 (Risk Engine), Member 6 (Dashboard)
**From:** Member 4 (Time Overrun Prediction)
**Date:** July 2026 Snapshot context

## 1. Target Definitions

### Classification: `time_overrun_flag`
- `1` if `revised_completion_date > original_completion_date`, else `0`.
- This is the primary target. The classifier outputs a probability of schedule delay.

### Regression: `time_overrun_months`
- `(revised_completion_date - original_completion_date).days / 30.44`
- Quantifies the severity of delay. Negative values mean early completion.

## 2. Prediction Point

**Implementation-time early warning.** The model answers: "Given this project's current state in the monthly PAIMANA report, will it miss its original deadline?"

## 3. Feature List (Strictly Safe)

**Numeric:** `original_cost`, `project_age_days`, `physical_progress`, `cumulative_expenditure`, `safe_expenditure_percent`, `safe_progress_gap`, `original_duration_days`

**Categorical:** `state`, `agency`, `sector`, `project_size_category`

## 4. Leakage Exclusions

The following features are **EXCLUDED** from all models:
- `revised_completion_date`, `revised_duration_days`, `time_overrun_months`, `time_overrun_flag`
- `revised_cost`, `cost_change`, `cost_change_percent`
- `expenditure_percent` (Day-1 version using `revised_cost` denominator)
- `progress_gap` (derived from leaky `expenditure_percent`)

## 5. Best Models & Evaluation

### Classification
| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|------|---------|
| **Logistic Regression** | **0.873** | **0.893** | **0.905** | **0.899** | **0.924** |
| Random Forest | 0.867 | 0.907 | 0.878 | 0.892 | 0.941 |
| XGBoost | 0.858 | 0.894 | 0.878 | 0.886 | 0.927 |

**Winner: Logistic Regression** — highest F1 (0.899) and recall (90.5% on the overrun class).

Confusion Matrix (on 353-sample test set):
```
           Predicted 0  Predicted 1
Actual 0       107           24
Actual 1        21          201
```

### Regression
| Model | MAE | RMSE | R2 |
|-------|-----|------|-----|
| **Linear Regression** | **12.26** | **21.27** | **0.588** |
| Random Forest | 8.50 | 24.73 | 0.442 |
| XGBoost | 8.69 | 23.81 | 0.483 |

**Winner: Linear Regression** — highest R2 (0.588).

## 6. Saved Model Locations

| File | Description |
|------|-------------|
| `models/time_classifier.pkl` | Best classifier (Logistic Regression) |
| `models/time_regressor.pkl` | Best regressor (Linear Regression) |
| `models/time_feature_columns.json` | Feature schema (numeric + categorical) |

## 7. Prediction Function

```python
from src.models.time_model import predict_time_risk

result = predict_time_risk({
    'original_cost': 2500.0,
    'project_age_days': 1800,
    'physical_progress': 55.0,
    'cumulative_expenditure': 1400.0,
    'safe_expenditure_percent': 56.0,
    'safe_progress_gap': 1.0,
    'original_duration_days': 1460,
    'state': 'Maharashtra',
    'agency': 'NHAI',
    'sector': 'Roads & Highways',
    'project_size_category': 'Medium',
})
# Returns:
# {
#   "risk_level": "MEDIUM",
#   "overrun_probability": 0.642,
#   "expected_overrun_months": 14.5,
#   "is_time_overrun": true
# }
```

### Risk Thresholds (Internal Convention)
| Probability | Risk Level |
|-------------|------------|
| > 0.70 | HIGH |
| 0.40 - 0.70 | MEDIUM |
| < 0.40 | LOW |

**These are NOT official MoSPI thresholds.** They are internal project conventions and should be calibrated with domain experts.

## 8. Top Feature Insights

Using Logistic Regression coefficient magnitudes:
1. `agency_Medical Education, MoHFW` (2.40) - specific agency is a very strong delay predictor
2. `project_age_days` (1.70) - older projects are more likely delayed
3. `original_duration_days` (1.39) - longer planned durations predict delays
4. `state_Multi-States (Bihar, Jharkhand)` (1.37) - multi-state projects are high risk
5. `physical_progress` (1.11) - lower physical progress predicts delays

## 9. Outputs

| File | Description |
|------|-------------|
| `outputs/member4/model_comparison.csv` | All model metrics |
| `outputs/member4/time_feature_importance.png` | Feature importance plot |
| `outputs/member4/time_prediction_results.csv` | Risk predictions for all 1,763 projects |

## 10. Limitations

1. **Single Snapshot:** This model is trained on the July 2026 cross-section. It maps current project states to current outcomes. For a production early-warning system, we need **historical monthly PAIMANA/OCMS snapshots** to learn temporal progressions.
2. **62.9% prevalence:** Nearly two-thirds of projects have time overruns. The model's baseline is a majority-class world, which means it needs good recall to be operationally useful (achieved: 90.5%).
3. **Sector is inferred:** The `sector` feature is inferred from agency/project name keywords. Some misclassifications are inevitable.

## 11. Recommendations for Member 5 (Risk Engine)

- Call both `predict_cost_risk()` and `predict_time_risk()` for each project.
- Combine the probabilities into a composite risk score (e.g., weighted average or max).
- Use the `time_prediction_results.csv` for bulk risk scoring.
