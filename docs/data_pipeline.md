# Data Pipeline Documentation — InfraGuard-AI

## Pipeline Overview

```text
FlashReport_July_2026.pdf  (Source PDF)
         ↓
    EXTRACTION            (src/data/extract.py)
         ↓
  paimana_raw_extracted.csv
         ↓
      CLEANING            (src/data/clean.py)
         ↓
   paimana_cleaned.csv
         ↓
     VALIDATION           (src/data/validate.py)
         ↓
  validation_report.txt
         ↓
    TRANSFORMATION        (src/data/transform.py)
         ↓
 ┌───────────────────┐
 │ paimana_master_v1  │   (data/processed/paimana_master_v1.csv)
 │ paimana_sample     │   (data/sample/paimana_sample.csv)
 └───────────────────┘
```

## Stage Details

### 1. Extraction (`src/data/extract.py`)
- **Input**: `data/raw/FlashReport_July_2026.pdf`
- **Output**: `data/processed/paimana_raw_extracted.csv`
- **Tool**: pdfplumber
- **Process**:
  - Opens the PDF and scans Table 6 (pages 54–152)
  - Extracts tables from each page
  - Filters rows where column 1 is a numeric serial number
  - Parses compound fields (project name + agency + code, date pairs, cost pairs)
  - Records source page for traceability
- **Run**: `python src/data/extract.py`

### 2. Cleaning (`src/data/clean.py`)
- **Input**: `data/processed/paimana_raw_extracted.csv`
- **Output**: `data/processed/paimana_cleaned.csv`
- **Process**:
  - Normalizes whitespace (collapses newlines, trims)
  - Converts dates from MM/YYYY → YYYY-MM
  - Removes currency formatting (commas, ₹ symbol)
  - Converts percentages to float
  - Cleans multi-state fields
  - Converts "-" to null (NOT to zero)
- **Run**: `python src/data/clean.py`

### 3. Validation (`src/data/validate.py`)
- **Input**: `data/processed/paimana_cleaned.csv`
- **Output**: `data/processed/validation_report.txt`
- **Process**:
  - Checks row count against expected (1,775)
  - Checks for missing/duplicate Sl.Nos
  - Checks for missing/duplicate project codes
  - Validates date ranges and consistency
  - Checks for negative costs
  - Checks for impossible progress values
  - Does NOT automatically delete problematic records
- **Run**: `python src/data/validate.py`

### 4. Transformation (`src/data/transform.py`)
- **Input**: `data/processed/paimana_cleaned.csv`
- **Output**:
  - `data/processed/paimana_master_v1.csv` (full dataset, 23 columns)
  - `data/sample/paimana_sample.csv` (50-row representative subset)
- **Process**:
  - Derives cost_overrun (binary) and cost_overrun_percent
  - Derives expenditure_percent
  - Derives progress_gap
  - Derives time features (original_duration, revised_duration, time_overrun)
  - Creates stratified sample for team use
- **Run**: `python src/data/transform.py`

## Full Pipeline Command

```bash
# Activate virtual environment
.\.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac

# Run pipeline in order
python src/data/extract.py
python src/data/clean.py
python src/data/validate.py
python src/data/transform.py
```

## Adding Future Reports

The pipeline is designed to support future monthly PAIMANA reports:

1. Place new PDF in `data/raw/`
2. Update `PDF_PATH` and `REPORT_MONTH` in `extract.py`
3. Run the full pipeline
4. The `report_month` and `source_report` columns track which snapshot each row came from
5. Multiple months can be concatenated for time-series analysis

> **Note**: A single monthly snapshot is sufficient for prototyping but NOT for production-quality time-series prediction. See TEAMME.md for details.
