/**
 * Email Command Worker — receives inbound emails via Resend webhook,
 * stores instructions in R2, and serves them to the local daemon.
 *
 * POST /inbound              — Resend webhook (email.received event)
 * GET  /instructions         — returns oldest pending instruction
 * PUT  /instructions/{id}/status — mark instruction as processing/completed/failed
 *
 * Auth: POST /inbound uses Svix signature verification.
 *       GET/PUT use Bearer token (matches AUTH_TOKEN env var).
 */

const R2_PREFIX = 'email-cmd/instructions/';

// --- Svix signature verification ---

async function verifyWebhook(request, secret) {
  const msgId = request.headers.get('svix-id');
  const msgTimestamp = request.headers.get('svix-timestamp');
  const msgSignature = request.headers.get('svix-signature');

  if (!msgId || !msgTimestamp || !msgSignature) return false;

  // Reject timestamps older than 5 minutes
  const now = Math.floor(Date.now() / 1000);
  if (Math.abs(now - parseInt(msgTimestamp)) > 300) return false;

  const body = await request.clone().text();
  const toSign = `${msgId}.${msgTimestamp}.${body}`;

  // Secret comes as "whsec_<base64>" — strip prefix
  const secretBytes = Uint8Array.from(
    atob(secret.replace('whsec_', '')),
    c => c.charCodeAt(0)
  );

  const key = await crypto.subtle.importKey(
    'raw', secretBytes, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(toSign));
  const computed = btoa(String.fromCharCode(...new Uint8Array(sig)));

  // msgSignature can contain multiple sigs: "v1,<base64> v1,<base64>"
  const signatures = msgSignature.split(' ');
  for (const s of signatures) {
    const [, val] = s.split(',');
    if (val === computed) return true;
  }
  return false;
}

// --- Helpers ---

function jsonResponse(data, status, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...extraHeaders },
  });
}

function stripQuotedReply(text) {
  // Remove common quoted-reply patterns
  const lines = text.split('\n');
  const cleaned = [];
  for (const line of lines) {
    // Stop at "On ... wrote:" or "> " quoted lines
    if (/^On .+ wrote:$/.test(line.trim())) break;
    if (/^>/.test(line.trim())) break;
    // Stop at "From:" header block
    if (/^From:/.test(line.trim())) break;
    // Stop at horizontal rule separators
    if (/^[-_]{3,}$/.test(line.trim())) break;
    // Stop at mobile signatures
    if (/^Sent from (Outlook|my iPhone|Mail)/i.test(line.trim())) break;
    cleaned.push(line);
  }
  return cleaned.join('\n').trim();
}

// --- Route handlers ---

async function handleInbound(request, env) {
  // Verify Svix signature
  if (env.WEBHOOK_SECRET) {
    const valid = await verifyWebhook(request, env.WEBHOOK_SECRET);
    if (!valid) return jsonResponse({ error: 'Invalid signature' }, 401);
  }

  const payload = await request.json();

  // Resend webhook sends metadata only — need to fetch full email via API
  const data = payload.data || payload;
  const emailId = data.email_id || data.id || '';
  const from = data.from || '';
  const subject = data.subject || '(no subject)';

  // Validate sender
  if (!from.toLowerCase().includes(env.ALLOWED_SENDER.toLowerCase())) {
    return jsonResponse({ ok: true }, 200);
  }

  // Fetch full email content from Resend API
  let text = '';
  if (emailId && env.RESEND_API_KEY) {
    try {
      const res = await fetch(`https://api.resend.com/emails/receiving/${emailId}`, {
        headers: { 'Authorization': `Bearer ${env.RESEND_API_KEY}` },
      });
      if (res.ok) {
        const full = await res.json();
        text = full.text || '';
      }
    } catch (e) {
      console.log('Failed to fetch email content:', e.message);
    }
  }

  // Fallback: use text/html from webhook payload if available
  if (!text) text = data.text || data.html || '';

  // Strip quoted reply text and email signatures
  const instruction = stripQuotedReply(text);
  if (!instruction) {
    return jsonResponse({ ok: true, note: 'empty instruction' }, 200);
  }

  // Store in R2
  const id = `${Date.now()}-${crypto.randomUUID().slice(0, 8)}`;
  const record = {
    id,
    from,
    subject,
    instruction,
    status: 'pending',
    created_at: new Date().toISOString(),
  };

  await env.BUCKET.put(
    `${R2_PREFIX}${id}.json`,
    JSON.stringify(record),
    { httpMetadata: { contentType: 'application/json' } }
  );

  return jsonResponse({ ok: true, id }, 200);
}

async function handleGetInstructions(request, env) {
  // List all instruction files, return oldest pending one
  const list = await env.BUCKET.list({ prefix: R2_PREFIX });

  let oldest = null;
  let oldestKey = null;

  for (const obj of list.objects) {
    const data = await env.BUCKET.get(obj.key);
    if (!data) continue;
    const record = JSON.parse(await data.text());
    if (record.status === 'pending') {
      if (!oldest || record.created_at < oldest.created_at) {
        oldest = record;
        oldestKey = obj.key;
      }
    }
  }

  if (!oldest) {
    return jsonResponse({ instruction: null }, 200);
  }

  return jsonResponse({ instruction: oldest }, 200);
}

async function handleUpdateStatus(request, env, id) {
  const body = await request.json();
  const newStatus = body.status; // processing, completed, failed
  if (!['processing', 'completed', 'failed'].includes(newStatus)) {
    return jsonResponse({ error: 'Invalid status' }, 400);
  }

  const key = `${R2_PREFIX}${id}.json`;
  const obj = await env.BUCKET.get(key);
  if (!obj) {
    return jsonResponse({ error: 'Not found' }, 404);
  }

  const record = JSON.parse(await obj.text());
  record.status = newStatus;
  record.updated_at = new Date().toISOString();

  // Add result if provided
  if (body.result) record.result = body.result;

  await env.BUCKET.put(key, JSON.stringify(record), {
    httpMetadata: { contentType: 'application/json' },
  });

  return jsonResponse({ ok: true, id, status: newStatus }, 200);
}

// --- Main ---

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const method = request.method;

    // POST /inbound — Resend webhook (no Bearer auth, uses Svix)
    if (method === 'POST' && url.pathname === '/inbound') {
      return handleInbound(request, env);
    }

    // All other routes require Bearer auth
    if (method === 'OPTIONS') {
      return new Response(null, { status: 204 });
    }

    const authHeader = request.headers.get('Authorization') || '';
    const token = authHeader.replace('Bearer ', '');
    if (token !== env.AUTH_TOKEN) {
      return jsonResponse({ error: 'Unauthorized' }, 401);
    }

    // GET /instructions
    if (method === 'GET' && url.pathname === '/instructions') {
      return handleGetInstructions(request, env);
    }

    // PUT /instructions/{id}/status
    const statusMatch = url.pathname.match(/^\/instructions\/([a-zA-Z0-9_-]+)\/status$/);
    if (method === 'PUT' && statusMatch) {
      return handleUpdateStatus(request, env, statusMatch[1]);
    }

    return jsonResponse({ error: 'Not found' }, 404);
  },
};
