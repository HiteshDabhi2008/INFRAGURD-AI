"""
Pydantic schemas for request/response serialization.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ── AUTH & USER SCHEMAS ──────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    organization: Optional[str] = None
    department: Optional[str] = None
    authority_type: str = "Viewer / Auditor"
    state_region: Optional[str] = None
    agency: Optional[str] = None
    designation: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class TokenData(BaseModel):
    email: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    organization: Optional[str] = None
    department: Optional[str] = None
    authority_type: str
    state_region: Optional[str] = None
    agency: Optional[str] = None
    designation: Optional[str] = None
    is_active: bool
    is_verified: bool
    role: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserVerifyUpdate(BaseModel):
    is_verified: bool
    role_name: Optional[str] = None


# ── PROJECT SCHEMAS ──────────────────────────────────────────────

class ProjectSnapshotOut(BaseModel):
    id: int
    report_month: str
    start_date: Optional[str] = None
    revised_cost: Optional[float] = None
    revised_completion_date: Optional[str] = None
    cumulative_expenditure: Optional[float] = None
    physical_progress: Optional[float] = None
    cost_overrun_pct: Optional[float] = None
    time_overrun_months: Optional[float] = None

    class Config:
        from_attributes = True


class ProjectSummary(BaseModel):
    project_code: str
    project_name: str
    agency: Optional[str] = None
    state: Optional[str] = None
    sector: Optional[str] = None
    ministry: Optional[str] = None
    original_cost: Optional[float] = None
    revised_cost: Optional[float] = None
    cumulative_expenditure: Optional[float] = None
    physical_progress: Optional[float] = None
    overall_risk: Optional[str] = "LOW"
    risk_score: Optional[int] = 0

    class Config:
        from_attributes = True


class ProjectDetail(BaseModel):
    project_code: str
    project_name: str
    agency: Optional[str] = None
    state: Optional[str] = None
    sector: Optional[str] = None
    ministry: Optional[str] = None
    approval_date: Optional[str] = None
    original_cost: Optional[float] = None
    original_completion_date: Optional[str] = None
    
    # Latest snapshot metrics
    revised_cost: Optional[float] = None
    revised_completion_date: Optional[str] = None
    cumulative_expenditure: Optional[float] = None
    physical_progress: Optional[float] = None
    expenditure_percent: Optional[float] = None
    progress_gap: Optional[float] = None
    cost_change: Optional[float] = None
    cost_change_percent: Optional[float] = None
    project_age_days: Optional[int] = None
    original_duration_days: Optional[int] = None
    revised_duration_days: Optional[int] = None

    # Risk metrics
    overall_risk: Optional[str] = "LOW"
    risk_score: Optional[int] = 0
    warnings: List[str] = []
    explanation: Optional[str] = None

    # Sub-model predictions
    cost_model_output: Optional[Dict[str, Any]] = None
    time_model_output: Optional[Dict[str, Any]] = None

    # History
    history: List[ProjectSnapshotOut] = []

    class Config:
        from_attributes = True


class PaginatedProjects(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
    projects: List[ProjectSummary]


# ── ANALYTICS SCHEMAS ────────────────────────────────────────────

class KPISummary(BaseModel):
    total_projects: int
    ongoing_projects: int
    high_risk_projects: int
    critical_risk_projects: int
    original_cost_total: float
    revised_cost_total: float
    total_expenditure: float
    average_physical_progress: float
    cost_overrun_count: int
    time_overrun_count: int


class ChartDataPoint(BaseModel):
    name: str
    value: float
    count: Optional[int] = None


class ScatterDataPoint(BaseModel):
    project_code: str
    project_name: str
    expenditure_percent: float
    physical_progress: float
    cost_cr: float
    risk_level: str


# ── AI & CHAT SCHEMAS ────────────────────────────────────────────

class AIChatRequest(BaseModel):
    message: str
    project_code: Optional[str] = None
    state: Optional[str] = None
    ministry: Optional[str] = None


class AIChatResponse(BaseModel):
    answer: str
    context_used: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── REPORT SCHEMAS ───────────────────────────────────────────────

class ReportRequest(BaseModel):
    report_type: str = "Portfolio Report" # Portfolio, Ministry, Department, Project, Risk
    ministry: Optional[str] = None
    state: Optional[str] = None
    risk_level: Optional[str] = None
    project_code: Optional[str] = None


class ReportResponse(BaseModel):
    title: str
    generated_at: str
    generated_by: str
    summary: Dict[str, Any]
    items: List[Dict[str, Any]]


# ── AUDIT LOG SCHEMAS ────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: int
    user_email: Optional[str] = None
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True
