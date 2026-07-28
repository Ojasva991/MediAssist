"""
Triage service - the orchestration layer for AI Symptom Analysis.

Flow: SymptomAnalysisRequest -> build prompt -> call Gemini ->
parse JSON -> validate into SymptomAnalysisResponse.

This is the ONLY place that knows about all three pieces (prompts,
gemini_client, models) at once. Routes (Milestone 4) will call
`analyze_symptoms()` and only ever deal with clean Pydantic models -
never raw AI output or JSON parsing.
"""

import json
import logging
import re

from pydantic import ValidationError

from app.ai.fallback import build_fallback_response
from app.ai.gemini_client import gemini_client, GeminiClientError
from app.ai.prompts import (
    IMAGE_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_analysis_prompt,
    build_image_analysis_prompt,
)
from app.models.symptom import (
    GuidanceReference,
    RuleEngineFindings,
    Severity,
    SymptomAnalysisRequest,
    SymptomAnalysisResponse,
)
from app.rag.retriever import retrieve as retrieve_guidance
from app.rules.engine import evaluate as evaluate_rules, more_urgent

logger = logging.getLogger(__name__)

DEFAULT_DISCLAIMER = (
    "This is not a medical diagnosis. If you are experiencing a medical "
    "emergency, contact local emergency services immediately."
)

# Defense-in-depth: the system prompt already instructs Gemini never to
# state a specific emergency number (see app/ai/prompts.py rule 6), since
# this app's actual SOS button dials India's number (112), not the
# US-centric "911" that LLMs default to from training data. LLMs don't
# always follow instructions perfectly, so this is a second, deterministic
# layer that scrubs any such number out if it slips through anyway - a
# wrong number in a medical emergency is not an acceptable failure mode.
_WRONG_EMERGENCY_NUMBER_PATTERN = re.compile(
    r"\b(?:call|dial|contact)\s+(?:the\s+)?(?:number\s+)?"
    r"(911|999|000|111|119|110|999|112 or 911)\b",
    re.IGNORECASE,
)
_GENERIC_REPLACEMENT = "contact your local emergency number"


def _sanitize_emergency_number(text: str) -> str:
    """Replace any AI-generated country-specific emergency number mention
    with generic guidance, so it can never contradict the app's real SOS
    number for the user's region. Preserves capitalization if the match
    was at the start of a sentence."""

    def _replace(match: re.Match) -> str:
        replacement = _GENERIC_REPLACEMENT
        if match.start() == 0 or text[match.start() - 2 : match.start()] in (". ", "! ", "? "):
            replacement = replacement[0].upper() + replacement[1:]
        return replacement

    return _WRONG_EMERGENCY_NUMBER_PATTERN.sub(_replace, text)


class TriageServiceError(Exception):
    """Raised when triage analysis cannot be completed, for any reason."""


def _parse_gemini_json(raw_text: str) -> dict:
    """
    Parse Gemini's raw text response into a dict.

    Even with response_mime_type="application/json" set on the API call,
    we don't blindly trust it - AI output should always be treated as
    untrusted input. This function isolates the "what if it's not valid
    JSON" problem in one place.

    We use raw_decode() instead of json.loads() because raw_decode()
    parses the FIRST valid JSON value and simply ignores anything after
    it (extra whitespace, stray trailing characters, etc). json.loads()
    is stricter and raises "Extra data" if anything trails the object -
    which we've seen Gemini occasionally produce even in JSON mode.
    """
    text = raw_text.strip()

    # Defensive: strip markdown code fences if the model added them
    # despite instructions (some models do this out of habit).
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        obj, _end_index = json.JSONDecoder().raw_decode(text)
    except json.JSONDecodeError as e:
        logger.error("Gemini returned invalid JSON: %s", raw_text[:500])
        raise TriageServiceError(
            "AI response could not be parsed as JSON. Please try again."
        ) from e

    if not isinstance(obj, dict):
        logger.error("Gemini JSON was not an object: %s", raw_text[:500])
        raise TriageServiceError(
            "AI response was not in the expected format. Please try again."
        )

    return obj


def analyze_symptoms(request: SymptomAnalysisRequest) -> SymptomAnalysisResponse:
    """
    Run a full triage analysis for the given (already-validated) request.

    Design note: this function no longer raises TriageServiceError for
    Gemini failures. Instead, ANY failure (API unreachable, malformed
    JSON, response not matching our schema) falls back to
    build_fallback_response(), which is a conservative safety net, not
    a diagnosis engine. See app/ai/fallback.py for why.

    TriageServiceError is kept as a class in case future callers need
    to distinguish "used fallback" from "fully failed" - currently
    nothing raises it, since the fallback always succeeds.

    Rule engine: runs first, deterministically, before Gemini is even
    called (see app/rules/engine.py). Its severity is a FLOOR - the
    final severity returned is whichever of (rule engine, Gemini) is
    more urgent, so a red-flag keyword match can never be silently
    downgraded by an LLM call that reads the situation as calmer than
    it is. The rule engine's findings are attached to the response
    (`rule_engine` field) for transparency either way.
    """
    rule_result = evaluate_rules(request)
    guidance_entries = retrieve_guidance(request.symptoms, top_k=3)

    user_prompt = build_analysis_prompt(request, guidance_entries)

    try:
        raw_text = gemini_client.generate(SYSTEM_PROMPT, user_prompt)
    except GeminiClientError as e:
        logger.error("Gemini call failed, using fallback: %s", e)
        return build_fallback_response(request)

    try:
        data = _parse_gemini_json(raw_text)
    except TriageServiceError as e:
        logger.error("Gemini JSON parsing failed, using fallback: %s", e)
        return build_fallback_response(request)

    # Defensive default: if the model somehow omits the disclaimer
    # despite instructions, we enforce it ourselves. Never let a missing
    # disclaimer slip through - this is a hard project rule, not optional.
    data.setdefault("disclaimer", DEFAULT_DISCLAIMER)

    # Defense-in-depth: scrub any wrong-country emergency number out of
    # free-text fields before they ever reach the user (see comment on
    # _sanitize_emergency_number above).
    if isinstance(data.get("recommended_action"), str):
        data["recommended_action"] = _sanitize_emergency_number(data["recommended_action"])
    if isinstance(data.get("disclaimer"), str):
        data["disclaimer"] = _sanitize_emergency_number(data["disclaimer"])

    # Reconcile the rule engine's floor with whatever Gemini reported,
    # BEFORE validating into the response model - never let a red-flag
    # keyword match get silently downgraded by the LLM's read of the
    # situation.
    llm_severity_raw = data.get("severity")
    if llm_severity_raw in ("LOW", "MODERATE", "HIGH", "EMERGENCY"):
        llm_severity_enum = Severity(llm_severity_raw)
        data["severity"] = more_urgent(rule_result.severity, llm_severity_enum).value
        data["llm_severity"] = llm_severity_enum.value
    else:
        data["severity"] = rule_result.severity.value
        data["llm_severity"] = None
    data["sos_recommended"] = bool(data.get("sos_recommended")) or rule_result.sos_recommended
    data["rule_engine"] = RuleEngineFindings(
        severity=rule_result.severity, fired_rules=rule_result.fired_rules
    )
    data["retrieved_guidance"] = [
        GuidanceReference(source=g.source, topic=g.topic) for g in guidance_entries
    ]

    try:
        return SymptomAnalysisResponse(**data)
    except ValidationError as e:
        logger.error(
            "Gemini JSON didn't match expected schema, using fallback: %s | data=%s",
            e,
            data,
        )
        return build_fallback_response(request)


IMAGE_ANALYSIS_DISCLAIMER_SUFFIX = (
    " Photo-based assessment is significantly less reliable than an "
    "in-person examination and cannot rule out serious conditions, "
    "including skin cancer. If you have a new, changing, or unusual-"
    "looking growth or wound, see a healthcare professional promptly "
    "regardless of this assessment."
)


def analyze_image(
    image_bytes: bytes,
    mime_type: str,
    *,
    age: int | None,
    gender: str | None,
    duration: str | None,
    symptoms_text: str | None,
    existing_conditions: str | None,
) -> SymptomAnalysisResponse:
    """
    Run a photo-based visual symptom analysis. Mirrors analyze_symptoms()
    above but for POST /analyze/image - same defense-in-depth pattern
    (rule-engine severity floor, emergency-number scrubbing, disclaimer
    enforcement, fallback on any failure), plus image-specific rules (see
    app/ai/prompts.py's IMAGE_SYSTEM_PROMPT) since photo-based assessment
    is a meaningfully higher-stakes failure mode than text (see that
    prompt's docstring for why).

    The rule engine still runs here, using whatever `symptoms_text` was
    provided alongside the photo (if any) - it cannot see the image
    itself, so it's a floor based on what the person described in words,
    not a full safety net for the visual content. That's a real,
    intentional limitation, not an oversight: the rule engine's red-flag
    keywords were built for described symptoms, not photos.
    """
    rule_engine_request = SymptomAnalysisRequest(
        age=age,
        gender=gender,
        symptoms=(
            symptoms_text.strip()
            if symptoms_text and symptoms_text.strip()
            else "Visible symptom shown in an uploaded photo, no text description provided."
        ),
        duration=duration or "Not specified",
        existing_conditions=existing_conditions,
    )
    rule_result = evaluate_rules(rule_engine_request)
    guidance_entries = retrieve_guidance(symptoms_text, top_k=3) if symptoms_text else []

    user_prompt = build_image_analysis_prompt(
        age=age,
        gender=gender,
        duration=duration,
        symptoms_text=symptoms_text,
        existing_conditions=existing_conditions,
    )

    try:
        raw_text = gemini_client.generate_with_image(
            IMAGE_SYSTEM_PROMPT, user_prompt, image_bytes, mime_type
        )
    except GeminiClientError as e:
        logger.error("Gemini image call failed, using fallback: %s", e)
        return build_fallback_response(rule_engine_request)

    try:
        data = _parse_gemini_json(raw_text)
    except TriageServiceError as e:
        logger.error("Gemini image JSON parsing failed, using fallback: %s", e)
        return build_fallback_response(rule_engine_request)

    data.setdefault("disclaimer", DEFAULT_DISCLAIMER)
    # Defense-in-depth: always append the stronger image-specific caveat,
    # regardless of whether the model already included something similar
    # per its instructions - never rely solely on the model following
    # IMAGE_SYSTEM_PROMPT's rule 6 on its own.
    if (
        isinstance(data.get("disclaimer"), str)
        and IMAGE_ANALYSIS_DISCLAIMER_SUFFIX.strip() not in data["disclaimer"]
    ):
        data["disclaimer"] = data["disclaimer"].rstrip() + IMAGE_ANALYSIS_DISCLAIMER_SUFFIX

    if isinstance(data.get("recommended_action"), str):
        data["recommended_action"] = _sanitize_emergency_number(data["recommended_action"])
    if isinstance(data.get("disclaimer"), str):
        data["disclaimer"] = _sanitize_emergency_number(data["disclaimer"])

    image_rejected = bool(data.get("image_rejected", False))

    # If the image was rejected (looks like a scan/document, not a photo
    # of a visible symptom), don't apply the rule-engine severity floor -
    # there's nothing to triage, and forcing a severity here would imply
    # an assessment was actually made when it wasn't.
    if image_rejected:
        data.setdefault("possible_conditions", [])
        data.setdefault("severity", "LOW")
        data.setdefault("sos_recommended", False)
        data["llm_severity"] = None
        data["rule_engine"] = None
        data["retrieved_guidance"] = []
    else:
        llm_severity_raw = data.get("severity")
        if llm_severity_raw in ("LOW", "MODERATE", "HIGH", "EMERGENCY"):
            llm_severity_enum = Severity(llm_severity_raw)
            data["severity"] = more_urgent(rule_result.severity, llm_severity_enum).value
            data["llm_severity"] = llm_severity_enum.value
        else:
            data["severity"] = rule_result.severity.value
            data["llm_severity"] = None
        data["sos_recommended"] = bool(data.get("sos_recommended")) or rule_result.sos_recommended
        data["rule_engine"] = RuleEngineFindings(
            severity=rule_result.severity, fired_rules=rule_result.fired_rules
        )
        data["retrieved_guidance"] = [
            GuidanceReference(source=g.source, topic=g.topic) for g in guidance_entries
        ]

    data["image_rejected"] = image_rejected

    try:
        return SymptomAnalysisResponse(**data)
    except ValidationError as e:
        logger.error(
            "Gemini image JSON didn't match expected schema, using fallback: %s | data=%s",
            e,
            data,
        )
        return build_fallback_response(rule_engine_request)
