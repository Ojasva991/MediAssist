"""
Data model for the Health Passport feature.

The Health Passport stores essential medical info for fast retrieval
during an emergency. This module only defines the *shape* of that data -
storage (Milestone 5, in-memory for the hackathon) lives elsewhere.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class BloodGroup(str, Enum):
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"
    UNKNOWN = "UNKNOWN"


class HealthPassport(BaseModel):
    """A user's essential medical information."""

    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=0, le=120)
    blood_group: BloodGroup = BloodGroup.UNKNOWN
    allergies: Optional[str] = Field(
        default=None, max_length=500, description="Comma-separated or free text"
    )
    medications: Optional[str] = Field(
        default=None, max_length=500, description="Current medications"
    )
    chronic_diseases: Optional[str] = Field(
        default=None, max_length=500, description="e.g. diabetes, hypertension"
    )
    emergency_contact_name: str = Field(..., min_length=1, max_length=100)
    emergency_contact_phone: str = Field(..., min_length=5, max_length=20)

    @field_validator("name", "emergency_contact_name")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("This field cannot be blank")
        return v.strip()

    @field_validator("emergency_contact_phone")
    @classmethod
    def phone_looks_valid(cls, v: str) -> str:
        # Loose check on purpose - hackathon scope, not full phone validation.
        # Just guards against obviously junk input like "abc".
        digits = [c for c in v if c.isdigit()]
        if len(digits) < 7:
            raise ValueError("emergency_contact_phone must contain at least 7 digits")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Priya Sharma",
                "age": 24,
                "blood_group": "O+",
                "allergies": "Penicillin",
                "medications": "None",
                "chronic_diseases": "Asthma",
                "emergency_contact_name": "Raj Sharma",
                "emergency_contact_phone": "+91-9876543210",
            }
        }
    }
