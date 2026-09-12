"""
transform.py — Member 1: Feature Derivation for PAIMANA Data
===============================================================
Derives features from cleaned data for downstream ML and analytics.
Produces the master dataset (paimana_master_v1.csv) and sample dataset.

IMPORTANT DATA LEAKAGE NOTE:
  - revised_cost and revised_completion_date are OUTCOME indicators.
  - They may be used to DEFINE targets (cost_overrun, time_overrun).
  - They must NOT be used as predictive INPUTS in ML models that
    predict cost or time overrun.
  - See docs/data_leakage.md for full documentation.

Usage:
    python -m src.data.transform
    or
    python src/data/transform.py
"""

import pandas as pd
import numpy as np
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_CSV = os.path.join(BASE_DIR, "data", "processed", "paimana_cleaned.csv")
MASTER_CSV = os.path.join(BASE_DIR, "data", "processed", "paimana_master_v1.csv")
SAMPLE_CSV = os.path.join(BASE_DIR, "data", "sample", "paimana_sample.csv")

SAMPLE_SIZE = 50  # Representative subset for other members


# ──────────────────────────────────────────────
# DERIVED FEATURE FUNCTIONS
# ──────────────────────────────────────────────

def derive_cost_overrun(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive cost overrun fields.
    cost_overrun = 1 if revised_cost > original_cost, else 0
    cost_overrun_percent = ((revised_cost - original_cost) / original_cost) * 100
    """
    df = df.copy()

    # Cost overrun binary flag
    mask = df['original_cost'].notna() & df['revised_cost'].notna()
    df.loc[mask, 'cost_overrun'] = (df.loc[mask, 'revised_cost'] > df.loc[mask, 'original_cost']).astype(int)

    # Cost overrun percentage
    mask_nonzero = mask & (df['original_cost'] > 0)
    df.loc[mask_nonzero, 'cost_overrun_percent'] = (
        (df.loc[mask_nonzero, 'revised_cost'] - df.loc[mask_nonzero, 'original_cost'])
        / df.loc[mask_nonzero, 'original_cost'] * 100
    ).round(2)

    return df


def derive_expenditure_percent(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive expenditure as percentage of revised cost.
    expenditure_percent = (cumulative_expenditure / revised_cost) * 100
    """
    df = df.copy()

    mask = df['cumulative_expenditure'].notna() & df['revised_cost'].notna() & (df['revised_cost'] > 0)
    df.loc[mask, 'expenditure_percent'] = (
        df.loc[mask, 'cumulative_expenditure'] / df.loc[mask, 'revised_cost'] * 100
    ).round(2)

    return df


def derive_progress_gap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive progress gap = expenditure_percent - physical_progress.
    A large positive gap may indicate overspending relative to progress.
    A large negative gap may indicate underspending.
    """
    df = df.copy()

    mask = df['expenditure_percent'].notna() & df['physical_progress'].notna()
    df.loc[mask, 'progress_gap'] = (
        df.loc[mask, 'expenditure_percent'] - df.loc[mask, 'physical_progress']
    ).round(2)

    return df


def derive_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive time-related features from date fields.
    Parses YYYY-MM format dates.
    """
    df = df.copy()

    def parse_ym(date_str):
        """Parse YYYY-MM to (year, month) tuple."""
        if pd.isna(date_str) or date_str is None:
            return (None, None)
        try:
            parts = str(date_str).split('-')
            return (int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            return (None, None)

    def months_between(start_ym, end_ym):
        """Calculate months between two (year, month) tuples."""
        if start_ym[0] is None or end_ym[0] is None:
            return None
        return (end_ym[0] - start_ym[0]) * 12 + (end_ym[1] - start_ym[1])

    # Original duration
    for idx, row in df.iterrows():
        approval_ym = parse_ym(row.get('approval_date'))
        orig_doc_ym = parse_ym(row.get('original_completion_date'))
        revised_doc_ym = parse_ym(row.get('revised_completion_date'))

        orig_duration = months_between(approval_ym, orig_doc_ym)
        if orig_duration is not None:
            df.at[idx, 'original_duration_months'] = orig_duration

        if revised_doc_ym[0] is not None:
            revised_duration = months_between(approval_ym, revised_doc_ym)
            if revised_duration is not None:
                df.at[idx, 'revised_duration_months'] = revised_duration

            time_overrun = months_between(orig_doc_ym, revised_doc_ym)
            if time_overrun is not None:
                df.at[idx, 'time_overrun_months'] = time_overrun

    return df


def create_sample(df: pd.DataFrame, n: int = SAMPLE_SIZE) -> pd.DataFrame:
    """
    Create a representative sample for other team members.
    Stratifies by state to ensure diversity.
    """
    if len(df) <= n:
        return df.copy()

    # Try stratified sampling by state
    try:
        sample = df.groupby('state', group_keys=False).apply(
            lambda x: x.sample(max(1, int(len(x) / len(df) * n)), random_state=42)
        )
        if len(sample) < n:
            remaining = df[~df.index.isin(sample.index)].sample(n - len(sample), random_state=42)
            sample = pd.concat([sample, remaining])
        return sample.head(n).sort_values('sl_no').reset_index(drop=True)
    except Exception:
        return df.sample(n, random_state=42).sort_values('sl_no').reset_index(drop=True)


# ──────────────────────────────────────────────
# MAIN TRANSFORM PIPELINE
# ──────────────────────────────────────────────

def transform_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all feature derivations."""
    print(f"Transforming {len(df)} rows...")

    df = derive_cost_overrun(df)
    print("  [+] Cost overrun features derived")

    df = derive_expenditure_percent(df)
    print("  [+] Expenditure percent derived")

    df = derive_progress_gap(df)
    print("  [+] Progress gap derived")

    df = derive_time_features(df)
    print("  [+] Time features derived")

    print(f"Transform complete. Final columns: {list(df.columns)}")
    return df


def main():
    """Run transform pipeline and produce master + sample datasets."""
    if not os.path.exists(INPUT_CSV):
        print(f"ERROR: Input CSV not found at {INPUT_CSV}")
        print("Run clean.py first.")
        sys.exit(1)

    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} rows from {INPUT_CSV}")

    df_master = transform_dataframe(df)

    # Save master
    os.makedirs(os.path.dirname(MASTER_CSV), exist_ok=True)
    df_master.to_csv(MASTER_CSV, index=False, encoding="utf-8-sig")
    print(f"\nSaved master dataset to: {MASTER_CSV}")
    print(f"Shape: {df_master.shape}")

    # Save sample
    df_sample = create_sample(df_master)
    os.makedirs(os.path.dirname(SAMPLE_CSV), exist_ok=True)
    df_sample.to_csv(SAMPLE_CSV, index=False, encoding="utf-8-sig")
    print(f"Saved sample dataset to: {SAMPLE_CSV}")
    print(f"Sample shape: {df_sample.shape}")

    # Quick stats
    print(f"\n{'='*60}")
    print("DERIVED FEATURE SUMMARY")
    print(f"{'='*60}")
    for col in ['cost_overrun', 'cost_overrun_percent', 'expenditure_percent',
                 'progress_gap', 'original_duration_months', 'revised_duration_months',
                 'time_overrun_months']:
        if col in df_master.columns:
            non_null = df_master[col].notna().sum()
            print(f"  {col}: {non_null} non-null ({non_null/len(df_master)*100:.1f}%)")
            if df_master[col].dtype in ['float64', 'int64', 'Int64']:
                print(f"    mean={df_master[col].mean():.2f}, min={df_master[col].min():.2f}, max={df_master[col].max():.2f}")

    if 'cost_overrun' in df_master.columns:
        co_counts = df_master['cost_overrun'].value_counts(dropna=False)
        print(f"\n  Cost overrun distribution:")
        print(f"    {co_counts.to_dict()}")

    return df_master


if __name__ == "__main__":
    main()
