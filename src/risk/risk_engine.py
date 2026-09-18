"""
risk_engine.py - Member 5
============================================================
The main risk engine combining Member 3 (Cost) and Member 4 (Time) predictions
along with current project indicators to calculate composite risk and rankings.
"""

import os
import pandas as pd
import numpy as np

# Configurable Risk Thresholds (Prototype, not official MoSPI thresholds)
COST_OVERRUN_HIGH_THRESHOLD = 20.0  # %
TIME_OVERRUN_HIGH_THRESHOLD = 20.0  # %
LOW_PROGRESS_THRESHOLD = 30.0       # %

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "member5")

HISTORICAL_CSV = os.path.join(PROCESSED_DIR, "paimana_historical.csv")
M3_PREDICTIONS = os.path.join(BASE_DIR, "outputs", "member3", "cost_predictions.csv")
M4_PREDICTIONS = os.path.join(BASE_DIR, "outputs", "member4", "time_predictions.csv")

OUT_RANKINGS = os.path.join(OUTPUT_DIR, "risk_rankings.csv")

def calculate_risk_score(row):
    score = 0
    warnings = []
    
    # 1. Cost Risk (0 - 40 points)
    cost_overrun = row.get('cost_overrun_percent', 0)
    if pd.isna(cost_overrun): cost_overrun = 0
    
    if cost_overrun > 50:
        score += 40
        warnings.append("Critical Cost Overrun Predicted")
    elif cost_overrun > COST_OVERRUN_HIGH_THRESHOLD:
        score += 30
        warnings.append("High Cost Overrun Predicted")
    elif cost_overrun > 5:
        score += 15
        
    # 2. Time Risk (0 - 40 points)
    time_overrun = row.get('time_overrun_percent', 0)
    if pd.isna(time_overrun): time_overrun = 0
    
    if time_overrun > 50:
        score += 40
        warnings.append("Critical Time Overrun Predicted")
    elif time_overrun > TIME_OVERRUN_HIGH_THRESHOLD:
        score += 30
        warnings.append("High Time Overrun Predicted")
    elif time_overrun > 5:
        score += 15
        
    # 3. Expenditure / Progress Mismatch (0 - 20 points)
    # E.g. spent 80% of money but only 20% progress
    exp_pct = row.get('expenditure_percent', 0)
    prog = row.get('physical_progress', 0)
    
    if pd.notna(exp_pct) and pd.notna(prog):
        gap = exp_pct - prog
        if gap > 40:
            score += 20
            warnings.append("Severe Expenditure/Progress Mismatch")
        elif gap > 20:
            score += 10
            warnings.append("High Expenditure relative to Progress")
            
    # Cap score at 100
    score = min(score, 100)
    return score, "; ".join(warnings)

def categorize_risk(score):
    if score >= 75: return "CRITICAL"
    if score >= 50: return "HIGH"
    if score >= 25: return "MEDIUM"
    return "LOW"

def run_risk_engine():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Read latest snapshot for each project from historical data
    print("Loading master project data...")
    df_hist = pd.read_csv(HISTORICAL_CSV)
    df_hist['report_date'] = pd.to_datetime(df_hist['report_date'])
    # Get the latest report for each project
    df_latest = df_hist.sort_values('report_date').groupby('project_code').last().reset_index()
    
    # Calculate current expenditure percent
    df_latest['original_cost'] = pd.to_numeric(df_latest['original_cost'], errors='coerce')
    df_latest['cumulative_expenditure'] = pd.to_numeric(df_latest['cumulative_expenditure'], errors='coerce')
    df_latest['physical_progress'] = pd.to_numeric(df_latest['physical_progress'], errors='coerce')
    
    df_latest['expenditure_percent'] = (df_latest['cumulative_expenditure'] / df_latest['original_cost']) * 100
    df_latest['expenditure_percent'] = df_latest['expenditure_percent'].replace([np.inf, -np.inf], np.nan)
    
    # Load M3 Predictions
    if os.path.exists(M3_PREDICTIONS):
        m3_df = pd.read_csv(M3_PREDICTIONS)
        # m3_df has 'report_month' (e.g. 'April 2026')
        m3_df['report_date'] = pd.to_datetime(m3_df['report_month'])
        m3_latest = m3_df.sort_values('report_date').groupby('project_code').last().reset_index()
        # Merge cost overrun percent
        df_latest = df_latest.merge(m3_latest[['project_code', 'predicted_total_cost', 'cost_overrun_percent']], on='project_code', how='left')
    else:
        print("Warning: M3 predictions not found.")
        df_latest['cost_overrun_percent'] = 0.0
        
    # Load M4 Predictions
    if os.path.exists(M4_PREDICTIONS):
        m4_df = pd.read_csv(M4_PREDICTIONS)
        m4_df['report_date'] = pd.to_datetime(m4_df['report_date'])
        m4_latest = m4_df.sort_values('report_date').groupby('project_code').last().reset_index()
        # Merge time overrun percent
        df_latest = df_latest.merge(m4_latest[['project_code', 'predicted_duration_months', 'time_overrun_percent']], on='project_code', how='left')
    else:
        print("Warning: M4 predictions not found.")
        df_latest['time_overrun_percent'] = 0.0

    print("Calculating risk scores...")
    # Calculate Risk Score and Categories
    results = df_latest.apply(calculate_risk_score, axis=1)
    df_latest['risk_score'] = [r[0] for r in results]
    df_latest['warnings'] = [r[1] for r in results]
    df_latest['risk_category'] = df_latest['risk_score'].apply(categorize_risk)
    
    # Warnings and Explanations
    import risk_rules
    import risk_explanation
    df_latest['warnings'] = df_latest.apply(risk_rules.generate_warnings, axis=1)
    df_latest['risk_explanation'] = df_latest.apply(lambda row: risk_explanation.generate_explanation(row, row['warnings']), axis=1)
    
    # Priority Ranking
    # Sort by risk_score descending
    df_latest = df_latest.sort_values(by='risk_score', ascending=False).reset_index(drop=True)
    df_latest['priority_rank'] = df_latest.index + 1
    
    # Save Risk Rankings
    output_cols = [
        'priority_rank', 'project_code', 'project_name', 'agency', 'state', 
        'physical_progress', 'expenditure_percent', 'cost_overrun_percent', 
        'time_overrun_percent', 'risk_score', 'risk_category', 'warnings',
        'risk_explanation'
    ]
    final_out = df_latest[output_cols]
    
    final_out.to_csv(OUT_RANKINGS, index=False)
    print(f"Risk engine execution complete. Saved {len(final_out)} rankings to {OUT_RANKINGS}")

    # Create high risk subset
    high_risk = final_out[final_out['risk_category'].isin(['CRITICAL', 'HIGH'])]
    high_risk.to_csv(os.path.join(OUTPUT_DIR, "high_risk_projects.csv"), index=False)
    
    # ---------------------------------------------------------
    # Visualizations
    # ---------------------------------------------------------
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    # 1. Risk Distribution
    plt.figure(figsize=(8, 5))
    sns.countplot(data=final_out, x='risk_category', order=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'], palette=['green', 'yellow', 'orange', 'red'])
    plt.title("Risk Category Distribution")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "risk_distribution.png"))
    plt.close()
    
    # 2. Cost vs Time Risk (Bubble chart)
    plt.figure(figsize=(10, 8))
    sns.scatterplot(
        data=final_out, 
        x='cost_overrun_percent', 
        y='time_overrun_percent', 
        hue='risk_category',
        hue_order=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
        palette=['green', 'yellow', 'orange', 'red'],
        size='risk_score', 
        sizes=(20, 200),
        alpha=0.6
    )
    plt.title("Cost Overrun vs Time Overrun Risk")
    plt.xlabel("Predicted Cost Overrun %")
    plt.ylabel("Predicted Time Overrun %")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "cost_vs_time_risk.png"))
    plt.close()

if __name__ == "__main__":
    run_risk_engine()
