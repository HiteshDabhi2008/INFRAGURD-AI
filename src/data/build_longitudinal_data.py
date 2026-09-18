"""
build_longitudinal_data.py - Member 3
============================================================
Extracts historical PAIMANA flash reports from April to July 2026,
cleans them using Member 1's cleaning functions, and concatenates
them into a longitudinal dataset for ML feature engineering.
"""

import os
import pandas as pd
from extract import extract_table6
from clean import clean_dataframe

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
OUT_CSV = os.path.join(BASE_DIR, "data", "processed", "paimana_historical.csv")

MONTHS = [
    {"file": "FlashReport_April2026.pdf", "report_month": "April 2026", "expected_count": 1832},
    {"file": "FlashReport_May2026.pdf", "report_month": "May 2026", "expected_count": 1832}, 
    {"file": "FlashReport_June_2026.pdf", "report_month": "June 2026", "expected_count": 1775},
    {"file": "FlashReport_July_2026.pdf", "report_month": "July 2026", "expected_count": 1775},
]

def map_month_to_date(month_str):
    mapping = {
        "April 2026": "2026-04",
        "May 2026": "2026-05",
        "June 2026": "2026-06",
        "July 2026": "2026-07"
    }
    return mapping.get(month_str, month_str)

def main():
    all_dfs = []
    
    for m in MONTHS:
        pdf_path = os.path.join(RAW_DIR, m["file"])
        if not os.path.exists(pdf_path):
            print(f"Skipping {m['file']} - not found.")
            continue
            
        print(f"\nProcessing {m['report_month']}...")
        df_raw = extract_table6(
            pdf_path=pdf_path,
            start_page=53,
            end_page=200,
            report_month=m['report_month'],
            source_report=m['file'],
            expected_count=m['expected_count']
        )
        
        df_clean = clean_dataframe(df_raw)
        
        # Add a date representation of the report month to allow sorting
        df_clean['report_date'] = df_clean['report_month'].apply(map_month_to_date)
        
        all_dfs.append(df_clean)
        
    if not all_dfs:
        print("No data extracted.")
        return
        
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Sort by project and chronological report date
    combined_df = combined_df.sort_values(by=['project_code', 'report_date'])
    
    # Save the output
    combined_df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\nSuccessfully saved longitudinal data ({len(combined_df)} rows) to {OUT_CSV}")

if __name__ == "__main__":
    main()
