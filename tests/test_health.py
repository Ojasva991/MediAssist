def test_root_returns_project_info(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["project"] == "MediAssist AI"
    assert body["status"] == "Running"


def test_health_check_reports_healthy(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
