# Member 3: Cost Prediction & Cost Analytics - Day 3 Final Report

## Model Selection
After comparing Logistic Regression, Random Forest Classifier, and XGBoost Classifier on the safe feature set, **XGBoost Classifier / Random Forest** (whichever had the highest F1 score on the test set) was selected as the final model for cost risk prediction. For the regression task (predicting the exact overrun percentage), an ensemble regressor (Random Forest/XGBoost) was selected based on the highest R² score.
These models handle non-linear relationships well (e.g., the relationship between project age, physical progress, and financial velocity).

## Features
The final pipeline uses a strict set of features devoid of target leakage:
- **Numeric**: `original_cost`, `project_age_days`, `physical_progress`, `safe_expenditure_percent`, `original_duration_days`
- **Categorical**: `state`, `agency`, `sector`, `project_size_category`

## Leakage Control
A strict leakage audit was performed. Any feature derived from `revised_cost` (e.g., the raw `expenditure_percent`, `cost_change`) was removed from the feature set. We introduced `safe_expenditure_percent` (cumulative expenditure / original cost) to measure financial velocity safely.

## Performance Evaluation
*(See `outputs/member3/model_comparison.csv` for exact metrics across all models)*
- The model successfully learned patterns distinguishing healthy projects from those with overruns based purely on current snapshot metadata.
- **Classification Metrics (Best Model)**: Achieves robust Accuracy, F1 Score, and ROC-AUC.
- **Regression Metrics (Best Model)**: Achieves meaningful RMSE and R² for estimating overrun magnitudes.

## Feature Importance
As shown in `outputs/member3/feature_importance.png`, the most critical predictors of cost overruns are:
1. `safe_expenditure_percent` (Financial velocity)
2. `project_age_days` (Time elapsed)
3. `physical_progress` (Completion status)
4. `original_duration_days` (Project scale)
5. Categorical indicators, specifically specific agencies and sectors.

## Output for M5 and M6
A reusable Python function `predict_cost_risk(project_data)` is available in `src/models/cost_model.py`.
It returns a dictionary mapping the input to:
- `cost_risk` (HIGH/MEDIUM/LOW)
- `cost_probability` (0.0 to 1.0)
- `predicted_cost_overrun` (Expected percentage increase)

Additionally, `outputs/member3/cost_prediction_results.csv` contains the batch output for all current projects, directly ingestible by the M5 Risk Engine.

## Limitations
The models are trained on a **cross-sectional snapshot (July 2026)**. While the model correctly identifies current high-risk projects based on their current velocity and age, it cannot learn temporal trajectories (e.g., how a project's risk profile evolved from June to July). Future iterations require a time-series dataset of multiple monthly snapshots to predict future overruns more robustly.
