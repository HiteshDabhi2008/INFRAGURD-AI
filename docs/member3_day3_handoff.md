# Member 3 to M5 & M6: Day 3 Handoff

This document explains how the Risk Engine (M5) and Dashboard (M6) members can integrate the finalized Cost Prediction model.

## 1. Using the Model in Python (M5 & M6)

A reusable prediction wrapper is located at `src/models/cost_model.py`. You can import and use it directly to score any project record:

```python
from src.models.cost_model import predict_cost_risk

# Example Input (Must contain safe features)
project_data = {
    "original_cost": 500.0,
    "project_age_days": 1200,
    "physical_progress": 45.0,
    "safe_expenditure_percent": 85.0,
    "original_duration_days": 1095,
    "state": "Maharashtra",
    "agency": "NHAI",
    "sector": "Roads & Highways",
    "project_size_category": "Small"
}

# Get Prediction
result = predict_cost_risk(project_data)
print(result)
```

**Output Format:**
```json
{
    "risk_level": "HIGH",
    "overrun_probability": 0.84,
    "expected_overrun_percent": 25.5,
    "is_cost_overrun": True
}
```

## 2. Meaning of the Output Variables

- **`overrun_probability`**: A float from 0.0 to 1.0 representing the model's confidence that the project will experience (or is currently experiencing) a cost overrun.
- **`risk_level`**: A categorical bucket derived from the probability:
  - `HIGH`: probability > 0.70
  - `MEDIUM`: probability > 0.40
  - `LOW`: probability <= 0.40
- **`expected_overrun_percent`**: The regression model's estimate of the percentage cost escalation.

## 3. Batch Predictions (For M5)
If you are building the Risk Engine over the entire dataset, you do not need to run inference row-by-row. 
I have exported the complete model predictions for the master dataset to:
**`outputs/member3/cost_prediction_results.csv`**

This file contains:
- `project_id`
- `cost_risk` (HIGH/MEDIUM/LOW)
- `cost_probability`
- `predicted_cost_overrun`

M5 can directly join this CSV with the master dataset using `project_id` to compute the overall Risk Score.

## 4. Dashboard Integration (For M6)
For the project details page on the dashboard, you should display:
- **Cost Risk Level**: Display a badge (Red = HIGH, Yellow = MEDIUM, Green = LOW) mapped to `risk_level`.
- **Cost Risk Probability**: Show `overrun_probability * 100` as a percentage.
- **Expected Escalation**: Show the `expected_overrun_percent`. 
*Note: Ensure the dashboard explicitly states that this is an AI-driven prediction, especially for projects that haven't officially reported a revised cost yet.*
