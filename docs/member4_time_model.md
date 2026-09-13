# Member 4: Time Overrun Prediction Model — Documentation
# ========================================================

## 1. Prediction Target

### Primary: Classification — `time_overrun_flag`
- **Calculation**: `1` if `revised_completion_date > original_completion_date`, else `0`.
- **Rationale**: The problem statement (26103) asks for an early-warning system. A binary classifier that outputs the *probability* of schedule delay is the most actionable metric for dashboard ranking and risk triage.

### Secondary: Regression — `time_overrun_months`
- **Calculation**: `(revised_completion_date - original_completion_date).days / 30.44`
- **Rationale**: Quantifies the severity of the delay. Useful for financial planning and penalty estimation. Trained only on the full dataset (not just delayed projects) to avoid selection bias.

## 2. Prediction Point

**Implementation-Time Early Warning (Recommended by Day-1 analysis)**

The model is designed to answer: *"Given this project's current state in the monthly PAIMANA snapshot, will it miss its original deadline?"*

Available information at this point:
- Original cost, planned duration, approval date
- Current physical progress, cumulative expenditure
- Project age (days since approval)
- Agency, state, sector, project size

**NOT available** (would constitute future information):
- The revised completion date itself
- Any derived metric that uses `revised_completion_date`

## 3. Data Leakage Audit

### Excluded Features (HIGH LEAKAGE RISK for time prediction):
| Feature | Reason |
|---------|--------|
| `revised_completion_date` | Directly defines the target |
| `revised_duration_days` | Derived from `revised_completion_date` |
| `time_overrun_months` | IS the regression target |
| `time_overrun_flag` | IS the classification target |
| `revised_cost` | Known only after revisions; partially correlated with schedule revisions |
| `cost_change` | Derived from `revised_cost` |
| `cost_change_percent` | Derived from `revised_cost` |
| `expenditure_percent` (Day-1 version) | Uses `revised_cost` in denominator |
| `progress_gap` (Day-1 version) | Derived from leaky `expenditure_percent` |

### Safe Input Features:
| Feature | Type | Rationale |
|---------|------|-----------|
| `original_cost` | Numeric | Baseline cost known at approval |
| `project_age_days` | Numeric | Days since approval to snapshot date |
| `physical_progress` | Numeric | Current reported completion % |
| `cumulative_expenditure` | Numeric | Total spend to date |
| `safe_expenditure_percent` | Numeric | `cumulative_expenditure / original_cost * 100` |
| `safe_progress_gap` | Numeric | `safe_expenditure_percent - physical_progress` |
| `original_duration_days` | Numeric | `original_completion_date - approval_date` |
| `state` | Categorical | Geographic location |
| `agency` | Categorical | Executing body |
| `sector` | Categorical | Inferred from agency/project name |
| `project_size_category` | Categorical | Small / Medium / Large |

## 4. Temporal Limitation

> **WARNING**: This model is trained on a single cross-sectional snapshot (July 2026). In this snapshot, both completed and ongoing projects coexist. A project with `physical_progress=100%` and a known `revised_completion_date` is fundamentally different from an early-stage project whose outcome is truly unknown.
>
> A production-grade early-warning system requires **multiple historical monthly PAIMANA/OCMS snapshots** so the model can learn temporal progressions (e.g., predicting month T+12 outcomes from month T features).
>
> The current model should be treated as a **prototype point-in-time evaluator**, not a validated temporal forecaster.

## 5. Risk Thresholds

The `predict_time_risk()` function maps classifier probability to risk levels:

| Probability Range | Risk Level |
|-------------------|------------|
| > 0.70 | HIGH |
| 0.40 – 0.70 | MEDIUM |
| < 0.40 | LOW |

**These thresholds are internal project conventions, NOT official MoSPI thresholds.** They should be calibrated against domain expert feedback and historical outcomes in a production deployment.
