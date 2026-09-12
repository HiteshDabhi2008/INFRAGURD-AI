# Data Leakage Prevention — InfraGuard-AI

## What Is Data Leakage?

Data leakage occurs when information from the prediction target (outcome) is accidentally included as an input feature during model training. This makes the model appear to perform well during training but fail in real-world use because the "leaked" information would not be available at prediction time.

## Leakage Risks in PAIMANA Data

### Cost Overrun Prediction (Member 3)

**Target variable**: `cost_overrun` (binary: 1 if revised_cost > original_cost)

**DO NOT use as input features**:
| Variable | Reason |
|---|---|
| `revised_cost` | Directly defines cost overrun — it IS the outcome |
| `cost_overrun_percent` | Derived from revised_cost |
| `expenditure_percent` | Uses revised_cost in its calculation |

**SAFE to use as input features**:
| Variable | Reason |
|---|---|
| `original_cost` | Known at project approval time |
| `approval_date` | Known at project start |
| `original_completion_date` | Known at project approval |
| `state` | Known at project start |
| `agency` | Known at project start |
| `sector` | Known at project start (if available) |
| `original_duration_months` | Derived from approval + original completion |
| `physical_progress` | Observable at monitoring point |
| `cumulative_expenditure` | Observable at monitoring point |

> **Note**: `cumulative_expenditure` can be used as an input because it represents money already spent (observable), not the final cost revision decision.

### Time Overrun Prediction (Member 4)

**Target variable**: `time_overrun_months` or binary flag (did project extend beyond original_completion_date?)

**DO NOT use as input features**:
| Variable | Reason |
|---|---|
| `revised_completion_date` | Directly defines time overrun — it IS the outcome |
| `revised_duration_months` | Derived from revised_completion_date |
| `time_overrun_months` | Derived from revised_completion_date |

**SAFE to use as input features**:
| Variable | Reason |
|---|---|
| `original_cost` | Known at project start |
| `approval_date` | Known at project start |
| `original_completion_date` | Known at project start |
| `start_date` | Known at project start |
| `state`, `agency` | Known at project start |
| `original_duration_months` | Known at project start |
| `physical_progress` | Observable at monitoring point |
| `cumulative_expenditure` | Observable at monitoring point |

## General Rules

1. **Separate features from targets before training**. Never include target-derived columns in the feature matrix.

2. **Think about what is known at prediction time**. A production system would predict risk for an *ongoing* project. Only use information that would realistically be available at that point.

3. **Document all features used**. Each model must list its input features and explain why each is valid.

4. **Use cross-validation properly**. Ensure no data from the test set leaks into the training set.

5. **Be careful with aggregate features**. If you derive sector-level averages, ensure these are computed only on training data, not the full dataset.

## Quick Reference

```
╔════════════════════════════════════╗
║        FEATURE SEPARATION          ║
╠════════════════════════════════════╣
║                                    ║
║  INPUT FEATURES     TARGET/OUTCOME ║
║  ───────────────    ────────────── ║
║  original_cost      revised_cost   ║
║  approval_date      revised_doc    ║
║  original_doc       cost_overrun   ║
║  start_date         time_overrun   ║
║  state, agency                     ║
║  physical_progress                 ║
║  cum_expenditure                   ║
║  original_duration                 ║
║                                    ║
╚════════════════════════════════════╝
```
