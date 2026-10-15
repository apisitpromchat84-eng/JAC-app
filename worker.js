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
  `CREATE TABLE IF NOT EXISTS summaries (dev TEXT PRIMARY KEY, data TEXT, updated INTEGER)`,
  // who = which person a device probably belongs to: the nickname if set, otherwise a fingerprint
  // (hash of network address + phone type + screen) so Safari, the home-screen app and the LINE browser
  // of one phone count as one person. Only the hash is stored, never the address itself.
  `CREATE TABLE IF NOT EXISTS who (dev TEXT PRIMARY KEY, fp TEXT, pkey TEXT, updated INTEGER)`,
  // per-category snapshot kept once per month (the last one sent in that month), for month-to-month comparison
  `CREATE TABLE IF NOT EXISTS monthly (dev TEXT, month TEXT, data TEXT, updated INTEGER, PRIMARY KEY (dev, month))`,
  // cloud copy of a person's progress (opt-in): nickname + 4-digit PIN; only a hash of the PIN is stored
  `CREATE TABLE IF NOT EXISTS sync (nk TEXT PRIMARY KEY, pinh TEXT, data TEXT, updated INTEGER, dev TEXT, fails INTEGER DEFAULT 0, lock INTEGER DEFAULT 0)`,
  // per-network counters (key = hash of the network address + what is being counted), reset after a time window
  `CREATE TABLE IF NOT EXISTS throttle (k TEXT PRIMARY KEY, n INTEGER, reset INTEGER)`
];
// password for /stats: set it as a Worker secret (Cloudflare dashboard → Settings → Variables and Secrets,
// or `npx wrangler secret put STATS_KEY`). Nothing about it is stored in this public repo.
const sha256 = async t => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(t)))].map(b => b.toString(16).padStart(2, '0')).join('');
async function keyOk(req, env) {
  const want = env.STATS_KEY;
  if (typeof want !== 'string' || want.length < 12) return false;          // no secret set → stats stay locked
  const [a, b] = await Promise.all([sha256(req.headers.get('x-key') || ''), sha256(want)]);
  let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);   // compare without early exit
  return d === 0;
}
// count one hit for this network + bucket; true when the limit is already reached
async function overLimit(req, env, bucket, limit, windowMs) {
  const ip = req.headers.get('cf-connecting-ip') || '';
  const k = bucket + ':' + (await sha256('jac-thr|' + ip)).slice(0, 20), now = Date.now();
  const r = await env.DB.prepare(`INSERT INTO throttle (k, n, reset) VALUES (?, 1, ?)
      ON CONFLICT(k) DO UPDATE SET n = CASE WHEN reset < ? THEN 1 ELSE n + 1 END, reset = CASE WHEN reset < ? THEN excluded.reset ELSE reset END
      RETURNING n`).bind(k, now + windowMs, now, now).first();
  return !!r && r.n > limit;
}
let ready = false;
async function ensure(db) {
  if (ready) return;
  for (const q of SCHEMA) await db.prepare(q).run();
  try { await db.prepare('ALTER TABLE events ADD COLUMN rid TEXT').run(); } catch (e) {}      // older databases
  await db.prepare('CREATE UNIQUE INDEX IF NOT EXISTS events_rid ON events (dev, rid)').run();
  await db.prepare("INSERT OR IGNORE INTO who (dev, pkey, updated) SELECT dev, 'n:' || LOWER(name), updated FROM names").run();
  await db.prepare("INSERT OR IGNORE INTO monthly (dev, month, data, updated) SELECT dev, strftime('%Y-%m', updated / 1000 + 32400, 'unixepoch'), data, updated FROM summaries").run();
  ready = true;
}

const json = (d, status = 200) => new Response(JSON.stringify(d), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' } });
const jstDay = ts => new Date(ts + 9 * 3600e3).toISOString().slice(0, 10);          // day boundary in Japan time
const devOk = d => typeof d === 'string' && /^[a-z0-9]{8,32}$/.test(d);
const PARTS = ['gakka', 'jitsugi', 'life'];
const FP_SALT = 'jac-who-2026';
function phoneType(ua) {           // "iPhone iOS 18", "Android 14 SM-S911B", … (browser left out on purpose)
  ua = String(ua || '');
  let m = ua.match(/(iPhone|iPad|iPod).*?OS (\d+)/); if (m) return m[1] + ' iOS ' + m[2];
  m = ua.match(/Android (\d+)[^;)]*;\s*([^;)]+?)(?:\s+Build|\))/); if (m) return 'Android ' + m[1] + ' ' + m[2].replace(/\s*wv$/, '');
  if (/Macintosh/.test(ua)) return 'Mac'; if (/Windows/.test(ua)) return 'Windows';
  return ua.slice(0, 40);
}

// keep only the fields the app sends, with the right types — the stats page renders these
const num = v => Number.isFinite(+v) ? Math.max(0, Math.min(1e6, Math.round(+v))) : 0;
const str = (v, n) => String(v == null ? '' : v).replace(/[<>"'`\\]/g, '').slice(0, n);
function cleanSummary(sm) {
  if (!sm || typeof sm !== 'object' || !Array.isArray(sm.cats)) return null;
  const cats = sm.cats.slice(0, 200).filter(c => c && typeof c === 'object' && PARTS.includes(c.part))
    .map(c => ({ id: str(c.id, 40), th: str(c.th, 80), part: c.part, c: num(c.c), t: num(c.t), done: num(c.done), tried: num(c.tried), total: num(c.total), wrong: num(c.wrong) }));
  const parts = {};
  if (sm.parts && typeof sm.parts === 'object') PARTS.forEach(p => { const x = sm.parts[p]; if (x && typeof x === 'object') parts[p] = { n: num(x.n), pass: num(x.pass), min: num(x.min) }; });
  return { cats, parts, exam: str(sm.exam, 20), lset: str(sm.lset, 20) };
}

async function ping(req, env) {
  let b; try { b = await req.json(); } catch (e) { return json({ ok: false }, 400); }
  if (!devOk(b.dev)) return json({ ok: false }, 400);
  // a phone pings a few times a minute at most; this only stops scripts filling the database
  if (await overLimit(req, env, 'ping', 1200, 3600e3)) return json({ ok: false, error: 'busy' }, 429);
  const now = Date.now(), part = PARTS.includes(b.part) ? b.part : '';
  const name = String(b.name || '').replace(/[<>"'`\\]/g, '').trim().slice(0, 24);
  const stmts = [
    env.DB.prepare('INSERT INTO pings (dev, ts, part) VALUES (?, ?, ?) ON CONFLICT(dev) DO UPDATE SET ts = excluded.ts, part = excluded.part').bind(b.dev, now, part),
    env.DB.prepare('INSERT OR IGNORE INTO opens (day, dev) VALUES (?, ?)').bind(jstDay(now), b.dev)
  ];
  if (typeof b.avatar === 'string' && /^data:image\/(jpeg|webp|png);base64,[A-Za-z0-9+/=]+$/.test(b.avatar) && b.avatar.length < 40000)
    stmts.push(env.DB.prepare('INSERT INTO avatars (dev, img, updated) VALUES (?, ?, ?) ON CONFLICT(dev) DO UPDATE SET img = excluded.img, updated = excluded.updated').bind(b.dev, b.avatar, now));
  if (b.avatar === '') stmts.push(env.DB.prepare('DELETE FROM avatars WHERE dev = ?').bind(b.dev));
  const sm = cleanSummary(b.summary);
  if (sm) { const t = JSON.stringify(sm); if (t.length < 20000)
    stmts.push(env.DB.prepare('INSERT INTO summaries (dev, data, updated) VALUES (?, ?, ?) ON CONFLICT(dev) DO UPDATE SET data = excluded.data, updated = excluded.updated').bind(b.dev, t, now));
    stmts.push(env.DB.prepare('INSERT INTO monthly (dev, month, data, updated) VALUES (?, ?, ?, ?) ON CONFLICT(dev, month) DO UPDATE SET data = excluded.data, updated = excluded.updated').bind(b.dev, jstDay(now).slice(0, 7), t, now)); }
  if (name) stmts.push(env.DB.prepare('INSERT INTO names (dev, name, updated) VALUES (?, ?, ?) ON CONFLICT(dev) DO UPDATE SET name = excluded.name, updated = excluded.updated').bind(b.dev, name, now));
  {
    const ip = req.headers.get('cf-connecting-ip') || '', scr = String(b.scr || '').slice(0, 24);
    const fp = (await sha256(FP_SALT + '|' + ip + '|' + phoneType(req.headers.get('user-agent')) + '|' + scr)).slice(0, 16);
    let pkey = name ? 'n:' + name.toLowerCase() : '';
    if (!pkey) { const r = await env.DB.prepare('SELECT name FROM names WHERE dev = ?').bind(b.dev).first(); pkey = r && r.name ? 'n:' + r.name.toLowerCase() : 'fp:' + fp; }
    stmts.push(env.DB.prepare('INSERT INTO who (dev, fp, pkey, updated) VALUES (?, ?, ?, ?) ON CONFLICT(dev) DO UPDATE SET fp = excluded.fp, pkey = excluded.pkey, updated = excluded.updated').bind(b.dev, fp, pkey, now));
  }
  let ev = Array.isArray(b.events) ? b.events.slice(0, 20) : [];
  // at most 300 results per device per day: real study never gets near this, a spam loop would
  if (ev.length) { const c = await env.DB.prepare('SELECT COUNT(*) AS n FROM events WHERE dev = ? AND day = ?').bind(b.dev, jstDay(now)).first(); if (c && c.n >= 300) ev = []; }
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
    // only this device's own picture — never another person's picture looked up by nickname
    const r = await env.DB.prepare('SELECT img FROM avatars WHERE dev = ?').bind(b.dev).first();
    if (r && r.img) out.avatar = r.img;
  }
  return json(out);
}

async function stats(env) {
  const now = Date.now(), today = jstDay(now), from = jstDay(now - 13 * 864e5);
  const one = (q, ...a) => env.DB.prepare(q).bind(...a).first();
  const all = async (q, ...a) => (await env.DB.prepare(q).bind(...a).all()).results;
  const live = await all(`SELECT p.part AS part, COUNT(DISTINCT COALESCE(w.pkey, 'dev:' || p.dev)) AS c FROM pings p LEFT JOIN who w ON w.dev = p.dev WHERE p.ts > ? GROUP BY p.part`, now - 5 * 60e3);
  const t = await one(`SELECT COUNT(DISTINCT COALESCE(w.pkey, 'dev:' || e.dev)) AS devs, COUNT(*) AS quizzes, COALESCE(SUM(e.n),0) AS n, COALESCE(SUM(e.s),0) AS s FROM events e LEFT JOIN who w ON w.dev = e.dev WHERE e.day = ?`, today);
  const opensToday = await one(`SELECT COUNT(DISTINCT COALESCE(w.pkey, 'dev:' || o.dev)) AS c, COUNT(*) AS devices FROM opens o LEFT JOIN who w ON w.dev = o.dev WHERE o.day = ?`, today);
  const days = await all(`SELECT e.day AS day, COUNT(DISTINCT COALESCE(w.pkey, 'dev:' || e.dev)) AS devs, COUNT(*) AS quizzes, SUM(e.n) AS n, SUM(e.s) AS s FROM events e LEFT JOIN who w ON w.dev = e.dev WHERE e.day >= ? GROUP BY e.day`, from);
  const opens = await all(`SELECT o.day AS day, COUNT(DISTINCT COALESCE(w.pkey, 'dev:' || o.dev)) AS c FROM opens o LEFT JOIN who w ON w.dev = o.dev WHERE o.day >= ? GROUP BY o.day`, from);
  const parts = await all('SELECT part, COUNT(*) AS quizzes, SUM(n) AS n, SUM(s) AS s FROM events WHERE day = ? GROUP BY part', today);
  const mocks = await all(`SELECT part, COUNT(*) AS c, SUM(CASE WHEN s * 100 >= n * 75 THEN 1 ELSE 0 END) AS pass FROM events WHERE mode = 'real' AND day >= ? GROUP BY part`, from);
  const hours = await all(`SELECT CAST(((ts / 3600000) + 9) % 24 AS INTEGER) AS h, COUNT(*) AS c FROM events WHERE day >= ? GROUP BY h`, jstDay(now - 6 * 864e5));
  const recent = await all('SELECT ts, part, mode, n, s FROM events ORDER BY ts DESC LIMIT 25');
  const devs7 = await one(`SELECT COUNT(DISTINCT COALESCE(w.pkey, 'dev:' || o.dev)) AS c FROM opens o LEFT JOIN who w ON w.dev = o.dev WHERE o.day >= ?`, jstDay(now - 6 * 864e5));
  // people: devices with the same nickname are merged
  const people = await all(`SELECT COALESCE(w.pkey, 'dev:' || p.dev) AS k, MAX(n.name) AS name, COUNT(DISTINCT p.dev) AS devices, MAX(p.ts) AS last, MAX(p.part) AS part,
      (SELECT COALESCE(SUM(e.n),0) FROM events e LEFT JOIN who w2 ON w2.dev = e.dev WHERE COALESCE(w2.pkey, 'dev:' || e.dev) = COALESCE(w.pkey, 'dev:' || p.dev) AND e.day = ?) AS n_today,
      (SELECT COALESCE(SUM(e.s),0) FROM events e LEFT JOIN who w2 ON w2.dev = e.dev WHERE COALESCE(w2.pkey, 'dev:' || e.dev) = COALESCE(w.pkey, 'dev:' || p.dev) AND e.day = ?) AS s_today,
      (SELECT COALESCE(SUM(e.n),0) FROM events e LEFT JOIN who w2 ON w2.dev = e.dev WHERE COALESCE(w2.pkey, 'dev:' || e.dev) = COALESCE(w.pkey, 'dev:' || p.dev) AND e.day >= ?) AS n_7,
      (SELECT COALESCE(SUM(e.n),0) FROM events e LEFT JOIN who w2 ON w2.dev = e.dev WHERE COALESCE(w2.pkey, 'dev:' || e.dev) = COALESCE(w.pkey, 'dev:' || p.dev)) AS n_all,
      (SELECT COALESCE(SUM(e.s),0) FROM events e LEFT JOIN who w2 ON w2.dev = e.dev WHERE COALESCE(w2.pkey, 'dev:' || e.dev) = COALESCE(w.pkey, 'dev:' || p.dev)) AS s_all,
      (SELECT e.s * 100 / e.n FROM events e LEFT JOIN who w2 ON w2.dev = e.dev WHERE COALESCE(w2.pkey, 'dev:' || e.dev) = COALESCE(w.pkey, 'dev:' || p.dev) AND e.mode = 'real' ORDER BY e.ts DESC LIMIT 1) AS mock_pct,
      (SELECT e.part FROM events e LEFT JOIN who w2 ON w2.dev = e.dev WHERE COALESCE(w2.pkey, 'dev:' || e.dev) = COALESCE(w.pkey, 'dev:' || p.dev) AND e.mode = 'real' ORDER BY e.ts DESC LIMIT 1) AS mock_part,
      (SELECT a.img FROM avatars a LEFT JOIN who w3 ON w3.dev = a.dev WHERE COALESCE(w3.pkey, 'dev:' || a.dev) = COALESCE(w.pkey, 'dev:' || p.dev) ORDER BY a.updated DESC LIMIT 1) AS avatar
    FROM pings p LEFT JOIN names n ON n.dev = p.dev LEFT JOIN who w ON w.dev = p.dev GROUP BY k ORDER BY last DESC LIMIT 300`, today, today, jstDay(now - 6 * 864e5));
  const recentNamed = await all('SELECT e.ts, e.part, e.mode, e.n, e.s, n.name FROM events e LEFT JOIN names n ON n.dev = e.dev ORDER BY e.ts DESC LIMIT 25');
  return json({ now, today, live, t, opensToday: opensToday.c, devicesToday: opensToday.devices, days, opens, parts, mocks, hours, recent: recentNamed, devs7: devs7.c, people });
}

// one person (all devices that share the nickname)
// one person on several devices (phone + tablet): per category keep the device that practised it most
function mergeSums(rows) {
  let sum = null;
  rows.forEach(r => { let d; try { d = JSON.parse(r.data); } catch (e) { return; }
    if (!d || !Array.isArray(d.cats)) return;
    if (!sum) { sum = { data: d, updated: r.updated }; return; }
    const m = {}; sum.data.cats.forEach(c => m[c.part + '|' + c.id] = c);
    (d.cats || []).forEach(c => { const k = c.part + '|' + c.id, o = m[k];
      if (!o) { sum.data.cats.push(c); return; }
      if ((c.t || 0) > (o.t || 0)) { o.c = c.c; o.t = c.t; o.wrong = c.wrong; }
      o.done = Math.max(o.done || 0, c.done || 0); o.tried = Math.max(o.tried == null ? o.done : o.tried, c.tried == null ? c.done : c.tried); });
    if (!sum.data.exam && d.exam) sum.data.exam = d.exam; });
  return sum;
}
// month rows: activity from the quiz results of that month + the per-category snapshot at the end of that month
const MONTH_SQL = (where) => `SELECT substr(day, 1, 7) AS m, part, COUNT(*) AS quizzes, SUM(n) AS n, SUM(s) AS s, COUNT(DISTINCT day) AS days,
  SUM(mode = 'real') AS mocks, AVG(CASE WHEN mode = 'real' THEN s * 100.0 / n END) AS mockAvg, MAX(CASE WHEN mode = 'real' THEN s * 100.0 / n END) AS mockBest
  FROM events WHERE ${where} GROUP BY m, part`;
function buildMonths(evRows, dayRows, snapRows) {
  const M = {};
  const get = m => M[m] || (M[m] = { m, days: 0, quizzes: 0, n: 0, s: 0, mocks: 0, mockSum: 0, mockBest: null, parts: {} });
  evRows.forEach(r => { const o = get(r.m), p = r.part || 'other';
    o.quizzes += r.quizzes; o.n += r.n || 0; o.s += r.s || 0; o.mocks += r.mocks || 0;
    if (r.mocks) { o.mockSum += r.mockAvg * r.mocks; o.mockBest = Math.max(o.mockBest || 0, r.mockBest); }
    o.parts[p] = { quizzes: r.quizzes, n: r.n || 0, s: r.s || 0, mocks: r.mocks || 0, mockAvg: r.mocks ? Math.round(r.mockAvg) : null, mockBest: r.mocks ? Math.round(r.mockBest) : null }; });
  dayRows.forEach(r => { get(r.m).days = r.days; });
  const byMonth = {}; snapRows.forEach(r => (byMonth[r.month] = byMonth[r.month] || []).push(r));
  Object.keys(byMonth).forEach(m => { const sm = mergeSums(byMonth[m]); if (!sm) return; const o = get(m);
    o.cats = sm.data.cats.map(c => ({ part: c.part, id: c.id, th: c.th, c: c.c || 0, t: c.t || 0, tried: c.tried == null ? c.done || 0 : c.tried, total: c.total || 0 }));
    ['gakka', 'jitsugi', 'life'].forEach(p => { const cs = o.cats.filter(c => c.part === p); if (!cs.length) return;
      const pp = o.parts[p] || (o.parts[p] = { quizzes: 0, n: 0, s: 0, mocks: 0, mockAvg: null, mockBest: null });
      pp.tried = cs.reduce((a, c) => a + c.tried, 0); pp.total = cs.reduce((a, c) => a + c.total, 0); }); });
  return Object.values(M).map(o => { o.mockAvg = o.mocks ? Math.round(o.mockSum / o.mocks) : null; o.mockBest = o.mockBest == null ? null : Math.round(o.mockBest); delete o.mockSum; return o; })
    .sort((a, b) => a.m < b.m ? -1 : 1);
}
async function personMonths(env, devs) {
  const qs = devs.map(() => '?').join(',');
  const ev = (await env.DB.prepare(MONTH_SQL(`dev IN (${qs})`)).bind(...devs).all()).results;
  const dd = (await env.DB.prepare(`SELECT substr(day, 1, 7) AS m, COUNT(DISTINCT day) AS days FROM events WHERE dev IN (${qs}) GROUP BY m`).bind(...devs).all()).results;
  const sn = (await env.DB.prepare(`SELECT month, data, updated FROM monthly WHERE dev IN (${qs}) ORDER BY updated DESC`).bind(...devs).all()).results;
  return buildMonths(ev, dd, sn);
}
// everyone's summary for one month (and the month before, to show growth) — for the table + CSV download
async function monthly(env, m) {
  const months = (await env.DB.prepare("SELECT DISTINCT substr(day, 1, 7) AS m FROM events ORDER BY m DESC").all()).results.map(r => r.m);
  if (!/^\d{4}-\d{2}$/.test(m || '')) m = months[0] || jstDay(Date.now()).slice(0, 7);
  const d = new Date(m + '-01T00:00:00Z'); d.setUTCMonth(d.getUTCMonth() - 1); const pm = d.toISOString().slice(0, 7);
  const KEY = "COALESCE(w.pkey, 'dev:' || e.dev)";
  const people = (await env.DB.prepare(`SELECT DISTINCT ${KEY} AS k FROM events e LEFT JOIN who w ON w.dev = e.dev WHERE substr(e.day, 1, 7) IN (?, ?)`).bind(m, pm).all()).results.map(r => r.k);
  const rows = [];
  for (const k of people) {
    const devs = (await env.DB.prepare(`SELECT d.dev FROM (SELECT dev FROM pings UNION SELECT dev FROM events) d LEFT JOIN who w ON w.dev = d.dev WHERE COALESCE(w.pkey, 'dev:' || d.dev) = ?`).bind(k).all()).results.map(r => r.dev);
    if (!devs.length) continue;
    const qs = devs.map(() => '?').join(',');
    const ms = await personMonths(env, devs);
    const cur = ms.find(x => x.m === m), prev = ms.find(x => x.m === pm);
    if (!cur && !prev) continue;
    const name = await env.DB.prepare(`SELECT name FROM names WHERE dev IN (${qs}) ORDER BY updated DESC LIMIT 1`).bind(...devs).first();
    rows.push({ k, name: name && name.name, cur: cur || null, prev: prev || null });
  }
  return json({ m, pm, months, rows });
}

async function person(env, k) {
  const KEY = "COALESCE(w.pkey, 'dev:' || d.dev)";
  const devs = (await env.DB.prepare(`SELECT d.dev FROM (SELECT dev FROM pings UNION SELECT dev FROM events) d LEFT JOIN who w ON w.dev = d.dev WHERE ${KEY} = ?`).bind(k).all()).results.map(r => r.dev);
  if (!devs.length) return json({ error: 'not found' }, 404);
  const qs = devs.map(() => '?').join(',');
  const now = Date.now();
  const sums = (await env.DB.prepare(`SELECT data, updated FROM summaries WHERE dev IN (${qs}) ORDER BY updated DESC`).bind(...devs).all()).results;
  const sum = mergeSums(sums);
  const name = await env.DB.prepare(`SELECT name FROM names WHERE dev IN (${qs}) ORDER BY updated DESC LIMIT 1`).bind(...devs).first();
  const av = await env.DB.prepare(`SELECT img FROM avatars WHERE dev IN (${qs}) ORDER BY updated DESC LIMIT 1`).bind(...devs).first();
  const last = await env.DB.prepare(`SELECT MAX(ts) AS ts FROM pings WHERE dev IN (${qs})`).bind(...devs).first();
  const events = (await env.DB.prepare(`SELECT ts, day, part, mode, n, s FROM events WHERE dev IN (${qs}) ORDER BY ts DESC LIMIT 300`).bind(...devs).all()).results;
  const days = (await env.DB.prepare(`SELECT day, SUM(n) AS n, SUM(s) AS s FROM events WHERE dev IN (${qs}) AND day >= ? GROUP BY day`).bind(...devs, jstDay(now - 13 * 864e5)).all()).results;
  return json({ now, today: jstDay(now), k, devices: devs.length, name: name && name.name, avatar: av && av.img, last: last && last.ts,
    summary: sum ? sum.data : null, synced: sum ? sum.updated : 0, events, days, months: await personMonths(env, devs) });
}

/* ---------- progress sync (nickname + PIN) ----------
   op 'check' {name}                 → { exists }            (no PIN: lets a new phone offer "pull your progress")
   op 'head'  {name,pin}             → { updated, dev }
   op 'load'  {name,pin}             → { data, updated }
   op 'save'  {name,pin,dev,base,data,force} → { updated } | 409 { updated } when another device saved since `base`
   5 wrong PINs → that name is locked for 15 minutes. */
const SYNC_MAX = 600000;           // a full progress copy is far below this
const PIN_FAILS_PER_NET = 20;      // wrong PINs allowed from one network per hour, across all names
async function sync(req, env) {
  let b; try { b = await req.json(); } catch (e) { return json({ ok: false }, 400); }
  const name = String(b.name || '').replace(/[<>"'`\\]/g, '').replace(/\s+/g, ' ').trim().slice(0, 24);
  const nk = name.toLowerCase(), now = Date.now();
  if (!nk) return json({ error: 'name' }, 400);
  if (await overLimit(req, env, 'sync', 300, 3600e3)) return json({ error: 'locked', until: now + 3600e3 }, 429);
  const row = await env.DB.prepare('SELECT pinh, updated, dev, fails, lock FROM sync WHERE nk = ?').bind(nk).first();
  if (b.op === 'check') return json({ exists: !!row, updated: row ? row.updated : 0 });
  if (!/^\d{4}$/.test(String(b.pin || ''))) return json({ error: 'pin' }, 400);
  if (row && row.lock > now) return json({ error: 'locked', until: row.lock }, 429);
  // reserve one attempt atomically before checking the PIN (so a burst of parallel requests is counted too);
  // a correct PIN gives the attempt back below
  const thrKey = 'pinfail:' + (await sha256('jac-thr|' + (req.headers.get('cf-connecting-ip') || ''))).slice(0, 20);
  if (await overLimit(req, env, 'pinfail', PIN_FAILS_PER_NET, 3600e3)) return json({ error: 'locked', until: now + 3600e3 }, 429);
  const pinh = await sha256('jac-sync|' + nk + '|' + b.pin);
  if (!row || row.pinh === pinh) await env.DB.prepare('UPDATE throttle SET n = MAX(n - 1, 0) WHERE k = ?').bind(thrKey).run();
  if (row && row.pinh !== pinh) {
    // count in one atomic statement so requests sent at the same moment can't all see the old count
    const r = await env.DB.prepare(`UPDATE sync SET fails = CASE WHEN fails + 1 >= 5 THEN 0 ELSE fails + 1 END,
        lock = CASE WHEN fails + 1 >= 5 THEN ? ELSE lock END WHERE nk = ? RETURNING fails, lock`).bind(now + 15 * 60e3, nk).first();
    const locked = r && r.lock > now;
    return json({ error: 'wrongpin', left: locked ? 0 : 5 - (r ? r.fails : 0) }, 403);
  }
  if (row && row.fails) await env.DB.prepare('UPDATE sync SET fails = 0 WHERE nk = ?').bind(nk).run();
  if (b.op === 'head') return json({ exists: !!row, updated: row ? row.updated : 0, same: !!row && row.dev === b.dev });
  if (b.op === 'load') {
    if (!row) return json({ error: 'none' }, 404);
    const r = await env.DB.prepare('SELECT data, updated FROM sync WHERE nk = ?').bind(nk).first();
    return json({ data: r.data, updated: r.updated });
  }
  if (b.op === 'save') {
    if (!devOk(b.dev) || typeof b.data !== 'string' || b.data.length > SYNC_MAX) return json({ error: 'data' }, 400);
    let d; try { d = JSON.parse(b.data); } catch (e) { return json({ error: 'data' }, 400); }
    if (!d || d.app !== 'jac-exam' || !d.keys || typeof d.keys !== 'object') return json({ error: 'data' }, 400);
    if (row && !b.force && row.updated !== Number(b.base) && row.dev !== b.dev) return json({ error: 'newer', updated: row.updated }, 409);
    if (!row && await overLimit(req, env, 'newname', 10, 864e5)) return json({ error: 'locked', until: now + 864e5 }, 429);
    await env.DB.prepare('INSERT INTO sync (nk, pinh, data, updated, dev) VALUES (?, ?, ?, ?, ?) ON CONFLICT(nk) DO UPDATE SET data = excluded.data, updated = excluded.updated, dev = excluded.dev')
      .bind(nk, pinh, b.data, now, b.dev).run();
    return json({ updated: now, created: !row });
  }
  return json({ error: 'op' }, 400);
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
      if (path === '/api/sync' && req.method === 'POST') return await sync(req, env);
      if (path === '/api/person' || path === '/api/monthly' || path === '/api/stats') {
        // reserve an attempt first (atomic, so parallel guesses are counted); a correct key gives it back
        if (await overLimit(req, env, 'statskey', 10, 3600e3)) return json({ error: 'locked' }, 429);
        if (!(await keyOk(req, env))) return json({ error: 'key' }, 401);
        const thrKey = 'statskey:' + (await sha256('jac-thr|' + (req.headers.get('cf-connecting-ip') || ''))).slice(0, 20);
        await env.DB.prepare('UPDATE throttle SET n = MAX(n - 1, 0) WHERE k = ?').bind(thrKey).run();
        const q = new URL(req.url).searchParams;
        if (path === '/api/person') return await person(env, q.get('k') || '');
        if (path === '/api/monthly') return await monthly(env, q.get('m') || '');
        return await stats(env);
      }
      return json({ error: 'not found' }, 404);
    } catch (e) { console.error(e); return json({ error: 'server' }, 500); }
  }
};
