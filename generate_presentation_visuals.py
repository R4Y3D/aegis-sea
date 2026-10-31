"""
Generates high-resolution graphical visuals for the Aegis-Sea Capstone Progress Report:
1. paper_skeleton.png: Clean academic layout of the 9-section capstone paper outline
2. system_architecture.png: End-to-end cyber-physical data flow and defense pipeline
3. project_timeline.png: Gantt-style milestone progress from Sept 2026 to Dec 2026
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.getcwd(), 'presentation_assets')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_paper_skeleton():
    """Renders a high-resolution IEEE/ACM paper outline skeleton image."""
    width, height = 1600, 1100
    image = Image.new('RGB', (width, height), color='#0a0f1d')
    draw = ImageDraw.Draw(image)

    # Outer border
    draw.rectangle([20, 20, width - 20, height - 20], outline='#1e293b', width=3)
    draw.rectangle([24, 24, width - 24, height - 24], outline='#38bdf8', width=1)

    # Header banner
    draw.rectangle([30, 30, width - 30, 120], fill='#0f172a', outline='#38bdf8', width=2)
    
    # We will use default bitmap or standard fonts
    try:
        title_font = ImageFont.truetype('arial.ttf', 30)
        subtitle_font = ImageFont.truetype('arial.ttf', 16)
        section_font = ImageFont.truetype('arialbd.ttf', 17)
        body_font = ImageFont.truetype('arial.ttf', 14)
        tag_font = ImageFont.truetype('arialbd.ttf', 11)
    except Exception:
        title_font = subtitle_font = section_font = body_font = tag_font = ImageFont.load_default()

    draw.text((50, 45), "CAPSTONE PROJECT PAPER SKELETON & OUTLINE", fill='#38bdf8', font=title_font)
    draw.text((50, 85), "Aegis-Sea: Resilient Cyber-Physical Threat Intelligence & Automated Incident Response for Subsea Undersea Infrastructure", fill='#94a3b8', font=subtitle_font)

    sections = [
        ("SECTION I: INTRODUCTION & MOTIVATION", [
            "1.1 Criticality of 712 Global Submarine Fiber Cables (95%+ Intercontinental Traffic, $10T+ Daily)",
            "1.2 Gray-Zone Anchor-Dragging Sabotage (Balticconnector, C-Lion1, Red Sea Incidents)",
            "1.3 The Core Vulnerability: Insecurity of Unauthenticated, Unencrypted Maritime AIS Telemetry",
            "1.4 Key Contributions: Zero-Trust Spatial Index, 6-Factor Kinematic Core, Pre-Emptive BGP Evacuation"
        ], "#38bdf8", "3.0 Pages · Complete"),

        ("SECTION II: BACKGROUND & RELATED WORK", [
            "2.1 Undersea Cable Protection Zones (UNCLOS Jurisdictional Gaps, 3 NM CPZ Standards)",
            "2.2 Automated Identification System (AIS) Vulnerabilities (VHF Spoofing, Dark Vessels, Phantoms)",
            "2.3 Prior Monitoring Approaches (MarineTraffic, Windward) & Their Failure Against Adversarial Manipulation",
            "2.4 Cyber-Physical Incident Response & BGP Traffic Engineering (RFC 7999 Graceful Shutdown)"
        ], "#818cf8", "3.5 Pages · Complete"),

        ("SECTION III: THREAT MODEL & ADVERSARY CAPABILITIES", [
            "3.1 Physical Threat Vectors: Anchor Dragging (1.0-3.5 kn), Perpendicular Furrowing, Loitering",
            "3.2 Cyber Vectors: AIS Blackouts ('Going Dark'), SDR GPS Jump Spoofing, Synthetic Ghost Ships",
            "3.3 Failover Denial-of-Service: Weaponizing Protective Failover Logic to Induce Route-Flap Congestion",
            "3.4 Trust Assumptions: Defense Engine Operates Over Untrusted Commercial Surveillance Feeds"
        ], "#f87171", "3.0 Pages · Complete"),

        ("SECTION IV: AEGIS-SEA ARCHITECTURE & TELEMETRY TRUST LAYER", [
            "4.1 2-Tier R-Tree Spatial Indexing over 11,842 Cable Geometries (<0.02 ms Lookup Latency)",
            "4.2 Dual Watch Corridors: 9.0 NM Advisory Alert Corridor & 3.0 NM Cable Protection Zone (CPZ)",
            "4.3 Telemetry Trust Engine: Kinematic Velocity Jump Filtering (Max Physical Threshold 35 kn)",
            "4.4 Phantom Contact Discrimination: Prior Historical Track & RF Doppler Sanity Verification"
        ], "#fb923c", "4.0 Pages · Complete"),

        ("SECTION V: 6-FACTOR KINEMATIC COMPOSITE THREAT SCORER", [
            "5.1 Mathematical Formulation: Quadratic Distance Decay, Sigmoid Speed Anomaly, CPZ Loitering",
            "5.2 Angular Perpendicularity & Trench Crossing Projection",
            "5.3 Historical Blackout Penalty & Kinematic Trust Weighting",
            "5.4 Threat Classification Matrix: Normal (<40), Advisory (40-69), High (70-79), Critical (80-100)"
        ], "#facc15", "4.0 Pages · Complete"),

        ("SECTION VI: AUTOMATED SOAR DISPATCHER & BGP PRE-EMPTIVE DRAIN", [
            "6.1 Automated Incident Orchestration (Webhooks, Syslog, Cooldown Deduplication)",
            "6.2 Pre-Computed BGP Community Payloads (RFC 7999 AS65000:666 Pre-Emptive Evacuation)",
            "6.3 Failover Hold Logic: Multi-Sensor Cross-Check Thwarting Decoy-Driven Route-Flap DoS",
            "6.4 End-to-End Latency: Sub-10ms Dispatch from Telemetry Breach to Route Announcement"
        ], "#4ade80", "3.5 Pages · In Progress"),

        ("SECTION VII: EXPERIMENTAL EVALUATION & BENCHMARK SUITE", [
            "7.1 10 Deterministic Benchmark Attack Scenarios (Yi Peng 3, Transponder Jumps, Ghost Decoys)",
            "7.2 Computational Benchmarks: Spatial Index Throughput, Polling Scalability, Scoring Overhead",
            "7.3 Detection Precision, Recall, and ROC Curves Across False Alarm Datasets",
            "7.4 Hardware-in-the-Loop SDN Testbed: Packet Loss & Convergence vs. Post-Cut Failures"
        ], "#2dd4bf", "4.5 Pages · In Progress"),

        ("SECTION VIII: DISCUSSION, LIMITATIONS & FUTURE WORK", [
            "8.1 Optical Telemetry Correlation: OTDR Power Drop Integration with Spatial Coordinates",
            "8.2 Game-Theoretic Stackelberg Evasion Models Between Saboteurs and Aegis Monitors",
            "8.3 Legal & Policy Implications: Proactive Network Defense Under UNCLOS Maritime Law",
            "8.4 Deployment Roadmap: Autonomous Shore-Based & Maritime Edge Systems"
        ], "#a78bfa", "2.0 Pages · Outlined"),

        ("SECTION IX: CONCLUSION & ACADEMIC DELIVERABLES", [
            "9.1 Summary of Capstone Achievements: Resilient Real-Time Cyber-Physical Cable Defense",
            "9.2 Artifact Availability: Open-Source God's Eye View Digital Twin & Aegis-Engine Testbed"
        ], "#38bdf8", "1.5 Pages · Outlined"),
    ]

    # Two-column layout
    col1_x = 40
    col2_x = 810
    col_width = 750
    y_starts = [140, 140]

    for idx, (sec_title, items, border_color, status_text) in enumerate(sections):
        col_idx = 0 if idx < 5 else 1
        x = col1_x if col_idx == 0 else col2_x
        y = y_starts[col_idx]
        card_h = 175 if len(items) == 4 else 125

        # Draw card container
        draw.rectangle([x, y, x + col_width, y + card_h], fill='#131d31', outline=border_color, width=2)

        # Card header pill
        draw.rectangle([x + 10, y + 8, x + col_width - 10, y + 36], fill='#1e293b')
        draw.text((x + 18, y + 13), sec_title, fill=border_color, font=section_font)

        # Status badge
        badge_w = 160
        badge_x = x + col_width - badge_w - 15
        draw.rectangle([badge_x, y + 10, badge_x + badge_w, y + 32], fill='#0f172a', outline=border_color, width=1)
        draw.text((badge_x + 10, y + 14), status_text, fill='#ffffff', font=tag_font)

        # Subsections
        item_y = y + 44
        for item in items:
            draw.text((x + 18, item_y), f"• {item}", fill='#cbd5e1', font=body_font)
            item_y += 26

        y_starts[col_idx] += card_h + 16

    out_path = os.path.join(OUTPUT_DIR, 'paper_skeleton.png')
    image.save(out_path, dpi=(150, 150))
    print(f"Generated paper skeleton visual: {out_path}")
    return out_path


def generate_project_timeline():
    """Renders a Gantt milestone roadmap diagram."""
    fig, ax = plt.subplots(figsize=(14, 7), facecolor='#0b111e')
    ax.set_facecolor('#0b111e')

    phases = [
        ("Phase 0: Geospatial Indexing & Foundation\n(712 Cables, R-Tree, Benchmarking)", 0.0, 1.8, "#22c55e", "COMPLETED\n(Oct 12)"),
        ("Phase 1: 6-Factor Threat Core & Microservice\n(FastAPI, AIS Poller, Telemetry Trust)", 1.8, 3.8, "#22c55e", "COMPLETED\n(Oct 26)"),
        ("Phase 2: SOAR Dispatcher & 3D Kinematics\n(BGP RFC 7999, Cesium Live Simulation)", 3.8, 5.8, "#22c55e", "COMPLETED\n(Oct 31)"),
        ("Milestone: Midterm Progress Report & Demo\n(Presentation Deck, Script, Paper Outline)", 5.6, 6.0, "#38bdf8", "TODAY\n(Oct 31)"),
        ("Phase 3: Containerlab SDN BGP Testbed\n(FRRouting, Latency & Convergence Benchmarks)", 6.0, 8.5, "#eab308", "NEXT UP\n(Nov 01-20)"),
        ("Phase 4: Optical OTDR & Game-Theoretic Evasion\n(Power-Drop Correlation, Stackelberg Model)", 8.5, 10.5, "#f97316", "PLANNED\n(Nov 21-Dec 05)"),
        ("Phase 5: Capstone Paper & Final Defense\n(IEEE/ACM Submission, Committee Presentation)", 10.5, 12.0, "#a855f7", "FINAL\n(Dec 06-15)"),
    ]

    y_ticks = []
    y_labels = []

    for i, (title, start, end, color, status) in enumerate(phases):
        y = len(phases) - 1 - i
        y_ticks.append(y)
        y_labels.append(title.split('\n')[0])

        # Background bar
        ax.barh(y, end - start, left=start, height=0.55, color=color, alpha=0.85, edgecolor='#ffffff', linewidth=1.2)

        # Status text inside or beside bar
        mid_x = start + (end - start) / 2.0
        ax.text(mid_x, y, status.replace('\n', ' · '), ha='center', va='center', color='#ffffff', fontweight='bold', fontsize=9)

    # Current progress vertical marker (Oct 31 / Today)
    ax.axvline(x=5.9, color='#ef4444', linestyle='--', linewidth=2.5, label='Current Milestone (Oct 31, 2026)')
    ax.text(5.95, len(phases) - 0.2, "MIDTERM PROGRESS REPORT (OCT 31)", color='#ef4444', fontweight='bold', fontsize=10)

    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels, color='#e2e8f0', fontsize=10, fontweight='bold')
    ax.set_xticks([0, 2, 4, 6, 8, 10, 12])
    ax.set_xticklabels(["Sept 15", "Oct 01", "Oct 15", "Nov 01", "Nov 15", "Dec 01", "Dec 15"], color='#94a3b8', fontsize=10)
    ax.set_xlabel("Capstone Project Timeline (Fall 2026 Semester)", color='#38bdf8', fontsize=12, fontweight='bold', labelpad=12)
    ax.set_title("Aegis-Sea Capstone Milestone Execution Roadmap & Schedule", color='#38bdf8', fontsize=14, fontweight='bold', pad=18)

    # Style grid
    ax.grid(axis='x', color='#1e293b', linestyle=':', alpha=0.8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#334155')
    ax.spines['bottom'].set_color('#334155')
    ax.tick_params(colors='#94a3b8')

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, 'project_timeline.png')
    plt.savefig(out_path, dpi=160, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Generated timeline visual: {out_path}")
    return out_path


def generate_architecture_diagram():
    """Renders a clean pipeline architecture diagram."""
    fig, ax = plt.subplots(figsize=(14, 7), facecolor='#0b111e')
    ax.set_facecolor('#0b111e')

    # Draw 4 main pipeline stage blocks
    boxes = [
        ("DATA INGESTION & SPATIAL INDEX", [
            "• 712 Global Submarine Cables",
            "• 11,842 Line Segments",
            "• 2-Tier R-Tree Spatial Index",
            "• <0.02 ms Lookup Latency",
            "• Live Maritime AIS Feeds"
        ], 0.05, 0.20, "#38bdf8"),

        ("ZERO-TRUST TELEMETRY LAYER", [
            "• Kinematic Velocity Filter (>35 kn)",
            "• SDR GPS Jump Anomaly Detector",
            "• Blackout Course Projection",
            "• Phantom Ghost Ship Scorer",
            "• Cross-Sensor Verification"
        ], 0.28, 0.20, "#fb923c"),

        ("6-FACTOR COMPOSITE SCORER", [
            "• Quadratic Distance Decay (CPZ)",
            "• Sigmoid Anchor Drag Speed",
            "• Angular Perpendicular Heading",
            "• Loitering Duration in CPZ",
            "• Threat Score S ∈ [0, 100]"
        ], 0.51, 0.20, "#eab308"),

        ("AUTOMATED SOAR & BGP DRAIN", [
            "• Webhook & Syslog Alerts",
            "• RFC 7999 BGP Route Shutdown",
            "• Community AS65000:666",
            "• Failover Hold for Decoys",
            "• Pre-Emptive Traffic Evac"
        ], 0.74, 0.20, "#ef4444"),
    ]

    for title, items, left, width, color in boxes:
        # Outer box
        rect = patches.FancyBboxPatch(
            (left, 0.25), width, 0.60,
            boxstyle="round,pad=0.02,rounding_size=0.03",
            facecolor='#131d31', edgecolor=color, linewidth=2.0
        )
        ax.add_patch(rect)

        # Title banner
        ax.text(left + width/2.0, 0.80, title, ha='center', va='center', color=color, fontweight='bold', fontsize=11)

        # Body items
        y_pos = 0.70
        for item in items:
            ax.text(left + 0.015, y_pos, item, ha='left', va='center', color='#cbd5e1', fontsize=9.5)
            y_pos -= 0.085

    # Connect boxes with arrows
    for x_conn in [0.25, 0.48, 0.71]:
        ax.annotate(
            '', xy=(x_conn + 0.03, 0.55), xytext=(x_conn, 0.55),
            arrowprops=dict(arrowstyle="->", color='#38bdf8', lw=2.5, mutation_scale=18)
        )

    # 3D Digital Twin visualization block spanning underneath
    vis_rect = patches.FancyBboxPatch(
        (0.05, 0.04), 0.89, 0.14,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        facecolor='#0f172a', edgecolor='#22c55e', linewidth=1.5
    )
    ax.add_patch(vis_rect)
    ax.text(0.50, 0.11, "3D GEOSPATIAL DIGITAL TWIN & REAL-TIME INCIDENT HUD (GOD'S EYE VIEW / CESIUMJS)", ha='center', va='center', color='#22c55e', fontweight='bold', fontsize=11)
    ax.text(0.50, 0.065, "Interactive Kinematic Adversary Replay · 3 NM Danger Halos · Play/Pause/Scrubber · Director Mode Sequences", ha='center', va='center', color='#94a3b8', fontsize=9.5)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 0.95)
    ax.axis('off')
    ax.set_title("Aegis-Sea End-to-End Cyber-Physical Threat Intelligence & Incident Response Architecture", color='#38bdf8', fontsize=13, fontweight='bold', pad=15)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, 'system_architecture.png')
    plt.savefig(out_path, dpi=160, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Generated architecture visual: {out_path}")
    return out_path


if __name__ == '__main__':
    generate_paper_skeleton()
    generate_project_timeline()
    generate_architecture_diagram()
    print("All presentation visuals successfully generated in presentation_assets/")
