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

    try:
        result = analyze_symptoms(payload)
    except Exception as e:
        logger.exception("Unexpected error in /analyze: %s", e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while analyzing symptoms. Please try again.",
        ) from e

    if current_user_id:
        try:
            save_analysis(current_user_id, payload, result)
        except Exception as e:
            # History is a nice-to-have, not core functionality - the user
            # must still get their analysis even if saving it fails.
            logger.exception("Failed to save analysis history for %s: %s", current_user_id, e)

    return result