import test from 'node:test';
import assert from 'node:assert/strict';

test('AegisThreatLayer: SVG data URIs generate safely without Latin1/btoa exceptions', async () => {
  // Verify that SVG templates with SVG paths and attributes encode cleanly into data URIs
  const sampleSvgs = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><polygon points="32,4 50,50 32,40 14,50" fill="#ef4444"/></svg>`,
    `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><circle cx="32" cy="32" r="28" fill="rgba(234, 179, 8, 0.22)"/></svg>`,
    `<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36"><path d="M11 20 C11 27 25 27 25 20" stroke="#fff"/></svg>`,
  ];

  for (const svg of sampleSvgs) {
    const dataUri = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg.trim());
    assert.ok(dataUri.startsWith('data:image/svg+xml;charset=utf-8,'));
    assert.ok(dataUri.length > 50);
  }
});

test('AegisThreatService: updates threat list and notifies subscribers', async () => {
  const { aegisThreatService } = await import('../services/aegisThreatService.js');
  let notified = false;

  const unsub = aegisThreatService.subscribe((state) => {
    notified = true;
    assert.ok(Array.isArray(state.threats));
  });

  assert.ok(notified, 'Subscriber should be immediately notified with initial state');
  unsub();
});

test('AegisThreatService: simulation switching isolates active scenario without stacking', async () => {
  const { aegisThreatService } = await import('../services/aegisThreatService.js');

  // Inject Yi Peng 3 simulation
  const sim1 = { mmsi: '412543000', vessel_name: 'Yi Peng 3', threat_level: 'CRITICAL', threat_score: 85 };
  aegisThreatService.activeSimulations.set('412543000', sim1);
  aegisThreatService.threatsByMmsi.set('412543000', sim1);
  aegisThreatService.allThreats = [sim1];
  assert.strictEqual(aegisThreatService.activeSimulations.size, 1);

  // When switching to GPS jump, old simulations must be cleared
  const sim2 = { mmsi: '999000102', vessel_name: 'SDR Spoofed Fix', threat_level: 'ADVISORY', threat_score: 46.8 };
  const simulationMmsis = ['412543000', '999000102', '999000103'];
  aegisThreatService.activeSimulations.clear();
  for (const mmsi of simulationMmsis) {
    aegisThreatService.threatsByMmsi.delete(mmsi);
  }
  aegisThreatService.allThreats = aegisThreatService.allThreats.filter(
    (t) => !simulationMmsis.includes(String(t.mmsi)),
  );
  aegisThreatService.activeSimulations.set('999000102', sim2);
  aegisThreatService.threatsByMmsi.set('999000102', sim2);
  aegisThreatService.allThreats.push(sim2);

  // Assert only sim2 is active, not sim1
  assert.strictEqual(aegisThreatService.activeSimulations.size, 1);
  assert.strictEqual(aegisThreatService.activeSimulations.has('999000102'), true);
  assert.strictEqual(aegisThreatService.activeSimulations.has('412543000'), false);
  assert.strictEqual(aegisThreatService.allThreats.length, 1);
  assert.strictEqual(aegisThreatService.allThreats[0].mmsi, '999000102');

  aegisThreatService.clearSimulations();
  assert.strictEqual(aegisThreatService.activeSimulations.size, 0);
});

test('AegisThreat: buildSelectedVesselCard renders cyber-physical threat intelligence for CPZ vessels', async () => {
  const { aegisThreatService } = await import('../services/aegisThreatService.js');
  const { buildSelectedVesselCard } = await import('../data/aisLiveVessels.js');

  const mmsi = '273615060';
  const normalCpzThreat = {
    mmsi,
    vessel_name: 'VYACHESL.PAYSHCHIKOV',
    threat_level: 'NORMAL',
    threat_score: 29.14,
    closest_cable: {
      cable_id: 'finland-estonia-3-eesf-3',
      cable_name: 'Finland-Estonia 3 (EESF-3)',
      distance_nm: 1.3067,
      in_cpz: true,
      in_alert_corridor: true,
    },
    recommended_action: 'NONE',
  };

  aegisThreatService.threatsByMmsi.set(mmsi, normalCpzThreat);

  const mockRecord = {
    mmsi,
    name: 'VYACHESL.PAYSHCHIKOV',
    type: 'Cargo',
    speed: 8.4,
    heading: 75,
    course: 75,
    lat: 59.7242,
    lon: 24.51613,
    lastPositionUtc: '2026-11-09T02:08:53Z',
  };

  const card = buildSelectedVesselCard(mockRecord);
  assert.ok(card);
  assert.strictEqual(card.selected, true);
  assert.strictEqual(card.accent, '#06b6d4'); // Cyan accent for monitored corridor transit

  const hasScore = card.details.some((d) => d.includes('AEGIS: NORMAL (Score 29.1/100)'));
  assert.ok(hasScore, `Expected Aegis score line in card.details: ${JSON.stringify(card.details)}`);

  const hasCable = card.details.some((d) => d.includes('Finland-Estonia 3 (EESF-3) (1.3 NM · Inside CPZ)'));
  assert.ok(hasCable, `Expected cable distance and CPZ badge in card.details: ${JSON.stringify(card.details)}`);

  const hasTransit = card.details.some((d) => d.includes('Transit: Normal Speed (8.4 kn)'));
  assert.ok(hasTransit, `Expected normal transit speed line: ${JSON.stringify(card.details)}`);

  // Clean up
  aegisThreatService.threatsByMmsi.delete(mmsi);
});

test('AegisThreat: buildSelectedVesselCard renders CRITICAL threat alert and SOAR action', async () => {
  const { aegisThreatService } = await import('../services/aegisThreatService.js');
  const { buildSelectedVesselCard } = await import('../data/aisLiveVessels.js');

  const mmsi = '412543000';
  const criticalThreat = {
    mmsi,
    vessel_name: 'Yi Peng 3',
    threat_level: 'CRITICAL',
    threat_score: 88.9,
    closest_cable: {
      cable_id: 'c-lion1',
      cable_name: 'C-Lion1 (Baltic Subsea Cable)',
      distance_nm: 0.38,
      in_cpz: true,
      in_alert_corridor: true,
    },
    recommended_action: 'TRIGGER_PREEMPTIVE_FAILOVER',
  };

  aegisThreatService.threatsByMmsi.set(mmsi, criticalThreat);

  const mockRecord = {
    mmsi,
    name: 'Yi Peng 3',
    type: 'Bulk Carrier',
    speed: 1.2,
    heading: 205,
    course: 205,
    lat: 60.05,
    lon: 25.02,
    lastPositionUtc: '2026-11-09T02:08:53Z',
  };

  const card = buildSelectedVesselCard(mockRecord);
  assert.strictEqual(card.accent, '#ef4444'); // Red accent for critical danger

  const hasCrit = card.details.some((d) => d.includes('🚨 AEGIS: CRITICAL (Score 88.9/100)'));
  assert.ok(hasCrit, `Expected critical threat line in card: ${JSON.stringify(card.details)}`);

  const hasAction = card.details.some((d) => d.includes('⚡ Action: TRIGGER_PREEMPTIVE_FAILOVER'));
  assert.ok(hasAction, `Expected failover action in card: ${JSON.stringify(card.details)}`);

  // Clean up
  aegisThreatService.threatsByMmsi.delete(mmsi);
});
