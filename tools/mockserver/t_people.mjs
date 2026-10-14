const B = 'http://localhost:8790', K = { 'x-key': process.env.STATS_KEY };
const iphone = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1';
const line = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Safari Line/14.0';
const ping = (dev, ua, ip, scr, name = '', ev = []) => fetch(B + '/api/ping', { method: 'POST', headers: { 'content-type': 'application/json', 'user-agent': ua, 'cf-connecting-ip': ip }, body: JSON.stringify({ dev, name, part: 'gakka', events: ev, scr }) });
const e = r => [{ rid: r, ts: Date.now(), part: 'gakka', mode: 'mini', n: 10, s: 8 }];
await ping('safari0001', iphone, '1.2.3.4', '393x852@3', '', e('a1'));   // one person: Safari + home screen + LINE browser
await ping('homescr001', iphone, '1.2.3.4', '393x852@3');
await ping('linebrw001', line, '1.2.3.4', '393x852@3');
await ping('other00001', iphone, '5.6.7.8', '430x932@3', '', e('b1'));   // another person
await ping('named00001', iphone, '9.9.9.9', '393x852@3', 'ชายอาม', e('c1'));   // named, two devices
await ping('named00002', 'Mozilla/5.0 (iPad; CPU OS 18_5 like Mac OS X)', '9.9.9.9', '820x1180@2', 'ชายอาม');
const d = await (await fetch(B + '/api/stats', { headers: K })).json();
if (d.error) { console.log(d); process.exit(1); }
console.log('open people', d.opensToday, 'devices', d.devicesToday, '| quiz people', d.t.devs, '| 7d', d.devs7, '| live', JSON.stringify(d.live));
console.log(d.people.map(p => [p.k.slice(0, 14), p.name, p.devices, p.n_today]));
const pk = d.people.find(p => p.k.startsWith('fp:') && p.devices === 3);
const pr = await (await fetch(B + '/api/person?k=' + encodeURIComponent(pk.k), { headers: K })).json(); console.log('person devices', pr.devices, 'events', pr.events.length);
const nk = d.people.find(p => p.name);
const pn = await (await fetch(B + '/api/person?k=' + encodeURIComponent(nk.k), { headers: K })).json(); console.log('named person devices', pn.devices, pn.name);
