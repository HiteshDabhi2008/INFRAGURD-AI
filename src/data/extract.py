"""
extract.py — Member 1: PAIMANA Flash Report PDF Extraction
============================================================
Extracts Table 6 (All Ongoing Projects) from the PAIMANA Flash Report PDF.

Table 6 spans pages 54-152 in the July 2026 report.
Each page contains a table with 8 columns:
  1. Sl.No
  2. Project Name (Agency) (Project Code) (Legacy OCMS Code) (PMGID)
  3. State
  4. Date of Approval (Start Date) MM/YYYY
  5. Original/Target DoC (Revised DoC) MM/YYYY
  6. Original Cost / Revised Cost in Rs. Crore
  7. Cumulative Expenditure in Rs. Crore
  8. Physical Progress (%)

Usage:
    python -m src.data.extract
    or
    python src/data/extract.py
"""

import pdfplumber
import pandas as pd
import re
import os
import sys


# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PDF_PATH = os.path.join(BASE_DIR, "data", "raw", "FlashReport_July_2026.pdf")
OUTPUT_RAW_CSV = os.path.join(BASE_DIR, "data", "processed", "paimana_raw_extracted.csv")

# Table 6 starts on page 54 (0-indexed: 53) and ends on page 152 (0-indexed: 151)
TABLE6_START_PAGE = 53  # 0-indexed
TABLE6_END_PAGE = 152   # 0-indexed, inclusive

REPORT_MONTH = "July 2026"
SOURCE_REPORT = "FlashReport_July_2026.pdf"
EXPECTED_PROJECT_COUNT = 1775


# ──────────────────────────────────────────────
# FIELD PARSERS
# ──────────────────────────────────────────────

def parse_project_name_field(raw: str) -> dict:
    """
    Parse the compound project name field.
    Format:
        Project Name
        (Agency)
        (Project Code)
        (Legacy OCMS Code) (PMGID)

    Returns dict with: project_name, agency, project_code, legacy_ocms_code, pmgid
    """
    result = {
        "project_name": None,
        "agency": None,
        "project_code": None,
        "legacy_ocms_code": None,
        "pmgid": None,
    }
    if not raw or not raw.strip():
        return result

    lines = raw.strip().split("\n")

    # Project name is everything before the first parenthesized group
    # Agency is the first parenthesized group
    # Then project code, legacy code, pmgid follow

    full_text = raw.strip()

    # Extract all parenthesized groups
    paren_groups = re.findall(r'\(([^)]*)\)', full_text)

    # Project name is text before the first '('
    first_paren = full_text.find('(')
    if first_paren > 0:
        result["project_name"] = full_text[:first_paren].strip()
    else:
        result["project_name"] = full_text.strip()

    # Agency is typically the first parenthesized group (contains text, not just numbers)
    if paren_groups:
        # Agency is the first group that contains alphabetic characters
        for i, grp in enumerate(paren_groups):
            if re.search(r'[a-zA-Z]', grp):
                result["agency"] = grp.strip()
                remaining_groups = paren_groups[i + 1:]
                break
        else:
            remaining_groups = paren_groups

        # Project code is the first numeric-only group after agency
        for grp in remaining_groups:
            grp_clean = grp.strip()
            if grp_clean.isdigit() and result["project_code"] is None:
                result["project_code"] = grp_clean
            elif grp_clean == "-" or grp_clean == "":
                # Legacy OCMS or PMGID might be "-"
                if result["legacy_ocms_code"] is None:
                    result["legacy_ocms_code"] = None  # "-" means not available
                elif result["pmgid"] is None:
                    result["pmgid"] = None

    return result


def parse_date_pair(raw: str) -> tuple:
    """
    Parse a field containing two dates separated by newline.
    Format: MM/YYYY\n(MM/YYYY)  or  MM/YYYY\n(-)
    Returns (primary_date, secondary_date)
    """
    if not raw or not raw.strip():
        return (None, None)

    raw = raw.strip()
    parts = re.split(r'\n', raw)

    primary = parts[0].strip() if len(parts) > 0 else None
    secondary = None
    if len(parts) > 1:
        sec = parts[1].strip()
        # Remove surrounding parentheses
        sec = re.sub(r'^\(|\)$', '', sec).strip()
        if sec == "-" or sec == "":
            secondary = None
        else:
            secondary = sec

    return (primary, secondary)


def parse_cost_pair(raw: str) -> tuple:
    """
    Parse a field containing two cost values separated by newline.
    Format: 1,234.56\n(1,234.56)
    Returns (original_cost, revised_cost) as strings (cleaned later)
    """
    if not raw or not raw.strip():
        return (None, None)

    raw = raw.strip()
    parts = re.split(r'\n', raw)

    primary = parts[0].strip() if len(parts) > 0 else None
    secondary = None
    if len(parts) > 1:
        sec = parts[1].strip()
        sec = re.sub(r'^\(|\)$', '', sec).strip()
        if sec == "-" or sec == "":
            secondary = None
        else:
            secondary = sec

    return (primary, secondary)


# ──────────────────────────────────────────────
# MAIN EXTRACTION
# ──────────────────────────────────────────────

def extract_table6(pdf_path: str) -> pd.DataFrame:
    """
    Extract all project rows from Table 6 of the PAIMANA Flash Report.

    Returns a DataFrame with raw extracted fields.
    """
    all_rows = []
    skipped_rows = []

    print(f"Opening PDF: {pdf_path}")
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")
        print(f"Extracting Table 6 from pages {TABLE6_START_PAGE + 1} to {TABLE6_END_PAGE + 1}...")

        for page_idx in range(TABLE6_START_PAGE, min(TABLE6_END_PAGE + 1, total_pages)):
            page = pdf.pages[page_idx]
            page_num = page_idx + 1
            tables = page.extract_tables()

            for table in tables:
                if not table:
                    continue

                for row in table:
                    if not row or not row[0]:
                        continue

                    sl_no = str(row[0]).strip()

                    # Skip header rows and non-data rows
                    if not sl_no.isdigit():
                        continue

                    # Ensure row has 8 columns
                    if len(row) < 8:
                        skipped_rows.append({
                            "sl_no": sl_no,
                            "page": page_num,
                            "reason": f"Only {len(row)} columns (expected 8)",
                            "raw": str(row),
                        })
                        continue

                    # Parse compound fields
                    project_info = parse_project_name_field(row[1])
                    approval_date, start_date = parse_date_pair(row[3])
                    original_doc, revised_doc = parse_date_pair(row[4])
                    original_cost, revised_cost = parse_cost_pair(row[5])

                    all_rows.append({
                        "sl_no": int(sl_no),
                        "project_name": project_info["project_name"],
                        "agency": project_info["agency"],
                        "project_code": project_info["project_code"],
                        "state": str(row[2]).strip() if row[2] else None,
                        "approval_date": approval_date,
                        "start_date": start_date,
                        "original_completion_date": original_doc,
                        "revised_completion_date": revised_doc,
                        "original_cost": original_cost,
                        "revised_cost": revised_cost,
                        "cumulative_expenditure": str(row[6]).strip() if row[6] else None,
                        "physical_progress": str(row[7]).strip() if row[7] else None,
                        "source_page": page_num,
                        "report_month": REPORT_MONTH,
                        "source_report": SOURCE_REPORT,
                    })

    df = pd.DataFrame(all_rows)

    # Report extraction stats
    print(f"\n{'='*60}")
    print(f"EXTRACTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total rows extracted:      {len(df)}")
    print(f"Expected project count:    {EXPECTED_PROJECT_COUNT}")
    print(f"Max Sl.No found:           {df['sl_no'].max() if len(df) > 0 else 'N/A'}")
    print(f"Min Sl.No found:           {df['sl_no'].min() if len(df) > 0 else 'N/A'}")
    print(f"Unique Sl.No count:        {df['sl_no'].nunique() if len(df) > 0 else 'N/A'}")
    print(f"Skipped rows:              {len(skipped_rows)}")

    if skipped_rows:
        print(f"\nSkipped row details:")
        for s in skipped_rows:
            print(f"  Sl.No {s['sl_no']} (page {s['page']}): {s['reason']}")

    # Check for missing Sl.Nos
    if len(df) > 0:
        expected_sl_nos = set(range(1, EXPECTED_PROJECT_COUNT + 1))
        found_sl_nos = set(df['sl_no'].tolist())
        missing_sl_nos = sorted(expected_sl_nos - found_sl_nos)
        duplicate_sl_nos = df[df['sl_no'].duplicated(keep=False)]['sl_no'].unique().tolist()

        print(f"\nMissing Sl.Nos ({len(missing_sl_nos)}): {missing_sl_nos[:30]}{'...' if len(missing_sl_nos) > 30 else ''}")
        print(f"Duplicate Sl.Nos ({len(duplicate_sl_nos)}): {duplicate_sl_nos[:30]}{'...' if len(duplicate_sl_nos) > 30 else ''}")

    return df


def main():
    """Run extraction and save to CSV."""
    if not os.path.exists(PDF_PATH):
        print(f"ERROR: PDF not found at {PDF_PATH}")
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_RAW_CSV), exist_ok=True)

    df = extract_table6(PDF_PATH)

    # Save raw extraction
    df.to_csv(OUTPUT_RAW_CSV, index=False, encoding="utf-8-sig")
    print(f"\nSaved raw extraction to: {OUTPUT_RAW_CSV}")
    print(f"Shape: {df.shape}")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nFirst 3 rows:")
    print(df.head(3).to_string())

    return df


if __name__ == "__main__":
    main()
