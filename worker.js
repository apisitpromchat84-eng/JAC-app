// แอป JAC — anonymous activity counter (Cloudflare Worker + D1)
// No login, no names: each device sends a random id, the part/mode it studied and its score.
// Static files in ./public are served directly; only /api/* and /stats come through here.
import STATS_HTML from './stats_page.js';   // generated from stats.html by make_stats.py

const SCHEMA = [
  `CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER, day TEXT, dev TEXT, part TEXT, mode TEXT, n INTEGER, s INTEGER)`,
  `CREATE INDEX IF NOT EXISTS events_day ON events (day)`,
  `CREATE TABLE IF NOT EXISTS pings (dev TEXT PRIMARY KEY, ts INTEGER, part TEXT)`,
  `CREATE TABLE IF NOT EXISTS opens (day TEXT, dev TEXT, PRIMARY KEY (day, dev))`
];
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
  const stmts = [
    env.DB.prepare('INSERT INTO pings (dev, ts, part) VALUES (?, ?, ?) ON CONFLICT(dev) DO UPDATE SET ts = excluded.ts, part = excluded.part').bind(b.dev, now, part),
    env.DB.prepare('INSERT OR IGNORE INTO opens (day, dev) VALUES (?, ?)').bind(jstDay(now), b.dev)
  ];
  const ev = Array.isArray(b.events) ? b.events.slice(0, 20) : [];
  ev.forEach(x => {
    if (!x || !Number.isInteger(x.n) || x.n < 1 || x.n > 500 || !Number.isInteger(x.s) || x.s < 0 || x.s > x.n) return;
    const ts = Math.min(Number(x.ts) || now, now);
    stmts.push(env.DB.prepare('INSERT INTO events (ts, day, dev, part, mode, n, s) VALUES (?, ?, ?, ?, ?, ?, ?)')
      .bind(ts, jstDay(ts), b.dev, PARTS.includes(x.part) ? x.part : '', String(x.mode || '').slice(0, 12), x.n, x.s));
  });
  await env.DB.batch(stmts);
  return json({ ok: true, saved: stmts.length - 2 });
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
  return json({ now, today, live, t, opensToday: opensToday.c, days, opens, parts, mocks, hours, recent, devs7: devs7.c });
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
      if (path === '/api/stats') return await stats(env);
      return json({ error: 'not found' }, 404);
    } catch (e) { return json({ error: String(e && e.message || e).slice(0, 200) }, 500); }
  }
};
