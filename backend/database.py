"""
database.py — Database connection layer (cloud-abstraction point).

The SAME ORM models run against:
  * local mode  : SQLite file (zero setup)
  * cloud mode  : Supabase Postgres (free tier, managed)

Only DATABASE_URL changes. This demonstrates "cloud database" without
vendor lock-in — a key cloud-architecture skill.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import settings

# SQLite needs a special flag when used with FastAPI threads.
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,   # survive transient cloud-DB disconnects
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Base class for every ORM model in the system."""


def get_db():
    """FastAPI dependency: one DB session per request, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
