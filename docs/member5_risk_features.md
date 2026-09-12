# Risk Feature Analysis (Member 5)

This document audits potential risk variables for the Early Warning System, explicitly categorizing data leakage threats.

## 1. Verified PAIMANA Indicators

### `original_cost`
- **Leakage Risk**: NONE. Set at approval.
- **Utility**: Defines project scale. Mega-projects inherently carry more complexity risk.

### `original_duration_months`
- **Leakage Risk**: NONE.
- **Utility**: Longer projects are exposed to more macroeconomic volatility.

### `state` & `agency`
- **Leakage Risk**: NONE.
- **Utility**: Proxies for administrative efficiency and terrain complexity.

### `physical_progress`
- **Leakage Risk**: LOW (Valid for implementation-time predictions).
- **Utility**: Critical indicator of actual on-ground execution.

### `cumulative_expenditure`
- **Leakage Risk**: LOW.
- **Utility**: Crucial when compared against `original_cost` and `physical_progress` to find dissonant stalling (spending without building).

## 2. High Leakage Indicators (DO NOT USE AS ML INPUTS)

The following variables mathematically define the risk outcomes. Feeding them into a prediction model guarantees 100% false accuracy (Data Leakage).

- **`revised_cost`**: Directly leaks cost overruns.
- **`revised_completion_date`**: Directly leaks schedule overruns.
- **`cost_change` / `cost_overrun_%`**: IS the target.
- **`time_overrun` / `time_overrun_%`**: IS the target.
- **`expenditure_percent` (if derived as Exp/Rev_Cost)**: Leaks the revised cost in the denominator.
- **`revised_duration`**: Leaks the revised completion date.

## 3. External Variables Research

To build a truly robust Risk Engine in later iterations, we must ingest external datasets.

### A. Pre-Construction Blockers
- **Land Acquisition Status**
  - *Why*: The #1 reason for project stalling in India.
  - *PAIMANA Availability*: No.
  - *External Source*: State Revenue Departments / Bhoomi portals.
- **Environmental & Forest Clearances**
  - *Why*: Strict regulatory requirements can stall projects in eco-sensitive zones for years.
  - *PAIMANA Availability*: No.
  - *External Source*: PARIVESH portal (MoEFCC).

### B. Execution Blockers
- **Weather / Flood Data**
  - *Why*: Heavy monsoons physically halt civil works.
  - *PAIMANA Availability*: No.
  - *External Source*: IMD (Indian Meteorological Department) API.
- **Utility Shifting**
  - *Why*: Waiting for local bodies to move power/water lines.
  - *PAIMANA Availability*: No.
  - *External Source*: PM GatiShakti NMP portals.

### C. Financial & Macro Risks
- **Inflation / Material Prices (Steel, Cement)**
  - *Why*: Sharp increases destroy contractor margins, leading to abandoned works.
  - *PAIMANA Availability*: No.
  - *External Source*: Wholesale Price Index (WPI) via data.gov.in.
- **Contractor Performance History**
  - *Why*: Repeated defaults by specific vendors.
  - *PAIMANA Availability*: No.
  - *External Source*: MCA (Ministry of Corporate Affairs) or agency blacklists.
