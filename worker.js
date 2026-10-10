// แอป JAC — server part (Cloudflare Worker)
// Static files in ./public are served by Cloudflare directly. Only /api/*, /auth/* and /admin go through this script.
//
// Settings (Cloudflare dashboard → Workers & Pages → jac-app → Settings → Variables and Secrets):
//   GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET   — Google login (Google Cloud Console → OAuth client, type "Web")
//   LINE_CHANNEL_ID, LINE_CHANNEL_SECRET     — LINE login (LINE Developers → LINE Login channel)
//   ADMIN_EMAILS  — comma list of e-mails that may open /admin (Google accounts)
//   ADMIN_IDS     — comma list of user ids that may open /admin (e.g. line:Uxxxx, shown in the app's settings)
// While no login provider is set, the app keeps working without login (nothing changes for users).

import ADMIN_HTML from './admin_page.js';   // generated from admin.html by make_admin.py

const SESSION_DAYS = 180;
const MAX_PROGRESS = 300 * 1024;          // bytes of synced progress per user

const SCHEMA = [
  `CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, provider TEXT, email TEXT, name TEXT, picture TEXT,
     created INTEGER, last_seen INTEGER, logins INTEGER DEFAULT 0)`,
  `CREATE TABLE IF NOT EXISTS sessions (hash TEXT PRIMARY KEY, user_id TEXT, created INTEGER, expires INTEGER)`,
  `CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, ts INTEGER, part TEXT,
     mode TEXT, label TEXT, n INTEGER, s INTEGER, rid TEXT)`,
  `CREATE INDEX IF NOT EXISTS results_user ON results (user_id, ts)`,
  `CREATE UNIQUE INDEX IF NOT EXISTS results_rid ON results (user_id, rid)`,
  `CREATE TABLE IF NOT EXISTS progress (user_id TEXT PRIMARY KEY, data TEXT, summary TEXT, updated INTEGER)`
];
let schemaReady = false;
async function ensureSchema(db) {
  if (schemaReady) return;
  for (const sql of SCHEMA) await db.prepare(sql).run();
  schemaReady = true;
}

/* ---------- small helpers ---------- */
const json = (data, status = 200, headers = {}) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', ...headers } });
const redirect = (to, headers = {}) => new Response(null, { status: 302, headers: { location: to, 'cache-control': 'no-store', ...headers } });
const hex = buf => [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
const randomToken = (n = 32) => hex(crypto.getRandomValues(new Uint8Array(n)));
const sha256 = async s => hex(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)));
const list = v => String(v || '').split(',').map(x => x.trim().toLowerCase()).filter(Boolean);
function cookies(req) {
  const out = {};
  (req.headers.get('cookie') || '').split(';').forEach(p => { const i = p.indexOf('='); if (i > 0) out[p.slice(0, i).trim()] = decodeURIComponent(p.slice(i + 1).trim()); });
  return out;
}
const cookie = (name, value, maxAge) => `${name}=${encodeURIComponent(value)}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAge}`;
function jwtPayload(token) {
  const part = String(token || '').split('.')[1]; if (!part) throw new Error('bad id_token');
  const b64 = part.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((part.length + 3) % 4);
  return JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(b64), c => c.charCodeAt(0))));
}
const providers = env => [env.GOOGLE_CLIENT_ID && env.GOOGLE_CLIENT_SECRET && 'google', env.LINE_CHANNEL_ID && env.LINE_CHANNEL_SECRET && 'line'].filter(Boolean);
const isAdmin = (env, u) => !!u && ((u.email && list(env.ADMIN_EMAILS).includes(u.email.toLowerCase())) || list(env.ADMIN_IDS).includes(u.id.toLowerCase()));

async function currentUser(req, env) {
  const t = cookies(req).jac_s; if (!t) return null;
  const row = await env.DB.prepare('SELECT u.* , s.expires FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.hash = ?').bind(await sha256(t)).first();
  if (!row || row.expires < Date.now()) return null;
  return row;
}

/* ---------- login with Google / LINE (OAuth 2.0 + OpenID Connect, code flow) ---------- */
const PROV = {
  google: {
    auth: 'https://accounts.google.com/o/oauth2/v2/auth',
    token: 'https://oauth2.googleapis.com/token',
    scope: 'openid email profile',
    id: env => env.GOOGLE_CLIENT_ID, secret: env => env.GOOGLE_CLIENT_SECRET,
    iss: ['https://accounts.google.com', 'accounts.google.com']
  },
  line: {
    auth: 'https://access.line.me/oauth2/v2.1/authorize',
    token: 'https://api.line.me/oauth2/v2.1/token',
    scope: 'openid profile email',
    id: env => env.LINE_CHANNEL_ID, secret: env => env.LINE_CHANNEL_SECRET,
    iss: ['https://access.line.me']
  }
};
function loginStart(req, env, name) {
  const p = PROV[name]; if (!p || !providers(env).includes(name)) return json({ error: 'provider not configured' }, 404);
  const origin = new URL(req.url).origin, state = randomToken(16), nonce = randomToken(16);
  const q = new URLSearchParams({ response_type: 'code', client_id: p.id(env), redirect_uri: `${origin}/auth/${name}/callback`, scope: p.scope, state, nonce });
  if (name === 'google') q.set('prompt', 'select_account');
  return redirect(`${p.auth}?${q}`, { 'set-cookie': cookie('jac_st', `${name}.${state}.${nonce}`, 600) });
}
async function loginCallback(req, env, name) {
  const p = PROV[name], url = new URL(req.url);
  const fail = msg => redirect('/?login_error=' + encodeURIComponent(msg), { 'set-cookie': cookie('jac_st', '', 0) });
  if (!p || !providers(env).includes(name)) return fail('ยังไม่ได้ตั้งค่าการเข้าสู่ระบบนี้');
  if (url.searchParams.get('error')) return fail('ยกเลิกการเข้าสู่ระบบ');
  const [stName, state, nonce] = (cookies(req).jac_st || '').split('.');
  if (stName !== name || !state || state !== url.searchParams.get('state')) return fail('หมดเวลา ลองกดเข้าสู่ระบบอีกครั้ง');
  const res = await fetch(p.token, {
    method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ grant_type: 'authorization_code', code: url.searchParams.get('code') || '', redirect_uri: `${url.origin}/auth/${name}/callback`, client_id: p.id(env), client_secret: p.secret(env) })
  });
  if (!res.ok) return fail('เข้าสู่ระบบไม่สำเร็จ (' + res.status + ')');
  const tok = await res.json();
  let c;
  try { c = jwtPayload(tok.id_token); } catch (e) { return fail('เข้าสู่ระบบไม่สำเร็จ'); }
  // the token came straight from the provider over TLS; still check who it is for and that it is fresh
  const aud = Array.isArray(c.aud) ? c.aud : [c.aud];
  if (!aud.includes(p.id(env)) || !p.iss.includes(c.iss) || (c.exp && c.exp * 1000 < Date.now()) || (c.nonce && c.nonce !== nonce) || !c.sub)
    return fail('เข้าสู่ระบบไม่สำเร็จ (token)');
  const id = `${name}:${c.sub}`, now = Date.now();
  await env.DB.prepare(`INSERT INTO users (id, provider, email, name, picture, created, last_seen, logins) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
    ON CONFLICT(id) DO UPDATE SET email = COALESCE(excluded.email, users.email), name = excluded.name, picture = excluded.picture, last_seen = excluded.last_seen, logins = users.logins + 1`)
    .bind(id, name, c.email || null, c.name || c.email || 'ผู้ใช้', c.picture || null, now, now).run();
  const t = randomToken();
  await env.DB.prepare('INSERT INTO sessions (hash, user_id, created, expires) VALUES (?, ?, ?, ?)').bind(await sha256(t), id, now, now + SESSION_DAYS * 864e5).run();
  const h = new Headers({ location: '/?login=ok', 'cache-control': 'no-store' });
  h.append('set-cookie', cookie('jac_s', t, SESSION_DAYS * 86400));
  h.append('set-cookie', cookie('jac_st', '', 0));
  return new Response(null, { status: 302, headers: h });
}

/* ---------- API ---------- */
async function api(req, env, path) {
  const user = await currentUser(req, env);
  if (path === '/api/me') {
    if (user && Date.now() - (user.last_seen || 0) > 10 * 60e3) await env.DB.prepare('UPDATE users SET last_seen = ? WHERE id = ?').bind(Date.now(), user.id).run();
    return json({ configured: providers(env).length > 0, providers: providers(env),
      user: user && { id: user.id, provider: user.provider, name: user.name, email: user.email, picture: user.picture }, admin: isAdmin(env, user) });
  }
  if (!user) return json({ error: 'login required' }, 401);
  if (path === '/api/logout' && req.method === 'POST') {
    const t = cookies(req).jac_s; if (t) await env.DB.prepare('DELETE FROM sessions WHERE hash = ?').bind(await sha256(t)).run();
    return json({ ok: true }, 200, { 'set-cookie': cookie('jac_s', '', 0) });
  }
  if (path === '/api/result' && req.method === 'POST') {
    let items; try { items = await req.json(); } catch (e) { return json({ error: 'bad json' }, 400); }
    items = (Array.isArray(items) ? items : [items]).slice(0, 50);
    const ok = x => x && Number.isInteger(x.n) && x.n > 0 && x.n <= 500 && Number.isInteger(x.s) && x.s >= 0 && x.s <= x.n;
    const stmts = items.filter(ok).map(x => env.DB.prepare('INSERT OR IGNORE INTO results (user_id, ts, part, mode, label, n, s, rid) VALUES (?, ?, ?, ?, ?, ?, ?, ?)')
      .bind(user.id, Math.min(Number(x.ts) || Date.now(), Date.now()), String(x.part || '').slice(0, 20), String(x.mode || '').slice(0, 20), String(x.label || '').slice(0, 80), x.n, x.s, String(x.rid || randomToken(8)).slice(0, 40)));
    if (stmts.length) await env.DB.batch(stmts);
    return json({ ok: true, saved: stmts.length });
  }
  if (path === '/api/progress') {
    if (req.method === 'GET') {
      const row = await env.DB.prepare('SELECT data, updated FROM progress WHERE user_id = ?').bind(user.id).first();
      return json(row ? { data: JSON.parse(row.data), updated: row.updated } : { data: null, updated: 0 });
    }
    if (req.method === 'PUT') {
      const text = await req.text();
      if (text.length > MAX_PROGRESS) return json({ error: 'too large' }, 413);
      let body; try { body = JSON.parse(text); } catch (e) { return json({ error: 'bad json' }, 400); }
      const now = Date.now();
      await env.DB.prepare(`INSERT INTO progress (user_id, data, summary, updated) VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET data = excluded.data, summary = excluded.summary, updated = excluded.updated`)
        .bind(user.id, JSON.stringify(body.data || {}), JSON.stringify(body.summary || {}), now).run();
      return json({ ok: true, updated: now });
    }
  }
  if (path.startsWith('/api/admin/')) {
    if (!isAdmin(env, user)) return json({ error: 'admin only' }, 403);
    if (path === '/api/admin/users') {
      const { results } = await env.DB.prepare(`SELECT u.id, u.provider, u.email, u.name, u.picture, u.created, u.last_seen, u.logins,
          COUNT(r.id) AS quizzes, COALESCE(SUM(r.n), 0) AS answered, COALESCE(SUM(r.s), 0) AS correct, MAX(r.ts) AS last_quiz,
          SUM(CASE WHEN r.ts > ? THEN r.n ELSE 0 END) AS answered7, p.summary
        FROM users u LEFT JOIN results r ON r.user_id = u.id LEFT JOIN progress p ON p.user_id = u.id
        GROUP BY u.id ORDER BY u.last_seen DESC`).bind(Date.now() - 7 * 864e5).all();
      const mocks = (await env.DB.prepare(`SELECT user_id, part, n, s, ts FROM results WHERE mode = 'real' ORDER BY ts`).all()).results;
      const byUser = {};
      mocks.forEach(m => { const u = (byUser[m.user_id] = byUser[m.user_id] || {}); const p = (u[m.part] = u[m.part] || { count: 0, best: 0, last: 0, lastTs: 0 });
        const pct = Math.round(m.s / m.n * 100); p.count++; p.best = Math.max(p.best, pct); p.last = pct; p.lastTs = m.ts; });
      return json({ users: results.map(r => ({ ...r, summary: r.summary ? JSON.parse(r.summary) : null, mocks: byUser[r.id] || {} })) });
    }
    if (path === '/api/admin/user') {
      const id = new URL(req.url).searchParams.get('id') || '';
      const u = await env.DB.prepare('SELECT * FROM users WHERE id = ?').bind(id).first();
      if (!u) return json({ error: 'not found' }, 404);
      const { results } = await env.DB.prepare('SELECT ts, part, mode, label, n, s FROM results WHERE user_id = ? ORDER BY ts DESC LIMIT 300').bind(id).all();
      const p = await env.DB.prepare('SELECT summary, updated FROM progress WHERE user_id = ?').bind(id).first();
      return json({ user: u, results, summary: p && p.summary ? JSON.parse(p.summary) : null, synced: p ? p.updated : 0 });
    }
  }
  return json({ error: 'not found' }, 404);
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url), path = url.pathname;
    if (!path.startsWith('/api/') && !path.startsWith('/auth/') && path !== '/admin' && !path.startsWith('/admin/')) return env.ASSETS.fetch(req);
    if (!env.DB) return json({ configured: false, providers: [], user: null, admin: false, note: 'no database binding' }, path === '/api/me' ? 200 : 503);
    await ensureSchema(env.DB);
    try {
      const m = path.match(/^\/auth\/(google|line)(\/callback)?$/);
      if (m) return m[2] ? loginCallback(req, env, m[1]) : loginStart(req, env, m[1]);
      if (path === '/admin' || path === '/admin/') {
        const user = await currentUser(req, env);
        if (!isAdmin(env, user)) return redirect('/?admin=denied');
        return new Response(ADMIN_HTML, { headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store', 'x-robots-tag': 'noindex' } });
      }
      if (path.startsWith('/api/')) return api(req, env, path);
      return json({ error: 'not found' }, 404);
    } catch (e) {
      return json({ error: 'server error', detail: String(e && e.message || e).slice(0, 200) }, 500);
    }
  }
};
