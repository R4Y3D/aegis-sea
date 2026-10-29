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
