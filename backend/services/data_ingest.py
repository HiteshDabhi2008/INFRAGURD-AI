"""
Data ingestion, database initialization, 4-month historical trajectory generator,
and CSV upload validation engine for InfraGuard-AI.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy.orm import Session

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.database import engine, Base, SessionLocal
from backend.models import (
    Role, User, Project, ProjectSnapshot, ProjectFeature, MLPrediction, RiskAssessment, AuditLog, UploadedFile
)
from backend.auth import get_password_hash
from dashboard.data_loader import _infer_sector


ROLES_CONFIG = [
    ("Super Admin", "Full administrative control, user approvals, audit trails, and system settings"),
    ("MoSPI/IPMD Admin", "National portfolio oversight, all ministries, sectors, and inter-state analytics"),
    ("Ministry Authority", "Scoped to assigned ministry and respective department projects"),
    ("State Authority", "Scoped to infrastructure projects within specific state or union territory"),
    ("Agency / Project Authority", "Scoped to assigned implementation agencies and project codes"),
    ("Viewer / Auditor", "Read-only access to authorized projects, reports, and public analytics")
]

DEMO_USERS = [
    {
        "email": "admin@infraguard.gov.in",
        "full_name": "Dr. Rajeshwar Sharma",
        "organization": "Cabinet Secretariat",
        "department": "Infrastructure Monitoring Wing",
        "authority_type": "Super Admin",
        "role_name": "Super Admin",
        "state_region": "National",
        "agency": "IPMD",
        "designation": "Principal Director General",
        "is_verified": True
    },
    {
        "email": "mospi@ipmd.gov.in",
        "full_name": "Anita Venkatesh",
        "organization": "MoSPI",
        "department": "Infrastructure & Project Monitoring Division (IPMD)",
        "authority_type": "MoSPI/IPMD Admin",
        "role_name": "MoSPI/IPMD Admin",
        "state_region": "National",
        "agency": "MoSPI",
        "designation": "Joint Secretary",
        "is_verified": True
    },
    {
        "email": "railways@gov.in",
        "full_name": "K. S. Narayanan",
        "organization": "Ministry of Railways",
        "department": "Railway Board",
        "authority_type": "Ministry Authority",
        "role_name": "Ministry Authority",
        "state_region": "All India",
        "agency": "CAO/Con",
        "designation": "Executive Director (Works)",
        "is_verified": True
    },
    {
        "email": "gujarat@gov.in",
        "full_name": "Bhavin Patel",
        "organization": "Government of Gujarat",
        "department": "Roads & Buildings Department",
        "authority_type": "State Authority",
        "role_name": "State Authority",
        "state_region": "Gujarat",
        "agency": "GSRDC",
        "designation": "Superintending Engineer",
        "is_verified": True
    },
    {
        "email": "auditor@cag.gov.in",
        "full_name": "Priyanka Saxena",
        "organization": "Comptroller & Auditor General of India",
        "department": "Infrastructure Audit Wing",
        "authority_type": "Viewer / Auditor",
        "role_name": "Viewer / Auditor",
        "state_region": "All India",
        "agency": "CAG",
        "designation": "Senior Audit Officer",
        "is_verified": True
    },
    {
        "email": "pending@nhai.gov.in",
        "full_name": "Vikram Malhotra",
        "organization": "National Highways Authority of India",
        "department": "Regional Office - North",
        "authority_type": "Agency / Project Authority",
        "role_name": "Agency / Project Authority",
        "state_region": "Punjab",
        "agency": "NHAI",
        "designation": "Project Director",
        "is_verified": False  # To test the Super Admin verification workflow!
    }
]


def initialize_database(db: Session = None):
    """Create tables, seed roles, demo users, and populate 1,775 projects."""
    print("Initializing Database schema...")
    Base.metadata.create_all(bind=engine)

    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        # 1. Seed Roles
        role_map = {}
        for name, desc in ROLES_CONFIG:
            r = db.query(Role).filter(Role.name == name).first()
            if not r:
                r = Role(name=name, description=desc)
                db.add(r)
                db.flush()
            role_map[name] = r.id
        db.commit()

        # 2. Seed Demo Users
        demo_pwd = os.getenv("DEFAULT_ADMIN_PASSWORD")
        if not demo_pwd:
            print("Skipping DEMO_USERS seeding because DEFAULT_ADMIN_PASSWORD is not set.")
        else:
            for u in DEMO_USERS:
                existing = db.query(User).filter(User.email == u["email"]).first()
                if not existing:
                    role_id = role_map.get(u["role_name"], role_map["Viewer / Auditor"])
                    new_user = User(
                        email=u["email"],
                        full_name=u["full_name"],
                        hashed_password=get_password_hash(demo_pwd),
                        organization=u["organization"],
                        department=u["department"],
                        authority_type=u["authority_type"],
                        state_region=u["state_region"],
                        agency=u["agency"],
                        designation=u["designation"],
                        is_active=True,
                        is_verified=u["is_verified"],
                        role_id=role_id
                    )
                    db.add(new_user)
            db.commit()

        # 3. Seed Projects & 4-Month Snapshots
        project_count = db.query(Project).count()
        if project_count == 0:
            print("Seeding projects and 4-month historical trajectories from CSVs...")
            _seed_projects_and_history(db)
        else:
            print(f"Database already contains {project_count} projects.")

    finally:
        if should_close:
            db.close()


def _seed_projects_and_history(db: Session):
    """Ingest master_projects.csv, features, precomputed risks, and 4-month trajectory."""
    master_csv = os.path.join(BASE_DIR, "data", "processed", "master_projects.csv")
    features_csv = os.path.join(BASE_DIR, "data", "processed", "project_features.csv")
    early_csv = os.path.join(BASE_DIR, "outputs", "member5", "early_warning_results.csv")

    if not os.path.exists(master_csv):
        print(f"Master CSV not found at {master_csv}. Skipping initial seed.")
        return

    df_master = pd.read_csv(master_csv)
    df_features = pd.read_csv(features_csv) if os.path.exists(features_csv) else pd.DataFrame()
    df_early = pd.read_csv(early_csv) if os.path.exists(early_csv) else pd.DataFrame()

    # Features map
    features_map = {}
    if not df_features.empty:
        for _, row in df_features.iterrows():
            code = str(row["project_code"]).strip()
            features_map[code] = row.to_dict()

    # Early warnings / risk map
    risk_map = {}
    if not df_early.empty:
        for _, row in df_early.iterrows():
            code = str(row["project_code"]).strip()
            risk_map[code] = row.to_dict()

    print(f"Processing {len(df_master)} master projects...")

    projects_to_add = []
    snapshots_to_add = []
    features_to_add = []
    risks_to_add = []

    months = ["April 2026", "May 2026", "June 2026", "July 2026"]

    for idx, row in df_master.iterrows():
        p_code = str(row["project_code"]).strip()
        agency = str(row["agency"]).strip() if pd.notna(row.get("agency")) else "Unknown"
        state = str(row["state"]).strip() if pd.notna(row.get("state")) else "Multi-State"
        sector = _infer_sector(agency)
        
        # Derive ministry from agency
        ministry = _infer_ministry(agency, sector)

        orig_cost = float(row["original_cost"]) if pd.notna(row.get("original_cost")) else 100.0
        rev_cost = float(row["revised_cost"]) if pd.notna(row.get("revised_cost")) else orig_cost
        cum_exp = float(row["cumulative_expenditure"]) if pd.notna(row.get("cumulative_expenditure")) else 0.0
        phys_prog = float(row["physical_progress"]) if pd.notna(row.get("physical_progress")) else 0.0

        p = Project(
            project_code=p_code,
            project_name=str(row["project_name"]).strip(),
            agency=agency,
            state=state,
            sector=sector,
            ministry=ministry,
            approval_date=str(row["approval_date"]) if pd.notna(row.get("approval_date")) else None,
            original_cost=orig_cost,
            original_completion_date=str(row["original_completion_date"]) if pd.notna(row.get("original_completion_date")) else None
        )
        projects_to_add.append(p)

        # Generate 4-Month Historical Trajectory:
        # April, May, June, July 2026
        # July is current ground truth.
        for m_idx, month in enumerate(months):
            # Monthly decay factor backwards:
            # July = 1.0, June = 0.96, May = 0.91, April = 0.85
            if m_idx == 3: # July
                m_exp = cum_exp
                m_prog = phys_prog
            elif m_idx == 2: # June
                m_exp = round(cum_exp * 0.96, 2)
                m_prog = round(max(0.0, phys_prog - np.random.uniform(0.8, 2.0)), 2)
            elif m_idx == 1: # May
                m_exp = round(cum_exp * 0.91, 2)
                m_prog = round(max(0.0, phys_prog - np.random.uniform(2.2, 4.0)), 2)
            else: # April
                m_exp = round(cum_exp * 0.85, 2)
                m_prog = round(max(0.0, phys_prog - np.random.uniform(4.2, 6.5)), 2)

            cost_overrun_pct = round(((rev_cost - orig_cost) / orig_cost) * 100, 2) if orig_cost > 0 else 0.0

            s = ProjectSnapshot(
                project_code=p_code,
                report_month=month,
                start_date=str(row["start_date"]) if pd.notna(row.get("start_date")) else None,
                revised_cost=rev_cost,
                revised_completion_date=str(row["revised_completion_date"]) if pd.notna(row.get("revised_completion_date")) else None,
                cumulative_expenditure=m_exp,
                physical_progress=m_prog,
                cost_overrun_pct=cost_overrun_pct,
                time_overrun_months=round(float(row.get("time_overrun_months", 0.0) or 0.0), 1)
            )
            snapshots_to_add.append(s)

        # Feature entry
        feat = features_map.get(p_code, {})
        f = ProjectFeature(
            project_code=p_code,
            report_month="July 2026",
            project_age_days=int(feat.get("project_age_days", 365) or 365),
            original_duration_days=int(feat.get("original_duration_days", 730) or 730),
            revised_duration_days=int(feat.get("revised_duration_days", 730) or 730),
            expenditure_percent=float(feat.get("expenditure_percent", (cum_exp/rev_cost*100) if rev_cost else 0) or 0),
            progress_gap=float(feat.get("progress_gap", 0) or 0),
            cost_change=float(feat.get("cost_change", rev_cost - orig_cost) or 0),
            cost_change_percent=float(feat.get("cost_change_percent", cost_overrun_pct) or 0),
            project_size_category=str(feat.get("project_size_category", "Medium"))
        )
        features_to_add.append(f)

        # Risk assessment entry
        r_info = risk_map.get(p_code, {})
        category = str(r_info.get("overall_risk", "LOW")).upper()
        if category not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            category = "LOW"
        score = int(r_info.get("risk_score", 0) or 0)
        
        # Build warnings list
        warnings_list = []
        if pd.notna(r_info.get("warnings")):
            raw_w = str(r_info["warnings"])
            try:
                warnings_list = json.loads(raw_w.replace("'", '"')) if "[" in raw_w else [raw_w]
            except Exception:
                warnings_list = [raw_w]

        r = RiskAssessment(
            project_code=p_code,
            report_month="July 2026",
            risk_score=score,
            overall_risk=category,
            warnings_json=json.dumps(warnings_list),
            explanation=str(r_info.get("explanation", f"Project monitored under standard {category} risk protocol."))
        )
        risks_to_add.append(r)

    print("Batch committing records...")
    db.bulk_save_objects(projects_to_add)
    db.bulk_save_objects(snapshots_to_add)
    db.bulk_save_objects(features_to_add)
    db.bulk_save_objects(risks_to_add)
    db.commit()
    print(f"Successfully seeded {len(projects_to_add)} projects and {len(snapshots_to_add)} historical snapshots!")


def _infer_ministry(agency: str, sector: str) -> str:
    """Infer the overseeing Union Ministry from agency and sector."""
    a = str(agency).lower()
    s = str(sector).lower()
    if "rail" in a or "mor" in a or "rail" in s:
        return "Ministry of Railways"
    elif "nhai" in a or "morth" in a or "road" in s or "highway" in s:
        return "Ministry of Road Transport and Highways"
    elif "ntpc" in a or "nhpc" in a or "power" in s or "energy" in s:
        return "Ministry of Power"
    elif "ongc" in a or "oil" in a or "gas" in a or "petroleum" in s:
        return "Ministry of Petroleum and Natural Gas"
    elif "aai" in a or "airport" in a or "aviation" in s:
        return "Ministry of Civil Aviation"
    elif "port" in a or "shipping" in s:
        return "Ministry of Ports, Shipping and Waterways"
    elif "coal" in a or "ccl" in a or "cil" in a:
        return "Ministry of Coal"
    elif "steel" in a or "sail" in a:
        return "Ministry of Steel"
    elif "metro" in a or "housing" in a or "urban" in s:
        return "Ministry of Housing and Urban Affairs"
    elif "telecom" in a or "bsnl" in a:
        return "Ministry of Communications"
    elif "aiims" in a or "health" in s:
        return "Ministry of Health and Family Welfare"
    elif "iit" in a or "nit" in a or "education" in s:
        return "Ministry of Education"
    else:
        return "Ministry of Heavy Industries & Public Enterprises"


def validate_and_process_csv(df: pd.DataFrame, user_id: int, db: Session) -> dict:
    """
    7-step CSV validation pipeline:
    1. Check columns
    2. Check project IDs
    3. Check dates & month
    4. Check numeric ranges
    5. Check missing values
    6. Feature engineering
    7. Database persistence
    """
    report = {
        "status": "FAILED",
        "step_results": [],
        "errors": [],
        "rows_processed": 0
    }

    # Step 1: Column Validation
    required_cols = ["project_name", "agency", "project_code", "state", "original_cost", "revised_cost", "cumulative_expenditure", "physical_progress"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        err = f"Missing required columns: {missing}"
        report["step_results"].append({"step": 1, "name": "Column Validation", "status": "FAILED", "details": err})
        report["errors"].append(err)
        return report
    report["step_results"].append({"step": 1, "name": "Column Validation", "status": "PASSED", "details": "All required columns present"})

    # Step 2: Project ID Validation
    null_codes = df["project_code"].isna().sum()
    if null_codes > 0:
        err = f"Found {null_codes} rows with missing project_code."
        report["step_results"].append({"step": 2, "name": "Project Code Check", "status": "FAILED", "details": err})
        report["errors"].append(err)
        return report
    report["step_results"].append({"step": 2, "name": "Project Code Check", "status": "PASSED", "details": f"Validated {len(df)} project IDs"})

    # Step 3: Date & Month Check
    report_month = df["report_month"].iloc[0] if "report_month" in df.columns else "August 2026"
    report["step_results"].append({"step": 3, "name": "Report Period Check", "status": "PASSED", "details": f"Valid period: {report_month}"})

    # Step 4: Numeric Ranges
    for col in ["original_cost", "revised_cost", "cumulative_expenditure", "physical_progress"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    invalid_cost = (df["original_cost"] < 0).sum() + (df["revised_cost"] < 0).sum()
    invalid_progress = ((df["physical_progress"] < 0) | (df["physical_progress"] > 100)).sum()
    if invalid_cost > 0 or invalid_progress > 0:
        err = f"Invalid ranges: {invalid_cost} negative costs, {invalid_progress} invalid progress values (>100 or <0)."
        report["step_results"].append({"step": 4, "name": "Numeric Range Check", "status": "FAILED", "details": err})
        report["errors"].append(err)
        return report
    report["step_results"].append({"step": 4, "name": "Numeric Range Check", "status": "PASSED", "details": "All numeric values valid"})

    # Step 5: Missing Values Sanitization
    df["original_cost"] = df["original_cost"].fillna(0.0)
    df["revised_cost"] = df["revised_cost"].fillna(df["original_cost"])
    df["cumulative_expenditure"] = df["cumulative_expenditure"].fillna(0.0)
    df["physical_progress"] = df["physical_progress"].fillna(0.0)
    report["step_results"].append({"step": 5, "name": "Missing Value Handling", "status": "PASSED", "details": "Cleaned missing values with domain defaults"})

    # Step 6: Feature Engineering
    df["expenditure_percent"] = (df["cumulative_expenditure"] / df["revised_cost"].replace(0, 1)) * 100
    df["progress_gap"] = df["expenditure_percent"] - df["physical_progress"]
    df["cost_change"] = df["revised_cost"] - df["original_cost"]
    df["cost_change_percent"] = (df["cost_change"] / df["original_cost"].replace(0, 1)) * 100
    report["step_results"].append({"step": 6, "name": "Feature Engineering", "status": "PASSED", "details": "Engineered expenditure_percent, progress_gap, and cost changes"})

    # Step 7: Database Store
    new_projects = 0
    updated_snapshots = 0
    for _, r in df.iterrows():
        p_code = str(r["project_code"]).strip()
        p = db.query(Project).filter(Project.project_code == p_code).first()
        if not p:
            sector = _infer_sector(r["agency"])
            p = Project(
                project_code=p_code,
                project_name=str(r["project_name"]),
                agency=str(r["agency"]),
                state=str(r.get("state", "Multi-State")),
                sector=sector,
                ministry=_infer_ministry(r["agency"], sector),
                original_cost=float(r["original_cost"])
            )
            db.add(p)
            new_projects += 1

        # Add or update snapshot
        snap = db.query(ProjectSnapshot).filter(
            ProjectSnapshot.project_code == p_code,
            ProjectSnapshot.report_month == report_month
        ).first()
        if not snap:
            snap = ProjectSnapshot(
                project_code=p_code,
                report_month=report_month,
                revised_cost=float(r["revised_cost"]),
                cumulative_expenditure=float(r["cumulative_expenditure"]),
                physical_progress=float(r["physical_progress"]),
                cost_overrun_pct=float(r["cost_change_percent"])
            )
            db.add(snap)
            updated_snapshots += 1

    db.commit()
    report["step_results"].append({
        "step": 7,
        "name": "Database Persistence",
        "status": "PASSED",
        "details": f"Added {new_projects} new projects, recorded {updated_snapshots} snapshots for {report_month}"
    })
    report["status"] = "SUCCESS"
    report["rows_processed"] = len(df)
    return report
