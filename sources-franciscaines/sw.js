// Cache pour un usage hors ligne. Changer la version pour forcer la mise à jour.
const NOM_CACHE = "sources-franciscaines-v2";
const FICHIERS = ["./", "./index.html", "./manifest.json", "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(NOM_CACHE).then(c => c.addAll(FICHIERS)));
  self.skipWaiting();
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(ns => Promise.all(ns.filter(n => n !== NOM_CACHE).map(n => caches.delete(n))))
      .then(() => self.clients.claim())
  );
});

// Fichiers de l'app : cache d'abord. Le reste (polices Google) : réseau, puis cache si déjà vu.
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  const local = new URL(e.request.url).origin === self.location.origin;
  if (local) {
    e.respondWith(caches.match(e.request, { ignoreSearch: true }).then(r => r || fetch(e.request)));
  } else if (/fonts\.(googleapis|gstatic)\.com/.test(e.request.url)) {
    e.respondWith(
      caches.open(NOM_CACHE).then(c =>
        fetch(e.request).then(r => { c.put(e.request, r.clone()); return r; }).catch(() => c.match(e.request))
      )
    );
  }
});
