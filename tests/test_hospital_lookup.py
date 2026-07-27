from app.emergency.hospital_lookup import (
    _element_coords,
    _force_ipv4_dns,
    _format_address,
    _haversine_km,
)
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
