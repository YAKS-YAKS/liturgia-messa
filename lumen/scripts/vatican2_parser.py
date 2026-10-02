#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parseur générique des pages vatican.va (documents conciliaires, version française) — v2.

Les pages du site vatican.va utilisent plusieurs conventions de balisage :
  * en-têtes de section en <b><i>N. Titre</i></b> (avec ou sans ancre) ;
  * en-têtes fusionnés avec le texte (<a name="N.">N.</a> Texte…) — OE, OT, SC ;
  * titres de section en ligne dans le corps du texte (GS, IM, PC, SC, AG) ;
  * chapitres « CHAPITRE X : … » avec ancre, sans ancre, ou en ligne dans un paragraphe ;
  * sous-titres en chiffres romains (LG ch. VIII, CD) ou chapitres romains (OT) ;
  * mots structurels en capitales (CONCLUSION, PRÉAMBULE…) parfois en ligne ;
  * notes de bas de page en fin de page, sous deux formats (liens _ftn ou « [ N ] »).

Ce parseur balaye chaque <p> et découpe son contenu en segments (chapitre, section,
sous-titre, texte) quel que soit le style rencontré.
"""

from __future__ import annotations

import html as html_lib
import json
import re
import sys

CHIFFRES_ROMAINS = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
    "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
    "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15, "XVI": 16,
}
CHAPITRES_EN_LETTRES = {
    "PREMIER": 1, "DEUXIÈME": 2, "DEUXIEME": 2,
    "TROISIÈME": 3, "TROISIEME": 3, "QUATRIÈME": 4, "QUATRIEME": 4,
    "CINQUIÈME": 5, "CINQUIEME": 5, "SIXIÈME": 6, "SIXIEME": 6,
    "SEPTIÈME": 7, "SEPTIEME": 7, "HUITIÈME": 8, "HUITIEME": 8,
}

RE_PARAGRAPHE = re.compile(r"<p([^>]*)>(.*?)</p>", re.S)
RE_RENVOI_NOTE = re.compile(r"\[<a[^>]*_ftnref\d+[^>]*>\d+</a>\]")
RE_NOTE = re.compile(r"name=\"_ftn(\d+)\"")
RE_MARQUEUR_NOTE = re.compile(r"\[\s*\d+\s*\]")

# — segments détectés dans le texte d'un <p> —
RE_EN_TETE_BOLD = re.compile(
    r"<b>\s*<i>\s*(?:<a name=\"\d+\.?\">)?\s*(\d+)\.\s*(?:</a>)?\s*([^<]*?)</i>\s*</b>",
    re.I,
)
RE_ANCRE_NUM = re.compile(r"<a name=\"(\d+)\.?\">\s*(\d+)\.\s*")
RE_CHAPITRE = re.compile(
    r"\bCHAPITRE\s+(PREMIER|DEUXIÈME|DEUXIEME|TROISIÈME|TROISIEME|QUATRIÈME|QUATRIEME|"
    r"CINQUIÈME|CINQUIEME|SIXIÈME|SIXIEME|SEPTIÈME|SEPTIEME|HUITIÈME|HUITIEME|[IVX]{1,4})"
    r"\s*(?:</a>)?\s*:\s*",
)
RE_MOT_STRUCTURE = re.compile(
    r"\b(?:CONCLUSION|PRÉAMBULE|PREAMPLE|AVANT-PROPOS|AVANT PROPOS|PROLOGUE|"
    r"EXPOSÉ PRÉLIMINAIRE|EXPOSE PRÉLIMINAIRE)\b"
)
RE_APPENDICE = re.compile(r"\bAppendice\s*:")
RE_ARTICLE = re.compile(r"\bArticle\s+\d+\s*:")
RE_ANCRE_ROM = re.compile(r"<a name=\"([IVX]+)[._][^\"]*\">")


def _texte_brut(chunk: str) -> str:
    """Nettoyage d'un segment de contenu : suppression des marqueurs de notes, balises, entités."""
    chunk = RE_RENVOI_NOTE.sub("", chunk)
    chunk = RE_MARQUEUR_NOTE.sub("", chunk)
    chunk = chunk.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
    chunk = re.sub(r"<[^>]+>", " ", chunk)
    chunk = html_lib.unescape(chunk)
    chunk = re.sub(r"\s+", " ", chunk).strip()
    return chunk


def _texte_note(chunk: str) -> str:
    """Nettoyage d'une note de bas de page (on garde le numéro initial)."""
    chunk = chunk.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
    chunk = re.sub(r"<[^>]+>", " ", chunk)
    chunk = html_lib.unescape(chunk)
    chunk = re.sub(r"\s+", " ", chunk).strip()
    return chunk


def _numero_chapitre(mot: str) -> int | None:
    """« PREMIER » → 1, « II » → 2, etc."""
    mot = mot.upper().replace("É", "E").replace("È", "E").replace("Ê", "E")
    if mot in CHIFFRES_ROMAINS:
        return CHIFFRES_ROMAINS[mot]
    if mot in CHAPITRES_EN_LETTRES:
        return CHAPITRES_EN_LETTRES[mot]
    return None


def _segments(brut: str, meta: dict, avec_ancres_chapitre: bool) -> list[tuple]:
    """Découpe le contenu brut d'un <p> en segments (genre, charge utile).

    genre ∈ {'chapitre', 'section', 'section_ancree', 'sous_titre', 'article', 'texte'}
    """
    normalise = html_lib.unescape(brut)  # entités décodées, balises intactes
    matches: list[tuple[int, int, str, object]] = []
    acceptes: list[tuple[int, int]] = []

    def ajouter(m):
        for (a, b) in acceptes:
            if not (m.end() <= a or m.start() >= b):
                return False  # chevauche un segment déjà accepté
        acceptes.append((m.start(), m.end()))
        matches.append((m.start(), m.end(), m.group(0), None))
        return True

    # 1. en-têtes en gras-italique : <b><i>N. Titre</i></b>
    for m in RE_EN_TETE_BOLD.finditer(normalise):
        if ajouter(m):
            matches[-1] = (m.start(), m.end(), "section",
                           (int(m.group(1)), _texte_brut(m.group(2))))
    # 2. chapitres « CHAPITRE X : » (ancre ou non, en ligne ou non)
    for m in RE_CHAPITRE.finditer(normalise):
        if ajouter(m):
            numero = _numero_chapitre(m.group(1))
            reste = normalise[m.end():]
            fin = re.search(r"\s+\d{1,3}\.\s|<a name=\"\d+\.?\"", reste)
            if fin:
                titre = _texte_brut(reste[:fin.start()])
                fin_segment = m.end() + fin.start()
            else:
                titre = _texte_brut(reste)
                fin_segment = m.end() + len(reste)
            matches[-1] = (m.start(), fin_segment, "chapitre", (numero, titre))
    # 3. mots structurels en capitales (CONCLUSION, PRÉAMBULE…)
    for m in RE_MOT_STRUCTURE.finditer(normalise):
        if ajouter(m):
            matches[-1] = (m.start(), m.end(), "chapitre", (None, m.group(0).capitalize()))
    # 4. « Appendice : »
    for m in RE_APPENDICE.finditer(normalise):
        if ajouter(m):
            matches[-1] = (m.start(), m.end(), "chapitre", (None, "Appendice"))
    # 5. « Article N : » → sous-titre en attente
    for m in RE_ARTICLE.finditer(normalise):
        if ajouter(m):
            reste = normalise[m.end():]
            fin = re.search(r"\s+\d{1,3}\.\s", reste)
            titre = _texte_brut(reste[:fin.start()] if fin else reste)
            matches[-1] = (m.start(), m.end(), "article", "Article " + m.group(0)[8:] + titre)
    # 6. ancre numérique non grasse : <a name="N.">N.</a> Texte…
    for m in RE_ANCRE_NUM.finditer(normalise):
        if ajouter(m):
            matches[-1] = (m.start(), m.end(), "section_ancree", int(m.group(1)))
    # 6 bis. en-tête romain : chapitre (sans ancres CHAPITRE) ou sous-titre
    for m in RE_ANCRE_ROM.finditer(normalise):
        if ajouter(m):
            reste = normalise[m.end():]
            fin = re.search(r"\s+\d{1,3}\.\s|<a name=\"\d+\.?\"", reste)
            if fin:
                titre = _texte_brut(reste[:fin.start()])
                fin_segment = m.end() + fin.start()
            else:
                titre = _texte_brut(reste)
                fin_segment = m.end() + len(reste)
            titre = re.sub(r"^[IVX]+\s*[–\-.]?\s*", "", titre).strip()
            if avec_ancres_chapitre:
                matches[-1] = (m.start(), fin_segment, "sous_titre", titre)
            else:
                numero = CHIFFRES_ROMAINS.get(m.group(1))
                matches[-1] = (m.start(), fin_segment, "chapitre", (numero, titre))
    # 7. titres connus en ligne (métadonnée) : « N. Titre »
    for numero, titre in (meta.get("titres_inline") or {}).items():
        motif = re.compile(
            r"(?<![\d.])" + str(numero) + r"\.\s+" + re.escape(titre))
        for m in motif.finditer(normalise):
            if ajouter(m):
                matches[-1] = (m.start(), m.end(), "section",
                               (int(numero), titre if titre else ""))

    matches.sort(key=lambda x: x[0])
    if not matches:
        return [("texte", _texte_brut(brut))]

    segments = []
    pos = 0
    for debut, fin, genre, charge in matches:
        avant = _texte_brut(normalise[pos:debut])
        if avant:
            segments.append(("texte", avant))
        segments.append((genre, charge))
        pos = fin
    apres = _texte_brut(normalise[pos:])
    if apres:
        segments.append(("texte", apres))
    return segments


def analyser_page(html_brut: str, meta: dict) -> dict:
    """Analyse la page d'un document conciliaire et renvoie le dictionnaire structuré."""
    document = {
        "id": meta["id"],
        "titre": meta["titre"],
        "sous_titre": meta.get("sous_titre", ""),
        "type": meta.get("type", "document"),
        "categorie": meta.get("categorie", ""),
        "date": meta.get("date", ""),
        "promulgateur": meta.get("promulgateur", ""),
        "source": meta.get("source", ""),
        "licence_note": meta.get("licence_note", ""),
        "promulgation": "",
        "introduction": [],
        "chapitres": [],
        "annexes": [],
        "notes": [],
        "signatures": [],
        "formule_finale": [],
    }

    # y a-t-il des chapitres avec ancre « CHAPITRE_ » quelque part ?
    avec_ancres_chapitre = bool(re.search(r'<a name="CHAPITRE_', html_brut))

    blocs = [(m.group(1).strip(), m.group(2)) for m in RE_PARAGRAPHE.finditer(html_brut)]

    chapitres: list[dict] = []
    section_courante: dict | None = None
    chapitre_courant: dict | None = None
    sous_titre_en_attente: str | None = None
    introduction: list[str] = []
    promulgation: list[str] = []
    notes: list[str] = []
    signatures: list[str] = []
    formule: list[str] = []
    zone_notes = False
    est_centre = lambda attr: "center" in attr  # noqa: E731

    for attr, brut in blocs:
        if zone_notes:
            if RE_NOTE.search(brut):
                notes.append(_texte_note(brut))
            continue
        if RE_NOTE.search(brut):
            zone_notes = True
            notes.append(_texte_note(brut))
            continue

        texte = _texte_brut(brut)
        if not texte:
            continue

        # — signatures et formule finale (apostrophes normalisées) —
        texte_droits = texte.replace("\u2019", "'").replace("\u2018", "'")
        if texte_droits.startswith("Ego ") or texte_droits.startswith("(Suivent les signatures"):
            signatures.append(texte)
            continue
        if texte_droits == "Moi, Paul, évêque de l'Eglise catholique.":
            signatures.append(texte)
            continue
        if texte_droits.startswith("Tout l'ensemble et chacun des points"):
            formule.append(texte)
            continue

        # — bloc de promulgation (avant le premier chapitre) —
        if not chapitres and est_centre(attr) and re.search(
            r"SERVITEUR DES SERVITEURS|CONSTITUTION|DÉCRET|DECRET|DÉCLARATION|DECLARATION",
            texte, re.I,
        ):
            promulgation.append(texte)
            continue

        # — titre de groupe centré (documents signalés : OE…), hors chapitres et articles —
        if (meta.get("titres_centres")
                and est_centre(attr)
                and not RE_CHAPITRE.search(brut)
                and not RE_ARTICLE.search(brut)
                and len(texte) <= 90
                and not texte[0].isdigit()
                and not re.match(r"^[IVX]+\s", texte)):
            chapitre_courant = {"numero": None, "titre": texte, "sections": []}
            chapitres.append(chapitre_courant)
            section_courante = None
            continue

        # — découpage générique du <p> en segments —
        for genre, charge in _segments(brut, meta, avec_ancres_chapitre):
            if genre == "chapitre":
                numero, titre = charge
                chapitre_courant = {"numero": numero, "titre": titre, "sections": []}
                chapitres.append(chapitre_courant)
                section_courante = None
            elif genre == "section":
                numero, titre = charge
                if chapitre_courant is None:
                    chapitre_courant = {"numero": None, "titre": "", "sections": []}
                    chapitres.append(chapitre_courant)
                section_courante = {
                    "numero": numero, "titre": titre,
                    "sous_titre": sous_titre_en_attente or "", "paragraphes": [],
                }
                sous_titre_en_attente = None
                chapitre_courant["sections"].append(section_courante)
            elif genre == "section_ancree":
                if chapitre_courant is None:
                    chapitre_courant = {"numero": None, "titre": "", "sections": []}
                    chapitres.append(chapitre_courant)
                section_courante = {
                    "numero": charge, "titre": "",
                    "sous_titre": sous_titre_en_attente or "", "paragraphes": [],
                }
                sous_titre_en_attente = None
                chapitre_courant["sections"].append(section_courante)
            elif genre == "article":
                sous_titre_en_attente = charge
            elif genre == "sous_titre":
                sous_titre_en_attente = charge
            else:  # texte
                if section_courante is not None:
                    section_courante["paragraphes"].append(charge)
                elif chapitre_courant is not None:
                    section_courante = {"numero": None, "titre": "", "sous_titre": "", "paragraphes": [charge]}
                    chapitre_courant["sections"].append(section_courante)
                else:
                    introduction.append(charge)

    # — post-traitements pilotés par la métadonnée —

    # prologue : le premier chapitre sans numéro est le prologue (DV, PO, CD, SC, DH…)
    if meta.get("prologue") and chapitres and chapitres[0]["numero"] is None:
        chapitres[0]["titre"] = "Prologue"
    if meta.get("titre_chapitre_initial") and chapitres and chapitres[0]["numero"] is None:
        chapitres[0]["titre"] = meta["titre_chapitre_initial"]

    # parties synthétiques (GS) : insérer un pseudo-chapitre avant la section cible
    for partie in meta.get("parties") or []:
        for i, ch in enumerate(chapitres):
            for j, sec in enumerate(ch["sections"]):
                if sec["numero"] is not None and sec["numero"] >= partie["avant"]:
                    if sec["numero"] == partie["avant"]:
                        gauche = ch["sections"][:j]
                        droite = ch["sections"][j:]
                        nouveau = {"numero": None, "titre": partie["titre"], "sections": droite}
                        if gauche:
                            chapitres[i] = {**ch, "sections": gauche}
                            chapitres.insert(i + 1, nouveau)
                        else:
                            chapitres[i] = nouveau
                    break
            else:
                continue
            break

    # notification finale explicite (LG)
    if meta.get("notification_apres") is not None and meta.get("notification_motif"):
        for ch in chapitres:
            for sec in ch["sections"]:
                if sec["numero"] == meta["notification_apres"]:
                    paragraphes = sec["paragraphes"]
                    for k, p in enumerate(paragraphes):
                        if meta["notification_motif"].lower() in p.lower():
                            document["annexes"].append({
                                "titre": "Notification", "paragraphes": paragraphes[k:],
                            })
                            sec["paragraphes"] = paragraphes[:k]
                            break
                    break

    # section finale non balisée (AA n. 33)
    sf = meta.get("section_finale")
    if sf:
        for ch in chapitres:
            for sec in ch["sections"]:
                if sec["numero"] == sf["apres"]:
                    paragraphes = sec["paragraphes"]
                    for k, p in enumerate(paragraphes):
                        if sf["motif"].lower() in p.lower():
                            reste = paragraphes[k:]
                            sec["paragraphes"] = paragraphes[:k]
                            chapitres.append({
                                "numero": None, "titre": "Conclusion",
                                "sections": [{
                                    "numero": sf["numero"], "titre": sf.get("titre", ""),
                                    "sous_titre": "", "paragraphes": reste,
                                }],
                            })
                            break
                    break

    document["promulgation"] = " ".join(promulgation)
    document["introduction"] = introduction
    document["chapitres"] = chapitres
    document["notes"] = notes
    document["signatures"] = signatures
    document["formule_finale"] = formule
    document["nb_mots"] = sum(
        len(p.split())
        for ch in chapitres
        for sec in ch["sections"]
        for p in sec["paragraphes"]
    ) + sum(len(p.split()) for p in introduction)
    return document


if __name__ == "__main__":
    if len(sys.argv) < 9:
        print("usage: vatican2_parser.py fichier.html id titre sous_titre type categorie date source")
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8", errors="replace") as fh:
        contenu = fh.read()
    meta = {
        "id": sys.argv[2], "titre": sys.argv[3], "sous_titre": sys.argv[4],
        "type": sys.argv[5], "categorie": sys.argv[6], "date": sys.argv[7],
        "source": sys.argv[8],
    }
    print(json.dumps(analyser_page(contenu, meta), ensure_ascii=False, indent=2))
