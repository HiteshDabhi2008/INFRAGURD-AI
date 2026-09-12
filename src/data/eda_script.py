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

print("=== BASIC EDA ===")
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"Null Values:\n{df.isnull().sum()}")

# 1. Cost Analysis (outputs/cost_analysis.png)
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='original_cost', y='revised_cost', alpha=0.5)
plt.plot([0, df['original_cost'].max()], [0, df['original_cost'].max()], 'r--', label='No Cost Overrun')
plt.title('Original vs Revised Cost (in ₹ Crore)')
plt.xlabel('Original Cost')
plt.ylabel('Revised Cost')
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "cost_analysis.png"))
plt.close()

# 2. Cost Overrun Distribution (outputs/cost_overrun_distribution.png)
plt.figure(figsize=(10, 6))
sns.histplot(data=df[df['cost_overrun_percent'] > 0], x='cost_overrun_percent', bins=50)
plt.title('Distribution of Cost Overrun Percentage (For Projects with > 0% Overrun)')
plt.xlabel('Cost Overrun Percentage (%)')
plt.ylabel('Number of Projects')
# Limit x axis to 95th percentile to avoid extreme outliers squishing the plot
p95 = df['cost_overrun_percent'].quantile(0.95)
plt.xlim(0, p95) 
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "cost_overrun_distribution.png"))
plt.close()

# 3. Expenditure vs Progress (outputs/expenditure_vs_progress.png)
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='physical_progress', y='expenditure_percent', alpha=0.5)
plt.plot([0, 100], [0, 100], 'r--', label='Expenditure matches Progress')
plt.title('Physical Progress vs Expenditure Percentage')
plt.xlabel('Physical Progress (%)')
plt.ylabel('Expenditure Percentage (%)')
# limit y-axis to handle extreme outliers
plt.ylim(0, 200)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "expenditure_vs_progress.png"))
plt.close()

# 4. Progress Distribution (outputs/progress_distribution.png)
plt.figure(figsize=(10, 6))
sns.histplot(data=df, x='physical_progress', bins=20)
plt.title('Distribution of Physical Progress')
plt.xlabel('Physical Progress (%)')
plt.ylabel('Number of Projects')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "progress_distribution.png"))
plt.close()

# 5. Projects by State (outputs/projects_by_state.png)
plt.figure(figsize=(12, 8))
state_counts = df['state'].value_counts().head(20)
sns.barplot(x=state_counts.values, y=state_counts.index, palette='viridis')
plt.title('Top 20 States by Number of Projects')
plt.xlabel('Number of Projects')
plt.ylabel('State')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "projects_by_state.png"))
plt.close()

# 6. Projects by Agency (outputs/projects_by_agency.png)
plt.figure(figsize=(12, 8))
agency_counts = df['agency'].value_counts().head(20)
sns.barplot(x=agency_counts.values, y=agency_counts.index, palette='magma')
plt.title('Top 20 Agencies by Number of Projects')
plt.xlabel('Number of Projects')
plt.ylabel('Agency')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "projects_by_agency.png"))
plt.close()

# No explicit sector column available yet to generate projects_by_sector.png
# We will create an empty dummy image or just skip it and note it in report.

print("EDA charts generated successfully.")

# Generate Notebook
nb = nbf.v4.new_notebook()

code_1 = """# Member 2 - Day 1 EDA
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load Data
df = pd.read_csv('../data/processed/paimana_master_v1.csv')
"""

code_2 = """# Basic EDA
print(df.shape)
df.info()
df.head()
"""

code_3 = """# Missing Values
df.isnull().sum()
"""

code_4 = """# Categorical Analysis
print("Top States:\\n", df['state'].value_counts().head(10))
print("\\nTop Agencies:\\n", df['agency'].value_counts().head(10))
"""

code_5 = """# Cost Analysis
df[['original_cost', 'revised_cost', 'cumulative_expenditure']].describe()
"""

code_6 = """# Physical Progress vs Expenditure Gap
df[['physical_progress', 'expenditure_percent', 'progress_gap']].describe()
"""

code_7 = """# Time Analysis
df[['original_duration_months', 'revised_duration_months', 'time_overrun_months']].describe()
"""

nb.cells = [
    nbf.v4.new_code_cell(code_1),
    nbf.v4.new_code_cell(code_2),
    nbf.v4.new_code_cell(code_3),
    nbf.v4.new_code_cell(code_4),
    nbf.v4.new_code_cell(code_5),
    nbf.v4.new_code_cell(code_6),
    nbf.v4.new_code_cell(code_7),
]

notebook_path = os.path.join(BASE_DIR, "notebooks", "member2_day1_eda.ipynb")
with open(notebook_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print(f"Notebook created at {notebook_path}")
