import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import nbformat as nbf

# Setup directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MASTER_CSV = os.path.join(BASE_DIR, "data", "processed", "paimana_master_v1.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load data
df = pd.read_csv(MASTER_CSV)

# Step 4 - Define Cost Metrics (Already largely present, but cost_change needs calculating)
df['cost_change'] = df['revised_cost'] - df['original_cost']
# We already have cost_overrun_percent and expenditure_percent from Member 1

print("=== COST EDA STATISTICS ===")
print(f"Total projects: {len(df)}")
print(f"Projects with cost increase: {len(df[df['cost_change'] > 0])}")
print(f"Projects with unchanged cost: {len(df[df['cost_change'] == 0])}")
print(f"Projects with cost decrease: {len(df[df['cost_change'] < 0])}")

print(f"\nCost Change stats (Crores):")
print(df['cost_change'].describe())

print(f"\nCost Overrun % stats (for those > 0):")
print(df[df['cost_overrun_percent'] > 0]['cost_overrun_percent'].describe())

# Step 10 - Create Charts

# 1. Cost Overrun Distribution
plt.figure(figsize=(10, 6))
sns.histplot(data=df[df['cost_overrun_percent'] > 0], x='cost_overrun_percent', bins=50)
plt.title('Distribution of Cost Overrun % (>0% only)')
plt.xlabel('Cost Overrun %')
plt.ylabel('Count')
p95 = df['cost_overrun_percent'].quantile(0.95)
plt.xlim(0, p95)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "member3_cost_overrun_distribution.png"))
plt.close()

# 2. Original vs Revised Cost
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='original_cost', y='revised_cost', alpha=0.5, color='blue')
plt.plot([0, df['original_cost'].max()], [0, df['original_cost'].max()], 'r--', label='Unchanged Cost Line')
plt.title('Original Cost vs Revised Cost (in ₹ Crore)')
plt.xlabel('Original Cost (₹ Crore)')
plt.ylabel('Revised Cost (₹ Crore)')
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "member3_original_vs_revised_cost.png"))
plt.close()

# 3. Cost Overrun by State (Top 15)
plt.figure(figsize=(12, 8))
state_overrun = df.groupby('state')['cost_overrun'].mean().sort_values(ascending=False).head(15) * 100
sns.barplot(x=state_overrun.values, y=state_overrun.index, color='teal')
plt.title('Top 15 States by % of Projects with Cost Overrun')
plt.xlabel('% of Projects with Overrun')
plt.ylabel('State')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "member3_cost_overrun_by_state.png"))
plt.close()

# 4. Cost Overrun by Agency (Top 15)
plt.figure(figsize=(12, 8))
# Only consider agencies with at least 5 projects
agency_counts = df['agency'].value_counts()
valid_agencies = agency_counts[agency_counts >= 5].index
agency_overrun = df[df['agency'].isin(valid_agencies)].groupby('agency')['cost_overrun'].mean().sort_values(ascending=False).head(15) * 100
sns.barplot(x=agency_overrun.values, y=agency_overrun.index, color='coral')
plt.title('Top 15 Agencies by % of Projects with Cost Overrun (Min 5 projects)')
plt.xlabel('% of Projects with Overrun')
plt.ylabel('Agency')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "member3_cost_overrun_by_agency.png"))
plt.close()

# 5. Cost Overrun vs Physical Progress
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df[df['cost_overrun_percent'] > 0], x='physical_progress', y='cost_overrun_percent', alpha=0.5)
plt.title('Physical Progress vs Cost Overrun %')
plt.xlabel('Physical Progress (%)')
plt.ylabel('Cost Overrun (%)')
plt.ylim(0, p95)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "member3_cost_overrun_vs_progress.png"))
plt.close()

# 6. Cost Overrun vs Expenditure
plt.figure(figsize=(10, 6))
# Filter extreme outliers for better visualization
valid_exp = df[(df['expenditure_percent'] <= 200) & (df['cost_overrun_percent'] > 0)]
sns.scatterplot(data=valid_exp, x='expenditure_percent', y='cost_overrun_percent', alpha=0.5, color='purple')
plt.title('Expenditure % vs Cost Overrun % (Zoomed <200%)')
plt.xlabel('Expenditure % (Relative to Revised Cost)')
plt.ylabel('Cost Overrun %')
plt.ylim(0, p95)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "member3_cost_overrun_vs_expenditure.png"))
plt.close()

print("\nMember 3 Charts generated successfully.")

# Generate Notebook
nb = nbf.v4.new_notebook()

cells = [
    nbf.v4.new_markdown_cell("# Member 3 - Cost EDA (Day 1)"),
    nbf.v4.new_code_cell("""import pandas as pd\nimport matplotlib.pyplot as plt\nimport seaborn as sns\n\ndf = pd.read_csv('../data/processed/paimana_master_v1.csv')\ndf['cost_change'] = df['revised_cost'] - df['original_cost']\ndf.shape"""),
    nbf.v4.new_markdown_cell("## 1. Cost Overview"),
    nbf.v4.new_code_cell("""print(f"Projects with cost increase: {len(df[df['cost_change'] > 0])}")\nprint(f"Projects unchanged: {len(df[df['cost_change'] == 0])}")\nprint(f"Projects with cost decrease: {len(df[df['cost_change'] < 0])}")"""),
    nbf.v4.new_markdown_cell("## 2. Statistical Summary of Overruns"),
    nbf.v4.new_code_cell("""df[df['cost_change'] > 0][['cost_change', 'cost_overrun_percent']].describe()"""),
    nbf.v4.new_markdown_cell("## 3. Cost vs Progress Correlation"),
    nbf.v4.new_code_cell("""df[['cost_overrun_percent', 'physical_progress', 'expenditure_percent']].corr()"""),
    nbf.v4.new_markdown_cell("## 4. State & Agency Breakdown"),
    nbf.v4.new_code_cell("""df.groupby('state')['cost_overrun'].mean().sort_values(ascending=False).head()""")
]

nb.cells = cells
notebook_path = os.path.join(BASE_DIR, "notebooks", "member3_day1_cost_eda.ipynb")
with open(notebook_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
print(f"Notebook created at {notebook_path}")
