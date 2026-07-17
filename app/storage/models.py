"""
SQLAlchemy table definitions for Postgres-backed storage.

Mirrors the exact columns the old Google Sheets tabs used, so no data
shape changes for the rest of the app - just where it's stored.
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, func

from app.storage.db import Base


class UserRecord(Base):
    __tablename__ = "users"

    user_id = Column(String(24), primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)


class PassportRecord(Base):
    __tablename__ = "passports"

    user_id = Column(String(24), primary_key=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    blood_group = Column(String(10), nullable=False, default="UNKNOWN")
    allergies = Column(String(500), nullable=True)
    medications = Column(String(500), nullable=True)
    chronic_diseases = Column(String(500), nullable=True)
    emergency_contact_name = Column(String(100), nullable=False)
    emergency_contact_phone = Column(String(20), nullable=False)


class AnalysisHistoryRecord(Base):
    """
    One saved symptom analysis. Only created when the caller was
    logged in at the time of the /analyze request (see
    app.auth.dependencies.get_optional_user_id and app/routes/analyze.py) -
    logged-out analyses are never saved anywhere.
    """

    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(24), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # What the user reported
    age = Column(Integer, nullable=False)
    gender = Column(String(30), nullable=False)
    symptoms = Column(String(1000), nullable=False)
    duration = Column(String(100), nullable=False)
    existing_conditions = Column(String(500), nullable=True)

    # What the AI returned
    possible_conditions = Column(JSON, nullable=False)  # list[str]
    severity = Column(String(20), nullable=False)
    recommended_action = Column(String(1000), nullable=False)
    sos_recommended = Column(Boolean, nullable=False)
    disclaimer = Column(String(1000), nullable=False)
