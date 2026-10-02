/* Raupenbuch Service Worker – offline-first.
   Bei jeder Änderung an einer Datei VERSION erhöhen, dann lädt die App die neue Version. */
const VERSION = "rb-5.0.0";
const FILES = [
  "./", "index.html", "manifest.webmanifest",
  "icon-192.png", "icon-512.png", "icon-maskable.png",
  "jspdf.umd.min.js", "qrcode.js", "jsQR.js",
  "ibm-plex-sans-latin-400-normal.woff2", "ibm-plex-sans-latin-500-normal.woff2", "ibm-plex-sans-latin-600-normal.woff2",
  "ibm-plex-mono-latin-400-normal.woff2", "ibm-plex-mono-latin-500-normal.woff2",
  "spectral-latin-600-normal.woff2", "spectral-latin-400-italic.woff2", "spectral-latin-600-italic.woff2"
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(FILES.map(f => new Request(f, {cache: "reload"})))));
});

self.addEventListener("activate", e => {
  e.waitUntil((async () => {
    for(const k of await caches.keys()) if(k !== VERSION) await caches.delete(k);
    await self.clients.claim();
  })());
});

self.addEventListener("message", e => { if(e.data === "skipWaiting") self.skipWaiting(); });

self.addEventListener("fetch", e => {
  const req = e.request;
  if(req.method !== "GET") return;
  const url = new URL(req.url);
  if(url.origin !== location.origin) return;
  // Navigation auf die App (…/ oder …/index.html): App-Seite aus dem Cache (offline-first)
  if(req.mode === "navigate" && (url.pathname.endsWith("/") || url.pathname.endsWith("/index.html"))){
    e.respondWith(caches.match("index.html").then(r => r || fetch(req)));
    return;
  }
  e.respondWith(caches.match(req, {ignoreSearch: true}).then(r => r || fetch(req).then(res => {
    if(res.ok && res.type === "basic"){ const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
    return res;
  })));
});
