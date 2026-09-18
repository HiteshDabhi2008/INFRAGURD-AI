"""
Database configuration and session management for InfraGuard-AI.
Supports PostgreSQL / Supabase via DATABASE_URL or defaults to local SQLite.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DB_PATH = os.path.join(BASE_DIR, "data", "processed", "infraguard.db")
    DATABASE_URL = f"sqlite:///{DB_PATH}"

# Setup SQLite connect_args if needed
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI dependency for DB session lifecycle."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
