"""
cost_features.py - Member 3
============================================================
Engineers temporal features (lags, velocity) for cost prediction 
using the longitudinal PAIMANA dataset.
"""

import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_CSV = os.path.join(BASE_DIR, "data", "processed", "paimana_historical.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "data", "processed", "cost_ml_dataset.csv")

def engineer_features(df):
    """
    Given a longitudinal dataset sorted by project_code and report_date,
    calculate temporal features and extract the latest observation as the target row.
    """
    df = df.copy()
    
    # Ensure sorted order
    df = df.sort_values(by=['project_code', 'report_date'])
    
    # Calculate lags using groupby shift
    # Group by project_code
    grouped = df.groupby('project_code')
    
    # Lag 1 month
    df['prev_progress'] = grouped['physical_progress'].shift(1)
    df['prev_expenditure'] = grouped['cumulative_expenditure'].shift(1)
    
    # Calculate changes
    df['progress_change_1m'] = df['physical_progress'] - df['prev_progress']
    df['expenditure_change_1m'] = df['cumulative_expenditure'] - df['prev_expenditure']
    
    # Number of observations
    df['num_observations'] = grouped['report_month'].transform('count')
    
    # We want to predict for the latest month available for each project
    latest_df = df.drop_duplicates(subset=['project_code'], keep='last').copy()
    
    # We should only keep projects that have original_cost and physical_progress
    latest_df = latest_df.dropna(subset=['original_cost', 'physical_progress'])
    
    # Add expenditure per progress point
    latest_df['expenditure_per_progress'] = np.where(
        latest_df['physical_progress'] > 0,
        latest_df['cumulative_expenditure'] / latest_df['physical_progress'],
        0
    )
    
    # Project size category
    bins = [0, 1000, 5000, np.inf]
    labels = ['Small', 'Medium', 'Large']
    latest_df['project_size_category'] = pd.cut(latest_df['original_cost'], bins=bins, labels=labels, right=False)
    latest_df['project_size_category'] = latest_df['project_size_category'].astype(str)
    
    # Target definition
    # ------------------
    # The objective is to predict Total Cost at 100% completion.
    # Since we don't have many projects at 100%, we use the 'revised_cost' as the proxy for ground truth total cost,
    # as it's the current official estimate of final cost.
    # Alternatively, if physical_progress is 100%, revised_cost IS the final cost.
    
    latest_df['target_total_cost'] = latest_df['revised_cost'].fillna(latest_df['original_cost'])
    
    # LEAKAGE PREVENTION:
    # We must NOT use revised_cost, cost_overrun, or any target-derived fields as features.
    
    # Impute missing temporal features (for projects with only 1 month of data)
    latest_df['progress_change_1m'] = latest_df['progress_change_1m'].fillna(0)
    latest_df['expenditure_change_1m'] = latest_df['expenditure_change_1m'].fillna(0)
    
    # Select final columns for modeling
    feature_cols = [
        'project_code', 'project_name', 'agency', 'state', 'report_month',
        'original_cost', 'physical_progress', 'cumulative_expenditure',
        'progress_change_1m', 'expenditure_change_1m', 'num_observations',
        'expenditure_per_progress', 'project_size_category', 
        'target_total_cost' # This is our target!
    ]
    
    final_df = latest_df[feature_cols].copy()
    
    return final_df

def main():
    if not os.path.exists(INPUT_CSV):
        print(f"Error: {INPUT_CSV} not found. Run build_longitudinal_data.py first.")
        return
        
    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} longitudinal records.")
    
    final_df = engineer_features(df)
    
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    final_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    
    print(f"Engineered features for {len(final_df)} unique projects.")
    print(f"Saved to {OUTPUT_CSV}")
    print("\nFeature Summary:")
    print(final_df.describe())

if __name__ == "__main__":
    main()
