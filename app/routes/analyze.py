"""
/analyze route - HTTP layer for AI Symptom Analysis.

Responsibilities:
1. Validate incoming request.
2. Forward request to the AI triage service.
3. Return a structured triage response.

No business logic is implemented here.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.ai.triage_service import analyze_image, analyze_symptoms, answer_follow_up
from app.auth.dependencies import get_optional_user_id
from app.config import settings
from app.models.followup import FollowUpRequest, FollowUpResponse
from app.models.symptom import (
    SymptomAnalysisRequest,
    SymptomAnalysisResponse,
)
from app.rate_limit import limiter
from app.storage.history_store import save_analysis
from app.storage.passport_store import get_passport

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Symptom Analysis"])

# Same reasoning/caps as Health Passport document uploads
# (app/storage/document_store.py) - kept in sync deliberately, images
# submitted here are typically phone-camera photos, same size ballpark
# as a scanned document.
MAX_IMAGE_SIZE_BYTES = 8 * 1024 * 1024  # 8 MB
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post(
    "/analyze",
    response_model=SymptomAnalysisResponse,
    summary="Analyze User Symptoms",
    description="""
Analyze user-reported symptoms using the Vaeda AI triage engine.

The AI estimates the urgency of the reported symptoms and recommends the
next appropriate medical action.

### Input
- Age
- Gender
- Symptoms
- Duration
- Existing medical conditions (optional)

### Output
- Possible conditions
- Severity (LOW, MODERATE, HIGH, EMERGENCY)
- Recommended next step
- SOS recommendation
- Medical disclaimer

⚠️ This endpoint **does not diagnose diseases** and should not be used as
a replacement for professional medical advice.
""",
    response_description="Structured AI-generated triage assessment.",
    responses={
        200: {
            "description": "Symptoms analyzed successfully.",
        },
        422: {
            "description": "Validation error. Invalid or missing input fields.",
        },
        500: {
            "description": "Unexpected internal server error.",
        },
    },
)
@limiter.limit(settings.RATE_LIMIT_ANALYZE)
def analyze(
    request: Request,
    payload: SymptomAnalysisRequest,
    current_user_id: Optional[str] = Depends(get_optional_user_id),
) -> SymptomAnalysisResponse:
    """
    Analyze symptoms and estimate medical urgency.

    This endpoint performs AI-assisted symptom triage and returns a
    structured assessment. It never attempts to diagnose diseases.

    Works with or without login - anyone can use it. If the caller is
    logged in (valid Bearer token), the analysis is also saved to their
    history (see GET /history/{user_id}). A failed history save never
    blocks the actual analysis response.

    Rate limited per client IP (see app.rate_limit / settings.RATE_LIMIT_ANALYZE)
    - this endpoint calls the Gemini API, which costs money per request and
    has no authentication gate, so it needs its own abuse protection.
    """

    # Fill in age/gender/existing_conditions from the caller's saved Health
    # Passport when they weren't provided directly - this is what lets a
    # logged-in user skip re-entering them on every analysis. Anything the
    # caller DID send in the request takes priority over the saved passport,
    # so someone can still override for a one-off analysis (e.g. checking
    # symptoms on behalf of someone else) without editing their own passport.
    age = payload.age
    gender = payload.gender
    existing_conditions = payload.existing_conditions

    if current_user_id and (age is None or not gender or not existing_conditions):
        try:
            saved_passport = get_passport(current_user_id)
        except Exception as e:
            # A passport lookup failure should never block an analysis the
            # user is otherwise able to complete - just fall through and
            # let the missing-fields check below ask for the data directly.
            logger.exception(
                "Failed to load Health Passport for %s during /analyze: %s",
                current_user_id,
                e,
            )
            saved_passport = None

        if saved_passport is not None:
            if age is None:
                age = saved_passport.age
            if not gender:
                gender = saved_passport.gender
            if not existing_conditions:
                existing_conditions = saved_passport.chronic_diseases

    if age is None or not gender:
        raise HTTPException(
            status_code=400,
            detail=(
                "Age and gender are required for a symptom analysis. Provide "
                "them directly in this request, or save them once in your "
                "Health Passport so you never have to enter them again."
            ),
        )

    resolved_payload = payload.model_copy(
        update={"age": age, "gender": gender, "existing_conditions": existing_conditions}
    )

    try:
        result = analyze_symptoms(resolved_payload)
    except Exception as e:
        logger.exception("Unexpected error in /analyze: %s", e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while analyzing symptoms. Please try again.",
        ) from e

    if current_user_id:
        try:
            history_id = save_analysis(current_user_id, resolved_payload, result)
            result = result.model_copy(update={"history_id": history_id})
        except Exception as e:
            # History is a nice-to-have, not core functionality - the user
            # must still get their analysis even if saving it fails.
            logger.exception("Failed to save analysis history for %s: %s", current_user_id, e)

    return result

@router.post(
    "/analyze/image",
    response_model=SymptomAnalysisResponse,
    summary="Analyze a Photo of a Visible Symptom",
    description="""
Analyze a photo of a visible symptom (skin change, rash, wound, swelling,
bite, bruise) using the Vaeda AI triage engine's image-analysis mode.

Deliberately NOT for medical scans (X-rays, CT/MRI, lab report photos) -
the AI is instructed to decline interpreting those (`image_rejected: true`
in the response) rather than attempt it, since that needs a radiologist
or the ordering doctor, not general visual AI analysis.

Photo-based assessment is inherently less reliable than an in-person
exam or even text-described symptoms - see the mandatory extra caveat
in every response's `disclaimer` field.

⚠️ This endpoint **does not diagnose diseases** and should not be used
as a replacement for professional medical advice, especially for any
new, changing, or unusual-looking growth or wound.
""",
    responses={
        200: {"description": "Image analyzed successfully."},
        400: {"description": "Invalid image (wrong type, too large, or unreadable)."},
        422: {"description": "Validation error on the accompanying form fields."},
        500: {"description": "Unexpected internal server error."},
    },
)
@limiter.limit(settings.RATE_LIMIT_ANALYZE_IMAGE)
async def analyze_image_route(
    request: Request,
    image: UploadFile = File(...),
    symptoms: Optional[str] = Form(default=None, max_length=1000),
    duration: Optional[str] = Form(default=None, max_length=100),
    age: Optional[int] = Form(default=None, ge=0, le=120),
    gender: Optional[str] = Form(default=None, max_length=30),
    existing_conditions: Optional[str] = Form(default=None, max_length=500),
    current_user_id: Optional[str] = Depends(get_optional_user_id),
) -> SymptomAnalysisResponse:
    """
    Same auth/history/passport-fill-in behavior as POST /analyze (see
    that docstring) - works with or without login, saves to history if
    logged in, fills in age/gender/existing_conditions from a saved
    Health Passport when the caller doesn't provide them and is logged
    in. Unlike /analyze, none of the patient-info fields are strictly
    required here - a photo can be submitted with no accompanying text
    at all, since the image itself is the primary input.
    """
    if image.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported image type '{image.content_type}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_IMAGE_CONTENT_TYPES))}."
            ),
        )

    image_bytes = await image.read()
    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Image is too large. Maximum size is {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB.",
        )
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    resolved_age = age
    resolved_gender = gender
    resolved_existing_conditions = existing_conditions

    if current_user_id and (
        resolved_age is None or not resolved_gender or not resolved_existing_conditions
    ):
        try:
            saved_passport = get_passport(current_user_id)
        except Exception as e:
            logger.exception(
                "Failed to load Health Passport for %s during /analyze/image: %s",
                current_user_id,
                e,
            )
            saved_passport = None

        if saved_passport is not None:
            if resolved_age is None:
                resolved_age = saved_passport.age
            if not resolved_gender:
                resolved_gender = saved_passport.gender
            if not resolved_existing_conditions:
                resolved_existing_conditions = saved_passport.chronic_diseases

    try:
        result = analyze_image(
            image_bytes,
            image.content_type,
            age=resolved_age,
            gender=resolved_gender,
            duration=duration,
            symptoms_text=symptoms,
            existing_conditions=resolved_existing_conditions,
        )
    except Exception as e:
        logger.exception("Unexpected error in /analyze/image: %s", e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while analyzing the image. Please try again.",
        ) from e

    if current_user_id:
        # analysis_history.age/gender are NOT NULL (shared table with the
        # text-only /analyze flow, which always has both by the time it
        # gets this far). Unlike /analyze, this endpoint deliberately
        # allows a photo with zero accompanying patient info - so unlike
        # /analyze, that info may genuinely not exist here. Rather than
        # fabricate a fake age/gender to satisfy the constraint (which
        # would misrepresent real data in someone's history), just skip
        # saving to history in that case - the analysis itself still
        # succeeds and is returned either way, only the history record
        # is skipped.
        if resolved_age is not None and resolved_gender:
            try:
                history_request = SymptomAnalysisRequest(
                    age=resolved_age,
                    gender=resolved_gender,
                    symptoms=(
                        symptoms.strip()
                        if symptoms and symptoms.strip()
                        else "[Photo-based analysis]"
                    ),
                    duration=duration or "Not specified",
                    existing_conditions=resolved_existing_conditions,
                )
                history_id = save_analysis(current_user_id, history_request, result)
                result = result.model_copy(update={"history_id": history_id})
            except Exception as e:
                logger.exception(
                    "Failed to save image-analysis history for %s: %s", current_user_id, e
                )
        else:
            logger.info(
                "Skipping history save for image analysis by %s - no age/gender available "
                "(neither provided nor found in a saved passport).",
                current_user_id,
            )

    return result


@router.post(
    "/analyze/follow-up",
    response_model=FollowUpResponse,
    summary="Ask a Follow-Up Question About an Analysis",
    description="""
Continue a conversation about an earlier symptom analysis - "why is this
serious?", "what if I also have X?", and similar.

Stateless: send the full conversation each time (see FollowUpRequest) -
nothing is remembered server-side between calls.

The deterministic rule engine re-runs over the WHOLE conversation
(original symptoms + every message exchanged) on every call - if
something you describe mid-conversation is a known red flag, the
severity floor rises regardless of what the AI itself concludes, same
as the original analysis endpoint.

⚠️ Same disclaimers as POST /analyze apply - this is informational only,
not a diagnosis, and not a substitute for professional care.
""",
)
@limiter.limit(settings.RATE_LIMIT_ANALYZE)
def follow_up_route(request: Request, payload: FollowUpRequest) -> FollowUpResponse:
    return answer_follow_up(
        original_symptoms=payload.original_symptoms,
        conversation=[turn.model_dump() for turn in payload.conversation],
        message=payload.message,
    )
