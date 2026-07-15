"""
/analyze route - HTTP layer for AI Symptom Analysis.

This module deliberately contains NO business logic. Its only job is:
  1. Receive and let FastAPI validate the request (via SymptomAnalysisRequest)
  2. Call triage_service.analyze_symptoms()
  3. Return the result

All the interesting work (prompting, calling Gemini, parsing, fallback)
lives in app/ai/. This keeps the route trivially easy to read and test.
"""

import logging

from fastapi import APIRouter, HTTPException

from app.ai.triage_service import analyze_symptoms
from app.models.symptom import SymptomAnalysisRequest, SymptomAnalysisResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Symptom Analysis"])


@router.post("/analyze", response_model=SymptomAnalysisResponse)
def analyze(request: SymptomAnalysisRequest) -> SymptomAnalysisResponse:
    """
    Analyze reported symptoms and return an estimated urgency/triage result.

    NOTE: This endpoint does NOT diagnose any disease. It estimates
    severity and recommends a next step only. See `disclaimer` in the
    response, which is always present.

    FastAPI validates the incoming JSON against SymptomAnalysisRequest
    automatically - invalid input (e.g. negative age, blank symptoms)
    is rejected with a 422 error before this function even runs.
    """
    try:
        return analyze_symptoms(request)
    except Exception as e:
        # analyze_symptoms() already handles Gemini failures internally
        # via the fallback (see app/ai/triage_service.py) - it should not
        # raise under normal operation. This is a last-resort safety net
        # for anything truly unexpected (e.g. a bug), so the API never
        # returns a raw 500 with a stack trace to the frontend.
        logger.exception("Unexpected error in /analyze: %s", e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while analyzing symptoms. Please try again.",
        ) from e
