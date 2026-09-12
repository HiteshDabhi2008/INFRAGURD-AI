"""
clean.py — Member 1: Data Cleaning for PAIMANA Extracted Data
==============================================================
Reusable cleaning functions for normalizing text, dates, currency,
numeric values, and percentages.

Usage:
    python -m src.data.clean
    or
    python src/data/clean.py
"""

import pandas as pd
import numpy as np
import re
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_CSV = os.path.join(BASE_DIR, "data", "processed", "paimana_raw_extracted.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "data", "processed", "paimana_cleaned.csv")


# ──────────────────────────────────────────────
# TEXT CLEANING
# ──────────────────────────────────────────────

def clean_whitespace(text):
    """Normalize whitespace: collapse multiple spaces, strip, replace newlines."""
    if pd.isna(text) or text is None:
        return None
    text = str(text)
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def clean_text_column(series: pd.Series) -> pd.Series:
    """Apply whitespace cleaning to a text column."""
    return series.apply(clean_whitespace)


# ──────────────────────────────────────────────
# DATE CLEANING
# ──────────────────────────────────────────────

def clean_date(date_str):
    """
    Normalize date string from MM/YYYY to YYYY-MM format.
    Returns None for missing/invalid dates.
    Handles formats: MM/YYYY, M/YYYY
    """
    if pd.isna(date_str) or date_str is None:
        return None

    date_str = str(date_str).strip()
    if date_str in ['-', '', 'None', 'nan', 'NA', 'N/A']:
        return None

    # Remove any surrounding parentheses
    date_str = re.sub(r'[()]', '', date_str).strip()

    # Try MM/YYYY format
    match = re.match(r'^(\d{1,2})/(\d{4})$', date_str)
    if match:
        month = int(match.group(1))
        year = int(match.group(2))
        if 1 <= month <= 12 and 1900 <= year <= 2100:
            return f"{year}-{month:02d}"

    return date_str  # Return as-is if can't parse (will be flagged in validation)


# ──────────────────────────────────────────────
# CURRENCY / NUMERIC CLEANING
# ──────────────────────────────────────────────

def clean_currency(value):
    """
    Clean currency value: remove commas, ₹ symbol, spaces.
    '5,000.50' -> 5000.50
    '₹ 5,000.50' -> 5000.50
    '-' -> None
    Does NOT convert missing to zero.
    """
    if pd.isna(value) or value is None:
        return None

    value = str(value).strip()
    if value in ['-', '', 'None', 'nan', 'NA', 'N/A']:
        return None

    # Remove ₹ symbol, commas, spaces
    value = value.replace('₹', '').replace(',', '').replace(' ', '')

    # Remove surrounding parentheses (sometimes used for revised cost)
    value = re.sub(r'[()]', '', value).strip()

    try:
        return float(value)
    except ValueError:
        return None  # Will be flagged in validation


def clean_percentage(value):
    """
    Clean percentage value.
    '65%' -> 65.0
    '65' -> 65.0
    '-' -> None
    Does NOT convert missing to zero.
    """
    if pd.isna(value) or value is None:
        return None

    value = str(value).strip()
    if value in ['-', '', 'None', 'nan', 'NA', 'N/A']:
        return None

    # Remove % symbol
    value = value.replace('%', '').strip()

    try:
        return float(value)
    except ValueError:
        return None


# ──────────────────────────────────────────────
# STATE CLEANING
# ──────────────────────────────────────────────

def clean_state(state_str):
    """
    Clean state field. Multi-state projects may have long embedded text.
    Collapse newlines and excessive whitespace but preserve the state info.
    """
    if pd.isna(state_str) or state_str is None:
        return None

    state_str = str(state_str).strip()
    if state_str in ['-', '', 'None', 'nan']:
        return None

    # Collapse newlines
    state_str = state_str.replace('\n', ', ').replace('\r', ', ')
    state_str = re.sub(r',\s*,', ',', state_str)
    state_str = re.sub(r'\s+', ' ', state_str)

    return state_str.strip()


# ──────────────────────────────────────────────
# MAIN CLEANING PIPELINE
# ──────────────────────────────────────────────

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all cleaning steps to the raw extracted DataFrame."""
    df = df.copy()
    print(f"Cleaning {len(df)} rows...")

    # 1. Clean text columns
    for col in ['project_name', 'agency', 'state']:
        if col in df.columns:
            df[col] = clean_text_column(df[col])

    # 2. Clean state specifically
    if 'state' in df.columns:
        df['state'] = df['state'].apply(clean_state)

    # 3. Clean dates
    for col in ['approval_date', 'start_date', 'original_completion_date', 'revised_completion_date']:
        if col in df.columns:
            df[col] = df[col].apply(clean_date)

    # 4. Clean currency/cost fields
    for col in ['original_cost', 'revised_cost', 'cumulative_expenditure']:
        if col in df.columns:
            df[col] = df[col].apply(clean_currency)

    # 5. Clean percentage
    if 'physical_progress' in df.columns:
        df['physical_progress'] = df['physical_progress'].apply(clean_percentage)

    # 6. Ensure sl_no is integer
    if 'sl_no' in df.columns:
        df['sl_no'] = pd.to_numeric(df['sl_no'], errors='coerce').astype('Int64')

    print(f"Cleaning complete.")
    return df


def main():
    """Run cleaning pipeline."""
    if not os.path.exists(INPUT_CSV):
        print(f"ERROR: Input CSV not found at {INPUT_CSV}")
        print("Run extract.py first.")
        sys.exit(1)

    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} rows from {INPUT_CSV}")

    df_clean = clean_dataframe(df)

    # Save
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df_clean.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\nSaved cleaned data to: {OUTPUT_CSV}")
    print(f"Shape: {df_clean.shape}")

    # Summary
    print(f"\nData types after cleaning:")
    print(df_clean.dtypes)
    print(f"\nNull counts:")
    print(df_clean.isnull().sum())

    return df_clean


if __name__ == "__main__":
    main()
