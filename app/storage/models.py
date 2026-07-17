"""
SQLAlchemy table definitions for Postgres-backed storage.

Mirrors the exact columns the old Google Sheets tabs used, so no data
shape changes for the rest of the app - just where it's stored.
"""

from sqlalchemy import Column, String, Integer

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
