# Lumen · Magistère

PWA statique (iPhone, hors ligne) : lecteur de textes du Magistère, recherche plein texte, et panneau IA
(analyse / commentaire / réflexion) sur un mot, un passage ou une section.

## État

- **App** : lecteur, recherche, panneau IA, réglages, hors-ligne : fait.
- **Corpus Vatican II** : **pas encore dans ce dossier.** `data/documents/` doit contenir `index.json` + un `<id>.json` par document.
  Tant qu'il est vide, l'accueil l'indique.
- **Scripts** (`scripts/`) : parseur et construction des 16 documents, repris de la session précédente.
  Ils exigent un accès à vatican.va (depuis un poste qui l'a) : `python3 scripts/construire_vatican2.py`.
  Dernières anomalies connues à vérifier après construction : chapitre fantôme dans *Orientalium Ecclesiarum*,
  section 13 d'*Optatam Totius*, paragraphe parasite `">` dans *Presbyterorum Ordinis*.
- **Hors périmètre** : motu proprio (écartés) ; écrits franciscains : voir `../sources-franciscaines/`.
  Aucune fiche d'analyse pré-rédigée : les analyses viennent de l'IA en direct.

## IA

Réglages « ⚙︎ IA » : fournisseur (Anthropic, DeepSeek, compatible OpenAI), clé, modèle.
La clé reste dans le `localStorage` du navigateur et part directement au fournisseur choisi.
Le prompt système impose : pas de complaisance, distinction texte / déduction / opinion, aucune citation inventée.
Les réponses d'IA peuvent contenir des erreurs : toujours confronter au texte officiel.

## Format d'un document

`{id, titre, sous_titre, date, source, introduction:[str], chapitres:[{numero, titre, sections:[{numero, titre, sous_titre, paragraphes:[str]}]}], annexes, notes:[str]}`

## Tester en local

`python3 -m http.server` dans ce dossier, puis http://localhost:8000.
