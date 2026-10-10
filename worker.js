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
  `CREATE TABLE IF NOT EXISTS avatars (dev TEXT PRIMARY KEY, img TEXT, updated INTEGER)`
];
// password for /stats (only its SHA-256 is stored here)
const STATS_KEY_SHA256 = 'd38ac90ed5baac73579f69da615e0fe79b865be8ddf0bdde5599e23d8ed5d99b';
const sha256 = async t => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(t)))].map(b => b.toString(16).padStart(2, '0')).join('');
let ready = false;
async function ensure(db) { if (ready) return; for (const q of SCHEMA) await db.prepare(q).run(); ready = true; }

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
  if (name) stmts.push(env.DB.prepare('INSERT INTO names (dev, name, updated) VALUES (?, ?, ?) ON CONFLICT(dev) DO UPDATE SET name = excluded.name, updated = excluded.updated').bind(b.dev, name, now));
  const ev = Array.isArray(b.events) ? b.events.slice(0, 20) : [];
  ev.forEach(x => {
    if (!x || !Number.isInteger(x.n) || x.n < 1 || x.n > 500 || !Number.isInteger(x.s) || x.s < 0 || x.s > x.n) return;
    const ts = Math.min(Number(x.ts) || now, now);
    stmts.push(env.DB.prepare('INSERT INTO events (ts, day, dev, part, mode, n, s) VALUES (?, ?, ?, ?, ?, ?, ?)')
      .bind(ts, jstDay(ts), b.dev, PARTS.includes(x.part) ? x.part : '', String(x.mode || '').slice(0, 12), x.n, x.s));
  });
  await env.DB.batch(stmts);
  return json({ ok: true });
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
      if (path === '/api/stats') {
        if (await sha256(req.headers.get('x-key') || '') !== STATS_KEY_SHA256) return json({ error: 'key' }, 401);
        return await stats(env);
      }
      return json({ error: 'not found' }, 404);
    } catch (e) { return json({ error: String(e && e.message || e).slice(0, 200) }, 500); }
  }
};
