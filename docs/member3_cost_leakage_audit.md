# Member 3: Cost ML Data Leakage Audit

## Objective
The objective of the ML model is to predict the **Total Cost at 100% Completion** for ongoing PAIMANA infrastructure projects using only data that would be available at a given snapshot in time (the `report_month`).

## Definition of Target Variable
- **Target**: `target_total_cost` (Predicted Total Cost at 100% completion)
- **Proxy used**: `revised_cost` is used as the ground truth representing the final expected cost of the project (if `revised_cost` is missing, we use `original_cost`).

## Data Leakage Prevention Strategy
To ensure the model simulates a real-world predictive scenario, we must **NOT** feed the model any features that are mathematically derived from or directly represent the target variable (`revised_cost`). If we include such features, the model will "cheat" by extracting the answer directly from the inputs, rendering it useless for actual early-warning predictions.

### 🔴 LEAKAGE FEATURES (BANNED)
The following features are EXCLUDED from the ML model pipeline because they leak the target:
1. `revised_cost`: Directly represents the target.
2. `cost_overrun`: A binary flag derived by comparing `revised_cost` to `original_cost`.
3. `cost_overrun_percent`: Derived using `revised_cost`.
4. `cost_change`: Derived using `revised_cost`.
5. `expenditure_percent`: Calculated as `(cumulative_expenditure / revised_cost) * 100`. Because the denominator is `revised_cost`, this feature implicitly leaks information about the final revised cost. 
6. `progress_gap`: Calculated as `expenditure_percent - physical_progress`. Inherits leakage from `expenditure_percent`.

### 🟢 SAFE FEATURES (INCLUDED)
The following features are safe to use as they are known independently of the final cost overrun:
1. `original_cost`: The officially approved initial budget.
2. `physical_progress`: Current completion percentage.
3. `cumulative_expenditure`: Total amount spent *up to the current month*.
4. `progress_change_1m`: The change in physical progress over the last month (derived from historical dataset).
5. `expenditure_change_1m`: The change in expenditure over the last month (derived from historical dataset).
6. `expenditure_per_progress`: `cumulative_expenditure / physical_progress` (a safe proxy for spending velocity that does NOT rely on `revised_cost`).
7. `num_observations`: Number of months the project has been tracked in our dataset.
8. `state`, `agency`, `project_size_category`: Static categorical features.

## Conclusion
By strictly excluding any variable that touches `revised_cost`, the model is forced to learn the *relationship* between current spending (`cumulative_expenditure`), initial budget (`original_cost`), current progress (`physical_progress`), and temporal velocity (`progress_change_1m`), providing a genuine ML prediction.
