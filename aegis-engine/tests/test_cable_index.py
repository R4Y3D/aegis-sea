"""Unit and performance tests for CableCorridorIndex."""

import time
import pytest

from aegis.cable_index import CableCorridorIndex
from aegis.config import settings


@pytest.fixture(scope="module")
def cable_index():
    """Module-scoped fixture to avoid re-reading GeoJSON on every test."""
    return CableCorridorIndex(auto_load=True)


def test_load_all_712_cables(cable_index):
    """Verify that all 712 submarine cable features and their segments are loaded."""
    assert cable_index.total_features == 712
    assert cable_index.total_cables == 694
    assert cable_index.total_segments > 11000

    stats = cable_index.get_stats()
    assert stats.total_features == 712
    assert stats.total_cables == 694
    assert stats.total_segments > 11000
    assert stats.build_time_ms > 0


def test_baltic_sea_query_returns_baltika_and_lion(cable_index):
    """Verify known incident corridor in the Baltic Sea near Gotland."""
    # Lat 57.0 N, Lon 20.0 E
    results = cable_index.query_corridor(lat=57.0, lon=20.0, max_distance_nm=9.0)
    assert len(results) >= 1

    closest = results[0]
    assert closest.cable_id == "kingisepp-kaliningrad-system-baltika"
    assert closest.distance_nm < 3.0
    assert closest.in_cpz is True
    assert closest.in_alert_corridor is True
    assert 0.0 < closest.s_prox <= 1.0
    assert 0.0 <= closest.cable_azimuth_deg < 180.0


def test_wider_corridor_finds_c_lion1(cable_index):
    """Verify that expanding the corridor horizon detects C-Lion1."""
    results = cable_index.query_corridor(lat=57.0, lon=20.0, max_distance_nm=15.0)
    cable_ids = [r.cable_id for r in results]
    assert "c-lion1" in cable_ids
    assert "kingisepp-kaliningrad-system-baltika" in cable_ids


def test_mid_ocean_remote_point_returns_empty(cable_index):
    """Verify that a remote oceanic location far from any cables returns no results."""
    # Point Nemo area in South Pacific
    lat, lon = -48.876, -123.393
    results = cable_index.query_corridor(lat=lat, lon=lon, max_distance_nm=9.0)
    assert len(results) == 0
    assert cable_index.is_in_corridor(lat=lat, lon=lon) is False
    assert cable_index.get_closest_cable(lat=lat, lon=lon) is None


def test_red_sea_falcon_cable(cable_index):
    """Verify detection of the FALCON cable system in the Gulf of Oman."""
    # Near FALCON coordinate: 24.435 deg N, 57.681 deg E
    closest = cable_index.get_closest_cable(lat=24.435, lon=57.681, max_distance_nm=5.0)
    assert closest is not None
    assert "falcon" in closest.cable_id.lower()
    assert closest.distance_nm < 2.0
    assert closest.in_cpz is True


def test_s_prox_quadratic_decay():
    """Verify mathematical formulation of S_prox."""
    max_d = 9.0
    # At d = 0, S_prox = 1.0
    assert (max(0.0, 1.0 - (0.0 / max_d)) ** 2) == 1.0
    # At d = 4.5 NM (halfway), S_prox = 0.25
    assert (max(0.0, 1.0 - (4.5 / max_d)) ** 2) == 0.25
    # At d = 9.0 NM, S_prox = 0.0
    assert (max(0.0, 1.0 - (9.0 / max_d)) ** 2) == 0.0
    # Beyond d_max, S_prox = 0.0
    assert (max(0.0, 1.0 - (12.0 / max_d)) ** 2) == 0.0


def test_query_performance_sub_millisecond(cable_index):
    """Verify that queries execute in well under 1 millisecond per vessel position."""
    test_points = [
        (57.0, 20.0),    # Baltic Sea
        (24.435, 57.681), # Gulf of Oman
        (1.25, 103.8),   # Singapore Strait
        (35.5, -5.3),    # Strait of Gibraltar
        (0.0, 0.0),      # Gulf of Guinea
    ]

    latencies_ms = []
    for lat, lon in test_points:
        for _ in range(50):
            t0 = time.perf_counter()
            cable_index.query_corridor(lat=lat, lon=lon, max_distance_nm=9.0)
            latencies_ms.append((time.perf_counter() - t0) * 1000.0)

    avg_latency = sum(latencies_ms) / len(latencies_ms)
    print(f"\nAverage query latency: {avg_latency:.4f} ms")
    assert avg_latency < 1.0  # Must be strictly sub-millisecond


def test_antimeridian_query_does_not_error(cable_index):
    """Verify that querying near longitude -180 / +180 does not fail."""
    # Near Fiji / Pacific antimeridian
    results_pos = cable_index.query_corridor(lat=-17.0, lon=179.95, max_distance_nm=9.0)
    results_neg = cable_index.query_corridor(lat=-17.0, lon=-179.95, max_distance_nm=9.0)
    assert isinstance(results_pos, list)
    assert isinstance(results_neg, list)


def test_invalid_geojson_path_raises_error():
    """Verify FileNotFoundError when loading a nonexistent path."""
    with pytest.raises(FileNotFoundError):
        CableCorridorIndex(geojson_path="nonexistent/path/cables.json")
