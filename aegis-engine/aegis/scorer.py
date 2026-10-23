"""Aegis-Sea 6-Factor Threat Scoring Engine with Telemetry Trust Layer."""

import math
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict
from aegis.config import settings, Settings
from aegis.cable_index import CableCorridorIndex
from aegis.models import (
    CableProximity,
    FactorScores,
    TelemetryTrust,
    ThreatAssessment,
    ThreatLevel,
    VesselTrackPoint,
)


class ThreatScorer:
    """Evaluates multi-factor maritime risk scores against subsea cable corridors."""

    def __init__(
        self,
        cable_index: CableCorridorIndex,
        config: Optional[Settings] = None,
    ):
        self.cable_index = cable_index
        self.config = config or settings

    def score_vessel(
        self,
        mmsi: str,
        lat: float,
        lon: float,
        sog: float,
        cog: float,
        heading: Optional[float] = None,
        name: str = "Unknown Vessel",
        imo: Optional[str] = None,
        ship_type: Optional[str] = None,
        history: Optional[List[VesselTrackPoint]] = None,
        current_time_epoch: Optional[float] = None,
        entered_corridor_epoch: Optional[float] = None,
        last_seen_epoch: Optional[float] = None,
    ) -> ThreatAssessment:
        """Computes a full ThreatAssessment for a vessel contact."""
        now = current_time_epoch or datetime.now(timezone.utc).timestamp()
        last_seen = last_seen_epoch or now

        # Step 1: Telemetry Trust Layer (Adversarial Spoofing & Jump Filter)
        trust = self._evaluate_telemetry_trust(
            current_lat=lat,
            current_lon=lon,
            current_sog=sog,
            current_epoch=now,
            last_seen_epoch=last_seen,
            history=history or [],
        )

        # Step 2: Spatial Query against Subsea Cable Corridor
        closest_cable = self.cable_index.get_closest_cable(
            lat=lat,
            lon=lon,
            max_distance_nm=self.config.alert_horizon_nm,
        )

        # If beyond the 9 NM alert horizon, vessel is outside all danger zones
        if closest_cable is None or not closest_cable.in_alert_corridor:
            return ThreatAssessment(
                event_id=f"aegis-{mmsi}-{int(now)}",
                mmsi=mmsi,
                vessel_name=name,
                imo=imo,
                ship_type=ship_type,
                coordinates={"lat": lat, "lon": lon},
                sog_knots=round(sog, 2),
                cog_degrees=round(cog, 2),
                heading_degrees=round(heading, 2) if heading is not None else None,
                threat_score=0.0,
                threat_level=ThreatLevel.NORMAL,
                closest_cable=closest_cable,
                score_breakdown=FactorScores(),
                telemetry_trust=trust,
                recommended_action="NONE",
            )

        # Step 3: Compute all 6 Individual Threat Factors [0.0, 1.0]
        s_prox = closest_cable.s_prox
        s_speed = self._compute_speed_score(sog)
        s_loiter = self._compute_loiter_score(now, entered_corridor_epoch)
        s_heading = self._compute_heading_score(cog, closest_cable.cable_azimuth_deg)
        s_anchor = self._compute_anchor_score(
            sog=sog,
            in_cpz=closest_cable.in_cpz,
            history=history or [],
            now_epoch=now,
        )
        s_dark = self._compute_dark_score(now, last_seen)

        # Telemetry Trust Mitigation: If flagged for an impossible kinematic jump,
        # discount anchor drop score to prevent spoofed false alarms
        if trust.is_jump:
            s_anchor = 0.0

        factors = FactorScores(
            s_prox=round(s_prox, 4),
            s_speed=round(s_speed, 4),
            s_loiter=round(s_loiter, 4),
            s_heading=round(s_heading, 4),
            s_anchor=round(s_anchor, 4),
            s_dark=round(s_dark, 4),
        )

        # Step 4: Composite Weighted Summation T in [0, 100]
        raw_score = (
            self.config.weight_proximity * s_prox
            + self.config.weight_speed * s_speed
            + self.config.weight_loiter * s_loiter
            + self.config.weight_heading * s_heading
            + self.config.weight_anchor * s_anchor
            + self.config.weight_dark * s_dark
        )
        threat_score = round(min(100.0, max(0.0, raw_score)), 2)

        # Step 5: Classify into Threat Level
        threat_level = self._classify_threat_level(threat_score)

        # Step 6: Generate Recommended Action & Cross-Layer Mitigation Paths
        recommended_action, bgp_prefixes, backup_paths = self._determine_mitigation(
            threat_level=threat_level,
            cable=closest_cable,
            trust=trust,
        )

        return ThreatAssessment(
            event_id=f"aegis-{mmsi}-{int(now)}",
            mmsi=mmsi,
            vessel_name=name,
            imo=imo,
            ship_type=ship_type,
            coordinates={"lat": lat, "lon": lon},
            sog_knots=round(sog, 2),
            cog_degrees=round(cog, 2),
            heading_degrees=round(heading, 2) if heading is not None else None,
            threat_score=threat_score,
            threat_level=threat_level,
            closest_cable=closest_cable,
            score_breakdown=factors,
            telemetry_trust=trust,
            recommended_action=recommended_action,
            affected_bgp_prefixes=bgp_prefixes,
            backup_transit_paths=backup_paths,
        )

    # -------------------------------------------------------------------------
    # Factor Computation Formulations
    # -------------------------------------------------------------------------

    def _compute_speed_score(self, sog: float) -> float:
        """Kinematic Speed Anomaly via Logistic Sigmoid.

        S_speed(v) = 1 / (1 + exp(k_s * (v_sog - v_mid)))
        Anchor-dragging velocities (1.0 - 3.5 kn) score > 0.65; cruising (15 kn) scores ~0.0.
        """
        exponent = self.config.speed_steepness * (sog - self.config.speed_midpoint_knots)
        # Numerical clamp to prevent float overflow
        exponent = max(-30.0, min(30.0, exponent))
        return 1.0 / (1.0 + math.exp(exponent))

    def _compute_loiter_score(
        self, now_epoch: float, entered_corridor_epoch: Optional[float]
    ) -> float:
        """Quantifies dwell time inside the cable alert corridor.

        S_loiter = min(1.0, (t_now - t_enter) / tau_loiter)
        """
        if entered_corridor_epoch is None:
            return 0.0
        dwell_seconds = max(0.0, now_epoch - entered_corridor_epoch)
        return min(1.0, dwell_seconds / self.config.loiter_tau_seconds)

    def _compute_heading_score(self, cog: float, cable_azimuth: float) -> float:
        """Measures orientation between vessel course and cable segment azimuth.

        S_heading = |cos(theta_cog - theta_cable)|
        Vessels traveling parallel (0 deg / 180 deg) maximize seabed trench exposure.
        """
        delta_rad = math.radians(cog - cable_azimuth)
        return abs(math.cos(delta_rad))

    def _compute_anchor_score(
        self,
        sog: float,
        in_cpz: bool,
        history: List[VesselTrackPoint],
        now_epoch: float,
    ) -> float:
        """Mechanical Anchor Catch Signature.

        Returns 1.0 if vessel is inside the 3 NM CPZ, current speed <= 1.5 kn,
        and previous speed within the deceleration window (600s) was > 6.0 kn.
        """
        if not in_cpz or sog > self.config.anchor_current_speed_max:
            return 0.0

        if not history:
            return 0.0

        # Look back within deceleration window (default 600 seconds)
        cutoff = now_epoch - self.config.anchor_decel_window_seconds
        for pt in reversed(history):
            if pt.timestamp_epoch < cutoff:
                break
            if pt.sog >= self.config.anchor_prior_speed_min:
                return 1.0

        return 0.0

    def _compute_dark_score(self, now_epoch: float, last_seen_epoch: float) -> float:
        """Penalizes transponder silence when observed near a cable corridor.

        S_dark = min(1.0, (t_now - t_last) / tau_dark)
        """
        silence_seconds = max(0.0, now_epoch - last_seen_epoch)
        if silence_seconds <= 60.0:
            return 0.0
        return min(1.0, silence_seconds / self.config.dark_tau_seconds)

    # -------------------------------------------------------------------------
    # Telemetry Trust Layer
    # -------------------------------------------------------------------------

    def _evaluate_telemetry_trust(
        self,
        current_lat: float,
        current_lon: float,
        current_sog: float,
        current_epoch: float,
        last_seen_epoch: float,
        history: List[VesselTrackPoint],
    ) -> TelemetryTrust:
        """Applies kinematic validation filters to detect spoofing or ghost ships."""
        trust = TelemetryTrust()

        # Coordinate Bounds Sanity
        if not (-90.0 <= current_lat <= 90.0 and -180.0 <= current_lon <= 180.0):
            trust.is_valid = False
            trust.trust_score = 0.0
            return trust

        # Transponder silence check
        silence = max(0.0, current_epoch - last_seen_epoch)
        if silence > 300.0:  # > 5 minutes of silence
            trust.is_dark = True
            trust.dark_duration_seconds = silence

        # Kinematic Jump Filter (detecting teleportation / GPS spoofing)
        if history:
            last_pt = history[-1]
            dt = current_epoch - last_pt.timestamp_epoch
            if dt > 1.0:
                # Approximate distance in Nautical Miles using local projection
                dx = (current_lon - last_pt.lon) * math.cos(math.radians(current_lat)) * 60.0
                dy = (current_lat - last_pt.lat) * 60.0
                dist_nm = math.hypot(dx, dy)
                implied_speed = (dist_nm / dt) * 3600.0  # knots

                trust.implied_speed_knots = round(implied_speed, 2)
                if implied_speed > self.config.max_plausible_vessel_speed_knots:
                    trust.is_jump = True
                    trust.trust_score = 0.3  # Severely penalize telemetry credibility

        # Ghost Ship Decoy Check: Newly seen contact popping up with 0 prior history
        # already inside dragging speed bounds
        if len(history) < self.config.ghost_track_min_samples and current_sog <= 3.5:
            trust.is_ghost_candidate = True

        return trust

    # -------------------------------------------------------------------------
    # Operational Escalation & Mitigation Logic
    # -------------------------------------------------------------------------

    def _classify_threat_level(self, score: float) -> ThreatLevel:
        """Maps composite score to operational tier."""
        if score >= self.config.threshold_critical:
            return ThreatLevel.CRITICAL
        elif score >= self.config.threshold_high:
            return ThreatLevel.HIGH
        elif score >= self.config.threshold_advisory:
            return ThreatLevel.ADVISORY
        return ThreatLevel.NORMAL

    def _determine_mitigation(
        self,
        threat_level: ThreatLevel,
        cable: CableProximity,
        trust: TelemetryTrust,
    ) -> Tuple[str, List[str], List[str]]:
        """Determines automated SOAR instructions and pre-computed BGP backup paths."""
        if threat_level == ThreatLevel.CRITICAL:
            # If flagged as an unverified ghost ship, require operator review first
            if trust.is_ghost_candidate and trust.is_jump:
                return "VERIFY_GHOST_TARGET_BEFORE_FAILOVER", [], []

            action = "TRIGGER_PREEMPTIVE_FAILOVER"
            prefixes = [f"194.100.{hash(cable.cable_id) % 250}.0/24"]
            backups = [f"backup-terrestrial-{cable.cable_id}-alt01"]
            return action, prefixes, backups

        elif threat_level == ThreatLevel.HIGH:
            return "DISPATCH_SOAR_ALERT", [], []
        elif threat_level == ThreatLevel.ADVISORY:
            return "INCREASE_MONITORING_FREQUENCY", [], []

        return "NONE", [], []
