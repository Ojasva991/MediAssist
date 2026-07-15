"""
Fallback triage logic - used ONLY when Gemini is unavailable.

This is NOT a diagnosis engine and NOT a replacement for the AI. Its
only job is to prevent the app from crashing or leaving the user with
nothing when Gemini fails, by doing a conservative, transparent safety
check: escalate to EMERGENCY if obvious red-flag keywords are present,
otherwise clearly say analysis is unavailable.

This keeps the "never diagnose" project rule intact - the fallback
never suggests a condition, it only decides whether to escalate
urgency while the AI is down. When in doubt, it always prefers to
say "we couldn't analyze this" over guessing.
"""

import logging

from app.models.symptom import Severity, SymptomAnalysisResponse

logger = logging.getLogger(__name__)

# Deliberately short and unambiguous - only signs where waiting for a
# retry could be dangerous. Not meant to be exhaustive. Simple substring
# matching on purpose: this is a safety net, not an NLP system, and
# false positives (over-escalating) are the safe failure direction here.
_EMERGENCY_RED_FLAGS = [
    "chest pain",
    "can't breathe",
    "cannot breathe",
    "difficulty breathing",
    "shortness of breath",
    "not breathing",
    "unconscious",
    "unresponsive",
    "severe bleeding",
    "uncontrolled bleeding",
    "stroke",
    "slurred speech",
    "face drooping",
    "sudden numbness",
    "severe allergic reaction",
    "anaphylaxis",
    "suicidal",
    "overdose",
    "seizure",
]

FALLBACK_DISCLAIMER = (
    "The AI triage service was unavailable, so this is a basic safety "
    "fallback response, NOT a full analysis. This is not a medical "
    "diagnosis. Please consult a healthcare professional."
)


def _contains_red_flag(symptoms: str) -> bool:
    text = symptoms.lower()
    return any(flag in text for flag in _EMERGENCY_RED_FLAGS)


def build_fallback_response(symptoms: str) -> SymptomAnalysisResponse:
    """
    Build a conservative, transparent response when Gemini could not be
    reached or returned unusable output.

    `possible_conditions` is always left empty here - deliberately, so
    the frontend/reviewer can visually tell a fallback response apart
    from a real AI analysis (which always lists at least one condition).
    """
    if _contains_red_flag(symptoms):
        logger.warning(
            "Fallback triggered WITH red-flag keywords present: %s", symptoms[:200]
        )
        return SymptomAnalysisResponse(
            possible_conditions=[],
            severity=Severity.EMERGENCY,
            recommended_action=(
                "AI analysis is currently unavailable, but your description "
                "mentions symptoms that can be serious. To be safe, seek "
                "emergency medical attention or contact emergency services "
                "immediately."
            ),
            sos_recommended=True,
            disclaimer=FALLBACK_DISCLAIMER,
        )

    logger.warning("Fallback triggered, no red flags detected: %s", symptoms[:200])
    return SymptomAnalysisResponse(
        possible_conditions=[],
        severity=Severity.MODERATE,
        recommended_action=(
            "AI analysis is temporarily unavailable, so your symptoms "
            "could not be assessed automatically. Please consult a "
            "healthcare professional, or contact emergency services if "
            "your symptoms are severe or worsen."
        ),
        sos_recommended=False,
        disclaimer=FALLBACK_DISCLAIMER,
    )
