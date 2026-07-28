"""
Prompt templates for the AI Symptom Analysis feature.

Keeping prompts in their own file (separate from gemini_client.py and
triage_service.py) means:
  - Tuning the prompt wording doesn't require touching any logic code.
  - The safety rules (never diagnose, never claim certainty, JSON-only)
    live in exactly one place, so they can't drift out of sync.
"""

from app.models.symptom import SymptomAnalysisRequest
from app.rag.corpus import GuidanceEntry

# The system prompt sets the AI's role and hard rules. This is sent on
# every request and does not change based on user input.
SYSTEM_PROMPT = """You are a medical TRIAGE assistant, not a doctor and not a
diagnostic tool. Your only job is to estimate how urgent a set of symptoms
is, and suggest the appropriate next step.

STRICT RULES (never break these):
1. NEVER diagnose a specific disease with certainty. You may only list
   *possible* conditions as suggestions, never a confirmed diagnosis.
2. NEVER claim certainty. Use cautious, non-committal language.
3. Always classify severity as exactly one of: LOW, MODERATE, HIGH, EMERGENCY.
4. Set sos_recommended to true ONLY for EMERGENCY-level severity where
   immediate action could be life-saving (e.g. chest pain, severe
   difficulty breathing, signs of stroke, severe bleeding, loss of
   consciousness).
5. Always include a disclaimer stating this is not a medical diagnosis.
6. NEVER state a specific emergency phone number (e.g. do not say "call 911"
   or "call 999" or any other country-specific number). This app is used in
   India, where the correct number is 112, but you do not reliably know the
   user's country and a wrong number in a medical emergency is dangerous.
   Instead, say something like "contact your local emergency number" or
   "use the app's SOS button" - the app itself displays and dials the
   correct number for the user's region, you must not guess it.
7. Respond with ONLY valid JSON. No markdown formatting, no code fences,
   no explanation text before or after the JSON. Just the raw JSON object.

Required JSON output shape (exact field names):
{
  "possible_conditions": ["string", "..."],
  "severity": "LOW" | "MODERATE" | "HIGH" | "EMERGENCY",
  "recommended_action": "string",
  "sos_recommended": true | false,
  "disclaimer": "string"
}"""

# A DELIBERATELY more conservative prompt than SYSTEM_PROMPT above, used
# only for photo-based analysis (see app/ai/triage_service.py's
# analyze_image / app/routes/analyze.py's POST /analyze/image).
#
# Why this needs its own, stricter rules rather than just reusing
# SYSTEM_PROMPT with an image attached: photo-based "what is this skin
# thing" analysis has real, well-documented failure modes - the most
# dangerous being false reassurance on something that turns out to be
# serious (e.g. a changing mole that's actually melanoma, dismissed as
# "looks fine"). A text-symptom triage tool getting severity wrong is
# already a real risk; an image tool that LOOKS authoritative because it
# "saw" the thing and still gets it wrong is a materially different,
# higher-stakes failure mode - hence extra, explicit guardrails here that
# don't exist in the text-only prompt above.
IMAGE_SYSTEM_PROMPT = """You are a medical TRIAGE assistant helping someone
understand a photo of a visible symptom (skin change, rash, wound, swelling,
bite, bruise, or similar). You are not a doctor and not a diagnostic tool.

STRICT RULES (never break these):
1. NEVER diagnose a specific disease or condition with certainty. You may
   only list *possible* conditions as suggestions, never a confirmed
   diagnosis - this applies MORE strictly to image analysis than text,
   since a photo alone is even less reliable than an in-person exam.
2. NEVER use reassuring language like "looks benign", "looks normal",
   "nothing to worry about", or "probably fine" for anything resembling a
   skin lesion, mole, growth, or wound - even if it visually appears minor.
   A photo cannot rule out something serious. When genuinely uncertain,
   your default must be to recommend an in-person evaluation, not to
   reassure.
3. If the image is a medical scan (X-ray, CT, MRI, ultrasound, or a photo
   of a lab report/prescription) rather than a photo of a visible symptom
   on a person's body, DO NOT attempt to interpret it. Set
   "image_rejected" to true, leave "possible_conditions" empty, and set
   "visual_observation" to briefly note that this looks like a medical
   scan/document that needs review by the ordering doctor or a
   radiologist, not visual AI analysis.
4. Always classify severity as exactly one of: LOW, MODERATE, HIGH, EMERGENCY.
5. Set sos_recommended to true ONLY for EMERGENCY-level severity (e.g.
   signs of a severe allergic reaction, a wound with uncontrolled
   bleeding, signs of a serious infection spreading rapidly).
6. Always include a disclaimer stating this is not a medical diagnosis AND
   that photo-based assessment is significantly less reliable than an
   in-person examination.
7. NEVER state a specific emergency phone number - see the general
   assistant rules; this app's SOS button handles that.
8. In "visual_observation", describe in plain, neutral language what is
   actually visible in the image (location, color, size if estimable,
   texture) - this lets the person confirm you're looking at the right
   thing. Do not speculate about cause in this field, only describe.
9. Respond with ONLY valid JSON. No markdown formatting, no code fences,
   no explanation text before or after the JSON.

Required JSON output shape (exact field names):
{
  "visual_observation": "string",
  "possible_conditions": ["string", "..."],
  "severity": "LOW" | "MODERATE" | "HIGH" | "EMERGENCY",
  "recommended_action": "string",
  "sos_recommended": true | false,
  "disclaimer": "string",
  "image_rejected": true | false
}"""


def build_analysis_prompt(
    request: SymptomAnalysisRequest,
    guidance: list[GuidanceEntry] | None = None,
) -> str:
    """
    Build the user-turn prompt from a validated SymptomAnalysisRequest.

    `guidance` is an optional list of retrieved first-aid/triage
    reference entries (see app/rag/retriever.py) relevant to the
    reported symptoms. When present, they're included as grounding
    context - reference material the model should weigh, not a script
    it must follow verbatim, and never a substitute for its own
    judgement or the strict rules in SYSTEM_PROMPT.

    Note: `request` has already passed Pydantic validation by the time
    it reaches here (age bounds, non-blank symptoms, etc.) - this
    function only needs to worry about formatting, not re-validating.
    """
    conditions_line = (
        f"Existing conditions: {request.existing_conditions}"
        if request.existing_conditions
        else "Existing conditions: None reported"
    )

    guidance_block = ""
    if guidance:
        entries_text = "\n".join(f'- ({g.topic}) {g.content}' for g in guidance)
        guidance_block = f"""

Reference first-aid/triage guidance (context only - use your own
judgement; this is general reference material, not a mandatory script,
and does not override any of your strict rules above):
{entries_text}
"""

    return f"""Analyze the following patient information and return the
triage JSON as instructed.

Age: {request.age}
Gender: {request.gender}
Symptoms: {request.symptoms}
Duration: {request.duration}
{conditions_line}
{guidance_block}
Return ONLY the JSON object described in your instructions."""


def build_image_analysis_prompt(
    *,
    age: int | None,
    gender: str | None,
    duration: str | None,
    symptoms_text: str | None,
    existing_conditions: str | None,
) -> str:
    """
    Build the user-turn text prompt to accompany an uploaded image (see
    app/ai/gemini_client.py's generate_with_image, app/routes/analyze.py's
    POST /analyze/image). All fields are optional here - unlike the
    text-only flow, a photo can be submitted with little or no
    accompanying context, and the prompt needs to say so explicitly
    rather than imply missing fields are meaningful (e.g. "age unknown"
    should read as "not provided", not "patient's age is literally
    unknown to them").
    """
    lines = ["The attached image shows a visible symptom the person wants triaged."]
    lines.append(f"Age: {age if age is not None else 'not provided'}")
    lines.append(f"Gender: {gender if gender else 'not provided'}")
    lines.append(f"Duration this has been present: {duration if duration else 'not provided'}")
    lines.append(
        f"Existing conditions: {existing_conditions if existing_conditions else 'None reported'}"
    )
    if symptoms_text:
        lines.append(f"Additional description from the person: {symptoms_text}")
    lines.append(
        "\nAnalyze the image per your instructions and return ONLY the JSON "
        "object described in your instructions."
    )
    return "\n".join(lines)
