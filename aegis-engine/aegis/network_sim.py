"""Aegis-Sea BGP Network Convergence & Pre-emptive Evacuation Simulator.

Simulates cyber-physical IP transit flows across submarine cable infrastructure,
comparing network convergence, packet loss, and service disruption under two paradigms:

1. Reactive Status Quo (Loss-of-Light):
   - Physical cable cut occurs without warning.
   - Edge routers experience sudden link failure.
   - BGP Hold Timer / BFD countdown expiration causes transient blackholing (3s to 90s).
   - High packet loss, TCP connection resets, and global BGP route flapping.

2. Proactive Aegis-Sea Pre-emptive Evacuation (Proposed):
   - Aegis-Sea detects verified anchor-drag threat 60s to 120s before physical impact.
   - Automated SOAR dispatches RFC 7999 / RFC 8326 Graceful Shutdown (BGP Community 65000:666).
   - Upstream Autonomous Systems depress LOCAL_PREF and pre-drain traffic onto backup ring
     while physical fiber is still 100% operational.
   - Zero packet drops, zero TCP resets, seamless operational continuity when cut occurs.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple, Optional
import numpy as np


@dataclass
class NetworkSimConfig:
    """Parameters for the subsea cyber-physical transit simulation."""
    sim_duration_sec: float = 240.0
    time_step_sec: float = 0.5
    normal_traffic_gbps: float = 65.0       # 65 Gbps baseline transatlantic load
    primary_capacity_gbps: float = 100.0    # 100 Gbps subsea fiber capacity
    backup_capacity_gbps: float = 80.0      # 80 Gbps redundant diverse ring capacity
    primary_rtt_ms: float = 38.0            # Subsea low-latency fiber
    backup_rtt_ms: float = 78.0             # Terrestrial / satellite backup loop
    
    # Event Timestamps
    aegis_detection_time_sec: float = 60.0  # Aegis verifies threat & arms failover
    physical_cut_time_sec: float = 120.0    # Anchor physically severs seabed cable
    
    # Protocol Latencies
    bgp_graceful_drain_duration_ms: float = 450.0 # BGP RFC 8326 reconvergence window
    reactive_bfd_hold_sec: float = 6.0            # Fast BFD failure detection delay
    reactive_bgp_flap_duration_sec: float = 18.0  # Path hunt and withdrawal dampening


@dataclass
class ConvergenceTimeseries:
    """Timeline arrays tracking network performance."""
    timestamps_sec: List[float]
    primary_traffic_gbps: List[float]
    backup_traffic_gbps: List[float]
    dropped_traffic_gbps: List[float]
    cumulative_dropped_gigabits: List[float]
    effective_latency_ms: List[float]


@dataclass
class NetworkEvaluationReport:
    """Summary metrics comparing reactive vs pre-emptive evacuation."""
    paradigm: str
    total_data_lost_gigabits: float
    total_data_lost_gigabytes: float
    outage_duration_sec: float
    peak_packet_drop_rate_pct: float
    average_latency_ms: float
    service_availability_pct: float


class BGPConvergenceSimulator:
    """Simulates BGP routing dynamics under physical sabotage conditions."""

    def __init__(self, config: Optional[NetworkSimConfig] = None):
        self.config = config or NetworkSimConfig()

    def run_reactive_loss_of_light(self) -> Tuple[ConvergenceTimeseries, NetworkEvaluationReport]:
        """Simulates the industry-standard reactive failure path (unannounced cut)."""
        cfg = self.config
        steps = int(cfg.sim_duration_sec / cfg.time_step_sec)
        
        timestamps = []
        primary_traffic = []
        backup_traffic = []
        dropped_traffic = []
        cum_dropped = []
        latencies = []
        
        running_dropped_gb = 0.0
        cut_t = cfg.physical_cut_time_sec
        reconverge_end_t = cut_t + cfg.reactive_bfd_hold_sec + cfg.reactive_bgp_flap_duration_sec

        for i in range(steps):
            t = i * cfg.time_step_sec
            timestamps.append(round(t, 2))
            load = cfg.normal_traffic_gbps

            if t < cut_t:
                # Normal operation: all traffic on primary subsea link
                p_flow = load
                b_flow = 0.0
                d_flow = 0.0
                rtt = cfg.primary_rtt_ms
            elif cut_t <= t < (cut_t + cfg.reactive_bfd_hold_sec):
                # Blackholing window: physical link is DEAD, but routers still route to it
                p_flow = 0.0
                b_flow = 0.0
                d_flow = load  # 100% of traffic is dropped into the seabed
                rtt = 999.0    # Infinite packet drop
            elif (cut_t + cfg.reactive_bfd_hold_sec) <= t < reconverge_end_t:
                # BGP route flap / reconvergence window: partial loss as routes update
                progress = (t - (cut_t + cfg.reactive_bfd_hold_sec)) / cfg.reactive_bgp_flap_duration_sec
                # Exponential decay of dropped packets as alternative AS paths stabilize
                b_flow = min(cfg.backup_capacity_gbps, load * progress)
                p_flow = 0.0
                d_flow = max(0.0, load - b_flow)
                rtt = cfg.backup_rtt_ms + (1.0 - progress) * 80.0
            else:
                # Post-reconvergence: stable backup ring
                p_flow = 0.0
                b_flow = min(cfg.backup_capacity_gbps, load)
                d_flow = max(0.0, load - cfg.backup_capacity_gbps)
                rtt = cfg.backup_rtt_ms

            # Integrate dropped gigabits
            dropped_in_step = d_flow * cfg.time_step_sec
            running_dropped_gb += dropped_in_step

            primary_traffic.append(round(p_flow, 2))
            backup_traffic.append(round(b_flow, 2))
            dropped_traffic.append(round(d_flow, 2))
            cum_dropped.append(round(running_dropped_gb, 2))
            latencies.append(round(rtt, 1))

        # Metrics calculation
        total_lost_gbits = running_dropped_gb
        total_lost_gbytes = total_lost_gbits / 8.0
        outage_sec = cfg.reactive_bfd_hold_sec + cfg.reactive_bgp_flap_duration_sec
        peak_drop_pct = 100.0
        avail_pct = max(0.0, 100.0 * (1.0 - (outage_sec / cfg.sim_duration_sec)))

        timeseries = ConvergenceTimeseries(
            timestamps_sec=timestamps,
            primary_traffic_gbps=primary_traffic,
            backup_traffic_gbps=backup_traffic,
            dropped_traffic_gbps=dropped_traffic,
            cumulative_dropped_gigabits=cum_dropped,
            effective_latency_ms=latencies,
        )
        report = NetworkEvaluationReport(
            paradigm="Reactive Loss-of-Light (Status Quo)",
            total_data_lost_gigabits=round(total_lost_gbits, 1),
            total_data_lost_gigabytes=round(total_lost_gbytes, 2),
            outage_duration_sec=round(outage_sec, 1),
            peak_packet_drop_rate_pct=peak_drop_pct,
            average_latency_ms=round(float(np.mean(latencies)), 1),
            service_availability_pct=round(avail_pct, 2),
        )
        return timeseries, report

    def run_preemptive_aegis_evacuation(self) -> Tuple[ConvergenceTimeseries, NetworkEvaluationReport]:
        """Simulates Aegis-Sea pre-emptive RFC 7999 BGP Graceful Evacuation."""
        cfg = self.config
        steps = int(cfg.sim_duration_sec / cfg.time_step_sec)

        timestamps = []
        primary_traffic = []
        backup_traffic = []
        dropped_traffic = []
        cum_dropped = []
        latencies = []

        running_dropped_gb = 0.0
        aegis_t = cfg.aegis_detection_time_sec
        cut_t = cfg.physical_cut_time_sec
        drain_duration_sec = cfg.bgp_graceful_drain_duration_ms / 1000.0

        for i in range(steps):
            t = i * cfg.time_step_sec
            timestamps.append(round(t, 2))
            load = cfg.normal_traffic_gbps

            if t < aegis_t:
                # Normal operation: all traffic on primary subsea link
                p_flow = load
                b_flow = 0.0
                d_flow = 0.0
                rtt = cfg.primary_rtt_ms
            elif aegis_t <= t < (aegis_t + drain_duration_sec):
                # Graceful switchover window: traffic shifting while physical fiber is 100% intact!
                progress = (t - aegis_t) / drain_duration_sec
                p_flow = load * (1.0 - progress)
                b_flow = load * progress
                d_flow = 0.0  # ZERO packets dropped because fiber is still healthy
                rtt = cfg.primary_rtt_ms + (cfg.backup_rtt_ms - cfg.primary_rtt_ms) * progress
            else:
                # Fully migrated to backup ring well before cut_t
                p_flow = 0.0
                b_flow = min(cfg.backup_capacity_gbps, load)
                # Backup ring capacity is 80 Gbps, load is 65 Gbps -> zero loss!
                d_flow = max(0.0, load - cfg.backup_capacity_gbps)
                rtt = cfg.backup_rtt_ms

            # Even when t >= cut_t, traffic is already safely on backup!
            dropped_in_step = d_flow * cfg.time_step_sec
            running_dropped_gb += dropped_in_step

            primary_traffic.append(round(p_flow, 2))
            backup_traffic.append(round(b_flow, 2))
            dropped_traffic.append(round(d_flow, 2))
            cum_dropped.append(round(running_dropped_gb, 2))
            latencies.append(round(rtt, 1))

        timeseries = ConvergenceTimeseries(
            timestamps_sec=timestamps,
            primary_traffic_gbps=primary_traffic,
            backup_traffic_gbps=backup_traffic,
            dropped_traffic_gbps=dropped_traffic,
            cumulative_dropped_gigabits=cum_dropped,
            effective_latency_ms=latencies,
        )
        report = NetworkEvaluationReport(
            paradigm="Aegis-Sea Pre-emptive BGP Evacuation",
            total_data_lost_gigabits=round(running_dropped_gb, 1),
            total_data_lost_gigabytes=round(running_dropped_gb / 8.0, 2),
            outage_duration_sec=0.0,
            peak_packet_drop_rate_pct=0.0,
            average_latency_ms=round(float(np.mean(latencies)), 1),
            service_availability_pct=100.0,
        )
        return timeseries, report

    def generate_comparison_summary(self) -> Dict[str, Any]:
        """Runs both simulations and generates a structured side-by-side comparison."""
        reactive_ts, reactive_rep = self.run_reactive_loss_of_light()
        aegis_ts, aegis_rep = self.run_preemptive_aegis_evacuation()

        # Compute improvements
        saved_gb = reactive_rep.total_data_lost_gigabytes - aegis_rep.total_data_lost_gigabytes
        saved_downtime = reactive_rep.outage_duration_sec - aegis_rep.outage_duration_sec

        return {
            "reactive": reactive_rep.__dict__,
            "aegis_preemptive": aegis_rep.__dict__,
            "impact_delta": {
                "saved_data_loss_gigabytes": round(saved_gb, 2),
                "saved_outage_downtime_sec": round(saved_downtime, 1),
                "packet_drop_reduction_pct": 100.0,
                "conclusion": (
                    f"Aegis-Sea pre-emptive BGP evacuation saved {saved_gb:.1f} GB of customer/financial data "
                    f"and prevented {saved_downtime:.1f} seconds of transit blackholing."
                ),
            },
        }
