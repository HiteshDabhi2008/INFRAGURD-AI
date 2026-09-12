import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import nbformat as nbf

def main():
    # Setup directories
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('notebooks', exist_ok=True)
    os.makedirs('docs', exist_ok=True)

    # Load data
    try:
        df = pd.read_csv('data/processed/paimana_master_v1.csv')
    except FileNotFoundError:
        print("Master dataset not found. Please ensure Member 1 data pipeline has run.")
        return

    # 1. TIME METRICS CALCULATION
    # Ensure dates are datetime objects
    date_cols = ['approval_date', 'original_completion_date', 'revised_completion_date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Calculate Durations in Months (approximate: days / 30.44)
    if 'approval_date' in df.columns and 'original_completion_date' in df.columns:
        df['original_duration_months'] = (df['original_completion_date'] - df['approval_date']).dt.days / 30.44
    
    if 'approval_date' in df.columns and 'revised_completion_date' in df.columns:
        df['revised_duration_months'] = (df['revised_completion_date'] - df['approval_date']).dt.days / 30.44

    # Time Overrun Calculation
    # If revised_completion_date is missing, we assume NO overrun (revised = original)
    if 'revised_completion_date' in df.columns and 'original_completion_date' in df.columns:
        # Fill missing revised dates with original dates
        revised_filled = df['revised_completion_date'].fillna(df['original_completion_date'])
        df['time_overrun_months'] = (revised_filled - df['original_completion_date']).dt.days / 30.44
        # Floor negative overruns to 0 (early completion) if any, or keep them to see early finishers
        # Let's keep them as is to see the true distribution
    
    # Binary Target
    df['time_overrun_flag'] = (df['time_overrun_months'] > 0).astype(int)

    # 2. TIME EDA
    total_projects = len(df)
    with_extension = df['time_overrun_flag'].sum()
    without_extension = total_projects - with_extension
    
    time_overrun_stats = df[df['time_overrun_months'] > 0]['time_overrun_months'].describe()
    
    print("=== TIME EDA STATISTICS ===")
    print(f"Total projects: {total_projects}")
    print(f"Projects with time extension: {with_extension} ({with_extension/total_projects*100:.1f}%)")
    print(f"Projects without time extension: {without_extension} ({without_extension/total_projects*100:.1f}%)")
    print("\nTime Overrun stats (Months, for delayed projects):")
    print(time_overrun_stats)
    
    # 3. VISUALIZATIONS
    sns.set_theme(style="whitegrid")

    # A. Duration Distribution
    if 'original_duration_months' in df.columns:
        plt.figure(figsize=(10, 6))
        sns.histplot(data=df, x='original_duration_months', bins=50, kde=True, color='blue')
        plt.title('Distribution of Original Project Durations (Months)')
        plt.xlabel('Original Duration (Months)')
        plt.ylabel('Number of Projects')
        plt.savefig('outputs/member4_duration_distribution.png', bbox_inches='tight')
        plt.close()

    # B. Time Overrun Distribution (only delayed projects)
    delayed_df = df[df['time_overrun_months'] > 0]
    plt.figure(figsize=(10, 6))
    sns.histplot(data=delayed_df, x='time_overrun_months', bins=50, kde=True, color='red')
    plt.title('Distribution of Time Overruns (Months) for Delayed Projects')
    plt.xlabel('Time Overrun (Months)')
    plt.ylabel('Number of Projects')
    plt.savefig('outputs/member4_time_overrun_distribution.png', bbox_inches='tight')
    plt.close()

    # C. Time Overrun by State (Top 15 States by count of delayed projects)
    if 'state' in df.columns:
        state_delay_counts = delayed_df['state'].value_counts().head(15).index
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=delayed_df[delayed_df['state'].isin(state_delay_counts)], 
                    x='state', y='time_overrun_months')
        plt.xticks(rotation=45, ha='right')
        plt.title('Time Overrun Distribution by Top 15 States (Delayed Projects)')
        plt.ylabel('Time Overrun (Months)')
        plt.xlabel('State')
        plt.savefig('outputs/member4_time_overrun_by_state.png', bbox_inches='tight')
        plt.close()

    # D. Time Overrun by Agency (Top 15)
    if 'agency' in df.columns:
        agency_delay_counts = delayed_df['agency'].value_counts().head(15).index
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=delayed_df[delayed_df['agency'].isin(agency_delay_counts)], 
                    x='agency', y='time_overrun_months')
        plt.xticks(rotation=45, ha='right')
        plt.title('Time Overrun Distribution by Top 15 Agencies (Delayed Projects)')
        plt.ylabel('Time Overrun (Months)')
        plt.xlabel('Agency')
        plt.savefig('outputs/member4_time_overrun_by_agency.png', bbox_inches='tight')
        plt.close()

    # E. Time Overrun vs Physical Progress
    if 'physical_progress' in df.columns:
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=delayed_df, x='physical_progress', y='time_overrun_months', alpha=0.5, color='purple')
        plt.title('Time Overrun vs Physical Progress')
        plt.xlabel('Physical Progress (%)')
        plt.ylabel('Time Overrun (Months)')
        plt.savefig('outputs/member4_time_overrun_vs_progress.png', bbox_inches='tight')
        plt.close()
        
    # F. Duration vs Physical Progress
    if 'original_duration_months' in df.columns and 'physical_progress' in df.columns:
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=df, x='original_duration_months', y='physical_progress', alpha=0.5, hue='time_overrun_flag', palette={0:'green', 1:'red'})
        plt.title('Original Duration vs Physical Progress')
        plt.xlabel('Original Duration (Months)')
        plt.ylabel('Physical Progress (%)')
        plt.legend(title='Delayed', labels=['No', 'Yes'])
        plt.savefig('outputs/member4_duration_vs_progress.png', bbox_inches='tight')
        plt.close()

    # GENERATE JUPYTER NOTEBOOK FOR MEMBER 4
    nb = nbf.v4.new_notebook()
    cells = []
    
    cells.append(nbf.v4.new_markdown_cell("# Member 4: Time EDA\nExploratory Data Analysis focused on schedule and time overruns."))
    
    code1 = """import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('../data/processed/paimana_master_v1.csv')
date_cols = ['approval_date', 'original_completion_date', 'revised_completion_date']
for col in date_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

df['original_duration_months'] = (df['original_completion_date'] - df['approval_date']).dt.days / 30.44
df['time_overrun_months'] = (df['revised_completion_date'].fillna(df['original_completion_date']) - df['original_completion_date']).dt.days / 30.44
df['time_overrun_flag'] = (df['time_overrun_months'] > 0).astype(int)
"""
    cells.append(nbf.v4.new_code_cell(code1))
    
    code2 = """# Display Stats
print(f"Total projects: {len(df)}")
delayed = df[df['time_overrun_months'] > 0]
print(f"Delayed projects: {len(delayed)}")
print(delayed['time_overrun_months'].describe())
"""
    cells.append(nbf.v4.new_code_cell(code2))
    
    code3 = """# Visualize Distribution
plt.figure(figsize=(10, 5))
sns.histplot(data=delayed, x='time_overrun_months', bins=50)
plt.title('Time Overrun Distribution (Months)')
plt.show()
"""
    cells.append(nbf.v4.new_code_cell(code3))
    
    nb['cells'] = cells
    with open('notebooks/member4_day1_time_eda.ipynb', 'w') as f:
        nbf.write(nb, f)
        
    print("Member 4 Charts generated successfully.")
    print("Notebook created at notebooks/member4_day1_time_eda.ipynb")

if __name__ == "__main__":
    main()
