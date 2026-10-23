# Aegis-Sea Red Team Simulation Testbed: Experimental Results

**Project:** Aegis-Sea: Resilient Cyber-Physical Threat Intelligence & Incident Response for Subsea Cables
**Research Context:** Fordham University Capstone in Cybersecurity (CISC 6090)
**Student Researcher:** Rayed Jawad (`rjawad1@fordham.edu`)
**Faculty Advisor:** Dr. Juntao Chen
**Course Instructor:** Dr. Thaier Hayajneh

---

## 1. Executive Summary

To address the research question proposed by Dr. Juntao Chen—*whether maritime defenses can still detect and respond correctly when adversaries manipulate the underlying telemetry*—we constructed an adversarial red-team simulation testbed. We benchmarked a standard **Naive Geofencing Baseline** (geofence proximity + dragging velocity) against **Aegis-Sea's Trust-Aware Multi-Factor Engine** across three attack scenarios.

### Key Comparative Findings

| Attack Scenario | Ground Truth | Naive Geofencing (Baseline) | Aegis-Sea (Trust Layer) | Operational Impact |
| :--- | :---: | :---: | :---: | :--- |
| **Ground-Truth Anchor Dragging Sabotage** | `GENUINE_ATTACK` | TRUE_POSITIVE<br/>*(Detected)* | TRUE_POSITIVE<br/>*(Detected & Pre-emptive Failover Armed)* | Both systems detect the threat; Aegis-Sea validates track kinematics and arms pre-emptive BGP evacuation. |
| **GPS Coordinate Jump / SDR Telemetry Spoofing** | `ADVERSARIAL_SPOOFING` | FALSE_POSITIVE<br/>*(Fooled by Spoofed Fix)* | FALSE_ALARM_SUPPRESSED<br/>*(Kinematic Jump Filter Activated)* | Naive geofencing blindly triggers emergency failover. Aegis-Sea flags 240 kn jump and suppresses false alarm. |
| **Phantom Ghost Ship Decoy (Failover DoS)** | `GHOST_DECOY_ATTACK` | FALSE_POSITIVE<br/>*(Unnecessary Network Reroute Triggered)* | FAILOVER_HELD<br/>*(Requires Target Verification Before Route Drain)* | Naive geofencing causes traffic disruption. Aegis-Sea identifies phantom contact and mandates verification. |

---

## 2. Quantitative Accuracy & False Alarm Analysis

- **Naive Geofencing Detection Accuracy:** `33.3%` (1/3). While it detects physical sabotage, it suffers a **100% False Positive Rate under adversarial spoofing**, blindly triggering emergency BGP traffic failovers on non-existent or manipulated threats.
- **Aegis-Sea Detection Accuracy:** `100.0%` (3/3). Aegis-Sea successfully differentiates physical maritime sabotage from digital telemetry injection.
  - **Kinematic Jump Suppression:** Catches impossible velocity deltas ($>35\text{ kn}$) caused by SDR position injection, suppressing false anchor-drop alarms.
  - **Decoy Failover Safety Gate:** Detects unverified phantom targets appearing abruptly in the Cable Protection Zone (CPZ) and holds traffic rerouting until target verification.

---

## 3. Detailed Scenario Breakdowns

### SCENARIO-01: Ground-Truth Anchor Dragging Sabotage
- **Ground Truth:** `GENUINE_ATTACK`
- **Scenario Profile:** Vessel decelerates from 10.5 kn to 1.2 kn inside C-Lion1 3 NM CPZ, dragging for 45 min
- **Naive Baseline:** Level `CRITICAL` | Action: `TRIGGER_PREEMPTIVE_FAILOVER` | Verdict: `TRUE_POSITIVE (Detected)`
- **Aegis-Sea Engine:** Threat Score `80.9/100.0` (HIGH) | Trust Status: `VALID_TELEMETRY` | Action: `DISPATCH_SOAR_ALERT`
- **Outcome Analysis:** Both systems detect the threat; Aegis-Sea validates track kinematics and arms pre-emptive BGP evacuation.

### SCENARIO-02: GPS Coordinate Jump / SDR Telemetry Spoofing
- **Ground Truth:** `ADVERSARIAL_SPOOFING`
- **Scenario Profile:** Coordinate teleports 2.0 NM in 30s (implied 240 kn velocity) to trigger false alarm
- **Naive Baseline:** Level `CRITICAL` | Action: `TRIGGER_PREEMPTIVE_FAILOVER` | Verdict: `FALSE_POSITIVE (Fooled by Spoofed Fix)`
- **Aegis-Sea Engine:** Threat Score `46.8/100.0` (ADVISORY) | Trust Status: `FLAGGED_JUMP (239.76 kn)` | Action: `INCREASE_MONITORING_FREQUENCY`
- **Outcome Analysis:** Naive geofencing blindly triggers emergency failover. Aegis-Sea flags 240 kn jump and suppresses false alarm.

### SCENARIO-03: Phantom Ghost Ship Decoy (Failover DoS)
- **Ground Truth:** `GHOST_DECOY_ATTACK`
- **Scenario Profile:** Fabricated target appears abruptly inside 3 NM CPZ with 0 prior history at dragging speed
- **Naive Baseline:** Level `CRITICAL` | Action: `TRIGGER_PREEMPTIVE_FAILOVER` | Verdict: `FALSE_POSITIVE (Unnecessary Network Reroute Triggered)`
- **Aegis-Sea Engine:** Threat Score `58.0/100.0` (ADVISORY) | Trust Status: `GHOST_CANDIDATE_FLAGGED` | Action: `INCREASE_MONITORING_FREQUENCY`
- **Outcome Analysis:** Naive geofencing causes traffic disruption. Aegis-Sea identifies phantom contact and mandates verification.
