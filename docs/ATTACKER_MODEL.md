# Aegis-Sea Attacker Model & Adversary Taxonomy

**Project:** Aegis-Sea — Resilient Cyber-Physical Defense for Undersea Infrastructure  
**Course:** CISC 6090: Capstone in Cybersecurity, Fordham University  
**Student Researcher:** Rayed Jawad (`rjawad1@fordham.edu`)  
**Project Advisor:** Dr. Juntao Chen  
**Course Instructor:** Dr. Thaier Hayajneh  

---

## 1. Executive Summary

Traditional maritime monitoring systems assume that vessel surveillance data is truthful. However, the Automatic Identification System (AIS) operates over unauthenticated, unencrypted VHF radio, creating an expansive attack surface. 

In this attacker model, we formalize the capabilities, constraints, and attack vectors of adversaries targeting undersea fiber-optic cables. Rather than treating cable cuts merely as accidents, Aegis-Sea addresses deliberate **cyber-physical sabotage** where the adversary physically targets seabed infrastructure while simultaneously exploiting or manipulating the telemetry used to detect them.

---

## 2. Why Undersea Defense Is Fundamentally Unique

Undersea infrastructure security differs dramatically from traditional land-based enterprise network security across three core dimensions:

| Dimension | Land-Based Network Security | Undersea Infrastructure Defense |
| :--- | :--- | :--- |
| **Physical Accessibility** | Datacenters, switches, and conduits can be physically accessed, inspected, and repaired by on-site technicians within minutes or hours. | Cables rest on the seabed at depths up to 3,000–6,000 meters. Visual inspection requires specialized ROVs (Remotely Operated Vehicles), and physical repairs require specialized cable ships that take **weeks to months** to deploy. |
| **Legal & Jurisdictional Vacuum** | Sovereign law enforcement can immediately enter private or public land to halt sabotage or investigate suspicious actors. | Under the UN Convention on the Law of the Sea (UNCLOS Articles 56, 79, 113), coastal states have limited legal authority to board, inspect, or intercept foreign-flagged commercial vessels in international waters or Exclusive Economic Zones (EEZ) prior to actual damage. |
| **Cost & Impact Asymmetry** | Attackers typically need network access, zero-days, or insider credentials. Damaged fiber conduits can often be bypassed by local rerouting. | A $500 software-defined radio and an ordinary merchant anchor can sever cables carrying **>95% of intercontinental traffic** and **$10 trillion in daily transactions**, causing tens of millions of dollars in repair costs and global latency penalties. |

---

## 3. Threat Actor Taxonomy

We identify three distinct threat actor profiles operating in the maritime cyber-physical domain:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        THREAT ACTOR PROFILES                           │
│                                                                        │
│   [ State-Sponsored Gray-Zone ]        [ Cyber / Electronic Adversary ]│
│   • Covert sabotage orders            • Software-Defined Radios (SDR)  │
│   • Commercial flags of convenience   • AIS spoofing & ghost tracks    │
│   • Plausible deniability ("drag")    • Intentional false failover DoS │
│                                                                        │
│   [ Negligent / Compromised Merchant ]                                 │
│   • Improper anchoring in CPZ corridors                                │
│   • Cyber-compromised electronic chart display (ECDIS)                 │
│   • Failure to respect Notices to Mariners                             │
└────────────────────────────────────────────────────────────────────────┘
```

1. **State-Sponsored Hybrid / Gray-Zone Actors:**
   - *Motivation:* Geopolitical coercion, intelligence gathering, strategic infrastructure denial during conflict or pre-conflict phases.
   - *Method:* Tasking commercial merchant vessels (bulk carriers, container ships, trawlers) flying flags of convenience to drop anchor across designated cable corridors while maintaining engine propulsion.
   - *Historical Ground Truth:* The *Newnew Polar Bear* (severed Balticconnector pipeline and telecom cable in Oct 2023 by dragging its anchor for 180 km at 1.1–3.0 kn) and the *Yi Peng 3* (severed C-Lion1 and BCS East-West cables in Nov 2024 by dragging anchor for >100 NM).

2. **Cyber & Electronic Warfare Adversaries:**
   - *Motivation:* Blind coastal defenses, mask covert operations, or induce self-inflicted Denial of Service (DoS) on network capacity.
   - *Method:* Deploying Software-Defined Radios (SDRs) to broadcast fabricated AIS messages, spoof vessel coordinates, or simulate phantom emergency collision/anchoring alerts.

3. **Negligent or Compromised Commercial Operators:**
   - *Motivation:* Operational convenience, navigational error, or steering failure in adverse weather.
   - *Method:* Anchoring inside charted Cable Protection Zones (CPZs) or drifting unmonitored over cable trenches with compromised Electronic Chart Display and Information Systems (ECDIS).

---

## 4. Adversary Capabilities & Resources

An adversary targeting undersea infrastructure has access to the following technical capabilities:

* **RF Broadcast Equipment:** Low-cost, commercially available Software-Defined Radios (HackRF One, BladeRF, USRP) costing \$200–\$1,000, capable of transmitting on AIS maritime VHF frequencies (161.975 MHz and 162.025 MHz).
* **Protocol Manipulation:** Complete control over unauthenticated AIVDM/AIVDO AIS message sentences (e.g., Type 1/2/3 Position Reports, Type 5 Static Data, Type 24 Reports), allowing arbitrary manipulation of MMSI, latitude, longitude, Speed Over Ground (SOG), Course Over Ground (COG), and True Heading.
* **Transponder Power Control:** Ability to physically power off or disconnect the ship's Class A transponder or GPS antenna via bridge switches, producing arbitrary periods of surveillance darkness.
* **Seamanship & Mechanical Control:** Control over the vessel’s winches and main propulsion, enabling slow, high-torque dragging of port/starboard anchors at 1.0–3.5 knots across ocean trenches.

---

## 5. Adversarial Attack Vectors

Aegis-Sea models five concrete attack vectors combining physical mechanics with telemetry manipulation:

```
V1: Slow Anchor-Dragging (Physical Anchor Sabotage)
    [Cruising: 14 kn] ──► [Anchor Dropped] ──► [Sustained Drag: 1.5–3.5 kn across cable]

V2: Transponder Blackout ("Going Dark")
    [Broadcasting AIS] ──► [Transponder Switched Off 2 NM out] ──► [Silent Crossing]

V3: Kinematic Jump & Coordinate Spoofing
    [Real Ship at Cable] ──► [Fake AIS reports ship 25 NM away in authorized anchorage]

V4: Ghost Ship Decoy (False-Failover DoS)
    [No Ship Exists] ──► [SDR injects fake dragging ship atop cable] ──► [Forces BGP Failover]

V5: Regional GPS Interference Noise
    [Regional Jamming in Baltic] ──► [Dozens of ships show erratic coordinate jitter]
```

### Vector 1: Slow Anchor-Dragging Sabotage (Physical Baseline)
- **Description:** A ship drops anchor in shallow waters (< 100m) while under engine power, dragging the anchor flukes through the seabed until hooking and snapping subsea fiber conduits.
- **Kinematic Signature:** Speed drops from cruising (12–24 kn) to dragging speed (1.0–3.5 kn) with course aligned either parallel to the cable trench (maximum physical exposure) or perpendicular (high-force shear intercept).

### Vector 2: Transponder Blackout ("Going Dark")
- **Description:** The crew powers down the vessel’s AIS transponder upon approaching a cable corridor, exploiting coastal radar gaps and cloud cover to sever the cable without leaving a continuous digital trail.
- **Defense Requirement:** The system must detect sudden transponder silence near a cable corridor, retain the contact state, calculate a dead-reckoning trajectory projection, and escalate a high-priority blackout alert ($S_{\text{dark}}$).

### Vector 3: Kinematic Jump & Coordinate Spoofing
- **Description:** The adversary transmits falsified GPS coordinates so the ship appears to be miles away in a safe, designated anchorage, while in reality the physical vessel is dragging anchor over a restricted cable zone.
- **Defense Requirement:** Telemetry jump filters must calculate the implied speed between consecutive pings ($\Delta d / \Delta t$). Implausible velocities (> 35 knots for commercial displacement hulls) are flagged as telemetry manipulation artifacts.

### Vector 4: Ghost Ship Decoys (Denial of Service on Network Capacity)
- **Description:** The attacker broadcasts fabricated AIS pings of a phantom vessel dragging an anchor across a high-capacity intercontinental cable (e.g., MAREA or C-Lion1).
- **Objective:** Tricking automated security systems into triggering emergency BGP route failover. Rerouting hundreds of terabits to secondary paths saturates backup links, creating a self-inflicted network outage.
- **Defense Requirement:** Aegis-Sea’s trust layer evaluates historical track continuity, signal plausibility, and secondary sensor confirmation before recommending automated traffic rerouting.

### Vector 5: Regional Electronic Warfare & GPS Interference
- **Description:** Widespread GNSS jamming and spoofing (common in the Baltic Sea and Eastern Mediterranean) creates correlated coordinate jitter across hundreds of civilian ships.
- **Defense Requirement:** Aegis-Sea incorporates spatial clustering logic (Willems et al., 2026). When multi-vessel coordinate displacements are correlated across a region, the system diagnoses regional electronic warfare noise rather than an isolated cable attack.

---

## 6. Trust-Aware Defense Principles

To defend against these vectors, Aegis-Sea operates under three core cybersecurity principles:

1. **Zero-Trust Telemetry:** AIS messages are treated as unauthenticated sensor inputs. Telemetry must be verified against kinematic laws (maximum velocity, realistic acceleration) and continuity checks before being accepted as truthful.
2. **Multi-Factor Convergence:** Physical alarms are never triggered on a single variable (e.g., proximity alone). Alerts require simultaneous corroboration across distance, speed, dwell time, and heading to prevent false positives.
3. **Pre-Emptive Autonomous Response:** Because physical repair takes weeks and naval interdiction is legally constrained in international waters, network mitigation (SDN BGP traffic drainage) must execute automatically in seconds *before* the physical cable is severed.
