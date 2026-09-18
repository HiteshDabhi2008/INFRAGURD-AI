# Member 2: Day 3 Findings

## 1. Key EDA Findings
- **Projects by State**: Maharashtra, Uttar Pradesh, and Multi-State projects dominate the portfolio in volume and cost.
- **Projects by Sector (Inferred)**: Roads & Highways and Railways constitute the vast majority of infrastructure projects.
- **Cost Escalation**: A significant number of projects have zero cost change, but a long tail exists where cost increases drastically. Multi-state and Water Resources projects show the highest cost escalations.
- **Physical Progress vs Expenditure**: Most projects have expenditure closely matching physical progress. However, projects where expenditure far exceeds physical progress (progress gap < 0) are critical risk areas.
- **Project Age**: Project age varies widely, but older projects (long duration since approval) don't consistently show higher physical progress, indicating systemic delays rather than just immaturity.

## 2. Final Features
- **Cost ML**: `original_cost`, `project_age_days`, `physical_progress`, `safe_expenditure_percent`, `state`, `agency`, `sector`, `original_duration_days`, `project_size_category`.
- **Time ML**: `approval_date`, `original_completion_date`, `original_duration_days`, `project_age_days`, `physical_progress`, `safe_expenditure_percent`, `safe_progress_gap`, `original_cost`, `state`, `agency`, `sector`.
- **Risk Engine**: Cost indicators, `safe_expenditure_percent`, `physical_progress`, `safe_progress_gap`, `project_age_days`, schedule indicators, `project_size_category`, geographic/agency metadata.

## 3. Leakage Warnings
- **Cost Models**: DO NOT USE `revised_cost`, `cost_change`, `cost_change_percent`, `cost_overrun`, `cost_overrun_percent`, `expenditure_percent` (if derived from revised cost), or `progress_gap` (if derived from revised cost).
- **Time Models**: DO NOT USE `revised_completion_date`, `time_overrun`, `time_overrun_months`, `revised_duration_days`, or `revised_duration_months`.

## 4. External Variables
- **Wholesale Price Index (WPI)**: 
  - *Why it matters*: Useful for modeling material inflation.
  - *Data Source*: MoSPI (Office of the Economic Adviser).
  - *Update Frequency*: Monthly.
  - *Geographical level*: National.
  - *Join method*: Join on `report_month`.
  - *Availability*: Freely available for our prototype.
- **Rainfall / Monsoon Data**: 
  - *Why it matters*: Identifies weather-induced delays in construction.
  - *Data Source*: IMD (India Meteorological Department).
  - *Update Frequency*: Daily/Monthly.
  - *Geographical level*: State/Sub-division.
  - *Join method*: Join on `state` and `report_month`.
  - *Availability*: Available, but requires scraping or APIs.
- **State-level Ease of Doing Business**: 
  - *Why it matters*: Acts as a categorical risk proxy for land acquisition.
  - *Data Source*: DPIIT.
  - *Update Frequency*: Annual.
  - *Geographical level*: State.
  - *Join method*: Join on `state`.
  - *Availability*: Available as an annual report for prototype.

## 5. Recommendations
- **M3 (Cost ML)**: Predict `cost_overrun` (binary) or `cost_change` (regression). Base expenditure ratios on `original_cost` to avoid leakage.
- **M4 (Time ML)**: Predict `time_overrun_months` or delay probability. Leverage `project_age_days` and `original_duration_days` to capture project velocity.
- **M5 (Risk Engine)**: Flag projects with high `safe_expenditure_percent` but low `physical_progress`. Use multi-state status as a systemic risk multiplier.

## 6. Limitations
The current dataset represents a **single monthly snapshot** (July 2026). Consequently, the ML features map static points in time rather than trajectories. Future predictive modeling will improve significantly when multiple monthly snapshots are collected, allowing models to learn temporal dynamics and changes over time.
