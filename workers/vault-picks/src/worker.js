/**
 * Vault Picks Worker — Cloudflare Worker for persisting picker selections and verdicts.
 *
 * GET  /picks/{session-id}     → returns picks.json from R2
 * PUT  /picks/{session-id}     → saves picks.json to R2
 * GET  /verdicts/{session-id}  → returns verdicts.json from R2
 * PUT  /verdicts/{session-id}  → saves verdicts.json to R2
 *
 * Auth: Bearer token in Authorization header (matches AUTH_TOKEN env var).
 * CORS: Allows requests from salus-mind.com and media.salus-mind.com.
 */

export default {
  async fetch(request, env) {
    // CORS headers
    const origin = request.headers.get('Origin') || '';
    const allowedOrigins = [
      'https://salus-mind.com',
      'https://www.salus-mind.com',
      'https://media.salus-mind.com',
      'http://localhost',
      'null', // file:// origin
    ];
    const corsOrigin = allowedOrigins.includes(origin) ? origin : allowedOrigins[0];

    const corsHeaders = {
      'Access-Control-Allow-Origin': corsOrigin,
      'Access-Control-Allow-Methods': 'GET, PUT, OPTIONS',
      'Access-Control-Allow-Headers': 'Authorization, Content-Type',
      'Access-Control-Max-Age': '86400',
    };

    // Handle preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    // Parse path: /picks/{session-id} or /verdicts/{session-id}
    const url = new URL(request.url);
    const picksMatch = url.pathname.match(/^\/picks\/([a-zA-Z0-9_-]+)$/);
    const verdictsMatch = url.pathname.match(/^\/verdicts\/([a-zA-Z0-9_-]+)$/);
    const match = picksMatch || verdictsMatch;
    if (!match) {
      return new Response(JSON.stringify({ error: 'Invalid path. Use /picks/{session-id} or /verdicts/{session-id}' }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const sessionId = match[1];
    const isVerdicts = !!verdictsMatch;
    const r2Key = isVerdicts
      ? `vault/${sessionId}/verdicts/verdicts.json`
      : `vault/${sessionId}/picks/picks.json`;

    // Auth check
    const authHeader = request.headers.get('Authorization') || '';
    const token = authHeader.replace('Bearer ', '');
    if (token !== env.AUTH_TOKEN) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    if (request.method === 'GET') {
      // Fetch picks from R2
      const object = await env.VAULT_BUCKET.get(r2Key);
      if (!object) {
        return new Response(JSON.stringify({ picks: [], session: sessionId }), {
          status: 200,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
      const data = await object.text();
      return new Response(data, {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    if (request.method === 'PUT') {
      // Save picks to R2
      const body = await request.text();

      // Validate JSON
      try {
        JSON.parse(body);
      } catch {
        return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }

      await env.VAULT_BUCKET.put(r2Key, body, {
        httpMetadata: { contentType: 'application/json' },
      });

      return new Response(JSON.stringify({ ok: true, key: r2Key }), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  },
};
