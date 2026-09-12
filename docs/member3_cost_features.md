# Cost Feature Research (Member 3)

This document catalogs the available features in the `paimana_master_v1.csv` dataset and their suitability as inputs for the Cost Prediction Model.

## Feature Classifications

### `original_cost`
- **Type**: Float (₹ Crore)
- **Meaning**: Initial approved budget.
- **Source**: PDF Column 6, Line 1
- **Usefulness**: High. Larger projects have higher complexity and historically higher risk of overrun.
- **Leakage Risk**: None. Known at approval.
- **Classification**: **SAFE INPUT**

### `original_duration_months`
- **Type**: Float
- **Meaning**: Planned project timeline (`original_completion_date` - `approval_date`).
- **Source**: Derived from PDF Column 4 and 5
- **Usefulness**: High. Longer projects are exposed to more macroeconomic shifts (inflation, election cycles).
- **Leakage Risk**: None.
- **Classification**: **SAFE INPUT**

### `state`
- **Type**: String (Categorical)
- **Meaning**: Project location.
- **Source**: PDF Column 3
- **Usefulness**: High. Proxies local regulatory efficiency, land acquisition challenges, and labor availability. Requires Target Encoding for ML.
- **Leakage Risk**: None.
- **Classification**: **SAFE INPUT**

### `agency`
- **Type**: String (Categorical)
- **Meaning**: Executing organization (e.g., NHAI, AAI).
- **Source**: PDF Column 2
- **Usefulness**: Very High. Different agencies have vastly different management efficiency and historical overrun rates. Requires Target/Frequency Encoding.
- **Leakage Risk**: None.
- **Classification**: **SAFE INPUT**

### `physical_progress`
- **Type**: Float (%)
- **Meaning**: Percentage of physical completion.
- **Source**: PDF Column 8
- **Usefulness**: Medium. Must be used carefully. A project at 99% progress with no overrun is safe; a project at 10% progress with 80% budget spent is failing. 
- **Leakage Risk**: Low, provided the model is meant to predict *future* overruns from the *current* snapshot.
- **Classification**: **POTENTIAL INPUT**

### `cumulative_expenditure`
- **Type**: Float (₹ Crore)
- **Meaning**: Total funds spent to date.
- **Source**: PDF Column 7
- **Usefulness**: High (when converted to a ratio against `original_cost`).
- **Leakage Risk**: Low, as it represents observable sunk costs, not the final revised budget.
- **Classification**: **POTENTIAL INPUT**

---

## High Leakage Risk Variables (DO NOT USE AS INPUTS)

### `revised_cost`
- **Meaning**: The new total budget.
- **Why it leaks**: This directly defines the target. If you know the revised cost, you mathematically know the overrun.
- **Classification**: **TARGET/OUTCOME (LEAKAGE)**

### `cost_overrun_percent` & `cost_change`
- **Meaning**: The calculated overrun.
- **Why it leaks**: It IS the target.
- **Classification**: **TARGET/OUTCOME (LEAKAGE)**

### `expenditure_percent`
- **Meaning**: `(cumulative_expenditure / revised_cost) * 100`
- **Why it leaks**: The denominator is `revised_cost`. Feeding this to a model implicitly feeds it the revised cost.
- **Alternative**: Calculate `safe_expenditure_percent = (cumulative_expenditure / original_cost) * 100`.

### `progress_gap`
- **Meaning**: `expenditure_percent - physical_progress`
- **Why it leaks**: Relies on the leaky `expenditure_percent`.
- **Alternative**: Calculate `safe_progress_gap = safe_expenditure_percent - physical_progress`.

---

## Missing / Future Features

- **Sector & Ministry**: Not extracted at project level in Table 6. Highly predictive (e.g., Railways vs Telecom). Requires mapping from Tables 1-2.
- **Macro-Economic Variables (External)**: Inflation (WPI), material costs. (See external data research).
