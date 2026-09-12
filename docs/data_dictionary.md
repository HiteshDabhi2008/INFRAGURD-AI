# Data Dictionary — InfraGuard-AI (PAIMANA Flash Report)

## Source
- **Report**: PAIMANA Flash Report, July 2026
- **Publisher**: Ministry of Statistics and Programme Implementation (MoSPI)
- **Portal**: https://paimana-proj.mospi.gov.in
- **Table**: Table 6 — All Ongoing Projects
- **Scope**: Central Sector Infrastructure Projects costing ₹150 crore & above

## Master Dataset: `paimana_master_v1.csv`

### Raw Fields (from PDF)

| Field | Type | Meaning | Source | Missing Treatment | Example |
|---|---|---|---|---|---|
| `sl_no` | Int | Serial number in flash report | PDF Sl.No column | None expected | `1` |
| `project_name` | String | Name of the infrastructure project | PDF Column 2 (parsed) | None expected | `Construction of New Terminal at Kadapa Airport` |
| `agency` | String | Implementing agency | PDF Column 2 (parsed, parenthesized) | None expected | `Airport Authority of India [AAI]` |
| `project_code` | String | PAIMANA project code | PDF Column 2 (parsed, numeric in parens) | Rare missing | `612786` |
| `state` | String | State/UT or "PAN India" / "Multi-States" | PDF Column 3 | None expected | `Andhra Pradesh` |
| `approval_date` | String (YYYY-MM) | Date of project approval | PDF Column 4 line 1 | 12 missing (0.7%) — left as null | `2023-03` |
| `start_date` | String (YYYY-MM) | Actual start date | PDF Column 4 line 2 (in parens) | Left as null if "-" | `2024-01` |
| `original_completion_date` | String (YYYY-MM) | Original/target date of completion | PDF Column 5 line 1 | None expected | `2026-01` |
| `revised_completion_date` | String (YYYY-MM) | Revised date of completion | PDF Column 5 line 2 (in parens) | 348 missing (19.6%) — "-" means not revised, left as null | `2026-09` |
| `original_cost` | Float | Original estimated cost (₹ crore) | PDF Column 6 line 1 | None expected | `265.91` |
| `revised_cost` | Float | Revised/current estimated cost (₹ crore) | PDF Column 6 line 2 (in parens) | None expected | `265.91` |
| `cumulative_expenditure` | Float | Total expenditure to date (₹ crore) | PDF Column 7 | None expected | `176.38` |
| `physical_progress` | Float | Physical progress percentage | PDF Column 8 | None expected | `80.0` |
| `source_page` | Int | PDF page number where this row was extracted | Extraction metadata | Always present | `55` |
| `report_month` | String | Month of the flash report | Extraction metadata | Always present | `July 2026` |
| `source_report` | String | Filename of source PDF | Extraction metadata | Always present | `FlashReport_July_2026.pdf` |

### Derived Fields

| Field | Type | Meaning | Formula | Missing Treatment | Example |
|---|---|---|---|---|---|
| `cost_overrun` | Int (0/1) | Binary flag: did cost increase? | `1 if revised_cost > original_cost else 0` | Null if either cost is missing | `1` |
| `cost_overrun_percent` | Float | Percentage cost increase | `((revised - original) / original) * 100` | Null if original_cost is 0 or missing | `35.2` |
| `expenditure_percent` | Float | Expenditure as % of revised cost | `(cumulative_expenditure / revised_cost) * 100` | Null if revised_cost is 0 or missing | `66.3` |
| `progress_gap` | Float | Gap between spending and physical progress | `expenditure_percent - physical_progress` | Null if either is missing | `-13.7` |
| `original_duration_months` | Float | Planned project duration in months | `months(original_completion_date - approval_date)` | Null if dates missing | `36` |
| `revised_duration_months` | Float | Revised project duration in months | `months(revised_completion_date - approval_date)` | Null if revised_completion_date is missing | `42` |
| `time_overrun_months` | Float | Time overrun in months | `months(revised_completion_date - original_completion_date)` | Null if revised_completion_date is missing | `6` |

## ⚠️ Data Leakage Warning

The following fields are **OUTCOME INDICATORS** and must **NOT** be used as predictive inputs in ML models:

- `revised_cost` → Defines cost overrun (target for Member 3)
- `revised_completion_date` → Defines time overrun (target for Member 4)
- `cost_overrun`, `cost_overrun_percent` → Derived targets
- `time_overrun_months` → Derived target

See [data_leakage.md](data_leakage.md) for full documentation.

## Notes

- All cost values are in **₹ crore (Indian Rupees, crore)**.
- Dates are normalized to **YYYY-MM** format.
- `"-"` in the source PDF means "not applicable" or "not revised" — stored as `null`.
- Missing values are **NOT** converted to zero.
- The July 2026 report is a **single monthly snapshot**. It is NOT a time series.

> TODO: Verify field definitions with official PAIMANA/MoSPI data dictionary if available.
