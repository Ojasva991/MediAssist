"""
Data models for the Symptom Analysis History feature.

A history entry is a saved snapshot of one past /analyze call for a
given user - the exact request they made and the exact response they
got back, plus when it happened.
"""

from datetime import datetime

from pydantic import BaseModel, Field

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

    feedback: bool | None = Field(
        default=None,
        description=(
            "Thumbs-up (true) / thumbs-down (false) feedback already given "
            "on this analysis, or null if none has been given yet."
        ),
    )

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
                "feedback": None,
            }
        }
    }


class FeedbackRequest(BaseModel):
    """Body for POST /history/{user_id}/{history_id}/feedback."""

    is_helpful: bool = Field(
        ..., description="True for thumbs-up, False for thumbs-down."
    )


class TrendFinding(BaseModel):
    """
    One recurring-symptom pattern detected across a user's recent
    history (see app/insights/trends.py). Informational only - never
    a diagnosis, just "you've mentioned X repeatedly lately."
    """

    keyword: str = Field(..., description="The recurring symptom keyword.")
    occurrences: int = Field(
        ..., description="Number of separate analyses this keyword appeared in."
    )
    window_days: int = Field(
        ..., description="The lookback window (in days) this count covers."
    )
