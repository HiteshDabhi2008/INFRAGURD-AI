import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for plots
plt.style.use('ggplot')
sns.set_theme(style="whitegrid")

# Create output dir
output_dir = "outputs/member2"
os.makedirs(output_dir, exist_ok=True)

def main():
    print("Loading datasets...")
    master = pd.read_csv("data/processed/master_projects.csv")
    features = pd.read_csv("data/processed/project_features.csv")
    
    # Merge on project_code and report_month
    df = pd.merge(master, features, on=['project_code', 'report_month'], how='left')
    
    # Clean some strings
    df['state'] = df['state'].fillna('Unknown').astype(str)
    df['agency'] = df['agency'].fillna('Unknown').astype(str)
    
    # Helper to infer sector
    def infer_sector(row):
        agency = str(row['agency']).lower()
        name = str(row['project_name']).lower()
        if 'rail' in agency or 'rail' in name or 'rly' in agency:
            return 'Railways'
        if 'road' in agency or 'highway' in agency or 'nhai' in agency or 'nhidcl' in agency or 'road' in name:
            return 'Roads & Highways'
        if 'power' in agency or 'ntpc' in agency or 'pgcil' in agency or 'hydro' in agency or 'power' in name:
            return 'Power'
        if 'coal' in agency or 'mine' in agency or 'mining' in name or 'coal' in name:
            return 'Coal & Mining'
        if 'petroleum' in agency or 'oil' in agency or 'gas' in agency or 'refinery' in name or 'ongc' in agency:
            return 'Petroleum & Natural Gas'
        if 'water' in agency or 'irrigation' in name:
            return 'Water Resources'
        if 'urban' in agency or 'metro' in name or 'housing' in agency:
            return 'Urban Development'
        if 'telecom' in agency or 'bsnl' in agency or 'telecom' in name:
            return 'Telecommunications'
        if 'airport' in agency or 'aviation' in agency or 'airport' in name or 'aai' in agency:
            return 'Civil Aviation'
        if 'port' in agency or 'shipping' in agency or 'port' in name:
            return 'Ports & Shipping'
        return 'Other'

    df['sector'] = df.apply(infer_sector, axis=1)

    print(f"Total projects: {len(df)}")
    
    # --- 1. Projects by State ---
    plt.figure(figsize=(12, 8))
    state_counts = df['state'].value_counts().head(20)
    sns.barplot(x=state_counts.values, y=state_counts.index, palette="viridis")
    plt.title("Top 20 States/UTs by Project Count")
    plt.xlabel("Number of Projects")
    plt.ylabel("State/UT")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/projects_by_state.png")
    plt.close()

    # --- 2. Projects by Sector ---
    plt.figure(figsize=(10, 6))
    sector_counts = df['sector'].value_counts()
    sns.barplot(x=sector_counts.values, y=sector_counts.index, palette="magma")
    plt.title("Projects by Inferred Sector")
    plt.xlabel("Number of Projects")
    plt.ylabel("Sector")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/projects_by_sector.png")
    plt.close()

    # --- 3. Projects by Agency ---
    plt.figure(figsize=(10, 6))
    agency_counts = df['agency'].value_counts().head(10)
    sns.barplot(x=agency_counts.values, y=agency_counts.index, palette="plasma")
    plt.title("Top 10 Agencies by Project Count")
    plt.xlabel("Number of Projects")
    plt.ylabel("Agency")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/projects_by_agency.png")
    plt.close()

    # --- 4. Cost Distribution ---
    plt.figure(figsize=(10, 6))
    # Filter extreme outliers for visualization
    cost_data = df[df['original_cost'] < 20000]['original_cost'].dropna()
    sns.histplot(cost_data, bins=50, kde=True, color="blue")
    plt.title("Distribution of Original Costs (Projects < ₹20,000 Cr)")
    plt.xlabel("Original Cost (₹ Crore)")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/cost_distribution.png")
    plt.close()

    # --- 5. Cost Change Distribution ---
    plt.figure(figsize=(10, 6))
    # Filter extreme outliers
    cost_change_data = df[(df['cost_change_percent'] > -50) & (df['cost_change_percent'] < 200)]['cost_change_percent'].dropna()
    sns.histplot(cost_change_data, bins=50, kde=True, color="red")
    plt.title("Distribution of Cost Change Percentage (-50% to +200%)")
    plt.xlabel("Cost Change (%)")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/cost_change_distribution.png")
    plt.close()

    # --- 6. Progress Distribution ---
    plt.figure(figsize=(10, 6))
    progress_data = df['physical_progress'].dropna()
    sns.histplot(progress_data, bins=20, kde=True, color="green")
    plt.title("Distribution of Physical Progress (%)")
    plt.xlabel("Physical Progress (%)")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/progress_distribution.png")
    plt.close()

    # --- 7. Expenditure vs Progress ---
    plt.figure(figsize=(10, 6))
    plot_df = df[(df['physical_progress'].notna()) & (df['expenditure_percent'].notna())].copy()
    plot_df = plot_df[plot_df['expenditure_percent'] <= 150] # cap for plotting
    sns.scatterplot(data=plot_df, x='physical_progress', y='expenditure_percent', alpha=0.5, color="purple")
    # Add a diagonal line for y=x
    plt.plot([0, 100], [0, 100], color='red', linestyle='--')
    plt.title("Expenditure % vs Physical Progress %")
    plt.xlabel("Physical Progress (%)")
    plt.ylabel("Expenditure (%)")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/expenditure_vs_progress.png")
    plt.close()
    
    # --- 8. Project Age Distribution ---
    plt.figure(figsize=(10, 6))
    age_data = df['project_age_days'].dropna() / 365.25 # converting to years
    sns.histplot(age_data, bins=30, kde=True, color="orange")
    plt.title("Distribution of Project Age (Years)")
    plt.xlabel("Project Age (Years from Approval to July 2026)")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/project_age_distribution.png")
    plt.close()

    # --- 9. Correlation Matrix ---
    plt.figure(figsize=(12, 10))
    corr_cols = [
        'original_cost', 'revised_cost', 'cumulative_expenditure', 'physical_progress',
        'project_age_days', 'original_duration_days', 'revised_duration_days',
        'expenditure_percent', 'progress_gap', 'cost_change', 'cost_change_percent'
    ]
    # Calculate numeric correlations
    corr_data = df[corr_cols].corr()
    sns.heatmap(corr_data, annot=True, cmap="coolwarm", fmt=".2f", vmin=-1, vmax=1)
    plt.title("Correlation Matrix of Numeric Features")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/correlation_matrix.png")
    plt.close()

    print("\n--- PATTERN INVESTIGATION ---")
    
    # States with higher cost escalation (average cost change %)
    state_cost = df.groupby('state')['cost_change_percent'].mean().sort_values(ascending=False)
    print("\nTop 5 States by Avg Cost Escalation (%):")
    print(state_cost.head(5))
    
    # Agencies with higher cost escalation
    agency_cost = df.groupby('agency')['cost_change_percent'].mean().sort_values(ascending=False)
    print("\nTop 5 Agencies by Avg Cost Escalation (%):")
    print(agency_cost[agency_cost.index.isin(agency_counts.index)].head(5)) # Only consider top 10 agencies for stability

    # Sectors with higher cost escalation
    sector_cost = df.groupby('sector')['cost_change_percent'].mean().sort_values(ascending=False)
    print("\nSectors by Avg Cost Escalation (%):")
    print(sector_cost)
    
    # High expenditure but low progress
    # e.g., expenditure > 75%, progress < 25%
    high_spend_low_prog = df[(df['expenditure_percent'] > 75) & (df['physical_progress'] < 25)]
    print(f"\nProjects with >75% expenditure but <25% progress: {len(high_spend_low_prog)}")
    
    # Project size vs cost escalation
    size_cost = df.groupby('project_size_category')['cost_change_percent'].mean()
    print("\nAvg Cost Escalation (%) by Project Size:")
    print(size_cost)
    
    # Project age vs progress (Correlation)
    age_prog_corr = df['project_age_days'].corr(df['physical_progress'])
    print(f"\nCorrelation between Project Age and Physical Progress: {age_prog_corr:.3f}")
    
    print("\nEDA Visualizations generated in outputs/member2/")

if __name__ == "__main__":
    main()
