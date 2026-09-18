# Member 3: Cost Prediction ML Model

## Overview
This document outlines the methodology and results for the Machine Learning model designed to predict the **Total Cost at 100% Completion** for PAIMANA infrastructure projects.

## Objective
To provide an early-warning signal for cost overruns by comparing the currently observed spending velocity against the initial budget.

## Data Processing
The model leverages a longitudinal dataset constructed from monthly snapshot PDFs (April 2026 – July 2026).
- **Inputs**: Features engineered in `cost_features.py` using historical data.
- **Target**: `target_total_cost` (proxied using `revised_cost` for training).

## Models Evaluated
1. **Baseline**: Ridge Regression (Linear Regression with L2 regularization)
2. **Random Forest Regressor**: Selected for its robustness to outliers and non-linear relationships.
3. **XGBoost Regressor**: Used for gradient boosting performance if available in the environment.

## Model Selection
The final model is selected based on minimizing the Mean Absolute Error (MAE) and Mean Absolute Percentage Error (MAPE). 

## Output Contract (for Member 5 & 6)
- **File**: `outputs/member3/cost_predictions.csv`
- **Fields Provided**:
  - `project_code`: Unique identifier
  - `predicted_total_cost`: Predicted cost at completion (Cr)
  - `cost_overrun_percent`: Predicted overrun percentage relative to `original_cost`.

## How to Run Inference
Use the functions provided in `src/models/cost_model.py`:
```python
from src.models.cost_model import predict_project_cost_risk

# Example data
project_data = {
    'original_cost': 500.0,
    'physical_progress': 45.0,
    'cumulative_expenditure': 200.0,
    'progress_change_1m': 2.5,
    'expenditure_change_1m': 10.0,
    'expenditure_per_progress': 4.44,
    'state': 'Maharashtra',
    'agency': 'NHAI',
    'project_size_category': 'Small'
}

risk = predict_project_cost_risk(project_data)
print(risk['predicted_total_cost'])
print(risk['cost_overrun_percent'])
```
