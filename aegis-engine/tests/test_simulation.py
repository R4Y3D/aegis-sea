"""Unit tests for Aegis-Sea Red Team Simulation Testbed."""

import pytest
from aegis.cable_index import CableCorridorIndex
from aegis.simulation import SimulationRunner, NaiveGeofenceDetector


@pytest.fixture(scope="module")
def cable_index():
    return CableCorridorIndex(auto_load=True)


@pytest.fixture
def runner(cable_index):
    return SimulationRunner(cable_index=cable_index)


def test_naive_detector_cpz_dragging(cable_index):
    """Naive geofence flags any vessel in CPZ at slow speed."""
    naive = NaiveGeofenceDetector(cable_index=cable_index)
    res = naive.evaluate(lat=60.05, lon=25.02, sog=1.2)
    assert res["alarm_triggered"] is True
    assert res["threat_level"] == "CRITICAL"
    assert res["recommended_action"] == "TRIGGER_PREEMPTIVE_FAILOVER"


def test_simulation_scenario_1_anchor_dragging(runner):
    """Scenario 1: True positive detected by both systems."""
    res = runner.run_scenario_1_anchor_dragging()
    assert "TRUE_POSITIVE" in res["naive"]["verdict"]
    assert "TRUE_POSITIVE" in res["aegis"]["verdict"]
    assert res["aegis"]["threat_score"] >= 60.0


def test_simulation_scenario_2_spoofed_jump(runner):
    """Scenario 2: Naive detector fooled; Aegis-Sea suppresses false alarm."""
    res = runner.run_scenario_2_gps_teleportation_jump()
    assert "FALSE_POSITIVE" in res["naive"]["verdict"]
    assert "FALSE_ALARM_SUPPRESSED" in res["aegis"]["verdict"]
    assert "FLAGGED_JUMP" in res["aegis"]["trust_status"]


def test_simulation_scenario_3_ghost_decoy(runner):
    """Scenario 3: Naive detector triggers failover; Aegis-Sea holds for verification."""
    res = runner.run_scenario_3_ghost_ship_decoy()
    assert "FALSE_POSITIVE" in res["naive"]["verdict"]
    assert "FAILOVER_HELD" in res["aegis"]["verdict"]
    assert res["aegis"]["trust_status"] == "GHOST_CANDIDATE_FLAGGED"


def test_simulation_run_all(runner):
    """Runs all 3 scenarios and validates summary outputs."""
    results = runner.run_all()
    assert len(results) == 3
    assert all("id" in r and "aegis" in r and "naive" in r for r in results)
