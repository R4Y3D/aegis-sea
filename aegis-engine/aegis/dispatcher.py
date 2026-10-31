"""Aegis-Sea Automated Incident Response & BGP Pre-emptive Evacuation Dispatcher.

Orchestrates security and network mitigation when maritime threats approach subsea cables:
1. Dispatches standardized SOAR/SIEM alert payloads to security operation centers.
2. Generates pre-computed Software-Defined Network (SDN) and BGP route withdrawal
   payloads to evacuate IP transit across cables before physical severance occurs.
3. Implements Telemetry Trust Safeguards:
   - Suppresses failover for spoofed GPS teleportation jumps.
   - Holds route drain for unverified phantom ghost decoys (Failover DoS protection).
4. Maintains an in-memory audit log and enforces alert cooldown deduplication.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
import httpx

from aegis.config import Settings, settings
from aegis.models import (
    BGPEvacuationPayload,
    DispatchRecord,
    DispatchStatus,
    SOARAlertPayload,
    ThreatAssessment,
    ThreatLevel,
)

logger = logging.getLogger("aegis.dispatcher")


class AlertDispatcher:
    """Automated incident response and network mitigation dispatcher."""

    def __init__(
        self,
        config: Optional[Settings] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.config = config or settings
        self._external_client = client
        self._history: List[DispatchRecord] = []
        self._cooldown_tracker: Dict[str, float] = {}
        self._max_history: int = 500

    async def _get_client(self) -> httpx.AsyncClient:
        if self._external_client is not None and not self._external_client.is_closed:
            return self._external_client
        return httpx.AsyncClient(timeout=8.0)

    def build_soar_payload(self, assessment: ThreatAssessment) -> SOARAlertPayload:
        """Constructs a structured SOAR/SIEM incident response alert payload."""
        cable_name = (
            assessment.closest_cable.cable_name
            if assessment.closest_cable
            else "Unknown Subsea Cable"
        )
        cable_id = (
            assessment.closest_cable.cable_id
            if assessment.closest_cable
            else None
        )
        dist_nm = (
            assessment.closest_cable.distance_nm
            if assessment.closest_cable
            else None
        )

        trust = assessment.telemetry_trust

        # Formulate human-readable incident narrative
        if assessment.threat_level == ThreatLevel.CRITICAL:
            if trust.is_ghost_candidate and trust.is_jump:
                summary = (
                    f"PHANTOM GHOST DECOY FLAGGED: Target {assessment.vessel_name} (MMSI {assessment.mmsi}) "
                    f"appeared abruptly within {cable_name} CPZ ({dist_nm} NM) with zero voyage history. "
                    f"Pre-emptive route drain withheld to prevent network disruption. Verification required."
                )
            else:
                summary = (
                    f"CRITICAL ANCHOR DRAG THREAT: Vessel {assessment.vessel_name} (MMSI {assessment.mmsi}) "
                    f"moving at {assessment.sog_knots:.1f} kn within {cable_name} CPZ ({dist_nm} NM). "
                    f"Kinematic anchor snag signature verified. Automated pre-emptive BGP evacuation armed."
                )
        elif trust.is_jump:
            summary = (
                f"SDR TELEMETRY SPOOFING DETECTED: Vessel {assessment.vessel_name} (MMSI {assessment.mmsi}) "
                f"exhibited impossible kinematic displacement jump ({trust.implied_speed_knots} kn). "
                f"Trust layer suppressed false alarm; failover aborted."
            )
        elif assessment.threat_level == ThreatLevel.HIGH:
            summary = (
                f"HIGH THREAT ADVISORY: Suspicious vessel maneuver by {assessment.vessel_name} (MMSI {assessment.mmsi}) "
                f"near {cable_name} ({dist_nm} NM, score {assessment.threat_score}/100). SOC alert dispatched."
            )
        else:
            summary = (
                f"ADVISORY MONITORING: Vessel {assessment.vessel_name} (MMSI {assessment.mmsi}) "
                f"in corridor for {cable_name} ({dist_nm} NM). Monitoring frequency elevated."
            )

        return SOARAlertPayload(
            event_id=assessment.event_id,
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
            severity=assessment.threat_level.value,
            action=assessment.recommended_action,
            vessel_mmsi=assessment.mmsi,
            vessel_name=assessment.vessel_name,
            threat_score=assessment.threat_score,
            cable_id=cable_id,
            cable_name=cable_name,
            distance_nm=dist_nm,
            coordinates=assessment.coordinates,
            telemetry_trust=trust,
            incident_summary=summary,
        )

    def build_bgp_evacuation_payload(
        self, assessment: ThreatAssessment
    ) -> BGPEvacuationPayload:
        """Generates pre-computed BGP prefix withdrawal or route demotion instructions."""
        cable_id = (
            assessment.closest_cable.cable_id
            if assessment.closest_cable
            else "generic-subsea-link"
        )
        cable_name = (
            assessment.closest_cable.cable_name
            if assessment.closest_cable
            else "Subsea Fiber Corridor"
        )

        trust = assessment.telemetry_trust

        # Determine default affected IP prefixes if none assigned
        prefixes = assessment.affected_bgp_prefixes or [
            f"194.100.{abs(hash(cable_id)) % 250}.0/24",
            f"194.100.{(abs(hash(cable_id)) + 1) % 250}.0/24",
        ]

        # Determine redundant backup routes
        backup_paths = assessment.backup_transit_paths or [
            f"backup-terrestrial-{cable_id}-primary",
            f"backup-subsea-diverse-ring-02",
        ]

        if assessment.threat_level == ThreatLevel.CRITICAL:
            if trust.is_ghost_candidate and trust.is_jump:
                action = "FAILOVER_HOLD"
                status = "HELD_UNVERIFIED_DECOY"
                community = "NONE (HELD_PENDING_CONFIRMATION)"
            else:
                action = "PREEMPTIVE_EVACUATION"
                status = "ARMED_PREEMPTIVE"
                community = "65000:666 (GRACEFUL_SHUTDOWN)"
        elif trust.is_jump:
            action = "SUPPRESSED"
            status = "SUPPRESSED_SPOOF"
            community = "NONE (SPOOF_FILTERED)"
        elif assessment.threat_level == ThreatLevel.HIGH:
            action = "PREPEND_AS_PATH"
            status = "ARMED_PREPARATORY"
            community = "65000:70 (LOW_LOCAL_PREF)"
        else:
            action = "MONITOR"
            status = "MONITORING"
            community = "NONE"

        return BGPEvacuationPayload(
            cable_id=cable_id,
            cable_name=cable_name,
            action=action,
            status=status,
            affected_prefixes=prefixes,
            bgp_community=community,
            backup_transit_paths=backup_paths,
            estimated_switchover_ms=450,
        )

    async def dispatch(
        self,
        assessment: ThreatAssessment,
        force: bool = False,
    ) -> DispatchRecord:
        """Evaluates and dispatches SOAR alerts and BGP mitigation instructions."""
        now = time.time()
        cable_id = (
            assessment.closest_cable.cable_id
            if assessment.closest_cable
            else "none"
        )
        cooldown_key = f"{assessment.mmsi}:{cable_id}:{assessment.threat_level.value}"

        # Cooldown deduplication check
        if not force and assessment.threat_level not in (ThreatLevel.NORMAL,):
            last_dispatch = self._cooldown_tracker.get(cooldown_key, 0.0)
            if now - last_dispatch < self.config.alert_cooldown_seconds:
                record = DispatchRecord(
                    dispatch_id=f"disp-{assessment.mmsi}-{int(now)}",
                    mmsi=assessment.mmsi,
                    vessel_name=assessment.vessel_name,
                    threat_level=assessment.threat_level,
                    threat_score=assessment.threat_score,
                    status=DispatchStatus.SUPPRESSED_COOLDOWN,
                    error_message=f"Suppressed by cooldown ({int(now - last_dispatch)}s / {int(self.config.alert_cooldown_seconds)}s)",
                )
                self._record_dispatch(record)
                return record

        # Build payloads
        soar_payload = self.build_soar_payload(assessment)
        bgp_payload = self.build_bgp_evacuation_payload(assessment)
        trust = assessment.telemetry_trust

        # Determine dispatch status based on trust layer
        target_webhook = self.config.soar_webhook_url
        error_message = None

        if trust.is_ghost_candidate and trust.is_jump:
            status = DispatchStatus.HELD_VERIFICATION
        elif trust.is_jump:
            status = DispatchStatus.SUPPRESSED_SPOOF
        elif target_webhook:
            # Active external webhook configured
            try:
                client = await self._get_client()
                resp = await client.post(
                    target_webhook,
                    json={
                        "soar": soar_payload.model_dump(),
                        "bgp": bgp_payload.model_dump(),
                    },
                )
                if resp.status_code in (200, 201, 202, 204):
                    status = DispatchStatus.DISPATCHED
                else:
                    status = DispatchStatus.FAILED
                    error_message = f"Webhook HTTP {resp.status_code}"
            except Exception as ex:
                status = DispatchStatus.FAILED
                error_message = str(ex)
                logger.error(f"Failed to transmit webhook to {target_webhook}: {ex}")
        else:
            # Simulated local dispatch (testbed / laboratory mode)
            status = DispatchStatus.SIMULATED

        # Update cooldown tracker on successful evaluation
        self._cooldown_tracker[cooldown_key] = now

        record = DispatchRecord(
            dispatch_id=f"disp-{assessment.mmsi}-{int(now)}",
            mmsi=assessment.mmsi,
            vessel_name=assessment.vessel_name,
            threat_level=assessment.threat_level,
            threat_score=assessment.threat_score,
            status=status,
            soar_payload=soar_payload,
            bgp_payload=bgp_payload,
            target_webhook=target_webhook,
            error_message=error_message,
        )

        self._record_dispatch(record)
        logger.info(
            f"[DISPATCH] MMSI {assessment.mmsi} ({assessment.threat_level.value}, Score: {assessment.threat_score}) -> {status.value}"
        )
        return record

    def _record_dispatch(self, record: DispatchRecord):
        self._history.insert(0, record)
        if len(self._history) > self._max_history:
            self._history.pop()

    def get_history(self, limit: int = 50) -> List[DispatchRecord]:
        """Returns recent dispatch history."""
        return self._history[:limit]

    def clear_history(self):
        """Clears in-memory audit history and cooldowns."""
        self._history.clear()
        self._cooldown_tracker.clear()
