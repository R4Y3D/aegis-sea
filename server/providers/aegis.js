/**
 * Aegis-Sea Threat Intelligence Reverse Proxy.
 * Proxies `/api/threats` requests from the Node.js / Vite server to the
 * Aegis-Sea Python Threat Engine running on port 8400.
 */

const DEFAULT_AEGIS_URL = 'http://127.0.0.1:8400';

export function aegisProxy() {
  const targetBase = (process.env.AEGIS_ENGINE_URL || DEFAULT_AEGIS_URL).replace(/\/+$/, '');

  async function handler(req, res) {
    const json = (status, payload) => {
      res.writeHead(status, {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store',
      });
      res.end(JSON.stringify(payload));
    };

    const incomingUrl = req.url || '';
    const targetUrl = `${targetBase}/api/threats${incomingUrl}`;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      // Collect request body if POST / PUT
      let body = undefined;
      if (['POST', 'PUT', 'PATCH'].includes(req.method)) {
        const chunks = [];
        for await (const chunk of req) {
          chunks.push(chunk);
        }
        body = Buffer.concat(chunks);
      }

      const response = await fetch(targetUrl, {
        method: req.method,
        headers: {
          'Content-Type': req.headers['content-type'] || 'application/json',
          Accept: 'application/json',
        },
        body,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      const data = await response.text();
      res.writeHead(response.status, {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store',
      });
      res.end(data);
    } catch (err) {
      json(503, {
        service: 'aegis-sea',
        status: 'engine_offline',
        error: 'Aegis-Sea Python engine unreachable on port 8400. Ensure aegis-engine service is running.',
        threats: [],
      });
    }
  }

  return {
    name: 'aegis-threats-proxy',
    configureServer({ middlewares }) {
      middlewares.use('/api/threats', handler);
    },
    configurePreviewServer({ middlewares }) {
      middlewares.use('/api/threats', handler);
    },
  };
}
