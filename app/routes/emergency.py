"""
/emergency routes - emergency-flow improvements layered on top of the
existing SOS page (calling 112 / an emergency contact).

No authentication required, deliberately: the SOS page itself works
for logged-out users (it degrades gracefully with no passport data),
and someone in an emergency shouldn't be blocked from finding a nearby
hospital because they're not logged in. Rate-limited by IP instead,
same reasoning/pattern as /analyze (see app/rate_limit.py).
"""

import logging

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.config import settings
from app.emergency.hospital_lookup import HospitalLookupError, fetch_nearby_hospitals
from app.models.emergency import NearbyHospital
from app.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/emergency", tags=["Emergency"])

_MAX_RADIUS_KM = 25.0
_MAX_LIMIT = 20


@router.get("/nearby-hospitals", response_model=list[NearbyHospital])
@limiter.limit(settings.RATE_LIMIT_NEARBY_HOSPITALS)
def nearby_hospitals(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(default=5.0, gt=0, le=_MAX_RADIUS_KM),
    limit: int = Query(default=10, ge=1, le=_MAX_LIMIT),
) -> list[NearbyHospital]:
    """
    Best-effort nearby-hospital lookup via OpenStreetMap (see
    app/emergency/hospital_lookup.py). Returns [] rather than an error
    if the lookup succeeds but finds nothing within range - an empty
    list is a normal, expected outcome in less-mapped areas, not a
    failure state the frontend needs to treat specially beyond showing
    "no results found."
    """
    try:
        return fetch_nearby_hospitals(lat, lon, radius_km, limit)
    except HospitalLookupError as exc:
        logger.warning("Nearby-hospitals lookup failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Couldn't reach the hospital lookup service right now. "
                "You can still call the emergency number or your emergency contact."
            ),
        )
