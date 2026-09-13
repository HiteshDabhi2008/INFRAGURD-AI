# ML Feature Recommendations

Based on the Exploratory Data Analysis (EDA) of the `paimana_master_v1.csv` and the generated features in `project_features.csv`, here are the recommendations for predictive modeling for Cost Overruns, Time Delays, and Risk Engines.

## 1. Feature Recommendations for Cost Model (Member 3)

### Safe Features (Available at Prediction Time):
*   `original_cost`: Very important. Large projects (>$5000 Cr) have an average cost escalation of 13.4%, which is higher than medium or small projects.
*   `agency`: Highly predictive. Some agencies like *Medical Education* (31.5% avg escalation) have systemic issues, while others like *Roads & Highways* are well managed (1.2% avg escalation).
*   `state`: Crucial. Multi-state projects have extreme escalations (e.g., MP/Maharashtra at 230%, Gujarat/MP at 966%).
*   `sector`: Strong predictor. Water Resources projects have huge escalations (137% avg).
*   `project_size_category`: Helps bucket models effectively.

### Features to Avoid (Leakage Risk):
*   **DO NOT USE** `revised_cost`, `cost_change`, or `cost_change_percent` as inputs. These are your target variables.
*   **DO NOT USE** `expenditure_percent` (as currently defined if it uses revised cost). Use `safe_expenditure_percent` instead.

## 2. Feature Recommendations for Time Model (Member 4)

### Safe Features:
*   `original_duration_days`: Longer projects inherently face more geopolitical and macro-economic uncertainty.
*   `project_age_days`: Time elapsed since approval. Correlation with physical progress is only ~0.386, meaning aging projects aren't necessarily progressing at expected rates.
*   `state` and `sector`: Same logic as cost. Water resources, urban development, and multi-state projects face more land acquisition delays.
*   `agency`: Helps identify structurally slow executing bodies.

### Features to Avoid (Leakage Risk):
*   **DO NOT USE** `revised_completion_date`, `time_overrun`, etc. as inputs.
*   Avoid using raw current `physical_progress` without normalizing it by `project_age_days`.

## 3. Recommendations for Risk Engine (Member 5)

The risk engine should synthesize outputs from both the Cost and Time models, combined with current snapshot indicators.

### Key Risk Indicators (KRIs):
*   **Financial Velocity vs Physical Progress**: Projects where `safe_expenditure_percent > 75%` but `physical_progress < 25%` (we found 4 such projects) are at extreme risk of failure or massive cost overruns.
*   **Age vs Progress**: High `project_age_days` but low `physical_progress`.
*   **External Risk Factors**: As researched, integrate State-level Ease of Doing Business or historical weather disruption indices.
*   **Multi-State Penalty**: Apply a systemic risk multiplier for any project crossing state lines, as our EDA shows they suffer the worst delays and cost escalations.

## Summary Notes for ML Teams
Do not claim correlation as causation. The July 2026 report is a snapshot. When building models, treat this snapshot as a point-in-time evaluation. Ensure to strictly divide `original_cost` when computing financial progress metrics for ML inputs to prevent leakage of the final `revised_cost` target.
