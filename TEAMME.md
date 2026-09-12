# TEAMME.md - InfraGuard-AI

## Project Overview
InfraGuard-AI is an AI-powered predictive analytics and early-warning platform for PAIMANA infrastructure project monitoring.

**PAIMANA**: The PAIMANA (Project Appraisal, Infrastructure, Monitoring, and Analysis) system is a framework for monitoring central sector infrastructure projects.
**MoSPI Problem Statement 26103**: Use case on web-based integrated project-monitoring platform.
**Purpose**: To develop a web-based platform that leverages predictive analytics to monitor infrastructure projects, predict cost and time overruns, and generate early warnings to mitigate risks.
**System Predictions**: The system will predict the likelihood of cost overruns and time overruns for ongoing infrastructure projects.
**Early Warnings**: The system provides early warnings by combining cost and time risks with physical progress and expenditure mismatches, generating a comprehensive project risk score and actionable alerts.

## Main Objectives
1. Cost-overrun prediction
2. Time-overrun prediction
3. Project risk scoring
4. Early-warning alerts
5. Project/sector/state analytics
6. Explainable AI
7. AI/LLM-based project intelligence assistant
8. Interactive web dashboard

## Team Structure & Responsibilities

The team consists of exactly 6 members.

### Member 1 — Data Engineering
**Responsibilities:**
- PAIMANA PDF/data extraction
- Data cleaning
- Missing-value handling
- Duplicate checking
- Date/cost normalization
- Data dictionary
- ML-ready dataset

**Expected Files:**
- `data/raw/`
- `data/processed/`
- `notebooks/01_data_cleaning.ipynb`
- `docs/data_dictionary.md`

### Member 2 — Data Analysis & Research
**Responsibilities:**
- Exploratory Data Analysis (EDA)
- Statistical analysis
- Sector/ministry/state analysis
- Correlation analysis
- Feature engineering
- CUF vs additional-variable analysis
- Research findings

**Expected Files:**
- `notebooks/02_eda.ipynb`
- `src/analysis/`
- `docs/research.md`

### Member 3 — Cost Overrun ML
**Responsibilities:**
- Define cost-overrun target
- Feature preparation
- Train baseline models
- Compare Logistic Regression, Random Forest and XGBoost/CatBoost if appropriate
- Evaluate Accuracy, Precision, Recall, F1 and ROC-AUC
- Select the best model
- Add SHAP/explainability where practical

**Expected Files:**
- `notebooks/03_cost_model.ipynb`
- `src/models/cost_model.py`
- `models/cost_model.pkl`

> **IMPORTANT:** Avoid data leakage. Do not use future/outcome variables such as revised cost as an input when predicting whether cost will overrun.

### Member 4 — Time Overrun ML
**Responsibilities:**
- Define time-overrun target
- Calculate delay using original and revised completion dates
- Train classification/regression models
- Compare models
- Evaluate performance
- Select the best model
- Add explainability

**Expected Files:**
- `notebooks/04_time_model.ipynb`
- `src/models/time_model.py`
- `models/time_model.pkl`

> **IMPORTANT:** Avoid using revised completion date as a predictive input when it represents the outcome being predicted.

### Member 5 — Risk & Early Warning
**Responsibilities:**
- Combine cost risk
- Combine time risk
- Analyse physical progress
- Analyse expenditure/progress mismatch
- Build project risk score
- Define Low/Moderate/High/Critical categories
- Create early-warning rules
- Generate recommended actions

**Expected Files:**
- `src/risk/risk_engine.py`
- `src/risk/early_warning.py`
- `docs/risk_methodology.md`

> **NOTE:** Risk thresholds must be clearly documented as our prototype methodology unless supported by official PAIMANA/MoSPI documentation.

### Member 6 — Website, Dashboard & AI
**Responsibilities:**
- Streamlit dashboard
- Plotly visualizations
- Project search/filtering
- Risk dashboard
- Project detail page
- ML model integration
- SHAP visualization
- AI/LLM assistant
- RAG if required
- Final deployment preparation

**Expected Structure:**
- `dashboard/app.py`
- `dashboard/pages/`
- `dashboard/components/`
- `chatbot/`

> **NOTE:** The AI assistant must answer using verified PAIMANA/project data and must not invent project facts.

## Project Architecture

```text
PAIMANA DATA
     ↓
DATA INGESTION
     ↓
DATA CLEANING & VALIDATION
     ↓
FEATURE ENGINEERING
     ↓
 ┌───────────────┬────────────────┐
 ↓               ↓                ↓
COST ML        TIME ML       DATA ANALYTICS
 ↓               ↓                ↓
 └───────────────┴────────────────┘
                 ↓
            RISK ENGINE
                 ↓
         EARLY WARNING SYSTEM
                 ↓
       EXPLAINABLE AI / SHAP
                 ↓
          STREAMLIT DASHBOARD
                 ↓
          AI PROJECT ASSISTANT
```

## Data Rules
The current project uses a July 2026 PAIMANA Flash Report as a sample dataset.

**Important:**
The July report is a monthly snapshot. It can be used for EDA, prototype development, risk classification, dashboard demonstration, and initial ML experiments. But do NOT claim that a single monthly snapshot is sufficient for production-quality time-series early-warning prediction. The final system should be designed so that future monthly PAIMANA records can be added.

**Supported Data Layer Entities:**
Project ID, Project Name, Agency, Ministry, Sector, State, Approval Date, Original Completion Date, Revised Completion Date, Original Cost, Revised Cost, Cumulative Expenditure, Physical Progress, Milestones/status where available.

**Derived Features May Include:**
`cost_overrun`, `cost_overrun_percent`, `expenditure_percent`, `progress_gap`, `original_duration_months`, `revised_duration_months`, `time_overrun_months`.

## Machine Learning Rules
Clearly document data leakage prevention.

**DO NOT use:**
- `revised_cost`
- `revised_completion_date`
as predictive features when these variables represent the outcome being predicted. Use only information that would realistically be available at the prediction point.

**Separate:**
- Features
- Targets
- Derived outcome variables

## Common Interface
Define a common prediction format so that all modules can integrate. For each project, the system should eventually be able to produce:

```json
{
  "project_id": "",
  "cost_risk_probability": 0.0,
  "time_risk_probability": 0.0,
  "risk_score": 0,
  "risk_category": "",
  "early_warning": [],
  "explanation": []
}
```
*Do not hard-code fake predictions.*

## Development Workflow
The team has only 4 days. Work must happen in parallel.

- **Day 1**: Discovery + environment + initial data + model prototypes + dashboard skeleton.
- **Day 2**: Data cleaning + EDA + ML models + risk engine + dashboard development.
- **Day 3**: Integration of all modules + explainability + AI assistant + testing.
- **Day 4**: Final testing + deployment + presentation + demo preparation.

## Git Workflow
Recommended branches: `main`, `dev`, `feature/data`, `feature/eda`, `feature/cost-model`, `feature/time-model`, `feature/risk`, `feature/dashboard-ai`.

**Rules:**
- Never directly push experimental work to `main`.
- Use meaningful commit messages (e.g., `feat: add cost overrun model`, `fix: handle missing completion dates`, `docs: update data dictionary`).
- Pull/rebase before major integration.
- Do not commit `.env`, API keys or large raw datasets.
- Keep interfaces between modules stable.

## Definition of Done
A module is considered complete only when:
1. Code runs without errors.
2. Input/output format is documented.
3. Basic testing is completed.
4. No API keys/secrets are committed.
5. Results are reproducible.
6. The module can be integrated with the main dashboard.
7. Limitations are documented.

## Important Note
Do not invent PAIMANA data, official thresholds, official MoSPI methodologies, API endpoints, or performance results. If information is unavailable, write:
`TODO: Verify with official PAIMANA/MoSPI source.`
Keep the architecture modular and beginner-friendly.
