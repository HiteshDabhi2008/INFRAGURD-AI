# Risk Scoring Engine (Member 5)

This document details the prototype calculations for the internal Risk Scoring Engine applied to the PAIMANA July 2026 dataset.

## The Composite Score Methodology

The `total_risk_score` (ranging from 0 to 9) is the sum of three independent 3-point sub-scores:

### 1. Cost Risk Score (0-3)
Evaluates financial overrun severity.
- **Score 3**: Cost Overrun > 50%
- **Score 2**: Cost Overrun > 15%
- **Score 1**: Cost Overrun > 0%
- **Score 0**: No overrun (or cost decrease).

### 2. Time Risk Score (0-3)
Evaluates schedule extension severity relative to the original planned duration.
- **Score 3**: Time Overrun > 50% of original duration
- **Score 2**: Time Overrun > 20% of original duration
- **Score 1**: Time Overrun > 0%
- **Score 0**: No delay.

### 3. Progress Gap Risk Score (0-3)
Evaluates execution dissonance (spending money without achieving physical progress).
*Progress Gap = (Cumulative Expenditure / Original Cost) - Physical Progress*
- **Score 3**: Gap > 30% (Severe financial drain without assets on ground).
- **Score 2**: Gap > 15%
- **Score 1**: Physical Progress < 5% AND Gap > 5% (Early stalling indicator).
- **Score 0**: Healthy alignment between spend and progress.

## Risk Categorization

The `total_risk_score` is then bucketed into actionable categories:
- **CRITICAL**: Score 7 to 9. Requires immediate MoSPI intervention/audit.
- **HIGH**: Score 4 to 6. High probability of significant failure.
- **MEDIUM**: Score 2 to 3. Early friction detected.
- **LOW**: Score 0 to 1. On track.

## Results on PAIMANA July 2026

Applying this prototype algorithm via `src/data/eda_member5.py` yielded:
- **106 Projects** classified as **CRITICAL**.
- These projects represent the most toxic assets in the portfolio, exhibiting massive cost overruns, doubling of schedules, and severe financial-progress gaps simultaneously.

*A list of the top 20 most critical projects has been exported to `outputs/member5_critical_projects.csv`.*
