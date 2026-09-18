# Member 5 - Risk Engine and Early Warning System

## Objective
To synthesize the outputs from Member 1 (Data), Member 2 (Feature extraction), Member 3 (Cost Prediction), and Member 4 (Time Prediction) into a unified Risk Engine. The engine categorizes projects into risk levels and produces prioritized early warnings.

## Methodology

### 1. Risk Engine (`src/risk/risk_engine.py`)
- We merge the latest snapshots of cost predictions and time predictions with the underlying project progress and expenditure data.
- **Risk Score Formulation:**
  A composite 0-100 `risk_score` is computed using:
  - `cost_risk_weight` * `cost_overrun_percent`
  - `time_risk_weight` * `time_overrun_percent`
  - `mismatch_weight` * (Expenditure Percent - Physical Progress Percent)
- **Categorization:**
  - `CRITICAL`: Risk Score >= 75
  - `HIGH`: Risk Score >= 50
  - `MEDIUM`: Risk Score >= 25
  - `LOW`: Risk Score < 25

### 2. Early Warning Rules (`src/risk/risk_rules.py`)
Configurable thresholds are used to flag specific conditions:
- `COST_OVERRUN_HIGH`: > 20%
- `TIME_OVERRUN_HIGH`: > 20%
- `LOW_PROGRESS`: < 30% for projects older than 24 months.
- `EXPENDITURE_MISMATCH`: Expenditure leads progress by > 20%.

### 3. Natural Language Explanation (`src/risk/risk_explanation.py`)
For each project, an automated human-readable sentence is synthesized based on the rules violated, providing MoSPI decision-makers an immediate, easy-to-digest rationale for the assigned risk level.

## Execution
Run `python src/risk/risk_engine.py` to trigger the complete risk evaluation flow.

## Outputs
- `outputs/member5/risk_rankings.csv`: The master risk sheet with composite scores, categories, explanations, and priority ranks.
- `outputs/member5/high_risk_projects.csv`: Subset of projects flagged as CRITICAL or HIGH.
- `outputs/member5/risk_distribution.png`: Bar chart of risk category distribution.
- `outputs/member5/cost_vs_time_risk.png`: A bubble chart showing cost overrun vs. time overrun, with bubble size mapped to composite risk score.
