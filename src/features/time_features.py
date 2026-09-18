"""
time_features.py - Member 4
============================================================
Generates temporal features for the time prediction model.
It calculates project age, original duration, and progress velocity.
"""

import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
HISTORICAL_CSV = os.path.join(PROCESSED_DIR, "paimana_historical.csv")
OUT_CSV = os.path.join(PROCESSED_DIR, "time_ml_dataset.csv")

def parse_date(date_series):
    # Try multiple formats, as clean.py might have already parsed to YYYY-MM
    return pd.to_datetime(date_series, format='mixed', errors='coerce')

def generate_time_features():
    if not os.path.exists(HISTORICAL_CSV):
        raise FileNotFoundError(f"Source file not found: {HISTORICAL_CSV}")
        
    df = pd.read_csv(HISTORICAL_CSV)
    
    # Ensure physical_progress is numeric
    df['physical_progress'] = pd.to_numeric(df['physical_progress'], errors='coerce').fillna(0)
    
    # Parse dates
    df['report_date'] = pd.to_datetime(df['report_date'])
    df['start_date_parsed'] = parse_date(df['start_date'])
    df['original_completion_parsed'] = parse_date(df['original_completion_date'])
    df['revised_completion_parsed'] = parse_date(df['revised_completion_date'])
    
    # Calculate target (in months) - Using revised completion if available, else original
    # This acts as our proxy for the expected final completion date
    df['target_completion_date'] = df['revised_completion_parsed'].fillna(df['original_completion_parsed'])
    
    # Filter out rows where we don't have a start date or any target completion date
    df = df.dropna(subset=['start_date_parsed', 'target_completion_date'])
    
    # Calculate durations in months (approximate 30.44 days per month)
    DAYS_PER_MONTH = 30.44
    
    df['project_age_months'] = (df['report_date'] - df['start_date_parsed']).dt.days / DAYS_PER_MONTH
    # Cap negative age to 0 (projects that haven't started yet according to their report date)
    df['project_age_months'] = df['project_age_months'].clip(lower=0)
    
    df['original_duration_months'] = (df['original_completion_parsed'] - df['start_date_parsed']).dt.days / DAYS_PER_MONTH
    df['target_duration_months'] = (df['target_completion_date'] - df['start_date_parsed']).dt.days / DAYS_PER_MONTH
    
    # To avoid negative or zero durations causing issues
    df['original_duration_months'] = df['original_duration_months'].clip(lower=1)
    df['target_duration_months'] = df['target_duration_months'].clip(lower=1)
    
    df['remaining_original_duration_months'] = (df['original_completion_parsed'] - df['report_date']).dt.days / DAYS_PER_MONTH
    
    # Sort by project and date to compute lag features
    df = df.sort_values(by=['project_code', 'report_date'])
    
    # Calculate progress velocity (change in physical progress per month)
    df['prev_progress'] = df.groupby('project_code')['physical_progress'].shift(1)
    df['progress_change_1m'] = df['physical_progress'] - df['prev_progress']
    
    # Fill NAs for first month of a project with 0 or the average progress per month so far
    avg_progress_per_month = df['physical_progress'] / df['project_age_months'].replace(0, 1)
    df['progress_change_1m'] = df['progress_change_1m'].fillna(avg_progress_per_month)
    df['progress_change_1m'] = df['progress_change_1m'].clip(lower=0) # Can't go backwards
    
    # Categorical encodings
    df['agency'] = df['agency'].fillna('Unknown')
    df['state'] = df['state'].fillna('Unknown')
    
    # Select final features
    features = [
        'project_code', 'report_date', 'project_name', 'agency', 'state',
        'physical_progress', 'project_age_months', 'original_duration_months',
        'remaining_original_duration_months', 'progress_change_1m',
        'target_duration_months', 'original_completion_date', 'revised_completion_date'
    ]
    
    final_df = df[features].copy()
    
    # Drop rows with NAs in essential features
    final_df = final_df.dropna(subset=['target_duration_months', 'original_duration_months'])
    
    final_df.to_csv(OUT_CSV, index=False)
    print(f"Engineered time features for {final_df['project_code'].nunique()} unique projects.")
    print(f"Saved to {OUT_CSV}")

if __name__ == "__main__":
    generate_time_features()
