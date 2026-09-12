# ML Feature Map — PAIMANA Dataset

This document categorizes variables available in the `paimana_master_v1.csv` dataset for predictive modeling by Member 3 (Cost) and Member 4 (Time).

## Categorization Classes
- **SAFE INPUT**: Features safely known at or before prediction time. No leakage risk.
- **POTENTIAL INPUT**: Features whose availability depends on the time of prediction (e.g., current physical progress).
- **TARGET/OUTCOME**: Variables to be predicted.
- **HIGH LEAKAGE RISK**: Features that directly define or strongly correlate with the outcome and would not be known at prediction time.
- **REQUIRES VERIFICATION**: Needs more domain context before use.

---

## 1. Cost & Financial Features

### `original_cost`
- **Data Type**: Float (₹ Crore)
- **Source**: PDF Column 6 (Line 1)
- **Meaning**: The initially approved estimated cost of the project.
- **ML Use**: Baseline cost predictor. Larger projects may have inherently higher risks.
- **Leakage Risk**: None.
- **Classification**: **SAFE INPUT**

### `revised_cost`
- **Data Type**: Float (₹ Crore)
- **Source**: PDF Column 6 (Line 2)
- **Meaning**: The latest updated estimated cost of the project.
- **Target Use**: Used to define if a cost overrun occurred (`revised_cost > original_cost`).
- **Leakage Risk**: High. If used as an input to predict cost overrun, the model will just learn `if revised_cost > original_cost then overrun = 1`.
- **Classification**: **TARGET/OUTCOME / HIGH LEAKAGE RISK**

### `cumulative_expenditure`
- **Data Type**: Float (₹ Crore)
- **Source**: PDF Column 7
- **Meaning**: Total money spent so far on the project.
- **ML Use**: When compared to physical progress, can indicate financial health.
- **Leakage Risk**: Low, provided the prediction is made "as of" the reporting month.
- **Classification**: **POTENTIAL INPUT**

---

## 2. Schedule & Time Features

### `approval_date`
- **Data Type**: String (YYYY-MM)
- **Source**: PDF Column 4 (Line 1)
- **Meaning**: Date the project was initially approved.
- **ML Use**: Can be used to extract seasonality (approval month) or macro-economic conditions (approval year).
- **Leakage Risk**: None.
- **Classification**: **SAFE INPUT**

### `start_date`
- **Data Type**: String (YYYY-MM)
- **Source**: PDF Column 4 (Line 2)
- **Meaning**: Actual project start date.
- **ML Use**: Used to calculate actual delays before the project even started.
- **Classification**: **SAFE INPUT**

### `original_completion_date`
- **Data Type**: String (YYYY-MM)
- **Source**: PDF Column 5 (Line 1)
- **Meaning**: The initially planned completion date.
- **ML Use**: Used alongside approval date to compute `original_duration_months`.
- **Classification**: **SAFE INPUT**

### `revised_completion_date`
- **Data Type**: String (YYYY-MM)
- **Source**: PDF Column 5 (Line 2)
- **Meaning**: The newly expected or actual completion date.
- **Target Use**: Used to define time overrun (`revised_completion_date > original_completion_date`).
- **Leakage Risk**: High. Including this feature directly leaks whether a time overrun occurred.
- **Classification**: **TARGET/OUTCOME / HIGH LEAKAGE RISK**

### `original_duration_months` (Derived)
- **Data Type**: Float
- **Meaning**: `original_completion_date - approval_date`.
- **ML Use**: Helps models understand the scale and complexity of the project.
- **Classification**: **SAFE INPUT**

---

## 3. Progress Features

### `physical_progress`
- **Data Type**: Float (%)
- **Source**: PDF Column 8
- **Meaning**: Reported physical completion percentage (0-100%).
- **ML Use**: Very strong indicator when combined with time elapsed or expenditure.
- **Leakage Risk**: Low, assuming prediction is for *future* overruns from the current snapshot.
- **Classification**: **POTENTIAL INPUT**

### `expenditure_percent` (Derived)
- **Data Type**: Float (%)
- **Meaning**: `(cumulative_expenditure / revised_cost) * 100`
- **Leakage Risk**: **HIGH**. It uses `revised_cost` in the denominator! If used as an input to predict cost overruns, it implicitly leaks the revised cost.
- **Classification**: **HIGH LEAKAGE RISK** (Use `cumulative_expenditure / original_cost` instead for safe ML inputs).

### `progress_gap` (Derived)
- **Data Type**: Float
- **Meaning**: `expenditure_percent - physical_progress`
- **Leakage Risk**: **HIGH**, because it relies on `expenditure_percent`, which relies on `revised_cost`.
- **Classification**: **HIGH LEAKAGE RISK**

---

## 4. Categorical Features

### `agency`
- **Data Type**: String
- **Meaning**: The executing body (e.g., NHAI, Railways).
- **ML Use**: Highly predictive. Certain agencies may have systemic delays or cost overruns.
- **Classification**: **SAFE INPUT**

### `state`
- **Data Type**: String
- **Meaning**: Geographical location of the project.
- **ML Use**: Proxy for local regulatory, environmental, and land acquisition challenges.
- **Classification**: **SAFE INPUT**

### `sector` / `ministry` (Implicit)
- **Data Type**: String (Not cleanly available yet)
- **Meaning**: Broad category (e.g., Road Transport, Petroleum).
- **Missing Data Concern**: Not extracted directly in Table 6. Will need mapping from Agency.
- **Classification**: **REQUIRES VERIFICATION**
