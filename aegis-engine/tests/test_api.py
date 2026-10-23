"""Integration tests for Aegis-Sea FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from aegis.main import app


@pytest.fixture(scope="module")
def client():
    """Module-scoped test client that runs the lifespan context once."""
    with TestClient(app) as test_client:
        yield test_client


def test_health_check_endpoint(client):
    """Verifies that /health returns loaded index statistics."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["cables_indexed"] == 712
    assert data["segments_indexed"] > 11000
    assert "vessels_monitored" in data


def test_overview_endpoint(client):
    """Verifies that /api/threats/overview returns fleet statistics."""
    response = client.get("/api/threats/overview")
    assert response.status_code == 200
    data = response.json()
    assert "monitored_vessels_total" in data
    assert "threats_critical_count" in data
    assert isinstance(data["threats"], list)


def test_evaluate_and_get_vessel_threat(client):
    """Evaluates a vessel and retrieves it via /api/threats/{mmsi}."""
    mmsi = "888777666"
    payload = {
        "mmsi": mmsi,
        "lat": 60.05,
        "lon": 25.02,
        "sog": 1.2,
        "cog": 205.0,
        "heading": 205.0,
        "name": "Baltic Evaluation Target",
        "imo": "9123456",
        "ship_type": "Bulk Carrier",
    }

    eval_resp = client.post("/api/evaluate", json=payload)
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["mmsi"] == mmsi
    assert eval_data["vessel_name"] == "Baltic Evaluation Target"
    assert eval_data["threat_score"] > 30.0
    assert eval_data["closest_cable"]["cable_id"] is not None

    # Retrieve specific vessel threat
    get_resp = client.get(f"/api/threats/{mmsi}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["mmsi"] == mmsi
    assert get_data["threat_score"] == eval_data["threat_score"]


def test_get_nonexistent_vessel_returns_404(client):
    """Queries an unmonitored MMSI and expects 404."""
    response = client.get("/api/threats/000000000")
    assert response.status_code == 404
    assert "not currently tracked" in response.json()["detail"]


def test_list_threats_filtering(client):
    """Tests /api/threats with corridor_only and min_level queries."""
    response = client.get("/api/threats?corridor_only=true")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for t in data:
        assert t["closest_cable"] is not None
        assert t["closest_cable"]["in_alert_corridor"] is True
