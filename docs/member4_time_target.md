# Time Overrun Target Definition (Member 4)

This document evaluates the potential Machine Learning targets for predicting schedule delays (time overruns) in the InfraGuard-AI model, using the PAIMANA July 2026 dataset.

## Potential ML Targets Investigated

### 1. Classification: `time_overrun_flag` (Binary)
- **Definition**: `1` if `revised_completion_date > original_completion_date`, else `0`.
- **Pros**:
  - Extremely clear business meaning: "Will this project miss its original deadline?"
  - More resilient to extreme outliers in delays (e.g., projects delayed by 150 months are treated the same as 1-month delays in terms of binary risk).
  - Faster to build a robust baseline model with high interpretability (using classifiers like XGBoost or Random Forest).
- **Cons**:
  - Loses the magnitude of the delay. A 1-month delay is treated identically to a 10-year delay.

### 2. Regression: `time_overrun_months` (Continuous)
- **Definition**: `(revised_completion_date - original_completion_date)` in months.
- **Pros**:
  - Quantifies the severity of the delay, which is highly useful for financial planning and contractor penalties.
- **Cons**:
  - Highly skewed distribution. The presence of massive right-tail outliers (delays > 100 months) makes linear regression unstable and tree-based regression prone to high MAE/RMSE.
  - Requires advanced outlier handling.

## The Prediction Point: When do we predict?

We must establish *when* the model makes its prediction, as this strictly governs which features are legally available without data leakage.

### Option A: Approval-time Prediction
- **Scenario**: At the moment a project is approved, predict if it will be delayed.
- **Available Inputs**: `original_cost`, `planned_duration`, `state`, `agency`.
- **Limitation**: We cannot use `physical_progress` or `cumulative_expenditure` because they do not exist at approval time.

### Option B: Implementation-time Early Warning (Recommended)
- **Scenario**: At the current reporting month (e.g., July 2026), given the project's current progress, predict if it will finish on time.
- **Available Inputs**: `original_cost`, `planned_duration`, `state`, `agency`, `physical_progress`, `cumulative_expenditure`, `project_age_months`.
- **Reasoning**: Problem Statement 26103 asks for an **Early Warning System**. This inherently means monitoring *ongoing* projects to catch deviations early. Therefore, we should use Option B.

## Final Target Recommendation

For the **Day-2 initial model**, the recommended target is:
**Binary Classification: `time_overrun_flag`**

**Reasoning**:
Predicting the *probability* of a schedule delay is the most actionable metric for an early-warning dashboard. It allows us to rank projects by "Risk of Delay". Once the binary classifier proves robust, a secondary Regression model predicting `time_overrun_months` can be trained specifically on projects flagged as high-risk.
