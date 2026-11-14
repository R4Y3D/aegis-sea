"""Aegis-Sea Adversarial Red Team Benchmarking & Novelty Evaluation Suite.

Provides empirical benchmarking of Aegis-Sea against existing state-of-the-art
paradigms across physical sabotage and adversarial cyber telemetry attacks:

1. Baseline 1: Naive Geofencing (Industry Standard / Commercial MDA)
   - Evaluates proximity threshold (<=3 NM) and speed threshold (<=3.5 kn).
   - Naively trusts AIS coordinates as ground truth.
2. Baseline 2: Unsupervised Kinematic Anomaly Detector (NPS / Sandia Labs ML baseline)
   - Evaluates statistical velocity, acceleration, and turning rate anomalies (Mahalanobis / Z-score).
   - Lacks infrastructure context (blind to subsea cable protection zones).
3. Proposed System: Aegis-Sea Zero-Trust Spatial Scoring Core
   - R-tree spatial indexing of 11,989 cable segments + 6-factor composite scoring +
     kinematic jump filtering + phantom ghost candidate clustering + BGP SOAR mitigation.
"""

import time
import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from aegis.cable_index import CableCorridorIndex
from aegis.config import settings, Settings
from aegis.dispatcher import AlertDispatcher
from aegis.models import (
    ThreatLevel,
    ThreatAssessment,
    VesselTrackPoint,
    TelemetryTrust,
)
from aegis.scorer import ThreatScorer


class TargetCategory(str, Enum):
    """Ground truth categories for benchmark vessel tracks."""
    BENIGN_CRUISING = "BENIGN_CRUISING"
    BENIGN_HARBOR_TUG = "BENIGN_HARBOR_TUG"
    BENIGN_FISHING = "BENIGN_FISHING"
    GENUINE_ANCHOR_DRAG = "GENUINE_ANCHOR_DRAG"
    SPOOF_GPS_JUMP = "SPOOF_GPS_JUMP"
    SPOOF_SLOW_DRIFT = "SPOOF_SLOW_DRIFT"
    GHOST_DECOY_SWARM = "GHOST_DECOY_SWARM"


@dataclass
class BenchmarkVesselSample:
    """A single synthetic or recorded vessel trajectory for benchmarking."""
    mmsi: str
    vessel_name: str
    category: TargetCategory
    is_genuine_attack: bool
    is_cyber_spoof: bool
    lat: float
    lon: float
    sog: float
    cog: float
    history: List[VesselTrackPoint]
    dwell_time_sec: float = 0.0
    notes: str = ""


@dataclass
class DetectorResult:
    """Standardized decision output for any evaluated detector."""
    detector_name: str
    alarm_triggered: bool
    failover_triggered: bool
    threat_level: str
    threat_score: float
    latency_microseconds: float
    reason: str


class NaiveGeofenceDetector:
    """Baseline 1: Industry-standard distance & speed threshold geofence.
    
    Triggered when a vessel is inside the 3 NM Cable Protection Zone (CPZ)
    with Speed Over Ground <= 3.5 knots. Assumes all AIS data is ground truth.
    """

    def __init__(self, cable_index: CableCorridorIndex, cpz_radius_nm: float = 3.0):
        self.cable_index = cable_index
        self.cpz_radius_nm = cpz_radius_nm

    def evaluate(self, sample: BenchmarkVesselSample) -> DetectorResult:
        t0 = time.perf_counter()
        closest = self.cable_index.get_closest_cable(
            lat=sample.lat, lon=sample.lon, max_distance_nm=self.cpz_radius_nm
        )
        elapsed_us = (time.perf_counter() - t0) * 1_000_000.0

        if closest and closest.in_cpz and sample.sog <= 3.5:
            return DetectorResult(
                detector_name="NaiveGeofence",
                alarm_triggered=True,
                failover_triggered=True,
                threat_level="CRITICAL",
                threat_score=85.0,
                latency_microseconds=elapsed_us,
                reason="Inside CPZ with SOG <= 3.5 kn",
            )
        elif closest and closest.in_alert_corridor:
            return DetectorResult(
                detector_name="NaiveGeofence",
                alarm_triggered=False,
                failover_triggered=False,
                threat_level="ADVISORY",
                threat_score=40.0,
                latency_microseconds=elapsed_us,
                reason="Inside alert corridor",
            )
        return DetectorResult(
            detector_name="NaiveGeofence",
            alarm_triggered=False,
            failover_triggered=False,
            threat_level="NORMAL",
            threat_score=10.0,
            latency_microseconds=elapsed_us,
            reason="Outside CPZ or cruising speed",
        )


class KinematicMLAnomalyDetector:
    """Baseline 2: Unsupervised Kinematic Anomaly Detector (NPS / Sandia Labs baseline).
    
    Uses statistical kinematic profile scoring (speed deviation, turning rate variance,
    and acceleration bounds) representing autoencoders / isolation forests.
    Blind to subsea cable locations (evaluates anomaly in an infrastructure vacuum).
    """

    def __init__(self):
        # Normal cruising baseline parameters: mean 14.5 kn, std 3.2 kn
        self.cruising_mean_sog = 14.5
        self.cruising_std_sog = 3.2
        self.max_plausible_accel_kn_s = 0.5  # 0.5 kn/s max physical acceleration

    def evaluate(self, sample: BenchmarkVesselSample) -> DetectorResult:
        t0 = time.perf_counter()

        # 1. Speed Z-score
        z_speed = abs(sample.sog - self.cruising_mean_sog) / self.cruising_std_sog

        # 2. Kinematic acceleration between last two points
        max_accel = 0.0
        turning_rate = 0.0
        if len(sample.history) >= 1:
            prev = sample.history[-1]
            dt = max(1.0, 30.0)  # assume nominal 30s fix
            dsog = abs(sample.sog - prev.sog)
            max_accel = dsog / dt
            dcog = abs(sample.cog - prev.cog)
            if dcog > 180.0:
                dcog = 360.0 - dcog
            turning_rate = dcog / dt

        # Anomaly score composite [0, 100]
        # High score for sharp slowdowns, excessive turning, or impossible acceleration
        accel_penalty = max(0.0, (max_accel - 0.2) * 50.0)
        slow_penalty = 40.0 if sample.sog <= 3.5 else 0.0
        turn_penalty = min(30.0, turning_rate * 10.0)
        anomaly_score = min(100.0, z_speed * 15.0 + accel_penalty + slow_penalty + turn_penalty)

        elapsed_us = (time.perf_counter() - t0) * 1_000_000.0

        alarm = anomaly_score >= 65.0
        # ML systems trigger failover if critical alert threshold exceeded
        failover = anomaly_score >= 80.0

        level = "NORMAL"
        if anomaly_score >= 80.0:
            level = "CRITICAL"
        elif anomaly_score >= 60.0:
            level = "HIGH"
        elif anomaly_score >= 35.0:
            level = "ADVISORY"

        return DetectorResult(
            detector_name="KinematicML",
            alarm_triggered=alarm,
            failover_triggered=failover,
            threat_level=level,
            threat_score=round(anomaly_score, 1),
            latency_microseconds=elapsed_us,
            reason=f"Kinematic anomaly score: {anomaly_score:.1f}/100",
        )


class AegisZeroTrustEvaluator:
    """Proposed System: Aegis-Sea Zero-Trust Spatial Scoring Core."""

    def __init__(self, cable_index: CableCorridorIndex):
        self.cable_index = cable_index
        self.scorer = ThreatScorer(cable_index=cable_index)
        self.dispatcher = AlertDispatcher(config=settings)

    def evaluate(self, sample: BenchmarkVesselSample) -> DetectorResult:
        t0 = time.perf_counter()
        now = time.time()
        entered_epoch = (now - sample.dwell_time_sec) if sample.dwell_time_sec > 0 else None

        assessment: ThreatAssessment = self.scorer.score_vessel(
            mmsi=sample.mmsi,
            lat=sample.lat,
            lon=sample.lon,
            sog=sample.sog,
            cog=sample.cog,
            name=sample.vessel_name,
            history=sample.history,
            current_time_epoch=now,
            entered_corridor_epoch=entered_epoch,
            last_seen_epoch=now,
        )

        bgp_payload = self.dispatcher.build_bgp_evacuation_payload(assessment)
        elapsed_us = (time.perf_counter() - t0) * 1_000_000.0

        alarm = assessment.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL)
        # Pre-emptive BGP evacuation is armed ONLY when threat is CRITICAL and telemetry is authentic
        failover = (
            assessment.threat_level == ThreatLevel.CRITICAL
            and bgp_payload.status == "ARMED_PREEMPTIVE"
        )

        return DetectorResult(
            detector_name="AegisSea",
            alarm_triggered=alarm,
            failover_triggered=failover,
            threat_level=assessment.threat_level.value,
            threat_score=assessment.threat_score,
            latency_microseconds=elapsed_us,
            reason=f"Aegis score: {assessment.threat_score:.1f}, BGP: {bgp_payload.status}",
        )


class AdversarialDatasetGenerator:
    """Generates synthetic, labeled maritime fleets for statistical benchmarking."""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        np.random.seed(seed)

    def generate_fleet(
        self,
        n_benign_cruising: int = 600,
        n_benign_harbor_tugs: int = 150,
        n_benign_fishing: int = 150,
        n_genuine_sabotage: int = 100,
        n_spoof_gps_jump: int = 100,
        n_spoof_slow_drift: int = 50,
        n_ghost_swarms: int = 50,
    ) -> List[BenchmarkVesselSample]:
        """Synthesizes an annotated evaluation dataset of diverse maritime contacts."""
        samples: List[BenchmarkVesselSample] = []
        now = time.time()

        # 1. Benign Cruising Cargo/Tanker (Normal international traffic in transit)
        for i in range(n_benign_cruising):
            lat = random.uniform(50.0, 62.0)
            lon = random.uniform(10.0, 30.0)
            sog = random.gauss(14.5, 2.5)
            sog = max(8.0, min(24.0, sog))
            cog = random.uniform(0.0, 360.0)
            history = [
                VesselTrackPoint(
                    lat=lat - 0.05, lon=lon - 0.05, sog=sog, cog=cog, timestamp_epoch=now - 300.0
                ),
                VesselTrackPoint(
                    lat=lat - 0.02, lon=lon - 0.02, sog=sog, cog=cog, timestamp_epoch=now - 120.0
                ),
            ]
            samples.append(
                BenchmarkVesselSample(
                    mmsi=f"200{i:06d}",
                    vessel_name=f"CARGO_{i}",
                    category=TargetCategory.BENIGN_CRUISING,
                    is_genuine_attack=False,
                    is_cyber_spoof=False,
                    lat=lat,
                    lon=lon,
                    sog=sog,
                    cog=cog,
                    history=history,
                    dwell_time_sec=120.0,
                )
            )

        # 2. Benign Harbor Tugs / Service Vessels (Slow, sharp turns, but at coastal ports)
        # Coordinates in Helsinki harbor / Gulf of Finland coast away from deep cable trench
        for i in range(n_benign_harbor_tugs):
            lat = 60.15 + random.uniform(-0.02, 0.02)
            lon = 24.93 + random.uniform(-0.02, 0.02)
            sog = random.uniform(0.5, 3.5)
            cog = random.uniform(0.0, 360.0)
            history = [
                VesselTrackPoint(lat=lat - 0.005, lon=lon, sog=2.5, cog=(cog + 45) % 360, timestamp_epoch=now - 180.0),
                VesselTrackPoint(lat=lat, lon=lon - 0.005, sog=1.2, cog=cog, timestamp_epoch=now - 60.0),
            ]
            samples.append(
                BenchmarkVesselSample(
                    mmsi=f"230{i:06d}",
                    vessel_name=f"TUG_{i}",
                    category=TargetCategory.BENIGN_HARBOR_TUG,
                    is_genuine_attack=False,
                    is_cyber_spoof=False,
                    lat=lat,
                    lon=lon,
                    sog=sog,
                    cog=cog,
                    history=history,
                    dwell_time_sec=1800.0,
                )
            )

        # 3. Benign Fishing Vessels (Slow speeds, variable courses in open waters)
        for i in range(n_benign_fishing):
            lat = random.uniform(55.0, 59.0)
            lon = random.uniform(15.0, 22.0)
            sog = random.uniform(1.8, 4.5)
            cog = random.uniform(0.0, 360.0)
            history = [
                VesselTrackPoint(lat=lat - 0.01, lon=lon, sog=4.0, cog=(cog + 90) % 360, timestamp_epoch=now - 300.0),
                VesselTrackPoint(lat=lat, lon=lon - 0.01, sog=2.1, cog=cog, timestamp_epoch=now - 120.0),
            ]
            samples.append(
                BenchmarkVesselSample(
                    mmsi=f"240{i:06d}",
                    vessel_name=f"TRAWLER_{i}",
                    category=TargetCategory.BENIGN_FISHING,
                    is_genuine_attack=False,
                    is_cyber_spoof=False,
                    lat=lat,
                    lon=lon,
                    sog=sog,
                    cog=cog,
                    history=history,
                    dwell_time_sec=900.0,
                )
            )

        # 4. Genuine Physical Sabotage (Yi Peng 3 Baltic Sea anchor drag profile across C-Lion1)
        # Position placed directly over C-Lion1 cable (lat ~60.05, lon ~25.02)
        for i in range(n_genuine_sabotage):
            lat = 60.05 + random.uniform(-0.01, 0.01)
            lon = 25.02 + random.uniform(-0.01, 0.01)
            sog = random.uniform(1.0, 2.5)  # anchor dragging speed
            cog = random.uniform(195.0, 215.0)  # aligned with seabed cable trench
            history = [
                VesselTrackPoint(lat=lat - 0.05, lon=lon - 0.02, sog=11.5, cog=200.0, timestamp_epoch=now - 1200.0),
                VesselTrackPoint(lat=lat - 0.02, lon=lon - 0.01, sog=6.0, cog=200.0, timestamp_epoch=now - 600.0),
                VesselTrackPoint(lat=lat - 0.005, lon=lon, sog=2.0, cog=205.0, timestamp_epoch=now - 180.0),
            ]
            samples.append(
                BenchmarkVesselSample(
                    mmsi=f"412{i:06d}",
                    vessel_name=f"SABOTAGE_CARRIER_{i}",
                    category=TargetCategory.GENUINE_ANCHOR_DRAG,
                    is_genuine_attack=True,
                    is_cyber_spoof=False,
                    lat=lat,
                    lon=lon,
                    sog=sog,
                    cog=cog,
                    history=history,
                    dwell_time_sec=2700.0,  # 45 min dwell dragging
                    notes="Decelerated from 11.5 kn to 1.5 kn inside 3 NM CPZ, dragging over trench",
                )
            )

        # 5. SDR GPS Teleportation Jump (Impulse Spoofing)
        # Last known point 2.5 NM away 30s ago, sudden teleportation jump to cable trench
        for i in range(n_spoof_gps_jump):
            lat = 60.0333 + random.uniform(-0.005, 0.005)
            lon = 25.0 + random.uniform(-0.005, 0.005)
            sog = random.uniform(0.8, 2.0)
            cog = random.uniform(0.0, 360.0)
            # 30s prior was 2.5 NM away (implied speed ~300 knots)
            history = [
                VesselTrackPoint(lat=60.0, lon=24.95, sog=12.0, cog=90.0, timestamp_epoch=now - 30.0)
            ]
            samples.append(
                BenchmarkVesselSample(
                    mmsi=f"999{i:06d}",
                    vessel_name=f"SDR_JUMP_{i}",
                    category=TargetCategory.SPOOF_GPS_JUMP,
                    is_genuine_attack=False,
                    is_cyber_spoof=True,
                    lat=lat,
                    lon=lon,
                    sog=sog,
                    cog=cog,
                    history=history,
                    dwell_time_sec=30.0,
                    notes="Implied velocity jump > 200 kn from SDR coordinate synthesis",
                )
            )

        # 6. Adversarial Slow-Drift Meaconing (Crafted to evade naive velocity jumps)
        # Adversary slowly shifts coordinates to mimic a drag while keeping acceleration low
        for i in range(n_spoof_slow_drift):
            lat = 60.045 + random.uniform(-0.005, 0.005)
            lon = 25.015 + random.uniform(-0.005, 0.005)
            sog = random.uniform(1.2, 2.2)
            cog = 205.0
            history = [
                VesselTrackPoint(lat=lat - 0.015, lon=lon - 0.005, sog=3.2, cog=205.0, timestamp_epoch=now - 600.0),
                VesselTrackPoint(lat=lat - 0.008, lon=lon - 0.003, sog=2.5, cog=205.0, timestamp_epoch=now - 300.0),
                VesselTrackPoint(lat=lat - 0.003, lon=lon - 0.001, sog=1.8, cog=205.0, timestamp_epoch=now - 100.0),
            ]
            samples.append(
                BenchmarkVesselSample(
                    mmsi=f"998{i:06d}",
                    vessel_name=f"SLOW_DRIFT_{i}",
                    category=TargetCategory.SPOOF_SLOW_DRIFT,
                    is_genuine_attack=False,
                    is_cyber_spoof=True,
                    lat=lat,
                    lon=lon,
                    sog=sog,
                    cog=cog,
                    history=history,
                    dwell_time_sec=600.0,
                    notes="Synthetic coordinate drift crafted below kinematic impulse thresholds",
                )
            )

        # 7. Failover DoS Ghost Vessel Swarm
        # Synthesized transponder appearing instantaneously inside CPZ with 0 prior history
        for i in range(n_ghost_swarms):
            lat = 60.05 + random.uniform(-0.01, 0.01)
            lon = 25.02 + random.uniform(-0.01, 0.01)
            sog = random.uniform(1.0, 2.0)
            cog = random.uniform(0.0, 360.0)
            samples.append(
                BenchmarkVesselSample(
                    mmsi=f"997{i:06d}",
                    vessel_name=f"PHANTOM_GHOST_{i}",
                    category=TargetCategory.GHOST_DECOY_SWARM,
                    is_genuine_attack=False,
                    is_cyber_spoof=True,
                    lat=lat,
                    lon=lon,
                    sog=sog,
                    cog=cog,
                    history=[],  # Zero historical AIS points
                    dwell_time_sec=0.0,
                    notes="Abrupt appearance in CPZ designed to trigger unneeded BGP failover",
                )
            )

        random.shuffle(samples)
        return samples


@dataclass
class BenchmarkMetrics:
    """Summary statistics for a detector evaluation."""
    detector_name: str
    total_samples: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    accuracy: float
    precision: float
    recall: float
    specificity: float
    f1_score: float
    false_positive_rate: float
    failover_dos_vulnerability_rate: float
    mean_latency_microseconds: float

    def to_markdown_row(self) -> str:
        return (
            f"| **{self.detector_name}** | {self.accuracy:.1%} | {self.precision:.1%} | "
            f"{self.recall:.1%} | {self.f1_score:.3f} | {self.false_positive_rate:.1%} | "
            f"**{self.failover_dos_vulnerability_rate:.1%}** | {self.mean_latency_microseconds:.1f} μs |"
        )


class NoveltyBenchmarkRunner:
    """Orchestrates comprehensive multi-baseline benchmarking against adversarial fleets."""

    def __init__(self, cable_index: Optional[CableCorridorIndex] = None):
        self.cable_index = cable_index or CableCorridorIndex(auto_load=True)
        self.naive = NaiveGeofenceDetector(cable_index=self.cable_index)
        self.kinematic_ml = KinematicMLAnomalyDetector()
        self.aegis = AegisZeroTrustEvaluator(cable_index=self.cable_index)
        self.dataset_gen = AdversarialDatasetGenerator()

    def run_benchmark(self, dataset: Optional[List[BenchmarkVesselSample]] = None) -> Dict[str, BenchmarkMetrics]:
        """Runs the entire benchmark dataset across all 3 detectors and computes metrics."""
        samples = dataset or self.dataset_gen.generate_fleet()

        detectors = [
            ("NaiveGeofence", self.naive),
            ("KinematicML", self.kinematic_ml),
            ("AegisSea", self.aegis),
        ]

        metrics_by_detector: Dict[str, BenchmarkMetrics] = {}

        for det_name, detector in detectors:
            tp = 0
            fp = 0
            tn = 0
            fn = 0
            latencies = []
            dos_triggered_on_cyber = 0
            total_cyber_spoofs = 0

            for s in samples:
                res: DetectorResult = detector.evaluate(s)
                latencies.append(res.latency_microseconds)

                # Ground truth classification
                # A "True Positive" is correctly raising an alarm for GENUINE_ATTACK
                if s.is_genuine_attack:
                    if res.alarm_triggered:
                        tp += 1
                    else:
                        fn += 1
                else:
                    # Benign or Cyber Spoof
                    if res.alarm_triggered:
                        fp += 1
                    else:
                        tn += 1

                # Failover DoS metric: Cyber spoofing attack tricked system into failover
                if s.is_cyber_spoof:
                    total_cyber_spoofs += 1
                    if res.failover_triggered:
                        dos_triggered_on_cyber += 1

            total = len(samples)
            acc = (tp + tn) / total if total > 0 else 0.0
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            dos_rate = (
                dos_triggered_on_cyber / total_cyber_spoofs
                if total_cyber_spoofs > 0
                else 0.0
            )

            metrics_by_detector[det_name] = BenchmarkMetrics(
                detector_name=det_name,
                total_samples=total,
                true_positives=tp,
                false_positives=fp,
                true_negatives=tn,
                false_negatives=fn,
                accuracy=acc,
                precision=prec,
                recall=rec,
                specificity=spec,
                f1_score=f1,
                false_positive_rate=fpr,
                failover_dos_vulnerability_rate=dos_rate,
                mean_latency_microseconds=float(np.mean(latencies)),
            )

        return metrics_by_detector

    def generate_markdown_table(self, metrics: Dict[str, BenchmarkMetrics]) -> str:
        """Outputs a publication-ready Markdown comparison table."""
        header = (
            "| Detector Architecture | Accuracy | Precision | Recall (TPR) | F1-Score | "
            "False Alarm Rate (FPR) | **Failover DoS Vulnerability** | Eval Latency |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        )
        rows = [m.to_markdown_row() for m in metrics.values()]
        return "\n".join([header] + rows)
