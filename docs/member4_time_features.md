# Member 4 - Day 3 Final Time Prediction Features

This document outlines the final set of features and the strict leakage check performed to ensure the time prediction models (`models/time_classifier.pkl` and `models/time_regressor.pkl`) are robust and use only available early-warning information.

## Target Definition
Two targets were finalized for the time prediction system based on Day 2 justification:
1. **`time_overrun_flag` (Classification)**: Binary target denoting whether the project is delayed beyond its original completion date (i.e. `time_overrun_months > 0`).
2. **`time_overrun_months` (Regression)**: Continuous target measuring the exact magnitude of the delay in months from the original schedule.

## Strict Leakage Check
To ensure the models simulate a real-world predictive environment (where future knowledge is hidden), we strictly excluded the following fields:
* `revised_completion_date`
* `time_overrun` (raw delay flag)
* `time_overrun_months` (target)
* Any future completion or anticipated milestone features.

## Final Selected Features

The models rely heavily on the project's financial velocity and progress to implicitly gauge time risk.

### Numeric Features (`NUM_FEATURES`)
* `original_cost`: Baseline budget, indicating project complexity.
* `original_duration_days`: Initial scheduled time budget.
* `project_age_days`: Time elapsed since the `approval_date`.
* `physical_progress`: The reported completion percentage (%).
* `cumulative_expenditure`: Total funds spent.
* `safe_expenditure_percent`: (`cumulative_expenditure` / `original_cost`) * 100.
* `safe_progress_gap`: `safe_expenditure_percent` - `physical_progress`. Highlights potential mismatches in physical vs financial progress.

### Categorical Features (`CAT_FEATURES`)
* `state`: The state where the project is being executed.
* `agency`: Execution agency responsible.
* `sector`: Industry sector (e.g., Railways, Roads & Highways).
* `project_size_category`: Mega / Major size classification.
