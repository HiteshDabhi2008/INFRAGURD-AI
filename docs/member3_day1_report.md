# Member 3 — Day 1 Final Report (Cost Analytics)

## 1. Dataset & Scope
- **Dataset Used**: `data/processed/paimana_master_v1.csv` (1,775 projects).
- **Cost Fields Available**: `original_cost`, `revised_cost`, `cumulative_expenditure`, `cost_overrun`, `cost_overrun_percent`, `expenditure_percent`, `cost_change`.

## 2. Cost Analysis Summary
- **Cost Increase Count**: 482 projects (27.2%)
- **Cost Decrease Count**: 316 projects (17.8%)
- **Unchanged Cost Count**: 977 projects (55.0%)
- **Mean Cost Overrun (for >0% projects)**: 50.69%
- **Median Cost Overrun (for >0% projects)**: 23.47%

*Important Pattern*: Mega-projects usually exhibit low *percentage* overruns but massive absolute monetary losses. A small subset of projects has extreme percentage overruns (>500%), heavily skewing the dataset. 

## 3. Recommended ML Target
- **Selected Target**: `cost_overrun_flag` (Binary Classification: `1` if revised > original, else `0`).
- **Alternative**: `cost_overrun_percent` (Regression). This is rejected for the Day-2 baseline model because the extreme right-tail outliers make linear and tree-based regression highly unstable without complex transformations.

## 4. ML Feature & Leakage Analysis
- **Safe Inputs**: `original_cost`, `original_duration_months`, `state`, `agency`.
- **Potential Snapshot Inputs**: `physical_progress`, `cumulative_expenditure`.
- **LEAKAGE VARIABLES (DO NOT USE)**: 
  - `revised_cost` (Mathematically defines the target).
  - `cost_change`, `cost_overrun_percent` (They ARE the target).
  - `expenditure_percent` and `progress_gap` (They use `revised_cost` in their denominator calculations, thus leaking the target).

## 5. Temporal-Data Limitations
The current July 2026 data is a **single monthly snapshot**. It allows us to perform *retrospective pattern recognition* (identifying common features of projects that have *already* failed). For a true "Early Warning System," we need historical time-series data (e.g., month-over-month snapshots) to train a model to predict future failures before they happen.

## 6. External Data Sources Researched (Additional Variables)
- **Wholesale Price Index (WPI)**: To track material inflation (Steel, Cement) affecting long-duration projects. (Available: data.gov.in / RBI API).
- **IMD Rainfall Data**: Extreme weather heavily delays civil works, inflating contractor costs.
- **PARIVESH / Land Acquisition**: Regulatory delays inherently cause cost escalation due to inflation and idle labor.

## 7. Recommended Day-2 Models & Explainability
- **Primary Model**: Random Forest Classifier or XGBoost Classifier (Good at handling categorical data like `state`/`agency` and robust to non-linear relationships).
- **Evaluation Metrics**: 
  - **F1-Score** (Primary, due to class imbalance: 27% vs 73%).
  - **ROC-AUC** (To evaluate the model's ability to rank risk probabilities).
  - **Recall** (Crucial: we prefer false alarms over missing a massive cost overrun).
- **Explainability**: SHAP (SHapley Additive exPlanations) will be used to generate localized explanations (e.g., "This project was flagged 85% risky primarily because it is managed by Agency X in State Y with an original duration of 60 months").

## 8. Files Created
- `notebooks/member3_day1_cost_eda.ipynb`
- `src/data/eda_member3.py`
- `docs/member3_cost_analysis.md`
- `docs/member3_cost_features.md`
- `docs/member3_cost_target.md`
- `docs/member3_day1_report.md`
- `outputs/member3_cost_overrun_distribution.png`
- `outputs/member3_original_vs_revised_cost.png`
- `outputs/member3_cost_overrun_by_state.png`
- `outputs/member3_cost_overrun_by_agency.png`
- `outputs/member3_cost_overrun_vs_progress.png`
- `outputs/member3_cost_overrun_vs_expenditure.png`

## 9. Unresolved Issues
- `sector` and `ministry` are missing at the project level in Table 6. Need mapping from other sources.
- Extreme expenditure outliers require domain verification to ensure they aren't MoSPI data entry typos.

## 10. Handoff & Next Steps
- **For Member 4 (Time ML)**: Note the leakage rules. Do not use `revised_completion_date` as an input feature for your time-delay model.
- **For Member 5 (Risk)**: You can use the binary probabilities output by the Day-2 Cost Model as one of the inputs to the final Risk Score.
- **For Member 6 (Dashboard)**: Ensure the frontend displays the SHAP explainability charts that will be generated tomorrow.

---

### WHAT MEMBER 3 WILL BUILD ON DAY 2:
I will build a scikit-learn pipeline to preprocess the categorical features (`state`, `agency`), train an **XGBoost Classifier** to predict the `cost_overrun_flag`, evaluate it using F1/ROC-AUC, and extract feature importance using **SHAP values**.
