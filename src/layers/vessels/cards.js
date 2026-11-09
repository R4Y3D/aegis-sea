import {
  accentForVesselType,
  normalizeVesselType,
} from '../../data/vesselLabels.js';
import { aegisThreatService } from '../../services/aegisThreatService.js';

export function createCards({
  vesselState,
  services,
  parts: components,
  layer,
  options,
}) {
  const { state } = vesselState;

  function updateSelectedVesselHud(record) {
    const el = document.getElementById('hud-ais-vessel');
    if (!el) return;

    // Pinned vessels missing from recent refreshes get a stale marker
    const stale = (record.missedRefreshes || 0) > 0;
    el.classList.add('active');
    const lines = [
      `AIS: ${trimHudValue(record.name, 32)}`,
      `${trimHudValue(record.type || 'VESSEL', 24)}  SPD: ${formatSpeed(record.speed)}  HDG: ${formatHeading(record.heading ?? record.course)}`,
      `MMSI: ${record.mmsi || '--'}  ${formatPositionTime(record)}${stale ? '  · STALE' : ''}`,
    ];

    const threat = record?.mmsi ? aegisThreatService.getThreatForMmsi(record.mmsi) : null;
    if (threat && threat.threat_level) {
      const scoreStr = Number(threat.threat_score || 0).toFixed(1);
      const cableStr = threat.closest_cable ? ` · ${trimHudValue(threat.closest_cable.cable_name, 22)} (${Number(threat.closest_cable.distance_nm || 0).toFixed(1)} NM)` : '';
      lines.push(`AEGIS: ${threat.threat_level} (${scoreStr}/100)${cableStr}`);
    }

    el.textContent = lines.join('\n');
  }

  function resetSelectedVesselHud() {
    const el = document.getElementById('hud-ais-vessel');
    if (!el) return;
    el.classList.remove('active');
    el.textContent = 'AIS: --';
  }

  function trimHudValue(value, maxLength) {
    const text = String(value || '--').trim() || '--';
    return text.length > maxLength
      ? `${text.slice(0, maxLength - 3)}...`
      : text;
  }

  /**
   * Card model for an ambient (decluttered-in) vessel — name title plus one
   * compact type/speed/heading detail line, anchored at the record's current
   * rendered position (height-datum caveat: no datum work here). Pure —
   * exported for unit tests.
   * @param {Object} record - Vessel record.
   * @returns {Object} vesselLabels entry.
   */

  function buildVesselCard(record) {
    const parts = [];
    const type = vesselTypeShort(record);
    if (type) parts.push(type);
    if (record.speed !== null && record.speed !== undefined)
      parts.push(formatSpeed(record.speed));
    const direction = record.heading ?? record.course;
    if (Number.isFinite(direction)) parts.push(`${Math.round(direction)}°`);

    let accent = accentForVesselType(record.type);
    const threat = record?.mmsi ? aegisThreatService.getThreatForMmsi(record.mmsi) : null;
    if (threat && threat.threat_level && threat.threat_level !== 'NORMAL') {
      if (threat.threat_level === 'CRITICAL') accent = '#ef4444';
      else if (threat.threat_level === 'HIGH') accent = '#f97316';
      else if (threat.threat_level === 'ADVISORY') accent = '#eab308';
      parts.unshift(`⚠️ ${threat.threat_level}`);
    }

    return {
      id: vesselOverlayEntryId(record),
      actionable: Boolean(record?.mmsi),
      position:
        components.rendering.getVisual(record).billboard?.position ||
        components.rendering.getVisual(record).position,
      gapPx: 10,
      accent,
      title: trimHudValue(displayVesselName(record), 26),
      details: parts.length ? [parts.join(' · ')] : [],
      selected: false,
      priority: components.rendering.labelPriority(record, null),
    };
  }

  /**
   * Card model for the click-selected vessel — the full-detail card, drawn last
   * (on top) and never distance-faded by the overlay. Pinned-but-vanished
   * vessels carry a STALE marker (mirrors the HUD readout). Pure — exported
   * for unit tests.
   * @param {Object} record - Selected vessel record.
   * @returns {Object} vesselLabels entry.
   */

  function buildSelectedVesselCard(record) {
    const direction = record.heading ?? record.course;
    const details = [
      [
        vesselTypeShort(record) || 'VESSEL',
        formatSpeed(record.speed),
        Number.isFinite(direction) ? `${Math.round(direction)}°` : '--°',
      ].join(' · '),
    ];
    const destination = String(record.destination || '').trim();
    if (destination) details.push(`→ ${trimHudValue(destination, 24)}`);
    const stale = (record.missedRefreshes || 0) > 0;
    details.push(
      `MMSI ${record.mmsi || '--'} · ${formatPositionTime(record)}${stale ? ' · STALE' : ''}`,
    );

    let accent = accentForVesselType(record.type);
    const threat = record?.mmsi ? aegisThreatService.getThreatForMmsi(record.mmsi) : null;
    if (record?.mmsi && !threat) {
      aegisThreatService.fetchThreatForVessel(record);
    }
    if (threat && threat.threat_level) {
      const score = Number(threat.threat_score || 0).toFixed(1);
      if (threat.threat_level === 'CRITICAL') {
        accent = '#ef4444';
        details.unshift(`🚨 AEGIS: CRITICAL (Score ${score}/100)`);
      } else if (threat.threat_level === 'HIGH') {
        accent = '#f97316';
        details.unshift(`⚠️ AEGIS: HIGH (Score ${score}/100)`);
      } else if (threat.threat_level === 'ADVISORY') {
        accent = '#eab308';
        details.unshift(`⚠️ AEGIS: ADVISORY (Score ${score}/100)`);
      } else {
        if (threat.closest_cable && (threat.closest_cable.in_cpz || threat.closest_cable.in_alert_corridor || threat.closest_cable.distance_nm <= 9.0)) {
          accent = '#06b6d4';
          details.unshift(`🛡️ AEGIS: NORMAL (Score ${score}/100)`);
        } else {
          details.unshift(`🛡️ AEGIS: CLEAR (Score ${score}/100)`);
        }
      }

      if (threat.closest_cable && (threat.closest_cable.distance_nm <= 9.0 || threat.closest_cable.in_alert_corridor)) {
        const cpzBadge = threat.closest_cable.in_cpz ? ' · Inside CPZ' : '';
        details.push(`🛡️ Cable: ${threat.closest_cable.cable_name} (${Number(threat.closest_cable.distance_nm || 0).toFixed(1)} NM${cpzBadge})`);
      } else if (threat.threat_level === 'NORMAL') {
        details.push('🛡️ Subsea Corridors: Clear (>9 NM)');
      }

      if (threat.recommended_action && threat.recommended_action !== 'NONE') {
        details.push(`⚡ Action: ${threat.recommended_action}`);
      } else if (threat.threat_level === 'NORMAL' && threat.closest_cable && threat.closest_cable.in_cpz) {
        details.push(`Transit: Normal Speed (${Number(record.speed || 0).toFixed(1)} kn)`);
      }
    }

    return {
      id: vesselOverlayEntryId(record),
      actionable: Boolean(record?.mmsi),
      position:
        components.rendering.getVisual(record).billboard?.position ||
        components.rendering.getVisual(record).position,
      gapPx: 12,
      accent,
      title: trimHudValue(displayVesselName(record), 32),
      details,
      selected: true,
      priority: 100000,
    };
  }

  /** Stable overlay identity for MMSI-keyed and source-retained unkeyed rows. */

  function vesselOverlayEntryId(record) {
    const mmsi = String(record?.mmsi || '').trim();
    if (mmsi) return `vessel:${mmsi}`;
    const name = String(record?.name || 'VESSEL').trim() || 'VESSEL';
    const lat = Number.isFinite(record?.lat) ? record.lat.toFixed(5) : 'x';
    const lon = Number.isFinite(record?.lon) ? record.lon.toFixed(5) : 'x';
    return `vessel:unkeyed:${name}:${lat}:${lon}`;
  }

  /** Uppercased, card-width-bounded AIS type (empty string when unknown). */

  function vesselTypeShort(record) {
    return normalizeVesselType(record.type).toUpperCase().slice(0, 14);
  }

  /**
   * True when `screen` is at least `minSepPx` away from every accepted screen
   * position (greedy card-declutter accept test, mirroring the FIRMS pass).
   * Exported for unit tests.
   * @param {Array<{x: number, y: number}>} accepted - Accepted card positions.
   * @param {{x: number, y: number}} screen - Candidate window coordinates.
   * @param {number} minSepPx - Minimum separation in pixels.
   * @returns {boolean}
   */

  function cardScreenSeparated(accepted, screen, minSepPx) {
    const minSq = minSepPx * minSepPx;
    for (let i = 0; i < accepted.length; i += 1) {
      const dx = screen.x - accepted[i].x;
      const dy = screen.y - accepted[i].y;
      if (dx * dx + dy * dy < minSq) return false;
    }
    return true;
  }

  function displayVesselName(record) {
    const name = String(record.name || '').trim();
    if (name && name !== 'VESSEL' && name !== record.mmsi) return name;
    return record.mmsi ? `MMSI ${record.mmsi}` : 'VESSEL';
  }

  function formatSpeed(speed) {
    return speed === null ? '--KT' : `${speed.toFixed(1)}KT`;
  }

  function formatHeading(heading) {
    return Number.isFinite(heading) ? `${Math.round(heading)}DEG` : '--DEG';
  }

  function formatPositionTime(record) {
    if (!record.lastPositionUtc) return 'POS: LIVE';
    const date = new Date(record.lastPositionUtc);
    if (Number.isNaN(date.getTime())) return 'POS: LIVE';
    return `POS: ${date.toISOString().slice(11, 19)}Z`;
  }
  if (typeof aegisThreatService?.subscribe === 'function') {
    aegisThreatService.subscribe(() => {
      const selected = state.selectedRecord;
      if (selected) {
        updateSelectedVesselHud(selected);
        components.rendering?.updateVisibility?.(true);
      }
    });
  }

  return {
    updateSelectedVesselHud,
    resetSelectedVesselHud,
    trimHudValue,
    buildVesselCard,
    buildSelectedVesselCard,
    vesselOverlayEntryId,
    vesselTypeShort,
    cardScreenSeparated,
    displayVesselName,
    formatSpeed,
    formatHeading,
    formatPositionTime,
  };
}
