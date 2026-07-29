"""
/drug-interactions routes.

Public (no login required, same reasoning as /emergency/nearby-hospitals
- this is informational, not tied to any saved user data), rate-limited
by IP. Purely deterministic - see app/interactions/matcher.py's
docstring for why this never calls an AI model.
"""

from fastapi import APIRouter, Request

from app.config import settings
from app.interactions.matcher import check_interactions
from app.models.drug_interaction import (
    DrugInteractionCheckRequest,
    DrugInteractionCheckResponse,
    InteractionMatchOut,
)
from app.rate_limit import limiter

router = APIRouter(prefix="/drug-interactions", tags=["Drug Interactions"])

DISCLAIMER = (
    "This checks your medications against a small, hand-picked list of well-known "
    "interactions - it is NOT a comprehensive drug interaction database. A combination "
    "not flagged here has simply not been checked against a real, complete interaction "
    "database - it does not mean it is safe. Always ask a pharmacist or doctor before "
    "starting, stopping, or combining any medications."
)


@router.post("/check", response_model=DrugInteractionCheckResponse)
@limiter.limit(settings.RATE_LIMIT_DRUG_INTERACTIONS)
def check_drug_interactions(
    request: Request, payload: DrugInteractionCheckRequest
) -> DrugInteractionCheckResponse:
    matches, unrecognized = check_interactions(payload.drugs)
    return DrugInteractionCheckResponse(
        matches=[InteractionMatchOut(**vars(m)) for m in matches],
        unrecognized_drugs=unrecognized,
        disclaimer=DISCLAIMER,
    )
