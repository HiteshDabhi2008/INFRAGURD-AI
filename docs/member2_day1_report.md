# Member 2 — Day 1 Final Report

## 1. Dataset Used
- **Master Dataset**: `data/processed/paimana_master_v1.csv` (Provided by Member 1)
- **Rows**: 1,775
- **Columns**: 23

## 2. Important Variables Identified
- **Cost**: `original_cost`, `revised_cost`, `cumulative_expenditure`
- **Schedule**: `approval_date`, `original_completion_date`, `revised_completion_date`
- **Progress**: `physical_progress`
- **Categorical**: `state`, `agency`
- **Derived Targets**: `cost_overrun`, `time_overrun_months`

## 3. Missing Value Findings
- `sl_no`, `project_code`, `agency`, `state`: 0 missing
- `original_cost`, `revised_cost`, `cumulative_expenditure`, `physical_progress`: 0 missing
- `approval_date`: 12 missing (0.7%)
- `revised_completion_date`: 348 missing (19.6% - indicates no timeline revision)

## 4. Cost Findings
- Total projects with Cost Overrun: 482 (27.2%)
- Most overruns are relatively small (under 25%), but there is a heavy right tail of extreme outliers exceeding 100% cost increases.
- Many projects show 0% cost overrun (they are executing strictly on or below budget).

## 5. Progress & Expenditure Findings
- `physical_progress` covers the full range from 0% to 100%.
- A notable number of projects have 0% progress but significant expenditure, or 100% progress but low relative expenditure.
- The derived `progress_gap` (Expenditure % - Physical Progress %) reveals major discrepancies for some outliers that require further investigation. Some projects list >1000% expenditure relative to current revised cost, which points to severe source data anomalies or massive budget mismanagement.

## 6. Time/Schedule Findings
- 348 projects have no `revised_completion_date`, meaning they are officially running on their original timeline (or haven't reported delays).
- The average `time_overrun_months` for delayed projects is ~23 months.
- Time delays heavily correlate with cost overruns (to be confirmed statistically by Member 5).

## 7. Potential Risk Indicators (Exploratory)
- **Abnormal Expenditure-Progress Relationship**: E.g., Expenditure % >> Physical Progress %.
- **Stagnation Near Completion**: Physical progress > 90% but past deadline (regulatory stalling).
- **Delayed Start**: Huge gap between approval and start date.
- **Large Schedule Difference**: Revised duration > 2x original duration.
- *(See `docs/risk_indicator_research.md` for details).*

## 8. Potential ML Features & Leakage Risks
- **Safe Inputs**: `original_cost`, `approval_date`, `state`, `agency`, `original_duration_months`.
- **Potential Inputs (snapshot)**: `physical_progress`, `cumulative_expenditure`.
- **High Leakage Risk (DO NOT USE AS INPUTS)**: `revised_cost`, `revised_completion_date`, `expenditure_percent`, `progress_gap`. 
- *(See `docs/ml_feature_map.md` for details).*

## 9. Recommended ML Targets
- **Cost Target (Member 3)**: Predict `cost_overrun` (Binary: 0 or 1).
- **Time Target (Member 4)**: Predict `time_overrun_months` (Continuous regression) or `is_delayed` (Binary).

## 10. Recommended Dashboard KPIs (Member 6)
- Total Ongoing Projects (1,775)
- Total Original Cost vs Total Revised Cost
- Total Cumulative Expenditure
- Average Physical Progress
- Cost Overrun % (Filterable by State/Agency)
- Top 10 Highest Risk Projects

## 11. External Data Sources Researched
- **Wholesale Price Index (WPI)**: Material inflation (data.gov.in / RBI).
- **Rainfall / Weather**: IMD data for monsoon impact.
- **Land/Forest Clearances**: PARIVESH portal.
- **Ease of Doing Business**: DPIIT BRAP rankings by state.
- *(See `docs/external_data_research.md` for details).*

## 12. Files Created
- `notebooks/member2_day1_eda.ipynb`
- `src/data/eda_script.py`
- `outputs/cost_analysis.png`
- `outputs/cost_overrun_distribution.png`
- `outputs/expenditure_vs_progress.png`
- `outputs/progress_distribution.png`
- `outputs/projects_by_state.png`
- `outputs/projects_by_agency.png`
- `docs/feature_research.md`
- `docs/ml_feature_map.md`
- `docs/risk_indicator_research.md`
- `docs/external_data_research.md`
- `docs/member2_day1_report.md`

## 13. Files Modified
- None of Member 1's files were modified or overwritten.

## 14. Unresolved Issues
- The `sector` and `ministry` variables are missing from the project-level data in Table 6. This is a critical gap for categorical ML encoding. We need to either map agencies to ministries or extract this from other parts of the PDF.
- Extreme outliers in `cumulative_expenditure` (up to 42,000% of revised cost) need to be validated—they may be typos in the MoSPI report.

## 15. Handoff Recommendations
- **Member 3 (Cost ML)**: Start building a baseline Random Forest classifier using `original_cost`, `state`, `agency`, and `original_duration_months` to predict `cost_overrun`. Do not use `revised_cost`.
- **Member 4 (Time ML)**: Start a regression model predicting `time_overrun_months`.
- **Member 5 (Risk)**: Begin creating a composite risk score rule-engine using the indicators in `docs/risk_indicator_research.md`. 
- **Member 6 (Dashboard)**: Build the UI layout using the KPIs listed in Section 10 and the sample dataset.
