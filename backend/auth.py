"""
Authentication, Password Hashing, JWT Tokens, and Role-Based Authorization for InfraGuard-AI.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from backend.database import get_db
from backend.models import User, Role, AuditLog

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY must be configured in the server environment")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")
    return user


def get_current_verified_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending authority verification by Super Admin"
        )
    return current_user


def require_roles(allowed_roles: List[str]):
    """Decorator dependency to enforce specific roles."""
    def role_checker(current_user: User = Depends(get_current_user)):
        user_role = _canonical_role(current_user)
        allowed = {_canonical_role_name(role) for role in allowed_roles}
        if user_role not in allowed and user_role != "SUPER_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of {allowed_roles}"
            )
        return current_user
    return role_checker


def check_project_access(user: User, project_state: Optional[str], project_agency: Optional[str], project_ministry: Optional[str]) -> bool:
    """Check if the user has access to this project based on organization/state scope."""
    user_role = _canonical_role(user)
    project_state = (project_state or "").casefold()
    project_agency = (project_agency or "").casefold()
    project_ministry = (project_ministry or "").casefold()
    user_state = (user.state_region or "").casefold()
    user_agency = (user.agency or "").casefold()
    user_organization = (user.organization or "").casefold()
    user_department = (user.department or "").casefold()

    if user_role in {"SUPER_ADMIN", "MOSPI_IPMD_ADMIN"}:
        return True

    if user_role == "MINISTRY_AUTHORITY":
        return bool(
            (user_organization and project_ministry and user_organization in project_ministry)
            or (user_department and project_ministry and user_department in project_ministry)
        )

    if user_role == "DEPARTMENT_AUTHORITY":
        return bool(
            (user_department and project_ministry and user_department in project_ministry)
            or (user_organization and project_ministry and user_organization in project_ministry)
        )

    if user_role == "AGENCY_AUTHORITY":
        return bool(user_agency and project_agency and user_agency in project_agency)

    if user_role == "STATE_AUTHORITY":
        return bool(user_state and user_state not in {"all", "all india", "national"} and user_state in project_state)

    if user_role == "VIEWER_AUDITOR":
        if user_state in {"all", "all india", "national"}:
            return True
        if not user_state and not user_agency:
            return False
        return bool((user_state and user_state in project_state) or (user_agency and user_agency in project_agency))

    return False


def _canonical_role_name(role_name: str) -> str:
    normalized = role_name.strip().casefold().replace("/", "_").replace(" ", "_")
    aliases = {
        "super_admin": "SUPER_ADMIN",
        "mospi_ipmd_admin": "MOSPI_IPMD_ADMIN",
        "ministry_authority": "MINISTRY_AUTHORITY",
        "department_authority": "DEPARTMENT_AUTHORITY",
        "state_authority": "STATE_AUTHORITY",
        "agency_project_authority": "AGENCY_AUTHORITY",
        "agency_authority": "AGENCY_AUTHORITY",
        "viewer_auditor": "VIEWER_AUDITOR",
    }
    return aliases.get(normalized, normalized.upper())


def _canonical_role(user: User) -> str:
    role_name = user.role.name if user.role else user.authority_type
    return _canonical_role_name(role_name)


def log_audit_action(db: Session, user: Optional[User], action: str, details: str, ip_address: Optional[str] = None):
    """Log user or system actions to the audit trail."""
    try:
        log_entry = AuditLog(
            user_id=user.id if user else None,
            user_email=user.email if user else "SYSTEM",
            action=action,
            details=details,
            ip_address=ip_address,
            timestamp=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"Error recording audit log: {e}")
