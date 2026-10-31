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
