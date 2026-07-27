"""
Nearby-hospital lookup for the emergency SOS flow.

Uses OpenStreetMap's public Overpass API - deliberately NOT Google
Places or any other API that requires a key/billing account, same
"no new paid service/credentials without asking first" reasoning this
project already applies elsewhere (see the Health Passport document
storage tradeoff notes in app/storage/document_store.py). Overpass is
free, requires no API key, and is queried server-side only (never from
the browser), same pattern as every other external call in this app
(Gemini, WHO ingestion).

This is a best-effort convenience lookup, not a guarantee of accuracy
or completeness - OpenStreetMap data quality varies by region. The SOS
page's actual emergency-calling flow (tel: links) does not depend on
this in any way; if this lookup fails or returns nothing, the person
can still call the emergency number and their emergency contact.
"""

import logging
import math
import socket
from contextlib import contextmanager
from urllib.error import URLError
from urllib.request import Request, urlopen
import json

from app.config import settings
from app.models.emergency import NearbyHospital

logger = logging.getLogger(__name__)


class HospitalLookupError(Exception):
    """Raised when the Overpass API can't be reached or returns bad data."""


@contextmanager
def _force_ipv4_dns():
    """
    Forces socket.getaddrinfo to only return IPv4 addresses for the
    duration of the wrapped block.

    Why this exists: some hosting platforms (Render's free tier among
    them) have no working outbound IPv6 route in their containers, but
    Python's urlopen doesn't fall back to IPv4 when DNS hands it an
    IPv6 address first - it just fails with
    "OSError: [Errno 101] Network is unreachable" and gives up, even
    though the same host is perfectly reachable over IPv4. This is a
    real, observed failure mode (see the Overpass 503s in production
    logs), not a hypothetical - hence working around it explicitly
    here rather than assuming a bare urlopen() call is enough.
    """
    original_getaddrinfo = socket.getaddrinfo

    def _ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
        return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

    socket.getaddrinfo = _ipv4_only
    try:
        yield
    finally:
        socket.getaddrinfo = original_getaddrinfo


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0  # Earth's mean radius in km
    p1, p2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(d_lambda / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _build_query(lat: float, lon: float, radius_km: float) -> str:
    radius_m = int(radius_km * 1000)
    # amenity=hospital covers the standard OSM tag for hospitals/ERs.
    # out center gives a usable lat/lon for ways/relations (buildings/
    # campuses mapped as areas, not just points) via their centroid.
    return f"""
        [out:json][timeout:20];
        (
          node["amenity"="hospital"](around:{radius_m},{lat},{lon});
          way["amenity"="hospital"](around:{radius_m},{lat},{lon});
          relation["amenity"="hospital"](around:{radius_m},{lat},{lon});
        );
        out center tags;
    """.strip()


def _element_coords(element: dict) -> tuple[float, float] | None:
    if "lat" in element and "lon" in element:
        return element["lat"], element["lon"]
    center = element.get("center")
    if center and "lat" in center and "lon" in center:
        return center["lat"], center["lon"]
    return None


def _format_address(tags: dict) -> str | None:
    parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:city") or tags.get("addr:suburb"),
    ]
    parts = [p for p in parts if p]
    return ", ".join(parts) if parts else None


def _query_one_endpoint(url: str, query: str) -> dict:
    request = Request(
        url,
        data=f"data={query}".encode(),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Vaeda-emergency-lookup/1.0 (contact via GitHub repo)",
        },
    )
    with _force_ipv4_dns(), urlopen(request, timeout=20) as response:
        return json.loads(response.read())


def fetch_nearby_hospitals(
    lat: float, lon: float, radius_km: float, limit: int
) -> list[NearbyHospital]:
    """
    Queries Overpass for hospitals within `radius_km` of (lat, lon),
    returns up to `limit` results sorted nearest-first.

    Tries each URL in settings.OVERPASS_API_URLS in order, moving to
    the next on failure - some public mirrors block/rate-limit shared
    hosting IPs (see settings.OVERPASS_API_URLS's comment), so treating
    this as "try several, not just one" is the actual fix, not just a
    nice-to-have.

    Raises HospitalLookupError only if every configured endpoint fails
    - callers (see app/routes/emergency.py) turn that into a 503, never
    a crash, since this is a convenience feature layered on top of an
    emergency page that must keep working regardless.
    """
    query = _build_query(lat, lon, radius_km)
    errors: list[str] = []

    for url in settings.OVERPASS_API_URLS:
        try:
            payload = _query_one_endpoint(url, query)
            break
        except (URLError, OSError, TimeoutError, json.JSONDecodeError) as exc:
            logger.warning("Overpass endpoint %s failed: %s", url, exc)
            errors.append(f"{url}: {exc}")
    else:
        raise HospitalLookupError(
            f"All {len(settings.OVERPASS_API_URLS)} Overpass endpoint(s) failed: "
            + "; ".join(errors)
        )

    elements = payload.get("elements", [])
    results: list[NearbyHospital] = []
    for element in elements:
        coords = _element_coords(element)
        if coords is None:
            continue
        el_lat, el_lon = coords
        tags = element.get("tags", {})
        name = tags.get("name") or "Unnamed hospital"
        distance = _haversine_km(lat, lon, el_lat, el_lon)
        results.append(
            NearbyHospital(
                name=name,
                latitude=el_lat,
                longitude=el_lon,
                distance_km=round(distance, 2),
                address=_format_address(tags),
                phone=tags.get("phone") or tags.get("contact:phone"),
            )
        )

    results.sort(key=lambda h: h.distance_km)
    return results[:limit]
