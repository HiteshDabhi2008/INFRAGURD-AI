"""
SQLAlchemy database models for InfraGuard-AI platform.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from backend.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    organization = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    authority_type = Column(String(100), nullable=False, default="Viewer / Auditor")
    state_region = Column(String(100), nullable=True)
    agency = Column(String(255), nullable=True)
    designation = Column(String(255), nullable=True)
    government_id = Column(String(100), unique=True, index=True, nullable=True)
    mobile_number = Column(String(50), nullable=True)
    sector = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = relationship("Role", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    project_code = Column(String(100), primary_key=True, index=True)
    project_name = Column(Text, nullable=False)
    agency = Column(String(255), index=True, nullable=True)
    state = Column(String(255), index=True, nullable=True)
    sector = Column(String(255), index=True, nullable=True)
    ministry = Column(String(255), index=True, nullable=True)
    department = Column(String(255), index=True, nullable=True)
    district = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True, default="Ongoing")
    approval_date = Column(String(50), nullable=True)
    original_cost = Column(Float, nullable=True)
    original_completion_date = Column(String(50), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    snapshots = relationship("ProjectSnapshot", back_populates="project", cascade="all, delete-orphan")
    features = relationship("ProjectFeature", back_populates="project", cascade="all, delete-orphan")
    predictions = relationship("MLPrediction", back_populates="project", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="project", cascade="all, delete-orphan")


class ProjectSnapshot(Base):
    __tablename__ = "project_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    project_code = Column(String(100), ForeignKey("projects.project_code"), index=True, nullable=False)
    report_month = Column(String(50), index=True, nullable=False)  # April 2026, May 2026, etc.
    start_date = Column(String(50), nullable=True)
    revised_cost = Column(Float, nullable=True)
    revised_completion_date = Column(String(50), nullable=True)
    cumulative_expenditure = Column(Float, nullable=True)
    physical_progress = Column(Float, nullable=True)
    cost_overrun_pct = Column(Float, nullable=True)
    time_overrun_months = Column(Float, nullable=True)
    project_status = Column(String(50), nullable=True, default="Ongoing")
    remarks = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="snapshots")

    __table_args__ = (
        Index("ix_project_month", "project_code", "report_month", unique=True),
    )


class ProjectFeature(Base):
    __tablename__ = "project_features"

    id = Column(Integer, primary_key=True, index=True)
    project_code = Column(String(100), ForeignKey("projects.project_code"), index=True, nullable=False)
    report_month = Column(String(50), nullable=False)
    project_age_days = Column(Integer, nullable=True)
    original_duration_days = Column(Integer, nullable=True)
    revised_duration_days = Column(Integer, nullable=True)
    expenditure_percent = Column(Float, nullable=True)
    progress_gap = Column(Float, nullable=True)
    cost_change = Column(Float, nullable=True)
    cost_change_percent = Column(Float, nullable=True)
    project_size_category = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="features")


class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    id = Column(Integer, primary_key=True, index=True)
    project_code = Column(String(100), ForeignKey("projects.project_code"), index=True, nullable=False)
    report_month = Column(String(50), nullable=False)
    cost_risk_level = Column(String(20), nullable=True)      # LOW, MEDIUM, HIGH
    cost_overrun_prob = Column(Float, nullable=True)
    predicted_cost_overrun = Column(Float, nullable=True)
    time_risk_level = Column(String(20), nullable=True)      # LOW, MEDIUM, HIGH
    time_overrun_prob = Column(Float, nullable=True)
    predicted_time_months = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="predictions")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    project_code = Column(String(100), ForeignKey("projects.project_code"), index=True, nullable=False)
    report_month = Column(String(50), nullable=False)
    risk_score = Column(Integer, nullable=False)
    overall_risk = Column(String(50), index=True, nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    warnings_json = Column(Text, nullable=True)                   # JSON list of early warnings
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="risk_assessments")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(100), index=True, nullable=False) # LOGIN, LOGOUT, VIEW_PROJECT, UPLOAD_DATA, etc.
    details = Column(Text, nullable=True)
    ip_address = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    status = Column(String(50), default="PROCESSING") # PROCESSING, SUCCESS, FAILED
    row_count = Column(Integer, default=0)
    error_log = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
