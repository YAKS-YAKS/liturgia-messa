/* ============================================================
   LOGIQUE DE L'APPLICATION « Ordinario della Messa »
   Trois fonctionnalités :
   1. Navigation entre les 5 parties de la messe
   2. Taille du texte (boutons A− et A+)
   3. Mode nuit (bouton 🌙)
   ============================================================ */

// On récupère les éléments de la page dont on a besoin
const liensNav = document.querySelectorAll(".lien-nav");   // boutons du menu
const sections = document.querySelectorAll(".section");    // les 5 parties
const btnPrecedente = document.getElementById("btn-precedente");
const btnSuccessivo = document.getElementById("btn-successivo");
const btnMenu = document.getElementById("btn-menu");
const menu = document.getElementById("menu");

// L'ordre des sections, pour les boutons Précédent / Suivant
const ordre = ["introduzione", "parola", "eucaristica", "comunione", "conclusione"];
let indexActuel = 0; // 0 = première section (Riti di Introduzione)

/* ---------- 1. NAVIGATION ---------- */

// Affiche la section demandée et cache les autres
function afficherSection(id) {
  indexActuel = ordre.indexOf(id);

  // Cacher toutes les sections, puis montrer la bonne
  sections.forEach(function (section) {
    section.classList.toggle("visible", section.id === id);
  });

  // Mettre en évidence le bon bouton du menu
  liensNav.forEach(function (lien) {
    lien.classList.toggle("actif", lien.dataset.section === id);
  });

  // Griser Précédent sur la 1ère section, Suivant sur la dernière
  btnPrecedente.disabled = (indexActuel === 0);
  btnSuccessivo.disabled = (indexActuel === ordre.length - 1);

  // Remonter en haut de la page
  window.scrollTo({ top: 0, behavior: "smooth" });

  // Sur téléphone : refermer le menu après un clic
  menu.classList.remove("ouvert");
}

// Quand on clique sur un bouton du menu
liensNav.forEach(function (lien) {
  lien.addEventListener("click", function () {
    afficherSection(lien.dataset.section);
  });
});

// Boutons Précédent / Suivant
btnPrecedente.addEventListener("click", function () {
  if (indexActuel > 0) {
    afficherSection(ordre[indexActuel - 1]);
  }
});

btnSuccessivo.addEventListener("click", function () {
  if (indexActuel < ordre.length - 1) {
    afficherSection(ordre[indexActuel + 1]);
  }
});

// Bouton ☰ : ouvrir / fermer le menu sur téléphone
btnMenu.addEventListener("click", function () {
  menu.classList.toggle("ouvert");
});

/* ---------- 2. TAILLE DU TEXTE ---------- */

let tailleTexte = 18; // taille de départ, en pixels

function appliquerTaille() {
  // On modifie la variable CSS --taille-texte définie dans style.css
  document.documentElement.style.setProperty("--taille-texte", tailleTexte + "px");
}

document.getElementById("btn-plus").addEventListener("click", function () {
  if (tailleTexte < 30) {
    tailleTexte += 2;
    appliquerTaille();
  }
});

document.getElementById("btn-moins").addEventListener("click", function () {
  if (tailleTexte > 12) {
    tailleTexte -= 2;
    appliquerTaille();
  }
});

/* ---------- 3. MODE NUIT ---------- */

document.getElementById("btn-nuit").addEventListener("click", function () {
  // Ajoute ou enlève la classe "nuit" sur <body> :
  // le CSS change alors toutes les couleurs (voir style.css)
  document.body.classList.toggle("nuit");
});

// Au démarrage : afficher la première section
afficherSection("introduzione");

/* ---------- 4. MODE HORS-LIGNE (PWA) ---------- */

// On enregistre le "service worker" (voir sw.js) : il met l'app
// en cache pour qu'elle fonctionne sans connexion internet.
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").then(function () {
    console.log("Service worker enregistré : l'app fonctionne hors-ligne.");
  }).catch(function (erreur) {
    console.log("Service worker non disponible :", erreur);
  });
}
