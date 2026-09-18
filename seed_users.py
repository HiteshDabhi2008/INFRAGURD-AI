import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.database import SessionLocal, engine, Base
from backend.models import User, Role
from backend.auth import get_password_hash

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

def seed_db():
    admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "").strip().casefold()
    admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "")
    if not admin_email or not admin_password:
        raise RuntimeError("DEFAULT_ADMIN_EMAIL and DEFAULT_ADMIN_PASSWORD must be configured")
    if len(admin_password) < 12:
        raise RuntimeError("DEFAULT_ADMIN_PASSWORD must contain at least 12 characters")

    db = SessionLocal()
    try:
        # Create roles
        roles_data = [
            "Super Admin",
            "MoSPI/IPMD Admin",
            "Ministry Authority",
            "State Authority",
            "Agency / Project Authority",
            "Viewer / Auditor"
        ]
        
        roles = {}
        for r_name in roles_data:
            role = db.query(Role).filter(Role.name == r_name).first()
            if not role:
                role = Role(name=r_name)
                db.add(role)
                db.commit()
                db.refresh(role)
            roles[r_name] = role
        
        # Create or update only the environment-configured development admin.
        user = db.query(User).filter(User.email == admin_email).first()
        if not user:
            user = User(
                email=admin_email,
                full_name="InfraGuard Administrator",
                hashed_password=get_password_hash(admin_password),
                authority_type="Super Admin",
                organization="MoSPI/IPMD",
                department="Infrastructure Monitoring",
                agency="IPMD",
                role_id=roles["Super Admin"].id,
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            db.commit()
            print(f"Created default admin: {user.email}")
        else:
            user.role_id = roles["Super Admin"].id
            user.authority_type = "Super Admin"
            user.is_active = True
            user.is_verified = True
            db.commit()
            print(f"Default admin already exists: {user.email}")
                
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
    print("Database seeding completed.")
