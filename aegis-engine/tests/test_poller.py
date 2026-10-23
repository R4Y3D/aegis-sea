"""Unit tests for Aegis-Sea AIS Telemetry Poller."""

import pytest
import httpx
from aegis.cable_index import CableCorridorIndex
from aegis.config import Settings
from aegis.models import ThreatLevel
from aegis.scorer import ThreatScorer
from aegis.poller import AISPoller


@pytest.fixture(scope="module")
def cable_index():
    return CableCorridorIndex(auto_load=True)


@pytest.fixture
def poller(cable_index):
    settings = Settings(
        alert_horizon_nm=9.0,
        cpz_radius_nm=3.0,
        node_server_url="http://mock-node:4173",
    )
    scorer = ThreatScorer(cable_index=cable_index, config=settings)
    return AISPoller(scorer=scorer, config=settings, max_track_samples=10)


def test_ingest_and_track_buffer(poller):
    """Verifies that sequential telemetry updates build a bounded ring buffer."""
    mmsi = "111222333"
    t0 = 1700000000.0

    # Ingest 15 points (buffer limit is 10)
    for i in range(15):
        poller.ingest_vessel_telemetry(
            mmsi=mmsi,
            lat=60.0 + (i * 0.001),
            lon=25.0 + (i * 0.001),
            sog=12.0,
            cog=45.0,
            timestamp_epoch=t0 + (i * 30.0),
        )

    assessment = poller.get_assessment(mmsi)
    assert assessment is not None
    assert assessment.mmsi == mmsi

    cached = poller._vessels[mmsi]
    assert len(cached.track_history) == 10  # Bounded to max_track_samples
    assert cached.track_history[-1].timestamp_epoch == t0 + (14 * 30.0)


def test_corridor_dwell_tracking(poller):
    """Verifies that entering corridor stamps entered_corridor_epoch and exiting resets it."""
    mmsi = "222333444"
    t0 = 1700000000.0

    # Point 1: Inside C-Lion1 corridor in Baltic Sea
    a1 = poller.ingest_vessel_telemetry(
        mmsi=mmsi,
        lat=60.05,
        lon=25.02,
        sog=3.0,
        cog=0.0,
        timestamp_epoch=t0,
    )
    cached = poller._vessels[mmsi]
    assert cached.entered_corridor_epoch == t0

    # Point 2: 10 minutes later, still inside corridor
    a2 = poller.ingest_vessel_telemetry(
        mmsi=mmsi,
        lat=60.051,
        lon=25.021,
        sog=3.0,
        cog=0.0,
        timestamp_epoch=t0 + 600.0,
    )
    cached = poller._vessels[mmsi]
    assert cached.entered_corridor_epoch == t0  # Preserved original entry time
    assert a2.score_breakdown.s_loiter > 0.1

    # Point 3: Teleports far out to middle of Pacific Ocean (outside corridor)
    a3 = poller.ingest_vessel_telemetry(
        mmsi=mmsi,
        lat=0.0,
        lon=-160.0,
        sog=15.0,
        cog=90.0,
        timestamp_epoch=t0 + 1200.0,
    )
    cached = poller._vessels[mmsi]
    assert cached.entered_corridor_epoch is None


def test_overview_aggregation(poller):
    """Verifies overview counts and threat level filtering."""
    # Vessel 1: Safe transit outside corridor
    poller.ingest_vessel_telemetry(
        mmsi="100000001",
        lat=0.0,
        lon=-160.0,
        sog=14.0,
        cog=90.0,
    )
    # Vessel 2: Loitering right over C-Lion1
    poller.ingest_vessel_telemetry(
        mmsi="100000002",
        lat=60.05,
        lon=25.02,
        sog=1.2,
        cog=205.0,
    )

    overview = poller.get_overview()
    assert overview.monitored_vessels_total >= 2
    assert overview.corridor_vessels_total >= 1
    assert overview.threats_normal_count >= 1

    all_corridor = poller.get_all_assessments(only_in_corridor=True)
    assert all(a.closest_cable and a.closest_cable.in_alert_corridor for a in all_corridor)


@pytest.mark.asyncio
async def test_poll_once_success_mock(poller, monkeypatch):
    """Verifies poll_once successfully parses Node.js JSON payload."""
    mock_payload = {
        "rows": [
            {
                "mmsi": "555666777",
                "lat": 60.05,
                "lon": 25.02,
                "speed": 2.5,
                "course": 180.0,
                "heading": 180.0,
                "name": "Baltic Carrier",
                "imo": "9876543",
                "type": "Cargo",
                "last_position_epoch": 1700000100.0,
            }
        ],
        "source": "AISStream",
        "status": "live",
    }

    async def mock_get(self, url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(200, json=mock_payload, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    count = await poller.poll_once()
    assert count == 1
    assert poller._last_poll_status == "OK"

    assessment = poller.get_assessment("555666777")
    assert assessment is not None
    assert assessment.vessel_name == "Baltic Carrier"
    assert assessment.sog_knots == 2.5


@pytest.mark.asyncio
async def test_poll_once_connection_error_graceful(poller, monkeypatch):
    """Verifies poll_once handles connection errors without crashing."""
    async def mock_get_error(self, url, **kwargs):
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get_error)

    count = await poller.poll_once()
    assert count == 0
    assert poller._last_poll_status == "UNREACHABLE"
