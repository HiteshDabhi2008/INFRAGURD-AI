import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.auth import (
    check_project_access, create_access_token, get_current_user,
    get_current_verified_user, get_password_hash, log_audit_action,
    verify_password, _canonical_role
)
from backend.database import Base, engine, get_db
from backend.models import MLPrediction, Project, ProjectFeature, ProjectSnapshot, RiskAssessment, Role, User
from backend.services.ml_service import build_project_model_dict, run_full_risk_assessment
from backend.services.ai_service import (
    answer_user_query, get_authorized_portfolio_metrics, generate_portfolio_overview_report
)
from src.models.cost_model import predict_project_cost_risk
from src.models.time_model import predict_time_risk

Base.metadata.create_all(bind=engine)

app = FastAPI(title="InfraGuard-AI Main API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    email: str
    password: str


class RegistrationRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)
    organization: Optional[str] = None
    department: Optional[str] = None
    state_region: Optional[str] = None
    agency: Optional[str] = None
    designation: Optional[str] = None


class ChatRequest(BaseModel):
    message: Optional[str] = None
    query: Optional[str] = None
    project_code: Optional[str] = None
    state: Optional[str] = None
    ministry: Optional[str] = None


class MonthlyUpdateRequest(BaseModel):
    report_month: str = Field(min_length=3)
    physical_progress: Optional[float] = Field(default=None, ge=0, le=100)
    cumulative_expenditure: Optional[float] = Field(default=None, ge=0)
    status: Optional[str] = None
    project_status: Optional[str] = None
    revised_cost: Optional[float] = Field(default=None, ge=0)
    revised_completion_date: Optional[str] = None
    remarks: Optional[str] = None
    allow_edit: Optional[bool] = False


class CreateProjectRequest(BaseModel):
    project_code: str = Field(min_length=1)
    project_name: str = Field(min_length=2)
    ministry: str = Field(min_length=1)
    department: Optional[str] = None
    agency: Optional[str] = None
    sector: str = Field(min_length=1)
    state: str = Field(min_length=1)
    district: Optional[str] = None
    location: Optional[str] = None
    approval_date: Optional[str] = None
    original_completion_date: Optional[str] = None
    revised_completion_date: Optional[str] = None
    original_cost: float = Field(ge=0)
    revised_cost: Optional[float] = Field(default=None, ge=0)
    cumulative_expenditure: Optional[float] = Field(default=None, ge=0)
    physical_progress: Optional[float] = Field(default=None, ge=0, le=100)
    reporting_month: Optional[str] = None
    status: Optional[str] = "Ongoing"
    remarks: Optional[str] = None
    milestones: Optional[str] = None


class GenerateReportRequest(BaseModel):
    report_type: str = "portfolio_overview"
    project_code: Optional[str] = None


def _latest_snapshot(db: Session, project_code: str) -> Optional[ProjectSnapshot]:
    return (
        db.query(ProjectSnapshot)
        .filter(ProjectSnapshot.project_code == project_code)
        .order_by(ProjectSnapshot.created_at.desc(), ProjectSnapshot.id.desc())
        .first()
    )


def _latest_risk(db: Session, project_code: str) -> Optional[RiskAssessment]:
    return (
        db.query(RiskAssessment)
        .filter(RiskAssessment.project_code == project_code)
        .order_by(RiskAssessment.created_at.desc(), RiskAssessment.id.desc())
        .first()
    )


def _authorized(user: User, project: Project) -> None:
    if not check_project_access(user, project.state, project.agency, project.ministry, project.sector):
        raise HTTPException(status_code=403, detail="You are not authorized to access this project")


def _risk_dict(risk: Optional[RiskAssessment]) -> Dict[str, Any]:
    if not risk:
        return {"overall_risk": None, "risk_score": None, "warnings": [], "explanation": None}
    try:
        warnings = json.loads(risk.warnings_json or "[]")
    except json.JSONDecodeError:
        warnings = [risk.warnings_json] if risk.warnings_json else []
    return {
        "overall_risk": risk.overall_risk,
        "risk_score": risk.risk_score,
        "warnings": warnings,
        "explanation": risk.explanation,
        "report_month": risk.report_month,
    }


def _summary(db: Session, project: Project, user: User, snapshot: Optional[ProjectSnapshot] = None, risk: Optional[RiskAssessment] = None) -> Dict[str, Any]:
    _authorized(user, project)
    if snapshot is None:
        snapshot = _latest_snapshot(db, project.project_code)
    if risk is None:
        risk = _latest_risk(db, project.project_code)
    return {
        "project_code": project.project_code,
        "project_name": project.project_name,
        "agency": project.agency,
        "state": project.state,
        "sector": project.sector,
        "ministry": project.ministry,
        "department": getattr(project, "department", None),
        "district": getattr(project, "district", None),
        "location": getattr(project, "location", None),
        "status": getattr(project, "status", "Ongoing"),
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "created_by": getattr(project, "created_by", None),
        "original_cost": project.original_cost,
        "revised_cost": snapshot.revised_cost if snapshot else None,
        "cumulative_expenditure": snapshot.cumulative_expenditure if snapshot else None,
        "physical_progress": snapshot.physical_progress if snapshot else None,
        **_risk_dict(risk),
    }


def _detail(db: Session, project: Project, user: User) -> Dict[str, Any]:
    result = _summary(db, project, user)
    history = (
        db.query(ProjectSnapshot)
        .filter(ProjectSnapshot.project_code == project.project_code)
        .order_by(ProjectSnapshot.created_at.asc(), ProjectSnapshot.id.asc())
        .all()
    )
    result.update({
        "approval_date": project.approval_date,
        "original_completion_date": project.original_completion_date,
        "department": getattr(project, "department", None),
        "district": getattr(project, "district", None),
        "location": getattr(project, "location", None),
        "status": getattr(project, "status", "Ongoing"),
        "history": [{
            "id": item.id,
            "report_month": item.report_month,
            "revised_cost": item.revised_cost,
            "revised_completion_date": item.revised_completion_date,
            "cumulative_expenditure": item.cumulative_expenditure,
            "physical_progress": item.physical_progress,
            "cost_overrun_pct": item.cost_overrun_pct,
            "time_overrun_months": item.time_overrun_months,
            "remarks": item.remarks,
            "created_by": item.created_by,
        } for item in history],
    })
    return result


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.query(Project.project_code).limit(1).all()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    cost_ml = os.path.exists(os.path.join(BASE_DIR, "models", "cost_prediction_model.pkl"))
    time_ml = os.path.exists(os.path.join(BASE_DIR, "models", "time_prediction_model.pkl"))
    
    return {
        "status": "ok" if db_status == "connected" else "degraded", 
        "database": db_status,
        "cost_ml": "ready" if cost_ml else "missing",
        "time_ml": "ready" if time_ml else "missing",
        "rag": "not_configured"
    }


@app.get("/health/groq")
def groq_health():
    from backend.services.ai_service import groq_health as get_groq_health
    return get_groq_health()


@app.post("/api/auth/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    token = create_access_token({"sub": user.email})
    log_audit_action(db, user, "LOGIN", "User logged in via web portal.")
    return {"access_token": token, "token_type": "bearer", "user": {
        "id": user.id, "email": user.email, "full_name": user.full_name,
        "authority_type": user.authority_type, "organization": user.organization,
        "state_region": user.state_region, "agency": user.agency,
    }}


@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(request: RegistrationRequest, db: Session = Depends(get_db)):
    email = request.email.strip().casefold()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    viewer_role = db.query(Role).filter(Role.name == "Viewer / Auditor").first()
    if not viewer_role:
        viewer_role = Role(
            name="Viewer / Auditor",
            description="Read-only access to authorized projects and reports",
        )
        db.add(viewer_role)
        db.flush()

    user = User(
        email=email,
        full_name=request.full_name.strip(),
        hashed_password=get_password_hash(request.password),
        organization=request.organization,
        department=request.department,
        authority_type="Viewer / Auditor",
        state_region=request.state_region,
        agency=request.agency,
        designation=request.designation,
        is_active=True,
        is_verified=False,
        role_id=viewer_role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_audit_action(db, user, "REGISTRATION_SUBMITTED", "Account submitted for authority verification.")
    return {
        "id": user.id,
        "email": user.email,
        "status": "pending_verification",
        "message": "Registration submitted for authority verification",
    }


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    mobile_number: Optional[str] = None
    designation: Optional[str] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    agency: Optional[str] = None
    state_region: Optional[str] = None


class AdminUpdateUserRequest(BaseModel):
    authority_type: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    government_id: Optional[str] = None
    mobile_number: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    organization: Optional[str] = None
    agency: Optional[str] = None
    state_region: Optional[str] = None


def mask_gov_id(gov_id: Optional[str]) -> str:
    if not gov_id:
        return "Not Assigned"
    clean = str(gov_id).strip()
    if len(clean) <= 4:
        return f"GOV-****{clean}"
    return f"GOV-****{clean[-4:]}"


@app.post("/api/auth/change-password")
def change_password(request: ChangePasswordRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not verify_password(request.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    current_user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    log_audit_action(db, current_user, "PASSWORD_CHANGED", "User changed their password.")
    return {"message": "Password changed successfully"}


@app.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "authority_type": current_user.authority_type,
        "role": current_user.authority_type,
        "canonical_role": _canonical_role(current_user),
        "organization": current_user.organization,
        "department": current_user.department,
        "designation": current_user.designation,
        "state_region": current_user.state_region,
        "agency": current_user.agency,
        "government_id": current_user.government_id,
        "masked_government_id": mask_gov_id(current_user.government_id),
        "mobile_number": current_user.mobile_number,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }


@app.put("/api/auth/profile")
def update_profile(
    request: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    if request.full_name is not None and request.full_name.strip():
        current_user.full_name = request.full_name.strip()
    if request.mobile_number is not None:
        current_user.mobile_number = request.mobile_number.strip()
    if request.designation is not None:
        current_user.designation = request.designation.strip()
    if request.organization is not None:
        current_user.organization = request.organization.strip()
    if request.department is not None:
        current_user.department = request.department.strip()
    if request.agency is not None:
        current_user.agency = request.agency.strip()
    if request.state_region is not None:
        current_user.state_region = request.state_region.strip()

    db.commit()
    db.refresh(current_user)
    log_audit_action(db, current_user, "USER_PROFILE_UPDATED", f"User {current_user.email} updated profile details.")
    return get_me(current_user)


@app.get("/api/admin/users")
def list_admin_users(
    q: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    user_role = _canonical_role(current_user)
    if user_role not in {"SUPER_ADMIN", "MOSPI_IPMD_ADMIN"}:
        raise HTTPException(status_code=403, detail="Super Admin or MoSPI IPMD Admin privileges required")

    query = db.query(User)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(or_(
            User.email.ilike(term),
            User.full_name.ilike(term),
            User.government_id.ilike(term),
            User.agency.ilike(term),
            User.organization.ilike(term)
        ))
    if role and role not in {"All", "All Roles"}:
        query = query.filter(User.authority_type.ilike(f"%{role}%"))

    users = query.order_by(User.id.asc()).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "authority_type": u.authority_type,
            "organization": u.organization,
            "department": u.department,
            "designation": u.designation,
            "state_region": u.state_region,
            "agency": u.agency,
            "government_id": u.government_id,
            "masked_government_id": mask_gov_id(u.government_id),
            "mobile_number": u.mobile_number,
            "is_active": u.is_active,
            "is_verified": u.is_verified,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@app.put("/api/admin/users/{user_id}")
def admin_update_user(
    user_id: int,
    request: AdminUpdateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    admin_role = _canonical_role(current_user)
    if admin_role not in {"SUPER_ADMIN", "MOSPI_IPMD_ADMIN"}:
        raise HTTPException(status_code=403, detail="Super Admin or MoSPI IPMD Admin privileges required")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    changes = []
    if request.authority_type is not None:
        old_role = target_user.authority_type
        target_user.authority_type = request.authority_type
        r_obj = db.query(Role).filter(Role.name == request.authority_type).first()
        if r_obj:
            target_user.role_id = r_obj.id
        changes.append(f"Role: {old_role} -> {request.authority_type}")
    if request.is_active is not None:
        target_user.is_active = request.is_active
        changes.append(f"Active: {request.is_active}")
    if request.is_verified is not None:
        target_user.is_verified = request.is_verified
        changes.append(f"Verified: {request.is_verified}")
    if request.government_id is not None:
        target_user.government_id = request.government_id.strip() or None
        changes.append(f"GovID: {target_user.government_id}")
    if request.mobile_number is not None:
        target_user.mobile_number = request.mobile_number.strip() or None
    if request.full_name is not None:
        target_user.full_name = request.full_name.strip()
    if request.department is not None:
        target_user.department = request.department.strip() or None
    if request.designation is not None:
        target_user.designation = request.designation.strip() or None
    if request.organization is not None:
        target_user.organization = request.organization.strip() or None
    if request.agency is not None:
        target_user.agency = request.agency.strip() or None
    if request.state_region is not None:
        target_user.state_region = request.state_region.strip() or None

    db.commit()
    db.refresh(target_user)
    log_audit_action(db, current_user, "ADMIN_USER_UPDATED", f"Admin updated user {target_user.email}: {', '.join(changes)}")
    return {
        "id": target_user.id,
        "email": target_user.email,
        "full_name": target_user.full_name,
        "authority_type": target_user.authority_type,
        "organization": target_user.organization,
        "department": target_user.department,
        "designation": target_user.designation,
        "state_region": target_user.state_region,
        "agency": target_user.agency,
        "government_id": target_user.government_id,
        "masked_government_id": mask_gov_id(target_user.government_id),
        "mobile_number": target_user.mobile_number,
        "is_active": target_user.is_active,
        "is_verified": target_user.is_verified,
        "created_at": target_user.created_at.isoformat() if target_user.created_at else None,
    }


@app.get("/api/admin/audit-logs")
def list_admin_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    admin_role = _canonical_role(current_user)
    if admin_role not in {"SUPER_ADMIN", "MOSPI_IPMD_ADMIN"}:
        raise HTTPException(status_code=403, detail="Super Admin privileges required")

    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    logs = query.order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "user_email": l.user_email,
            "action": l.action,
            "details": l.details,
            "ip_address": l.ip_address,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None,
        }
        for l in logs
    ]


def _project_query(db: Session, user: User, q: Optional[str] = None, state: Optional[str] = None, sector: Optional[str] = None, ministry: Optional[str] = None, agency: Optional[str] = None, risk: Optional[str] = None, report_month: Optional[str] = None):
    # Sector authorization check
    user_sector = (getattr(user, "sector", None) or "").casefold()
    if user_sector and user_sector not in {"all", "all sectors", "national"}:
        if sector and user_sector not in sector.casefold():
            return []
        sector = getattr(user, "sector", None)

    query = db.query(Project)
    if q:
        term = f"%{q}%"
        query = query.filter(or_(Project.project_code.ilike(term), Project.project_name.ilike(term), Project.agency.ilike(term), Project.ministry.ilike(term)))
    if state:
        query = query.filter(Project.state.ilike(f"%{state}%"))
    if sector:
        query = query.filter(Project.sector.ilike(f"%{sector}%"))
    if ministry:
        query = query.filter(Project.ministry.ilike(f"%{ministry}%"))
    if agency:
        query = query.filter(Project.agency.ilike(f"%{agency}%"))
    projects = query.order_by(Project.project_code.asc()).all()
    all_snapshots = db.query(ProjectSnapshot).order_by(ProjectSnapshot.id.asc()).all()
    snapshot_map = {s.project_code: s for s in all_snapshots}
    all_risks = db.query(RiskAssessment).order_by(RiskAssessment.id.asc()).all()
    risk_map = {r.project_code: r for r in all_risks}

    output = []
    for project in projects:
        if not check_project_access(user, project.state, project.agency, project.ministry, project.sector):
            continue
        snap = snapshot_map.get(project.project_code)
        r_item = risk_map.get(project.project_code)
        item = _summary(db, project, user, snapshot=snap, risk=r_item)
        if risk and (item.get("overall_risk") or "").upper() != risk.upper():
            continue
        if report_month:
            if not snap or report_month.lower() not in (snap.report_month or "").lower():
                continue
        output.append(item)
    return output


@app.get("/api/sectors")
def get_sectors(db: Session = Depends(get_db)):
    """Get all distinct sectors available in the project database."""
    sectors = db.query(Project.sector).filter(Project.sector.isnot(None)).distinct().all()
    return sorted(list({s[0].strip() for s in sectors if s[0] and s[0].strip()}))


@app.get("/api/projects/check-duplicate")
def check_project_duplicate(
    project_code: str = Query(...),
    project_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    code_match = db.query(Project).filter(Project.project_code.ilike(project_code.strip())).first()
    if code_match:
        return {
            "exists": True,
            "possible_duplicate": True,
            "message": "Project ID already exists.",
            "existing_project": {
                "project_code": code_match.project_code,
                "project_name": code_match.project_name,
                "ministry": code_match.ministry,
                "agency": code_match.agency,
                "state": code_match.state,
                "sector": code_match.sector,
            }
        }

    similar_project = None
    if project_name and len(project_name.strip()) > 3:
        clean = project_name.strip()
        match = db.query(Project).filter(
            or_(
                Project.project_name.ilike(f"%{clean}%"),
                Project.project_name.ilike(f"{clean[:20]}%") if len(clean) >= 20 else False
            )
        ).first()
        if match:
            similar_project = {
                "project_code": match.project_code,
                "project_name": match.project_name,
                "ministry": match.ministry,
                "agency": match.agency,
                "state": match.state,
                "sector": match.sector,
            }

    return {
        "exists": False,
        "possible_duplicate": bool(similar_project),
        "existing_project": similar_project,
        "message": "Possible duplicate project found." if similar_project else "Project ID is available."
    }


@app.post("/api/projects", status_code=status.HTTP_201_CREATED)
def create_project(
    payload: CreateProjectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Create a new infrastructure project with role-based validation,
    non-negative cost checks, progress boundaries, initial snapshot, and audit logging.
    """
    user_role = _canonical_role(current_user)
    if user_role == "VIEWER_AUDITOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to create projects. Viewer / Auditor accounts have read-only access."
        )

    # Scoped authority checks
    if user_role not in {"SUPER_ADMIN", "MOSPI_IPMD_ADMIN"}:
        if user_role == "MINISTRY_AUTHORITY":
            user_org = (current_user.organization or current_user.department or "").casefold()
            if user_org and user_org not in (payload.ministry or "").casefold():
                raise HTTPException(status_code=403, detail="You can only create projects belonging to your authorized ministry.")
        elif user_role == "DEPARTMENT_AUTHORITY":
            user_dept = (current_user.department or current_user.organization or "").casefold()
            if user_dept and user_dept not in (payload.department or payload.ministry or "").casefold():
                raise HTTPException(status_code=403, detail="You can only create projects belonging to your authorized department.")
        elif user_role == "AGENCY_AUTHORITY":
            user_agency = (current_user.agency or "").casefold()
            if user_agency and user_agency not in (payload.agency or "").casefold():
                raise HTTPException(status_code=403, detail="You can only create projects belonging to your authorized agency.")
        elif user_role == "STATE_AUTHORITY":
            user_state = (current_user.state_region or "").casefold()
            if user_state and user_state not in {"all", "all india", "national"} and user_state not in (payload.state or "").casefold():
                raise HTTPException(status_code=403, detail="You can only create projects belonging to your authorized state.")

        # Sector authorization check
        user_sector = (getattr(current_user, "sector", None) or "").casefold()
        if user_sector and user_sector not in {"all", "all sectors", "national"}:
            if user_sector not in (payload.sector or "").casefold():
                raise HTTPException(status_code=403, detail=f"You are only authorized to create projects in the {current_user.sector} sector.")

    # Unique check
    existing = db.query(Project).filter(Project.project_code == payload.project_code.strip()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project ID already exists.")

    # Cost validations
    if payload.original_cost < 0:
        raise HTTPException(status_code=400, detail="Original Approved Cost cannot be negative.")
    if payload.revised_cost is not None and payload.revised_cost < 0:
        raise HTTPException(status_code=400, detail="Revised Cost cannot be negative.")
    if payload.cumulative_expenditure is not None and payload.cumulative_expenditure < 0:
        raise HTTPException(status_code=400, detail="Cumulative Expenditure cannot be negative.")

    # Progress validation
    if payload.physical_progress is not None:
        if payload.physical_progress < 0 or payload.physical_progress > 100:
            raise HTTPException(status_code=400, detail="Physical progress must be between 0 and 100%.")

    # Date ordering validation
    if payload.approval_date and payload.original_completion_date:
        try:
            d_app = datetime.fromisoformat(payload.approval_date.replace("Z", ""))
            d_comp = datetime.fromisoformat(payload.original_completion_date.replace("Z", ""))
            if d_comp < d_app:
                raise HTTPException(status_code=400, detail="Target completion date cannot be earlier than approval date.")
        except ValueError:
            pass

    # Create project
    project = Project(
        project_code=payload.project_code.strip(),
        project_name=payload.project_name.strip(),
        agency=payload.agency,
        state=payload.state,
        sector=payload.sector,
        ministry=payload.ministry,
        department=payload.department,
        district=payload.district,
        location=payload.location,
        status=payload.status or "Ongoing",
        approval_date=payload.approval_date,
        original_cost=payload.original_cost,
        original_completion_date=payload.original_completion_date,
        created_by=current_user.email,
        created_at=datetime.utcnow()
    )
    db.add(project)

    # Initial snapshot if progress, expenditure, or reporting month provided
    if payload.physical_progress is not None or payload.cumulative_expenditure is not None or payload.reporting_month:
        report_month = payload.reporting_month.strip() if payload.reporting_month else datetime.utcnow().strftime("%B %Y")
        snapshot = ProjectSnapshot(
            project_code=project.project_code,
            report_month=report_month,
            start_date=payload.approval_date,
            revised_cost=payload.revised_cost or payload.original_cost,
            revised_completion_date=payload.revised_completion_date or payload.original_completion_date,
            cumulative_expenditure=payload.cumulative_expenditure or 0.0,
            physical_progress=payload.physical_progress or 0.0,
            project_status=payload.status or "Ongoing",
            remarks=payload.remarks,
            created_by=current_user.email,
            created_at=datetime.utcnow()
        )
        db.add(snapshot)

    # Audit logging
    log_audit_action(
        db=db,
        user=current_user,
        action="PROJECT_CREATED",
        details=f"Registered new project {project.project_code} ({project.project_name}) | Ministry: {project.ministry} | Sector: {project.sector} | Cost: ₹{project.original_cost} Cr"
    )

    db.commit()
    db.refresh(project)
    return _detail(db, project, current_user)


@app.get("/api/projects/newly-added")
def get_newly_added_projects(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Retrieve newly registered projects sorted by created_at desc within authorized scope."""
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    all_snapshots = db.query(ProjectSnapshot).order_by(ProjectSnapshot.id.asc()).all()
    snapshot_map = {s.project_code: s for s in all_snapshots}
    all_risks = db.query(RiskAssessment).order_by(RiskAssessment.id.asc()).all()
    risk_map = {r.project_code: r for r in all_risks}

    output = []
    for project in projects:
        if not check_project_access(current_user, project.state, project.agency, project.ministry, project.sector):
            continue
        snap = snapshot_map.get(project.project_code)
        r_item = risk_map.get(project.project_code)
        item = _summary(db, project, current_user, snapshot=snap, risk=r_item)
        item["created_at"] = project.created_at.isoformat() if project.created_at else None
        item["created_by"] = project.created_by or "System Import"
        item["status"] = project.status or "Ongoing"
        output.append(item)
        if len(output) >= limit:
            break
    return output


@app.get("/api/projects/search")
def search_projects(q: str = Query(min_length=1), db: Session = Depends(get_db), current_user: User = Depends(get_current_verified_user)):
    return _project_query(db, current_user, q, None, None, None, None, None)[:25]


@app.get("/api/projects")
def list_projects(q: Optional[str] = None, state: Optional[str] = None, sector: Optional[str] = None, ministry: Optional[str] = None, agency: Optional[str] = None, risk: Optional[str] = None, report_month: Optional[str] = None, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), current_user: User = Depends(get_current_verified_user)):
    projects = _project_query(db, current_user, q, state, sector, ministry, agency, risk, report_month)
    start = (page - 1) * limit
    return {"total": len(projects), "page": page, "limit": limit, "pages": math.ceil(len(projects) / limit) if projects else 0, "projects": projects[start:start + limit]}


@app.get("/api/projects/{project_code}")
def get_project_details(project_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_verified_user)):
    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _authorized(current_user, project)
    return _detail(db, project, current_user)


@app.get("/api/projects/{project_code}/history")
def get_project_history(project_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_verified_user)):
    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _authorized(current_user, project)
    history = db.query(ProjectSnapshot).filter(ProjectSnapshot.project_code == project_code).order_by(ProjectSnapshot.created_at.asc(), ProjectSnapshot.id.asc()).all()
    return [{"id": item.id, "report_month": item.report_month, "revised_cost": item.revised_cost, "revised_completion_date": item.revised_completion_date, "cumulative_expenditure": item.cumulative_expenditure, "physical_progress": item.physical_progress, "cost_overrun_pct": item.cost_overrun_pct, "time_overrun_months": item.time_overrun_months, "remarks": item.remarks, "created_by": item.created_by} for item in history]


def _analytics(db: Session, user: User, field: str) -> List[Dict[str, Any]]:
    projects = [p for p in db.query(Project).all() if check_project_access(user, p.state, p.agency, p.ministry, p.sector)]
    all_snapshots = db.query(ProjectSnapshot).order_by(ProjectSnapshot.id.asc()).all()
    snapshot_map = {s.project_code: s for s in all_snapshots}
    all_risks = db.query(RiskAssessment).order_by(RiskAssessment.id.asc()).all()
    risk_map = {r.project_code: r for r in all_risks}

    groups = defaultdict(list)
    for project in projects:
        snap = snapshot_map.get(project.project_code)
        r_item = risk_map.get(project.project_code)
        groups[getattr(project, field) or "Unknown"].append(_summary(db, project, user, snapshot=snap, risk=r_item))
    return [{"name": name, "project_count": len(items), "original_cost": sum(x.get("original_cost") or 0 for x in items), "revised_cost": sum(x.get("revised_cost") or 0 for x in items), "expenditure": sum(x.get("cumulative_expenditure") or 0 for x in items), "average_progress": round(sum(x.get("physical_progress") or 0 for x in items) / len(items), 2) if items else 0, "high_risk_count": sum(1 for x in items if x.get("overall_risk") == "HIGH"), "critical_count": sum(1 for x in items if x.get("overall_risk") == "CRITICAL")} for name, items in sorted(groups.items())]


@app.get("/api/reports/portfolio-data")
def get_reports_portfolio_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Return aggregated, authorized portfolio statistics for executive reporting."""
    return get_authorized_portfolio_metrics(current_user, db)


@app.post("/api/reports/generate")
def generate_ai_report(
    payload: GenerateReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Generate structured AI report grounded in real database numbers via Groq."""
    try:
        return generate_portfolio_overview_report(
            user=current_user,
            db=db,
            report_type=payload.report_type,
            project_code=payload.project_code
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI report generation failed: {str(e)}"
        )


@app.post("/api/ai/chat")
def chat_with_ai(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Grounding AI chat interface connected to Groq."""
    query = req.message or req.query or ""
    if not query:
        raise HTTPException(status_code=400, detail="Message or query is required.")
    try:
        return answer_user_query(
            query=query,
            user=current_user,
            db=db,
            project_code=req.project_code,
            state=req.state,
            ministry=req.ministry
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI Assistant query failed: {str(e)}"
        )


@app.get("/api/analytics/overview")
@app.get("/api/dashboard/stats")
def overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_verified_user)):
    items = _project_query(db, current_user, None, None, None, None, None, None)
    risk_counts = defaultdict(int)
    for item in items:
        risk_counts[item.get("overall_risk") or "UNASSESSED"] += 1
    return {"total_projects": len(items), "ongoing_projects": sum(1 for x in items if (x.get("physical_progress") or 0) < 100), "high_risk_projects": risk_counts["HIGH"], "critical_risk_projects": risk_counts["CRITICAL"], "original_cost_total": sum(x.get("original_cost") or 0 for x in items), "revised_cost_total": sum(x.get("revised_cost") or 0 for x in items), "total_expenditure": sum(x.get("cumulative_expenditure") or 0 for x in items), "average_physical_progress": round(sum(x.get("physical_progress") or 0 for x in items) / len(items), 2) if items else 0, "risk_distribution": [{"name": name, "value": value} for name, value in risk_counts.items()]}


@app.get("/api/analytics/ministry")
def ministry_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_verified_user)): return _analytics(db, current_user, "ministry")


@app.get("/api/analytics/sector")
def sector_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_verified_user)): return _analytics(db, current_user, "sector")


@app.get("/api/analytics/state")
def state_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_verified_user)): return _analytics(db, current_user, "state")


@app.get("/api/analytics/agency")
def agency_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_verified_user)): return _analytics(db, current_user, "agency")


@app.get("/api/analytics/risk-dashboard")
def risk_dashboard_analytics(
    ministry: Optional[str] = None,
    sector: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    # 1. Fetch authorized projects
    query = db.query(Project)
    if ministry and ministry not in {"All", "All Ministries"}:
        query = query.filter(Project.ministry.ilike(f"%{ministry}%"))
    if sector and sector not in {"All", "All Sectors"}:
        query = query.filter(Project.sector.ilike(f"%{sector}%"))
    projects = [p for p in query.all() if check_project_access(current_user, p.state, p.agency, p.ministry, p.sector)]
    p_codes = {p.project_code for p in projects}

    # Distinct ministries and sectors for filter dropdowns (scoped to user's authorized access)
    all_user_projects = [p for p in db.query(Project.ministry, Project.sector, Project.state, Project.agency).all() 
                         if check_project_access(current_user, p.state, p.agency, p.ministry, p.sector)]
    distinct_ministries = sorted(list({p.ministry for p in all_user_projects if p.ministry}))
    distinct_sectors = sorted(list({p.sector for p in all_user_projects if p.sector}))

    # 2. Bulk load snapshots & risks
    all_snapshots = db.query(ProjectSnapshot).order_by(ProjectSnapshot.id.asc()).all()
    month_order = ["April 2026", "May 2026", "June 2026", "July 2026"]
    
    latest_snapshot_map = {}
    prev_snapshot_map = {}
    snapshots_by_month = defaultdict(dict)
    
    for s in all_snapshots:
        if s.project_code in p_codes:
            snapshots_by_month[s.report_month][s.project_code] = s
            if s.report_month == "July 2026":
                latest_snapshot_map[s.project_code] = s
            elif s.report_month == "June 2026":
                prev_snapshot_map[s.project_code] = s
            elif s.project_code not in latest_snapshot_map:
                latest_snapshot_map[s.project_code] = s
                
    all_risks = db.query(RiskAssessment).order_by(RiskAssessment.id.asc()).all()
    risk_map = {r.project_code: r for r in all_risks if r.project_code in p_codes}

    # 3. KPI & Aggregation Calculations
    total_projects = len(projects)
    risk_counts = defaultdict(int)
    early_warnings_list = []
    
    cost_overrun_risk_count = 0
    schedule_delay_risk_count = 0
    low_progress_count = 0
    exp_gap_count = 0
    
    perf_counts = {
        "Performing Well (Progress ≥75%)": 0,
        "Stable (Progress 40-74%)": 0,
        "Watch List (Progress <40%)": 0,
        "High Cost/Schedule Overrun": 0,
        "Critical Attention Required": 0,
    }
    
    ministry_risk_map = defaultdict(lambda: {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "CRITICAL": 0, "TOTAL": 0})
    high_risk_projects_list = []

    for p in projects:
        r = risk_map.get(p.project_code)
        s = latest_snapshot_map.get(p.project_code)
        
        overall = r.overall_risk.upper() if r and r.overall_risk else "LOW"
        score = r.risk_score if r else 0
        risk_counts[overall] += 1
        
        min_key = p.ministry or "Other"
        ministry_risk_map[min_key][overall] += 1
        ministry_risk_map[min_key]["TOTAL"] += 1

        prog = s.physical_progress if s and s.physical_progress is not None else 0.0
        cum_exp = s.cumulative_expenditure if s and s.cumulative_expenditure is not None else 0.0
        rev_cost = s.revised_cost if s and s.revised_cost else p.original_cost
        orig_cost = p.original_cost or 100.0
        cost_overrun_pct = round(((rev_cost - orig_cost) / orig_cost) * 100, 1) if orig_cost > 0 else 0.0
        time_overrun_m = s.time_overrun_months if s and s.time_overrun_months is not None else 0.0
        exp_pct = (cum_exp / rev_cost * 100) if rev_cost > 0 else 0.0
        gap = exp_pct - prog
        
        if cost_overrun_pct > 15:
            cost_overrun_risk_count += 1
        if time_overrun_m > 3:
            schedule_delay_risk_count += 1
        if prog < 30:
            low_progress_count += 1
        if gap > 20:
            exp_gap_count += 1

        if overall == "CRITICAL":
            perf_counts["Critical Attention Required"] += 1
        elif overall == "HIGH":
            perf_counts["High Cost/Schedule Overrun"] += 1
        elif prog >= 75:
            perf_counts["Performing Well (Progress ≥75%)"] += 1
        elif prog >= 40:
            perf_counts["Stable (Progress 40-74%)"] += 1
        else:
            perf_counts["Watch List (Progress <40%)"] += 1

        warnings = []
        if r and r.warnings_json and r.warnings_json.strip() not in {"[]", ""}:
            try:
                warnings = json.loads(r.warnings_json)
            except Exception:
                warnings = [r.warnings_json]
        elif r and r.explanation:
            bullets = [line.strip().lstrip("* -") for line in r.explanation.splitlines() if line.strip().startswith("*")]
            if bullets:
                warnings = bullets
            elif overall in {"CRITICAL", "HIGH"}:
                warnings = [f"{overall} risk threshold exceeded."]

        if warnings:
            w_text = warnings[0] if warnings else "Risk Alert"
            w_type = "Cost Overrun" if "cost" in w_text.lower() else "Time Overrun" if "time" in w_text.lower() or "schedule" in w_text.lower() else "Progress Delay" if "progress" in w_text.lower() else "Expenditure Gap"
            early_warnings_list.append({
                "project_code": p.project_code,
                "project_name": p.project_name,
                "risk_type": w_type,
                "date": s.report_month if s else "July 2026",
                "severity": overall,
                "status": "Open" if overall in {"CRITICAL", "HIGH"} else "In Progress",
                "explanation": w_text
            })

        if overall in {"CRITICAL", "HIGH"} or score >= 40:
            cost_prob = min(98, max(15, int(cost_overrun_pct * 1.2))) if cost_overrun_pct > 0 else 25
            time_prob = min(95, max(20, int(time_overrun_m * 3.5))) if time_overrun_m > 0 else 30
            high_risk_projects_list.append({
                "project_code": p.project_code,
                "project_name": p.project_name,
                "ministry": p.ministry or "Unassigned",
                "agency": p.agency or "Unassigned",
                "state": p.state or "Multi-State",
                "risk_level": overall,
                "risk_score": score,
                "cost_overrun_pct": max(0.0, cost_overrun_pct),
                "cost_probability": cost_prob,
                "time_overrun_months": max(0.0, time_overrun_m),
                "time_probability": time_prob,
                "overall_risk_pct": min(100, max(20, score)),
                "physical_progress": prog
            })

    high_risk_projects_list.sort(key=lambda x: (1 if x["risk_level"]=="CRITICAL" else 2 if x["risk_level"]=="HIGH" else 3, -x["risk_score"]))

    # 4. MoM changes
    june_high = 0
    june_med = 0
    june_low = 0
    for p in projects:
        js = prev_snapshot_map.get(p.project_code)
        if js:
            j_rev = js.revised_cost or p.original_cost
            j_orig = p.original_cost or 100.0
            j_cost_over = ((j_rev - j_orig) / j_orig * 100) if j_orig > 0 else 0
            j_time_over = js.time_overrun_months or 0
            if j_cost_over > 50 or j_time_over > 12:
                june_high += 1
            elif j_cost_over > 15 or j_time_over > 3:
                june_med += 1
            else:
                june_low += 1
        else:
            june_low += 1

    high_delta = (risk_counts["HIGH"] + risk_counts["CRITICAL"]) - june_high
    med_delta = risk_counts["MEDIUM"] - june_med
    low_delta = risk_counts["LOW"] - june_low

    def format_delta(d):
        return f"+{d}" if d > 0 else str(d)

    distribution = [
        {"name": "High Risk", "key": "HIGH", "count": risk_counts["HIGH"], "percent": round((risk_counts["HIGH"] / total_projects * 100), 1) if total_projects else 0, "color": "#ef4444"},
        {"name": "Medium Risk", "key": "MEDIUM", "count": risk_counts["MEDIUM"], "percent": round((risk_counts["MEDIUM"] / total_projects * 100), 1) if total_projects else 0, "color": "#f59e0b"},
        {"name": "Low Risk", "key": "LOW", "count": risk_counts["LOW"], "percent": round((risk_counts["LOW"] / total_projects * 100), 1) if total_projects else 0, "color": "#10b981"},
    ]
    if risk_counts["CRITICAL"] > 0:
        distribution.insert(0, {"name": "Critical Risk", "key": "CRITICAL", "count": risk_counts["CRITICAL"], "percent": round((risk_counts["CRITICAL"] / total_projects * 100), 1) if total_projects else 0, "color": "#991b1b"})

    trend_data = []
    month_names = {"April 2026": "Apr", "May 2026": "May", "June 2026": "Jun", "July 2026": "Jul"}
    for m in month_order:
        m_snaps = snapshots_by_month.get(m, {})
        m_high = 0
        m_med = 0
        m_low = 0
        for p in projects:
            ms = m_snaps.get(p.project_code)
            if ms:
                m_rev = ms.revised_cost or p.original_cost
                m_orig = p.original_cost or 100.0
                m_c_over = ((m_rev - m_orig) / m_orig * 100) if m_orig > 0 else 0
                m_t_over = ms.time_overrun_months or 0
                if m_c_over > 40 or m_t_over > 12:
                    m_high += 1
                elif m_c_over > 15 or m_t_over > 3:
                    m_med += 1
                else:
                    m_low += 1
            else:
                m_low += 1
        trend_data.append({
            "month": month_names.get(m, m[:3]),
            "full_month": m,
            "High": m_high,
            "Medium": m_med,
            "Low": m_low
        })

    performance_data = [
        {"category": cat, "count": count, "percent": round((count / total_projects * 100), 1) if total_projects else 0}
        for cat, count in perf_counts.items()
    ]

    sorted_mins = sorted(ministry_risk_map.items(), key=lambda x: x[1]["TOTAL"], reverse=True)[:7]
    heatmap_data = []
    total_h = 0
    total_m = 0
    total_l = 0
    for min_name, m_counts in sorted_mins:
        h_sum = m_counts["HIGH"] + m_counts["CRITICAL"]
        total_h += h_sum
        total_m += m_counts["MEDIUM"]
        total_l += m_counts["LOW"]
        short_name = min_name.replace("Ministry of ", "") if min_name.startswith("Ministry of ") else min_name
        heatmap_data.append({
            "ministry": short_name,
            "full_name": min_name,
            "high": h_sum,
            "medium": m_counts["MEDIUM"],
            "low": m_counts["LOW"],
            "total": m_counts["TOTAL"]
        })

    denom = max(1, total_projects)
    top_factors = [
        {"factor": "Cost Overrun Risk", "count": cost_overrun_risk_count, "percentage": round(cost_overrun_risk_count / denom * 100, 1)},
        {"factor": "Schedule Delay Risk", "count": schedule_delay_risk_count, "percentage": round(schedule_delay_risk_count / denom * 100, 1)},
        {"factor": "Low Physical Progress (<30%)", "count": low_progress_count, "percentage": round(low_progress_count / denom * 100, 1)},
        {"factor": "High Expenditure / Low Progress", "count": exp_gap_count, "percentage": round(exp_gap_count / denom * 100, 1)},
    ]

    return {
        "last_updated": "July 2026",
        "kpis": {
            "high_risk": risk_counts["HIGH"] + risk_counts["CRITICAL"],
            "high_risk_mom": format_delta(high_delta),
            "medium_risk": risk_counts["MEDIUM"],
            "medium_risk_mom": format_delta(med_delta),
            "low_risk": risk_counts["LOW"],
            "low_risk_mom": format_delta(low_delta),
            "total_projects": total_projects,
            "early_warnings_count": len(early_warnings_list),
            "early_warnings_mom": format_delta(len(early_warnings_list) - 18)
        },
        "distribution": distribution,
        "trend": trend_data,
        "performance": performance_data,
        "heatmap": heatmap_data,
        "heatmap_totals": {
            "high": total_h,
            "medium": total_m,
            "low": total_l,
            "total": total_h + total_m + total_l
        },
        "top_risk_factors": top_factors,
        "recent_early_warnings": early_warnings_list[:12],
        "high_risk_projects": high_risk_projects_list[:25],
        "ministries": distinct_ministries,
        "sectors": distinct_sectors
    }


def _model_input(db: Session, project_code: str, user: User):
    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _authorized(user, project)
    snapshot = _latest_snapshot(db, project_code)
    feature = db.query(ProjectFeature).filter(ProjectFeature.project_code == project_code).order_by(ProjectFeature.created_at.desc(), ProjectFeature.id.desc()).first()
    if not snapshot:
        raise HTTPException(status_code=422, detail="No monthly snapshot is available for this project")
    return project, snapshot, feature, build_project_model_dict(project, snapshot, feature)


@app.post("/api/ml/cost/predict")
def cost_predict(payload: Dict[str, str], db: Session = Depends(get_db), current_user: User = Depends(get_current_verified_user)):
    _, _, _, model_input = _model_input(db, payload.get("project_id") or payload.get("project_code") or "", current_user)
    try:
        result = predict_project_cost_risk(model_input)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Cost model unavailable: {exc}") from exc
    return {"project_id": model_input["project_code"], **result}


@app.post("/api/ml/time/predict")
def time_predict(payload: Dict[str, str], db: Session = Depends(get_db), current_user: User = Depends(get_current_verified_user)):
    _, _, _, model_input = _model_input(db, payload.get("project_id") or payload.get("project_code") or "", current_user)
    try:
        result = predict_time_risk(model_input)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Time model unavailable: {exc}") from exc
    return {"project_id": model_input["project_code"], **result}


@app.post("/api/risk/predict")
def risk_predict(payload: Dict[str, str], db: Session = Depends(get_db), current_user: User = Depends(get_current_verified_user)):
    _, _, _, model_input = _model_input(db, payload.get("project_id") or payload.get("project_code") or "", current_user)
    try:
        return run_full_risk_assessment(model_input)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Risk engine unavailable: {exc}") from exc


def normalize_state_name(name: str) -> str:
    if not name:
        return "Unknown"
    n = name.strip()
    low = n.lower()
    if "odisha" in low or "orissa" in low:
        return "Odisha"
    if "uttarakhand" in low or "uttaranchal" in low:
        return "Uttarakhand"
    if "andaman" in low:
        return "Andaman and Nicobar"
    if "dadra" in low or "daman" in low:
        return "Dadra and Nagar Haveli"
    if "jammu" in low:
        return "Jammu and Kashmir"
    return n


def _extract_states_for_project(raw_state: Optional[str]) -> List[str]:
    if not raw_state:
        return []
    s = raw_state.strip()
    if s.startswith("Multi-States (") and s.endswith(")"):
        inner = s[len("Multi-States ("):-1]
        return [p.strip() for p in inner.split(",") if p.strip()]
    if s in {"PAN India", "Offshore", "Unknown"}:
        return [s]
    return [s]


@app.get("/api/projects/{project_code}/snapshot/{report_month}")
def get_project_snapshot(
    project_code: str,
    report_month: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _authorized(current_user, project)
    snapshot = (
        db.query(ProjectSnapshot)
        .filter(ProjectSnapshot.project_code == project_code, ProjectSnapshot.report_month == report_month)
        .first()
    )
    if not snapshot:
        return {"exists": False, "snapshot": None}
    return {
        "exists": True,
        "snapshot": {
            "id": snapshot.id,
            "project_code": snapshot.project_code,
            "report_month": snapshot.report_month,
            "physical_progress": snapshot.physical_progress,
            "cumulative_expenditure": snapshot.cumulative_expenditure,
            "revised_cost": snapshot.revised_cost,
            "revised_completion_date": snapshot.revised_completion_date,
            "project_status": snapshot.project_status or "Ongoing",
            "remarks": snapshot.remarks,
            "created_by": snapshot.created_by,
            "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None
        }
    }


@app.post("/api/projects/{project_code}/monthly-update")
def monthly_update(
    project_code: str,
    request: MonthlyUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    user_role = _canonical_role(current_user)
    if user_role == "VIEWER_AUDITOR":
        raise HTTPException(status_code=403, detail="Viewer / Auditor role is read-only. Data modification is restricted.")

    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _authorized(current_user, project)

    existing = (
        db.query(ProjectSnapshot)
        .filter(ProjectSnapshot.project_code == project_code, ProjectSnapshot.report_month == request.report_month)
        .first()
    )

    if existing and not request.allow_edit:
        return JSONResponse(
            status_code=409,
            content={
                "detail": f"A snapshot for reporting month '{request.report_month}' already exists for this project.",
                "existing_snapshot": {
                    "id": existing.id,
                    "project_code": existing.project_code,
                    "report_month": existing.report_month,
                    "physical_progress": existing.physical_progress,
                    "cumulative_expenditure": existing.cumulative_expenditure,
                    "revised_cost": existing.revised_cost,
                    "revised_completion_date": existing.revised_completion_date,
                    "project_status": existing.project_status or "Ongoing",
                    "remarks": existing.remarks,
                    "created_by": existing.created_by,
                    "created_at": existing.created_at.isoformat() if existing.created_at else None
                }
            }
        )

    status_val = request.project_status or request.status or "Ongoing"
    orig_cost = project.original_cost or 0.0
    rev_cost = request.revised_cost if request.revised_cost is not None else (existing.revised_cost if existing and existing.revised_cost else orig_cost)
    cost_overrun_pct = round(((rev_cost - orig_cost) / orig_cost * 100), 2) if orig_cost > 0 else 0.0

    if existing and request.allow_edit:
        if request.physical_progress is not None:
            existing.physical_progress = request.physical_progress
        if request.cumulative_expenditure is not None:
            existing.cumulative_expenditure = request.cumulative_expenditure
        if request.revised_cost is not None:
            existing.revised_cost = request.revised_cost
        if request.revised_completion_date is not None:
            existing.revised_completion_date = request.revised_completion_date
        existing.project_status = status_val
        existing.cost_overrun_pct = cost_overrun_pct
        if request.remarks is not None:
            existing.remarks = request.remarks
        existing.created_by = current_user.email
        snapshot = existing
        action_name = "MONTHLY_UPDATE_EDITED"
    else:
        snapshot = ProjectSnapshot(
            project_code=project_code,
            report_month=request.report_month,
            physical_progress=request.physical_progress,
            cumulative_expenditure=request.cumulative_expenditure,
            revised_cost=rev_cost,
            revised_completion_date=request.revised_completion_date,
            cost_overrun_pct=cost_overrun_pct,
            project_status=status_val,
            remarks=request.remarks,
            created_by=current_user.email,
            created_at=datetime.utcnow()
        )
        db.add(snapshot)
        action_name = "MONTHLY_UPDATE_SUBMITTED"

    db.flush()

    # Recalculate ProjectFeature
    prev_feature = (
        db.query(ProjectFeature)
        .filter(ProjectFeature.project_code == project_code)
        .order_by(ProjectFeature.created_at.desc(), ProjectFeature.id.desc())
        .first()
    )

    cum_exp = snapshot.cumulative_expenditure or 0.0
    exp_pct = round((cum_exp / rev_cost * 100) if rev_cost > 0 else 0.0, 2)
    prog = snapshot.physical_progress or 0.0
    prog_gap = round(exp_pct - prog, 2)
    cost_chg = round(rev_cost - orig_cost, 2)

    existing_feat = (
        db.query(ProjectFeature)
        .filter(ProjectFeature.project_code == project_code, ProjectFeature.report_month == request.report_month)
        .first()
    )
    if not existing_feat:
        existing_feat = ProjectFeature(
            project_code=project_code,
            report_month=request.report_month,
            project_age_days=(prev_feature.project_age_days + 30) if prev_feature and prev_feature.project_age_days else 365,
            original_duration_days=prev_feature.original_duration_days if prev_feature else 730,
            revised_duration_days=prev_feature.revised_duration_days if prev_feature else 730,
            project_size_category=prev_feature.project_size_category if prev_feature else ("Mega" if orig_cost > 1000 else "Medium")
        )
        db.add(existing_feat)

    existing_feat.expenditure_percent = exp_pct
    existing_feat.progress_gap = prog_gap
    existing_feat.cost_change = cost_chg
    existing_feat.cost_change_percent = cost_overrun_pct
    db.flush()

    # Re-evaluate M3, M4, M5 pipeline
    model_dict = build_project_model_dict(project, snapshot, existing_feat)
    risk_res = run_full_risk_assessment(model_dict)

    # Upsert RiskAssessment
    risk_record = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.project_code == project_code, RiskAssessment.report_month == request.report_month)
        .first()
    )
    if not risk_record:
        risk_record = RiskAssessment(project_code=project_code, report_month=request.report_month)
        db.add(risk_record)

    risk_record.risk_score = risk_res.get("risk_score", 0)
    risk_record.overall_risk = risk_res.get("overall_risk", "LOW")
    risk_record.warnings_json = json.dumps(risk_res.get("warnings", []))
    risk_record.explanation = risk_res.get("explanation", "Calculated based on real-time cost and time models.")
    risk_record.created_at = datetime.utcnow()

    # Upsert MLPrediction
    pred_record = (
        db.query(MLPrediction)
        .filter(MLPrediction.project_code == project_code, MLPrediction.report_month == request.report_month)
        .first()
    )
    if not pred_record:
        pred_record = MLPrediction(project_code=project_code, report_month=request.report_month)
        db.add(pred_record)

    cost_out = risk_res.get("cost_model_output", {})
    time_out = risk_res.get("time_model_output", {})
    pred_record.cost_risk_level = cost_out.get("risk_level", "LOW")
    pred_record.predicted_cost_overrun = cost_out.get("expected_overrun_percent", 0.0)
    pred_record.cost_overrun_prob = 0.85 if cost_out.get("is_cost_overrun") else 0.15
    pred_record.time_risk_level = time_out.get("risk_level", "LOW")
    pred_record.time_overrun_prob = 0.85 if time_out.get("is_time_overrun") else 0.15
    pred_record.predicted_time_months = float(time_out.get("predicted_delay_months", 0.0) or 0.0)
    pred_record.created_at = datetime.utcnow()

    log_audit_action(
        db, current_user, action_name,
        f"Project {project_code}, month {request.report_month}: progress={prog}%, exp={cum_exp} Cr, risk={risk_record.overall_risk} ({risk_record.risk_score})"
    )

    db.commit()
    db.refresh(snapshot)

    return {
        "success": True,
        "message": f"Monthly update for {request.report_month} successfully saved.",
        "snapshot": {
            "id": snapshot.id,
            "project_code": snapshot.project_code,
            "report_month": snapshot.report_month,
            "physical_progress": snapshot.physical_progress,
            "cumulative_expenditure": snapshot.cumulative_expenditure,
            "revised_cost": snapshot.revised_cost,
            "revised_completion_date": snapshot.revised_completion_date,
            "project_status": snapshot.project_status,
            "remarks": snapshot.remarks,
            "created_by": snapshot.created_by,
            "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None
        },
        "risk_assessment": {
            "risk_score": risk_record.risk_score,
            "overall_risk": risk_record.overall_risk,
            "warnings": risk_res.get("warnings", [])
        },
        "predictions": {
            "cost_risk_level": pred_record.cost_risk_level,
            "predicted_cost_overrun": pred_record.predicted_cost_overrun,
            "time_risk_level": pred_record.time_risk_level,
            "predicted_time_months": pred_record.predicted_time_months
        }
    }


@app.get("/api/analytics/state/map")
def state_map_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_verified_user)):
    projects = [p for p in db.query(Project).all() if check_project_access(current_user, p.state, p.agency, p.ministry, p.sector)]
    p_codes = {p.project_code for p in projects}

    all_snapshots = db.query(ProjectSnapshot).order_by(ProjectSnapshot.id.asc()).all()
    latest_snapshot_map = {}
    for s in all_snapshots:
        if s.project_code in p_codes:
            latest_snapshot_map[s.project_code] = s

    all_risks = db.query(RiskAssessment).order_by(RiskAssessment.id.asc()).all()
    latest_risk_map = {}
    for r in all_risks:
        if r.project_code in p_codes:
            latest_risk_map[r.project_code] = r

    state_data = defaultdict(lambda: {
        "state_name": "",
        "project_count": 0,
        "high_risk_count": 0,
        "critical_count": 0,
        "delayed_count": 0,
        "total_delay_months": 0.0,
        "progress_sum": 0.0,
        "original_cost": 0.0,
        "revised_cost": 0.0,
        "cumulative_expenditure": 0.0,
        "risk_counts": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
    })

    for p in projects:
        st_list = _extract_states_for_project(p.state)
        snap = latest_snapshot_map.get(p.project_code)
        risk = latest_risk_map.get(p.project_code)

        orig_cost = p.original_cost or 0.0
        rev_cost = snap.revised_cost if snap and snap.revised_cost else orig_cost
        exp = snap.cumulative_expenditure if snap and snap.cumulative_expenditure else 0.0
        prog = snap.physical_progress if snap and snap.physical_progress else 0.0
        delay_m = snap.time_overrun_months if snap and snap.time_overrun_months else 0.0
        risk_level = (risk.overall_risk if risk else "LOW").upper()
        if risk_level not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            risk_level = "LOW"
        risk_score = risk.risk_score if risk else 0

        for st in st_list:
            norm_st = normalize_state_name(st)
            if norm_st in {"PAN India", "Offshore", "Unknown"}:
                continue
            entry = state_data[norm_st]
            entry["state_name"] = norm_st
            entry["project_count"] += 1
            if risk_level in {"HIGH", "CRITICAL"} or risk_score >= 50:
                entry["high_risk_count"] += 1
            if risk_level == "CRITICAL" or risk_score >= 75:
                entry["critical_count"] += 1
            if delay_m > 0:
                entry["delayed_count"] += 1
            entry["total_delay_months"] += delay_m
            entry["progress_sum"] += prog
            entry["original_cost"] += orig_cost
            entry["revised_cost"] += rev_cost
            entry["cumulative_expenditure"] += exp
            entry["risk_counts"][risk_level] += 1

    formatted_states = {}
    for st_name, data in state_data.items():
        cnt = data["project_count"]
        avg_prog = round(data["progress_sum"] / cnt, 1) if cnt > 0 else 0.0
        avg_delay = round(data["total_delay_months"] / cnt, 1) if cnt > 0 else 0.0
        formatted_states[st_name] = {
            "state_name": st_name,
            "project_count": cnt,
            "high_risk_count": data["high_risk_count"],
            "critical_count": data["critical_count"],
            "delayed_count": data["delayed_count"],
            "avg_delay_months": avg_delay,
            "avg_progress": avg_prog,
            "original_cost": round(data["original_cost"], 2),
            "revised_cost": round(data["revised_cost"], 2),
            "cumulative_expenditure": round(data["cumulative_expenditure"], 2),
            "cost_utilization_pct": round((data["cumulative_expenditure"] / data["revised_cost"] * 100), 1) if data["revised_cost"] > 0 else 0.0,
            "risk_distribution": data["risk_counts"],
            "total_projects": cnt
        }

    tot_proj = len(projects)
    tot_orig = sum(p.original_cost or 0.0 for p in projects)
    tot_rev = sum(latest_snapshot_map[p.project_code].revised_cost if p.project_code in latest_snapshot_map and latest_snapshot_map[p.project_code].revised_cost else (p.original_cost or 0.0) for p in projects)
    tot_exp = sum(latest_snapshot_map[p.project_code].cumulative_expenditure or 0.0 for p in projects if p.project_code in latest_snapshot_map)
    tot_prog = sum(latest_snapshot_map[p.project_code].physical_progress or 0.0 for p in projects if p.project_code in latest_snapshot_map)
    avg_prog_all = round(tot_prog / tot_proj, 1) if tot_proj > 0 else 0.0
    high_risk_all = sum(1 for p in projects if p.project_code in latest_risk_map and (latest_risk_map[p.project_code].overall_risk in {"HIGH", "CRITICAL"} or (latest_risk_map[p.project_code].risk_score or 0) >= 50))
    critical_all = sum(1 for p in projects if p.project_code in latest_risk_map and (latest_risk_map[p.project_code].overall_risk == "CRITICAL" or (latest_risk_map[p.project_code].risk_score or 0) >= 75))
    delayed_all = sum(1 for p in projects if p.project_code in latest_snapshot_map and (latest_snapshot_map[p.project_code].time_overrun_months or 0) > 0)

    sorted_by_count = sorted(formatted_states.values(), key=lambda x: x["project_count"], reverse=True)
    top_states_by_projects = [{"state": s["state_name"], "projects": s["project_count"], "high_risk": s["high_risk_count"]} for s in sorted_by_count[:10]]

    risk_distribution_by_state = [
        {
            "state": s["state_name"],
            "LOW": s["risk_distribution"]["LOW"],
            "MEDIUM": s["risk_distribution"]["MEDIUM"],
            "HIGH": s["risk_distribution"]["HIGH"],
            "CRITICAL": s["risk_distribution"]["CRITICAL"],
            "total": s["project_count"]
        }
        for s in sorted_by_count[:10]
    ]

    sorted_by_delay = sorted(formatted_states.values(), key=lambda x: (x["delayed_count"], x["avg_delay_months"]), reverse=True)
    delay_analysis_by_state = [
        {
            "state": s["state_name"],
            "delayed_projects": s["delayed_count"],
            "avg_delay_months": s["avg_delay_months"],
            "total_projects": s["project_count"]
        }
        for s in sorted_by_delay[:10]
    ]

    avg_progress_by_state = [
        {
            "state": s["state_name"],
            "avg_progress": s["avg_progress"],
            "project_count": s["project_count"]
        }
        for s in sorted(formatted_states.values(), key=lambda x: x["avg_progress"], reverse=True)[:10]
    ]

    financial_overview_by_state = [
        {
            "state": s["state_name"],
            "revised_cost": s["revised_cost"],
            "cumulative_expenditure": s["cumulative_expenditure"],
            "utilization_pct": s["cost_utilization_pct"]
        }
        for s in sorted(formatted_states.values(), key=lambda x: x["revised_cost"], reverse=True)[:10]
    ]

    return {
        "summary": {
            "total_states": len(formatted_states),
            "total_projects": tot_proj,
            "total_cost": round(tot_rev, 2),
            "original_cost": round(tot_orig, 2),
            "total_expenditure": round(tot_exp, 2),
            "avg_progress": avg_prog_all,
            "high_risk_projects": high_risk_all,
            "critical_projects": critical_all,
            "delayed_projects": delayed_all
        },
        "state_stats": formatted_states,
        "top_states_by_projects": top_states_by_projects,
        "risk_distribution_by_state": risk_distribution_by_state,
        "delay_analysis_by_state": delay_analysis_by_state,
        "avg_progress_by_state": avg_progress_by_state,
        "financial_overview_by_state": financial_overview_by_state
    }


@app.get("/api/analytics/state/{state_name}/projects")
def state_projects(state_name: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_verified_user)):
    norm_query = normalize_state_name(state_name).casefold()
    all_projects = [p for p in db.query(Project).all() if check_project_access(current_user, p.state, p.agency, p.ministry, p.sector)]

    matched_projects = []
    p_codes = set()
    for p in all_projects:
        extracted = _extract_states_for_project(p.state)
        states_for_p = [normalize_state_name(s).casefold() for s in extracted]
        if norm_query in states_for_p or norm_query in (p.state or "").casefold():
            matched_projects.append(p)
            p_codes.add(p.project_code)

    all_snapshots = db.query(ProjectSnapshot).filter(ProjectSnapshot.project_code.in_(p_codes)).order_by(ProjectSnapshot.id.asc()).all() if p_codes else []
    snap_map = {}
    for s in all_snapshots:
        snap_map[s.project_code] = s

    all_risks = db.query(RiskAssessment).filter(RiskAssessment.project_code.in_(p_codes)).order_by(RiskAssessment.id.asc()).all() if p_codes else []
    risk_map = {}
    for r in all_risks:
        risk_map[r.project_code] = r

    result = []
    for p in matched_projects:
        s = snap_map.get(p.project_code)
        r = risk_map.get(p.project_code)
        result.append({
            "project_code": p.project_code,
            "project_name": p.project_name,
            "agency": p.agency,
            "sector": p.sector,
            "ministry": p.ministry,
            "state": p.state,
            "original_cost": p.original_cost,
            "revised_cost": s.revised_cost if s and s.revised_cost else p.original_cost,
            "cumulative_expenditure": s.cumulative_expenditure if s else 0.0,
            "physical_progress": s.physical_progress if s else 0.0,
            "cost_overrun_pct": s.cost_overrun_pct if s else 0.0,
            "time_overrun_months": s.time_overrun_months if s else 0.0,
            "project_status": s.project_status if s and s.project_status else "Ongoing",
            "report_month": s.report_month if s else None,
            "risk_score": r.risk_score if r else 0,
            "overall_risk": r.overall_risk if r else "LOW",
        })
    return {"state_name": state_name, "total": len(result), "projects": result}


@app.post("/api/ai/chat")
def chat_with_ai(request: ChatRequest, current_user: User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
    from backend.services.ai_service import answer_user_query
    message = request.message or request.query
    if not message:
        raise HTTPException(status_code=422, detail="message is required")
    try:
        return answer_user_query(message, current_user, db, request.project_code, request.state, request.ministry)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

@app.get("/api/reports/download")
def download_reports(q: Optional[str] = None, state: Optional[str] = None, sector: Optional[str] = None, ministry: Optional[str] = None, agency: Optional[str] = None, risk: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_verified_user)):
    from backend.services.reports import generate_projects_csv
    from fastapi.responses import PlainTextResponse
    
    projects = _project_query(db, current_user, q, state, sector, ministry, agency, risk, None)
    csv_data = generate_projects_csv(db, projects)
    
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=infraguard_report.csv"}
    )
