"""Unit tests for Phase 3 Novelty Benchmark and Adversarial Evaluation Suite."""

import pytest
from aegis.cable_index import CableCorridorIndex
from aegis.benchmark import (
    NoveltyBenchmarkRunner,
    AdversarialDatasetGenerator,
    NaiveGeofenceDetector,
    KinematicMLAnomalyDetector,
    AegisZeroTrustEvaluator,
    TargetCategory,
)


@pytest.fixture(scope="module")
def cable_index():
    return CableCorridorIndex(auto_load=True)


@pytest.fixture
def dataset_gen():
    return AdversarialDatasetGenerator(seed=123)


def test_adversarial_dataset_generation(dataset_gen):
    """Generates synthetic fleet with proper class distributions."""
    fleet = dataset_gen.generate_fleet(
        n_benign_cruising=20,
        n_benign_harbor_tugs=5,
        n_benign_fishing=5,
        n_genuine_sabotage=5,
        n_spoof_gps_jump=5,
        n_spoof_slow_drift=3,
        n_ghost_swarms=2,
    )
    assert len(fleet) == 45
    sabotage = [s for s in fleet if s.category == TargetCategory.GENUINE_ANCHOR_DRAG]
    assert len(sabotage) == 5
    assert all(s.is_genuine_attack for s in sabotage)

    jumps = [s for s in fleet if s.category == TargetCategory.SPOOF_GPS_JUMP]
    assert len(jumps) == 5
    assert all(s.is_cyber_spoof for s in jumps)


def test_benchmark_runner_execution(cable_index, dataset_gen):
    """Runs novelty benchmark and verifies metrics calculation across all 3 detectors."""
    runner = NoveltyBenchmarkRunner(cable_index=cable_index)
    fleet = dataset_gen.generate_fleet(
        n_benign_cruising=30,
        n_benign_harbor_tugs=10,
        n_benign_fishing=10,
        n_genuine_sabotage=10,
        n_spoof_gps_jump=10,
        n_spoof_slow_drift=5,
        n_ghost_swarms=5,
    )
    metrics = runner.run_benchmark(dataset=fleet)

    assert "NaiveGeofence" in metrics
    assert "KinematicML" in metrics
    assert "AegisSea" in metrics

    aegis_metrics = metrics["AegisSea"]
    naive_metrics = metrics["NaiveGeofence"]

    # Aegis-Sea must achieve 100% recall on genuine sabotage
    assert aegis_metrics.recall == 1.0

    # Aegis-Sea must significantly outperform Naive Geofencing on accuracy and DoS resistance
    assert aegis_metrics.accuracy > naive_metrics.accuracy
    assert aegis_metrics.failover_dos_vulnerability_rate < naive_metrics.failover_dos_vulnerability_rate
    assert aegis_metrics.failover_dos_vulnerability_rate == 0.0


def test_markdown_table_generation(cable_index, dataset_gen):
    """Validates markdown table formatting."""
    runner = NoveltyBenchmarkRunner(cable_index=cable_index)
    fleet = dataset_gen.generate_fleet(
        n_benign_cruising=10,
        n_benign_harbor_tugs=5,
        n_benign_fishing=5,
        n_genuine_sabotage=5,
        n_spoof_gps_jump=5,
        n_spoof_slow_drift=2,
        n_ghost_swarms=2,
    )
    metrics = runner.run_benchmark(dataset=fleet)
    table_str = runner.generate_markdown_table(metrics)
    assert "| Detector Architecture |" in table_str
    assert "**AegisSea**" in table_str
    assert "**NaiveGeofence**" in table_str
