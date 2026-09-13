import pandas as pd
import numpy as np
import os

def validate_data(input_file, output_master_file, report_file):
    # Ensure directories exist
    os.makedirs(os.path.dirname(output_master_file), exist_ok=True)
    os.makedirs(os.path.dirname(report_file), exist_ok=True)

    df = pd.read_csv(input_file)
    report_lines = ["# Data Quality Report", ""]
    
    total_records = len(df)
    report_lines.append(f"**Total Records Processed:** {total_records}")
    report_lines.append("")
    
    # 1. Required columns
    required_columns = ['project_name', 'agency', 'project_code', 'state', 'original_cost', 'revised_cost']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        report_lines.append(f"**Missing Required Columns:** {', '.join(missing_cols)}")
    else:
        report_lines.append("**Required Columns:** All present.")
        
    report_lines.append("")
    
    # 2. Duplicate Records
    duplicates = df[df.duplicated()]
    if not duplicates.empty:
        report_lines.append(f"**Duplicate Records Found:** {len(duplicates)}")
        # Drop true duplicates
        df = df.drop_duplicates()
    else:
        report_lines.append("**Duplicate Records:** None found.")
        
    # Project ID duplicates (sometimes one project has multiple entries for different months, but here we assume project_code + report_month should be unique)
    if 'project_code' in df.columns and 'report_month' in df.columns:
        id_month_dups = df[df.duplicated(subset=['project_code', 'report_month'])]
        if not id_month_dups.empty:
            report_lines.append(f"**Duplicate Project Codes per Month:** {len(id_month_dups)}")
            # Drop these specifically keeping last
            df = df.drop_duplicates(subset=['project_code', 'report_month'], keep='last')
        else:
            report_lines.append("**Duplicate Project Codes per Month:** None found.")
            
    report_lines.append("")
            
    # 3. Missing Values
    report_lines.append("## Missing Values Summary")
    missing_summary = df.isnull().sum()
    missing_summary = missing_summary[missing_summary > 0]
    if missing_summary.empty:
        report_lines.append("No missing values.")
    else:
        for col, count in missing_summary.items():
            report_lines.append(f"- **{col}**: {count} ({count/len(df):.2%})")
            
    report_lines.append("")
    
    # 4. Dates Validation
    report_lines.append("## Dates Validation")
    date_cols = ['approval_date', 'start_date', 'original_completion_date', 'revised_completion_date']
    date_errors = 0
    for col in date_cols:
        if col in df.columns:
            # Convert to datetime to check validity
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    if 'start_date' in df.columns and 'original_completion_date' in df.columns:
        invalid_dates = df[df['start_date'] > df['original_completion_date']]
        if not invalid_dates.empty:
            report_lines.append(f"- **Invalid Dates (Start > Original Completion)**: {len(invalid_dates)} records.")
            # For ML, we might keep them but it's an anomaly. Let's just flag it.
            date_errors += len(invalid_dates)
            
    if date_errors == 0:
        report_lines.append("All date relationships look valid.")
        
    report_lines.append("")
        
    # 5. Costs & Physical Progress (Negative / Invalid values)
    report_lines.append("## Numerical Validations (Costs & Progress)")
    num_cols = ['original_cost', 'revised_cost', 'cumulative_expenditure', 'physical_progress']
    num_errors = 0
    for col in num_cols:
        if col in df.columns:
            # Convert to numeric
            df[col] = pd.to_numeric(df[col], errors='coerce')
            invalid_num = df[df[col] < 0]
            if not invalid_num.empty:
                report_lines.append(f"- **Negative values in {col}**: {len(invalid_num)} records.")
                num_errors += len(invalid_num)
                # Cap at 0
                df.loc[df[col] < 0, col] = 0
                
            if col == 'physical_progress':
                invalid_prog = df[df[col] > 100]
                if not invalid_prog.empty:
                    report_lines.append(f"- **Physical progress > 100%**: {len(invalid_prog)} records.")
                    num_errors += len(invalid_prog)
                    # Cap at 100
                    df.loc[df[col] > 100, col] = 100
                    
    if num_errors == 0:
        report_lines.append("All numerical values are valid (no negative costs/progress).")
        
    report_lines.append("")
        
    # Save the report
    with open(report_file, 'w') as f:
        f.write('\n'.join(report_lines))
        
    # Task 2: Master Dataset
    df.to_csv(output_master_file, index=False)
    print(f"Validation complete. Master dataset saved to {output_master_file}")
    print(f"Report saved to {report_file}")

if __name__ == "__main__":
    validate_data(
        input_file="data/processed/paimana_cleaned.csv",
        output_master_file="data/processed/master_projects.csv",
        report_file="docs/data_quality_report.md"
    )
