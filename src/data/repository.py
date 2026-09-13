import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'processed', 'database.sqlite')

def get_connection():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}. Please run init_db.py first.")
    # Use row factory to return dict-like rows
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_projects(include_features=True):
    """
    Retrieve all projects along with their latest snapshot and features.
    """
    conn = get_connection()
    query = """
        SELECT p.*, s.*, f.*
        FROM projects p
        LEFT JOIN project_snapshots s ON p.project_code = s.project_code
        LEFT JOIN project_features f ON p.project_code = f.project_code
        ORDER BY p.project_code
    """
    df = pd.read_sql_query(query, conn)
    # Deduplicate columns (project_code appears in all 3 tables)
    df = df.loc[:, ~df.columns.duplicated()]
    conn.close()
    return df

def get_project(project_code):
    """
    Retrieve a single project by its PAIMANA project code.
    """
    conn = get_connection()
    query = """
        SELECT p.*, s.*, f.*
        FROM projects p
        LEFT JOIN project_snapshots s ON p.project_code = s.project_code
        LEFT JOIN project_features f ON p.project_code = f.project_code
        WHERE p.project_code = ?
    """
    df = pd.read_sql_query(query, conn, params=(project_code,))
    df = df.loc[:, ~df.columns.duplicated()]
    conn.close()
    return df.to_dict('records')[0] if not df.empty else None

def get_projects_by_state(state):
    """
    Retrieve all projects for a specific state.
    """
    conn = get_connection()
    query = """
        SELECT p.*, s.*, f.*
        FROM projects p
        LEFT JOIN project_snapshots s ON p.project_code = s.project_code
        LEFT JOIN project_features f ON p.project_code = f.project_code
        WHERE p.state LIKE ?
    """
    df = pd.read_sql_query(query, conn, params=(f"%{state}%",))
    df = df.loc[:, ~df.columns.duplicated()]
    conn.close()
    return df

def get_projects_by_sector(sector):
    """
    Retrieve all projects matching a sector keyword.
    Note: Sector is not explicitly present in the initial extracted data,
    so this falls back to searching project_name and agency.
    """
    conn = get_connection()
    query = """
        SELECT p.*, s.*, f.*
        FROM projects p
        LEFT JOIN project_snapshots s ON p.project_code = s.project_code
        LEFT JOIN project_features f ON p.project_code = f.project_code
        WHERE p.project_name LIKE ? OR p.agency LIKE ?
    """
    df = pd.read_sql_query(query, conn, params=(f"%{sector}%", f"%{sector}%"))
    df = df.loc[:, ~df.columns.duplicated()]
    conn.close()
    return df

def get_projects_by_ministry(ministry):
    """
    Retrieve all projects matching a ministry keyword.
    Note: Ministry is not explicitly present in the initial extracted data,
    so this falls back to searching agency.
    """
    conn = get_connection()
    query = """
        SELECT p.*, s.*, f.*
        FROM projects p
        LEFT JOIN project_snapshots s ON p.project_code = s.project_code
        LEFT JOIN project_features f ON p.project_code = f.project_code
        WHERE p.agency LIKE ?
    """
    df = pd.read_sql_query(query, conn, params=(f"%{ministry}%",))
    df = df.loc[:, ~df.columns.duplicated()]
    conn.close()
    return df

def get_project_history(project_code):
    """
    Retrieve the historical snapshots of a project over time.
    """
    conn = get_connection()
    query = """
        SELECT s.*, d.report_month as data_source_month, d.file_path
        FROM project_snapshots s
        LEFT JOIN data_sources d ON s.data_source_id = d.id
        WHERE s.project_code = ?
        ORDER BY s.created_at ASC
    """
    df = pd.read_sql_query(query, conn, params=(project_code,))
    conn.close()
    return df

if __name__ == "__main__":
    # Test queries
    print("Testing Repository...")
    print(f"Total projects: {len(get_all_projects())}")
    
    # Try finding an active project
    test_state_df = get_projects_by_state("Andhra Pradesh")
    print(f"Total projects in Andhra Pradesh: {len(test_state_df)}")
    
    if not test_state_df.empty:
        test_code = test_state_df.iloc[0]['project_code']
        project = get_project(test_code)
        print(f"Details for project {test_code}: {project['project_name']} (Cost: {project['revised_cost']})")
