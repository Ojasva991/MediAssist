"""
/analyze route - HTTP layer for AI Symptom Analysis.

Responsibilities:
1. Validate incoming request.
2. Forward request to the AI triage service.
3. Return a structured triage response.

No business logic is implemented here.
"""

import logging

from fastapi import APIRouter, HTTPException

from app.ai.triage_service import analyze_symptoms
from app.models.symptom import (
    SymptomAnalysisRequest,
    SymptomAnalysisResponse,
)

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
def analyze(
    request: SymptomAnalysisRequest,
) -> SymptomAnalysisResponse:
    """
    Analyze symptoms and estimate medical urgency.

    This endpoint performs AI-assisted symptom triage and returns a
    structured assessment. It never attempts to diagnose diseases.
    """

    try:
        return analyze_symptoms(request)

    except Exception as e:
        logger.exception("Unexpected error in /analyze: %s", e)

        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while analyzing symptoms. Please try again.",
        ) from e