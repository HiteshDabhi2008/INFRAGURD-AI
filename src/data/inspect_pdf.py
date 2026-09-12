"""
Quick PDF inspector — Member 1 utility to understand PDF structure
before building the extraction pipeline.
"""
import pdfplumber
import sys
import os

PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "FlashReport_July_2026.pdf")

def safe_print(text):
    """Print with fallback for non-ascii characters."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode('ascii'))

def inspect_pdf(pdf_path: str):
    with pdfplumber.open(pdf_path) as pdf:
        safe_print(f"Total pages: {len(pdf.pages)}")
        safe_print("=" * 80)

        # Inspect first 5 pages for structure
        for i, page in enumerate(pdf.pages[:5]):
            text = page.extract_text() or ""
            tables = page.extract_tables()
            safe_print(f"\n--- Page {i + 1} ---")
            safe_print(f"Tables found: {len(tables)}")
            safe_print(text[:500])
            safe_print("...")

        # Now scan for the main project table (Table 6: All Ongoing Projects)
        safe_print("\n" + "=" * 80)
        safe_print("SCANNING FOR 'Table 6' and project data tables...")
        
        table6_start = None
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if "Table 6" in text or "All Ongoing Projects" in text:
                safe_print(f"Page {i+1}: Contains 'Table 6' or 'All Ongoing Projects'")
                if table6_start is None:
                    table6_start = i

        # Find the actual structure of the project table
        safe_print("\n" + "=" * 80)
        safe_print("INSPECTING TABLE STRUCTURE...")
        
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if tables:
                for tidx, t in enumerate(tables):
                    if t and len(t) > 1:
                        # Check if any row starts with a serial number
                        for row in t[:5]:
                            if row and row[0] and str(row[0]).strip().isdigit():
                                safe_print(f"\nProject table found on page {i + 1}, table index {tidx}")
                                safe_print(f"  Columns: {len(t[0])}")
                                safe_print(f"  Rows: {len(t)}")
                                safe_print(f"  First 3 rows:")
                                for r in t[:3]:
                                    safe_print(f"    {r}")
                                # Now show the HEADER — go back one table or check previous page
                                safe_print(f"\n  FULL first 5 rows including potential header:")
                                for r in t[:5]:
                                    safe_print(f"    {r}")
                                
                                # Count total data rows across all pages
                                safe_print("\n" + "=" * 80)
                                safe_print("COUNTING ALL PROJECT ROWS ACROSS ENTIRE PDF...")
                                total_rows = 0
                                max_sl_no = 0
                                pages_with_data = []
                                for pi, pg in enumerate(pdf.pages):
                                    pg_tables = pg.extract_tables()
                                    for pt in pg_tables:
                                        if pt:
                                            for pr in pt:
                                                if pr and pr[0]:
                                                    val = str(pr[0]).strip()
                                                    if val.isdigit():
                                                        total_rows += 1
                                                        sl = int(val)
                                                        if sl > max_sl_no:
                                                            max_sl_no = sl
                                                        if pi + 1 not in pages_with_data:
                                                            pages_with_data.append(pi + 1)
                                safe_print(f"Total rows with numeric Sl.No: {total_rows}")
                                safe_print(f"Max Sl.No found: {max_sl_no}")
                                safe_print(f"Pages with data: {pages_with_data[:10]}...{pages_with_data[-10:]}")
                                safe_print(f"Total pages with data: {len(pages_with_data)}")
                                return
                                
if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else PDF_PATH
    path = os.path.abspath(path)
    safe_print(f"Inspecting: {path}")
    inspect_pdf(path)
