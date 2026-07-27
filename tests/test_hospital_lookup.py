from app.config import settings
from app.emergency.hospital_lookup import (
    HospitalLookupError,
    _element_coords,
    _force_ipv4_dns,
    _format_address,
    _haversine_km,
    fetch_nearby_hospitals,
)
import app.emergency.hospital_lookup as hospital_lookup
import socket


def test_haversine_zero_distance_for_same_point():
    assert _haversine_km(23.25, 77.41, 23.25, 77.41) == 0.0


def test_haversine_known_distance_roughly_correct():
    # Roughly 1 degree of latitude is ~111 km.
    d = _haversine_km(0.0, 0.0, 1.0, 0.0)
    assert 110 < d < 112


def test_element_coords_prefers_direct_lat_lon():
    element = {"lat": 1.0, "lon": 2.0, "center": {"lat": 9.0, "lon": 9.0}}
    assert _element_coords(element) == (1.0, 2.0)


def test_element_coords_falls_back_to_center():
    element = {"center": {"lat": 5.0, "lon": 6.0}}
    assert _element_coords(element) == (5.0, 6.0)


def test_element_coords_returns_none_when_missing():
    assert _element_coords({}) is None


def test_format_address_combines_available_parts():
    tags = {"addr:housenumber": "12", "addr:street": "MG Road", "addr:city": "Bhopal"}
    assert _format_address(tags) == "12, MG Road, Bhopal"


def test_format_address_returns_none_when_no_parts():
    assert _format_address({}) is None


def test_force_ipv4_dns_forces_af_inet_regardless_of_requested_family():
    calls = []
    original = socket.getaddrinfo

    def spy_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        calls.append(family)
        return []

    socket.getaddrinfo = spy_getaddrinfo
    try:
        with _force_ipv4_dns():
            # Even asking for "any family" (0) or explicitly AF_INET6
            # should come out as AF_INET once wrapped.
            socket.getaddrinfo("example.com", 443, family=socket.AF_INET6)
    finally:
        socket.getaddrinfo = original

    assert calls == [socket.AF_INET]


def test_force_ipv4_dns_restores_original_after_exception():
    original = socket.getaddrinfo
    try:
        with _force_ipv4_dns():
            raise ValueError("simulated failure inside the block")
    except ValueError:
        pass
    assert socket.getaddrinfo is original


def test_fetch_falls_back_to_next_endpoint_on_failure(monkeypatch):
    monkeypatch.setattr(
        settings, "OVERPASS_API_URLS", ["https://bad-mirror.example", "https://good-mirror.example"]
    )
    calls = []

    def fake_query(url, query):
        calls.append(url)
        if url == "https://bad-mirror.example":
            raise OSError("Connection refused")
        return {"elements": []}

    monkeypatch.setattr(hospital_lookup, "_query_one_endpoint", fake_query)
    # radius=20 is already at/above the widening threshold, so a lone
    # empty result here shouldn't trigger a second widened attempt -
    # keeps this test isolated to just the mirror-fallback behavior.
    result = fetch_nearby_hospitals(23.25, 77.41, 20, 10)
    assert result == []
    assert calls == ["https://bad-mirror.example", "https://good-mirror.example"]


def test_fetch_raises_only_when_all_endpoints_fail(monkeypatch):
    monkeypatch.setattr(
        settings, "OVERPASS_API_URLS", ["https://bad-one.example", "https://bad-two.example"]
    )

    def always_fail(url, query):
        raise OSError("Connection refused")

    monkeypatch.setattr(hospital_lookup, "_query_one_endpoint", always_fail)
    try:
        fetch_nearby_hospitals(23.25, 77.41, 5, 10)
        assert False, "expected HospitalLookupError"
    except HospitalLookupError as exc:
        assert "bad-one.example" in str(exc)
        assert "bad-two.example" in str(exc)


def test_fetch_widens_radius_once_when_first_attempt_is_empty(monkeypatch):
    monkeypatch.setattr(settings, "OVERPASS_API_URLS", ["https://mirror.example"])
    seen_radii = []

    def fake_query(url, query):
        # radius_km isn't directly in the query dict return, but we can
        # infer which attempt this is from call order.
        seen_radii.append(len(seen_radii))
        if len(seen_radii) == 1:
            return {"elements": []}  # first (narrow) attempt: nothing found
        return {
            "elements": [
                {"type": "node", "lat": 23.26, "lon": 77.42, "tags": {"name": "Wide Hospital"}}
            ]
        }

    monkeypatch.setattr(hospital_lookup, "_query_one_endpoint", fake_query)
    result = fetch_nearby_hospitals(23.25, 77.41, 5, 10)
    assert len(seen_radii) == 2  # confirms it retried once after an empty first result
    assert len(result) == 1
    assert result[0].name == "Wide Hospital"


def test_fetch_does_not_widen_when_already_at_or_above_threshold(monkeypatch):
    monkeypatch.setattr(settings, "OVERPASS_API_URLS", ["https://mirror.example"])
    calls = []

    def fake_query(url, query):
        calls.append(1)
        return {"elements": []}

    monkeypatch.setattr(hospital_lookup, "_query_one_endpoint", fake_query)
    result = fetch_nearby_hospitals(23.25, 77.41, 20, 10)
    assert len(calls) == 1  # no widening retry - already wide enough
    assert result == []
