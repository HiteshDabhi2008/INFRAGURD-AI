# Member 4 - Day 3 Handoff

This document describes how Member 5 (Risk Engine) and Member 6 (Dashboard) can consume the output of the Time Overrun Prediction models.

## Final Models & Files
* **Classifier**: `models/time_classifier.pkl` (Logistic Regression - Predicts Risk/Probability)
* **Regressor**: `models/time_regressor.pkl` (Random Forest - Predicts overrun in months)
* **Schema**: `models/time_feature_columns.json` (Required columns/types)

## For Member 5 (Risk Engine)
You can consume the time risk outputs using one of two methods:

### Method 1: Pre-computed CSV Output (Batch)
The easiest method for large-scale integration is to ingest `outputs/member4/time_prediction_results.csv`.
It contains the following columns for every project in the master dataset:
* `project_id` (Mapped to `project_code`)
* `time_risk` (HIGH, MEDIUM, or LOW)
* `time_risk_probability` (Float 0-1)
* `time_overrun_predicted` (0 or 1)
* `time_overrun_months_predicted` (Float, numeric expectation of delay months)

Join this directly onto your existing data via `project_id`.

### Method 2: Python Inference API (Real-Time)
If you require live prediction on single project records, import the function from `src/models/time_model.py`:

```python
from src.models.time_model import predict_time_risk

# Pass a dictionary representing the project record (needs physical_progress, original_cost, etc)
result = predict_time_risk(project_record_dict)

print(result)
# Output:
# {
#    'risk_level': 'HIGH', 
#    'overrun_probability': 0.872, 
#    'expected_overrun_months': 17.7, 
#    'is_time_overrun': True
# }
```

You can then aggregate `time_risk` from this model with `cost_risk` from Member 3 to derive the **Overall Risk** metric.

## For Member 6 (Dashboard)
You can directly visualize the elements generated:
1. **Time Risk Categorization (`time_risk`)**: Use Red for HIGH, Yellow/Orange for MEDIUM, and Green for LOW on the dashboard.
2. **Expected Overrun Magnitude**: Display `expected_overrun_months` alongside the current schedule completion dates to provide concrete estimates to the user.
3. **Model Feature Importance**: You can embed `outputs/member4/time_feature_importance.png` in the dashboard to show stakeholders which project characteristics are driving the model's delay warnings.

## Known Limitations
The model is heavily reliant on single-snapshot variables and categorical structures (agency, sector) to determine delays, given that it does not track historical rate-of-change across months. Extreme outliers or completely novel projects might yield high variance in the regression metric (`expected_overrun_months`). Use the probability and classification metric (`time_risk`) as the primary decision driver.
