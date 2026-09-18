import io
import csv
from typing import List
from sqlalchemy.orm import Session
from backend.models import Project, ProjectSnapshot, ProjectFeature, RiskAssessment

def generate_projects_csv(db: Session, projects: List[Project]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Project Code", "Project Name", "Agency", "State", "Sector", "Ministry",
        "Original Cost", "Revised Cost", "Cumulative Expenditure", "Physical Progress",
        "Overall Risk"
    ])
    
    for p in projects:
        # Get latest snapshot and risk
        snap = db.query(ProjectSnapshot).filter(ProjectSnapshot.project_code == p.project_code).order_by(ProjectSnapshot.id.desc()).first()
        risk = db.query(RiskAssessment).filter(RiskAssessment.project_code == p.project_code).order_by(RiskAssessment.id.desc()).first()
        
        rev_cost = snap.revised_cost if snap else p.original_cost
        cum_exp = snap.cumulative_expenditure if snap else 0.0
        prog = snap.physical_progress if snap else 0.0
        r_level = risk.overall_risk if risk else "Unknown"
        
        writer.writerow([
            p.project_code, p.project_name, p.agency, p.state, p.sector, p.ministry,
            p.original_cost, rev_cost, cum_exp, prog, r_level
        ])
        
    return output.getvalue()
