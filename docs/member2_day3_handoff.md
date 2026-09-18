# Member 2: Day 3 Handoff

## What was completed
- Finalized Feature Analysis and systematically classified variables as Safe Input, Target, or Leakage Risk.
- Finalized Leakage Check and documented specific fields that M3 and M4 must avoid.
- Conducted final EDA using the latest master datasets, validating findings and generating essential charts in `outputs/member2/`.
- Finalized external data research, detailing WPI, Rainfall, and Ease of Doing Business variables for integration.
- Updated `docs/feature_recommendations.md` with a clear feature-to-model mapping table.
- Created `docs/member2_day3_findings.md` to summarize insights for the team.

## Final Feature List
The finalized feature mapping is available in `docs/feature_recommendations.md` and `docs/ml_feature_map.md`.

## Important EDA Findings
- The highest cost escalations are concentrated in multi-state projects and specific sectors like Water Resources.
- There is a noticeable disconnect between project age and physical progress, indicating delays aren't just for new projects but are structural across the lifecycle.
- Expenditure generally aligns with physical progress, but the outliers (high spend, low progress) represent the highest risk projects.

## Leakage Warnings
- **Avoid for Cost ML**: `revised_cost`, `cost_change`, `cost_overrun`, `expenditure_percent` (with revised denominator).
- **Avoid for Time ML**: `revised_completion_date`, `time_overrun_months`, `revised_duration_days`.

## External Data Recommendations
- **Inflation**: Wholesale Price Index (WPI) from MoSPI.
- **Weather**: Rainfall/Monsoon data from IMD.
- **Geopolitical/Regulatory**: Ease of Doing Business scores from DPIIT.

## Handoff to M3 (Cost ML)
**Recommended Inputs**: `original_cost`, `project_age_days`, `physical_progress`, `safe_expenditure_percent`, `state`, `agency`, `sector`, `original_duration_days`, `project_size_category`.
**Instruction**: Ensure the target (`cost_overrun`) is cleanly isolated from inputs. Do not use `revised_cost` or derivations.

## Handoff to M4 (Time ML)
**Recommended Inputs**: `approval_date`, `original_completion_date`, `original_duration_days`, `project_age_days`, `physical_progress`, `safe_expenditure_percent`, `safe_progress_gap`, `original_cost`, `state`, `agency`, `sector`. 
**Instruction**: Predict delays based on project velocity from the current snapshot.

## Handoff to M5 (Risk Engine)
**Important Indicators**: Incorporate financial velocity anomalies (high spend vs low progress), systemic geographic risks (multi-state/pan-India), and use the safe indicators (like `safe_progress_gap`) instead of raw variables.

## Remaining Limitations
We are working with a cross-sectional snapshot (July 2026) rather than longitudinal data. A time-series approach with future monthly snapshots will dramatically improve prediction capabilities. Do not claim causality from simple correlations found in this snapshot.
