# Data Quality Report — PAIMANA Flash Report July 2026

## Source
- **File**: `FlashReport_July_2026.pdf`
- **Pages**: 153 total, Table 6 on pages 54–152
- **Stated ongoing projects**: 1,775

## Extraction Results

| Metric | Value |
|---|---|
| Projects stated by report | 1,775 |
| Projects extracted | **1,775** |
| Unique Sl.No count | 1,775 |
| Missing Sl.Nos | **0** |
| Duplicate Sl.Nos | **0** |
| Skipped rows | 0 |
| Max Sl.No | 1,775 |
| Min Sl.No | 1 |

### Previous Extraction Gap — Resolved

A previous automated extraction produced 1,758 rows (17 missing). The suspicious Sl.Nos were:
`470, 524, 525, 526, 527, 528, 1710, 1711, 1712, 1713, 1714, 1715, 1716, 1717, 1718, 1719, 1720`

**Investigation**: All these Sl.Nos were successfully found in the current extraction:
- **Sl.No 470** (page 77): Multi-line project name with long agency text
- **Sl.Nos 524–528** (page 80): Railway projects with long names and multi-line cells
- **Sl.Nos 1709–1713** (page 149): Multi-state telecom projects with very long state fields containing multiple embedded state names separated by newlines

**Root cause**: The previous extraction likely used a tool that failed to handle multi-line cells, cells with embedded newlines in the state field, or page-break continuations. The current extraction using `pdfplumber` with `extract_tables()` handles these correctly.

**Status**: ✅ Fully reconciled. All 1,775 projects extracted.

## Validation Results

| Check | Result |
|---|---|
| Row count | ✅ 1,775 matches expected |
| Missing project IDs | ✅ 0 |
| Duplicate project IDs | ✅ 0 |
| Missing approval_date | ⚠️ 12 rows (0.7%) |
| Missing revised_completion_date | ⚠️ 348 rows (19.6%) — expected, "-" means not revised |
| Negative costs | ✅ 0 |
| Reversed dates (approval > completion) | ⚠️ 3 rows |
| Duplicate project names | ⚠️ 1 name shared by 2 rows |
| Missing project_name | ✅ 0 |
| Missing state | ✅ 0 |
| Missing original_cost | ✅ 0 |
| Missing revised_cost | ✅ 0 |
| Missing cumulative_expenditure | ✅ 0 |
| Missing physical_progress | ✅ 0 |

## Missing Value Summary

| Field | Missing Count | % | Notes |
|---|---|---|---|
| sl_no | 0 | 0% | |
| project_name | 0 | 0% | |
| agency | 0 | 0% | |
| project_code | 0 | 0% | |
| state | 0 | 0% | |
| approval_date | 12 | 0.7% | Source PDF has "-" for these |
| start_date | 0 | 0% | |
| original_completion_date | 0 | 0% | |
| revised_completion_date | 348 | 19.6% | "-" = not revised, stored as null |
| original_cost | 0 | 0% | |
| revised_cost | 0 | 0% | |
| cumulative_expenditure | 0 | 0% | |
| physical_progress | 0 | 0% | |

## Derived Feature Summary

| Feature | Non-null | Mean | Min | Max |
|---|---|---|---|---|
| cost_overrun (binary) | 1,775 (100%) | 0.27 | 0 | 1 |
| cost_overrun_percent | 1,775 (100%) | 10.19% | -99.96% | 1,921.01% |
| expenditure_percent | 1,775 (100%) | 69.58% | 0% | 42,080% |
| progress_gap | 1,775 (100%) | 10.58 | -100.0 | 42,057.36 |
| original_duration_months | 1,763 (99.3%) | 56.2 | -1,458 | 513 |
| revised_duration_months | 1,426 (80.3%) | 79.2 | 2 | 537 |
| time_overrun_months | 1,427 (80.4%) | 23.0 | -356 | 300 |

### Cost Overrun Distribution
- **No overrun (0)**: 1,293 projects (72.8%)
- **Has overrun (1)**: 482 projects (27.2%)

## Issues to Note

1. **3 rows with reversed dates**: approval_date > original_completion_date — likely data entry issues in the source.
2. **Extreme outlier values** in expenditure_percent (max 42,080%) and progress_gap — likely projects where expenditure vastly exceeds revised cost. These should be investigated but not removed.
3. **Negative original_duration_months** (min -1,458) — likely caused by approval_date being entered incorrectly in the source PDF.
4. **1 duplicate project name** — two different projects (different Sl.Nos) share the same name. Both are retained.

## Corrections Made
- Whitespace normalized (newlines collapsed to spaces)
- Multi-state fields collapsed (newlines to commas)
- Dates normalized from MM/YYYY to YYYY-MM
- Currency values stripped of commas
- Percentage symbols removed
- "-" values converted to null (NOT to zero)

## Unresolved Issues
- Reversed dates not corrected (source data issue)
- Extreme outliers not removed (need domain review)
- Ministry/sector not extracted at project level (not reliably present in Table 6)

> TODO: Verify reversed date records against the PAIMANA portal.
> TODO: Investigate extreme expenditure outliers with domain experts.
