/**
 * Banco POS — Service Worker (Phase 0: PWA shell)
 *
 * Scope: /pos  (served from /pos/sw.js with Service-Worker-Allowed: /pos)
 *
 * Strategy (P0 — installable + read-resilient, NO offline writes yet):
 *   - App shell + vendored libs + static assets: CACHE-FIRST (instant load, works on flaky/no net)
 *   - /pos pages (HTML): NETWORK-FIRST, fall back to cache when offline
 *   - /api/* and /pos/refresh: NETWORK-ONLY (sales/auth still require the server in P0)
 *
 * Phases 1–2 build on this: P1 adds an IndexedDB catalog read-cache; P2 adds the
 * offline sales OUTBOX + background sync. Bump CACHE_NAME on any shell change.
 */
// The build stamp is substituted in by the /pos/sw.js route at request time (look for
// __BANCO_BUILD__). It MUST change on every deploy, because activate() deletes every cache
// whose name isn't this one — that is the only thing that evicts stale /static/ assets.
//
// It used to be a hand-typed 'v185' with a comment saying "bump on any shell change", which is
// a manual step nobody performs. Consequence, found 2026-07-31: /static/ is served CACHE-FIRST
// with no expiry, so pos-i18n.js and pos-scanner.js NEVER updated on a device that had visited
// before. A JS fix could be deployed, verified live with curl, and still not reach the till —
// which is the worst possible failure mode: it looks shipped and isn't.
const CACHE_NAME = 'banco-pos-__BANCO_BUILD__';

// The shell we want available instantly / offline. Kept small + safe (GET, same-origin).
const SHELL = [
  '/pos/scan',
  '/static/vendor/tailwind.js',
  '/static/vendor/alpine.min.js',
  '/static/vendor/html2canvas.min.js',
  '/static/pos-scanner.js',
  '/static/pos/catalog-cache.js',
  '/static/pos/icons/icon-192.png',
  '/static/pos/icons/icon-512.png',
  '/static/pos/manifest.webmanifest',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      // addAll is atomic — one miss fails install. Add individually + tolerate misses
      // so a single renamed asset can't brick the SW.
      Promise.all(SHELL.map((url) => cache.add(url).catch(() => null)))
    )
  );
  // 2026-07-13: auto-activate new workers. A stale SW from BEFORE the /pos/callback bypass was
  // trapping mobile users on the "login bounces back" bug, and BL-011's wait-for-tap meant the fix
  // never reached them (the old worker kept control). skipWaiting activates the new SW on next load
  // WITHOUT reloading an in-progress page — it only changes which worker serves future fetches. A
  // broken login is worse than a silent asset swap. The manual SKIP_WAITING message below still works.
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// BL-011: page → SW. Activate the waiting worker only when the user taps the update nudge.
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Only handle our own origin + GET. Everything else (POST sales, cross-origin) passes through.
  if (req.method !== 'GET' || url.origin !== location.origin) return;

  // Sales + auth stay live in P0 — never serve a stale sale/token from cache.
  // /pos/callback is BYPASSED so the browser follows the OAuth 302 → /pos/dashboard#token=…
  // NATIVELY: when the SW follows that redirect via fetch(), the #token FRAGMENT is dropped and
  // the dashboard bounces back to login (the "press Login twice" bug on mobile). Let the browser do it.
  if (url.pathname.startsWith('/api/') || url.pathname === '/pos/refresh' || url.pathname === '/pos/callback') return;

  // Static assets + vendored libs: cache-first, then fill the cache on first hit.
  const isStatic = url.pathname.startsWith('/static/');
  if (isStatic) {
    event.respondWith(
      caches.match(req).then((cached) =>
        cached || fetch(req).then((resp) => {
          if (resp && resp.ok) {
            const clone = resp.clone();
            caches.open(CACHE_NAME).then((c) => c.put(req, clone));
          }
          return resp;
        })
      )
    );
    return;
  }

  // /pos pages: network-first (fresh when online), fall back to cache when offline.
  //
  // THE LAST LINK OF THIS CHAIN MUST NEVER BE undefined. It used to end in
  // `caches.match('/pos/scan')`, and caches.match resolves to UNDEFINED on a miss —
  // so respondWith(undefined) handed the browser nothing and the cashier got a
  // BLANK WHITE SCREEN with the previous page's title still in the title bar.
  // Angel hit exactly that on a cold boot, 2026-09-05: full screen, pure white,
  // titled "Login - HelixPOS - Artemis Store". The x restarted Chromium and it
  // came straight back as Layla — so nothing was wrong with her session, the
  // network, or the server (curl from the tablet: 200 in 86ms). A cache miss on
  // a boot where the network was still settling was enough to show her nothing
  // at all. A white screen tells a person nothing and offers them nothing; see
  // LESSON #12. Now the chain ends in a real page that says what happened and
  // retries by itself, so the till recovers without anybody pressing anything.
  if (url.pathname === '/pos' || url.pathname.startsWith('/pos/')) {
    event.respondWith(
      fetch(req).then((resp) => {
        if (resp && resp.ok) {
          const clone = resp.clone();
          caches.open(CACHE_NAME).then((c) => c.put(req, clone));
        }
        return resp;
      }).catch(() =>
        caches.match(req)
          .then((cached) => cached || caches.match('/pos/scan'))
          .then((cached) => cached || offlinePage())
      )
    );
  }
});

// The floor under the fallback chain. Returned only when the network failed AND
// nothing at all is cached — a first boot on a cold cache, or a deploy that just
// evicted every cache (CACHE_NAME carries the build stamp). It reloads itself, so
// the ordinary case — the network is a few seconds behind the browser at boot —
// heals with nobody touching the tablet.
function offlinePage() {
  return new Response(
    '<!doctype html><html><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<title>Reconnecting - HelixPOS</title><style>' +
    'html,body{height:100%;margin:0}' +
    'body{display:flex;align-items:center;justify-content:center;' +
    'font:16px/1.5 system-ui,sans-serif;background:#f9fafb;color:#111827;' +
    '-webkit-tap-highlight-color:transparent}' +
    '.b{text-align:center;padding:2rem;max-width:26rem}' +
    'h1{font-size:1.4rem;margin:0 0 .5rem}' +
    'p{color:#4b5563;margin:.4rem 0}' +
    'button{margin-top:1.5rem;font-size:1.05rem;padding:.9rem 2rem;border:0;' +
    'border-radius:.6rem;background:#111827;color:#fff}' +
    '.s{margin-top:1.25rem;font-size:.85rem;color:#6b7280}' +
    '</style></head><body><div class="b">' +
    '<h1>Reconnecting to the till</h1>' +
    '<p>The tablet cannot reach the shop server yet. This is normal for a few ' +
    'seconds after switching on.</p>' +
    '<p><b>Nothing has been lost.</b> It will come back on its own.</p>' +
    '<button onclick="location.reload()">Try now</button>' +
    '<p class="s">Retrying automatically&hellip; ' +
    'If this is still here after a minute, check the shop wifi.</p>' +
    '</div><script>setTimeout(function(){location.reload();},4000);<\/script>' +
    '</body></html>',
    { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' } }
  );
}
