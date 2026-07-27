"""
Data models for the emergency-flow "nearby hospitals" feature
(GET /emergency/nearby-hospitals).
"""

from pydantic import BaseModel, Field


class NearbyHospital(BaseModel):
    """One hospital/clinic returned by the nearby-hospitals lookup."""

    name: str
    latitude: float
    longitude: float
    distance_km: float = Field(..., description="Straight-line distance from the queried point.")
    address: str | None = Field(default=None, description="Best-effort address from source tags.")
    phone: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "City General Hospital",
                "latitude": 23.2599,
                "longitude": 77.4126,
                "distance_km": 1.4,
                "address": "MG Road, Bhopal",
                "phone": None,
            }
        }
    }
