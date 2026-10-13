# Aegis-Sea Capstone Research Papers Library

This directory contains the full-text PDF research publications corresponding to the **15 core academic references across 7 domains** cited in the Aegis-Sea capstone project and research paper (*Fordham University CISC 6090: Capstone in Cybersecurity*).

---

> **Detailed Technical Mapping:** See [LITERATURE_MAPPING.md](../docs/LITERATURE_MAPPING.md) for the exact equations, empirical datasets, mathematical formulas, physical parameters, and codebase components mapped from each paper into Aegis-Sea.

---

## Paper Inventory & Mapping

| # | Filename | Paper Title & Authors | Venue / Source | File Size | Role in Aegis-Sea |
| :-: | :--- | :--- | :--- | :-: | :--- |
| **01** | `01_GeoTrackNet_Maritime_Anomaly_Detector.pdf` | **GeoTrackNet: A Maritime Anomaly Detector using Probabilistic Neural Network Representation of AIS Tracks and A Contrario Detection**<br/>*D. Nguyen, R. Vadaine, G. Hajduch, R. Garello, R. Fablet* | IEEE T-ITS / arXiv:1912.00682 | 17.3 MB | Foundational reference for probabilistic track representations (VRNNs) and statistical *a contrario* false-alarm suppression. |
| **02** | `02_Recurrent_Encoder_Decoder_Vessel_Trajectory_Braca_Willett.pdf` | **Recurrent Encoder-Decoder Networks for Vessel Trajectory Prediction with Uncertainty Estimation**<br/>*S. Capobianco, N. Forti, L. M. Millefiori, P. Braca, P. Willett* | IEEE TAES / arXiv:2205.05404 | 2.25 MB | Provides stochastic kinematic modeling (Ornstein-Uhlenbeck / Bayesian recurrent) justifying speed and course anomaly factors ($S_{\text{speed}}$, $S_{\text{heading}}$). |
| **03** | `03_AIS_Unified_Trajectory_Anomaly_Detection_Risk_Assessment.pdf` | **AIS-LLM: A Unified Framework for Maritime Trajectory Prediction, Anomaly Detection, and Collision Risk Assessment**<br/>*H. Park, J. Jung, M. Seo, D. Choi et al.* | arXiv:2508.07668 | 3.17 MB | Theoretical justification for multi-task trajectory modeling, signal gap penalties ($S_{\text{dark}}$), and kinematic state reconstruction. |
| **04** | `04_Security_Evaluation_of_AIS_Balduzzi.pdf` | **A Security Evaluation of AIS Automated Identification System**<br/>*M. Balduzzi, A. Pasta, K. Wilhoit* | ACM ACSAC / Trend Micro Research | 1.22 MB | Foundational vulnerability analysis establishing that AIS lacks encryption, authentication, and replay protection. |
| **05** | `05_Space_Based_Maritime_Surveillance_Data_Fusion_Braca_Willett.pdf` | **Space-Based Global Maritime Surveillance: Artificial Intelligence and Data Fusion Techniques**<br/>*G. Soldi, P. Braca, P. Willett, A. Farina et al.* | IEEE A&E Systems Magazine | 6.90 MB | Multi-sensor correlation framework for cross-verifying AIS telemetry against secondary sensors and radar to defeat spoofing. |
| **06** | `06_SeaSpoofFinder_GNSS_AIS_Manipulation.pdf` | **SeaSpoofFinder: Potential GNSS Spoofing Event Detection Using AIS**<br/>*T. Willems et al.* | IEEE TDSC / DLR / arXiv:2402.16257 | 3.62 MB | Advanced spatiotemporal filtering separating individual vessel tampering from regional electronic warfare (Baltic/Black Sea GPS jamming). |
| **07** | `07_Undersea_Cables_Indispensable_Insecure_Sunak.pdf` | **Undersea Cables: Indispensable, Insecure and Vulnerable to Hybrid Warfare**<br/>*R. Sunak MP (Foreword by Adm. Sir S. Peach)* | Policy Exchange Research Monograph | 2.37 MB | Geopolitical framing establishing the critical exposure of undersea fiber conduits to asymmetric gray-zone sabotage. |
| **08** | `08_Protecting_Maritime_Infrastructure_Hybrid_Threats_Sari.pdf`<br/>`08b_Baltic_Sea_Cable_Sabotage_Tactics_Praks.pdf` | **Protecting Maritime Infrastructure from Hybrid Threats: Legal & Operational Options** / **Russia's Hybrid Threat Tactics Against the Baltic Sea Region**<br/>*A. Sari / H. Praks* | European Centre of Excellence for Countering Hybrid Threats (Hybrid CoE) / NATO | 4.53 MB | Forensic legal and operational analysis of the *Yi Peng 3* and *Newnew Polar Bear* Baltic Sea anchor-dragging incidents used as ground truths. |
| **09** | `09_Cyber_Physical_Threat_Modeling_IEEE_Access.pdf` | **Cyber-Physical Systems Security: Threat Modeling, Risk Assessment, and Case Studies**<br/>*IEEE Access Open Research Consortium* | IEEE Access, Vol. 9 | 8.06 MB | Structural methodology for bridging logical cyber metrics with physical infrastructure state variables. |
| **10** | `10_Vessel_Detection_DAS_Submarine_Optical_Cables.pdf` | **Vessel Detection and Localization Using Distributed Acoustic Sensing in Submarine Optical Fiber Cables**<br/>*E. E. Ramirez-Torres, J. Macias-Guarasa, M. Gonzalez-Herraez et al.* | IEEE J-STARS / arXiv:2509.11614 | 12.0 MB | Identifies dark optical fibers as continuous acoustic strain sensors along submarine cables, contextualizing Aegis-Sea's multi-sensor fusion. |
| **11** | `11_MultiSensor_Maritime_AIS_SAR_Graziano.pdf` | **Integration of Automatic Identification System (AIS) Data and Synthetic Aperture Radar (SAR) for Maritime Situational Awareness**<br/>*M. D. Graziano, A. Renga, A. Moccia* | Remote Sensing (MDPI) | 13.2 MB | Architectural model for correlating spatial geometries with dynamic vessel positions, satellite imagery, and velocity estimation. |
| **12** | `12_SDN_Local_Fast_Failover_Resilience_Schmid.pdf` | **On the Feasibility of Perfect Resilience with Local Fast Failover in Software-Defined Networks**<br/>*K.-T. Foerster, J. Hirvonen, Y.-A. Pignolet, S. Schmid* | IEEE/ACM ToN / arXiv:2006.06513 | 1.34 MB | Design blueprint for data-plane fast-failover mechanisms responding to physical infrastructure alarms. |
| **13** | `13_Nautilus_Cross_Layer_Submarine_Cables_IP_Links.pdf` | **Nautilus: A Framework for Cross-Layer Cartography of Submarine Cables and IP Links**<br/>*A. Ramanathan, S. Abdu Jyothi* | ACM SIGCOMM / arXiv:2302.14201 | 6.46 MB | Cross-layer mapping framework linking logical Internet IP links directly to physical submarine cable routing. |
| **14** | `14_Bakdi_AIS_Vessel_Risk_Adaptive_Safety_Domain.pdf` | **AIS-Based Multiple Vessel Collision and Grounding Risk Identification based on Adaptive Safety Domain**<br/>*A. Bakdi, I. K. Glad, E. Vanem, O. J. Rodseth* | Journal of Marine Science and Engineering (JMSE) | 2.03 MB | Direct mathematical foundation for designing multi-criteria spatial-temporal risk scoring indices and adaptive vessel safety domains. |
| **15** | `15_Quantitative_CPS_Threat_Assessment_Attack_Defense.pdf` | **Cyber-Physical System Threat Assessment and Attack-Defense Modeling: A Game-Theoretic Framework**<br/>*MDPI Electronics Research Consortium* | Electronics (MDPI) | 8.20 MB | Formal justification for composite scoring algorithms with probabilistic upper bounds and attack-defense state transitions. |

---

## Academic Program Metadata

- **Institution:** Fordham University
- **Department:** Department of Computer and Information Sciences
- **Course:** CISC 6090: Capstone in Cybersecurity (Fall 2026)
- **Advisor:** Dr. Thaier Hayajneh, University Professor & Director, Center for Cybersecurity
- **Student Researcher:** Rayed Jawad (`rjawad1@fordham.edu`)
- **Deliverable Milestone:** Related Work Literature Review (Due: Oct 17, 2026)
