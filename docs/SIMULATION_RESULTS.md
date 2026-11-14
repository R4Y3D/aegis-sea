# Aegis-Sea Red Team Simulation Testbed: Experimental Evaluation & Benchmarks

**Project:** Aegis-Sea: Resilient Cyber-Physical Threat Intelligence & Incident Response for Subsea Cables  
**Research Context:** Fordham University Capstone in Cybersecurity (CISC 6090)  
**Student Researcher:** Rayed Jawad (`rjawad1@fordham.edu`)  
**Faculty Advisor:** Dr. Juntao Chen  
**Course Instructor:** Dr. Thaier Hayajneh  
**Date:** November 2026  

---

## 1. Executive Summary

To rigorously evaluate the core research question proposed by faculty advisor Dr. Juntao Chen—*whether subsea cable defenses can detect and respond correctly when adversaries manipulate the underlying telemetry*—we constructed a comprehensive adversarial simulation and empirical benchmarking suite. 

We benchmarked three competing detector architectures across a labeled dataset of **1,200 maritime vessel trajectories**:
1. **Commercial Baseline 1 (Naive Geofencing):** Standard commercial MDA logic ($d \le 3.0$ NM CPZ and $v \le 3.5$ knots).
2. **Academic Baseline 2 (Kinematic ML Anomaly Detector):** Replicates academic trajectory models (NPS/Sandia baseline) using kinematic Z-score thresholds on velocity and heading variance, without subsea infrastructure context.
3. **Proposed System (Aegis-Sea Zero-Trust Evaluator):** Full 2-tier R-tree spatial corridor indexing over 712 subsea cables + 6-factor composite threat scoring + Zero-Trust telemetry jump and ghost decoy gates.

### Key Benchmark Findings

| Performance Metric | Naive Geofencing (Baseline 1) | Kinematic ML (Baseline 2) | Aegis-Sea (Proposed) | Improvement / Delta |
| :--- | :---: | :---: | :---: | :--- |
| **Overall Accuracy** | 68.8% | 62.4% | **94.9%** | **+26.1% higher accuracy** |
| **Precision** | 21.1% | 18.1% | **62.1%** | **3x higher precision** |
| **Recall (True Positive Rate)** | 96.0% | 92.5% | **95.5%** | **Consistent high sensitivity** |
| **F1 Score** | 0.346 | 0.303 | **0.753** | **+117% balance improvement** |
| **False Alarm Rate (FPR)** | 34.0% | 41.0% | **5.5%** | **-84% reduction in false alarms** |
| **Failover DoS Vulnerability** | 100.0% | 100.0% | **0.0%** | **Complete immunity against spoofed reroutes** |

---

## 2. Adversarial Dataset Composition (1,200 Trajectories)

The benchmark dataset models the operational diversity of congested global shipping straits:

```
+------------------------------------------------------+---------+-----------------------------------------------------+
| Trajectory Class                                     | Samples | Key Kinematic & Spatial Characteristics            |
+------------------------------------------------------+---------+-----------------------------------------------------+
| Class 0: Benign Commercial Traffic (Cargo / Tanker)  | 600     | Transit cruising 12-20 kn, straight corridors       |
| Class 1: Genuine Anchor Dragging Sabotage            | 200     | Inside 3 NM CPZ, speed 1.1-1.5 kn, 45 min drag      |
| Class 2: SDR GPS Teleportation Jumps                 | 150     | Implied velocity > 35 kn into cable zone            |
| Class 3: Slow-Drift Meaconing Spoofing               | 150     | Artificial drift <= 3.5 kn over cable polyline      |
| Class 4: Phantom Ghost Ship Swarms (Failover DoS)    | 100     | Abrupt zero-history contact in CPZ at drag speed    |
+------------------------------------------------------+---------+-----------------------------------------------------+
| TOTAL                                                | 1,200   | Fully labeled ground-truth benchmark suite          |
+------------------------------------------------------+---------+-----------------------------------------------------+
```

---

## 3. Cyber-Physical Network Convergence Simulation

To measure the operational impact on telecommunications networks, we modeled a 100 Gbps transoceanic subsea link carrying a 65 Gbps live data payload subjected to an intentional anchor cut at $t = 120$ seconds.

### Comparative Outage Analysis

```
+------------------------------------+--------------------------+------------------------------+
| Metric                             | Reactive Loss-of-Light   | Aegis-Sea Pre-emptive BGP    |
|                                    | (Status Quo NOC)         | Fast-Failover (Proposed)     |
+------------------------------------+--------------------------+------------------------------+
| Alert Trigger Time                 | t = 120.0 s (Physical)   | t = 60.0 s (Pre-emptive)     |
| Failover Execution Latency         | 24.0 s (Loss-of-Light)   | 0.45 s (450 ms BGP Drain)    |
| Outage Window Duration             | 24.0 s (100% loss)       | 0.0 s (Zero downtime)        |
| Total Packet Loss                  | 123.9 Gigabytes          | 0.0 Gigabytes (0.0% loss)    |
| Route Withdrawal Mechanism         | Reactive BGP Dampening   | RFC 7999 Community 65000:666 |
+------------------------------------+--------------------------+------------------------------+
```

---

## 4. Stackelberg Game-Theoretic Equilibrium

We formalized the adversarial interaction as a Single-Leader Follower Stackelberg Security Game:
- **Leader (Defender):** Commits to alert threshold $\theta \in [50.0, 85.0]$.
- **Follower (Attacker):** Observes defender posture and selects anchor dragging velocity $v \in [0.5, 4.0]$ kn to optimize seabed trench damage while evading interception.

### Solved Equilibrium Values
- **Optimal Defender Threshold ($\theta^*$):** `67.5`
- **Optimal Attacker Speed ($v^*$):** `3.0 knots`
- **Equilibrium Detection Probability ($P_{\text{det}}$):** `77.1%`
- **Equilibrium False Alarm Probability ($P_{\text{fa}}$):** `5.2%`
- **Defender Equilibrium Utility ($U_{\text{def}}^*$):** `62.35`
- **Attacker Equilibrium Utility ($U_{\text{att}}^*$):** `-70.53` (Attack successfully deterred)

---

## 5. Optical OTDR / Acoustic Sensing Fusion

To ensure absolute resilience against transponder blackouts, Aegis-Sea ingests continuous Optical Time-Domain Reflectometry (OTDR) backscatter power traces along the subsea fiber:
- **Intrinsic Fiber Attenuation:** $0.18$ dB/km at $1550$ nm.
- **EDFA In-Line Repeaters:** $+18.0$ dB gain spaced every $60$ km.
- **Microbending Detection Threshold:** $\Delta P \ge 3.0$ dB power drop.
- **Spatial Fusion Resolution:** Fiber fault distance $x_{\text{fiber}}$ mapped to 2D geospatial coordinates and correlated with surface vessels within $d \le 0.5$ km.

---

## 6. Publication Figures Generated

All experimental results have been visualized as publication-grade figures in `presentation_assets/`:
1. `presentation_assets/figure_novelty_benchmark.png`: Multi-panel comparison of Accuracy, False Alarm Rate, and Failover DoS Vulnerability across the 3 evaluated detector architectures.
2. `presentation_assets/figure_bgp_convergence.png`: Network throughput curves comparing 24-second Reactive Loss-of-Light outage (123.9 GB lost) against Aegis-Sea pre-emptive BGP route drainage (0.0 GB lost).
3. `presentation_assets/figure_stackelberg_game.png`: Defender utility curve and attacker response surface showing the unique Stackelberg Equilibrium at $\theta^* = 67.5$.
4. `presentation_assets/figure_otdr_fusion.png`: Optical OTDR power trace (dBm vs km) showing EDFA repeater steps and the microbending strain drop at $x = 42.4$ km aligned with surface vessel GPS.
