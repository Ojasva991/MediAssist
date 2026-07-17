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
from app.ai.prompts import SYSTEM_PROMPT, build_analysis_prompt
from app.models.symptom import SymptomAnalysisRequest, SymptomAnalysisResponse

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
    """
    user_prompt = build_analysis_prompt(request)

    try:
        raw_text = gemini_client.generate(SYSTEM_PROMPT, user_prompt)
    except GeminiClientError as e:
        logger.error("Gemini call failed, using fallback: %s", e)
        return build_fallback_response(request.symptoms)

    try:
        data = _parse_gemini_json(raw_text)
    except TriageServiceError as e:
        logger.error("Gemini JSON parsing failed, using fallback: %s", e)
        return build_fallback_response(request.symptoms)

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

    try:
        return SymptomAnalysisResponse(**data)
    except ValidationError as e:
        logger.error(
            "Gemini JSON didn't match expected schema, using fallback: %s | data=%s",
            e,
            data,
        )
        return build_fallback_response(request.symptoms)
