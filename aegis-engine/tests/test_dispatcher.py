"""Unit and integration tests for Aegis-Sea AlertDispatcher and BGP incident response."""

import pytest
import httpx
from fastapi.testclient import TestClient

from aegis.config import Settings
from aegis.dispatcher import AlertDispatcher
from aegis.main import app
from aegis.models import (
    CableProximity,
    DispatchStatus,
    ManualDispatchRequest,
    TelemetryTrust,
    ThreatAssessment,
    ThreatLevel,
)


@pytest.fixture
def sample_critical_assessment() -> ThreatAssessment:
    """Fixture producing a verified anchor dragging threat assessment."""
    return ThreatAssessment(
        event_id="aegis-test-412543000-01",
        mmsi="412543000",
        vessel_name="Yi Peng 3 (Simulated)",
        coordinates={"lat": 60.05, "lon": 25.02},
        sog_knots=1.2,
        cog_degrees=205.0,
        threat_score=85.0,
        threat_level=ThreatLevel.CRITICAL,
        closest_cable=CableProximity(
            cable_id="c-lion1",
            cable_name="C-Lion1 (Baltic Subsea Cable)",
            distance_nm=0.4,
            in_cpz=True,
            in_alert_corridor=True,
            s_prox=0.95,
            cable_azimuth_deg=25.0,
            nearest_lat=60.052,
            nearest_lon=25.025,
        ),
        telemetry_trust=TelemetryTrust(
            is_valid=True,
            is_jump=False,
            is_ghost_candidate=False,
            trust_score=1.0,
        ),
        recommended_action="TRIGGER_PREEMPTIVE_FAILOVER",
        affected_bgp_prefixes=["194.100.45.0/24"],
        backup_transit_paths=["backup-terrestrial-helsinki-stockholm"],
    )


@pytest.fixture
def sample_ghost_decoy_assessment() -> ThreatAssessment:
    """Fixture producing a phantom ghost decoy threat assessment."""
    return ThreatAssessment(
        event_id="aegis-test-999000103-01",
        mmsi="999000103",
        vessel_name="Phantom Ghost Contact",
        coordinates={"lat": 60.05, "lon": 25.02},
        sog_knots=1.5,
        cog_degrees=0.0,
        threat_score=82.0,
        threat_level=ThreatLevel.CRITICAL,
        closest_cable=CableProximity(
            cable_id="c-lion1",
            cable_name="C-Lion1 (Baltic Subsea Cable)",
            distance_nm=0.3,
            in_cpz=True,
            in_alert_corridor=True,
            s_prox=0.98,
            cable_azimuth_deg=25.0,
            nearest_lat=60.052,
            nearest_lon=25.025,
        ),
        telemetry_trust=TelemetryTrust(
            is_valid=True,
            is_jump=True,
            is_ghost_candidate=True,
            trust_score=0.4,
        ),
        recommended_action="VERIFY_GHOST_TARGET_BEFORE_FAILOVER",
    )


@pytest.fixture
def sample_spoofed_jump_assessment() -> ThreatAssessment:
    """Fixture producing an SDR spoofed jump threat assessment."""
    return ThreatAssessment(
        event_id="aegis-test-999000102-01",
        mmsi="999000102",
        vessel_name="SDR Spoofed Fix",
        coordinates={"lat": 60.0333, "lon": 25.0},
        sog_knots=1.0,
        cog_degrees=90.0,
        threat_score=46.8,
        threat_level=ThreatLevel.ADVISORY,
        closest_cable=CableProximity(
            cable_id="c-lion1",
            cable_name="C-Lion1 (Baltic Subsea Cable)",
            distance_nm=0.8,
            in_cpz=True,
            in_alert_corridor=True,
            s_prox=0.88,
            cable_azimuth_deg=25.0,
            nearest_lat=60.052,
            nearest_lon=25.025,
        ),
        telemetry_trust=TelemetryTrust(
            is_valid=True,
            is_jump=True,
            implied_speed_knots=239.8,
            trust_score=0.3,
        ),
        recommended_action="INCREASE_MONITORING_FREQUENCY",
    )


def test_soar_payload_generation(sample_critical_assessment):
    """Verifies standard SOAR alert formatting."""
    dispatcher = AlertDispatcher()
    soar = dispatcher.build_soar_payload(sample_critical_assessment)

    assert soar.event_id == sample_critical_assessment.event_id
    assert soar.severity == "CRITICAL"
    assert soar.action == "TRIGGER_PREEMPTIVE_FAILOVER"
    assert soar.vessel_mmsi == "412543000"
    assert soar.cable_id == "c-lion1"
    assert "CRITICAL ANCHOR DRAG THREAT" in soar.incident_summary
    assert soar.telemetry_trust.is_valid is True


def test_bgp_evacuation_critical_anchor_drag(sample_critical_assessment):
    """Verifies pre-emptive BGP evacuation payload for genuine physical attack."""
    dispatcher = AlertDispatcher()
    bgp = dispatcher.build_bgp_evacuation_payload(sample_critical_assessment)

    assert bgp.cable_id == "c-lion1"
    assert bgp.action == "PREEMPTIVE_EVACUATION"
    assert bgp.status == "ARMED_PREEMPTIVE"
    assert "65000:666" in bgp.bgp_community
    assert bgp.affected_prefixes == ["194.100.45.0/24"]
    assert "backup-terrestrial-helsinki-stockholm" in bgp.backup_transit_paths
    assert bgp.estimated_switchover_ms == 450


def test_bgp_evacuation_ghost_decoy_hold(sample_ghost_decoy_assessment):
    """Verifies route failover is withheld for phantom ghost decoys to prevent failover DoS."""
    dispatcher = AlertDispatcher()
    bgp = dispatcher.build_bgp_evacuation_payload(sample_ghost_decoy_assessment)

    assert bgp.cable_id == "c-lion1"
    assert bgp.action == "FAILOVER_HOLD"
    assert bgp.status == "HELD_UNVERIFIED_DECOY"
    assert "HELD" in bgp.bgp_community


def test_bgp_evacuation_spoofed_jump_suppression(sample_spoofed_jump_assessment):
    """Verifies BGP failover is completely suppressed on impossible GPS velocity jumps."""
    dispatcher = AlertDispatcher()
    bgp = dispatcher.build_bgp_evacuation_payload(sample_spoofed_jump_assessment)

    assert bgp.action == "SUPPRESSED"
    assert bgp.status == "SUPPRESSED_SPOOF"


@pytest.mark.asyncio
async def test_simulated_dispatch_and_history(sample_critical_assessment):
    """Verifies dispatch in simulation mode records to audit history."""
    dispatcher = AlertDispatcher()
    dispatcher.clear_history()

    record = await dispatcher.dispatch(sample_critical_assessment)

    assert record.status == DispatchStatus.SIMULATED
    assert record.mmsi == "412543000"
    assert record.threat_level == ThreatLevel.CRITICAL
    assert record.soar_payload is not None
    assert record.bgp_payload is not None
    assert record.bgp_payload.status == "ARMED_PREEMPTIVE"

    history = dispatcher.get_history()
    assert len(history) == 1
    assert history[0].dispatch_id == record.dispatch_id


@pytest.mark.asyncio
async def test_dispatcher_cooldown_deduplication(sample_critical_assessment):
    """Verifies alert cooldown suppresses duplicate alerts unless forced."""
    config = Settings(alert_cooldown_seconds=60.0)
    dispatcher = AlertDispatcher(config=config)
    dispatcher.clear_history()

    # First dispatch succeeds
    rec1 = await dispatcher.dispatch(sample_critical_assessment)
    assert rec1.status == DispatchStatus.SIMULATED

    # Immediate second dispatch is suppressed by cooldown
    rec2 = await dispatcher.dispatch(sample_critical_assessment)
    assert rec2.status == DispatchStatus.SUPPRESSED_COOLDOWN

    # Forced dispatch bypasses cooldown
    rec3 = await dispatcher.dispatch(sample_critical_assessment, force=True)
    assert rec3.status == DispatchStatus.SIMULATED


@pytest.mark.asyncio
async def test_dispatcher_remote_webhook_delivery(sample_critical_assessment):
    """Verifies live HTTP webhook transmission with mock client."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"received": True})

    transport = httpx.MockTransport(handler)
    mock_client = httpx.AsyncClient(transport=transport)

    config = Settings(soar_webhook_url="https://soar.internal.cyber.fordham.edu/webhook")
    dispatcher = AlertDispatcher(config=config, client=mock_client)

    record = await dispatcher.dispatch(sample_critical_assessment)
    assert record.status == DispatchStatus.DISPATCHED
    assert record.target_webhook == "https://soar.internal.cyber.fordham.edu/webhook"


def test_api_alert_history_endpoints():
    """Verifies FastAPI /api/alerts endpoints with TestClient."""
    with TestClient(app) as client:
        # Clear history first
        resp = client.post("/api/alerts/clear")
        assert resp.status_code == 200
        assert resp.json()["status"] == "cleared"

        # Check history is empty
        resp = client.get("/api/alerts/history")
        assert resp.status_code == 200
        assert resp.json() == []

        # Ingest a vessel to create state
        ingest_payload = {
            "mmsi": "412543000",
            "lat": 60.05,
            "lon": 25.02,
            "sog": 1.2,
            "cog": 205.0,
            "name": "Yi Peng 3",
        }
        resp = client.post("/api/evaluate", json=ingest_payload)
        assert resp.status_code == 200

        # Trigger manual dispatch
        resp = client.post("/api/alerts/dispatch", json={"mmsi": "412543000", "force": True})
        assert resp.status_code == 200
        record = resp.json()
        assert record["mmsi"] == "412543000"
        assert record["status"] in ("SIMULATED", "DISPATCHED")

        # Verify audit history
        resp = client.get("/api/alerts/history")
        assert resp.status_code == 200
        history = resp.json()
        assert len(history) >= 1
        assert history[0]["mmsi"] == "412543000"
