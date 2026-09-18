import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

# Setup path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from src.risk.risk_engine import predict_project_risk
import warnings
warnings.filterwarnings('ignore')

OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "member5")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    print("Loading datasets...")
    features_path = os.path.join(BASE_DIR, "data", "processed", "project_features.csv")
    master_path = os.path.join(BASE_DIR, "data", "processed", "master_projects.csv")
    
    features_df = pd.read_csv(features_path)
    master_df = pd.read_csv(master_path)
    
    # Merge needed categorical columns from master if they exist
    # master_projects has: state, agency, sector (wait, sector is inferred, but let's check what master has)
    # Actually, we can just merge all from master_df and features_df to have all possible required keys
    
    # report_month formatting differs ("Jul-26" vs "July 2026"), so we merge only on project_code
    merged_df = pd.merge(features_df, master_df, on="project_code", how="left", suffixes=("", "_master"))
    
    # Check if 'sector' exists, if not, create a dummy or infer from agency
    if "sector" not in merged_df.columns:
        # Fallback to a default if not created by Member 1/2
        merged_df["sector"] = "Unknown"
        
    print(f"Loaded {len(merged_df)} projects for scoring.")
    
    results = []
    
    for idx, row in merged_df.iterrows():
        # Convert row to dict, handling NaNs
        project_data = row.where(pd.notna(row), None).to_dict()
        
        try:
            risk = predict_project_risk(project_data)
            results.append(risk)
            if idx % 100 == 0:
                print(f"Processed {idx} projects...")
        except Exception as e:
            print(f"Error scoring project {project_data.get('project_code')}: {e}")
            continue
            
    print(f"Successfully scored {len(results)} projects.")
    
    # Create DataFrames for outputs
    results_df = pd.DataFrame([{
        "project_code": r["project_code"],
        "risk_score": r["risk_score"],
        "overall_risk": r["overall_risk"],
        "cost_risk_level": r["cost_model_output"]["risk_level"],
        "time_risk_level": r["time_model_output"]["risk_level"],
        "num_warnings": len(r["warnings"]),
        "explanation": r["explanation"]
    } for r in results])
    
    # 1. High Risk Projects
    high_risk_df = results_df[results_df["overall_risk"].isin(["HIGH", "CRITICAL"])]
    high_risk_df.to_csv(os.path.join(OUTPUT_DIR, "high_risk_projects.csv"), index=False)
    
    # 2. Early Warning Results (All projects with warnings)
    warnings_df = results_df[results_df["num_warnings"] > 0]
    warnings_df.to_csv(os.path.join(OUTPUT_DIR, "early_warning_results.csv"), index=False)
    
    # 3. Risk Summary
    summary = results_df["overall_risk"].value_counts().reset_index()
    summary.columns = ["Risk Category", "Count"]
    summary.to_csv(os.path.join(OUTPUT_DIR, "risk_summary.csv"), index=False)
    
    # 4. Risk Distribution Plot
    plt.figure(figsize=(8, 6))
    category_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    counts = results_df["overall_risk"].value_counts().reindex(category_order, fill_value=0)
    
    colors = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red", "CRITICAL": "darkred"}
    bar_colors = [colors[c] for c in category_order]
    
    counts.plot(kind="bar", color=bar_colors)
    plt.title("Portfolio Risk Distribution (Prototype Engine)")
    plt.xlabel("Risk Category")
    plt.ylabel("Number of Projects")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "risk_distribution.png"))
    
    print(f"Outputs saved to {OUTPUT_DIR}")
    
if __name__ == "__main__":
    main()
