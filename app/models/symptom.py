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
    llm_severity: Optional[Severity] = Field(
        default=None,
        description=(
            "The AI's own original severity assessment, BEFORE reconciliation "
            "with the rule engine. None for fallback responses (no LLM call "
            "was made). When this differs from the final `severity` above, "
            "the rule engine raised the urgency level - a signal worth "
            "surfacing to the user rather than hiding, since it means the "
            "two systems disagreed."
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
    history_id: Optional[int] = Field(
        default=None,
        description=(
            "ID of the saved history entry for this analysis, set only "
            "when the caller was logged in (so it could be saved at all - "
            "see app/routes/analyze.py). Used to submit feedback via "
            "POST /history/{user_id}/{history_id}/feedback. None for "
            "anonymous callers."
        ),
    )
    visual_observation: Optional[str] = Field(
        default=None,
        description=(
            "Plain-language description of what's visible in an uploaded "
            "image, from POST /analyze/image only - lets the caller "
            "confirm the AI looked at the right thing. None for text-only "
            "analyses (POST /analyze)."
        ),
    )
    image_rejected: bool = Field(
        default=False,
        description=(
            "True only for POST /analyze/image when the uploaded image "
            "looked like a medical scan/document (X-ray, CT, MRI, lab "
            "report) rather than a photo of a visible symptom - those are "
            "deliberately not interpreted (see app/ai/prompts.py's "
            "IMAGE_SYSTEM_PROMPT). Always False for POST /analyze."
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
