"""
Data models for the AI Symptom Analysis feature (/analyze endpoint).

These models define exactly what shape of data comes in and goes out.
FastAPI uses them to auto-validate requests and auto-generate the
/docs page - so a bad request (e.g. negative age, empty symptoms)
gets rejected with a clear 422 error before it ever reaches our code,
let alone the Gemini API.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    """
    Allowed severity levels. Using an Enum (not a free-text string)
    means the AI's output - and our own code - can never accidentally
    produce a typo'd or invalid severity value.
    """

    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    EMERGENCY = "EMERGENCY"


class SymptomAnalysisRequest(BaseModel):
    """What the frontend sends us to request a triage analysis."""

    age: int = Field(..., ge=0, le=120, description="Patient age in years (0-120)")
    gender: str = Field(..., min_length=1, max_length=30)
    symptoms: str = Field(..., min_length=3, max_length=1000)
    duration: str = Field(..., min_length=1, max_length=100)
    existing_conditions: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional pre-existing conditions, e.g. diabetes, asthma",
    )

    @field_validator("symptoms")
    @classmethod
    def symptoms_not_blank(cls, v: str) -> str:
        # min_length catches empty strings, but not "   " (whitespace only).
        if not v.strip():
            raise ValueError("symptoms cannot be blank")
        return v.strip()

    @field_validator("gender")
    @classmethod
    def gender_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("gender cannot be blank")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "age": 28,
                "gender": "Male",
                "symptoms": "Chest pain and sweating",
                "duration": "30 minutes",
                "existing_conditions": None,
            }
        }
    }


class SymptomAnalysisResponse(BaseModel):
    """What we send back to the frontend after analysis."""

    possible_conditions: list[str] = Field(
        ..., description="Possible (not confirmed) conditions - never a diagnosis"
    )
    severity: Severity
    recommended_action: str = Field(..., min_length=1)
    sos_recommended: bool
    disclaimer: str = Field(
        default="This is not a medical diagnosis. Consult a healthcare professional.",
        description="Always present. Never omit this field.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "possible_conditions": ["Heart-related emergency"],
                "severity": "EMERGENCY",
                "recommended_action": "Seek emergency medical attention immediately.",
                "sos_recommended": True,
                "disclaimer": "This is not a medical diagnosis.",
            }
        }
    }
