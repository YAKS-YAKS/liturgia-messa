// Cache hors ligne. Changer la version pour forcer la mise à jour.
const NOM_CACHE = "lumen-v1";
const FICHIERS = ["./", "./index.html", "./style.css", "./app.js", "./manifest.json",
  "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png", "./data/documents/index.json"];

self.addEventListener("install", e => {
  // addAll tolérant : l'index du corpus peut manquer tant qu'il n'a pas été ajouté.
  e.waitUntil(caches.open(NOM_CACHE).then(c =>
    Promise.all(FICHIERS.map(f => c.add(f).catch(() => null)))));
  self.skipWaiting();
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ns => Promise.all(ns.filter(n => n !== NOM_CACHE).map(n => caches.delete(n))))
    .then(() => self.clients.claim()));
});

// Fichiers de l'app et corpus : réseau d'abord (contenu à jour), cache en secours.
// Les appels aux API d'IA (autre origine) ne passent jamais par le cache.
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  if (new URL(e.request.url).origin !== self.location.origin) return;
  e.respondWith(
    fetch(e.request).then(r => {
      if (r.ok) { const copie = r.clone(); caches.open(NOM_CACHE).then(c => c.put(e.request, copie)); }
      return r;
    }).catch(() => caches.match(e.request, { ignoreSearch: true }))
  );
});
