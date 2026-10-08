// the page is network-first (cached as './' — Cloudflare Pages redirects /index.html to /)
// index.html is network-first, so CACHE only needs a new number when images/icons change
const CACHE = 'jac-exam-v22';
const ASSETS = [
  './', './manifest.webmanifest', './icon-192.png', './icon-512.png', './icon-maskable-512.png', './apple-touch-icon.png',
  './img/s1_q01.jpg',
  './img/s1_q06.jpg',
  './img/s1_q09.jpg',
  './img/s1_q11.jpg',
  './img/s2_q02.jpg',
  './img/s2_q06.jpg',
  './img/s2_q09.jpg',
  './img/s3_q01.jpg',
  './img/s3_q02.jpg',
  './img/s3_q04.jpg',
  './img/s3_q05.jpg',
  './img/s3_q06.jpg',
  './img/s3_q07.jpg',
  './img/s3_q08.jpg',
  './img/s3_q09.jpg',
  './img/s3_q10.jpg',
  './img/s3_q11.jpg',
  './img/s3_q12.jpg',
  './img/s3_q14.jpg',
  './img/s3_q16.jpg',
  './img/s4_q02.jpg',
  './img/s4_q03.jpg',
  './img/s4_q07.jpg',
  './img/s4_q14.jpg',
  './img/jt_085.jpg',
  './img/jt_086.jpg',
  './img/jt_099.jpg',
  './img/jt_103.jpg',
  './img/s4_q16.jpg',
  './img/s5_q10.jpg',
  './img/s5_q13.jpg',
  './img/l_001.jpg',
  './img/l_002.jpg',
  './img/l_003.jpg',
  './img/l_004.jpg',
  './img/l_005.jpg',
  './img/l_006.jpg',
  './img/l_007.jpg',
  './img/l_008.jpg',
  './img/l_009.jpg',
  './img/l_010.jpg',
  './img/l_011.jpg',
  './img/l_012.jpg',
  './img/l_013.jpg',
  './img/l_014.jpg',
  './img/l_015.jpg',
  './img/l_016.jpg',
  './img/l_017.jpg',
  './img/l_018.jpg',
  './img/l_019.jpg',
  './img/l_020.jpg',
  './img/l_021.jpg',
  './img/l_022.jpg',
  './img/l_023.jpg',
  './img/l_025.jpg',
  './img/l_026.jpg',
  './img/l_110.jpg',
  './img/l2_002.jpg',
  './img/l2_003.jpg',
  './img/l2_006.jpg',
  './img/l2_009.jpg',
  './img/l2_010.jpg',
  './img/l2_014.jpg',
  './img/l2_016.jpg',
  './img/l2_018.jpg',
  './img/l2_019.jpg',
  './img/l2_021.jpg',
  './img/l2_023.jpg',
  './img/l2_035.jpg',
  './img/l2_036.jpg',
  './img/l2_037.jpg',
  './img/l2_038.jpg',
  './img/l2_039.jpg',
  './img/l2_047.jpg',
  './img/l2_054.jpg',
  './img/l2_058.jpg',
  './img/l2_061.jpg',
  './img/l2_063.jpg',
  './img/l2_066.jpg',
  './img/l2_068.jpg',
  './img/l2_072.jpg',
  './img/l2_074.jpg',
  './img/l2_075.jpg',
  './img/l2_076.jpg',
  './img/l2_084.jpg',
  './img/l2_194.jpg',
  './img/l2_087.jpg',
  './img/l2_088.jpg',
  './img/l2_089.jpg',
  './img/l2_095.jpg',
  './img/l2_096.jpg',
  './img/l2_103.jpg',
  './img/l2_108.jpg',
  './img/l2_202.jpg',
  './img/l2_208.jpg',
  './img/l2_135.jpg',
  './img/l2_137.jpg',
  './img/l2_139.jpg',
  './img/l2_142.jpg',
  './img/l2_144.jpg',
  './img/l2_146.jpg',
  './img/l2_153.jpg',
  './img/l2_155.jpg',
  './img/l2_167.jpg',
  './img/l2_173.jpg',
  './img/l2_174.jpg',
  './img/l2_182.jpg',
  './img/l2_214.jpg',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
// Result photos are not pre-cached: each one is cached the first time it is shown.
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  // The page itself: network first, so a new upload shows up without changing CACHE; cache when offline.
  if (e.request.mode === 'navigate' || e.request.url.endsWith('/index.html')) {
    e.respondWith(fetch(e.request).then(res => {
      if (res.ok && !res.redirected) { const copy = res.clone(); caches.open(CACHE).then(c => c.put('./', copy)).catch(() => {}); }
      return res;
    }).catch(() => caches.match('./')));
    return;
  }
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {
    if (res.ok || res.type === 'opaque') {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy)).catch(() => {});
    }
    return res;
  }).catch(() => e.request.mode === 'navigate' ? caches.match('./') : Response.error())));
});
