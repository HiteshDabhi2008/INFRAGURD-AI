import sqlite3
import pandas as pd
import os

def init_db(db_path, schema_path, master_file, feature_file):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect and run schema
    conn = sqlite3.connect(db_path)
    with open(schema_path, 'r') as f:
        schema_script = f.read()
    conn.executescript(schema_script)
    
    # Load data
    master_df = pd.read_csv(master_file)
    feature_df = pd.read_csv(feature_file)
    
    cursor = conn.cursor()
    
    # Insert Data Source (Mocking one for the July 2026 report)
    cursor.execute("""
        INSERT INTO data_sources (source_name, report_month, file_path) 
        VALUES (?, ?, ?)
    """, ("PAIMANA Flash Report", "July 2026", "FlashReport_July_2026.pdf"))
    source_id = cursor.lastrowid
    
    # Insert Projects
    for _, row in master_df.iterrows():
        # Insert Project (Ignore duplicates)
        cursor.execute("""
            INSERT OR IGNORE INTO projects (project_code, project_name, agency, state, approval_date, original_cost, original_completion_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (row['project_code'], row['project_name'], row['agency'], row['state'], row['approval_date'], row['original_cost'], row['original_completion_date']))
        
        # Insert Snapshot
        cursor.execute("""
            INSERT OR IGNORE INTO project_snapshots (project_code, report_month, start_date, revised_cost, revised_completion_date, cumulative_expenditure, physical_progress, data_source_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (row['project_code'], row.get('report_month', 'July 2026'), row['start_date'], row['revised_cost'], row['revised_completion_date'], row['cumulative_expenditure'], row['physical_progress'], source_id))
        
    # Insert Features
    for _, row in feature_df.iterrows():
        cursor.execute("""
            INSERT OR IGNORE INTO project_features (project_code, report_month, project_age_days, original_duration_days, revised_duration_days, expenditure_percent, progress_gap, cost_change, cost_change_percent, project_size_category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['project_code'], row.get('report_month', 'July 2026'), row['project_age_days'], 
            row['original_duration_days'], row['revised_duration_days'], row['expenditure_percent'], 
            row['progress_gap'], row['cost_change'], row['cost_change_percent'], row['project_size_category']
        ))
        
    conn.commit()
    conn.close()
    print(f"Database initialized and populated at {db_path}")

if __name__ == "__main__":
    init_db(
        db_path="data/processed/database.sqlite",
        schema_path="src/data/schema.sql",
        master_file="data/processed/master_projects.csv",
        feature_file="data/processed/project_features.csv"
    )
