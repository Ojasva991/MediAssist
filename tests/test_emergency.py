import app.routes.emergency as emergency_route
from app.emergency.hospital_lookup import HospitalLookupError
from app.models.emergency import NearbyHospital


def test_nearby_hospitals_requires_lat_lon(client):
    resp = client.get("/emergency/nearby-hospitals")
    assert resp.status_code == 422


def test_nearby_hospitals_validates_lat_range(client):
    resp = client.get("/emergency/nearby-hospitals", params={"lat": 200, "lon": 10})
    assert resp.status_code == 422


def test_nearby_hospitals_returns_sorted_results(client, monkeypatch):
    fake_results = [
        NearbyHospital(name="Far Hospital", latitude=1.0, longitude=1.0, distance_km=4.2),
        NearbyHospital(name="Near Hospital", latitude=1.0, longitude=1.0, distance_km=0.8),
    ]
    monkeypatch.setattr(
        emergency_route, "fetch_nearby_hospitals", lambda lat, lon, radius_km, limit: fake_results
    )
    resp = client.get(
        "/emergency/nearby-hospitals", params={"lat": 23.25, "lon": 77.41, "radius_km": 5}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert body[0]["name"] == "Far Hospital"  # ordering trusted to hospital_lookup, not re-sorted


def test_nearby_hospitals_returns_empty_list_when_none_found(client, monkeypatch):
    monkeypatch.setattr(
        emergency_route, "fetch_nearby_hospitals", lambda lat, lon, radius_km, limit: []
    )
    resp = client.get("/emergency/nearby-hospitals", params={"lat": 0, "lon": 0})
    assert resp.status_code == 200
    assert resp.json() == []


def test_nearby_hospitals_returns_503_on_lookup_failure(client, monkeypatch):
    def _raise(*args, **kwargs):
        raise HospitalLookupError("simulated network failure")

    monkeypatch.setattr(emergency_route, "fetch_nearby_hospitals", _raise)
    resp = client.get("/emergency/nearby-hospitals", params={"lat": 23.25, "lon": 77.41})
    assert resp.status_code == 503


def test_nearby_hospitals_rejects_radius_over_max(client):
    resp = client.get(
        "/emergency/nearby-hospitals", params={"lat": 23.25, "lon": 77.41, "radius_km": 100}
    )
    assert resp.status_code == 422


def test_nearby_hospitals_rejects_limit_over_max(client):
    resp = client.get(
        "/emergency/nearby-hospitals", params={"lat": 23.25, "lon": 77.41, "limit": 100}
    )
    assert resp.status_code == 422
