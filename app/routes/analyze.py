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

from fastapi import APIRouter, Depends, HTTPException, Request

from app.ai.triage_service import analyze_symptoms
from app.auth.dependencies import get_optional_user_id
from app.config import settings
from app.models.symptom import (
    SymptomAnalysisRequest,
    SymptomAnalysisResponse,
)
from app.rate_limit import limiter
from app.storage.history_store import save_analysis
from app.storage.passport_store import get_passport

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Symptom Analysis"])


@router.post(
    "/analyze",
    response_model=SymptomAnalysisResponse,
    summary="Analyze User Symptoms",
    description="""
Analyze user-reported symptoms using the MediAssist AI triage engine.

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