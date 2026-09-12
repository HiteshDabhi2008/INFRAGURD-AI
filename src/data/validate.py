"""
validate.py — Member 1: Data Validation for PAIMANA Data
=========================================================
Checks for data quality issues WITHOUT automatically deleting records.
Reports problems for manual review.

Usage:
    python -m src.data.validate
    or
    python src/data/validate.py
"""

import pandas as pd
import numpy as np
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_CSV = os.path.join(BASE_DIR, "data", "processed", "paimana_cleaned.csv")
REPORT_PATH = os.path.join(BASE_DIR, "data", "processed", "validation_report.txt")

EXPECTED_PROJECT_COUNT = 1775


def validate_project_ids(df: pd.DataFrame) -> list:
    """Check for missing, duplicate, and out-of-range project IDs."""
    issues = []

    # Missing sl_no
    missing_ids = df[df['sl_no'].isna()]
    if len(missing_ids) > 0:
        issues.append(f"MISSING Sl.No: {len(missing_ids)} rows have no Sl.No")

    # Duplicate sl_no
    dupes = df[df['sl_no'].duplicated(keep=False)]
    if len(dupes) > 0:
        dupe_vals = sorted(dupes['sl_no'].dropna().unique().tolist())
        issues.append(f"DUPLICATE Sl.No: {len(dupe_vals)} values duplicated: {dupe_vals[:20]}{'...' if len(dupe_vals) > 20 else ''}")

    # Missing serial numbers in sequence
    if df['sl_no'].notna().any():
        expected = set(range(1, EXPECTED_PROJECT_COUNT + 1))
        found = set(df['sl_no'].dropna().astype(int).tolist())
        missing = sorted(expected - found)
        if missing:
            issues.append(f"MISSING from sequence: {len(missing)} Sl.Nos not found: {missing[:30]}{'...' if len(missing) > 30 else ''}")

    # Duplicate project codes
    if 'project_code' in df.columns:
        code_dupes = df[df['project_code'].notna() & df['project_code'].duplicated(keep=False)]
        if len(code_dupes) > 0:
            dupe_codes = sorted(code_dupes['project_code'].unique().tolist())
            issues.append(f"DUPLICATE Project Codes: {len(dupe_codes)} codes duplicated: {dupe_codes[:20]}{'...' if len(dupe_codes) > 20 else ''}")

    return issues


def validate_dates(df: pd.DataFrame) -> list:
    """Check for invalid or missing dates."""
    issues = []

    for col in ['approval_date', 'original_completion_date']:
        if col in df.columns:
            missing = df[col].isna().sum()
            if missing > 0:
                issues.append(f"MISSING {col}: {missing} rows ({missing/len(df)*100:.1f}%)")

    # Check for reversed dates (approval after completion)
    if 'approval_date' in df.columns and 'original_completion_date' in df.columns:
        valid_both = df[df['approval_date'].notna() & df['original_completion_date'].notna()]
        reversed_dates = valid_both[valid_both['approval_date'] > valid_both['original_completion_date']]
        if len(reversed_dates) > 0:
            issues.append(f"REVERSED DATES: {len(reversed_dates)} rows where approval_date > original_completion_date")

    return issues


def validate_costs(df: pd.DataFrame) -> list:
    """Check for invalid cost values."""
    issues = []

    for col in ['original_cost', 'revised_cost', 'cumulative_expenditure']:
        if col in df.columns:
            missing = df[col].isna().sum()
            if missing > 0:
                issues.append(f"MISSING {col}: {missing} rows ({missing/len(df)*100:.1f}%)")

            negative = df[df[col].notna() & (df[col] < 0)]
            if len(negative) > 0:
                issues.append(f"NEGATIVE {col}: {len(negative)} rows have negative values")

    return issues


def validate_progress(df: pd.DataFrame) -> list:
    """Check for impossible physical progress values."""
    issues = []

    if 'physical_progress' in df.columns:
        missing = df['physical_progress'].isna().sum()
        if missing > 0:
            issues.append(f"MISSING physical_progress: {missing} rows ({missing/len(df)*100:.1f}%)")

        invalid = df[df['physical_progress'].notna() & (df['physical_progress'] < 0)]
        if len(invalid) > 0:
            issues.append(f"NEGATIVE physical_progress: {len(invalid)} rows")

        over_100 = df[df['physical_progress'].notna() & (df['physical_progress'] > 100)]
        if len(over_100) > 0:
            issues.append(f"OVER 100% physical_progress: {len(over_100)} rows (Sl.Nos: {sorted(over_100['sl_no'].tolist())[:10]})")

    return issues


def validate_row_count(df: pd.DataFrame) -> list:
    """Check row count against expected."""
    issues = []

    if len(df) != EXPECTED_PROJECT_COUNT:
        issues.append(f"ROW COUNT MISMATCH: Got {len(df)}, expected {EXPECTED_PROJECT_COUNT} (diff: {len(df) - EXPECTED_PROJECT_COUNT})")
    else:
        issues.append(f"ROW COUNT OK: {len(df)} matches expected {EXPECTED_PROJECT_COUNT}")

    return issues


def validate_names(df: pd.DataFrame) -> list:
    """Check for suspicious duplicate project names."""
    issues = []

    if 'project_name' in df.columns:
        missing_names = df['project_name'].isna().sum()
        if missing_names > 0:
            issues.append(f"MISSING project_name: {missing_names} rows")

        name_dupes = df[df['project_name'].notna() & df['project_name'].duplicated(keep=False)]
        if len(name_dupes) > 0:
            dupe_names = name_dupes['project_name'].unique()[:10]
            issues.append(f"DUPLICATE project_name: {len(name_dupes)} rows share {len(df[df['project_name'].notna()].groupby('project_name').filter(lambda x: len(x) > 1)['project_name'].unique())} names")

    return issues


def run_validation(df: pd.DataFrame) -> dict:
    """Run all validation checks and return results."""
    print(f"\n{'='*60}")
    print("VALIDATION REPORT")
    print(f"{'='*60}")

    results = {
        "row_count": validate_row_count(df),
        "project_ids": validate_project_ids(df),
        "dates": validate_dates(df),
        "costs": validate_costs(df),
        "progress": validate_progress(df),
        "names": validate_names(df),
    }

    all_issues = []
    for category, issues in results.items():
        print(f"\n--- {category.upper()} ---")
        for issue in issues:
            print(f"  {issue}")
            all_issues.append(issue)

    # Summary
    print(f"\n{'='*60}")
    print(f"TOTAL ISSUES: {len(all_issues)}")
    print(f"\nNull value summary:")
    print(df.isnull().sum().to_string())

    return results


def main():
    """Run validation on cleaned data."""
    if not os.path.exists(INPUT_CSV):
        print(f"ERROR: Input CSV not found at {INPUT_CSV}")
        print("Run clean.py first.")
        sys.exit(1)

    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} rows from {INPUT_CSV}")

    results = run_validation(df)

    # Save report
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write("PAIMANA Data Validation Report\n")
        f.write(f"Input: {INPUT_CSV}\n")
        f.write(f"Rows: {len(df)}\n")
        f.write(f"{'='*60}\n\n")
        for category, issues in results.items():
            f.write(f"\n--- {category.upper()} ---\n")
            for issue in issues:
                f.write(f"  {issue}\n")
        f.write(f"\n{'='*60}\n")
        f.write(f"\nNull counts:\n")
        f.write(df.isnull().sum().to_string())

    print(f"\nValidation report saved to: {REPORT_PATH}")

    return results


if __name__ == "__main__":
    main()
