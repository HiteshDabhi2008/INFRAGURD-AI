# Feature Research & Recommendations

This document outlines the recommendations for the Machine Learning and Dashboarding teams (Members 3, 4, 5, 6) based on Member 2's Day 1 EDA.

## Cost ML Recommendations (For Member 3)

1. **What could be the cost prediction target?**
   - **Binary Classification**: `cost_overrun` (0 or 1). This is the easiest to start with. Did the project experience an overrun?
   - **Regression**: `cost_overrun_percent`. Predicting the actual magnitude of the overrun. Note: Exclude extreme outliers (>1000% overrun) from training or cap them to a maximum threshold (e.g., 200%) to avoid skewing the model.

2. **Which existing variables could be inputs?**
   - `original_cost`
   - `physical_progress` (as of reporting month)
   - `cumulative_expenditure` (as of reporting month)
   - `agency`
   - `state`
   - `original_duration_months`

3. **Which variables should not be inputs because of leakage?**
   - `revised_cost` (Directly defines the target)
   - `expenditure_percent` (Formula uses `revised_cost`)
   - `progress_gap` (Formula uses `expenditure_percent`)

4. **Which categorical variables may require encoding?**
   - `agency`: Needs Target Encoding or Frequency Encoding. There are too many unique agencies for simple One-Hot Encoding.
   - `state`: Can be One-Hot Encoded (approx 36 states/UTs). Consider grouping low-frequency states into "Other".

5. **Which additional variables could improve prediction?**
   - Extracted **Sector/Ministry** from PAIMANA Table 1 or 2.
   - External inflation indices (WPI for construction materials).

---

## Time ML Recommendations (For Member 4)

1. **What could be the time prediction target?**
   - **Regression**: `time_overrun_months` (Continuous number of months delayed).
   - **Binary**: `is_delayed` (Derived: `time_overrun_months > 0`).

2. **Which date/project variables can be used?**
   - `original_duration_months`
   - `physical_progress`
   - `cumulative_expenditure`
   - `original_cost`
   - `agency`, `state`

3. **Which variables would cause leakage?**
   - `revised_completion_date` (Directly defines the target)
   - `revised_duration_months`

4. **What historical information is missing?**
   - We only have the *current* `physical_progress`. We do not have the historical trajectory (e.g., how fast progress was made over the last 6 months). Time-series historical data would vastly improve predictions.

5. **What additional variables could improve time prediction?**
   - Land acquisition status.
   - Environmental/Forest clearance delays (PARIVESH).
   - Monthly rainfall deviations (IMD).

---

## Dashboard Recommendations (For Member 6)

1. **Potential Dashboard KPIs**:
   - Total Ongoing Projects: 1,775
   - Total Original Cost (Sum of `original_cost`)
   - Total Revised Cost (Sum of `revised_cost`)
   - Total Cumulative Expenditure (Sum of `cumulative_expenditure`)
   - Average Physical Progress
   - % of Projects with Cost Overrun
   - Average Cost Overrun %

2. **Potential Filters**:
   - `state` (e.g., filter to only show Maharashtra projects)
   - `agency` (e.g., filter to only show NHAI projects)
   - Overrun Status (Projects with Cost Overrun = Yes/No)
   - Physical Progress Range (e.g., 0-25%, 75-100%)

*(Note: Sector and Ministry are highly desirable filters but are not yet available at the project level in Table 6. They will need to be added later.)*
