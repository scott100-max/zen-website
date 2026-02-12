// ═══════════════════════════════════════════════════════════════════
// Salus Website — End-to-End Test Suite
// Runs against a local HTTP server serving the site files
// Uses Node.js built-in test runner (node:test) and fetch
// ═══════════════════════════════════════════════════════════════════

import { describe, it, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';

// ── Config ──────────────────────────────────────────────────────
const PORT = 8765;
const BASE = `http://127.0.0.1:${PORT}`;
const MEDIA_DOMAIN = 'https://media.salus-mind.com';
const SUPABASE_URL = 'https://egywowuyixfqytaucihf.supabase.co';

// ── Helpers ─────────────────────────────────────────────────────
async function get(path) {
  const url = `${BASE}/${path.replace(/^\//, '')}`;
  const res = await fetch(url, { signal: AbortSignal.timeout(10000) });
  return { status: res.status, html: await res.text(), headers: res.headers };
}

async function head(path) {
  const url = path.startsWith('http') ? path : `${BASE}/${path.replace(/^\//, '')}`;
  const res = await fetch(url, { method: 'HEAD', signal: AbortSignal.timeout(10000) });
  return { status: res.status, ok: res.ok, headers: res.headers };
}

function has(html, text) { return html.includes(text); }

function dataSrcs(html) {
  const r = /data-src="([^"]+)"/g;
  const a = []; let m;
  while ((m = r.exec(html))) a.push(m[1]);
  return [...new Set(a)];
}

// ── Server lifecycle ────────────────────────────────────────────
let server;

before(async () => {
  // Check if already running
  try {
    const r = await fetch(`${BASE}/index.html`, { signal: AbortSignal.timeout(1000) });
    if (r.ok) return;
  } catch { /* not running */ }

  server = spawn('npx', ['http-server', '.', '-p', String(PORT), '-s', '--no-dotfiles'], {
    cwd: process.cwd(),
    stdio: 'ignore',
  });

  // Poll until ready
  for (let i = 0; i < 40; i++) {
    await new Promise(r => setTimeout(r, 250));
    try {
      const r = await fetch(`${BASE}/index.html`, { signal: AbortSignal.timeout(2000) });
      if (r.ok) return;
    } catch { /* retry */ }
  }
  throw new Error('Server failed to start');
});

after(() => { if (server) server.kill('SIGTERM'); });

// ═════════════════════════════════════════════════════════════════
// 1. PAGE LOADING — All pages return 200 with correct titles
// ═════════════════════════════════════════════════════════════════
describe('1. Page Loading', () => {
  const PAGES = [
    ['', 'Salus'],
    ['index.html', 'Salus'],
    ['about.html', 'About'],
    ['sessions.html', 'Meditation'],
    ['mindfulness.html', 'Mindfulness'],
    ['breathe.html', 'Salus'],
    ['asmr.html', 'ASMR'],
    ['sleep-stories.html', 'Sleep'],
    ['soundscapes.html', 'Salus'],
    ['education.html', 'Salus'],
    ['cbt.html', 'CBT'],
    ['tools.html', 'Salus'],
    ['reading.html', 'Salus'],
    ['applied-psychology.html', 'Psychology'],
    ['login.html', 'Log In'],
    ['signup.html', 'Salus'],
    ['reset-password.html', 'Salus'],
    ['dashboard.html', 'Salus'],
    ['apps.html', 'Salus'],
    ['contact.html', 'Contact'],
    ['faq.html', 'FAQ'],
    ['terms.html', 'Terms'],
    ['privacy.html', 'Privacy'],
    ['disclaimer.html', 'Disclaimer'],
    ['newsletter.html', 'Newsletter'],
    ['media.html', 'Salus'],
    ['lend-your-voice.html', 'Voice'],
    ['mindfulness-21-day.html', 'Mindfulness'],
  ];

  for (const [path, title] of PAGES) {
    it(`${path || '/'} → 200, title contains "${title}"`, async () => {
      const { status, html } = await get(path);
      assert.equal(status, 200);
      assert.ok(html.toLowerCase().includes(title.toLowerCase()), `Missing "${title}" in title`);
    });
  }

  it('Homepage meta description mentions "family-run meditation"', async () => {
    const { html } = await get('index.html');
    assert.ok(has(html, 'family-run meditation'));
  });

  it('Homepage starts with DOCTYPE', async () => {
    const { html } = await get('index.html');
    assert.ok(html.trimStart().startsWith('<!DOCTYPE html>'));
  });

  it('Homepage has lang="en"', async () => {
    const { html } = await get('index.html');
    assert.ok(has(html, 'lang="en"'));
  });

  it('Non-existent page returns 404', async () => {
    const { status } = await get('this-page-does-not-exist-xyz.html');
    assert.equal(status, 404);
  });
});

// ═════════════════════════════════════════════════════════════════
// 2. NAVIGATION — Links exist and resolve
// ═════════════════════════════════════════════════════════════════
describe('2. Navigation', () => {
  const PRIMARY = ['index.html','sessions.html','mindfulness.html','cbt.html','asmr.html','sleep-stories.html','education.html','about.html'];
  const SECONDARY = ['tools.html','reading.html','applied-psychology.html','newsletter.html','contact.html','lend-your-voice.html'];
  const CTAS = ['apps.html','login.html'];

  for (const link of [...PRIMARY, ...SECONDARY, ...CTAS]) {
    it(`"${link}" returns 200`, async () => {
      const r = await head(link);
      assert.ok(r.ok, `${link} → ${r.status}`);
    });
  }

  it('Homepage HTML contains all primary nav links', async () => {
    const { html } = await get('index.html');
    for (const l of PRIMARY) assert.ok(has(html, `href="${l}"`), `Missing ${l}`);
  });

  it('Homepage HTML contains all secondary nav links', async () => {
    const { html } = await get('index.html');
    for (const l of SECONDARY) assert.ok(has(html, `href="${l}"`), `Missing ${l}`);
  });

  it('robots.txt accessible', async () => {
    assert.ok((await head('robots.txt')).ok);
  });

  it('sitemap.xml accessible', async () => {
    assert.ok((await head('sitemap.xml')).ok);
  });

  it('Homepage has canonical URL to salus-mind.com', async () => {
    const { html } = await get('index.html');
    assert.ok(has(html, 'rel="canonical"') && has(html, 'https://salus-mind.com'));
  });
});

// ═════════════════════════════════════════════════════════════════
// 3. AUTH PAGES — Forms, inputs, script references
// ═════════════════════════════════════════════════════════════════
describe('3. Auth Pages', () => {
  describe('Login', () => {
    it('has email input', async () => { assert.ok(has((await get('login.html')).html, 'type="email"')); });
    it('has password input', async () => { assert.ok(has((await get('login.html')).html, 'type="password"')); });
    it('loads Supabase JS v2', async () => { assert.ok(has((await get('login.html')).html, 'supabase-js@2')); });
    it('loads supabase-config.js', async () => { assert.ok(has((await get('login.html')).html, 'supabase-config.js')); });
    it('loads auth.js', async () => { assert.ok(has((await get('login.html')).html, 'auth.js')); });
    it('links to signup', async () => { assert.ok(has((await get('login.html')).html, 'signup.html')); });
    it('links to reset-password', async () => { assert.ok(has((await get('login.html')).html, 'reset-password.html')); });
  });

  describe('Signup', () => {
    it('has email input', async () => { assert.ok(has((await get('signup.html')).html, 'type="email"')); });
    it('has password input', async () => { assert.ok(has((await get('signup.html')).html, 'type="password"')); });
    it('loads auth scripts', async () => {
      const { html } = await get('signup.html');
      assert.ok(has(html, 'supabase-config.js') && has(html, 'auth.js'));
    });
    it('links to login', async () => { assert.ok(has((await get('signup.html')).html, 'login.html')); });
  });

  describe('Reset Password', () => {
    it('has email input', async () => { assert.ok(has((await get('reset-password.html')).html, 'type="email"')); });
    it('loads auth.js', async () => { assert.ok(has((await get('reset-password.html')).html, 'auth.js')); });
  });

  describe('Dashboard', () => {
    it('returns 200', async () => { assert.equal((await get('dashboard.html')).status, 200); });
    it('loads auth.js', async () => { assert.ok(has((await get('dashboard.html')).html, 'auth.js')); });
  });
});

// ═════════════════════════════════════════════════════════════════
// 4. SUPABASE INTEGRATION — Config and wiring
// ═════════════════════════════════════════════════════════════════
describe('4. Supabase Integration', () => {
  it('supabase-config.js exists', async () => {
    assert.equal((await get('js/supabase-config.js')).status, 200);
  });

  it('config has correct Supabase URL', async () => {
    assert.ok(has((await get('js/supabase-config.js')).html, 'egywowuyixfqytaucihf.supabase.co'));
  });

  it('config uses Legacy JWT key (eyJ…), not sb_publishable_', async () => {
    const { html } = await get('js/supabase-config.js');
    assert.ok(has(html, 'eyJ'));
    assert.ok(!has(html, 'sb_publishable_'));
  });

  it('config calls createClient()', async () => {
    assert.ok(has((await get('js/supabase-config.js')).html, 'createClient'));
  });

  it('config exposes window.salusSupabase', async () => {
    assert.ok(has((await get('js/supabase-config.js')).html, 'salusSupabase'));
  });

  it('auth.js exists and references salusSupabase', async () => {
    const { status, html } = await get('js/auth.js');
    assert.equal(status, 200);
    assert.ok(has(html, 'salusSupabase'));
  });

  const AUTH_PAGES = ['login.html', 'signup.html', 'reset-password.html', 'dashboard.html'];
  for (const page of AUTH_PAGES) {
    it(`${page} loads supabase CDN + config + auth.js`, async () => {
      const { html } = await get(page);
      assert.ok(has(html, 'supabase-js@2') || has(html, '@supabase/supabase-js'));
      assert.ok(has(html, 'supabase-config.js'));
      assert.ok(has(html, 'auth.js'));
    });
  }

  it('Login page script load order: CDN → config → auth', async () => {
    const { html } = await get('login.html');
    const a = html.indexOf('supabase-js@2');
    const b = html.indexOf('supabase-config.js');
    const c = html.indexOf('auth.js');
    assert.ok(a > -1 && b > -1 && c > -1);
    assert.ok(a < b, 'CDN before config');
    assert.ok(b < c, 'config before auth');
  });
});

// ═════════════════════════════════════════════════════════════════
// 5. MEDIA REFERENCES — Audio URLs point to R2
// ═════════════════════════════════════════════════════════════════
describe('5. Media References (R2)', () => {
  it('Sessions page has data-src audio players', async () => {
    assert.ok(dataSrcs((await get('sessions.html')).html).length > 0);
  });

  it('Sessions media URLs → R2 domain', async () => {
    for (const src of dataSrcs((await get('sessions.html')).html)) {
      assert.ok(src.startsWith(MEDIA_DOMAIN), `Expected R2 URL, got: ${src}`);
    }
  });

  it('Sessions media URLs end in .mp3', async () => {
    for (const src of dataSrcs((await get('sessions.html')).html)) {
      assert.ok(src.endsWith('.mp3'), `Expected .mp3, got: ${src}`);
    }
  });

  it('Mindfulness page has audio players', async () => {
    assert.ok(dataSrcs((await get('mindfulness.html')).html).length > 0);
  });

  it('Mindfulness media URLs → R2 domain', async () => {
    for (const src of dataSrcs((await get('mindfulness.html')).html)) {
      assert.ok(src.startsWith(MEDIA_DOMAIN), `Expected R2 URL, got: ${src}`);
    }
  });

  it('21-day mindfulness page has audio', async () => {
    assert.ok(dataSrcs((await get('mindfulness-21-day.html')).html).length > 0);
  });

  it('Media page has audio players', async () => {
    assert.ok(dataSrcs((await get('media.html')).html).length > 0);
  });

  it('No media URLs use relative paths', async () => {
    for (const page of ['sessions.html', 'mindfulness.html', 'media.html']) {
      for (const src of dataSrcs((await get(page)).html)) {
        assert.ok(!src.startsWith('/') && !src.startsWith('./') && !src.startsWith('content/'),
          `${page}: relative media URL: ${src}`);
      }
    }
  });

  it('Free audio files use /content/audio-free/ path', async () => {
    const free = dataSrcs((await get('sessions.html')).html).filter(s => s.includes('audio-free'));
    for (const src of free) {
      assert.ok(src.includes('/content/audio-free/'), `Wrong path: ${src}`);
    }
  });
});

// ═════════════════════════════════════════════════════════════════
// 6. CSS & JS ASSETS — Files load and have content
// ═════════════════════════════════════════════════════════════════
describe('6. Assets', () => {
  for (const file of ['css/style.css', 'js/auth.js', 'js/main.js', 'js/tracker.js', 'js/supabase-config.js']) {
    it(`${file} returns 200`, async () => {
      assert.ok((await head(file)).ok);
    });
  }

  it('style.css has CSS rules', async () => {
    const { html } = await get('css/style.css');
    assert.ok(html.length > 100);
    assert.ok(html.includes('{') && html.includes('}'));
  });

  it('auth.js has JavaScript code', async () => {
    const { html } = await get('js/auth.js');
    assert.ok(html.length > 100);
    assert.ok(html.includes('function') || html.includes('=>') || html.includes('const '));
  });

  it('OG image accessible', async () => {
    assert.ok((await head('images/meditation-woman-outdoor.jpg')).ok);
  });
});

// ═════════════════════════════════════════════════════════════════
// 7. SEO & META — OG tags, viewport, charset
// ═════════════════════════════════════════════════════════════════
describe('7. SEO & Meta', () => {
  it('Homepage has OG tags', async () => {
    const { html } = await get('index.html');
    for (const tag of ['og:title', 'og:description', 'og:image', 'og:url']) {
      assert.ok(has(html, tag), `Missing ${tag}`);
    }
  });

  it('Homepage has Twitter card', async () => {
    assert.ok(has((await get('index.html')).html, 'twitter:card'));
  });

  it('Sessions page has OG tags', async () => {
    const { html } = await get('sessions.html');
    assert.ok(has(html, 'og:title') && has(html, 'og:description'));
  });

  it('Homepage references style.css', async () => {
    assert.ok(has((await get('index.html')).html, 'css/style.css'));
  });

  it('Homepage loads main.js', async () => {
    assert.ok(has((await get('index.html')).html, 'js/main.js'));
  });

  for (const page of ['index.html', 'sessions.html', 'login.html', 'about.html']) {
    it(`${page} has viewport meta`, async () => {
      assert.ok(has((await get(page)).html, 'viewport'));
    });

    it(`${page} has UTF-8 charset`, async () => {
      const { html } = await get(page);
      assert.ok(has(html, 'charset="UTF-8"') || has(html, 'charset="utf-8"'));
    });
  }
});
