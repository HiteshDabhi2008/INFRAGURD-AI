import json
import math
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.auth import check_project_access, get_current_user, get_current_verified_user, log_audit_action, verify_password, create_access_token
from backend.database import Base, engine, get_db
from backend.models import Project, ProjectFeature, ProjectSnapshot, RiskAssessment, Role, User
from backend.services.ml_service import build_project_model_dict, run_full_risk_assessment
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
    revised_cost: Optional[float] = Field(default=None, ge=0)
    revised_completion_date: Optional[str] = None


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
    if not check_project_access(user, project.state, project.agency, project.ministry):
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


def _summary(db: Session, project: Project, user: User) -> Dict[str, Any]:
    _authorized(user, project)
    snapshot = _latest_snapshot(db, project.project_code)
    risk = _latest_risk(db, project.project_code)
    return {
        "project_code": project.project_code,
        "project_name": project.project_name,
        "agency": project.agency,
        "state": project.state,
        "sector": project.sector,
        "ministry": project.ministry,
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
        "history": [{
            "id": item.id,
            "report_month": item.report_month,
            "revised_cost": item.revised_cost,
            "revised_completion_date": item.revised_completion_date,
            "cumulative_expenditure": item.cumulative_expenditure,
            "physical_progress": item.physical_progress,
            "cost_overrun_pct": item.cost_overrun_pct,
            "time_overrun_months": item.time_overrun_months,
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

@app.post("/api/auth/change-password")
def change_password(request: ChangePasswordRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from backend.auth import verify_password, get_password_hash
    if not verify_password(request.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    current_user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    log_audit_action(db, current_user, "PASSWORD_CHANGED", "User changed their password.")
    return {"message": "Password changed successfully"}

@app.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "full_name": current_user.full_name,
            "authority_type": current_user.authority_type, "organization": current_user.organization,
            "state_region": current_user.state_region, "agency": current_user.agency}


def _project_query(db: Session, user: User, q: Optional[str], state: Optional[str], sector: Optional[str], ministry: Optional[str], agency: Optional[str], risk: Optional[str], report_month: Optional[str]):
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
    output = []
    for project in projects:
        if not check_project_access(user, project.state, project.agency, project.ministry):
            continue
        item = _summary(db, project, user)
        if risk and (item.get("overall_risk") or "").upper() != risk.upper():
            continue
        if report_month:
            month_exists = db.query(ProjectSnapshot.id).filter(ProjectSnapshot.project_code == project.project_code, ProjectSnapshot.report_month.ilike(f"%{report_month}%")).first()
            if not month_exists:
                continue
        output.append(item)
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
    return _detail(db, project, current_user)


@app.get("/api/projects/{project_code}/history")
def get_project_history(project_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_verified_user)):
    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _authorized(current_user, project)
    history = db.query(ProjectSnapshot).filter(ProjectSnapshot.project_code == project_code).order_by(ProjectSnapshot.created_at.asc(), ProjectSnapshot.id.asc()).all()
    return [{"id": item.id, "report_month": item.report_month, "revised_cost": item.revised_cost, "revised_completion_date": item.revised_completion_date, "cumulative_expenditure": item.cumulative_expenditure, "physical_progress": item.physical_progress, "cost_overrun_pct": item.cost_overrun_pct, "time_overrun_months": item.time_overrun_months} for item in history]


def _analytics(db: Session, user: User, field: str) -> List[Dict[str, Any]]:
    projects = [p for p in db.query(Project).all() if check_project_access(user, p.state, p.agency, p.ministry)]
    groups = defaultdict(list)
    for project in projects:
        groups[getattr(project, field) or "Unknown"].append(_summary(db, project, user))
    return [{"name": name, "project_count": len(items), "original_cost": sum(x.get("original_cost") or 0 for x in items), "revised_cost": sum(x.get("revised_cost") or 0 for x in items), "expenditure": sum(x.get("cumulative_expenditure") or 0 for x in items), "average_progress": round(sum(x.get("physical_progress") or 0 for x in items) / len(items), 2) if items else 0, "high_risk_count": sum(1 for x in items if x.get("overall_risk") == "HIGH"), "critical_count": sum(1 for x in items if x.get("overall_risk") == "CRITICAL")} for name, items in sorted(groups.items())]


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


@app.post("/api/projects/{project_code}/monthly-update")
def monthly_update(project_code: str, request: MonthlyUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_verified_user)):
    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _authorized(current_user, project)
    existing = db.query(ProjectSnapshot).filter(ProjectSnapshot.project_code == project_code, ProjectSnapshot.report_month == request.report_month).first()
    if existing:
        raise HTTPException(status_code=409, detail="A snapshot for this reporting month already exists")
    snapshot = ProjectSnapshot(project_code=project_code, report_month=request.report_month, physical_progress=request.physical_progress, cumulative_expenditure=request.cumulative_expenditure, revised_cost=request.revised_cost, revised_completion_date=request.revised_completion_date)
    db.add(snapshot)
    log_audit_action(db, current_user, "MONTHLY_UPDATE_SUBMITTED", f"Project {project_code}, month {request.report_month}")
    db.commit()
    db.refresh(snapshot)
    return {"id": snapshot.id, "project_code": project_code, "report_month": snapshot.report_month}


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
