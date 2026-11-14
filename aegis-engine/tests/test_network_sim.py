"""Unit tests for Phase 3 BGP Network Convergence Simulator."""

import pytest
from aegis.network_sim import (
    BGPConvergenceSimulator,
    NetworkSimConfig,
    ConvergenceTimeseries,
    NetworkEvaluationReport,
)


def test_network_simulator_reactive_loss_of_light():
    """Validates reactive cut simulation: blackholing and non-zero packet drops."""
    cfg = NetworkSimConfig(
        sim_duration_sec=180.0,
        time_step_sec=1.0,
        physical_cut_time_sec=60.0,
    )
    sim = BGPConvergenceSimulator(config=cfg)
    ts, report = sim.run_reactive_loss_of_light()

    assert isinstance(ts, ConvergenceTimeseries)
    assert isinstance(report, NetworkEvaluationReport)

    # Significant data loss must occur during the unannounced failure window
    assert report.total_data_lost_gigabytes > 0.0
    assert report.outage_duration_sec > 0.0
    assert report.peak_packet_drop_rate_pct == 100.0


def test_network_simulator_preemptive_evacuation():
    """Validates Aegis pre-emptive graceful shutdown: zero packet drops."""
    cfg = NetworkSimConfig(
        sim_duration_sec=180.0,
        time_step_sec=1.0,
        aegis_detection_time_sec=30.0,
        physical_cut_time_sec=60.0,
    )
    sim = BGPConvergenceSimulator(config=cfg)
    ts, report = sim.run_preemptive_aegis_evacuation()

    assert isinstance(ts, ConvergenceTimeseries)
    assert isinstance(report, NetworkEvaluationReport)

    # Pre-emptive graceful switchover before physical cut yields zero dropped packets
    assert report.total_data_lost_gigabytes == 0.0
    assert report.outage_duration_sec == 0.0
    assert report.peak_packet_drop_rate_pct == 0.0
    assert report.service_availability_pct == 100.0


def test_network_simulator_comparison_summary():
    """Validates delta summary generation."""
    sim = BGPConvergenceSimulator()
    summary = sim.generate_comparison_summary()

    assert "reactive" in summary
    assert "aegis_preemptive" in summary
    assert "impact_delta" in summary
    delta = summary["impact_delta"]
    assert delta["saved_data_loss_gigabytes"] > 0.0
    assert delta["saved_outage_downtime_sec"] > 0.0
    assert delta["packet_drop_reduction_pct"] == 100.0
