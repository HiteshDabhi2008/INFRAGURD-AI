# Member 5 - Day 3 Final Risk Scoring & Early Warning Engine

This document details the final Risk Scoring Engine implemented for the InfraGuard-AI platform. It successfully aggregates multi-modal indicators into a single actionable risk profile per project.

## Risk Methodology

The overall risk engine (`src/risk/risk_engine.py`) takes a composite approach to risk scoring by merging ML-based predictions with deterministic rules. 

### Inputs
1. **Cost Predictor (M3)**: Probabilities and risk brackets regarding budget overruns.
2. **Time Predictor (M4)**: Probabilities and risk brackets regarding schedule delays.
3. **Financial & Progress Indicators**: 
   - `safe_expenditure_percent`: Controls for budget revisions to accurately measure expenditure velocity against the original baseline.
   - `physical_progress`: Actual completion state on the ground.
   - `progress_gap`: The difference between financial expenditure and physical progress.
4. **Schedule Indicators**:
   - `project_age_days` and `original_duration_days` measure time elapsed versus time budgeted.

### Risk Categories
Using a weighted point system (defined fully in `docs/member5_risk_thresholds.md`), projects are classified into one of four distinct categories:
* **LOW**
* **MEDIUM**
* **HIGH**
* **CRITICAL**

## Early Warnings
In addition to a broad category, the engine generates specific diagnostic warnings (`src/risk/risk_rules.py`). Triggers include:
* **High Predictive Cost/Time Risk** (Probability > 0.70)
* **Expenditure Mismatch** (Financials outpacing physical completion by >20%)
* **Stagnation Near Deadline** (>80% time elapsed, but <50% completed)
* **Multiple Simultaneous Indicators** (Meta-warning for compound risk)

## Explanation Generation
The engine automatically generates a human-readable explanation (`src/risk/risk_explanation.py`) for the dashboard. It consolidates the active early-warning triggers into a bulleted summary, allowing stakeholders to understand exactly *why* a project received a CRITICAL or HIGH score without needing to inspect the underlying model probabilities manually.

## Testing & Outputs
The engine was run across the entire 1,763 project portfolio. 
The outputs generated for dashboard consumption include:
* `outputs/member5/high_risk_projects.csv` (Filtered high-priority lists)
* `outputs/member5/early_warning_results.csv` (Projects with active warning triggers)
* `outputs/member5/risk_summary.csv` (Aggregate counts)
* `outputs/member5/risk_distribution.png` (Visual distribution graph)

## Limitations
* **Prototype Thresholds**: The current thresholds (e.g., gap > 20% or probability > 0.70) are **Prototype / Proposed** heuristics designed for the proof-of-concept. They should be validated against official MoSPI/IPMD audit guidelines before production use.
* **Single Snapshot Reliance**: The engine operates purely on cross-sectional data (a single month's snapshot). True early-warning systems benefit significantly from time-series analysis (e.g., tracking the month-over-month *acceleration* of the progress gap).
