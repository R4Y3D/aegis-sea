"""Unit tests for Aegis-Sea Threat Scoring Engine."""

import time
import pytest
from aegis.cable_index import CableCorridorIndex
from aegis.config import Settings
from aegis.models import ThreatLevel, VesselTrackPoint
from aegis.scorer import ThreatScorer


@pytest.fixture(scope="module")
def cable_index():
    return CableCorridorIndex(auto_load=True)


@pytest.fixture
def custom_settings():
    return Settings(
        alert_horizon_nm=9.0,
        cpz_radius_nm=3.0,
        weight_proximity=30.0,
        weight_speed=20.0,
        weight_loiter=20.0,
        weight_heading=10.0,
        weight_anchor=10.0,
        weight_dark=10.0,
        threshold_critical=81.0,
        threshold_high=61.0,
        threshold_advisory=31.0,
    )


@pytest.fixture
def scorer(cable_index, custom_settings):
    return ThreatScorer(cable_index=cable_index, config=custom_settings)


def test_vessel_far_outside_alert_horizon(scorer):
    """Vessel in middle of Pacific Ocean far from indexed cable."""
    # (lat=0.0, lon=-160.0) is far from the indexed subsea cable network
    assessment = scorer.score_vessel(
        mmsi="999000001",
        lat=0.0,
        lon=-160.0,
        sog=14.0,
        cog=90.0,
        name="Cruising Pacific",
    )
    assert assessment.threat_score == 0.0
    assert assessment.threat_level == ThreatLevel.NORMAL
    assert assessment.recommended_action == "NONE"
    assert assessment.closest_cable is None or not assessment.closest_cable.in_alert_corridor


def test_vessel_cruising_safely_across_cable(scorer):
    """Vessel crossing C-Lion1 at 18 knots without lingering."""
    # Near C-Lion1 in Baltic Sea (~60.0N, 25.0E), but moving at normal transit speed (18 kn)
    assessment = scorer.score_vessel(
        mmsi="999000002",
        lat=60.05,
        lon=25.02,
        sog=18.0,
        cog=180.0,
        name="Fast Cargo",
    )
    # Proximity is nonzero, but speed score is ~0, loiter is 0, anchor is 0, dark is 0
    assert assessment.threat_level in [ThreatLevel.NORMAL, ThreatLevel.ADVISORY]
    assert assessment.threat_score < 50.0
    assert assessment.score_breakdown.s_speed < 0.01  # Sigmoid suppresses high speed
    assert assessment.score_breakdown.s_anchor == 0.0


def test_yi_peng_3_anchor_dragging_profile(scorer):
    """Simulates the Yi Peng 3 Baltic Sea profile (slow speed, anchor decel, inside CPZ)."""
    now = time.time()
    # Historic track: vessel cruising at 10.5 kn 8 minutes ago
    history = [
        VesselTrackPoint(
            lat=60.01,
            lon=25.00,
            sog=10.5,
            cog=200.0,
            timestamp_epoch=now - 480.0,
        ),
        VesselTrackPoint(
            lat=60.03,
            lon=25.01,
            sog=7.0,
            cog=200.0,
            timestamp_epoch=now - 240.0,
        ),
    ]

    # Current state: right on C-Lion1 (lat=60.05, lon=25.02), speed dropped to 1.2 kn,
    # heading aligned with cable, dwell time 45 min
    assessment = scorer.score_vessel(
        mmsi="412543000",
        lat=60.05,
        lon=25.02,
        sog=1.2,
        cog=205.0,
        name="Yi Peng 3 Simulated",
        history=history,
        current_time_epoch=now,
        entered_corridor_epoch=now - 2700.0,  # 45 min dwell
        last_seen_epoch=now,
    )

    assert assessment.closest_cable is not None
    assert assessment.closest_cable.in_cpz is True
    # Anchor catch signature should trigger because speed dropped from >6.0 to 1.2 in <600s inside CPZ
    assert assessment.score_breakdown.s_anchor == 1.0
    assert assessment.score_breakdown.s_speed > 0.8
    assert assessment.score_breakdown.s_loiter > 0.5
    # High or Critical threat score
    assert assessment.threat_score >= 60.0
    assert assessment.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]


def test_kinematic_jump_filter_spoofing(scorer):
    """Simulates GPS spoofing / teleportation jump > 35 knots."""
    now = time.time()
    # 30 seconds ago at (60.0, 25.0)
    history = [
        VesselTrackPoint(
            lat=60.0,
            lon=25.0,
            sog=1.0,
            cog=0.0,
            timestamp_epoch=now - 30.0,
        )
    ]

    # Current point 2.0 NM away in 30 seconds -> implied speed = 240 knots!
    # (0.0333 degrees latitude ~ 2.0 NM)
    assessment = scorer.score_vessel(
        mmsi="999000003",
        lat=60.0333,
        lon=25.0,
        sog=1.0,
        cog=0.0,
        name="Spoofed Teleport",
        history=history,
        current_time_epoch=now,
    )

    assert assessment.telemetry_trust.is_jump is True
    assert assessment.telemetry_trust.implied_speed_knots is not None
    assert assessment.telemetry_trust.implied_speed_knots > 100.0
    assert assessment.telemetry_trust.trust_score <= 0.3
    # Anchor score should be suppressed because of the jump
    assert assessment.score_breakdown.s_anchor == 0.0


def test_ghost_ship_candidate_and_failover_safety(scorer):
    """Ghost ship appearing abruptly in CPZ at dragging speed with zero history."""
    now = time.time()
    assessment = scorer.score_vessel(
        mmsi="999000004",
        lat=60.05,
        lon=25.02,
        sog=1.5,
        cog=0.0,
        name="Phantom Decoy",
        history=[],  # 0 history points
        current_time_epoch=now,
    )

    assert assessment.telemetry_trust.is_ghost_candidate is True
    assert assessment.closest_cable is not None


def test_loitering_progression(scorer):
    """Verifies that dwell time increases loiter score up to the 1-hour cap."""
    now = 1700000000.0
    s_0 = scorer._compute_loiter_score(now, None)
    s_15m = scorer._compute_loiter_score(now, now - 900.0)
    s_30m = scorer._compute_loiter_score(now, now - 1800.0)
    s_60m = scorer._compute_loiter_score(now, now - 3600.0)
    s_2h = scorer._compute_loiter_score(now, now - 7200.0)

    assert s_0 == 0.0
    assert pytest.approx(s_15m, 0.01) == 0.25
    assert pytest.approx(s_30m, 0.01) == 0.50
    assert pytest.approx(s_60m, 0.01) == 1.00
    assert s_2h == 1.00  # Clamped at 1.0


def test_dark_vessel_silence_penalty(scorer):
    """Verifies that transponder silence accumulates dark score up to 30 min cap."""
    now = 1700000000.0
    s_active = scorer._compute_dark_score(now, now - 30.0)       # 30s ago (normal AIS interval)
    s_15m = scorer._compute_dark_score(now, now - 900.0)         # 15m silence
    s_30m = scorer._compute_dark_score(now, now - 1800.0)        # 30m silence
    s_1h = scorer._compute_dark_score(now, now - 3600.0)         # 60m silence

    assert s_active == 0.0
    assert pytest.approx(s_15m, 0.01) == 0.50
    assert pytest.approx(s_30m, 0.01) == 1.00
    assert s_1h == 1.00


def test_heading_alignment_parallel_vs_perpendicular(scorer):
    """Verifies heading cosine: parallel is 1.0, perpendicular is 0.0."""
    cable_azimuth = 45.0
    parallel_same = scorer._compute_heading_score(45.0, cable_azimuth)
    parallel_opp = scorer._compute_heading_score(225.0, cable_azimuth)
    perp_1 = scorer._compute_heading_score(135.0, cable_azimuth)
    perp_2 = scorer._compute_heading_score(315.0, cable_azimuth)

    assert pytest.approx(parallel_same, 0.01) == 1.0
    assert pytest.approx(parallel_opp, 0.01) == 1.0
    assert pytest.approx(perp_1, 0.01) == 0.0
    assert pytest.approx(perp_2, 0.01) == 0.0


def test_invalid_coordinates_rejection(scorer):
    """Verifies out-of-bounds GPS coordinates are flagged invalid."""
    trust = scorer._evaluate_telemetry_trust(
        current_lat=95.0,  # Invalid latitude > 90
        current_lon=25.0,
        current_sog=10.0,
        current_epoch=1000.0,
        last_seen_epoch=1000.0,
        history=[],
    )
    assert trust.is_valid is False
    assert trust.trust_score == 0.0


def test_ghost_jump_failover_safety_mitigation(scorer):
    """If vessel has critical score but is a ghost jump, failover is held for verification."""
    from aegis.models import CableProximity, TelemetryTrust
    cable = CableProximity(
        cable_id="c-lion1",
        cable_name="C-Lion1",
        distance_nm=0.2,
        in_cpz=True,
        in_alert_corridor=True,
        s_prox=0.95,
        cable_azimuth_deg=45.0,
        nearest_lon=25.0,
        nearest_lat=60.0,
    )
    trust_spoofed = TelemetryTrust(is_ghost_candidate=True, is_jump=True)
    action, prefixes, backups = scorer._determine_mitigation(
        threat_level=ThreatLevel.CRITICAL,
        cable=cable,
        trust=trust_spoofed,
    )
    assert action == "VERIFY_GHOST_TARGET_BEFORE_FAILOVER"
    assert len(prefixes) == 0

    trust_legit = TelemetryTrust(is_ghost_candidate=False, is_jump=False)
    action_legit, prefixes_legit, backups_legit = scorer._determine_mitigation(
        threat_level=ThreatLevel.CRITICAL,
        cable=cable,
        trust=trust_legit,
    )
    assert action_legit == "TRIGGER_PREEMPTIVE_FAILOVER"
    assert len(prefixes_legit) > 0
    assert len(backups_legit) > 0

