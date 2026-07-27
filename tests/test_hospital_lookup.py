from app.emergency.hospital_lookup import _element_coords, _format_address, _haversine_km


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
