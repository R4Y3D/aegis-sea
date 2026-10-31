/**
 * Aegis-Sea Tactical Subsea Defense UI Controller.
 * Manages the floating tactical HUD dock, real-time threat metrics,
 * active threat drawer, and simulation attack injection buttons.
 */

import { aegisThreatService } from '../services/aegisThreatService.js';

export function initAegisThreatPanel({ onFlyToThreat, aegisLayer } = {}) {
  // Elements in floating HUD dock
  const hudDock = document.getElementById('aegis-hud-dock');
  const enginePill = document.getElementById('aegis-engine-pill');
  const countCrit = document.getElementById('aegis-count-crit');
  const countHigh = document.getElementById('aegis-count-high');
  const countAdv = document.getElementById('aegis-count-adv');

  const hudBtnAnchor = document.getElementById('aegis-sim-btn-anchor');
  const hudBtnJump = document.getElementById('aegis-sim-btn-jump');
  const hudBtnGhost = document.getElementById('aegis-sim-btn-ghost');
  const hudToggleBtn = document.getElementById('aegis-hud-toggle-btn');
  const hudDrawer = document.getElementById('aegis-hud-drawer');
  const hudDrawerList = document.getElementById('aegis-drawer-list');
  const toggleIcon = document.getElementById('aegis-toggle-icon');

  // Simulation Controller Bar elements
  const hudSimPlayBtn = document.getElementById('aegis-sim-play-btn');
  const hudSimReplayBtn = document.getElementById('aegis-sim-replay-btn');
  const hudSimProgress = document.getElementById('aegis-sim-progress');

  // Elements in sidebar panel (if present)
  const engineBadge = document.getElementById('aegis-engine-badge');
  const critCountEl = document.getElementById('aegis-crit-count');
  const highCountEl = document.getElementById('aegis-high-count');
  const advCountEl = document.getElementById('aegis-adv-count');
  const normCountEl = document.getElementById('aegis-norm-count');
  const threatListEl = document.getElementById('aegis-threat-list');

  const btnAnchor = document.getElementById('aegis-btn-sim-anchor');
  const btnJump = document.getElementById('aegis-btn-sim-jump');
  const btnGhost = document.getElementById('aegis-btn-sim-ghost');

  // Drawer toggle logic
  let isDrawerOpen = false;
  if (hudToggleBtn && hudDrawer) {
    hudToggleBtn.addEventListener('click', () => {
      isDrawerOpen = !isDrawerOpen;
      hudDrawer.hidden = !isDrawerOpen;
      if (toggleIcon) toggleIcon.textContent = isDrawerOpen ? '▲' : '▼';
    });
  }

  function renderThreatCards(threats, targetContainer) {
    if (!targetContainer) return;

    const elevated = threats.filter(
      (t) => t.threat_level && t.threat_level !== 'NORMAL',
    );

    if (elevated.length === 0) {
      targetContainer.innerHTML =
        '<div class="aegis-empty-state aegis-drawer-empty">All 712 subsea cable corridors secure. Click an attack simulation button above to test real-time threat detection and BGP failover.</div>';
      return;
    }

    targetContainer.innerHTML = elevated
      .map((t) => {
        const levelClass = (t.threat_level || 'NORMAL').toLowerCase();
        const score = Number(t.threat_score || 0).toFixed(1);
        const cableName = t.closest_cable?.cable_name || 'Subsea Cable';
        const dist = Number(t.closest_cable?.distance_nm || 0).toFixed(1);
        const trustJump = t.telemetry_trust?.is_jump;
        const trustGhost = t.telemetry_trust?.is_ghost_candidate;

        let badgeText = `${t.threat_level} (${score}/100)`;
        if (trustJump) badgeText += ' · SPOOFED JUMP';
        if (trustGhost) badgeText += ' · GHOST DECOY';

        return `
          <div class="aegis-threat-card ${levelClass}" data-mmsi="${t.mmsi}" role="button" tabindex="0" title="Click to track vessel on 3D globe">
            <div class="aegis-card-top">
              <span class="aegis-card-name">${escapeHtml(t.vessel_name || `MMSI ${t.mmsi}`)}</span>
              <span class="aegis-card-badge ${levelClass}">${badgeText}</span>
            </div>
            <div class="aegis-card-meta">
              <span><b>Target:</b> ${escapeHtml(cableName)} (${dist} NM)</span>
              <span><b>Speed:</b> ${Number(t.sog_knots || 0).toFixed(1)} kn</span>
            </div>
            <div class="aegis-card-action">
              <span><b>Action:</b> ${escapeHtml(t.recommended_action || 'NONE')}</span>
            </div>
          </div>
        `;
      })
      .join('');

    // Attach click listeners to fly to threat
    targetContainer.querySelectorAll('.aegis-threat-card').forEach((card) => {
      card.addEventListener('click', () => {
        const mmsi = card.dataset.mmsi;
        const targetThreat = threats.find((t) => String(t.mmsi) === mmsi);
        if (targetThreat && typeof onFlyToThreat === 'function') {
          onFlyToThreat(targetThreat);
        }
      });
    });
  }

  function updateOverview(overview, isOnline) {
    // Update floating HUD pill
    if (enginePill) {
      if (isOnline) {
        enginePill.textContent = '● ONLINE';
        enginePill.className = 'aegis-pill online';
      } else {
        enginePill.textContent = '○ STANDBY';
        enginePill.className = 'aegis-pill offline';
      }
    }

    if (countCrit) countCrit.textContent = overview.threats_critical_count ?? 0;
    if (countHigh) countHigh.textContent = overview.threats_high_count ?? 0;
    if (countAdv) countAdv.textContent = overview.threats_advisory_count ?? 0;

    // Update sidebar (if present)
    if (engineBadge) {
      if (isOnline) {
        engineBadge.textContent = '● ENGINE ONLINE';
        engineBadge.className = 'aegis-badge online';
      } else {
        engineBadge.textContent = '○ STANDBY';
        engineBadge.className = 'aegis-badge offline';
      }
    }

    if (critCountEl) critCountEl.textContent = overview.threats_critical_count ?? 0;
    if (highCountEl) highCountEl.textContent = overview.threats_high_count ?? 0;
    if (advCountEl) advCountEl.textContent = overview.threats_advisory_count ?? 0;
    if (normCountEl) normCountEl.textContent = overview.threats_normal_count ?? 0;
  }

  // Predefined scenario responses (fallback when Python backend is in standby)
  const fallbackScenarios = {
    anchor_drag: {
      event_id: 'aegis-sim-412543000',
      mmsi: '412543000',
      vessel_name: 'Yi Peng 3 (Anchor Dragging Sabotage)',
      coordinates: { lat: 60.05, lon: 25.02 },
      sog_knots: 1.2,
      cog_degrees: 205.0,
      threat_score: 80.9,
      threat_level: 'CRITICAL',
      closest_cable: {
        cable_id: 'c-lion1',
        cable_name: 'C-Lion1 (Baltic Subsea Cable)',
        distance_nm: 0.4,
        in_cpz: true,
        in_alert_corridor: true,
      },
      telemetry_trust: {
        is_valid: true,
        is_jump: false,
        is_ghost_candidate: false,
        trust_score: 1.0,
      },
      recommended_action: 'TRIGGER_PREEMPTIVE_FAILOVER',
    },
    gps_jump: {
      event_id: 'aegis-sim-999000102',
      mmsi: '999000102',
      vessel_name: 'SDR Spoofed Fix (Kinematic Jump)',
      coordinates: { lat: 60.0333, lon: 25.0 },
      sog_knots: 1.0,
      cog_degrees: 90.0,
      threat_score: 46.8,
      threat_level: 'ADVISORY',
      closest_cable: {
        cable_id: 'c-lion1',
        cable_name: 'C-Lion1 (Baltic Subsea Cable)',
        distance_nm: 0.8,
        in_cpz: true,
        in_alert_corridor: true,
      },
      telemetry_trust: {
        is_valid: true,
        is_jump: true,
        implied_speed_knots: 239.8,
        is_ghost_candidate: false,
        trust_score: 0.3,
      },
      recommended_action: 'INCREASE_MONITORING_FREQUENCY',
    },
    ghost_decoy: {
      event_id: 'aegis-sim-999000103',
      mmsi: '999000103',
      vessel_name: 'Phantom Ghost Decoy (Failover DoS)',
      coordinates: { lat: 60.05, lon: 25.02 },
      sog_knots: 1.5,
      cog_degrees: 0.0,
      threat_score: 58.0,
      threat_level: 'ADVISORY',
      closest_cable: {
        cable_id: 'c-lion1',
        cable_name: 'C-Lion1 (Baltic Subsea Cable)',
        distance_nm: 0.4,
        in_cpz: true,
        in_alert_corridor: true,
      },
      telemetry_trust: {
        is_valid: true,
        is_jump: false,
        is_ghost_candidate: true,
        trust_score: 0.5,
      },
      recommended_action: 'VERIFY_GHOST_TARGET_BEFORE_FAILOVER',
    },
  };

  // Trigger attack simulation
  async function triggerSimulation(type) {
    let assessment = await aegisThreatService.simulateScenario(type);

    // Fallback if backend offline
    if (!assessment && fallbackScenarios[type]) {
      assessment = fallbackScenarios[type];
      aegisThreatService.activeSimulations.set(String(assessment.mmsi), assessment);
      aegisThreatService.threatsByMmsi.set(String(assessment.mmsi), assessment);
      aegisThreatService.allThreats = [
        assessment,
        ...aegisThreatService.allThreats.filter((t) => t.mmsi !== assessment.mmsi),
      ];
      aegisThreatService.overview.threats_critical_count = aegisThreatService.allThreats.filter(
        (t) => t.threat_level === 'CRITICAL',
      ).length;
      aegisThreatService.overview.threats_high_count = aegisThreatService.allThreats.filter(
        (t) => t.threat_level === 'HIGH',
      ).length;
      aegisThreatService.overview.threats_advisory_count = aegisThreatService.allThreats.filter(
        (t) => t.threat_level === 'ADVISORY',
      ).length;
      aegisThreatService._notify();
    }

    // Automatically reveal drawer and fly camera to target
    if (assessment) {
      if (hudDrawer) {
        hudDrawer.hidden = false;
        isDrawerOpen = true;
        if (toggleIcon) toggleIcon.textContent = '▲';
      }
      if (typeof onFlyToThreat === 'function') {
        onFlyToThreat(assessment);
      }
    }
  }

  // Bind HUD buttons
  hudBtnAnchor?.addEventListener('click', () => triggerSimulation('anchor_drag'));
  hudBtnJump?.addEventListener('click', () => triggerSimulation('gps_jump'));
  hudBtnGhost?.addEventListener('click', () => triggerSimulation('ghost_decoy'));

  // Bind Simulation Controller bar
  hudSimPlayBtn?.addEventListener('click', () => {
    if (aegisLayer && typeof aegisLayer.togglePlay === 'function') {
      const isPlaying = aegisLayer.togglePlay();
      hudSimPlayBtn.textContent = isPlaying ? '⏸' : '▶';
    }
  });

  hudSimReplayBtn?.addEventListener('click', () => {
    if (aegisLayer && typeof aegisLayer.replay === 'function') {
      aegisLayer.replay();
    }
  });

  hudSimProgress?.addEventListener('input', (e) => {
    if (aegisLayer && typeof aegisLayer.setSimulationTime === 'function') {
      const ratio = Number(e.target.value) / 100.0;
      aegisLayer.setSimulationTime(ratio * 24.0);
    }
  });

  // Bind sidebar buttons
  btnAnchor?.addEventListener('click', () => triggerSimulation('anchor_drag'));
  btnJump?.addEventListener('click', () => triggerSimulation('gps_jump'));
  btnGhost?.addEventListener('click', () => triggerSimulation('ghost_decoy'));

  // Subscribe to service updates
  const unsubscribe = aegisThreatService.subscribe((state) => {
    updateOverview(state.overview, state.isEngineOnline);
    renderThreatCards(state.threats, hudDrawerList);
    renderThreatCards(state.threats, threatListEl);
  });

  // Start polling
  aegisThreatService.startPolling(15000);

  return {
    destroy() {
      unsubscribe();
      aegisThreatService.stopPolling();
    },
  };
}

function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
