"""Aegis-Sea Optical Time-Domain Reflectometry (OTDR) Cross-Layer Sensor Fusion.

Models optical fiber backscatter telemetry and correlates physical fiber strain
events with surface maritime vessel positions.

Key Optical Principles:
1. Rayleigh Backscatter Attenuation:
   - Baseline loss along single-mode subsea fiber: ~0.19 dB/km at 1550 nm.
   - Periodic optical repeater gain (EDFA) every 60-80 km.
2. Mechanical Anchor Snag / Microbending Event:
   - When an anchor snags cable armor, mechanical tension causes localized microbending loss
     (sudden attenuation drop Delta P >= 2.5 dB) at fiber distance d_fiber (km).
   - If fiber snaps, complete loss-of-light occurs with a high-reflectivity Fresnel peak.
3. Dual-Layer Cyber-Physical Fusion:
   - Maps OTDR fiber distance (km) to 3D geospatial coordinates (lat, lon) along the cable polyline.
   - Computes orthogonal spatial correlation distance Delta d between the optical strain point
     and candidate surface maritime vessels.
   - Provides undeniable physical-layer confirmation for forensic attribution and legal dispatch.
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from aegis.cable_index import CableCorridorIndex


class OpticalEventSeverity(str, Enum):
    """Classification of optical fiber backscatter events."""
    NOMINAL = "NOMINAL"                # Normal light transmission (<0.5 dB loss)
    STRAIN_ADVISORY = "STRAIN_ADVISORY"# Microbending / tension detected (0.5 - 3.0 dB drop)
    CRITICAL_SNAG = "CRITICAL_SNAG"    # Severe localized bending / impending cut (>3.0 dB drop)
    SEVERED_CUT = "SEVERED_CUT"        # Complete optical loss-of-light (Fresnel break)


@dataclass
class OTDREvent:
    """A detected physical optical anomaly along the subsea fiber strand."""
    cable_id: str
    cable_name: str
    fiber_distance_km: float           # Distance from landing station terminal in km
    attenuation_drop_db: float         # Localized signal attenuation in dB
    severity: OpticalEventSeverity
    timestamp_epoch: float
    is_reflective_break: bool          # Fresnel reflection peak present
    event_lat: float                   # Geocoded latitude along cable polyline
    event_lon: float                   # Geocoded longitude along cable polyline


@dataclass
class CrossLayerFusionRecord:
    """Correlation between surface maritime radar/AIS and physical optical backscatter."""
    cable_id: str
    cable_name: str
    otdr_event: OTDREvent
    correlated_mmsi: Optional[str]
    correlated_vessel_name: Optional[str]
    surface_distance_to_snag_nm: Optional[float]
    confidence_score: float            # Cross-layer attribution confidence [0.0, 1.0]
    attribution_verdict: str
    recommended_action: str


class OTDRTelemetrySimulator:
    """Simulates subsea fiber laser pulse backscatter and detects strain anomalies."""

    def __init__(self, cable_index: Optional[CableCorridorIndex] = None):
        self.cable_index = cable_index or CableCorridorIndex(auto_load=True)
        self.baseline_attenuation_db_per_km = 0.19  # Standard silica SMF-28 fiber

    def generate_trace(
        self,
        cable_id: str = "c-lion1",
        total_length_km: float = 1170.0,
        snag_location_km: Optional[float] = 142.5,
        snag_attenuation_db: float = 4.8,
        is_break: bool = False,
        points: int = 400,
    ) -> Dict[str, Any]:
        """Generates an OTDR optical power trace (dB vs Distance in km)."""
        distances = np.linspace(0.0, total_length_km, points)
        powers = []

        initial_power_dbm = 10.0  # Launch power +10 dBm
        current_power = initial_power_dbm

        for i, d in enumerate(distances):
            # Normal Rayleigh backscatter slope
            if i > 0:
                dd = d - distances[i - 1]
                current_power -= self.baseline_attenuation_db_per_km * dd

            # Optical Repeater (EDFA) boost every 70 km
            if i > 0 and int(d / 70.0) > int(distances[i - 1] / 70.0):
                current_power += 13.0  # Optical amplification gain

            # Anchor Snag / Mechanical Microbending Event
            if snag_location_km is not None and d >= snag_location_km:
                if is_break:
                    # Fiber severed: Fresnel reflection spike then drop to noise floor
                    if abs(d - snag_location_km) < (total_length_km / points):
                        current_power += 8.0  # Reflection spike
                    else:
                        current_power = -65.0  # Noise floor
                else:
                    # Bending loss step drop
                    if abs(d - snag_location_km) < (total_length_km / points):
                        current_power -= snag_attenuation_db

            # Add minor optical sensor noise
            noise = np.random.normal(0, 0.08)
            powers.append(round(float(current_power + noise), 2))

        # Detect the event
        detected_event = None
        if snag_location_km is not None:
            # Map distance along cable polyline to lat/lon
            event_lat, event_lon = self._interpolate_cable_coordinate(cable_id, snag_location_km, total_length_km)
            sev = (
                OpticalEventSeverity.SEVERED_CUT if is_break
                else OpticalEventSeverity.CRITICAL_SNAG if snag_attenuation_db >= 3.0
                else OpticalEventSeverity.STRAIN_ADVISORY
            )
            detected_event = OTDREvent(
                cable_id=cable_id,
                cable_name="C-Lion1 (Baltic Subsea Cable)",
                fiber_distance_km=snag_location_km,
                attenuation_drop_db=snag_attenuation_db if not is_break else 55.0,
                severity=sev,
                timestamp_epoch=0.0,
                is_reflective_break=is_break,
                event_lat=event_lat,
                event_lon=event_lon,
            )

        return {
            "cable_id": cable_id,
            "total_length_km": total_length_km,
            "distance_km": [round(float(d), 1) for d in distances],
            "optical_power_dbm": powers,
            "detected_event": detected_event.__dict__ if detected_event else None,
        }

    def correlate_with_maritime_vessel(
        self,
        otdr_event: OTDREvent,
        vessel_mmsi: str,
        vessel_name: str,
        vessel_lat: float,
        vessel_lon: float,
        vessel_sog: float,
    ) -> CrossLayerFusionRecord:
        """Correlates physical OTDR strain with surface vessel coordinates."""
        # Calculate Haversine distance between vessel and optical strain coordinate
        dist_nm = self._haversine_distance_nm(
            vessel_lat, vessel_lon, otdr_event.event_lat, otdr_event.event_lon
        )

        # Attribution logic
        # If surface vessel is within 1.0 NM of optical strain location moving at dragging speed (<=3.0 kn)
        if dist_nm <= 0.6 and vessel_sog <= 3.0:
            confidence = max(0.85, 1.0 - (dist_nm / 1.0) * 0.25)
            verdict = "CONFIRMED_PHYSICAL_SABOTAGE_CORRELATION"
            action = "DISPATCH_INTERCEPTION_AND_ENFORCE_BGP_EVACUATION"
        elif dist_nm <= 1.5:
            confidence = 0.65
            verdict = "PROBABLE_CORRELATION_SURFACE_MONITORING"
            action = "TASK_COASTAL_RADAR_AND_DRONE_VERIFICATION"
        else:
            confidence = 0.15
            verdict = "UNMATCHED_OPTICAL_STRAIN_POSSIBLE_DARK_VESSEL"
            action = "DISPATCH_MARITIME_PATROL_AIRCRAFT_DARK_VESSEL_SEARCH"

        return CrossLayerFusionRecord(
            cable_id=otdr_event.cable_id,
            cable_name=otdr_event.cable_name,
            otdr_event=otdr_event,
            correlated_mmsi=vessel_mmsi,
            correlated_vessel_name=vessel_name,
            surface_distance_to_snag_nm=round(dist_nm, 2),
            confidence_score=round(confidence, 2),
            attribution_verdict=verdict,
            recommended_action=action,
        )

    def _interpolate_cable_coordinate(
        self, cable_id: str, distance_km: float, total_length_km: float
    ) -> Tuple[float, float]:
        """Approximates coordinate along C-Lion1 polyline given fiber distance from terminal."""
        # C-Lion1 runs from Santahamina/Helsinki (60.15N, 25.04E) to Rostock, Germany (54.15N, 12.10E)
        # For simulation, interpolate along line
        fraction = max(0.0, min(1.0, distance_km / total_length_km))
        lat = 60.15 + fraction * (54.15 - 60.15)
        lon = 25.04 + fraction * (12.10 - 25.04)
        return round(lat, 4), round(lon, 4)

    def _haversine_distance_nm(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Great-circle distance between two coordinates in Nautical Miles."""
        r_earth_nm = 3440.065
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = (
            math.sin(dphi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
        return r_earth_nm * c
