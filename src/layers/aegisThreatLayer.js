/**
 * Aegis-Sea 3D Visual Threat & Adversary Simulation Layer for CesiumJS.
 * Features:
 * 1. Animated kinematic threat progression (Approach -> Deceleration -> Cable Breach -> Failover).
 * 2. 3.0 NM Cable Protection Zone (CPZ) danger halos with smooth alpha pulsing.
 * 3. High-contrast simulated adversary ship billboards (red hull, yellow jump, purple ghost).
 * 4. Glowing seabed anchor drag furrow line cutting across C-Lion1 subsea cable trench.
 * 5. Interactive simulation controls: Play, Pause, Replay, and Scrubber Timeline.
 * 6. Dynamic Cesium CallbackProperties that never crash or get wiped by background polling.
 */

import * as Cesium from 'cesium';
import { aegisThreatService } from '../services/aegisThreatService.js';

const CPZ_RADIUS_METERS = 5556.0; // 3.0 Nautical Miles (Cable Protection Zone)
const SIMULATION_DURATION_SEC = 24.0;

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
        <circle cx="32" cy="32" r="28" fill="rgba(234, 179, 8, 0.25)" stroke="#eab308" stroke-width="2" stroke-dasharray="5 3"/>
        <polygon points="32,4 52,50 32,40 12,50" fill="#eab308" stroke="#ffffff" stroke-width="2"/>
        <circle cx="32" cy="32" r="10" fill="#0f172a" stroke="#ffffff" stroke-width="1.5"/>
        <polygon points="33,25 28,32 32,32 31,39 36,31 32,31" fill="#fef08a"/>
      </svg>
    `;
  } else {
    // Translucent purple ghost decoy with ghost outline badge
    svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r="28" fill="rgba(168, 85, 247, 0.2)" stroke="#c084fc" stroke-width="1.5" stroke-dasharray="4 3"/>
        <polygon points="32,4 52,50 32,40 12,50" fill="rgba(168, 85, 247, 0.65)" stroke="#ffffff" stroke-width="2" stroke-dasharray="4 2"/>
        <circle cx="32" cy="32" r="10" fill="#0f172a" stroke="#c084fc" stroke-width="1.5"/>
        <path d="M28 36 C28 29 36 29 36 36 L36 37 L34 35 L32 37 L30 35 L28 37 Z" fill="#e9d5ff"/>
        <circle cx="30" cy="32" r="1" fill="#0f172a"/>
        <circle cx="34" cy="32" r="1" fill="#0f172a"/>
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

export function createAegisThreatLayer(viewer) {
  const entityMap = new Map(); // mmsi -> { ring, ship, trench, anchor, label, extra }
  let unsubscribe = null;
  let animRemover = null;

  // Active Simulation State
  const simState = {
    activeArchetype: null, // 'anchor_drag' | 'gps_jump' | 'ghost_decoy' | null
    elapsedSec: 0.0,
    durationSec: SIMULATION_DURATION_SEC,
    isPlaying: true,
    lastTickEpoch: performance.now(),
  };

  // Cached calculated scenario coordinates
  const calculatedPos = {
    shipLat: 60.05,
    shipLon: 25.02,
    anchorLat: 60.08,
    anchorLon: 25.04,
    sog: 1.2,
    score: 80.9,
    stageText: '',
  };

  /** Interpolates position and telemetry for Yi Peng 3 Anchor Drag scenario */
  function evaluateAnchorDragTimeline(elapsed) {
    const t = Math.min(elapsed, SIMULATION_DURATION_SEC);

    if (t < 8.0) {
      // Stage 1: Cruising approach (t: 0 to 8s)
      const p = t / 8.0;
      calculatedPos.shipLat = 60.13 - (p * 0.05); // 60.13 -> 60.08
      calculatedPos.shipLon = 25.09 - (p * 0.045); // 25.09 -> 25.045
      calculatedPos.anchorLat = calculatedPos.shipLat;
      calculatedPos.anchorLon = calculatedPos.shipLon;
      calculatedPos.sog = 10.5;
      calculatedPos.score = 22.0 + (p * 15.0);
      calculatedPos.stageText = `[STAGE 1/3: APPROACH] 10.5 kn · Cruising into 9 NM Alert Corridor · Score: ${calculatedPos.score.toFixed(1)} (NORMAL)`;
    } else if (t < 16.0) {
      // Stage 2: Deceleration & Anchor Drop inside 3 NM CPZ (t: 8 to 16s)
      const p = (t - 8.0) / 8.0;
      calculatedPos.shipLat = 60.08 - (p * 0.03); // 60.08 -> 60.05 (approaching cable)
      calculatedPos.shipLon = 25.045 - (p * 0.025); // 25.045 -> 25.02
      calculatedPos.anchorLat = 60.08; // Anchor caught at seabed drop point
      calculatedPos.anchorLon = 25.045;
      calculatedPos.sog = 10.5 - (p * 9.3); // Decelerates 10.5 kn -> 1.2 kn
      calculatedPos.score = 37.0 + (p * 38.0);
      calculatedPos.stageText = `[STAGE 2/3: DECELERATION] ${calculatedPos.sog.toFixed(1)} kn · Sharp Deceleration in 3 NM CPZ · Anchor Deployed · Score: ${calculatedPos.score.toFixed(1)} (HIGH)`;
    } else {
      // Stage 3: Dragging anchor across C-Lion1 subsea trench (t: 16 to 24s and onward)
      const creep = (t - 16.0) * 0.0025;
      calculatedPos.shipLat = 60.05 - (creep * 0.8);
      calculatedPos.shipLon = 25.02 - (creep * 0.6);
      calculatedPos.anchorLat = 60.05; // Snagged on C-Lion1 trench line
      calculatedPos.anchorLon = 25.02;
      calculatedPos.sog = 1.2;
      calculatedPos.score = 85.0;
      calculatedPos.stageText = `[STAGE 3/3: CABLE BREACH] 1.2 kn · Dragged Anchor Hooked C-Lion1 Trench · Score: 85.0 (CRITICAL)\n🛡️ AUTOMATED BGP PRE-EMPTIVE EVACUATION ARMED · ROUTE DRAIN PRIMED`;
    }
  }

  function updateThreatEntities(threats) {
    if (!viewer || !viewer.entities) return;

    const activeMmsis = new Set();

    for (const threat of threats) {
      if (!threat.coordinates || threat.threat_level === 'NORMAL') continue;
      const mmsi = String(threat.mmsi);
      activeMmsis.add(mmsi);

      // Determine simulated contact archetype
      let archetype = 'normal_elevated';
      if (mmsi === '412543000' || threat.vessel_name?.includes('Yi Peng 3')) {
        archetype = 'anchor_drag';
        simState.activeArchetype = 'anchor_drag';
      } else if (threat.telemetry_trust?.is_jump || mmsi === '999000102') {
        archetype = 'gps_jump';
        simState.activeArchetype = 'gps_jump';
      } else if (threat.telemetry_trust?.is_ghost_candidate || mmsi === '999000103') {
        archetype = 'ghost_decoy';
        simState.activeArchetype = 'ghost_decoy';
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
        position: new Cesium.CallbackProperty(() => {
          if (archetype === 'anchor_drag') {
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
              const pulse = 0.15 + (Math.sin(simState.elapsedSec * 2.5) * 0.05);
              if (archetype === 'anchor_drag') {
                return calculatedPos.score >= 80.0
                  ? Cesium.Color.fromCssColorString('#ef4444').withAlpha(pulse + 0.1)
                  : Cesium.Color.fromCssColorString('#f97316').withAlpha(pulse);
              }
              if (archetype === 'gps_jump') {
                return Cesium.Color.fromCssColorString('#eab308').withAlpha(pulse);
              }
              return Cesium.Color.fromCssColorString('#a855f7').withAlpha(pulse);
            }, false),
          ),
          outline: true,
          outlineColor: new Cesium.CallbackProperty(() => {
            if (archetype === 'anchor_drag') {
              return calculatedPos.score >= 80.0
                ? Cesium.Color.fromCssColorString('#ef4444')
                : Cesium.Color.fromCssColorString('#f97316');
            }
            if (archetype === 'gps_jump') return Cesium.Color.fromCssColorString('#eab308');
            return Cesium.Color.fromCssColorString('#c084fc');
          }, false),
          outlineWidth: 3,
        },
      });

      // 2. High-Contrast Hostile Vessel Billboard & Status Label
      const headingDeg = Number(threat.cog_degrees || threat.heading_degrees || 205);

      created.ship = viewer.entities.add({
        name: `Simulated Target: ${threat.vessel_name || mmsi}`,
        position: new Cesium.CallbackProperty(() => {
          if (archetype === 'anchor_drag') {
            return Cesium.Cartesian3.fromDegrees(calculatedPos.shipLon, calculatedPos.shipLat, 35);
          }
          if (archetype === 'gps_jump') {
            // Jumps at t=4s
            if (simState.elapsedSec < 4.0) {
              return Cesium.Cartesian3.fromDegrees(baseLon - 0.045, baseLat - 0.02, 35);
            }
            return Cesium.Cartesian3.fromDegrees(baseLon, baseLat, 35);
          }
          if (archetype === 'ghost_decoy') {
            // Materializes at t=3s
            return Cesium.Cartesian3.fromDegrees(baseLon, baseLat, 35);
          }
          return Cesium.Cartesian3.fromDegrees(baseLon, baseLat, 35);
        }, false),
        billboard: {
          image: buildHostileShipIcon(archetype),
          scale: 1.15,
          rotation: Cesium.Math.toRadians(headingDeg),
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
        label: {
          text: new Cesium.CallbackProperty(() => {
            if (archetype === 'anchor_drag') {
              return calculatedPos.stageText;
            }
            if (archetype === 'gps_jump') {
              if (simState.elapsedSec < 4.0) {
                return `[STAGE 1/2: NORMAL TRANSIT] ${threat.vessel_name}\nSOG: 12.0 kn · Legitimate AIS Fix · Threat Score: 15.0`;
              }
              return `⚡ [SDR TELEMETRY SPOOF] ${threat.vessel_name}\n⚠️ IMPOSSIBLE KINEMATIC DISPLACEMENT (239.8 kn)\n🛡️ TRUST LAYER: ALARM SUPPRESSED (SCORE: 46.8)\n⚡ ACTION: INCREASE MONITORED CADENCE`;
            }
            if (archetype === 'ghost_decoy') {
              if (simState.elapsedSec < 3.0) {
                return `[MONITORING] Scanning C-Lion1 Cable Protection Zone...`;
              }
              return `👻 [PHANTOM GHOST DECOY] ${threat.vessel_name}\n⚠️ ZERO VOYAGE HISTORY · APPEARED ABRUPTLY IN CPZ\n🛡️ TRUST LAYER: ROUTE DRAIN HELD FOR OPERATOR CONFIRMATION\n⚡ ACTION: VERIFY TARGET AUTHENTICITY`;
            }
            return `⚠️ ${threat.vessel_name}\nScore: ${threat.threat_score}/100`;
          }, false),
          font: '11px "JetBrains Mono", monospace',
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          fillColor: Cesium.Color.WHITE,
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 3,
          verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
          pixelOffset: new Cesium.Cartesian2(0, -42),
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
      });

      // 3. Bad Action Visualizations:
      if (archetype === 'anchor_drag') {
        // Glowing Seabed Anchor Drag Trench Line
        created.trench = viewer.entities.add({
          name: 'Anchor Dragging Seabed Trench',
          polyline: {
            positions: new Cesium.CallbackProperty(() => {
              if (simState.elapsedSec < 8.0) {
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
        const priorLon = baseLon - 0.045;
        const priorLat = baseLat - 0.02;

        created.trench = viewer.entities.add({
          name: 'GPS Teleportation Vector (SDR Spoofed)',
          polyline: {
            positions: Cesium.Cartesian3.fromDegreesArray([
              priorLon, priorLat,
              baseLon, baseLat,
            ]),
            width: 3,
            material: new Cesium.PolylineDashMaterialProperty({
              color: Cesium.Color.fromCssColorString('#eab308'),
              dashLength: 12,
            }),
          },
        });

        created.anchor = viewer.entities.add({
          position: Cesium.Cartesian3.fromDegrees(priorLon, priorLat, 15),
          label: {
            text: '⚡ FIX 30s AGO (2.0 NM LEAP @ 240 KNOTS)\n[FILTERED AS IMPOSSIBLE VELOCITY]',
            font: '10px "JetBrains Mono", monospace',
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            fillColor: Cesium.Color.fromCssColorString('#fef08a'),
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
        });
      }

      entityMap.set(mmsi, created);
    }

    // Clean up threats that were cleared (ignoring active simulations)
    for (const [mmsi, obj] of entityMap.entries()) {
      if (!activeMmsis.has(mmsi)) {
        if (obj.ring) viewer.entities.remove(obj.ring);
        if (obj.ship) viewer.entities.remove(obj.ship);
        if (obj.trench) viewer.entities.remove(obj.trench);
        if (obj.anchor) viewer.entities.remove(obj.anchor);
        entityMap.delete(mmsi);
      }
    }
  }

  function flyToThreat(threat) {
    if (!viewer || !threat || !threat.coordinates) return;
    const lat = threat.coordinates.lat;
    const lon = threat.coordinates.lon;

    // Reset simulation progress on trigger
    simState.elapsedSec = 0.0;
    simState.isPlaying = true;
    simState.lastTickEpoch = performance.now();

    // Cinematic low-angle camera framing subsea corridor
    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(lon + 0.015, lat - 0.045, 8500),
      orientation: {
        heading: Cesium.Math.toRadians(15),
        pitch: Cesium.Math.toRadians(-35),
        roll: 0.0,
      },
      duration: 2.2,
    });
  }

  // Animation Frame Loop
  animRemover = viewer.scene.preRender.addEventListener(() => {
    const nowEpoch = performance.now();
    const dt = (nowEpoch - simState.lastTickEpoch) / 1000.0;
    simState.lastTickEpoch = nowEpoch;

    if (simState.isPlaying && simState.activeArchetype === 'anchor_drag') {
      simState.elapsedSec += dt;
      if (simState.elapsedSec > SIMULATION_DURATION_SEC) {
        simState.elapsedSec = SIMULATION_DURATION_SEC; // Settle at breach
      }
    } else if (simState.isPlaying) {
      simState.elapsedSec += dt;
      if (simState.elapsedSec > 20.0) {
        simState.elapsedSec = 20.0;
      }
    }

    // Calculate positions
    evaluateAnchorDragTimeline(simState.elapsedSec);

    // Update simulation controller UI elements if present
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

    if (progressEl) {
      const ratio = (simState.elapsedSec / SIMULATION_DURATION_SEC) * 100;
      progressEl.value = ratio.toFixed(1);
    }
    if (timeTextEl) {
      const curSec = Math.floor(simState.elapsedSec);
      timeTextEl.textContent = `00:${curSec.toString().padStart(2, '0')} / 00:24`;
    }
    if (liveSogEl) {
      liveSogEl.textContent = `${calculatedPos.sog.toFixed(1)} kn`;
    }
    if (liveScoreEl) {
      liveScoreEl.textContent = `Score: ${calculatedPos.score.toFixed(1)}`;
      liveScoreEl.style.color = calculatedPos.score >= 80 ? '#ef4444' : (calculatedPos.score >= 60 ? '#f97316' : '#eab308');
    }
    if (playBtn) {
      playBtn.textContent = simState.isPlaying ? '⏸' : '▶';
    }
    if (stageBadgeEl) {
      if (simState.elapsedSec < 8.0) {
        stageBadgeEl.textContent = 'STAGE 1: APPROACH (10.5 kn)';
        stageBadgeEl.className = 'aegis-stage-badge approach';
      } else if (simState.elapsedSec < 16.0) {
        stageBadgeEl.textContent = 'STAGE 2: ANCHOR DROP (1.2 kn)';
        stageBadgeEl.className = 'aegis-stage-badge decel';
      } else {
        stageBadgeEl.textContent = 'STAGE 3: CABLE BREACH & BGP EVAC';
        stageBadgeEl.className = 'aegis-stage-badge breach';
      }
    }
  }

  // Subscribe to service updates
  unsubscribe = aegisThreatService.subscribe((state) => {
    updateThreatEntities(state.threats);
  });

  return {
    flyToThreat,
    simState,
    setSimulationTime(sec) {
      simState.elapsedSec = Math.max(0, Math.min(sec, SIMULATION_DURATION_SEC));
      evaluateAnchorDragTimeline(simState.elapsedSec);
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
      evaluateAnchorDragTimeline(0.0);
    },
    destroy() {
      if (unsubscribe) unsubscribe();
      if (animRemover) animRemover();
      if (viewer && viewer.entities) {
        for (const obj of entityMap.values()) {
          if (obj.ring) viewer.entities.remove(obj.ring);
          if (obj.ship) viewer.entities.remove(obj.ship);
          if (obj.trench) viewer.entities.remove(obj.trench);
          if (obj.anchor) viewer.entities.remove(obj.anchor);
        }
      }
      entityMap.clear();
    },
  };
}
