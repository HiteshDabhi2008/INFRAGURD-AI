import pandas as pd
import numpy as np
import os

def create_features(master_file, output_feature_file):
    os.makedirs(os.path.dirname(output_feature_file), exist_ok=True)
    
    df = pd.read_csv(master_file)
    
    # 1. Dates and Durations
    date_cols = ['approval_date', 'start_date', 'original_completion_date', 'revised_completion_date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            
    # Assuming current date is the report month date. Since reports are July 2026, let's use that if available, or just a generic 'now' (simulated to July 2026 for this dataset)
    current_date = pd.to_datetime('2026-07-01')
    
    if 'approval_date' in df.columns:
        df['project_age_days'] = (current_date - df['approval_date']).dt.days
    else:
        df['project_age_days'] = np.nan
        
    if 'start_date' in df.columns and 'original_completion_date' in df.columns:
        df['original_duration_days'] = (df['original_completion_date'] - df['start_date']).dt.days
    else:
        df['original_duration_days'] = np.nan
        
    if 'start_date' in df.columns and 'revised_completion_date' in df.columns:
        df['revised_duration_days'] = (df['revised_completion_date'] - df['start_date']).dt.days
    else:
        df['revised_duration_days'] = np.nan
        
    # 2. Costs
    if 'original_cost' in df.columns and 'revised_cost' in df.columns:
        df['cost_change'] = df['revised_cost'] - df['original_cost']
        df['cost_change_percent'] = np.where(
            df['original_cost'] > 0, 
            (df['cost_change'] / df['original_cost']) * 100, 
            0
        )
    else:
        df['cost_change'] = np.nan
        df['cost_change_percent'] = np.nan
        
    if 'cumulative_expenditure' in df.columns and 'revised_cost' in df.columns:
        df['expenditure_percent'] = np.where(
            df['revised_cost'] > 0,
            (df['cumulative_expenditure'] / df['revised_cost']) * 100,
            0
        )
    else:
        df['expenditure_percent'] = np.nan
        
    # 3. Progress
    if 'physical_progress' in df.columns and 'expenditure_percent' in df.columns:
        df['progress_gap'] = df['expenditure_percent'] - df['physical_progress']
    else:
        df['progress_gap'] = np.nan
        
    # 4. Project Size Category
    if 'original_cost' in df.columns:
        # e.g., < 1000 = Small, 1000-5000 = Medium, > 5000 = Large
        conditions = [
            (df['original_cost'] < 1000),
            (df['original_cost'] >= 1000) & (df['original_cost'] <= 5000),
            (df['original_cost'] > 5000)
        ]
        choices = ['Small', 'Medium', 'Large']
        df['project_size_category'] = np.select(conditions, choices, default='Unknown')
    else:
        df['project_size_category'] = 'Unknown'
        
    # Select only the identifier + derived fields for the feature set, or include all. The prompt says "Create data/processed/project_features.csv. Add reusable derived fields".
    # It's best to include project_code, report_month, and the new features so it can be joined with master.
    feature_cols = ['project_code', 'report_month', 'project_age_days', 'original_duration_days', 
                    'revised_duration_days', 'expenditure_percent', 'progress_gap', 'cost_change', 
                    'cost_change_percent', 'project_size_category']
    
    # Ensure columns exist before selecting
    feature_cols = [c for c in feature_cols if c in df.columns]
    
    df_features = df[feature_cols]
    df_features.to_csv(output_feature_file, index=False)
    
    print(f"Features created and saved to {output_feature_file}")
    
if __name__ == "__main__":
    create_features(
        master_file="data/processed/master_projects.csv",
        output_feature_file="data/processed/project_features.csv"
    )
