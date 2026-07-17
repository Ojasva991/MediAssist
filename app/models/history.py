"""
Data models for the Symptom Analysis History feature.

A history entry is a saved snapshot of one past /analyze call for a
given user - the exact request they made and the exact response they
got back, plus when it happened.
"""

from datetime import datetime

from pydantic import BaseModel

from app.models.symptom import Severity


class AnalysisHistoryItem(BaseModel):
    """One past symptom analysis, as returned by GET /history/{user_id}."""

    id: int
    created_at: datetime

    # What the user reported
    age: int
    gender: str
    symptoms: str
    duration: str
    existing_conditions: str | None = None

    # What the AI returned
    possible_conditions: list[str]
    severity: Severity
    recommended_action: str
    sos_recommended: bool
    disclaimer: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 12,
                "created_at": "2026-07-18T10:15:00Z",
                "age": 28,
                "gender": "Male",
                "symptoms": "Chest pain and sweating",
                "duration": "30 minutes",
                "existing_conditions": None,
                "possible_conditions": ["Heart-related emergency"],
                "severity": "EMERGENCY",
                "recommended_action": "Seek emergency medical attention immediately.",
                "sos_recommended": True,
                "disclaimer": "This is not a medical diagnosis.",
            }
        }
    }
