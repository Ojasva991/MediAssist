"""
Medical rule engine - Milestone: Symptoms -> Rule Engine -> Severity ->
LLM Explanation.

This runs BEFORE (and independently of) the Gemini call, on every
/analyze request. It's pure keyword/age/duration logic - no network
call, no AI - so it always runs, always produces the same output for
the same input, and every decision it makes is explainable (see
`fired_rules` on the result).

Why this exists: an LLM is good at generating a readable explanation,
but on its own it's not a reliable FINAL word on urgency - phrasing
that reads as calm can still describe something dangerous, and the same
symptoms can get a different severity from the LLM on different calls.
This rule engine gives an auditable, reproducible severity FLOOR that
the LLM is never allowed to downgrade below.

How it combines with the LLM (see app/ai/triage_service.py):
the final severity is whichever of (rule engine, LLM) is MORE urgent.
The rule engine can only push severity UP, never down, and it never
touches the LLM's possible_conditions or recommended_action text - it
only sets a floor for severity/sos_recommended, plus an explanation of
why.
"""

import re
from dataclasses import dataclass, field

from app.models.symptom import Severity, SymptomAnalysisRequest
from app.rules.red_flags import EMERGENCY_KEYWORDS, HIGH_RISK_KEYWORDS

# Ordering used to compare severities - higher index = more urgent.
_SEVERITY_ORDER = [Severity.LOW, Severity.MODERATE, Severity.HIGH, Severity.EMERGENCY]

_INFANT_AGE_THRESHOLD = 2
_ELDERLY_AGE_THRESHOLD = 65

# Loose, deliberately forgiving match for "this has been going on a
# while" - covers "2 weeks", "a few weeks", "3 months", "several weeks"
# etc. Not meant to parse duration precisely, just to catch chronicity.
_PROLONGED_DURATION_PATTERN = re.compile(r"\b(weeks?|months?)\b", re.IGNORECASE)


def more_urgent(a: Severity, b: Severity) -> Severity:
    """Return whichever of the two severities is more urgent (ties -> a)."""
    return a if _SEVERITY_ORDER.index(a) >= _SEVERITY_ORDER.index(b) else b


@dataclass
class RuleEngineResult:
    severity: Severity
    sos_recommended: bool
    fired_rules: list[str] = field(default_factory=list)


def evaluate(request: SymptomAnalysisRequest) -> RuleEngineResult:
    """Deterministically evaluate a symptom request and return a floor
    severity, independent of any LLM call."""
    text = request.symptoms.lower()
    fired: list[str] = []
    severity = Severity.LOW
    sos_recommended = False

    # 1. Emergency red-flag keywords - the highest tier, always wins.
    matched_emergency = [kw for kw in EMERGENCY_KEYWORDS if kw in text]
    if matched_emergency:
        severity = Severity.EMERGENCY
        sos_recommended = True
        fired.append(
            f"Symptom description matches an emergency red-flag keyword: "
            f"'{matched_emergency[0]}'"
        )

    # 2. High-risk keywords - bump to at least HIGH (unless already at
    # the higher EMERGENCY tier from rule 1).
    matched_high = [kw for kw in HIGH_RISK_KEYWORDS if kw in text]
    if matched_high and severity != Severity.EMERGENCY:
        severity = more_urgent(severity, Severity.HIGH)
        fired.append(
            f"Symptom description matches a high-risk keyword: '{matched_high[0]}'"
        )

    # 3. Age-based risk modifiers - infants/toddlers and patients 65+ are
    # bumped from LOW to MODERATE, since the same reported symptoms
    # carry more risk at those ages. This is a standard triage
    # heuristic, not a diagnosis, and only ever raises severity from the
    # otherwise-untouched LOW baseline.
    if request.age is not None and severity == Severity.LOW:
        if request.age <= _INFANT_AGE_THRESHOLD:
            severity = Severity.MODERATE
            fired.append(
                f"Patient age ({request.age}) is in the infant/toddler range - "
                "symptoms are treated more cautiously at this age"
            )
        elif request.age >= _ELDERLY_AGE_THRESHOLD:
            severity = Severity.MODERATE
            fired.append(
                f"Patient age ({request.age}) is 65 or older - symptoms are "
                "treated more cautiously at this age"
            )

    # 4. Duration - symptoms that have reportedly persisted for weeks or
    # months and are still at least MODERATE get bumped to HIGH: "still a
    # concern after this long" itself raises urgency, independent of what
    # the symptom is.
    if severity == Severity.MODERATE and _PROLONGED_DURATION_PATTERN.search(
        request.duration or ""
    ):
        severity = Severity.HIGH
        fired.append(
            f"Symptoms have reportedly persisted for an extended duration "
            f"('{request.duration}')"
        )

    return RuleEngineResult(
        severity=severity, sos_recommended=sos_recommended, fired_rules=fired
    )
