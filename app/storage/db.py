"""
Database engine and session setup for Postgres storage.

Replaces the previous Google Sheets storage. Uses SQLAlchemy so the
rest of the app doesn't need to know it's Postgres specifically - any
Postgres-compatible connection string works (Supabase, Neon, Render
Postgres, etc.)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# pool_pre_ping avoids "server closed the connection unexpectedly" errors
# after the free-tier DB has been idle for a while (same class of problem
# as Render's cold starts).
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_session():
    """Return a new DB session. Caller is responsible for closing it."""
    return SessionLocal()
