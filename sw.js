/* ============================================================
   SERVICE WORKER
   Ce petit programme tourne en arrière-plan dans le navigateur.
   Son rôle : garder une copie de tous les fichiers de l'app
   pour qu'elle fonctionne SANS connexion internet.
   ============================================================ */

// Nom du cache. Si vous modifiez l'app, changez "v1" en "v2"
// pour forcer le téléphone à recharger les nouveaux fichiers.
const NOM_CACHE = "liturgia-messa-v2";

// La liste de tous les fichiers à garder en mémoire
const FICHIERS = [
  "./",
  "./index.html",
  "./style.css",
  "./script.js",
  "./manifest.json",
  "./icon-192.png",
  "./icon-512.png",
  "./apple-touch-icon.png"
];

// À l'installation : on télécharge et stocke tous les fichiers
self.addEventListener("install", function (evenement) {
  evenement.waitUntil(
    caches.open(NOM_CACHE).then(function (cache) {
      return cache.addAll(FICHIERS);
    })
  );
  self.skipWaiting();
});

// À l'activation : on supprime les anciens caches (v1, v2...)
self.addEventListener("activate", function (evenement) {
  evenement.waitUntil(
    caches.keys().then(function (noms) {
      return Promise.all(
        noms
          .filter(function (nom) { return nom !== NOM_CACHE; })
          .map(function (nom) { return caches.delete(nom); })
      );
    })
  );
});

// À chaque requête : on sert d'abord la copie en cache,
// et si elle n'existe pas, on va la chercher sur internet.
self.addEventListener("fetch", function (evenement) {
  evenement.respondWith(
    caches.match(evenement.request).then(function (reponseCache) {
      return reponseCache || fetch(evenement.request);
    })
  );
});
