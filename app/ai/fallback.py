"""
Fallback triage logic - used ONLY when Gemini is unavailable.

This is NOT a diagnosis engine and NOT a replacement for the AI. Its
only job is to prevent the app from crashing or leaving the user with
nothing when Gemini fails, by falling back to the deterministic rule
engine's severity floor (see app/rules/engine.py) and being transparent
about what happened.

This keeps the "never diagnose" project rule intact - the fallback
never suggests a condition, it only reports whatever severity the rule
engine assigned while the AI is down. When in doubt, it always prefers
to say "we couldn't analyze this" over guessing.
"""

import logging

from app.models.symptom import (
    RuleEngineFindings,
    Severity,
    SymptomAnalysisRequest,
    SymptomAnalysisResponse,
)
from app.rules.engine import evaluate as evaluate_rules, more_urgent

logger = logging.getLogger(__name__)

FALLBACK_DISCLAIMER = (
    "The AI triage service was unavailable, so this is a basic safety "
    "fallback response, NOT a full analysis. This is not a medical "
    "diagnosis. Please consult a healthcare professional."
)


def build_fallback_response(request: SymptomAnalysisRequest) -> SymptomAnalysisResponse:
    """
    Build a conservative, transparent response when Gemini could not be
    reached or returned unusable output.

    `possible_conditions` is always left empty here - deliberately, so
    the frontend/reviewer can visually tell a fallback response apart
    from a real AI analysis (which always lists at least one condition).
    """
    rule_result = evaluate_rules(request)

    if rule_result.severity == Severity.EMERGENCY:
        logger.warning(
            "Fallback triggered WITH rule-engine EMERGENCY match: %s",
            request.symptoms[:200],
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
            rule_engine=RuleEngineFindings(
                severity=rule_result.severity, fired_rules=rule_result.fired_rules
            ),
        )

    # Even if no rule fired, being unable to run the real analysis at all
    # is itself a reason for some caution - this preserves that original
    # conservative floor while still letting the rule engine push higher
    # (e.g. an elderly patient with a symptom that's persisted for weeks).
    reported_severity = more_urgent(rule_result.severity, Severity.MODERATE)

    logger.warning(
        "Fallback triggered, rule engine severity=%s (reported as %s): %s",
        rule_result.severity.value,
        reported_severity.value,
        request.symptoms[:200],
    )
    return SymptomAnalysisResponse(
        possible_conditions=[],
        severity=reported_severity,
        recommended_action=(
            "AI analysis is temporarily unavailable, so your symptoms "
            "could not be assessed automatically. Please consult a "
            "healthcare professional, or contact emergency services if "
            "your symptoms are severe or worsen."
        ),
        sos_recommended=rule_result.sos_recommended,
        disclaimer=FALLBACK_DISCLAIMER,
        rule_engine=RuleEngineFindings(
            severity=rule_result.severity, fired_rules=rule_result.fired_rules
        ),
    )
