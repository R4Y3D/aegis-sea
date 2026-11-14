"""Unit tests for Phase 4 Optical OTDR Cross-Layer Sensor Fusion."""

import pytest
from aegis.cable_index import CableCorridorIndex
from aegis.otdr_fusion import (
    OTDRTelemetrySimulator,
    OpticalEventSeverity,
    OTDREvent,
    CrossLayerFusionRecord,
)


@pytest.fixture(scope="module")
def cable_index():
    return CableCorridorIndex(auto_load=True)


@pytest.fixture
def otdr_sim(cable_index):
    return OTDRTelemetrySimulator(cable_index=cable_index)


def test_otdr_trace_generation_nominal(otdr_sim):
    """Generates nominal optical backscatter trace with repeater boosts."""
    trace = otdr_sim.generate_trace(
        cable_id="c-lion1",
        total_length_km=500.0,
        snag_location_km=None,
        points=100,
    )
    assert len(trace["distance_km"]) == 100
    assert len(trace["optical_power_dbm"]) == 100
    assert trace["detected_event"] is None


def test_otdr_trace_generation_snag_event(otdr_sim):
    """Detects localized microbending attenuation drop at snag location."""
    trace = otdr_sim.generate_trace(
        cable_id="c-lion1",
        total_length_km=500.0,
        snag_location_km=142.5,
        snag_attenuation_db=4.5,
        is_break=False,
        points=100,
    )
    assert trace["detected_event"] is not None
    event_dict = trace["detected_event"]
    assert event_dict["fiber_distance_km"] == 142.5
    assert event_dict["severity"] == OpticalEventSeverity.CRITICAL_SNAG.value
    assert event_dict["attenuation_drop_db"] == 4.5
    assert "event_lat" in event_dict and "event_lon" in event_dict


def test_otdr_trace_generation_break_event(otdr_sim):
    """Detects complete optical loss-of-light on severed fiber."""
    trace = otdr_sim.generate_trace(
        cable_id="c-lion1",
        total_length_km=500.0,
        snag_location_km=210.0,
        is_break=True,
        points=100,
    )
    event_dict = trace["detected_event"]
    assert event_dict["is_reflective_break"] is True
    assert event_dict["severity"] == OpticalEventSeverity.SEVERED_CUT.value


def test_cross_layer_correlation_high_confidence(otdr_sim):
    """High confidence attribution when surface ship is within 0.5 NM at dragging speed."""
    event = OTDREvent(
        cable_id="c-lion1",
        cable_name="C-Lion1 (Baltic Subsea Cable)",
        fiber_distance_km=142.5,
        attenuation_drop_db=4.8,
        severity=OpticalEventSeverity.CRITICAL_SNAG,
        timestamp_epoch=0.0,
        is_reflective_break=False,
        event_lat=59.5,
        event_lon=23.5,
    )
    # Ship at 59.502, 23.502 moving at 1.2 knots (distance < 0.2 NM)
    record: CrossLayerFusionRecord = otdr_sim.correlate_with_maritime_vessel(
        otdr_event=event,
        vessel_mmsi="412543000",
        vessel_name="Yi Peng 3",
        vessel_lat=59.502,
        vessel_lon=23.502,
        vessel_sog=1.2,
    )
    assert record.confidence_score >= 0.85
    assert "CONFIRMED" in record.attribution_verdict
    assert record.surface_distance_to_snag_nm <= 0.5


def test_cross_layer_correlation_dark_vessel(otdr_sim):
    """Flags possible dark vessel when optical strain has no nearby surface AIS target."""
    event = OTDREvent(
        cable_id="c-lion1",
        cable_name="C-Lion1 (Baltic Subsea Cable)",
        fiber_distance_km=142.5,
        attenuation_drop_db=4.8,
        severity=OpticalEventSeverity.CRITICAL_SNAG,
        timestamp_epoch=0.0,
        is_reflective_break=False,
        event_lat=59.5,
        event_lon=23.5,
    )
    # Ship 8 NM away
    record: CrossLayerFusionRecord = otdr_sim.correlate_with_maritime_vessel(
        otdr_event=event,
        vessel_mmsi="200111222",
        vessel_name="Distant Cargo",
        vessel_lat=59.63,
        vessel_lon=23.5,
        vessel_sog=12.0,
    )
    assert record.confidence_score < 0.30
    assert "DARK_VESSEL" in record.attribution_verdict
