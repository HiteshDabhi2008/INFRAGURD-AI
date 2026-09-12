import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def main():
    # Setup directories
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('docs', exist_ok=True)

    # Load data
    try:
        df = pd.read_csv('data/processed/paimana_master_v1.csv')
    except FileNotFoundError:
        print("Master dataset not found. Please ensure Member 1 data pipeline has run.")
        return

    # Data Processing for Risk
    date_cols = ['approval_date', 'original_completion_date', 'revised_completion_date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Basic Risk Indicators (calculated similarly to member 3 & 4)
    # Time
    if 'approval_date' in df.columns and 'original_completion_date' in df.columns:
        df['original_duration_months'] = (df['original_completion_date'] - df['approval_date']).dt.days / 30.44
    if 'revised_completion_date' in df.columns and 'original_completion_date' in df.columns:
        revised_filled = df['revised_completion_date'].fillna(df['original_completion_date'])
        df['time_overrun_months'] = (revised_filled - df['original_completion_date']).dt.days / 30.44
        df['time_overrun_percent'] = np.where(df['original_duration_months'] > 0, 
                                              (df['time_overrun_months'] / df['original_duration_months']) * 100, 0)

    # Cost
    if 'original_cost' in df.columns and 'revised_cost' in df.columns:
        df['cost_overrun_percent'] = np.where(df['original_cost'] > 0,
                                              ((df['revised_cost'] - df['original_cost']) / df['original_cost']) * 100, 0)
    
    # Progress & Expenditure
    # To avoid leakage, expenditure % is evaluated against original cost
    if 'cumulative_expenditure' in df.columns and 'original_cost' in df.columns:
        df['safe_expenditure_percent'] = np.where(df['original_cost'] > 0,
                                                  (df['cumulative_expenditure'] / df['original_cost']) * 100, 0)
    
    if 'physical_progress' in df.columns:
        # Progress Gap = Expenditure % - Physical Progress %
        # A positive gap means we spent more % of budget than % of physical work done.
        df['progress_gap'] = df['safe_expenditure_percent'] - df['physical_progress']

    # --- PROTOTYPE RISK SCORING RULES (Retrospective / Static) ---
    # NOTE: This uses current snapshot data to evaluate CURRENT risk state.
    
    # Cost Risk Score (0-3)
    def calculate_cost_risk(row):
        overrun = row.get('cost_overrun_percent', 0)
        if overrun > 50: return 3
        elif overrun > 15: return 2
        elif overrun > 0: return 1
        return 0

    # Time Risk Score (0-3)
    def calculate_time_risk(row):
        overrun = row.get('time_overrun_percent', 0)
        if overrun > 50: return 3
        elif overrun > 20: return 2
        elif overrun > 0: return 1
        return 0

    # Progress Risk Score (0-3)
    # High gap between spend and progress = high risk
    def calculate_progress_risk(row):
        gap = row.get('progress_gap', 0)
        prog = row.get('physical_progress', 0)
        # If progress is very low (<10%) and it's not a new project, risk is high.
        # Simple heuristic:
        if gap > 30: return 3
        elif gap > 15: return 2
        elif prog < 5 and gap > 5: return 1
        return 0

    df['cost_risk_score'] = df.apply(calculate_cost_risk, axis=1)
    df['time_risk_score'] = df.apply(calculate_time_risk, axis=1)
    df['progress_risk_score'] = df.apply(calculate_progress_risk, axis=1)

    df['total_risk_score'] = df['cost_risk_score'] + df['time_risk_score'] + df['progress_risk_score']
    
    def assign_risk_category(score):
        if score >= 7: return 'CRITICAL'
        elif score >= 4: return 'HIGH'
        elif score >= 2: return 'MEDIUM'
        return 'LOW'

    df['risk_category'] = df['total_risk_score'].apply(assign_risk_category)

    # 1. Output High-Risk Candidates
    critical_projects = df[df['risk_category'] == 'CRITICAL'].sort_values(by='total_risk_score', ascending=False)
    critical_projects[['project_name', 'state', 'agency', 'total_risk_score', 'cost_overrun_percent', 'time_overrun_percent', 'progress_gap']].head(20).to_csv('outputs/member5_critical_projects.csv', index=False)
    print(f"Identified {len(critical_projects)} CRITICAL risk projects.")
    
    # 2. Risk Indicator Charts
    sns.set_theme(style="whitegrid")
    
    # A. Risk Category Distribution
    plt.figure(figsize=(8, 5))
    sns.countplot(data=df, x='risk_category', order=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'], palette=['green', 'yellow', 'orange', 'red'])
    plt.title('Project Risk Category Distribution (Prototype)')
    plt.ylabel('Number of Projects')
    plt.savefig('outputs/member5_risk_distribution.png', bbox_inches='tight')
    plt.close()

    # B. Progress Gap vs Cost Overrun (colored by Risk)
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='physical_progress', y='safe_expenditure_percent', hue='risk_category', 
                    hue_order=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'], palette=['green', 'yellow', 'orange', 'red'], alpha=0.6)
    # Add diagonal line (Expenditure = Progress)
    plt.plot([0, 100], [0, 100], 'k--', lw=1)
    plt.title('Physical Progress vs Expenditure (%)')
    plt.xlabel('Physical Progress (%)')
    plt.ylabel('Expenditure vs Original Cost (%)')
    plt.ylim(-5, max(df['safe_expenditure_percent'].max(), 100) + 10)
    plt.savefig('outputs/member5_progress_vs_expenditure.png', bbox_inches='tight')
    plt.close()
    
    # C. Risk by Agency (Top 15 Agencies)
    if 'agency' in df.columns:
        top_agencies = df['agency'].value_counts().head(15).index
        plt.figure(figsize=(12, 6))
        sns.countplot(data=df[df['agency'].isin(top_agencies)], x='agency', hue='risk_category',
                      hue_order=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'], palette=['green', 'yellow', 'orange', 'red'])
        plt.xticks(rotation=45, ha='right')
        plt.title('Risk Categories by Top 15 Agencies')
        plt.ylabel('Number of Projects')
        plt.legend(title='Risk Category')
        plt.savefig('outputs/member5_risk_by_agency.png', bbox_inches='tight')
        plt.close()

    print("Member 5 EDA and Risk calculation completed successfully.")

if __name__ == "__main__":
    main()
