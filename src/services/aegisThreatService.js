/**
 * Aegis-Sea Threat Intelligence Client Service.
 * Periodically polls the /api/threats endpoint and maintains real-time threat state.
 */

class AegisThreatService {
  constructor() {
    this.threatsByMmsi = new Map();
    this.allThreats = [];
    this.overview = {
      monitored_vessels_total: 0,
      corridor_vessels_total: 0,
      threats_critical_count: 0,
      threats_high_count: 0,
      threats_advisory_count: 0,
      threats_normal_count: 0,
      threats: [],
    };
    this.activeSimulations = new Map();
    this.isEngineOnline = false;
    this.lastUpdated = null;
    this._pollTimer = null;
    this._listeners = new Set();
    this._pollIntervalMs = 15000;
  }

  /** Starts periodic polling loop. */
  startPolling(intervalMs = 15000) {
    this._pollIntervalMs = intervalMs;
    this.fetchThreats();
    if (!this._pollTimer) {
      this._pollTimer = setInterval(() => this.fetchThreats(), this._pollIntervalMs);
    }
  }

  /** Stops periodic polling. */
  stopPolling() {
    if (this._pollTimer) {
      clearInterval(this._pollTimer);
      this._pollTimer = null;
    }
  }

  /** Subscribes a listener callback to threat state changes. */
  subscribe(callback) {
    this._listeners.add(callback);
    // Immediately invoke with current state snapshot
    try {
      callback({
        overview: this.overview,
        threats: this.allThreats,
        threatsByMmsi: this.threatsByMmsi,
        isEngineOnline: this.isEngineOnline,
        lastUpdated: this.lastUpdated,
      });
    } catch (err) {
      console.error('[AegisThreatService] Listener error:', err);
    }
    return () => this._listeners.delete(callback);
  }

  _notify() {
    for (const listener of this._listeners) {
      try {
        listener({
          overview: this.overview,
          threats: this.allThreats,
          threatsByMmsi: this.threatsByMmsi,
          isEngineOnline: this.isEngineOnline,
          lastUpdated: this.lastUpdated,
        });
      } catch (err) {
        console.error('[AegisThreatService] Listener error:', err);
      }
    }
  }

  /** Queries /api/threats/overview and /api/threats from the backend. */
  async fetchThreats() {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);

      const resp = await fetch('/api/threats/overview', {
        signal: controller.signal,
        headers: { Accept: 'application/json' },
      });
      clearTimeout(timeoutId);

      if (!resp.ok) {
        this.isEngineOnline = false;
        this._notify();
        return;
      }

      const overviewData = await resp.json();
      this.isEngineOnline = overviewData.status !== 'engine_offline';
      this.overview = overviewData;

      const newMap = new Map();
      const threatList = Array.isArray(overviewData.threats) ? overviewData.threats : [];
      for (const t of threatList) {
        if (t.mmsi) {
          newMap.set(String(t.mmsi), t);
        }
      }

      // Retain active adversarial simulations across background polls
      for (const [simMmsi, simThreat] of this.activeSimulations.entries()) {
        newMap.set(simMmsi, simThreat);
      }

      const combinedThreats = Array.from(newMap.values());
      combinedThreats.sort((a, b) => (b.threat_score || 0) - (a.threat_score || 0));

      this.threatsByMmsi = newMap;
      this.allThreats = combinedThreats;
      this.lastUpdated = Date.now();
      this._notify();
    } catch (err) {
      this.isEngineOnline = false;
      this._notify();
    }
  }

  /** Retrieves threat assessment for a specific vessel MMSI. */
  getThreatForMmsi(mmsi) {
    if (!mmsi) return null;
    return this.threatsByMmsi.get(String(mmsi)) || null;
  }

  /** Injects an adversarial attack scenario on-demand via /api/evaluate. */
  async simulateScenario(scenarioType) {
    const scenarios = {
      anchor_drag: {
        mmsi: '412543000',
        name: 'Yi Peng 3 (Simulated)',
        lat: 60.05,
        lon: 25.02,
        sog: 1.2,
        cog: 205.0,
        heading: 205.0,
        ship_type: 'Bulk Carrier',
        imo: '9224984',
      },
      gps_jump: {
        mmsi: '999000102',
        name: 'SDR Spoofed Fix',
        lat: 60.0333,
        lon: 25.0,
        sog: 1.0,
        cog: 90.0,
        ship_type: 'Cargo',
      },
      ghost_decoy: {
        mmsi: '999000103',
        name: 'Phantom Ghost Contact',
        lat: 60.05,
        lon: 25.02,
        sog: 1.5,
        cog: 0.0,
        ship_type: 'Unspecified',
      },
    };

    const payload = scenarios[scenarioType];
    if (!payload) return null;

    try {
      const resp = await fetch('/api/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (resp.ok) {
        const assessment = await resp.json();
        // Pin in active simulations map so background polls never wipe it
        this.activeSimulations.set(String(assessment.mmsi), assessment);
        this.threatsByMmsi.set(String(assessment.mmsi), assessment);
        this.allThreats = [
          assessment,
          ...this.allThreats.filter((t) => t.mmsi !== assessment.mmsi),
        ];
        this.allThreats.sort((a, b) => b.threat_score - a.threat_score);
        this._notify();
        return assessment;
      }
    } catch (err) {
      console.error('[AegisThreatService] Failed to simulate scenario:', err);
    }
    return null;
  }

  /** Clears active simulated threat scenarios. */
  clearSimulations() {
    this.activeSimulations.clear();
    this.fetchThreats();
  }
}

export const aegisThreatService = new AegisThreatService();
