/**
 * Aegis-Sea 3D Visual Threat & Adversary Simulation Layer for CesiumJS.
 * Renders:
 * 1. 3.0 NM Cable Protection Zone (CPZ) danger halos.
 * 2. High-contrast simulated adversary ships (distinct from commercial vessels).
 * 3. Physical anchor-dragging seabed trench cables cutting across subsea cables.
 * 4. GPS spoofing teleportation vectors and phantom ghost decoys.
 * 5. Real-time dynamic kinematic dragging animation.
 */

import * as Cesium from 'cesium';
import { aegisThreatService } from '../services/aegisThreatService.js';

const CPZ_RADIUS_METERS = 5556.0; // 3.0 Nautical Miles (Cable Protection Zone)

/** Builds high-contrast SVG data URI for adversary/simulated ships */
function buildHostileShipIcon(type) {
  let svg = '';

  if (type === 'anchor_drag') {
    // Red hostile hull with anchor badge (SVG paths only, no unicode font glyphs)
    svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r="28" fill="rgba(239, 68, 68, 0.28)" stroke="#ef4444" stroke-width="2.5" stroke-dasharray="6 3"/>
        <polygon points="32,4 50,50 32,40 14,50" fill="#ef4444" stroke="#ffffff" stroke-width="2.5"/>
        <circle cx="32" cy="32" r="11" fill="#0f172a" stroke="#ffffff" stroke-width="1.5"/>
        <!-- SVG Anchor Icon -->
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
        <circle cx="32" cy="32" r="28" fill="rgba(234, 179, 8, 0.22)" stroke="#eab308" stroke-width="2" stroke-dasharray="5 3"/>
        <polygon points="32,4 50,50 32,40 14,50" fill="#eab308" stroke="#ffffff" stroke-width="2"/>
        <circle cx="32" cy="32" r="10" fill="#0f172a" stroke="#ffffff" stroke-width="1.5"/>
        <!-- SVG Lightning Bolt -->
        <polygon points="33,25 28,32 32,32 31,39 36,31 32,31" fill="#fef08a"/>
      </svg>
    `;
  } else {
    // Translucent purple ghost decoy with ghost outline badge
    svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r="28" fill="rgba(168, 85, 247, 0.18)" stroke="#c084fc" stroke-width="1.5" stroke-dasharray="4 3"/>
        <polygon points="32,4 50,50 32,40 14,50" fill="rgba(168, 85, 247, 0.6)" stroke="#ffffff" stroke-width="2" stroke-dasharray="4 2"/>
        <circle cx="32" cy="32" r="10" fill="#0f172a" stroke="#c084fc" stroke-width="1.5"/>
        <!-- SVG Ghost Icon -->
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
  const entityMap = new Map(); // mmsi -> { ring, ship, trench, anchor, label }
  let unsubscribe = null;
  let animRemover = null;

  // Active simulated ship animation state
  let simulatedDragOffset = 0.0;

  function getLevelColors(level) {
    switch (level) {
      case 'CRITICAL':
        return {
          fill: Cesium.Color.fromCssColorString('#ef4444').withAlpha(0.2),
          outline: Cesium.Color.fromCssColorString('#ef4444').withAlpha(0.95),
        };
      case 'HIGH':
        return {
          fill: Cesium.Color.fromCssColorString('#f97316').withAlpha(0.15),
          outline: Cesium.Color.fromCssColorString('#f97316').withAlpha(0.85),
        };
      case 'ADVISORY':
        return {
          fill: Cesium.Color.fromCssColorString('#eab308').withAlpha(0.1),
          outline: Cesium.Color.fromCssColorString('#eab308').withAlpha(0.7),
        };
      default:
        return null;
    }
  }

  function updateThreatEntities(threats) {
    if (!viewer || !viewer.entities) return;

    const activeMmsis = new Set();

    for (const threat of threats) {
      if (!threat.coordinates || threat.threat_level === 'NORMAL') continue;
      const mmsi = String(threat.mmsi);
      activeMmsis.add(mmsi);

      const lat = threat.coordinates.lat;
      const lon = threat.coordinates.lon;
      const colors = getLevelColors(threat.threat_level);
      if (!colors) continue;

      const surfacePos = Cesium.Cartesian3.fromDegrees(lon, lat, 0);
      const shipPos = Cesium.Cartesian3.fromDegrees(lon, lat, 45); // Elevated slightly above sea level

      // Determine simulated contact archetype
      let archetype = 'normal_elevated';
      if (mmsi === '412543000' || threat.vessel_name?.includes('Yi Peng 3')) {
        archetype = 'anchor_drag';
      } else if (threat.telemetry_trust?.is_jump || mmsi === '999000102') {
        archetype = 'gps_jump';
      } else if (threat.telemetry_trust?.is_ghost_candidate || mmsi === '999000103') {
        archetype = 'ghost_decoy';
      }

      const existing = entityMap.get(mmsi);

      if (existing) {
        // Update positions
        if (existing.ring) {
          existing.ring.position = surfacePos;
          existing.ring.ellipse.material = colors.fill;
          existing.ring.ellipse.outlineColor = colors.outline;
        }
        if (existing.ship) {
          existing.ship.position = shipPos;
        }
      } else {
        const created = {};

        // 1. CPZ Threat Halo (3 NM Ring on water surface)
        created.ring = viewer.entities.add({
          name: `Aegis CPZ Threat Halo: ${threat.vessel_name || mmsi}`,
          position: surfacePos,
          ellipse: {
            semiMajorAxis: CPZ_RADIUS_METERS,
            semiMinorAxis: CPZ_RADIUS_METERS,
            height: 0,
            fill: true,
            material: colors.fill,
            outline: true,
            outlineColor: colors.outline,
            outlineWidth: threat.threat_level === 'CRITICAL' ? 3 : 2,
          },
        });

        // 2. Distinct Adversary Ship Billboard & Heading
        const headingDeg = Number(threat.cog_degrees || threat.heading_degrees || 0);
        created.ship = viewer.entities.add({
          name: `Simulated Target: ${threat.vessel_name || mmsi}`,
          position: shipPos,
          billboard: {
            image: buildHostileShipIcon(archetype),
            scale: 1.1,
            rotation: Cesium.Math.toRadians(headingDeg),
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
          label: {
            text: buildLabelText(threat, archetype),
            font: '11px "JetBrains Mono", monospace',
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            fillColor: threat.threat_level === 'CRITICAL' ? Cesium.Color.fromCssColorString('#fca5a5') : Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 3,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new Cesium.Cartesian2(0, -42),
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
        });

        // 3. Bad Action Visualizations:
        if (archetype === 'anchor_drag') {
          // Trailing Anchor Dragging Trench line cutting across the seabed corridor
          // Vessel moving course ~205 deg (south-southwest), so anchor trails north-northeast
          const anchorLon = lon + 0.018;
          const anchorLat = lat + 0.035;

          created.trench = viewer.entities.add({
            name: 'Anchor Dragging Seabed Trench',
            polyline: {
              positions: Cesium.Cartesian3.fromDegreesArrayHeights([
                lon, lat, 10,
                anchorLon, anchorLat, 0,
              ]),
              width: 5,
              material: new Cesium.PolylineGlowMaterialProperty({
                glowPower: 0.35,
                color: Cesium.Color.fromCssColorString('#ef4444'),
              }),
            },
          });

          // Anchor Hook Marker on the cable trench
          created.anchor = viewer.entities.add({
            position: Cesium.Cartesian3.fromDegrees(anchorLon, anchorLat, 15),
            billboard: {
              image: buildAnchorMarkerIcon(),
              scale: 0.9,
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
          // Teleportation Vector Line (showing impossible 2 NM jump in 30 seconds)
          const priorLon = lon - 0.045;
          const priorLat = lat - 0.02;

          created.trench = viewer.entities.add({
            name: 'GPS Teleportation Vector (SDR Spoofed)',
            polyline: {
              positions: Cesium.Cartesian3.fromDegreesArray([
                priorLon, priorLat,
                lon, lat,
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
    }

    // Clean up entities for threats that were cleared
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

  function buildLabelText(threat, archetype) {
    const score = Number(threat.threat_score || 0).toFixed(1);
    const speed = Number(threat.sog_knots || 0).toFixed(1);
    const cable = threat.closest_cable?.cable_name || 'Subsea Cable';

    if (archetype === 'anchor_drag') {
      return `🚨 [HOSTILE CONTACT] ${threat.vessel_name}\n⚓ DRAGGING ANCHOR ACROSS ${cable.toUpperCase()} @ ${speed} kn\n⚡ THREAT SCORE: ${score}/100 (CRITICAL)\n🛡️ BGP PRE-EMPTIVE EVACUATION ARMED`;
    } else if (archetype === 'gps_jump') {
      return `⚡ [SDR TELEMETRY SPOOF] ${threat.vessel_name}\n⚠️ IMPOSSIBLE KINEMATIC DISPLACEMENT (239.8 kn)\n🛡️ TRUST LAYER: ALARM SUPPRESSED (SCORE: ${score})\n⚡ ACTION: INCREASE MONITORED CADENCE`;
    } else if (archetype === 'ghost_decoy') {
      return `👻 [PHANTOM GHOST DECOY] ${threat.vessel_name}\n⚠️ ZERO VOYAGE HISTORY · APPEARED DIRECTLY IN CPZ\n🛡️ TRUST LAYER: ROUTE DRAIN HELD FOR OPERATOR CONFIRMATION\n⚡ ACTION: VERIFY TARGET AUTHENTICITY`;
    }

    return `⚠️ ${threat.vessel_name}\nSCORE: ${score} (${threat.threat_level})\nTARGET: ${cable}`;
  }

  function flyToThreat(threat) {
    if (!viewer || !threat || !threat.coordinates) return;
    const lat = threat.coordinates.lat;
    const lon = threat.coordinates.lon;

    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(lon, lat - 0.05, 14000), // Close tactical angle
      orientation: {
        heading: Cesium.Math.toRadians(0),
        pitch: Cesium.Math.toRadians(-45),
        roll: 0.0,
      },
      duration: 1.8,
    });
  }

  // Active creeping animation for dragging anchor
  animRemover = viewer.scene.preRender.addEventListener(() => {
    const yiPeng = entityMap.get('412543000');
    if (yiPeng && yiPeng.ship && yiPeng.trench) {
      simulatedDragOffset += 0.0000008; // Creeps slowly along heading
      const currentLat = 60.05 - simulatedDragOffset;
      const currentLon = 25.02 - (simulatedDragOffset * 0.4);

      const shipPos = Cesium.Cartesian3.fromDegrees(currentLon, currentLat, 45);
      yiPeng.ship.position = shipPos;

      // Trailing anchor line
      const anchorLon = currentLon + 0.018;
      const anchorLat = currentLat + 0.035;
      yiPeng.trench.polyline.positions = Cesium.Cartesian3.fromDegreesArrayHeights([
        currentLon, currentLat, 10,
        anchorLon, anchorLat, 0,
      ]);
    }
  });

  // Subscribe to service updates
  unsubscribe = aegisThreatService.subscribe((state) => {
    updateThreatEntities(state.threats);
  });

  return {
    flyToThreat,
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
