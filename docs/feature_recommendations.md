# ML Feature Recommendations

Based on the Exploratory Data Analysis (EDA) of the `master_projects.csv` and `project_features.csv`, here are the recommended features for predictive modeling for Cost Overruns, Time Delays, and the Risk Engine.

## Final Feature Recommendation Table

| Feature | Cost ML | Time ML | Risk | Status | Reason |
| --- | --- | --- | --- | --- | --- |
| `original_cost` | Yes | Yes | Yes | Safe | Project size indicator; directly correlates with absolute risk. |
| `physical_progress` | Yes | Yes | Yes | Safe | Current project condition. |
| `safe_expenditure_percent` | Yes | Yes | Yes | Safe | Current financial progress (calculated using original_cost). |
| `expenditure_percent` | No* | No* | Yes* | Leakage Risk | Calculated using revised_cost. Leads to target leakage for ML. |
| `project_age_days` | Yes | Yes | Yes | Safe | Time elapsed since approval. |
| `original_duration_days` | Yes | Yes | Yes | Safe | Originally planned length of the project. |
| `safe_progress_gap` | Yes | Yes | Yes | Safe | Difference between physical progress and safe financial progress. |
| `state` | Yes | Yes | Yes | Safe | Geographic patterns and state-level risks. |
| `agency` | Yes | Yes | Yes | Safe | Agency execution capabilities and history. |
| `sector` | Yes | Yes | Yes | Safe | Sector characteristics and complexities. |
| `project_size_category` | Yes | Yes | Yes | Safe | Derived categorical bucket for project size. |
| `revised_cost` | No* | No | Yes* | Leakage Risk | Defines cost overrun. Do not use as ML input. |
| `cost_change` | No* | No | Yes* | Leakage Risk | Defines cost overrun. Do not use as ML input. |
| `cost_overrun` | No* | No | Yes* | Leakage Risk | ML Target. |
| `revised_completion_date` | No | No* | Yes* | Leakage Risk | Defines time overrun. Do not use as ML input. |
| `time_overrun_months` | No | No* | Yes* | Leakage Risk | ML Target. |

## 1. Feature Recommendations for Cost Model (Member 3)

### Safe Features:
* `original_cost`: Very important. Large projects have higher cost escalations.
* `agency`: Highly predictive. Certain agencies exhibit systemic cost overrun issues.
* `state`: Crucial. Multi-state projects have extreme escalations.
* `sector`: Strong predictor.
* `project_size_category`: Helps bucket models effectively.

### Features to Avoid (Leakage Risk):
* **DO NOT USE** `revised_cost`, `cost_change`, `cost_change_percent`, `cost_overrun`, or `cost_overrun_percent` as inputs.
* **DO NOT USE** `expenditure_percent` or `progress_gap` if they are derived using `revised_cost`.

## 2. Feature Recommendations for Time Model (Member 4)

### Safe Features:
* `original_duration_days`: Longer projects inherently face more geopolitical and macro-economic uncertainty.
* `project_age_days`: Time elapsed since approval.
* `state` and `sector`: Important for identifying systemic delays.
* `agency`: Helps identify structurally slow executing bodies.

### Features to Avoid (Leakage Risk):
* **DO NOT USE** `revised_completion_date`, `time_overrun_months`, `revised_duration_days`, or `revised_duration_months` as inputs.

## 3. Recommendations for Risk Engine (Member 5)

The risk engine should synthesize outputs from both the Cost and Time models, combined with current snapshot indicators.

### Key Risk Indicators (KRIs):
* **Financial Velocity vs Physical Progress**: Projects with high expenditure but low physical progress (wide `safe_progress_gap`).
* **Age vs Progress**: High `project_age_days` but low `physical_progress`.
* **Systemic Risk**: Multi-state projects or agencies with historically poor performance.

## Summary Notes for ML Teams
Do not claim correlation as causation. The July 2026 report is a cross-sectional snapshot. Treat this data as point-in-time when building models. Strictly avoid using target-derived variables as inputs to prevent data leakage.
