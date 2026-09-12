"""
Inspect the detailed project table structure in Table 6 (pages 54+).
"""
import pdfplumber
import os

PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "FlashReport_July_2026.pdf")

def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode('ascii'))

def inspect_table6(pdf_path: str):
    with pdfplumber.open(pdf_path) as pdf:
        # Inspect pages 54-57 for the Table 6 header and structure
        for page_num in [53, 54, 55, 56, 57]:  # 0-indexed
            page = pdf.pages[page_num]
            text = page.extract_text() or ""
            tables = page.extract_tables()
            safe_print(f"\n{'='*80}")
            safe_print(f"PAGE {page_num + 1}")
            safe_print(f"Tables found: {len(tables)}")
            
            # Print text (first 300 chars)
            safe_print(f"\nText preview:")
            safe_print(text[:300])
            
            for tidx, t in enumerate(tables):
                if t:
                    safe_print(f"\n  Table {tidx}: {len(t)} rows x {len(t[0]) if t[0] else '?'} cols")
                    safe_print(f"  ALL rows of this table:")
                    for ri, r in enumerate(t):
                        safe_print(f"    Row {ri}: {r}")

        # Also check a page in the middle (around page 90) and near end
        safe_print(f"\n{'='*80}")
        safe_print("CHECKING MID AND END PAGES...")
        for page_num in [89, 140, 149, 150, 151]:
            page = pdf.pages[page_num]
            tables = page.extract_tables()
            for tidx, t in enumerate(tables):
                if t:
                    safe_print(f"\n  Page {page_num+1}, Table {tidx}: {len(t)} rows x {len(t[0]) if t[0] else '?'} cols")
                    safe_print(f"  First 2 rows: {t[:2]}")
                    safe_print(f"  Last 2 rows: {t[-2:]}")

        # Check the suspicious Sl.No range around 470, 524-528
        safe_print(f"\n{'='*80}")
        safe_print("SEARCHING FOR SUSPICIOUS Sl.No RANGES...")
        for i, page in enumerate(pdf.pages[53:]):  # Start from Table 6
            page_num = i + 54
            tables = page.extract_tables()
            for t in tables:
                if t:
                    for row in t:
                        if row and row[0]:
                            val = str(row[0]).strip()
                            if val in ['468', '469', '470', '471',
                                       '523', '524', '525', '526', '527', '528', '529',
                                       '1709', '1710', '1711', '1712', '1713',
                                       '1774', '1775']:
                                safe_print(f"  Page {page_num}, Sl.No {val}: {row[:4]}...")

if __name__ == "__main__":
    path = os.path.abspath(PDF_PATH)
    safe_print(f"Inspecting Table 6 structure in: {path}")
    inspect_table6(path)
