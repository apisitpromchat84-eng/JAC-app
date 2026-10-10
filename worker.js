// แอป JAC — anonymous activity counter (Cloudflare Worker + D1)
// No login, no names: each device sends a random id, the part/mode it studied and its score.
// Static files in ./public are served directly; only /api/* and /stats come through here.
import STATS_HTML from './stats_page.js';   // generated from stats.html by make_stats.py

const SCHEMA = [
  `CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER, day TEXT, dev TEXT, part TEXT, mode TEXT, n INTEGER, s INTEGER)`,
  `CREATE INDEX IF NOT EXISTS events_day ON events (day)`,
  `CREATE TABLE IF NOT EXISTS pings (dev TEXT PRIMARY KEY, ts INTEGER, part TEXT)`,
  `CREATE TABLE IF NOT EXISTS opens (day TEXT, dev TEXT, PRIMARY KEY (day, dev))`,
  `CREATE TABLE IF NOT EXISTS names (dev TEXT PRIMARY KEY, name TEXT, updated INTEGER)`,
  `CREATE TABLE IF NOT EXISTS avatars (dev TEXT PRIMARY KEY, img TEXT, updated INTEGER)`,
  `CREATE TABLE IF NOT EXISTS summaries (dev TEXT PRIMARY KEY, data TEXT, updated INTEGER)`
];
// password for /stats (only its SHA-256 is stored here)
const STATS_KEY_SHA256 = 'd38ac90ed5baac73579f69da615e0fe79b865be8ddf0bdde5599e23d8ed5d99b';
const sha256 = async t => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(t)))].map(b => b.toString(16).padStart(2, '0')).join('');
let ready = false;
async function ensure(db) {
  if (ready) return;
  for (const q of SCHEMA) await db.prepare(q).run();
  try { await db.prepare('ALTER TABLE events ADD COLUMN rid TEXT').run(); } catch (e) {}      // older databases
  await db.prepare('CREATE UNIQUE INDEX IF NOT EXISTS events_rid ON events (dev, rid)').run();
  ready = true;
}

const json = (d, status = 200) => new Response(JSON.stringify(d), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' } });
const jstDay = ts => new Date(ts + 9 * 3600e3).toISOString().slice(0, 10);          // day boundary in Japan time
const devOk = d => typeof d === 'string' && /^[a-z0-9]{8,32}$/.test(d);
const PARTS = ['gakka', 'jitsugi', 'life'];

async function ping(req, env) {
  let b; try { b = await req.json(); } catch (e) { return json({ ok: false }, 400); }
  if (!devOk(b.dev)) return json({ ok: false }, 400);
  const now = Date.now(), part = PARTS.includes(b.part) ? b.part : '';
  const name = String(b.name || '').replace(/[<>"'`\\]/g, '').trim().slice(0, 24);
  const stmts = [
    env.DB.prepare('INSERT INTO pings (dev, ts, part) VALUES (?, ?, ?) ON CONFLICT(dev) DO UPDATE SET ts = excluded.ts, part = excluded.part').bind(b.dev, now, part),
    env.DB.prepare('INSERT OR IGNORE INTO opens (day, dev) VALUES (?, ?)').bind(jstDay(now), b.dev)
  ];
  if (typeof b.avatar === 'string' && /^data:image\/(jpeg|webp|png);base64,[A-Za-z0-9+/=]+$/.test(b.avatar) && b.avatar.length < 40000)
    stmts.push(env.DB.prepare('INSERT INTO avatars (dev, img, updated) VALUES (?, ?, ?) ON CONFLICT(dev) DO UPDATE SET img = excluded.img, updated = excluded.updated').bind(b.dev, b.avatar, now));
  if (b.avatar === '') stmts.push(env.DB.prepare('DELETE FROM avatars WHERE dev = ?').bind(b.dev));
  if (b.summary && typeof b.summary === 'object') { const t = JSON.stringify(b.summary); if (t.length < 20000)
    stmts.push(env.DB.prepare('INSERT INTO summaries (dev, data, updated) VALUES (?, ?, ?) ON CONFLICT(dev) DO UPDATE SET data = excluded.data, updated = excluded.updated').bind(b.dev, t, now)); }
  if (name) stmts.push(env.DB.prepare('INSERT INTO names (dev, name, updated) VALUES (?, ?, ?) ON CONFLICT(dev) DO UPDATE SET name = excluded.name, updated = excluded.updated').bind(b.dev, name, now));
  const ev = Array.isArray(b.events) ? b.events.slice(0, 20) : [];
  ev.forEach(x => {
    if (!x || !Number.isInteger(x.n) || x.n < 1 || x.n > 500 || !Number.isInteger(x.s) || x.s < 0 || x.s > x.n) return;
    const ts = Math.min(Number(x.ts) || now, now);
    stmts.push(env.DB.prepare('INSERT OR IGNORE INTO events (ts, day, dev, part, mode, n, s, rid) VALUES (?, ?, ?, ?, ?, ?, ?, ?)')
      .bind(ts, jstDay(ts), b.dev, PARTS.includes(x.part) ? x.part : '', String(x.mode || '').slice(0, 12), x.n, x.s, typeof x.rid === 'string' ? x.rid.slice(0, 24) : null));
  });
  await env.DB.batch(stmts);
  // give a device back what the server already knows (storage cleared, Safari vs home-screen app, a new phone)
  const out = { ok: true };
  if (!name) {
    const r = await env.DB.prepare('SELECT n.name, a.img FROM names n LEFT JOIN avatars a ON a.dev = n.dev WHERE n.dev = ?').bind(b.dev).first();
    if (r && r.name) { out.name = r.name; if (r.img) out.avatar = r.img; }
  } else if (b.noav) {
    const r = await env.DB.prepare('SELECT a.img FROM names n JOIN avatars a ON a.dev = n.dev WHERE LOWER(n.name) = LOWER(?) ORDER BY a.updated DESC LIMIT 1').bind(name).first();
    if (r && r.img) out.avatar = r.img;
  }
  return json(out);
}

async function stats(env) {
  const now = Date.now(), today = jstDay(now), from = jstDay(now - 13 * 864e5);
  const one = (q, ...a) => env.DB.prepare(q).bind(...a).first();
  const all = async (q, ...a) => (await env.DB.prepare(q).bind(...a).all()).results;
  const live = await all('SELECT part, COUNT(*) AS c FROM pings WHERE ts > ? GROUP BY part', now - 5 * 60e3);
  const t = await one('SELECT COUNT(DISTINCT dev) AS devs, COUNT(*) AS quizzes, COALESCE(SUM(n),0) AS n, COALESCE(SUM(s),0) AS s FROM events WHERE day = ?', today);
  const opensToday = await one('SELECT COUNT(*) AS c FROM opens WHERE day = ?', today);
  const days = await all(`SELECT day, COUNT(DISTINCT dev) AS devs, COUNT(*) AS quizzes, SUM(n) AS n, SUM(s) AS s FROM events WHERE day >= ? GROUP BY day`, from);
  const opens = await all('SELECT day, COUNT(*) AS c FROM opens WHERE day >= ? GROUP BY day', from);
  const parts = await all('SELECT part, COUNT(*) AS quizzes, SUM(n) AS n, SUM(s) AS s FROM events WHERE day = ? GROUP BY part', today);
  const mocks = await all(`SELECT part, COUNT(*) AS c, SUM(CASE WHEN s * 100 >= n * 75 THEN 1 ELSE 0 END) AS pass FROM events WHERE mode = 'real' AND day >= ? GROUP BY part`, from);
  const hours = await all(`SELECT CAST(((ts / 3600000) + 9) % 24 AS INTEGER) AS h, COUNT(*) AS c FROM events WHERE day >= ? GROUP BY h`, jstDay(now - 6 * 864e5));
  const recent = await all('SELECT ts, part, mode, n, s FROM events ORDER BY ts DESC LIMIT 25');
  const devs7 = await one('SELECT COUNT(DISTINCT dev) AS c FROM opens WHERE day >= ?', jstDay(now - 6 * 864e5));
  // people: devices with the same nickname are merged
  const people = await all(`SELECT COALESCE(LOWER(n.name), 'dev:' || p.dev) AS k, MAX(n.name) AS name, MAX(p.ts) AS last, MAX(p.part) AS part,
      (SELECT COALESCE(SUM(e.n),0) FROM events e LEFT JOIN names n2 ON n2.dev = e.dev WHERE COALESCE(LOWER(n2.name), 'dev:' || e.dev) = COALESCE(LOWER(n.name), 'dev:' || p.dev) AND e.day = ?) AS n_today,
      (SELECT COALESCE(SUM(e.s),0) FROM events e LEFT JOIN names n2 ON n2.dev = e.dev WHERE COALESCE(LOWER(n2.name), 'dev:' || e.dev) = COALESCE(LOWER(n.name), 'dev:' || p.dev) AND e.day = ?) AS s_today,
      (SELECT COALESCE(SUM(e.n),0) FROM events e LEFT JOIN names n2 ON n2.dev = e.dev WHERE COALESCE(LOWER(n2.name), 'dev:' || e.dev) = COALESCE(LOWER(n.name), 'dev:' || p.dev) AND e.day >= ?) AS n_7,
      (SELECT COALESCE(SUM(e.n),0) FROM events e LEFT JOIN names n2 ON n2.dev = e.dev WHERE COALESCE(LOWER(n2.name), 'dev:' || e.dev) = COALESCE(LOWER(n.name), 'dev:' || p.dev)) AS n_all,
      (SELECT COALESCE(SUM(e.s),0) FROM events e LEFT JOIN names n2 ON n2.dev = e.dev WHERE COALESCE(LOWER(n2.name), 'dev:' || e.dev) = COALESCE(LOWER(n.name), 'dev:' || p.dev)) AS s_all,
      (SELECT e.s * 100 / e.n FROM events e LEFT JOIN names n2 ON n2.dev = e.dev WHERE COALESCE(LOWER(n2.name), 'dev:' || e.dev) = COALESCE(LOWER(n.name), 'dev:' || p.dev) AND e.mode = 'real' ORDER BY e.ts DESC LIMIT 1) AS mock_pct,
      (SELECT e.part FROM events e LEFT JOIN names n2 ON n2.dev = e.dev WHERE COALESCE(LOWER(n2.name), 'dev:' || e.dev) = COALESCE(LOWER(n.name), 'dev:' || p.dev) AND e.mode = 'real' ORDER BY e.ts DESC LIMIT 1) AS mock_part,
      (SELECT a.img FROM avatars a LEFT JOIN names n3 ON n3.dev = a.dev WHERE COALESCE(LOWER(n3.name), 'dev:' || a.dev) = COALESCE(LOWER(n.name), 'dev:' || p.dev) ORDER BY a.updated DESC LIMIT 1) AS avatar
    FROM pings p LEFT JOIN names n ON n.dev = p.dev GROUP BY k ORDER BY last DESC LIMIT 300`, today, today, jstDay(now - 6 * 864e5));
  const recentNamed = await all('SELECT e.ts, e.part, e.mode, e.n, e.s, n.name FROM events e LEFT JOIN names n ON n.dev = e.dev ORDER BY e.ts DESC LIMIT 25');
  return json({ now, today, live, t, opensToday: opensToday.c, days, opens, parts, mocks, hours, recent: recentNamed, devs7: devs7.c, people });
}

// one person (all devices that share the nickname)
async function person(env, k) {
  const KEY = "COALESCE(LOWER(n.name), 'dev:' || d.dev)";
  const devs = (await env.DB.prepare(`SELECT d.dev FROM (SELECT dev FROM pings UNION SELECT dev FROM events) d LEFT JOIN names n ON n.dev = d.dev WHERE ${KEY} = ?`).bind(k).all()).results.map(r => r.dev);
  if (!devs.length) return json({ error: 'not found' }, 404);
  const qs = devs.map(() => '?').join(',');
  const now = Date.now();
  const sums = (await env.DB.prepare(`SELECT data, updated FROM summaries WHERE dev IN (${qs}) ORDER BY updated DESC`).bind(...devs).all()).results;
  // one person on several devices (phone + tablet): per category keep the device that practised it most
  let sum = null;
  sums.forEach(r => { let d; try { d = JSON.parse(r.data); } catch (e) { return; }
    if (!sum) { sum = { data: d, updated: r.updated }; return; }
    const m = {}; sum.data.cats.forEach(c => m[c.part + '|' + c.id] = c);
    (d.cats || []).forEach(c => { const k = c.part + '|' + c.id, o = m[k];
      if (!o) { sum.data.cats.push(c); return; }
      if ((c.t || 0) > (o.t || 0)) { o.c = c.c; o.t = c.t; o.wrong = c.wrong; }
      o.done = Math.max(o.done || 0, c.done || 0); o.tried = Math.max(o.tried == null ? o.done : o.tried, c.tried == null ? c.done : c.tried); });
    if (!sum.data.exam && d.exam) sum.data.exam = d.exam; });
  const name = await env.DB.prepare(`SELECT name FROM names WHERE dev IN (${qs}) ORDER BY updated DESC LIMIT 1`).bind(...devs).first();
  const av = await env.DB.prepare(`SELECT img FROM avatars WHERE dev IN (${qs}) ORDER BY updated DESC LIMIT 1`).bind(...devs).first();
  const last = await env.DB.prepare(`SELECT MAX(ts) AS ts FROM pings WHERE dev IN (${qs})`).bind(...devs).first();
  const events = (await env.DB.prepare(`SELECT ts, day, part, mode, n, s FROM events WHERE dev IN (${qs}) ORDER BY ts DESC LIMIT 300`).bind(...devs).all()).results;
  const days = (await env.DB.prepare(`SELECT day, SUM(n) AS n, SUM(s) AS s FROM events WHERE dev IN (${qs}) AND day >= ? GROUP BY day`).bind(...devs, jstDay(now - 13 * 864e5)).all()).results;
  return json({ now, today: jstDay(now), k, devices: devs.length, name: name && name.name, avatar: av && av.img, last: last && last.ts,
    summary: sum ? sum.data : null, synced: sum ? sum.updated : 0, events, days });
}

export default {
  async fetch(req, env) {
    const path = new URL(req.url).pathname;
    if (path === '/stats' || path === '/stats/')
      return new Response(STATS_HTML, { headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store', 'x-robots-tag': 'noindex' } });
    if (!path.startsWith('/api/')) return env.ASSETS.fetch(req);
    if (!env.DB) return json({ ok: false, error: 'no database' }, 503);
    try {
      await ensure(env.DB);
      if (path === '/api/ping' && req.method === 'POST') return await ping(req, env);
      if (path === '/api/person') {
        if (await sha256(req.headers.get('x-key') || '') !== STATS_KEY_SHA256) return json({ error: 'key' }, 401);
        return await person(env, new URL(req.url).searchParams.get('k') || '');
      }
      if (path === '/api/stats') {
        if (await sha256(req.headers.get('x-key') || '') !== STATS_KEY_SHA256) return json({ error: 'key' }, 401);
        return await stats(env);
      }
      return json({ error: 'not found' }, 404);
    } catch (e) { return json({ error: String(e && e.message || e).slice(0, 200) }, 500); }
  }
};
