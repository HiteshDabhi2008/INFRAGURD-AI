# Member 3: Cost Prediction Model Definition

## 1. Prediction Targets

To provide a comprehensive cost-overrun prediction pipeline, we define two specific prediction targets:

*   **Classification Target (`cost_overrun_flag`)**: A binary indicator (1 or 0) predicting whether a project will experience *any* cost overrun.
    *   *Calculation*: `1 if revised_cost > original_cost else 0`
*   **Regression Target (`cost_overrun_percent`)**: A continuous value predicting the *magnitude* of the cost overrun as a percentage of the original cost.
    *   *Calculation*: `((revised_cost - original_cost) / original_cost) * 100` (Negative values denote cost savings, positive values denote escalations).

## 2. Data Leakage Audit

When predicting cost overruns, it is critical to ensure that no future knowledge about the `revised_cost` leaks into the input features.

### Excluded Features (High Leakage Risk):
*   `revised_cost`
*   `cost_change`
*   `cost_change_percent`
*   `cost_overrun` (if present)
*   `expenditure_percent` (Day 1 calculation used `revised_cost` in the denominator).
*   `progress_gap` (Relied on leaky `expenditure_percent`).

### Safe Input Features:
The following features are safe as they rely on the initial baselines or current snapshot metrics without incorporating the final revised expectations:
*   `original_cost`
*   `project_age_days`
*   `physical_progress`
*   `cumulative_expenditure`
*   `safe_expenditure_percent` (Calculated using `original_cost`)
*   `safe_progress_gap`
*   `state`
*   `agency`
*   `sector`
*   `original_duration_days`
*   `project_size_category`

## 3. Temporal Limitation Warning

> [!WARNING]
> This model is trained on a single snapshot of data (July 2026). In this snapshot, some projects have already concluded, some are ongoing, and some are just starting.
>
> A model trained to map current (potentially late-stage) features like `physical_progress=98%` to a known `revised_cost` is **not a true early-warning system**. To build a robust temporal predictive model, we would need historical month-over-month snapshots to train the model to predict *future* overruns based on *past* states (e.g., predicting month 24's cost overrun using data strictly from month 12).
>
> For this Hackathon prototype, we assume the snapshot serves as a proxy point-in-time evaluation.
