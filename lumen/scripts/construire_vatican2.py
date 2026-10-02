#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Construit le corpus Vatican II : télécharge les pages françaises de vatican.va,
les analyse (vatican2_parser) et écrit data/documents/{id}.json + data/documents/index.json.

Usage :
  python3 scripts/construire_vatican2.py [--seulement id1,id2]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vatican2_parser import analyser_page  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_RAW = os.path.join(RACINE, "data", "raw")
DOSSIER_DOCS = os.path.join(RACINE, "data", "documents")

BASE = "https://www.vatican.va/archive/hist_councils/ii_vatican_council/documents/"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Lumen/1.0"}

DOCUMENTS = [
    # ---------------- Constitutions ----------------
    dict(id="sacrosanctum-concilium", url=BASE + "vat-ii_const_19631204_sacrosanctum-concilium_fr.html",
         titre="Sacrosanctum Concilium", sous_titre="Constitution sur la sainte liturgie",
         type="constitution", categorie="Vatican II", date="1963-12-04",
         promulgateur="Concile Vatican II — Paul VI",
         resume="La réforme liturgique : participation active, langue vernaculaire, sacrements, année liturgique.",
         prologue=True, titres_inline={123: "Les styles artistiques"},
         mots_cles=["liturgie", "messe", "eucharistie", "sacrements", "participation active",
                    "langue vernaculaire", "année liturgique", "bréviaire", "musique sacrée",
                    "art sacré", "réforme liturgique", "mystère pascal"]),
    dict(id="lumen-gentium", url=BASE + "vat-ii_const_19641121_lumen-gentium_fr.html",
         titre="Lumen Gentium", sous_titre="Constitution dogmatique sur l'Église",
         type="constitution", categorie="Vatican II", date="1964-11-21",
         promulgateur="Concile Vatican II — Paul VI",
         resume="Le mystère de l'Église : peuple de Dieu, collégialité épiscopale, laïcs, sainteté, Marie.",
         notification_apres=69, notification_motif="ont été faites aux Pères",
         mots_cles=["Église", "peuple de Dieu", "corps du Christ", "épiscopat", "collégialité",
                    "primauté", "pape", "laïcs", "sacerdoce commun", "sainteté", "religieux",
                    "eschatologie", "Vierge Marie", "sacrement", "infaillibilité"]),
    dict(id="dei-verbum", url=BASE + "vat-ii_const_19651118_dei-verbum_fr.html",
         titre="Dei Verbum", sous_titre="Constitution dogmatique sur la Révélation divine",
         type="constitution", categorie="Vatican II", date="1965-11-18",
         promulgateur="Concile Vatican II — Paul VI",
         resume="Révélation, Écriture et Tradition, inspiration, interprétation de la Bible.",
         prologue=True,
         mots_cles=["Révélation", "Écriture", "Tradition", "inspiration", "exégèse", "canon",
                    "Ancien Testament", "Nouveau Testament", "Parole de Dieu", "magistère",
                    "interprétation", "prophètes", "évangiles"]),
    dict(id="gaudium-et-spes", url=BASE + "vat-ii_const_19651207_gaudium-et-spes_fr.html",
         titre="Gaudium et Spes", sous_titre="Constitution pastorale sur l'Église dans le monde de ce temps",
         type="constitution", categorie="Vatican II", date="1965-12-07",
         promulgateur="Concile Vatican II — Paul VI",
         resume="L'Église face au monde moderne : dignité humaine, culture, économie, famille, paix.",
         prologue=True,
         parties=[{"avant": 11, "titre": "Première partie : L'Église et la vocation humaine"},
                  {"avant": 46, "titre": "Deuxième partie : De quelques problèmes plus urgents"}],
         titres_inline={7: "Changements psychologiques, moraux, religieux",
                        17: "Grandeur de la liberté",
                        28: "Respect et amour des adversaires",
                        31: "Responsabilité et participation"},
         mots_cles=["monde moderne", "dignité humaine", "athéisme", "culture", "communauté humaine",
                    "économie", "famille", "mariage", "politique", "paix", "guerre", "progrès",
                    "dialogue", "liberté", "conscience"]),
    # ---------------- Décrets ----------------
    dict(id="inter-mirifica", url=BASE + "vat-ii_decree_19631204_inter-mirifica_fr.html",
         titre="Inter Mirifica", sous_titre="Décret sur les moyens de communication sociale",
         type="decret", categorie="Vatican II", date="1963-12-04",
         promulgateur="Concile Vatican II — Paul VI",
         resume="Presse, cinéma, radio, télévision : droits, devoirs, formation, déontologie.",
         titres_inline={23: "L’instruction pastorale", 24: "Exhortation finale"},
         mots_cles=["médias", "presse", "cinéma", "radio", "télévision", "communication sociale",
                    "opinion publique", "déontologie", "information", "publicité"]),
    dict(id="orientalium-ecclesiarum", url=BASE + "vat-ii_decree_19641121_orientalium-ecclesiarum_fr.html",
         titre="Orientalium Ecclesiarum", sous_titre="Décret sur les Églises orientales catholiques",
         type="decret", categorie="Vatican II", date="1964-11-21",
         promulgateur="Concile Vatican II — Paul VI",
         resume="Dignité des rites orientaux, patriarcats, discipline propre, communion sacramentelle.",
         titres_centres=True,
         mots_cles=["Églises orientales", "rites", "patriarcats", "œcuménisme", "discipline orientale",
                    "intercommunion", "communio in sacris", "tradition"]),
    dict(id="unitatis-redintegratio", url=BASE + "vat-ii_decree_19641121_unitatis-redintegratio_fr.html",
         titre="Unitatis Redintegratio", sous_titre="Décret sur l'œcuménisme",
         type="decret", categorie="Vatican II", date="1964-11-21",
         promulgateur="Concile Vatican II — Paul VI",
         resume="Le mouvement œcuménique : principes catholiques et exercice pratique du dialogue.",
         mots_cles=["œcuménisme", "unité des chrétiens", "dialogue", "Églises séparées", "Orient",
                    "protestantisme", "conversion du cœur", "hiérarchie des vérités", "réforme"]),
    dict(id="christus-dominus", url=BASE + "vat-ii_decree_19651028_christus-dominus_fr.html",
         titre="Christus Dominus", sous_titre="Décret sur la charge pastorale des évêques dans l'Église",
         type="decret", categorie="Vatican II", date="1965-10-28",
         promulgateur="Concile Vatican II — Paul VI",
         resume="Évêques, diocèses, conférences épiscopales, curés, coopération pastorale.",
         prologue=True,
         mots_cles=["évêques", "diocèse", "synode", "conférences épiscopales", "curie romaine",
                    "curés", "coopération", "réforme pastorale", "territoire"]),
    dict(id="perfectae-caritatis", url=BASE + "vat-ii_decree_19651028_perfectae-caritatis_fr.html",
         titre="Perfectae Caritatis", sous_titre="Décret sur la rénovation et l'adaptation de la vie religieuse",
         type="decret", categorie="Vatican II", date="1965-10-28",
         promulgateur="Concile Vatican II — Paul VI",
         resume="Renouveau de la vie religieuse : retour aux sources, adaptation, vœux, communautés.",
         titres_inline={25: "Conclusion"},
         mots_cles=["vie religieuse", "vœux", "renouveau", "obéissance", "pauvreté", "chasteté",
                    "communautés", "contemplation", "adaptation", "fondateurs"]),
    dict(id="optatam-totius", url=BASE + "vat-ii_decree_19651028_optatam-totius_fr.html",
         titre="Optatam Totius", sous_titre="Décret sur la formation des prêtres",
         type="decret", categorie="Vatican II", date="1965-10-28",
         promulgateur="Concile Vatican II — Paul VI",
         resume="Séminaires : formation spirituelle, intellectuelle et pastorale des futurs prêtres.",
         mots_cles=["séminaires", "formation sacerdotale", "spiritualité", "pastorale", "philosophie",
                    "théologie", "pédagogie", "vocations", "prêtres"]),
    dict(id="apostolicam-actuositatem", url=BASE + "vat-ii_decree_19651118_apostolicam-actuositatem_fr.html",
         titre="Apostolicam Actuositatem", sous_titre="Décret sur l'apostolat des laïcs",
         type="decret", categorie="Vatican II", date="1965-11-18",
         promulgateur="Concile Vatican II — Paul VI",
         resume="La vocation apostolique des laïcs dans l'Église et dans le monde.",
         section_finale={"apres": 32, "numero": 33, "titre": "Conclusion",
                         "motif": "Que les jeunes réalisent bien"},
         mots_cles=["laïcs", "apostolat", "Action catholique", "charismes", "monde", "témoignage",
                    "engagement", "associations", "sacerdoce commun"]),
    dict(id="presbyterorum-ordinis", url=BASE + "vat-ii_decree_19651207_presbyterorum-ordinis_fr.html",
         titre="Presbyterorum Ordinis", sous_titre="Décret sur le ministère et la vie des prêtres",
         type="decret", categorie="Vatican II", date="1965-12-07",
         promulgateur="Concile Vatican II — Paul VI",
         resume="Le presbytérat : ministère, relations, exigences spirituelles et matérielles.",
         prologue=True,
         mots_cles=["prêtres", "presbytérat", "eucharistie", "célibat", "obéissance", "pauvreté",
                    "ministère", "spiritualité sacerdotale", "conseil presbytéral"]),
    dict(id="ad-gentes", url=BASE + "vat-ii_decree_19651207_ad-gentes_fr.html",
         titre="Ad Gentes", sous_titre="Décret sur l'activité missionnaire de l'Église",
         type="decret", categorie="Vatican II", date="1965-12-07",
         promulgateur="Concile Vatican II — Paul VI",
         resume="La mission : fondements théologiques, évangélisation, jeunes Églises, coopération.",
         titre_chapitre_initial="Introduction",
         titres_inline={11: "Le témoignage de la vie et le dialogue", 42: ""},
         mots_cles=["mission", "évangélisation", "inculturation", "jeunes Églises", "catéchuménat",
                    "missionnaires", "dialogue", "salut des non-chrétiens", "Trinité"]),
    # ---------------- Déclarations ----------------
    dict(id="gravissimum-educationis", url=BASE + "vat-ii_decl_19651028_gravissimum-educationis_fr.html",
         titre="Gravissimum Educationis", sous_titre="Déclaration sur l'éducation chrétienne",
         type="declaration", categorie="Vatican II", date="1965-10-28",
         promulgateur="Concile Vatican II — Paul VI",
         resume="Droit universel à l'éducation, écoles catholiques, universités, catéchèse.",
         mots_cles=["éducation", "écoles", "universités", "catéchèse", "famille",
                    "liberté de l'enseignement", "maîtres", "dignité humaine"]),
    dict(id="nostra-aetate", url=BASE + "vat-ii_decl_19651028_nostra-aetate_fr.html",
         titre="Nostra Aetate", sous_titre="Déclaration sur les relations de l'Église avec les religions non chrétiennes",
         type="declaration", categorie="Vatican II", date="1965-10-28",
         promulgateur="Concile Vatican II — Paul VI",
         resume="Hindouisme, bouddhisme, islam, judaïsme : estime, dialogue, rejet de l'antisémitisme.",
         mots_cles=["religions non chrétiennes", "judaïsme", "islam", "hindouisme", "bouddhisme",
                    "dialogue interreligieux", "antisémitisme", "fraternité", "déicide"]),
    dict(id="dignitatis-humanae", url=BASE + "vat-ii_decl_19651207_dignitatis-humanae_fr.html",
         titre="Dignitatis Humanae", sous_titre="Déclaration sur la liberté religieuse",
         type="declaration", categorie="Vatican II", date="1965-12-07",
         promulgateur="Concile Vatican II — Paul VI",
         resume="La liberté religieuse fondée sur la dignité de la personne et la conscience.",
         prologue=True,
         mots_cles=["liberté religieuse", "conscience", "État", "tolérance", "dignité",
                    "droit civil", "laïcité", "immunité de contrainte"]),
]


def telecharger(meta: dict, forcer: bool = False) -> str:
    chemin = os.path.join(DOSSIER_RAW, meta["id"] + ".html")
    if os.path.exists(chemin) and not forcer:
        return chemin
    print(f"  ↓ téléchargement : {meta['url']}")
    requete = urllib.request.Request(meta["url"], headers=UA)
    with urllib.request.urlopen(requete, timeout=90) as reponse:
        octets = reponse.read()
    # encodage déclaré dans la page
    tete = octets[:3000].decode("ascii", errors="ignore")
    m = re.search(r"charset=([\w-]+)", tete, re.I)
    enc = (m.group(1) if m else "utf-8").lower()
    if enc in ("iso-8859-1", "latin1", "windows-1252"):
        texte = octets.decode("iso-8859-1", errors="replace")
    else:
        texte = octets.decode("utf-8", errors="replace")
    with open(chemin, "w", encoding="utf-8") as fh:
        fh.write(texte)
    return chemin


def construire(meta: dict, forcer: bool = False):
    chemin_raw = telecharger(meta, forcer)
    with open(chemin_raw, encoding="utf-8") as fh:
        html_brut = fh.read()
    document = analyser_page(html_brut, meta)
    chemin_doc = os.path.join(DOSSIER_DOCS, meta["id"] + ".json")
    with open(chemin_doc, "w", encoding="utf-8") as fh:
        json.dump(document, fh, ensure_ascii=False, indent=1)
    nb_sections = sum(len(c["sections"]) for c in document["chapitres"])
    print(f"  ✓ {meta['id']:<26} {len(document['chapitres']):>2} chap.  "
          f"{nb_sections:>3} sections  {document['nb_mots']:>6} mots  {len(document['notes']):>3} notes")
    return document


def construire_index():
    index = []
    for meta in DOCUMENTS:
        chemin = os.path.join(DOSSIER_DOCS, meta["id"] + ".json")
        with open(chemin, encoding="utf-8") as fh:
            doc = json.load(fh)
        index.append({
            "id": doc["id"], "titre": doc["titre"], "sous_titre": doc["sous_titre"],
            "type": doc["type"], "categorie": doc["categorie"], "date": doc["date"],
            "promulgateur": doc["promulgateur"], "resume": meta.get("resume", ""),
            "source": doc["source"], "mots_cles": meta.get("mots_cles", []),
            "nb_chapitres": len(doc["chapitres"]),
            "nb_sections": sum(len(c["sections"]) for c in doc["chapitres"]),
            "nb_mots": doc["nb_mots"], "nb_notes": len(doc["notes"]),
        })
    with open(os.path.join(DOSSIER_DOCS, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=1)
    print(f"\nIndex écrit : {len(index)} documents.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seulement", help="ids séparés par des virgules")
    ap.add_argument("--forcer", action="store_true", help="retélécharger")
    args = ap.parse_args()
    os.makedirs(DOSSIER_RAW, exist_ok=True)
    os.makedirs(DOSSIER_DOCS, exist_ok=True)

    selection = None
    if args.seulement:
        selection = set(args.seulement.split(","))
    docs = [d for d in DOCUMENTS if selection is None or d["id"] in selection]
    for meta in docs:
        try:
            construire(meta, args.forcer)
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ {meta['id']} : ERREUR {e}")
        time.sleep(0.4)
    construire_index()


if __name__ == "__main__":
    main()
