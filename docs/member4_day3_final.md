# Member 4 - Day 3 Final Time Prediction Model

This document summarizes the final Time Overrun predictive models created for Member 5 (Risk Engine) and Member 6 (Dashboard). 

## Target
* **Classification Target:** `time_overrun_flag` - Predicts whether a project will miss its original deadline.
* **Regression Target:** `time_overrun_months` - Predicts the delay magnitude in months.

## Features
We used financial velocity and current progress state (`safe_expenditure_percent`, `safe_progress_gap`, `physical_progress`, `project_age_days`) as well as project characteristics (`sector`, `agency`, `original_cost`).

## Leakage Check
Target leakages such as `revised_completion_date` and anticipated milestones were entirely removed to simulate a true early-warning system based strictly on current measurable state variables.

## Model Selection & Performance
We tested Logistic Regression, Random Forest, and XGBoost using a complete data pipeline consisting of `SimpleImputer`, `StandardScaler`, and `OneHotEncoder`.

### Classification (Best: Logistic Regression)
Logistic Regression outperformed the tree-based models on this task.
* **Accuracy:** 0.8442
* **Precision:** 0.8711
* **Recall:** 0.8829 (Very high, highly critical for capturing genuinely delayed projects early)
* **F1-Score:** 0.8770
* **ROC-AUC:** 0.8963

### Regression (Best: Random Forest Regressor)
Random Forest provided the best continuous predictions of the exact delay margin.
* **MAE:** 13.02 months
* **RMSE:** 30.41 months
* **R²:** 0.157

## Feature Importance
The strongest indicators for time delay risk are driven heavily by categorical variables associated with the agency (e.g., specific ministries or corporations) and the `sector` (e.g., Coal & Mining), as well as the continuous measure `physical_progress`. Feature importance plots have been exported to `outputs/member4/time_feature_importance.png`.

## Limitations
* **Cross-Sectional Limitation:** The model currently operates on a single snapshot of data (July 2026). It does not factor in the temporal trajectory (e.g., month-over-month change in `physical_progress`). Incorporating a time-series or multi-snapshot sequence would drastically improve predictive capabilities.
* **Regression Variability:** While the classification model is robust, the exact month count (Regression) has high variance (low R²), meaning the magnitude of the delay is harder to precisely pinpoint than the occurrence of a delay itself.
