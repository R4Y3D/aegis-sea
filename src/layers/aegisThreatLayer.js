/**
 * Aegis-Sea 3D Visual Threat & Adversary Simulation Layer for CesiumJS.
 * Features:
 * 1. Dedicated kinematic simulation timelines for all three scenarios:
 *    - Anchor Dragging Sabotage (Yi Peng 3)
 *    - SDR Spoofed Fix (Kinematic Jump)
 *    - Phantom Ghost Decoy (Failover DoS)
 * 2. 3.0 NM Cable Protection Zone (CPZ) danger halos with smooth alpha pulsing.
 * 3. High-contrast simulated adversary ship billboards (red hull, yellow jump, purple ghost).
 * 4. Distinct dynamic bad-action visualizations:
 *    - Glowing seabed furrow trench line & anchor snag for sabotage
 *    - Dashed yellow lightning vector & origin fix marker for GPS jump
 *    - Translucent materialization & expanding radar pulses for ghost decoy
 * 5. Interactive simulation controls: Play, Pause, Replay, and Scrubber Timeline.
 * 6. Dynamic Cesium CallbackProperties that never crash or get wiped by background polling.
 */

import * as Cesium from 'cesium';
import { aegisThreatService } from '../services/aegisThreatService.js';

const CPZ_RADIUS_METERS = 5556.0; // 3.0 Nautical Miles (Cable Protection Zone)

const SCENARIO_CAMERAS = {
  anchor_drag: {
    lon: 25.035,
    lat: 60.015,
    alt: 8500,
    heading: 15,
    pitch: -35,
  },
  gps_jump: {
    lon: 24.965,
    lat: 60.005,
    alt: 9500,
    heading: 35,
    pitch: -38,
  },
  ghost_decoy: {
    lon: 25.035,
    lat: 60.015,
    alt: 8200,
    heading: 18,
    pitch: -33,
  },
};

/** Builds SVG data URI for legitimate commercial cargo vessel */
function buildCargoShipIcon() {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
      <circle cx="32" cy="32" r="28" fill="rgba(56, 189, 248, 0.25)" stroke="#38bdf8" stroke-width="2"/>
      <polygon points="32,4 52,50 32,40 12,50" fill="#38bdf8" stroke="#ffffff" stroke-width="2"/>
      <circle cx="32" cy="32" r="10" fill="#0f172a" stroke="#ffffff" stroke-width="1.5"/>
      <polygon points="32,24 38,36 26,36" fill="#7dd3fc"/>
    </svg>
  `;
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg.trim());
}

/** Builds high-contrast SVG data URI for adversary/simulated ships */
function buildHostileShipIcon(type) {
  let svg = '';

  if (type === 'anchor_drag') {
    // Red combat hull with anchor badge
    svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r="28" fill="rgba(239, 68, 68, 0.3)" stroke="#ef4444" stroke-width="2.5" stroke-dasharray="6 3"/>
        <polygon points="32,4 52,50 32,40 12,50" fill="#ef4444" stroke="#ffffff" stroke-width="2.5"/>
        <circle cx="32" cy="32" r="11" fill="#0f172a" stroke="#ffffff" stroke-width="1.5"/>
        <circle cx="32" cy="27" r="2" fill="none" stroke="#fca5a5" stroke-width="1.2"/>
        <line x1="32" y1="29" x2="32" y2="37" stroke="#fca5a5" stroke-width="1.5"/>
        <line x1="28" y1="31" x2="36" y2="31" stroke="#fca5a5" stroke-width="1.5"/>
        <path d="M27 34 C27 38.5 37 38.5 37 34" fill="none" stroke="#fca5a5" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    `;
  } else if (type === 'gps_jump') {
    // Yellow/amber spoofed ship with lightning badge
    svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r="28" fill="rgba(234, 179, 8, 0.3)" stroke="#eab308" stroke-width="2.5" stroke-dasharray="5 3"/>
        <polygon points="32,4 52,50 32,40 12,50" fill="#eab308" stroke="#ffffff" stroke-width="2.5"/>
        <circle cx="32" cy="32" r="11" fill="#0f172a" stroke="#ffffff" stroke-width="1.5"/>
        <polygon points="34,23 27,32 32,32 30,41 37,31 32,31" fill="#fef08a"/>
      </svg>
    `;
  } else {
    // Translucent purple ghost decoy with phantom outline badge
    svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r="28" fill="rgba(168, 85, 247, 0.25)" stroke="#c084fc" stroke-width="2" stroke-dasharray="4 3"/>
        <polygon points="32,4 52,50 32,40 12,50" fill="rgba(168, 85, 247, 0.75)" stroke="#ffffff" stroke-width="2" stroke-dasharray="4 2"/>
        <circle cx="32" cy="32" r="11" fill="#0f172a" stroke="#c084fc" stroke-width="1.5"/>
        <path d="M27 36 C27 28 37 28 37 36 L37 38 L35 36 L32 38 L29 36 L27 38 Z" fill="#e9d5ff"/>
        <circle cx="29" cy="32" r="1.2" fill="#0f172a"/>
        <circle cx="35" cy="32" r="1.2" fill="#0f172a"/>
      </svg>
    `;
  }

  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg.trim());
}

/** Builds anchor marker SVG data URI */
function buildAnchorMarkerIcon() {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36">
      <circle cx="18" cy="18" r="16" fill="#ef4444" stroke="#ffffff" stroke-width="2"/>
      <circle cx="18" cy="11" r="2.5" fill="none" stroke="#ffffff" stroke-width="1.8"/>
      <line x1="18" y1="13.5" x2="18" y2="25" stroke="#ffffff" stroke-width="2"/>
      <line x1="13" y1="16.5" x2="23" y2="16.5" stroke="#ffffff" stroke-width="2"/>
      <path d="M11 20 C11 27 25 27 25 20" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>
      <polygon points="10,20 12,20 11,17" fill="#ffffff"/>
      <polygon points="24,20 26,20 25,17" fill="#ffffff"/>
    </svg>
  `;
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg.trim());
}

/** Builds lightning bolt marker SVG data URI for GPS spoof origin */
function buildLightningMarkerIcon() {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36">
      <circle cx="18" cy="18" r="16" fill="#eab308" stroke="#ffffff" stroke-width="2"/>
      <polygon points="19,7 13,18 18,18 17,29 23,17 18,17" fill="#0f172a"/>
    </svg>
  `;
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg.trim());
}

export function createAegisThreatLayer(viewer) {
  const entityMap = new Map(); // mmsi -> { ring, ship, trench, anchor }
  let unsubscribe = null;
  let animRemover = null;

  // Active Simulation State
  const simState = {
    activeArchetype: null, // 'anchor_drag' | 'gps_jump' | 'ghost_decoy'
    elapsedSec: 0.0,
    durationSec: 24.0,
    isPlaying: true,
    lastTickEpoch: performance.now(),
  };

  // Cached calculated scenario coordinates & telemetry
  const calculatedPos = {
    // Current animated vessel state
    shipLat: 60.05,
    shipLon: 25.02,
    shipHeading: 205.0,

    // Anchor Drag
    anchorLat: 60.08,
    anchorLon: 25.04,
    showTrench: false,

    // GPS Spoof Jump
    jumpOriginLat: 60.02,
    jumpOriginLon: 24.93,
    jumpDestLat: 60.0333,
    jumpDestLon: 25.0,
    isJumped: false,
    showJumpVector: false,

    // Ghost Decoy
    ghostLat: 60.05,
    ghostLon: 25.02,
    ghostOpacity: 0.0,
    radarRadiusMeters: 500.0,
    isGhostMaterialized: false,

    // Common telemetry & UI presentation
    sog: 1.2,
    score: 80.9,
    stageBadge: '',
    badgeClass: 'approach',
    stageColor: '#ef4444',
    shipLabelText: '',
  };

  /** Evaluates timeline for Yi Peng 3 Anchor Dragging Sabotage (24s) */
  function evaluateAnchorDragTimeline(elapsed) {
    const t = Math.max(0, Math.min(elapsed, 24.0));

    if (t < 8.0) {
      // Stage 1: Cruising approach (0 to 8s)
      const p = t / 8.0;
      calculatedPos.shipLat = 60.13 - p * 0.05; // 60.13 -> 60.08
      calculatedPos.shipLon = 25.09 - p * 0.045; // 25.09 -> 25.045
      calculatedPos.shipHeading = 205.0;
      calculatedPos.anchorLat = calculatedPos.shipLat;
      calculatedPos.anchorLon = calculatedPos.shipLon;
      calculatedPos.showTrench = false;
      calculatedPos.sog = 10.5;
      calculatedPos.score = 22.0 + p * 15.0;
      calculatedPos.stageBadge = 'STAGE 1: APPROACH (10.5 kn)';
      calculatedPos.badgeClass = 'approach';
      calculatedPos.stageColor = '#fef08a';
      calculatedPos.shipLabelText = `[STAGE 1/3: APPROACH] Yi Peng 3 · 10.5 kn\nCruising into 9 NM Alert Corridor · Score: ${calculatedPos.score.toFixed(1)} (NORMAL)`;
    } else if (t < 16.0) {
      // Stage 2: Deceleration & Anchor Drop inside 3 NM CPZ (8 to 16s)
      const p = (t - 8.0) / 8.0;
      calculatedPos.shipLat = 60.08 - p * 0.03; // 60.08 -> 60.05
      calculatedPos.shipLon = 25.045 - p * 0.025; // 25.045 -> 25.02
      calculatedPos.shipHeading = 205.0;
      calculatedPos.anchorLat = 60.08; // Anchor dropped to seabed at CPZ entry
      calculatedPos.anchorLon = 25.045;
      calculatedPos.showTrench = true;
      calculatedPos.sog = 10.5 - p * 9.3; // Decelerates 10.5 kn -> 1.2 kn
      calculatedPos.score = 37.0 + p * 38.0;
      calculatedPos.stageBadge = 'STAGE 2: ANCHOR DROP (1.2 kn)';
      calculatedPos.badgeClass = 'decel';
      calculatedPos.stageColor = '#fdba74';
      calculatedPos.shipLabelText = `[STAGE 2/3: DECELERATION] Yi Peng 3 · ${calculatedPos.sog.toFixed(1)} kn\nSharp Deceleration in 3 NM CPZ · Anchor Deployed · Score: ${calculatedPos.score.toFixed(1)} (HIGH)`;
    } else {
      // Stage 3: Dragging anchor across C-Lion1 subsea trench (16 to 24s)
      const creep = Math.min(8.0, t - 16.0) * 0.001;
      calculatedPos.shipLat = 60.05 - creep * 0.8;
      calculatedPos.shipLon = 25.02 - creep * 0.6;
      calculatedPos.shipHeading = 205.0;
      calculatedPos.anchorLat = 60.05; // Snagged on C-Lion1 trench line
      calculatedPos.anchorLon = 25.02;
      calculatedPos.showTrench = true;
      calculatedPos.sog = 1.2;
      calculatedPos.score = 85.0;
      calculatedPos.stageBadge = 'STAGE 3: CABLE BREACH & BGP EVAC';
      calculatedPos.badgeClass = 'breach';
      calculatedPos.stageColor = '#ef4444';
      calculatedPos.shipLabelText = `[STAGE 3/3: CABLE BREACH] Yi Peng 3 · 1.2 kn\nDragged Anchor Hooked C-Lion1 Trench · Score: 85.0 (CRITICAL)\n🛡️ AUTOMATED BGP PRE-EMPTIVE EVACUATION ARMED · ROUTE DRAIN PRIMED`;
    }
  }

  /** Evaluates timeline for SDR Spoofed Fix / Kinematic Jump (18s) */
  function evaluateGpsJumpTimeline(elapsed) {
    const t = Math.max(0, Math.min(elapsed, 18.0));

    if (t < 6.0) {
      // Stage 1: Legitimate Cruising Transit (0 to 6s)
      const p = t / 6.0;
      calculatedPos.shipLat = 60.016 + p * 0.004; // 60.016 -> 60.020
      calculatedPos.shipLon = 24.900 + p * 0.030; // 24.900 -> 24.930
      calculatedPos.shipHeading = 85.0;
      calculatedPos.isJumped = false;
      calculatedPos.showJumpVector = false;
      calculatedPos.sog = 12.0;
      calculatedPos.score = 15.0 + p * 3.0;
      calculatedPos.stageBadge = 'STAGE 1: LEGITIMATE TRANSIT (12 kn)';
      calculatedPos.badgeClass = 'legit';
      calculatedPos.stageColor = '#38bdf8';
      calculatedPos.shipLabelText = `[STAGE 1/3: LEGITIMATE FIX] Commercial Cargo\nSOG: 12.0 kn · COG: 085° · Baseline Track Normal · Score: ${calculatedPos.score.toFixed(1)} (NORMAL)`;
    } else if (t < 10.0) {
      // Stage 2: Instantaneous Teleportation Leap across C-Lion1 (6 to 10s)
      calculatedPos.shipLat = calculatedPos.jumpDestLat;
      calculatedPos.shipLon = calculatedPos.jumpDestLon;
      calculatedPos.shipHeading = 90.0;
      calculatedPos.isJumped = true;
      calculatedPos.showJumpVector = true;
      calculatedPos.sog = 1.0; // Claimed transponder speed
      calculatedPos.score = 46.8;
      calculatedPos.stageBadge = 'STAGE 2: TELEPORTATION LEAP (239.8 kn)';
      calculatedPos.badgeClass = 'jump';
      calculatedPos.stageColor = '#eab308';
      calculatedPos.shipLabelText = `⚡ [STAGE 2/3: SDR TELEMETRY JUMP DETECTED]\nReported SOG: 1.0 kn · Implied Velocity: 239.8 kn (2.0 NM in 1s)\n⚠️ IMPOSSIBLE KINEMATIC DISPLACEMENT · Score: 46.8 (ADVISORY)`;
    } else {
      // Stage 3: Trust Layer Intervention & False Alarm Suppressed (10 to 18s)
      calculatedPos.shipLat = calculatedPos.jumpDestLat;
      calculatedPos.shipLon = calculatedPos.jumpDestLon;
      calculatedPos.shipHeading = 90.0;
      calculatedPos.isJumped = true;
      calculatedPos.showJumpVector = true;
      calculatedPos.sog = 1.0;
      calculatedPos.score = 46.8;
      calculatedPos.stageBadge = 'STAGE 3: FALSE ALARM SUPPRESSED';
      calculatedPos.badgeClass = 'suppressed';
      calculatedPos.stageColor = '#fde047';
      calculatedPos.shipLabelText = `🛡️ [STAGE 3/3: TRUST LAYER INTERVENTION]\nKinematic Velocity Filter Tripped (Threshold 35 kn Exceeded)\n🛡️ FALSE ALARM SUPPRESSED · PRE-EMPTIVE FAILOVER HELD\nMonitoring Frequency Escalated (15s Cadence) · Traffic Undisturbed`;
    }
  }

  /** Evaluates timeline for Phantom Ghost Decoy / Failover DoS (18s) */
  function evaluateGhostDecoyTimeline(elapsed) {
    const t = Math.max(0, Math.min(elapsed, 18.0));

    if (t < 5.0) {
      // Stage 1: Quiet Subsea Corridor (0 to 5s)
      calculatedPos.shipLat = calculatedPos.ghostLat;
      calculatedPos.shipLon = calculatedPos.ghostLon;
      calculatedPos.shipHeading = 0.0;
      calculatedPos.ghostOpacity = 0.0;
      calculatedPos.radarRadiusMeters = 0.0;
      calculatedPos.isGhostMaterialized = false;
      calculatedPos.sog = 0.0;
      calculatedPos.score = 0.0;
      calculatedPos.stageBadge = 'STAGE 1: CORRIDOR SECURE (0 kn)';
      calculatedPos.badgeClass = 'quiet';
      calculatedPos.stageColor = '#22c55e';
      calculatedPos.shipLabelText = `[STAGE 1/3: SUBSEA CORRIDOR SECURE]\nC-Lion1 Protection Zone (CPZ) · Baseline Traffic Nominal\nNo Unauthorized Vessel Contacts`;
    } else if (t < 9.0) {
      // Stage 2: Synthesized AIS Injection / Ghost Contact Appears (5 to 9s)
      const p = (t - 5.0) / 4.0;
      calculatedPos.ghostOpacity = Math.min(1.0, p * 1.5);
      calculatedPos.shipLat = calculatedPos.ghostLat + p * 0.003;
      calculatedPos.shipLon = calculatedPos.ghostLon;
      calculatedPos.shipHeading = 0.0;
      calculatedPos.isGhostMaterialized = true;
      calculatedPos.radarRadiusMeters = 600.0 + (((t - 5.0) * 1200.0) % 3600.0);
      calculatedPos.sog = 1.5;
      calculatedPos.score = 25.0 + p * 33.0;
      calculatedPos.stageBadge = 'STAGE 2: PHANTOM INJECTION (1.5 kn)';
      calculatedPos.badgeClass = 'ghost';
      calculatedPos.stageColor = '#c084fc';
      calculatedPos.shipLabelText = `👻 [STAGE 2/3: PHANTOM CONTACT INJECTED]\nMMSI: 999000103 · SOG: 1.5 kn · Position: Inside 3 NM CPZ\n⚠️ ZERO VOYAGE HISTORY · NO RF DOPPLER · Score: ${calculatedPos.score.toFixed(1)} (ADVISORY)`;
    } else {
      // Stage 3: Failover DoS Thwarted / Route Drain Withheld (9 to 18s)
      calculatedPos.ghostOpacity = 0.85;
      calculatedPos.shipLat = calculatedPos.ghostLat + 0.003;
      calculatedPos.shipLon = calculatedPos.ghostLon;
      calculatedPos.shipHeading = 0.0;
      calculatedPos.isGhostMaterialized = true;
      calculatedPos.radarRadiusMeters = 600.0 + (((t - 9.0) * 1000.0) % 3600.0);
      calculatedPos.sog = 1.5;
      calculatedPos.score = 58.0;
      calculatedPos.stageBadge = 'STAGE 3: FAILOVER DoS THWARTED';
      calculatedPos.badgeClass = 'thwarted';
      calculatedPos.stageColor = '#a855f7';
      calculatedPos.shipLabelText = `🛡️ [STAGE 3/3: FAILOVER DoS THWARTED]\nSynthesized Transponder Broadcast (Phantom Injection) Thwarted\n🛡️ AUTOMATED ROUTE DRAIN WITHHELD · AS65000 BGP STABILITY PRESERVED\nCoastal Radar Cross-Verification Required · Satellite Tasked`;
    }
  }

  function removeEntityGroup(obj) {
    if (!viewer || !viewer.entities || !obj) return;
    for (const key of Object.keys(obj)) {
      if (obj[key]) {
        try {
          viewer.entities.remove(obj[key]);
        } catch (_) {}
      }
    }
  }

  function updateThreatEntities(threats) {
    if (!viewer || !viewer.entities) return;

    const activeMmsis = new Set();

    for (const threat of threats) {
      if (!threat.coordinates || threat.threat_level === 'NORMAL') continue;
      const mmsi = String(threat.mmsi);
      activeMmsis.add(mmsi);

      // Determine contact archetype
      let archetype = 'normal_elevated';
      if (mmsi === '412543000' || threat.vessel_name?.includes('Yi Peng 3')) {
        archetype = 'anchor_drag';
      } else if (threat.telemetry_trust?.is_jump || mmsi === '999000102') {
        archetype = 'gps_jump';
      } else if (threat.telemetry_trust?.is_ghost_candidate || mmsi === '999000103') {
        archetype = 'ghost_decoy';
      }

      if (!simState.activeArchetype && archetype !== 'normal_elevated') {
        simState.activeArchetype = archetype;
        simState.durationSec = archetype === 'anchor_drag' ? 24.0 : 18.0;
      }

      if (entityMap.has(mmsi)) {
        continue; // Already established with dynamic CallbackProperties
      }

      const created = {};
      const baseLat = threat.coordinates.lat;
      const baseLon = threat.coordinates.lon;

      // 1. CPZ Threat Halo (3 NM Ring on water surface with subtle breathing pulse)
      created.ring = viewer.entities.add({
        name: `Aegis CPZ Threat Halo: ${threat.vessel_name || mmsi}`,
        show: new Cesium.CallbackProperty(() => {
          if (archetype === 'ghost_decoy') return calculatedPos.isGhostMaterialized;
          return true;
        }, false),
        position: new Cesium.CallbackProperty(() => {
          if (archetype === 'anchor_drag' || archetype === 'gps_jump' || archetype === 'ghost_decoy') {
            return Cesium.Cartesian3.fromDegrees(calculatedPos.shipLon, calculatedPos.shipLat, 0);
          }
          return Cesium.Cartesian3.fromDegrees(baseLon, baseLat, 0);
        }, false),
        ellipse: {
          semiMajorAxis: CPZ_RADIUS_METERS,
          semiMinorAxis: CPZ_RADIUS_METERS,
          height: 0,
          fill: true,
          material: new Cesium.ColorMaterialProperty(
            new Cesium.CallbackProperty(() => {
              const pulse = 0.15 + Math.sin(simState.elapsedSec * 2.5) * 0.05;
              if (archetype === 'anchor_drag') {
                return calculatedPos.score >= 80.0
                  ? Cesium.Color.fromCssColorString('#ef4444').withAlpha(pulse + 0.1)
                  : Cesium.Color.fromCssColorString('#f97316').withAlpha(pulse);
              }
              if (archetype === 'gps_jump') {
                return calculatedPos.isJumped
                  ? Cesium.Color.fromCssColorString('#eab308').withAlpha(pulse + 0.05)
                  : Cesium.Color.fromCssColorString('#38bdf8').withAlpha(pulse);
              }
              if (archetype === 'ghost_decoy') {
                return Cesium.Color.fromCssColorString('#a855f7').withAlpha(pulse * calculatedPos.ghostOpacity);
              }
              return Cesium.Color.fromCssColorString('#38bdf8').withAlpha(pulse);
            }, false),
          ),
          outline: true,
          outlineColor: new Cesium.CallbackProperty(() => {
            if (archetype === 'anchor_drag') {
              return calculatedPos.score >= 80.0
                ? Cesium.Color.fromCssColorString('#ef4444')
                : Cesium.Color.fromCssColorString('#f97316');
            }
            if (archetype === 'gps_jump') {
              return calculatedPos.isJumped
                ? Cesium.Color.fromCssColorString('#eab308')
                : Cesium.Color.fromCssColorString('#38bdf8');
            }
            if (archetype === 'ghost_decoy') {
              return Cesium.Color.fromCssColorString('#c084fc');
            }
            return Cesium.Color.fromCssColorString('#38bdf8');
          }, false),
          outlineWidth: 3,
        },
      });

      // 2. High-Contrast Hostile Vessel Billboard & Dynamic Status Label
      created.ship = viewer.entities.add({
        name: `Simulated Target: ${threat.vessel_name || mmsi}`,
        show: new Cesium.CallbackProperty(() => {
          if (archetype === 'ghost_decoy') return calculatedPos.isGhostMaterialized;
          return true;
        }, false),
        position: new Cesium.CallbackProperty(() => {
          if (archetype === 'anchor_drag' || archetype === 'gps_jump' || archetype === 'ghost_decoy') {
            return Cesium.Cartesian3.fromDegrees(calculatedPos.shipLon, calculatedPos.shipLat, 35);
          }
          return Cesium.Cartesian3.fromDegrees(baseLon, baseLat, 35);
        }, false),
        billboard: {
          image: new Cesium.CallbackProperty(() => {
            if (archetype === 'gps_jump') {
              return calculatedPos.isJumped
                ? buildHostileShipIcon('gps_jump')
                : buildCargoShipIcon();
            }
            if (archetype === 'ghost_decoy') {
              return buildHostileShipIcon('ghost_decoy');
            }
            return buildHostileShipIcon('anchor_drag');
          }, false),
          scale: new Cesium.CallbackProperty(() => {
            if (archetype === 'ghost_decoy') {
              return 1.15 * Math.max(0.2, calculatedPos.ghostOpacity);
            }
            return 1.15;
          }, false),
          color: new Cesium.CallbackProperty(() => {
            if (archetype === 'ghost_decoy') {
              return new Cesium.Color(1, 1, 1, Math.max(0.1, calculatedPos.ghostOpacity));
            }
            return Cesium.Color.WHITE;
          }, false),
          rotation: new Cesium.CallbackProperty(() => {
            return Cesium.Math.toRadians(calculatedPos.shipHeading);
          }, false),
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
        label: {
          show: new Cesium.CallbackProperty(() => {
            if (archetype === 'ghost_decoy') return calculatedPos.isGhostMaterialized;
            return true;
          }, false),
          text: new Cesium.CallbackProperty(() => {
            if (archetype === 'anchor_drag' || archetype === 'gps_jump' || archetype === 'ghost_decoy') {
              return calculatedPos.shipLabelText;
            }
            return `⚠️ ${threat.vessel_name}\nScore: ${threat.threat_score}/100`;
          }, false),
          font: '11px "JetBrains Mono", monospace',
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          fillColor: new Cesium.CallbackProperty(() => {
            return Cesium.Color.fromCssColorString(calculatedPos.stageColor);
          }, false),
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 3,
          verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
          pixelOffset: new Cesium.Cartesian2(0, -42),
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
      });

      // 3. Scenario-Specific Bad Action Visualizations
      if (archetype === 'anchor_drag') {
        // Glowing Seabed Anchor Drag Trench Line
        created.trench = viewer.entities.add({
          name: 'Anchor Dragging Seabed Trench',
          show: new Cesium.CallbackProperty(() => calculatedPos.showTrench, false),
          polyline: {
            positions: new Cesium.CallbackProperty(() => {
              if (!calculatedPos.showTrench) {
                return [
                  Cesium.Cartesian3.fromDegrees(calculatedPos.shipLon, calculatedPos.shipLat, 0),
                  Cesium.Cartesian3.fromDegrees(calculatedPos.shipLon, calculatedPos.shipLat, 0),
                ];
              }
              return Cesium.Cartesian3.fromDegreesArrayHeights([
                calculatedPos.shipLon, calculatedPos.shipLat, 10,
                calculatedPos.anchorLon, calculatedPos.anchorLat, 0,
              ]);
            }, false),
            width: 5,
            material: new Cesium.PolylineGlowMaterialProperty({
              glowPower: 0.4,
              color: Cesium.Color.fromCssColorString('#ef4444'),
            }),
          },
        });

        // 3D Anchor Snag Hook Marker
        created.anchor = viewer.entities.add({
          name: 'Dragged Anchor Hook',
          show: new Cesium.CallbackProperty(() => calculatedPos.showTrench, false),
          position: new Cesium.CallbackProperty(() => {
            return Cesium.Cartesian3.fromDegrees(calculatedPos.anchorLon, calculatedPos.anchorLat, 15);
          }, false),
          billboard: {
            image: buildAnchorMarkerIcon(),
            scale: 0.95,
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
          label: {
            text: '⚓ DRAGGED ANCHOR (BREACHING C-LION1 TRENCH)',
            font: '10px "JetBrains Mono", monospace',
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            fillColor: Cesium.Color.fromCssColorString('#fca5a5'),
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            pixelOffset: new Cesium.Cartesian2(0, -22),
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
        });
      } else if (archetype === 'gps_jump') {
        // Yellow Dashed Teleportation Vector Line
        created.trench = viewer.entities.add({
          name: 'GPS Teleportation Vector (SDR Spoofed)',
          show: new Cesium.CallbackProperty(() => calculatedPos.showJumpVector, false),
          polyline: {
            positions: Cesium.Cartesian3.fromDegreesArrayHeights([
              calculatedPos.jumpOriginLon, calculatedPos.jumpOriginLat, 10,
              calculatedPos.jumpDestLon, calculatedPos.jumpDestLat, 10,
            ]),
            width: 4,
            material: new Cesium.PolylineDashMaterialProperty({
              color: Cesium.Color.fromCssColorString('#eab308'),
              dashLength: 14,
            }),
          },
        });

        // Origin Fix Marker (Fix 30 seconds ago)
        created.anchor = viewer.entities.add({
          name: 'Legitimate AIS Fix Origin',
          show: new Cesium.CallbackProperty(() => calculatedPos.isJumped, false),
          position: Cesium.Cartesian3.fromDegrees(
            calculatedPos.jumpOriginLon,
            calculatedPos.jumpOriginLat,
            15,
          ),
          billboard: {
            image: buildLightningMarkerIcon(),
            scale: 0.9,
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
          label: {
            text: '⚡ FIX 30s AGO (60.0200°N, 24.9300°E)\n[2.0 NM LEAP @ 239.8 KNOTS - FILTERED]',
            font: '10px "JetBrains Mono", monospace',
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            fillColor: Cesium.Color.fromCssColorString('#fef08a'),
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            pixelOffset: new Cesium.Cartesian2(0, -24),
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
        });
      } else if (archetype === 'ghost_decoy') {
        // Stage 1 Corridor Baseline Marker
        created.trench = viewer.entities.add({
          name: 'C-Lion1 Corridor Surveillance Status',
          show: new Cesium.CallbackProperty(() => !calculatedPos.isGhostMaterialized, false),
          position: Cesium.Cartesian3.fromDegrees(
            calculatedPos.ghostLon,
            calculatedPos.ghostLat,
            20,
          ),
          label: {
            text: '[SUBSEA MONITORING] C-Lion1 Cable Protection Zone (CPZ)\nCorridor Clear · Telemetry Baseline Normal',
            font: '10px "JetBrains Mono", monospace',
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            fillColor: Cesium.Color.fromCssColorString('#86efac'),
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
        });

        // Stage 2 & 3 Expanding Radar Pulses
        created.anchor = viewer.entities.add({
          name: 'Ghost Decoy Radar Pulse Ping',
          show: new Cesium.CallbackProperty(() => calculatedPos.isGhostMaterialized, false),
          position: Cesium.Cartesian3.fromDegrees(
            calculatedPos.ghostLon,
            calculatedPos.ghostLat,
            2,
          ),
          ellipse: {
            semiMajorAxis: new Cesium.CallbackProperty(() => calculatedPos.radarRadiusMeters, false),
            semiMinorAxis: new Cesium.CallbackProperty(() => calculatedPos.radarRadiusMeters, false),
            height: 2,
            fill: false,
            outline: true,
            outlineColor: new Cesium.CallbackProperty(() => {
              const alpha = Math.max(0.1, 1.0 - calculatedPos.radarRadiusMeters / 4000.0);
              return Cesium.Color.fromCssColorString('#c084fc').withAlpha(alpha);
            }, false),
            outlineWidth: 2.5,
          },
        });
      }

      entityMap.set(mmsi, created);
    }

    // Clean up entities no longer active
    for (const [mmsi, obj] of entityMap.entries()) {
      if (!activeMmsis.has(mmsi)) {
        removeEntityGroup(obj);
        entityMap.delete(mmsi);
      }
    }
  }

  /** Switches and launches an animated threat scenario */
  function startScenario(scenarioType, threat) {
    simState.activeArchetype = scenarioType;
    simState.durationSec = scenarioType === 'anchor_drag' ? 24.0 : 18.0;
    simState.elapsedSec = 0.0;
    simState.isPlaying = true;
    simState.lastTickEpoch = performance.now();

    // Immediately evaluate at t=0
    if (scenarioType === 'gps_jump') {
      evaluateGpsJumpTimeline(0.0);
    } else if (scenarioType === 'ghost_decoy') {
      evaluateGhostDecoyTimeline(0.0);
    } else {
      evaluateAnchorDragTimeline(0.0);
    }

    // Fly camera to target profile
    const cam = SCENARIO_CAMERAS[scenarioType] || SCENARIO_CAMERAS.anchor_drag;
    if (viewer && viewer.camera) {
      viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(cam.lon, cam.lat, cam.alt),
        orientation: {
          heading: Cesium.Math.toRadians(cam.heading),
          pitch: Cesium.Math.toRadians(cam.pitch),
          roll: 0.0,
        },
        duration: 2.0,
      });
    }

    updateSimulationControllerUI();
  }

  function flyToThreat(threat) {
    if (!viewer || !threat || !threat.coordinates) return;
    const mmsi = String(threat.mmsi);
    let archetype = 'anchor_drag';
    if (mmsi === '999000102' || threat.telemetry_trust?.is_jump) {
      archetype = 'gps_jump';
    } else if (mmsi === '999000103' || threat.telemetry_trust?.is_ghost_candidate) {
      archetype = 'ghost_decoy';
    }
    startScenario(archetype, threat);
  }

  // Animation Frame Loop
  animRemover = viewer.scene.preRender.addEventListener(() => {
    const nowEpoch = performance.now();
    const dt = (nowEpoch - simState.lastTickEpoch) / 1000.0;
    simState.lastTickEpoch = nowEpoch;

    if (simState.isPlaying) {
      simState.elapsedSec += dt;
      if (simState.elapsedSec > simState.durationSec) {
        simState.elapsedSec = simState.durationSec; // Hold at completion
      }
    }

    // Evaluate active archetype kinematic timeline
    if (simState.activeArchetype === 'gps_jump') {
      evaluateGpsJumpTimeline(simState.elapsedSec);
    } else if (simState.activeArchetype === 'ghost_decoy') {
      evaluateGhostDecoyTimeline(simState.elapsedSec);
    } else if (simState.activeArchetype === 'anchor_drag') {
      evaluateAnchorDragTimeline(simState.elapsedSec);
    }

    updateSimulationControllerUI();
  });

  function updateSimulationControllerUI() {
    const ctrl = document.getElementById('aegis-sim-controller');
    if (!ctrl || !simState.activeArchetype) return;

    ctrl.hidden = false;

    const progressEl = document.getElementById('aegis-sim-progress');
    const timeTextEl = document.getElementById('aegis-sim-time-text');
    const stageBadgeEl = document.getElementById('aegis-sim-stage-badge');
    const liveSogEl = document.getElementById('aegis-sim-live-sog');
    const liveScoreEl = document.getElementById('aegis-sim-live-score');
    const playBtn = document.getElementById('aegis-sim-play-btn');

    const duration = simState.durationSec || 24.0;
    if (progressEl) {
      const ratio = (simState.elapsedSec / duration) * 100;
      progressEl.value = ratio.toFixed(1);
    }
    if (timeTextEl) {
      const curSec = Math.floor(simState.elapsedSec);
      const totalSec = Math.floor(duration);
      timeTextEl.textContent = `00:${curSec.toString().padStart(2, '0')} / 00:${totalSec.toString().padStart(2, '0')}`;
    }
    if (liveSogEl) {
      liveSogEl.textContent = `${calculatedPos.sog.toFixed(1)} kn`;
    }
    if (liveScoreEl) {
      liveScoreEl.textContent = `Score: ${calculatedPos.score.toFixed(1)}`;
      liveScoreEl.style.color = calculatedPos.stageColor;
    }
    if (playBtn) {
      playBtn.textContent = simState.isPlaying ? '⏸' : '▶';
    }
    if (stageBadgeEl) {
      stageBadgeEl.textContent = calculatedPos.stageBadge;
      stageBadgeEl.className = `aegis-stage-badge ${calculatedPos.badgeClass}`;
    }
  }

  // Subscribe to service updates
  unsubscribe = aegisThreatService.subscribe((state) => {
    updateThreatEntities(state.threats);
  });

  return {
    startScenario,
    flyToThreat,
    simState,
    setSimulationTime(sec) {
      simState.elapsedSec = Math.max(0, Math.min(sec, simState.durationSec));
      if (simState.activeArchetype === 'gps_jump') {
        evaluateGpsJumpTimeline(simState.elapsedSec);
      } else if (simState.activeArchetype === 'ghost_decoy') {
        evaluateGhostDecoyTimeline(simState.elapsedSec);
      } else {
        evaluateAnchorDragTimeline(simState.elapsedSec);
      }
      updateSimulationControllerUI();
    },
    togglePlay() {
      simState.isPlaying = !simState.isPlaying;
      simState.lastTickEpoch = performance.now();
      return simState.isPlaying;
    },
    replay() {
      simState.elapsedSec = 0.0;
      simState.isPlaying = true;
      simState.lastTickEpoch = performance.now();
      if (simState.activeArchetype === 'gps_jump') {
        evaluateGpsJumpTimeline(0.0);
      } else if (simState.activeArchetype === 'ghost_decoy') {
        evaluateGhostDecoyTimeline(0.0);
      } else {
        evaluateAnchorDragTimeline(0.0);
      }
      updateSimulationControllerUI();
    },
    destroy() {
      if (unsubscribe) unsubscribe();
      if (animRemover) animRemover();
      if (viewer && viewer.entities) {
        for (const obj of entityMap.values()) {
          removeEntityGroup(obj);
        }
      }
      entityMap.clear();
    },
  };
}
