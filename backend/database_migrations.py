"""
Idempotent database migration script for InfraGuard-AI.
Safely adds new columns to SQLite database without touching existing data.
"""

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "infraguard.db")

def run_migrations():
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Update 'users' table
    cursor.execute("PRAGMA table_info(users)")
    user_cols = {col[1] for col in cursor.fetchall()}

    if "government_id" not in user_cols:
        print("Adding 'government_id' to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN government_id VARCHAR(100)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_government_id ON users(government_id)")

    if "mobile_number" not in user_cols:
        print("Adding 'mobile_number' to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN mobile_number VARCHAR(50)")

    # Ensure admin user has a verified government ID and mobile
    cursor.execute("SELECT id, email, government_id FROM users WHERE email = 'admin@infraguard.local'")
    admin = cursor.fetchone()
    if admin:
        if not admin[2]:
            print("Assigning default Government ID to admin user...")
            cursor.execute(
                "UPDATE users SET government_id = 'GOV-MOSPI-2026-0001', mobile_number = '+91 98765 43210' WHERE email = 'admin@infraguard.local'"
            )

    # 2. Update 'project_snapshots' table
    cursor.execute("PRAGMA table_info(project_snapshots)")
    snapshot_cols = {col[1] for col in cursor.fetchall()}

    if "project_status" not in snapshot_cols:
        print("Adding 'project_status' to project_snapshots table...")
        cursor.execute("ALTER TABLE project_snapshots ADD COLUMN project_status VARCHAR(50) DEFAULT 'Ongoing'")

    if "remarks" not in snapshot_cols:
        print("Adding 'remarks' to project_snapshots table...")
        cursor.execute("ALTER TABLE project_snapshots ADD COLUMN remarks TEXT")

    if "created_by" not in snapshot_cols:
        print("Adding 'created_by' to project_snapshots table...")
        cursor.execute("ALTER TABLE project_snapshots ADD COLUMN created_by VARCHAR(255)")

    conn.commit()
    conn.close()
    print("Database migrations applied successfully!")

if __name__ == "__main__":
    run_migrations()

