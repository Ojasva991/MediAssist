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
from app.ai.gateway import generate as ai_gateway_generate, AIGatewayError
from app.ai.prompts import (
    IMAGE_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    FOLLOWUP_SYSTEM_PROMPT,
    build_analysis_prompt,
    build_image_analysis_prompt,
    build_follow_up_prompt,
)
from app.models.followup import FollowUpResponse
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
    # Deliberately NOT anchored to English verbs like "call"/"dial" -
    # this needs to catch these numbers regardless of what language
    # surrounds them (e.g. "llama al 911", "911 पर कॉल करें"), since the
    # multilingual assistant (see app/ai/prompts.py) can respond in any
    # language the person used. These specific numbers are unlikely to
    # appear in medical triage text for any other reason, so matching
    # them as bare tokens - not just after specific English verbs - is
    # the safer tradeoff: a rare false positive here costs nothing, a
    # missed wrong number in a real emergency costs a lot.
    r"\b(911|999|000|111|119|110)\b"
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
        raw_text = ai_gateway_generate(SYSTEM_PROMPT, user_prompt)
    except AIGatewayError as e:
        logger.error("All AI providers failed, using fallback: %s", e)
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


def _follow_up_fallback(rule_result) -> FollowUpResponse:
    """
    Safe, conservative reply when the AI gateway is unavailable for a
    follow-up message - based purely on the deterministic rule engine,
    same reasoning as build_fallback_response for the main analysis.
    Never leaves someone without guidance just because every AI
    provider failed.
    """
    if rule_result.sos_recommended or rule_result.severity == Severity.EMERGENCY:
        reply = (
            "I'm having trouble processing your message right now, but based on what you've "
            "described, please treat this as urgent - use the SOS button or contact your local "
            "emergency number rather than waiting for a chat response."
        )
    else:
        reply = (
            "I'm having trouble processing your message right now. If your symptoms are "
            "getting worse or you're worried, please contact a healthcare professional or use "
            "the app's SOS page rather than waiting on this chat."
        )
    return FollowUpResponse(
        reply=reply,
        severity=rule_result.severity.value,
        escalation_detected=False,
        sos_recommended=rule_result.sos_recommended,
        disclaimer=DEFAULT_DISCLAIMER,
    )


def answer_follow_up(
    original_symptoms: str, conversation: list[dict], message: str
) -> FollowUpResponse:
    """
    Answers one follow-up chat message in a conversation attached to an
    earlier analysis (see POST /analyze/follow-up).

    The deterministic rule engine re-runs here over the FULL
    conversation text (original symptoms + every prior user message +
    this new one) - not just the AI's own judgment - so a red-flag
    phrase raised mid-conversation still raises the severity floor even
    if the AI's own "escalation_detected" call is wrong. Same "AI can't
    downgrade below the rule engine's floor" guarantee as the original
    analysis in analyze_symptoms() above.

    Stateless - no chat history is persisted here (see
    app/models/followup.py's scope note). Goes through the same AI
    gateway (Gemini -> Groq) as text analysis.
    """
    combined_text = " ".join(
        [original_symptoms]
        + [turn.get("content", "") for turn in conversation if turn.get("role") == "user"]
        + [message]
    )
    rule_engine_request = SymptomAnalysisRequest(
        age=None,
        gender=None,
        symptoms=(combined_text.strip() or "No description provided.")[:1000],
        duration="Not specified",
        existing_conditions=None,
    )
    rule_result = evaluate_rules(rule_engine_request)

    user_prompt = build_follow_up_prompt(conversation, message)

    try:
        raw_text = ai_gateway_generate(FOLLOWUP_SYSTEM_PROMPT, user_prompt)
    except AIGatewayError as e:
        logger.error("All AI providers failed for follow-up, using safe fallback: %s", e)
        return _follow_up_fallback(rule_result)

    try:
        data = _parse_gemini_json(raw_text)
    except TriageServiceError as e:
        logger.error("Follow-up JSON parsing failed, using safe fallback: %s", e)
        return _follow_up_fallback(rule_result)

    data.setdefault("disclaimer", DEFAULT_DISCLAIMER)
    if isinstance(data.get("reply"), str):
        data["reply"] = _sanitize_emergency_number(data["reply"])
    if isinstance(data.get("disclaimer"), str):
        data["disclaimer"] = _sanitize_emergency_number(data["disclaimer"])

    llm_severity_raw = data.get("severity")
    if llm_severity_raw in ("LOW", "MODERATE", "HIGH", "EMERGENCY"):
        llm_severity_enum = Severity(llm_severity_raw)
        reconciled_severity = more_urgent(rule_result.severity, llm_severity_enum)
    else:
        llm_severity_enum = None
        reconciled_severity = rule_result.severity

    data["severity"] = reconciled_severity.value
    data["sos_recommended"] = bool(data.get("sos_recommended")) or rule_result.sos_recommended

    # If the rule engine's floor forced severity UP beyond what the AI
    # itself reported, that's an escalation regardless of the AI's own
    # "escalation_detected" flag - defense in depth, don't just trust
    # the model noticed.
    if llm_severity_enum is not None and reconciled_severity != llm_severity_enum:
        data["escalation_detected"] = True
    else:
        data["escalation_detected"] = bool(data.get("escalation_detected", False))

    try:
        return FollowUpResponse(**data)
    except ValidationError as e:
        logger.error(
            "Follow-up JSON didn't match expected schema, using fallback: %s | data=%s", e, data
        )
        return _follow_up_fallback(rule_result)
