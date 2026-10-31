"""
Builds the complete 11-slide PowerPoint presentation (.pptx) for:
Aegis-Sea: Resilient Cyber-Physical Threat Intelligence & Automated Incident Response
Fordham University CISC 6090: Capstone in Cybersecurity
Student: Rayed Jawad (rjawad1@fordham.edu)
Advisor: Dr. Juntao Chen
Instructor: Dr. Thaier Hayajneh
Date: October 31, 2026
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

ASSETS_DIR = os.path.join(os.getcwd(), 'presentation_assets')
PPTX_PATH = os.path.join(os.getcwd(), 'Aegis_Sea_Progress_Report_Rayed_Jawad.pptx')

# Color Palette (Dark Cybersecurity Theme)
BG_COLOR = RGBColor(11, 17, 30)        # #0b111e Deep Navy
CARD_BG = RGBColor(19, 29, 49)        # #131d31 Slate Navy
CARD_BORDER = RGBColor(30, 41, 59)    # #1e293b Slate Border
CYAN_ACCENT = RGBColor(56, 189, 248)  # #38bdf8 Neon Cyan
WHITE_TEXT = RGBColor(255, 255, 255)  # #ffffff Pure White
MUTED_TEXT = RGBColor(148, 163, 184)  # #94a3b8 Muted Slate
BODY_TEXT = RGBColor(203, 213, 225)   # #cbd5e1 Light Slate
RED_ACCENT = RGBColor(239, 68, 68)    # #ef4444 Crimson
YELLOW_ACCENT = RGBColor(234, 179, 8) # #eab308 Amber Gold
GREEN_ACCENT = RGBColor(34, 197, 94)  # #22c55e Emerald Green
PURPLE_ACCENT = RGBColor(192, 132, 252)# #c084fc Electric Purple


def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def set_slide_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text="AEGIS-SEA // CISC 6090 CYBERSECURITY CAPSTONE"):
        # Header banner
        header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(1.0))
        tf = header_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p0 = tf.paragraphs[0]
        p0.text = category_text.upper()
        p0.font.size = Pt(11)
        p0.font.bold = True
        p0.font.color.rgb = CYAN_ACCENT

        p1 = tf.add_paragraph()
        p1.text = title_text
        p1.font.size = Pt(24)
        p1.font.bold = True
        p1.font.color.rgb = WHITE_TEXT

    def add_card(slide, left, top, width, height, border_color=CARD_BORDER, fill_color=CARD_BG):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = fill_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1.5)
        return card

    def set_notes(slide, notes_text):
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = notes_text.strip()

    # =========================================================================
    # SLIDE 1: Title & Academic Context
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide1)

    # Decorative top glow bar
    top_glow = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.8), Inches(11.733), Inches(0.06))
    top_glow.fill.solid()
    top_glow.fill.fore_color.rgb = CYAN_ACCENT
    top_glow.line.fill.background()

    # Main Title Box
    title_box = slide1.shapes.add_textbox(Inches(0.8), Inches(1.2), Inches(11.733), Inches(2.6))
    tf1 = title_box.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = tf1.margin_right = tf1.margin_bottom = 0

    p_sub = tf1.paragraphs[0]
    p_sub.text = "FORDHAM UNIVERSITY · CISC 6090: CAPSTONE IN CYBERSECURITY"
    p_sub.font.size = Pt(13)
    p_sub.font.bold = True
    p_sub.font.color.rgb = CYAN_ACCENT

    p_main = tf1.add_paragraph()
    p_main.text = "Aegis-Sea: Resilient Cyber-Physical Threat Intelligence & Automated Incident Response"
    p_main.font.size = Pt(28)
    p_main.font.bold = True
    p_main.font.color.rgb = WHITE_TEXT

    p_tag = tf1.add_paragraph()
    p_tag.text = "Defending 712 Undersea Fiber-Optic Cables Against Anchor-Dragging Sabotage & Telemetry Manipulation"
    p_tag.font.size = Pt(16)
    p_tag.font.color.rgb = BODY_TEXT

    # 4 Metadata Cards
    cards_data = [
        ("STUDENT AUTHOR", "Rayed Jawad", "rjawad1@fordham.edu\nM.S. Cybersecurity Candidate", CYAN_ACCENT),
        ("PROJECT ADVISOR", "Dr. Juntao Chen", "Associate Professor, CIS\nSecurity & Resilient Systems", GREEN_ACCENT),
        ("COURSE INSTRUCTOR", "Dr. Thaier Hayajneh", "Professor & Graduate Director\nCybersecurity Programs", YELLOW_ACCENT),
        ("DELIVERABLE", "Midterm Progress Report", "Presentation & Live 3D Demo\nOctober 31, 2026", PURPLE_ACCENT),
    ]

    card_w = 2.75
    gap = 0.24
    start_x = 0.8
    y_card = 4.1

    for idx, (lbl, name, detail, col) in enumerate(cards_data):
        x = start_x + idx * (card_w + gap)
        add_card(slide1, x, y_card, card_w, 2.4, border_color=col)

        tb = slide1.shapes.add_textbox(Inches(x + 0.15), Inches(y_card + 0.15), Inches(card_w - 0.3), Inches(2.1))
        tf = tb.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.text = lbl
        p0.font.size = Pt(10)
        p0.font.bold = True
        p0.font.color.rgb = col

        p1 = tf.add_paragraph()
        p1.text = name
        p1.font.size = Pt(16)
        p1.font.bold = True
        p1.font.color.rgb = WHITE_TEXT

        p2 = tf.add_paragraph()
        p2.text = detail
        p2.font.size = Pt(11)
        p2.font.color.rgb = MUTED_TEXT

    set_notes(slide1, """
Good afternoon Dr. Chen, Dr. Hayajneh, and colleagues.

I am Rayed Jawad, and today I am presenting the Midterm Progress Report for my Cybersecurity Capstone project: Aegis-Sea.

Aegis-Sea is a resilient cyber-physical threat intelligence and automated incident response engine designed to protect global submarine fiber-optic cables against gray-zone sabotage and telemetry spoofing.

In this presentation, I will cover our project goals, our progress across Milestones 0, 1, and 2, our academic paper outline, what remains to be done in Phase 3, our semester timeline, and a live 3D demonstration of our working defense engine.
""")

    # =========================================================================
    # SLIDE 2: Motivation & Undersea Cybersecurity Problem
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide2)
    add_header(slide2, "Motivation: The Undersea Infrastructure Crisis & AIS Insecurity")

    # Left Card: Physical Undersea Criticality
    add_card(slide2, 0.8, 1.6, 5.6, 5.2, border_color=CYAN_ACCENT)
    tb_l = slide2.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.8))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True

    p = tf_l.paragraphs[0]
    p.text = "THE PHYSICAL CRITICAL BACKBONE"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = CYAN_ACCENT

    items_l = [
        ("95%+ Global Internet Traffic:", "More than 95% of all transcontinental communications and over $10 Trillion in daily financial transactions travel via 712 seabed fiber cables."),
        ("Physical Fragility:", "Subsea cables are often no thicker than a garden hose, resting unmonitored on the seabed in international waters."),
        ("Recent Sabotage Precedents:", "In 2023, the Newnew Polar Bear severed Balticconnector. In November 2024, the Yi Peng 3 dragged its anchor for over 100 miles, severing the C-Lion1 and BCS cables under the guise of an 'accidental equipment failure.'"),
        ("Asymmetric Repair Costs:", "A $500 anchor drop inflicts tens of millions of dollars in downtime; specialized repair ships take weeks or months to arrive."),
    ]
    for h, b in items_l:
        p1 = tf_l.add_paragraph()
        p1.text = f"• {h} {b}"
        p1.font.size = Pt(11)
        p1.font.color.rgb = BODY_TEXT

    # Right Card: The Core Cybersecurity Problem
    add_card(slide2, 6.7, 1.6, 5.8, 5.2, border_color=RED_ACCENT)
    tb_r = slide2.shapes.add_textbox(Inches(6.9), Inches(1.8), Inches(5.4), Inches(4.8))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True

    p = tf_r.paragraphs[0]
    p.text = "THE CYBERSECURITY GAP: UNTRUSTED AIS TELEMETRY"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = RED_ACCENT

    items_r = [
        ("Zero Encryption / Zero Auth:", "Commercial monitors (MarineTraffic, Spire) trust Automatic Identification System (AIS) radio data as honest ground truth. Yet AIS operates on open VHF frequencies with zero cryptography."),
        ("Transponder Blackouts ('Dark Vessels'):", "Hostile vessels disable transponders miles before reaching cable corridors, attempting to evade radar and visual traps."),
        ("SDR GPS Telemetry Spoofing:", "Attackers transmit falsified GPS positions using cheap software-defined radios (HackRF) to mask dangerous maneuvers or simulate impossible displacement."),
        ("Ghost Decoys & Failover DoS:", "Attackers inject phantom ship tracks dragging anchors across cables to trick defensive SOAR systems into triggering unnecessary BGP failover, congesting backup circuits."),
    ]
    for h, b in items_r:
        p1 = tf_r.add_paragraph()
        p1.text = f"• {h} {b}"
        p1.font.size = Pt(11)
        p1.font.color.rgb = BODY_TEXT

    set_notes(slide2, """
To understand why Aegis-Sea is necessary, we must examine the intersection of physical infrastructure and cyber vulnerabilities.

Over 95% of all intercontinental internet traffic and ten trillion dollars in daily financial transfers rely on 712 subsea fiber-optic cables resting on the seabed.

In recent years, gray-zone maritime sabotage has emerged as a major national security threat. The Yi Peng 3 incident in the Baltic Sea demonstrated that a commercial vessel can sever multiple subsea cables by dragging its anchor for over a hundred miles.

The critical cybersecurity challenge is that existing maritime tracking tools treat Automatic Identification System (AIS) data as ground truth. But AIS has no encryption and no authentication. An adversary can turn off their transponder, spoof their GPS coordinates using a $500 Software Defined Radio, or inject phantom ghost ships to trigger a Denial-of-Service on network capacity.

Aegis-Sea was built to solve this exact problem: defending physical subsea infrastructure when the surveillance telemetry itself cannot be trusted.
""")

    # =========================================================================
    # SLIDE 3: Threat Vectors & Adversary Capability Model
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide3)
    add_header(slide3, "Threat Vectors: Physical Sabotage Meets Adversarial Telemetry")

    col_w = 3.7
    gap_3 = 0.28
    y_3 = 1.6
    h_3 = 5.2

    threat_cols = [
        ("PHYSICAL SABOTAGE", RED_ACCENT, [
            ("Anchor Dragging:", "Vessel drops anchor and drags across seabed at 1.0 to 3.5 knots, intentionally hooking subsea cable trench lines."),
            ("Perpendicular Intercept:", "Steering perpendicular to cable orientation maximizes the probability of hooking and snapping armored conduits."),
            ("Protection Zone Loitering:", "Hovering or idling within 3 NM Cable Protection Zone (CPZ) to reconnoiter cable positions."),
            ("Physical Consequence:", "Immediate optical link failure, severe transcontinental packet loss, and weeks of physical repair delay."),
        ]),
        ("TELEMETRY MANIPULATION", YELLOW_ACCENT, [
            ("Transponder Blackouts:", "Disabling AIS broadcast ('going dark') before entering protection zone to avoid automatic alerts."),
            ("SDR Teleportation Jumps:", "Transmitting fake GPS coordinates miles away to disguise the vessel's true physical position."),
            ("Kinematic Discrepancy:", "Vessel claims 1.0 kn speed while position moves 2 NM in 1 second (impossible 240 kn velocity)."),
            ("Surveillance Blindspots:", "Exploiting coastal AIS receiver gaps in international waters."),
        ]),
        ("FAILOVER DoS ATTACKS", PURPLE_ACCENT, [
            ("Weaponized Automation:", "Attackers exploit automated SOAR failover by injecting fake anchor-dragging signals near high-capacity cables."),
            ("Phantom Ghost Ships:", "Synthesized AIS messages created out of thin air with zero prior track or RF Doppler match."),
            ("Route-Flap Congestion:", "Trick automated defense systems into prematurely draining multi-terabit traffic onto secondary paths."),
            ("Aegis-Sea Defense:", "Multi-sensor trust layer validates target authenticity before triggering network route drains."),
        ]),
    ]

    for idx, (title, col, items) in enumerate(threat_cols):
        x = 0.8 + idx * (col_w + gap_3)
        add_card(slide3, x, y_3, col_w, h_3, border_color=col)

        tb = slide3.shapes.add_textbox(Inches(x + 0.15), Inches(y_3 + 0.2), Inches(col_w - 0.3), Inches(h_3 - 0.4))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = col

        for h, b in items:
            p1 = tf.add_paragraph()
            p1.text = f"• {h} {b}"
            p1.font.size = Pt(10.5)
            p1.font.color.rgb = BODY_TEXT

    set_notes(slide3, """
Slide 3 details our adversary threat model, which encompasses both physical and cyber capabilities.

On the physical side, we model anchor dragging at 1.0 to 3.5 knots, perpendicular trench cutting, and loitering inside the 3 Nautical Mile Cable Protection Zone.

On the cyber side, we model transponder blackouts, where a ship goes dark, and SDR GPS teleportation jumps, where forged coordinates create an impossible velocity anomaly.

Most importantly, we model Failover Denial-of-Service attacks. If an automated system blindly triggers traffic reroutes whenever an anchor-drag is reported, an attacker can broadcast fake ghost ships to force traffic off primary fiber routes, intentionally congesting backup networks.

Aegis-Sea is specifically architected to distinguish between genuine sabotage and telemetry spoofing.
""")

    # =========================================================================
    # SLIDE 4: System Architecture & Pipeline
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide4)
    add_header(slide4, "System Architecture: End-to-End Cyber-Physical Defense Pipeline")

    # Add diagram image
    arch_img_path = os.path.join(ASSETS_DIR, 'system_architecture.png')
    if os.path.exists(arch_img_path):
        slide4.shapes.add_picture(arch_img_path, Inches(0.8), Inches(1.5), Inches(11.733), Inches(5.4))

    set_notes(slide4, """
Slide 4 illustrates the end-to-end architecture of Aegis-Sea.

The pipeline operates in five tightly integrated stages:

First, Data Ingestion and Spatial Indexing: We ingest all 712 active submarine cable systems from TeleGeography, decomposed into 11,842 line segments. A two-tier R-tree spatial index evaluates thousands of vessel coordinates against every cable in under 0.02 milliseconds.

Second, the Zero-Trust Telemetry Layer: Before computing threat scores, we run kinematic jump filters, message interval checks, and ghost candidate analysis. If a vessel displaces at an impossible velocity, the trust layer intercepts the anomaly and suppresses false alarms.

Third, the 6-Factor Composite Threat Scoring Core: We evaluate proximity, speed anomaly, loitering time, perpendicular heading, blackout history, and trust confidence to output a composite threat score from 0 to 100.

Fourth, the Automated SOAR Dispatcher: When a threat is confirmed critical, the dispatcher pre-computes BGP evacuation payloads using RFC 7999 community tags, draining traffic off the endangered cable before the anchor hits the trench. If a ghost decoy is detected, failover is held.

Finally, our 3D Geospatial Digital Twin in CesiumJS renders the entire global infrastructure with real-time HUD controls and multi-stage kinematic animations.
""")

    # =========================================================================
    # SLIDE 5: Accomplishments So Far (Phases 0, 1, 2)
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide5)
    add_header(slide5, "What Has Been Accomplished: Milestones 0, 1, & 2 (100% Completed)")

    m_w = 3.7
    gap_5 = 0.28
    y_5 = 1.6
    h_5 = 5.2

    milestones = [
        ("MILESTONE 0: SPATIAL INDEXING", GREEN_ACCENT, [
            ("712 Subsea Cables Ingested:", "Fully decomposed and indexed 11,842 geographic cable line segments."),
            ("Sub-Millisecond Lookup Latency:", "Engineered 2-tier R-tree index achieving <0.02 ms per vessel lookup (<12 microseconds)."),
            ("Dual Watch Corridors:", "Built 9.0 NM Advisory Alert Corridors and 3.0 NM Cable Protection Zones (CPZ)."),
            ("Baseline Verification:", "100% pass on spatial indexing test harness over Baltic, Pacific, and Atlantic cables."),
        ]),
        ("MILESTONE 1: THREAT SCORING CORE", GREEN_ACCENT, [
            ("6-Factor Mathematical Core:", "Continuous sigmoid speed penalty (1.0-3.5 kn), quadratic proximity decay, and CPZ loiter tracking."),
            ("FastAPI Microservice:", "Production-ready backend running on port 8400 with endpoints for /api/threats and /api/evaluate."),
            ("Background AIS Poller:", "Continuous asynchronous polling tap processing live vessel telemetry feeds."),
            ("100% Precision Benchmarks:", "Verified against 10 deterministic ground-truth maritime threat scenarios."),
        ]),
        ("MILESTONE 2: SOAR & 3D VISUALS", CYAN_ACCENT, [
            ("Automated SOAR Dispatcher:", "Created aegis.dispatcher generating pre-computed BGP evacuation payloads (RFC 7999 AS65000:666)."),
            ("Failover Hold Logic:", "Suppressed false alarms on spoofed GPS jumps and withheld route drain on ghost decoys."),
            ("Dynamic 3D Cesium HUD:", "Floating tactical HUD dock with Play/Pause/Replay/Scrubber and live telemetry."),
            ("Dedicated Kinematics:", "Engineered unique 3D animations for all 3 scenarios; 42/42 Python tests passing."),
        ]),
    ]

    for idx, (title, col, items) in enumerate(milestones):
        x = 0.8 + idx * (m_w + gap_5)
        add_card(slide5, x, y_5, m_w, h_5, border_color=col)

        tb = slide5.shapes.add_textbox(Inches(x + 0.15), Inches(y_5 + 0.2), Inches(m_w - 0.3), Inches(h_5 - 0.4))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = col

        p_status = tf.add_paragraph()
        p_status.text = "STATUS: VERIFIED & PUSHED TO MAIN"
        p_status.font.size = Pt(9.5)
        p_status.font.bold = True
        p_status.font.color.rgb = GREEN_ACCENT

        for h, b in items:
            p1 = tf.add_paragraph()
            p1.text = f"• {h} {b}"
            p1.font.size = Pt(10.5)
            p1.font.color.rgb = BODY_TEXT

    set_notes(slide5, """
Slide 5 highlights our major technical achievements across Milestones 0, 1, and 2, all of which are 100% complete and pushed to our GitHub repository.

In Milestone 0, we completed the spatial indexing foundation. Ingesting all 712 subsea cables and indexing 11,842 line segments in an R-tree gave us a lookup latency of under 0.02 milliseconds per vessel.

In Milestone 1, we implemented the 6-factor composite scoring engine, FastAPI microservice, and live stream poller.

In Milestone 2, completed this week, we implemented the automated SOAR dispatcher, generating pre-computed BGP route evacuation payloads, and built the full 3D visual layer in CesiumJS with dedicated kinematic animations for all three threat scenarios.

Our entire backend test suite has 42 out of 42 passing unit tests, and our frontend Vite build compiles cleanly with zero errors.
""")

    # =========================================================================
    # SLIDE 6: Live 3D Operational Interface
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide6)
    add_header(slide6, "Operational Interface: Live 3D Digital Twin & Incident HUD")

    # Add 2 screenshot images side by side
    globe_img = os.path.join(ASSETS_DIR, 'live_globe_cables.png')
    hud_img = os.path.join(ASSETS_DIR, 'tactical_hud_dock.png')

    if os.path.exists(globe_img):
        slide6.shapes.add_picture(globe_img, Inches(0.8), Inches(1.6), Inches(5.7), Inches(4.2))
        cap1 = slide6.shapes.add_textbox(Inches(0.8), Inches(5.9), Inches(5.7), Inches(1.0))
        tf_c1 = cap1.text_frame
        tf_c1.word_wrap = True
        p = tf_c1.paragraphs[0]
        p.text = "FIGURE 1: GLOBAL 3D DIGITAL TWIN (CESIUMJS)"
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = CYAN_ACCENT
        p2 = tf_c1.add_paragraph()
        p2.text = "Visualizes all 712 global subsea fiber cables alongside 12,000 live vessel telemetry feeds with sub-millisecond proximity indexing."
        p2.font.size = Pt(10)
        p2.font.color.rgb = MUTED_TEXT

    if os.path.exists(hud_img):
        slide6.shapes.add_picture(hud_img, Inches(6.8), Inches(1.6), Inches(5.7), Inches(4.2))
        cap2 = slide6.shapes.add_textbox(Inches(6.8), Inches(5.9), Inches(5.7), Inches(1.0))
        tf_c2 = cap2.text_frame
        tf_c2.word_wrap = True
        p = tf_c2.paragraphs[0]
        p.text = "FIGURE 2: TACTICAL SUBSEA DEFENSE HUD DOCK"
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = CYAN_ACCENT
        p2 = tf_c2.add_paragraph()
        p2.text = "Real-time engine status pill, threat severity counters, attack simulation triggers, interactive playback scrubber, and elevated threat drawer."
        p2.font.size = Pt(10)
        p2.font.color.rgb = MUTED_TEXT

    set_notes(slide6, """
Slide 6 displays real in-browser screenshots of our working operational system.

On the left, Figure 1 shows our global 3D CesiumJS digital twin. Every blue line represents an indexed undersea cable, and the cyan dots represent real-time commercial vessels across global maritime corridors.

On the right, Figure 2 shows our Aegis Tactical Subsea Defense HUD dock. At the top, operators see the live engine status, real-time threat counts for Critical, High, and Advisory levels, and on-demand attack simulation buttons.

Directly below is the interactive playback controller bar, which includes Play/Pause, Replay, a 24-second timeline scrubber, and dynamic stage badges indicating exactly what phase an incident is in.
""")

    # =========================================================================
    # SLIDE 7: Live Technical Demonstration Script
    # =========================================================================
    slide7 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide7)
    add_header(slide7, "Live Technical Demonstration: Step-by-Step Operator Script")

    demo_steps = [
        ("DEMO STEP 1: GLOBAL INFRASTRUCTURE", CYAN_ACCENT, [
            "• Navigate to Baltic Sea corridor (Gulf of Finland).",
            "• Identify C-Lion1 subsea fiber cable linking Finland and Germany.",
            "• Point out 3.0 NM Cable Protection Zone (CPZ) danger halo.",
        ]),
        ("DEMO STEP 2: YI PENG 3 SABOTAGE", RED_ACCENT, [
            "• Click [▶ YI PENG 3 SABOTAGE] in top HUD dock.",
            "• Stage 1 (0-8s): 10.5 kn cruising approach from north-east.",
            "• Stage 2 (8-16s): Deceleration to 1.2 kn inside CPZ; anchor dropped.",
            "• Stage 3 (16-24s): Anchor trench cuts C-Lion1; score hits 85.0 (CRITICAL); automated BGP pre-emptive evacuation armed.",
        ]),
        ("DEMO STEP 3: GPS SPOOF JUMP", YELLOW_ACCENT, [
            "• Click [▶ GPS SPOOF JUMP] in top HUD dock.",
            "• Stage 1 (0-6s): Commercial cargo vessel cruising at 12 kn.",
            "• Stage 2 (6-10s): Instantaneous 2.0 NM teleportation leap (240 kn).",
            "• Stage 3 (10-18s): Aegis Trust Layer intervenes, trips kinematic jump filter, suppresses false alarm, and holds BGP failover.",
        ]),
        ("DEMO STEP 4: GHOST DECOY", PURPLE_ACCENT, [
            "• Click [▶ GHOST DECOY] in top HUD dock.",
            "• Stage 1 (0-5s): Quiet corridor surveillance baseline.",
            "• Stage 2 (5-9s): Synthesized AIS phantom contact materializes inside 3 NM CPZ at 1.5 kn with expanding radar waves.",
            "• Stage 3 (9-18s): Failover DoS thwarted; route drain withheld.",
        ]),
    ]

    card_w7 = 2.75
    gap_7 = 0.24
    y_7 = 1.6
    h_7 = 5.2

    for idx, (title, col, items) in enumerate(demo_steps):
        x = 0.8 + idx * (card_w7 + gap_7)
        add_card(slide7, x, y_7, card_w7, h_7, border_color=col)

        tb = slide7.shapes.add_textbox(Inches(x + 0.12), Inches(y_7 + 0.15), Inches(card_w7 - 0.24), Inches(h_7 - 0.3))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = col

        for step_text in items:
            p1 = tf.add_paragraph()
            p1.text = step_text
            p1.font.size = Pt(10)
            p1.font.color.rgb = BODY_TEXT

    set_notes(slide7, """
[PRESENTER ACTION: Transition to browser window showing God's Eye View with Aegis HUD]

"Now, I would like to transition to our live browser demonstration to show the defense engine in action.

Step 1: Here on our 3D globe, you can see the Baltic Sea corridor and the C-Lion1 submarine fiber cable linking Finland and Germany.

Step 2: I will click [▶ YI PENG 3 SABOTAGE]. Notice the ship approaching at 10.5 knots. As it enters the 3 Nautical Mile Cable Protection Zone, watch the sharp deceleration down to 1.2 knots. The anchor drops to the seabed, and a glowing red trench line is dragged across C-Lion1. The threat score immediately climbs to 85.0 CRITICAL, and Aegis primes an automated BGP route drain before physical severed loss occurs.

Step 3: Next, I will click [▶ GPS SPOOF JUMP]. Notice how the previous scenario is cleared. Here we see a commercial cargo vessel cruising east at 12 knots. Watch what happens at 6 seconds: the ship instantaneously teleports 2 nautical miles across the cable in a single second. An implied speed of 240 knots. A naive system would sound an alarm. But our Trust Layer detects the impossible velocity, trips the kinematic jump filter, suppresses the false alarm, and holds BGP failover.

Step 4: Finally, I click [▶ GHOST DECOY]. The corridor is initially quiet. Then, an adversary injects a synthesized AIS broadcast directly on top of the cable. A translucent purple ghost ship appears with expanding radar pulses. Instead of blindly draining routes, Aegis detects that this vessel has no historical track and no radar confirmation, thwarting the Failover DoS attack.

Let us now return to the slides to examine the paper skeleton and remaining tasks."
""")

    # =========================================================================
    # SLIDE 8: Skeleton & Outline of Project Paper
    # =========================================================================
    slide8 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide8)
    add_header(slide8, "Capstone Paper Skeleton: Academic Structure & Draft Progress")

    # Add generated paper skeleton image
    paper_img_path = os.path.join(ASSETS_DIR, 'paper_skeleton.png')
    if os.path.exists(paper_img_path):
        slide8.shapes.add_picture(paper_img_path, Inches(0.8), Inches(1.5), Inches(11.733), Inches(5.4))

    set_notes(slide8, """
Slide 8 presents the complete academic skeleton and outline of our Capstone Project Paper.

The paper is structured into nine formal sections following IEEE and ACM conference standards, with a target length of 28 to 30 pages:

Section I covers Introduction and Motivation, detailing the economic criticality of subsea cables and real-world gray-zone incidents.

Section II provides Background and Related Work, analyzing the UNCLOS legal void, AIS protocol weaknesses, and why commercial tools fail against adversarial telemetry.

Section III defines our Adversary Threat Model, formalizing both physical anchor-dragging and cyber telemetry attacks.

Section IV covers our System Architecture and Telemetry Trust Layer, detailing our 2-tier R-tree spatial index and velocity jump filters.

Section V details the 6-Factor Kinematic Composite Threat Scorer, presenting the mathematical formulations for sigmoid speed anomaly, distance decay, and loitering.

Section VI details the Automated SOAR Dispatcher and RFC 7999 BGP route evacuation mechanism.

Section VII presents our Experimental Evaluation across 10 benchmark attack datasets.

Sections VIII and IX conclude with Discussion, optical OTDR correlation, game-theoretic evasion models, and final conclusions.

Sections I through V are fully drafted, and Sections VI through IX are actively being completed.
""")

    # =========================================================================
    # SLIDE 9: What Remains to Be Done (Phase 3 & Beyond)
    # =========================================================================
    slide9 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide9)
    add_header(slide9, "What Remains to Be Done: Phase 3 Research Tasks & Evaluation")

    r_w = 2.75
    gap_9 = 0.24
    y_9 = 1.6
    h_9 = 5.2

    remaining_tasks = [
        ("TASK 1: VIRTUAL SDN TESTBED", CYAN_ACCENT, [
            ("Containerlab & FRRouting:", "Deploy virtual software routers (FRR / BIRD) simulating tier-1 BGP peering networks."),
            ("Empirical Failover Measurement:", "Measure exact packet loss, latency spikes, and convergence time comparing pre-emptive evacuation vs. unannounced physical cable severing."),
            ("BGP Community Validation:", "Verify RFC 7999 AS65000:666 graceful shutdown propagation across multi-AS topologies."),
        ]),
        ("TASK 2: OPTICAL POWER DROP (OTDR)", YELLOW_ACCENT, [
            ("Optical Power Telemetry:", "Correlate optical time-domain reflectometry (OTDR) backscatter drop with maritime coordinates."),
            ("Physical Localization:", "Pinpoint exact seabed cut coordinates within ±10 meters based on laser pulse reflection timing."),
            ("Hybrid Fusion:", "Combine optical physical alerts with external maritime AIS telemetry to eliminate all ambiguity."),
        ]),
        ("TASK 3: GAME-THEORETIC DEFENSE", PURPLE_ACCENT, [
            ("Stackelberg Game Formulation:", "Model saboteur optimizing vessel speed and loiter time against Aegis-Sea detection probability."),
            ("Adversarial Evasion Bounds:", "Determine optimal mathematical thresholds for CPZ dwell time and distance decay under noisy telemetry."),
            ("Cost-Benefit Analysis:", "Quantify trade-off between pre-emptive route drain disruption and physical cable damage risk."),
        ]),
        ("TASK 4: FINAL PAPER & DEFENSE", GREEN_ACCENT, [
            ("Statistical Validation:", "Evaluate ROC curves, precision, and recall across 10 deterministic benchmark datasets."),
            ("Paper Draft Finalization:", "Complete Sections VI, VII, and VIII of capstone manuscript."),
            ("Final Defense Presentation:", "Prepare final deliverable deck and submit to committee (December 2026)."),
        ]),
    ]

    for idx, (title, col, items) in enumerate(remaining_tasks):
        x = 0.8 + idx * (r_w + gap_9)
        add_card(slide9, x, y_9, r_w, h_9, border_color=col)

        tb = slide9.shapes.add_textbox(Inches(x + 0.12), Inches(y_9 + 0.15), Inches(r_w - 0.24), Inches(h_9 - 0.3))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = col

        for h, b in items:
            p1 = tf.add_paragraph()
            p1.text = f"• {h} {b}"
            p1.font.size = Pt(10)
            p1.font.color.rgb = BODY_TEXT

    set_notes(slide9, """
Slide 9 outlines what remains to be completed in Phase 3 and leading up to our final defense.

Our primary technical task is Task 1: deploying a virtual Software Defined Networking testbed using Containerlab and FRRouting. This will allow us to empirically measure packet loss, convergence time, and throughput during pre-emptive BGP evacuation versus sudden unannounced link failure.

Task 2 is integrating optical power telemetry. By correlating Optical Time-Domain Reflectometry (OTDR) laser backscatter drops with maritime coordinates, we can achieve sub-meter physical cut localization.

Task 3 is formalizing a Stackelberg game model between a saboteur trying to evade detection and our Aegis scoring engine, establishing mathematical bounds on detection thresholds.

Finally, Task 4 is completing the remaining sections of our capstone paper and preparing for the final defense in December.
""")

    # =========================================================================
    # SLIDE 10: Project Timeline & Milestone Roadmap
    # =========================================================================
    slide10 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide10)
    add_header(slide10, "Project Timeline & Execution Schedule: Fall 2026 Semester")

    timeline_img_path = os.path.join(ASSETS_DIR, 'project_timeline.png')
    if os.path.exists(timeline_img_path):
        slide10.shapes.add_picture(timeline_img_path, Inches(0.8), Inches(1.5), Inches(11.733), Inches(5.4))

    set_notes(slide10, """
Slide 10 presents our master execution schedule and milestone roadmap across the Fall 2026 semester.

As shown on the Gantt chart:

Phase 0, Geospatial Indexing and Foundation, was completed on October 12.

Phase 1, the 6-Factor Threat Core and Microservice, was completed on October 26.

Phase 2, the SOAR Dispatcher and 3D Kinematic Visuals, was completed on October 31.

Today, October 31, marks our Midterm Progress Report and Live Technical Demonstration.

Looking ahead, Phase 3, the Containerlab BGP testbed, will run from November 1 to November 20.

Phase 4, Optical OTDR and Game-Theoretic modeling, will run from November 21 to December 5.

And Phase 5, the final paper submission and capstone defense presentation, is scheduled for December 6 through December 15.

We are currently tracking exactly on schedule with all major deliverables met.
""")

    # =========================================================================
    # SLIDE 11: Summary & Q&A
    # =========================================================================
    slide11 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide11)
    add_header(slide11, "Summary & Faculty Q&A")

    # Left card: Key Contributions Summary
    add_card(slide11, 0.8, 1.6, 5.7, 5.2, border_color=CYAN_ACCENT)
    tb_sl = slide11.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.3), Inches(4.8))
    tf_sl = tb_sl.text_frame
    tf_sl.word_wrap = True

    p = tf_sl.paragraphs[0]
    p.text = "CORE CONTRIBUTIONS & CURRENT STATUS"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = CYAN_ACCENT

    summary_items = [
        ("Resilient Zero-Trust Defense:", "Aegis-Sea is the first cyber-physical defense engine for 712 subsea cables designed to operate over untrusted, spoofed telemetry."),
        ("Sub-Millisecond Scalability:", "2-tier R-tree spatial index evaluates thousands of vessels against 11,842 cable segments in under 0.02 milliseconds."),
        ("Pre-Emptive Traffic Evacuation:", "Automated SOAR dispatcher triggers RFC 7999 BGP graceful route drain before physical severed loss occurs, saving multi-terabit traffic from sudden collapse."),
        ("Full 3D Geospatial Digital Twin:", "Real-time CesiumJS operational interface with dedicated multi-stage kinematic animations for anchor-dragging, GPS spoof jumps, and ghost decoys."),
        ("100% Passing Test Harness:", "42/42 Python unit tests and 100% frontend JavaScript tests passing."),
    ]
    for h, b in summary_items:
        p1 = tf_sl.add_paragraph()
        p1.text = f"• {h} {b}"
        p1.font.size = Pt(11)
        p1.font.color.rgb = BODY_TEXT

    # Right card: Academic acknowledgments & Q&A
    add_card(slide11, 6.8, 1.6, 5.7, 5.2, border_color=GREEN_ACCENT)
    tb_sr = slide11.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
    tf_sr = tb_sr.text_frame
    tf_sr.word_wrap = True

    p = tf_sr.paragraphs[0]
    p.text = "ACKNOWLEDGMENTS & OPEN DISCUSSION"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = GREEN_ACCENT

    p1 = tf_sr.add_paragraph()
    p1.text = "Special thanks to:"
    p1.font.size = Pt(12)
    p1.font.color.rgb = WHITE_TEXT

    p2 = tf_sr.add_paragraph()
    p2.text = "• Dr. Juntao Chen (Project Advisor) for invaluable guidance on cyber-physical modeling and resilient systems.\n• Dr. Thaier Hayajneh (Course Instructor & Director) for leadership and capstone standards.\n• Department of Computer and Information Sciences, Fordham University."
    p2.font.size = Pt(11)
    p2.font.color.rgb = BODY_TEXT

    p_qa = tf_sr.add_paragraph()
    p_qa.text = "\nThank you for your time and feedback."
    p_qa.font.size = Pt(14)
    p_qa.font.bold = True
    p_qa.font.color.rgb = CYAN_ACCENT

    p_q = tf_sr.add_paragraph()
    p_q.text = "I am now open to questions from the faculty committee."
    p_q.font.size = Pt(13)
    p_q.font.bold = True
    p_q.font.color.rgb = WHITE_TEXT

    set_notes(slide11, """
In conclusion, Aegis-Sea demonstrates that we can proactively protect the critical physical backbone of the global internet even when the surveillance telemetry we rely on is actively weaponized by adversaries.

We have successfully completed Milestones 0, 1, and 2, delivering a sub-millisecond spatial index, a 6-factor composite scoring engine, an automated BGP incident response dispatcher, and a full 3D interactive CesiumJS operational interface with 42 out of 42 passing unit tests.

I want to express my sincere gratitude to my advisor, Dr. Juntao Chen, and my instructor, Dr. Thaier Hayajneh, for their continuous support and guidance throughout this capstone.

Thank you very much. I am now open to your questions and feedback.
""")

    prs.save(PPTX_PATH)
    print(f"Successfully generated PowerPoint presentation: {PPTX_PATH}")
    return PPTX_PATH


if __name__ == '__main__':
    create_deck()
