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

    # age/gender are optional here (unlike in the Health Passport, where
    # they're required): a logged-in caller with a saved passport doesn't
    # need to send them at all - app/routes/analyze.py fills them in from
    # the passport before running the analysis. They're still required in
    # practice for anonymous callers (or logged-in callers with no saved
    # passport yet) - that's enforced in the route, not here, since it
    # depends on who's calling, not on the shape of the request alone.
    age: Optional[int] = Field(
        default=None,
        ge=0,
        le=120,
        description="Patient age (0-120). Optional if saved in your Health Passport.",
    )
    gender: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=30,
        description="Optional if saved in your Health Passport.",
    )
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
    def gender_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("gender cannot be blank")
        return v.strip() if v else v

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


class RuleEngineFindings(BaseModel):
    """
    Explainability layer: what the deterministic rule engine
    (app/rules/engine.py) found, independent of the LLM. Included so the
    frontend/reviewer can see WHY a severity floor was set, not just
    trust the LLM's paragraph. `severity` here is the rule engine's OWN
    assessment - it may be lower than the final `severity` on the
    response if the LLM assessed something more urgent.
    """

    severity: Severity
    fired_rules: list[str] = Field(
        default_factory=list,
        description="Human-readable reasons the rule engine set this severity floor.",
    )


class GuidanceReference(BaseModel):
    """
    One piece of first-aid/triage guidance (see app/rag/corpus.py) that
    was retrieved as context for this analysis - included so the caller
    can see what grounded the AI's recommendation, not just trust the
    generated paragraph blindly.
    """

    source: str
    topic: str


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
    rule_engine: Optional[RuleEngineFindings] = Field(
        default=None,
        description=(
            "Deterministic rule-engine findings, included for transparency. "
            "The final `severity` above is always at least as urgent as "
            "rule_engine.severity - the rule engine can only raise urgency, "
            "never lower what the LLM assessed."
        ),
    )
    retrieved_guidance: list[GuidanceReference] = Field(
        default_factory=list,
        description=(
            "First-aid/triage guidance entries retrieved as grounding "
            "context for this analysis (see app/rag/). Empty if nothing in "
            "the corpus was relevant enough to the described symptoms."
        ),
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
