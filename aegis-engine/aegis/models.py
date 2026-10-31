"""Pydantic data models for Aegis-Sea Threat Engine."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class ThreatLevel(str, Enum):
    """Operational threat escalation tiers."""

    NORMAL = "NORMAL"        # 0 <= T <= 30 (Green - Normal Transit)
    ADVISORY = "ADVISORY"    # 31 <= T <= 60 (Yellow - Advisory Watch)
    HIGH = "HIGH"            # 61 <= T <= 80 (Orange - Active Threat / SOAR Alert)
    CRITICAL = "CRITICAL"    # 81 <= T <= 100 (Red - Imminent Cut / Pre-emptive Failover)


class CableProximity(BaseModel):
    """Result of querying a vessel's position against a submarine cable."""

    cable_id: str = Field(..., description="Unique cable identifier slug (e.g., 'c-lion1')")
    cable_name: str = Field(..., description="Human-readable cable system name")
    color: Optional[str] = Field(None, description="Hex color string for visual display")
    distance_nm: float = Field(..., description="Orthogonal distance to nearest point in Nautical Miles")
    in_cpz: bool = Field(..., description="Whether vessel is within 3 NM Cable Protection Zone")
    in_alert_corridor: bool = Field(..., description="Whether vessel is within 9 NM Alert Corridor")
    s_prox: float = Field(..., description="Normalized spatial proximity score [0.0, 1.0]")
    cable_azimuth_deg: float = Field(..., description="Tangent orientation of closest cable segment [0, 180)")
    nearest_lon: float = Field(..., description="Longitude of closest point on cable")
    nearest_lat: float = Field(..., description="Latitude of closest point on cable")


class CableIndexStats(BaseModel):
    """Statistics for the loaded CableCorridorIndex."""

    total_features: int = Field(..., description="Total GeoJSON feature records (712)")
    total_cables: int = Field(..., description="Unique subsea cable systems (694)")
    total_segments: int = Field(..., description="Total indexed polyline segments (11,989)")
    build_time_ms: float = Field(..., description="R-tree build time in milliseconds")


class VesselTrackPoint(BaseModel):
    """Individual historical track sample for kinematic analysis."""

    lat: float
    lon: float
    sog: float = Field(..., description="Speed Over Ground in knots")
    cog: float = Field(..., description="Course Over Ground in degrees [0, 360)")
    timestamp_epoch: float = Field(..., description="Observation timestamp in epoch seconds")


class TelemetryTrust(BaseModel):
    """Integrity and trustworthiness evaluation of incoming maritime telemetry."""

    is_valid: bool = Field(True, description="Whether telemetry passes basic bounds and sanity checks")
    is_jump: bool = Field(False, description="Flagged for impossible coordinate displacement jump")
    implied_speed_knots: Optional[float] = Field(None, description="Calculated speed between consecutive fixes")
    is_dark: bool = Field(False, description="Flagged for transponder silence near a cable corridor")
    dark_duration_seconds: float = Field(0.0, description="Elapsed seconds since last broadcast")
    is_ghost_candidate: bool = Field(
        False, description="Flagged as possible phantom decoy appearing abruptly inside CPZ"
    )
    trust_score: float = Field(1.0, description="Overall telemetry reliability multiplier [0.0, 1.0]")


class FactorScores(BaseModel):
    """Normalized individual threat factors [0.0, 1.0]."""

    s_prox: float = Field(0.0, description="Spatial proximity quadratic decay score")
    s_speed: float = Field(0.0, description="Kinematic speed anomaly sigmoid score")
    s_loiter: float = Field(0.0, description="Loitering and dwell time score")
    s_heading: float = Field(0.0, description="Heading and cable bearing alignment score")
    s_anchor: float = Field(0.0, description="Anchor deceleration catch signature score")
    s_dark: float = Field(0.0, description="Transponder blackout silence score")


class ThreatAssessment(BaseModel):
    """Complete cyber-physical threat assessment for a single vessel contact."""

    event_id: str = Field(..., description="Unique event identifier")
    timestamp_iso: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    mmsi: str = Field(..., description="Maritime Mobile Service Identity")
    vessel_name: str = Field(..., description="Reported ship name")
    imo: Optional[str] = Field(None, description="International Maritime Organization number")
    ship_type: Optional[str] = Field(None, description="Vessel classification type")
    coordinates: Dict[str, float] = Field(..., description="Current position {'lat': y, 'lon': x}")
    sog_knots: float = Field(..., description="Speed Over Ground in knots")
    cog_degrees: float = Field(..., description="Course Over Ground in degrees")
    heading_degrees: Optional[float] = Field(None, description="True heading in degrees")

    # Threat Scoring Core
    threat_score: float = Field(..., description="Composite Threat Score [0.0, 100.0]")
    threat_level: ThreatLevel = Field(..., description="Operational threat level (NORMAL, ADVISORY, HIGH, CRITICAL)")
    closest_cable: Optional[CableProximity] = Field(None, description="Nearest submarine cable corridor")
    score_breakdown: FactorScores = Field(default_factory=FactorScores)
    telemetry_trust: TelemetryTrust = Field(default_factory=TelemetryTrust)

    # Automated Incident Response Mitigation Instructions
    recommended_action: str = Field("NONE", description="Recommended SOAR action")
    affected_bgp_prefixes: List[str] = Field(default_factory=list, description="Targeted IP prefixes traversing cable")
    backup_transit_paths: List[str] = Field(default_factory=list, description="Pre-computed redundant transit paths")


class ThreatOverview(BaseModel):
    """System-wide summary of active threats and monitored vessels."""

    timestamp_iso: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    monitored_vessels_total: int
    corridor_vessels_total: int
    threats_critical_count: int
    threats_high_count: int
    threats_advisory_count: int
    threats_normal_count: int
    threats: List[ThreatAssessment] = Field(default_factory=list)


class EvaluateRequest(BaseModel):
    """Payload for on-demand or simulated vessel threat scoring evaluation."""

    mmsi: str = Field(..., description="Maritime Mobile Service Identity")
    lat: float = Field(..., description="Latitude [-90.0, 90.0]")
    lon: float = Field(..., description="Longitude [-180.0, 180.0]")
    sog: float = Field(..., description="Speed Over Ground in knots")
    cog: float = Field(..., description="Course Over Ground in degrees [0, 360)")
    heading: Optional[float] = Field(None, description="Reported true heading in degrees")
    name: str = Field("Unknown Vessel", description="Reported ship name")
    imo: Optional[str] = Field(None, description="IMO number")
    ship_type: Optional[str] = Field(None, description="Vessel classification type")
    history: List[VesselTrackPoint] = Field(
        default_factory=list, description="Historical track points for kinematic and jump analysis"
    )
    timestamp_epoch: Optional[float] = Field(None, description="Observation timestamp in epoch seconds")
    entered_corridor_epoch: Optional[float] = Field(None, description="Corridor entry epoch")
    last_seen_epoch: Optional[float] = Field(None, description="Previous broadcast epoch")


class DispatchStatus(str, Enum):
    """Execution status of an automated incident response dispatch."""

    DISPATCHED = "DISPATCHED"                  # Live webhook transmitted successfully
    SIMULATED = "SIMULATED"                    # Emitted to local log/testbed (no remote webhook configured)
    SUPPRESSED_COOLDOWN = "SUPPRESSED_COOLDOWN"# Suppressed by deduplication cooldown
    HELD_VERIFICATION = "HELD_VERIFICATION"    # Failover held: phantom decoy requires target confirmation
    SUPPRESSED_SPOOF = "SUPPRESSED_SPOOF"      # Suppressed: impossible kinematic jump filtered out
    FAILED = "FAILED"                          # Webhook transport failure


class SOARAlertPayload(BaseModel):
    """Standardized Security Operations Alert (SOAR/SIEM) payload."""

    event_id: str
    timestamp_iso: str
    severity: str
    action: str
    vessel_mmsi: str
    vessel_name: str
    threat_score: float
    cable_id: Optional[str] = None
    cable_name: Optional[str] = None
    distance_nm: Optional[float] = None
    coordinates: Dict[str, float]
    telemetry_trust: TelemetryTrust
    incident_summary: str


class BGPEvacuationPayload(BaseModel):
    """Pre-computed Software-Defined Network (SDN) and BGP route failover payload."""

    cable_id: str
    cable_name: str
    action: str = Field(..., description="'PREEMPTIVE_EVACUATION', 'PREPEND_AS_PATH', or 'FAILOVER_HOLD'")
    status: str = Field(..., description="'ARMED_PREEMPTIVE', 'HELD_UNVERIFIED_DECOY', or 'SUPPRESSED_SPOOF'")
    affected_prefixes: List[str]
    bgp_community: str = Field(..., description="BGP Community attribute (e.g., '65000:666' graceful-shutdown)")
    backup_transit_paths: List[str]
    estimated_switchover_ms: int = Field(
        450, description="Estimated BGP reconvergence time in ms (vs 30,000+ ms reactive loss-of-light)"
    )


class DispatchRecord(BaseModel):
    """Audit log entry for an executed or evaluated incident response event."""

    dispatch_id: str
    timestamp_iso: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    mmsi: str
    vessel_name: str
    threat_level: ThreatLevel
    threat_score: float
    status: DispatchStatus
    soar_payload: Optional[SOARAlertPayload] = None
    bgp_payload: Optional[BGPEvacuationPayload] = None
    target_webhook: Optional[str] = None
    error_message: Optional[str] = None


class ManualDispatchRequest(BaseModel):
    """Request payload to manually trigger an incident response dispatch."""

    mmsi: str
    force: bool = Field(False, description="Bypass alert cooldown deduplication")

