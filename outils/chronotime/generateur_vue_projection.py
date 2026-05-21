from __future__ import annotations

import argparse
import json
from datetime import date
from html import escape
from pathlib import Path
from typing import Any


SOURCE_ATTENDUE = "projection.demi_journees"
MOIS_FRANCAIS = {
    1: "janvier",
    2: "février",
    3: "mars",
    4: "avril",
    5: "mai",
    6: "juin",
    7: "juillet",
    8: "août",
    9: "septembre",
    10: "octobre",
    11: "novembre",
    12: "décembre",
}
TYPES_ALERTES = {
    "evenement_hors_periode_projection": "Événement hors période de projection",
    "solde_negatif_confirmation_possible": "Solde négatif probablement confirmable",
    "solde_minimum_depasse": "Solde minimum dépassé",
    "periode_compteur_absente": "Période de compteur absente",
    "quantite_evenement_non_projectee": "Quantité d'événement non projetée",
    "unite_non_projectee": "Unité non projetée",
    "date_cible_hors_periode": "Date cible hors période",
}
LABELS_SEVERITE = {
    "information": "information",
    "confirmation": "confirmation",
    "bloquant": "bloquant",
}
TIRET = "—"


def lire_json(chemin: Path) -> Any:
    try:
        texte = chemin.read_text(encoding="utf-8-sig")
    except OSError as erreur:
        raise SystemExit(f"Impossible de lire le fichier de projection : {chemin}") from erreur

    try:
        return json.loads(texte)
    except json.JSONDecodeError as erreur:
        raise SystemExit(f"JSON invalide dans le fichier de projection : {chemin}") from erreur


def charger_projection(chemin: Path) -> dict[str, Any]:
    donnees = lire_json(chemin)
    if not isinstance(donnees, dict):
        raise ValueError("La projection doit être un objet JSON.")
    if donnees.get("source") != SOURCE_ATTENDUE:
        raise ValueError(f"Source de projection invalide : {donnees.get('source')!r}.")
    return donnees


def date_iso_vers_objet(valeur: str) -> date:
    return date.fromisoformat(valeur)


def formater_date_francaise(valeur: str) -> str:
    jour = date_iso_vers_objet(valeur)
    return f"{jour.day} {MOIS_FRANCAIS[jour.month]} {jour.year}"


def formater_mois_annee(valeur: str) -> str:
    jour = date_iso_vers_objet(valeur)
    return f"{MOIS_FRANCAIS[jour.month]} {jour.year}"


def formater_periode_francaise(debut: str, fin: str) -> str:
    date_debut = date_iso_vers_objet(debut)
    date_fin = date_iso_vers_objet(fin)
    if date_debut.year == date_fin.year:
        return (
            f"du {date_debut.day} {MOIS_FRANCAIS[date_debut.month]} "
            f"au {date_fin.day} {MOIS_FRANCAIS[date_fin.month]} {date_fin.year}"
        )
    return f"du {formater_date_francaise(debut)} au {formater_date_francaise(fin)}"


def formater_nombre_francais(valeur: Any) -> str:
    if not isinstance(valeur, (int, float)):
        return TIRET
    texte = f"{float(valeur):.2f}".rstrip("0").rstrip(".")
    return texte.replace(".", ",")


def formater_quantite_jour(valeur: Any) -> str:
    if not isinstance(valeur, (int, float)):
        return TIRET
    return f"{formater_nombre_francais(valeur)} j"


def serialiser_objet(valeur: Any) -> str:
    return escape(json.dumps(valeur, ensure_ascii=False, indent=2))


def tableau_soldes(titre: str, soldes: dict[str, Any]) -> str:
    lignes = []
    for compteur, valeur in sorted(soldes.items()):
        lignes.append(
            "<tr>"
            f"<th>{escape(str(compteur))}</th>"
            f"<td>{escape(formater_quantite_jour(valeur))}</td>"
            "</tr>"
        )
    corps = "\n".join(lignes) if lignes else "<tr><td colspan=\"2\">Aucun solde.</td></tr>"
    return f"""
    <section class="carte">
      <h2>{escape(titre)}</h2>
      <table>
        <thead><tr><th>Compteur</th><th>Solde initial</th></tr></thead>
        <tbody>{corps}</tbody>
      </table>
    </section>
    """


def compteurs_dates_cibles(dates_cibles: list[Any]) -> list[str]:
    compteurs: set[str] = set()
    for cible in dates_cibles:
        soldes = cible.get("soldes") if isinstance(cible, dict) else None
        if isinstance(soldes, dict):
            for compteur in soldes:
                compteurs.add(str(compteur))
    return sorted(compteurs)


def tableau_dates_cibles(dates_cibles: list[Any]) -> str:
    compteurs = compteurs_dates_cibles(dates_cibles)
    entetes_compteurs = "".join(f"<th>{escape(compteur)}</th>" for compteur in compteurs)
    lignes = []
    for cible in dates_cibles:
        if not isinstance(cible, dict):
            continue
        soldes = cible.get("soldes")
        soldes = soldes if isinstance(soldes, dict) else {}
        cellules_compteurs = []
        for compteur in compteurs:
            valeur = soldes.get(compteur)
            cellules_compteurs.append(f"<td>{escape(formater_quantite_jour(valeur) if valeur is not None else TIRET)}</td>")
        lignes.append(
            "<tr>"
            f"<td>{escape(str(cible.get('libelle') or cible.get('identifiant', '')))}</td>"
            f"<td>{escape(formater_date_francaise(str(cible.get('date')))) if cible.get('date') else TIRET}</td>"
            f"{''.join(cellules_compteurs)}"
            "</tr>"
        )
    corps = "\n".join(lignes) if lignes else f"<tr><td colspan=\"{2 + len(compteurs)}\">Aucune date cible.</td></tr>"
    return f"""
    <section class="carte">
      <h2>Soldes aux dates cibles</h2>
      <table>
        <thead>
          <tr><th>Date cible</th><th>Date</th>{entetes_compteurs}</tr>
        </thead>
        <tbody>{corps}</tbody>
      </table>
    </section>
    """


def type_alerte_lisible(type_alerte: Any) -> str:
    return TYPES_ALERTES.get(str(type_alerte), str(type_alerte))


def severite_lisible(severite: Any) -> str:
    return LABELS_SEVERITE.get(str(severite), str(severite))


def resume_alerte(alerte: dict[str, Any]) -> str:
    morceaux = []
    if alerte.get("date"):
        morceaux.append(f"date {formater_date_francaise(str(alerte['date']))}")
    if alerte.get("date_debut") and alerte.get("date_fin"):
        morceaux.append(
            f"periode {formater_periode_francaise(str(alerte['date_debut']), str(alerte['date_fin']))}"
        )
    if alerte.get("compteur"):
        morceaux.append(f"compteur {alerte['compteur']}")
    identifiant = None
    if alerte.get("identifiant_evenement"):
        identifiant = str(alerte["identifiant_evenement"])
    elif isinstance(alerte.get("identifiants_evenements"), list) and alerte["identifiants_evenements"]:
        identifiant = str(alerte["identifiants_evenements"][0])
    if identifiant:
        morceaux.append(f"evenement {identifiant}")
    if alerte.get("quantite_non_couverte") is not None:
        morceaux.append(f"non couvert {formater_quantite_jour(alerte['quantite_non_couverte'])}")
    if not morceaux:
        return "Aucun contexte supplémentaire."
    return " ; ".join(morceaux)


def details_alerte(alerte: dict[str, Any]) -> str:
    return serialiser_objet(alerte)


def carte_alerte(alerte: dict[str, Any]) -> str:
    severite = severite_lisible(alerte.get("severite", "information"))
    date_texte = ""
    if alerte.get("date"):
        date_texte = formater_date_francaise(str(alerte["date"]))
    elif alerte.get("date_debut") and alerte.get("date_fin"):
        date_texte = formater_periode_francaise(str(alerte["date_debut"]), str(alerte["date_fin"]))
    return (
        f"<li class=\"alerte alerte-{escape(severite)}\">"
        f"<h3>{escape(type_alerte_lisible(alerte.get('type')))}</h3>"
        f"<p><strong>Sévérité</strong> : {escape(severite)}</p>"
        f"<p><strong>Date ou période</strong> : {escape(date_texte or TIRET)}</p>"
        f"<p><strong>Compteur</strong> : {escape(str(alerte.get('compteur', TIRET)))}</p>"
        f"<p><strong>Événement</strong> : {escape(str(alerte.get('identifiant_evenement') or (alerte.get('identifiants_evenements') or [TIRET])[0]))}</p>"
        f"<p><strong>Résumé humain</strong> : {escape(resume_alerte(alerte))}</p>"
        f"<details><summary>Détails techniques</summary><pre>{details_alerte(alerte)}</pre></details>"
        "</li>"
    )


def liste_alertes(alertes: list[Any]) -> str:
    elements = [carte_alerte(alerte) for alerte in alertes if isinstance(alerte, dict)]
    contenu = "\n".join(elements) if elements else "<li>Aucune alerte globale.</li>"
    return f"""
    <section class="carte">
      <h2>Alertes globales</h2>
      <p class="note">
        Certaines alertes globales peuvent ne pas apparaître sur la frise lorsqu'elles concernent un événement hors de la période projetée.
      </p>
      <ul class="liste-alertes">{contenu}</ul>
    </section>
    """


def demi_journee_a_consommation_non_couverte(demi_journee: dict[str, Any]) -> bool:
    for detail in demi_journee.get("consommations_detaillees", []):
        if isinstance(detail, dict) and float(detail.get("quantite_non_couverte") or 0.0) > 0:
            return True
    return False


def classes_demi_journee(demi_journee: dict[str, Any]) -> str:
    classes = ["case-demi-journee"]
    if demi_journee.get("consommations") or demi_journee.get("consommations_detaillees"):
        classes.append("case-consommee")
    if demi_journee_a_consommation_non_couverte(demi_journee):
        classes.append("case-non-couverte")
    if demi_journee.get("alertes"):
        classes.append("case-alerte")
    return " ".join(classes)


def est_debut_de_mois(date_iso: str, precedent: str | None) -> bool:
    if precedent is None:
        return True
    date_courante = date_iso_vers_objet(date_iso)
    date_precedente = date_iso_vers_objet(precedent)
    return date_courante.month != date_precedente.month or date_courante.year != date_precedente.year


def est_repere_jour(date_iso: str) -> bool:
    jour = date_iso_vers_objet(date_iso)
    return jour.day == 1 or jour.weekday() == 0


def generer_frise(demi_journees: list[Any]) -> str:
    morceaux = []
    date_precedente = None
    for demi_journee in demi_journees:
        if not isinstance(demi_journee, dict):
            continue
        date_iso = str(demi_journee.get("date", ""))
        if date_iso and est_debut_de_mois(date_iso, date_precedente):
            morceaux.append(f"<div class=\"repere-mois\">{escape(formater_mois_annee(date_iso))}</div>")
        marqueur_jour = ""
        if date_iso and demi_journee.get("portion") == "matin" and est_repere_jour(date_iso):
            marqueur_jour = f"<span class=\"repere-jour\">{date_iso_vers_objet(date_iso).day}</span>"
        titre = f"{formater_date_francaise(date_iso)} {demi_journee.get('portion', '')}" if date_iso else ""
        contenu = "M" if demi_journee.get("portion") == "matin" else "A"
        morceaux.append(
            "<span class=\"bloc-case\">"
            f"{marqueur_jour}"
            f"<span class=\"{classes_demi_journee(demi_journee)}\" title=\"{escape(titre)}\">{escape(contenu)}</span>"
            "</span>"
        )
        date_precedente = date_iso
    contenu_frise = "\n".join(morceaux) if morceaux else "<p>Aucune demi-journée.</p>"
    return f"""
    <section class="carte frise">
      <h2>Frise 1D des demi-journées</h2>
      <div class="legende">
        <span><i class="case-demi-journee"></i> sans consommation</span>
        <span><i class="case-demi-journee case-consommee"></i> consommation appliquée</span>
        <span><i class="case-demi-journee case-non-couverte"></i> quantité non couverte</span>
        <span><i class="case-demi-journee case-alerte"></i> alerte</span>
      </div>
      <div class="rail-frise">{contenu_frise}</div>
    </section>
    """


def demi_journees_utiles(demi_journees: list[Any]) -> list[dict[str, Any]]:
    utiles = []
    for demi_journee in demi_journees:
        if not isinstance(demi_journee, dict):
            continue
        if demi_journee.get("consommations") or demi_journee.get("consommations_detaillees") or demi_journee.get("alertes"):
            utiles.append(demi_journee)
    return utiles


def resume_consommations_detaillees(details: list[Any]) -> str:
    lignes = []
    for detail in details:
        if not isinstance(detail, dict):
            continue
        lignes.append(
            f"{detail.get('compteur', '?')} : demandée {formater_quantite_jour(detail.get('quantite_demandee'))}, "
            f"appliquée {formater_quantite_jour(detail.get('quantite_appliquee'))}, "
            f"non couverte {formater_quantite_jour(detail.get('quantite_non_couverte'))}"
        )
    return "<br>".join(escape(ligne) for ligne in lignes) if lignes else "Aucune consommation détaillée."


def tableau_soldes_concernes(
    soldes_avant: dict[str, Any],
    soldes_apres: dict[str, Any],
    compteurs: list[str],
) -> str:
    lignes = []
    for compteur in compteurs:
        lignes.append(
            "<tr>"
            f"<th>{escape(compteur)}</th>"
            f"<td>{escape(formater_quantite_jour(soldes_avant.get(compteur)))}</td>"
            f"<td>{escape(formater_quantite_jour(soldes_apres.get(compteur)))}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Compteur</th><th>Avant</th><th>Après</th></tr></thead>"
        f"<tbody>{''.join(lignes)}</tbody></table>"
    )


def bloc_details_demi_journees(demi_journees: list[Any]) -> str:
    blocs = []
    for demi_journee in demi_journees_utiles(demi_journees):
        date_lisible = formater_date_francaise(str(demi_journee.get("date")))
        details = demi_journee.get("consommations_detaillees", [])
        if not isinstance(details, list):
            details = []
        compteurs = sorted(
            {
                str(detail.get("compteur"))
                for detail in details
                if isinstance(detail, dict) and detail.get("compteur")
            }
        )
        if not compteurs:
            compteurs = sorted(str(compteur) for compteur in demi_journee.get("consommations", {}).keys())
        alertes = demi_journee.get("alertes", [])
        alertes = alertes if isinstance(alertes, list) else []
        blocs.append(
            "<article class=\"detail-demi-journee\">"
            f"<h3>{escape(date_lisible)} - {escape(str(demi_journee.get('portion', '')))}</h3>"
            "<dl>"
            f"<dt>Date</dt><dd>{escape(date_lisible)}</dd>"
            f"<dt>Portion</dt><dd>{escape(str(demi_journee.get('portion', '')))}</dd>"
            f"<dt>Compteurs consommés</dt><dd>{escape(', '.join(compteurs) if compteurs else 'Aucun')}</dd>"
            f"<dt>Résumé des consommations</dt><dd>{resume_consommations_detaillees(details)}</dd>"
            f"<dt>Soldes avant/après</dt><dd>{tableau_soldes_concernes(demi_journee.get('soldes_avant', {}), demi_journee.get('soldes_apres', {}), compteurs) if compteurs else 'Aucun compteur concerné.'}</dd>"
            f"<dt>Alertes</dt><dd>{escape(', '.join(type_alerte_lisible(alerte.get('type')) for alerte in alertes if isinstance(alerte, dict)) or 'Aucune')}</dd>"
            "</dl>"
            f"<details><summary>Détails techniques</summary><pre>{serialiser_objet(demi_journee)}</pre></details>"
            "</article>"
        )
    contenu = "\n".join(blocs) if blocs else "<p>Aucune demi-journée consommée ou alertée.</p>"
    return f"""
    <section class="carte">
      <h2>Détails des demi-journées utiles</h2>
      {contenu}
    </section>
    """


def cartes_resume(periode: dict[str, Any], resume: dict[str, Any], projection: dict[str, Any]) -> str:
    debut = str(periode.get("debut", ""))
    fin = str(periode.get("fin", ""))
    periode_lisible = formater_periode_francaise(debut, fin) if debut and fin else TIRET
    cartes = [
        ("Période", periode_lisible),
        ("Demi-journées projetées", str(resume.get("nombre_demi_journees", len(projection.get("demi_journees", []))))),
        ("Événements sources", str(resume.get("nombre_evenements_sources", len(projection.get("evenements_sources", []))))),
        ("Alertes globales", str(resume.get("nombre_alertes", len(projection.get("alertes", []))))),
    ]
    return "".join(
        f"<article class=\"tuile-resume\"><p class=\"tuile-label\">{escape(label)}</p><p class=\"tuile-valeur\">{escape(valeur)}</p></article>"
        for label, valeur in cartes
    )


def feuille_style() -> str:
    return """
    :root {
      --fond: #f5efe3;
      --encre: #1f2a24;
      --muted: #657168;
      --carte: #fffaf0;
      --trait: #d8c9ae;
      --accent: #146b5f;
      --accent-fort: #0d4a44;
      --alerte: #b13b2e;
      --confirmation: #9b6b00;
      --info: #35648f;
      --ombre: 0 18px 40px rgba(41, 31, 19, 0.14);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--encre);
      background:
        radial-gradient(circle at top left, rgba(20, 107, 95, 0.18), transparent 32rem),
        linear-gradient(135deg, #f8f1e6 0%, #efe1c8 100%);
      font-family: Georgia, "Times New Roman", serif;
      line-height: 1.45;
    }
    main {
      max-width: 1180px;
      margin: 0 auto;
      padding: 32px 18px 56px;
    }
    .hero {
      padding: 32px;
      border: 1px solid var(--trait);
      border-radius: 28px;
      background: rgba(255, 250, 240, 0.82);
      box-shadow: var(--ombre);
    }
    h1 {
      margin: 0 0 10px;
      font-size: clamp(2rem, 5vw, 4.8rem);
      line-height: 0.95;
      letter-spacing: -0.05em;
    }
    h2 {
      margin: 0 0 16px;
      font-size: 1.3rem;
      color: var(--accent-fort);
    }
    h3 { margin: 0 0 10px; }
    .grille {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 18px;
      margin-top: 18px;
    }
    .resume-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin-top: 18px;
    }
    .tuile-resume {
      padding: 18px;
      border: 1px solid var(--trait);
      border-radius: 20px;
      background: rgba(255, 250, 240, 0.88);
      box-shadow: 0 10px 26px rgba(41, 31, 19, 0.08);
    }
    .tuile-label {
      margin: 0 0 8px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 0.75rem;
    }
    .tuile-valeur {
      margin: 0;
      font-size: 1.35rem;
      color: var(--accent-fort);
    }
    .carte {
      margin-top: 18px;
      padding: 22px;
      border: 1px solid var(--trait);
      border-radius: 22px;
      background: rgba(255, 250, 240, 0.9);
      box-shadow: 0 10px 26px rgba(41, 31, 19, 0.08);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      overflow: hidden;
      border-radius: 14px;
    }
    th, td {
      padding: 10px 12px;
      border-bottom: 1px solid var(--trait);
      text-align: left;
      vertical-align: top;
    }
    th {
      color: var(--accent-fort);
      background: rgba(20, 107, 95, 0.08);
    }
    pre {
      margin: 0;
      white-space: pre-wrap;
      font-family: "Cascadia Mono", Consolas, monospace;
      font-size: 0.86rem;
    }
    .liste-alertes {
      padding: 0;
      list-style: none;
    }
    .alerte {
      margin: 10px 0;
      padding: 14px;
      border-left: 6px solid var(--info);
      background: rgba(53, 100, 143, 0.08);
      border-radius: 14px;
    }
    .alerte-confirmation { border-left-color: var(--confirmation); background: rgba(155, 107, 0, 0.1); }
    .alerte-bloquant { border-left-color: var(--alerte); background: rgba(177, 59, 46, 0.1); }
    .legende {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 14px;
      color: var(--muted);
      font-size: 0.92rem;
    }
    .legende span {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .rail-frise {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      padding: 16px;
      border-radius: 18px;
      background: #efe4d0;
      align-items: end;
    }
    .repere-mois {
      width: 100%;
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px dashed #b9aa8f;
      color: var(--accent-fort);
      font-weight: 700;
      text-transform: lowercase;
    }
    .bloc-case {
      display: inline-flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      min-width: 22px;
    }
    .repere-jour {
      color: var(--muted);
      font-size: 0.72rem;
      line-height: 1;
    }
    .case-demi-journee {
      display: inline-flex;
      width: 22px;
      height: 22px;
      align-items: center;
      justify-content: center;
      border: 1px solid #b9aa8f;
      border-radius: 7px;
      background: #fffaf0;
      color: var(--muted);
      font-size: 0.7rem;
      font-style: normal;
    }
    .case-consommee {
      background: var(--accent);
      border-color: var(--accent-fort);
      color: white;
    }
    .case-non-couverte {
      background: repeating-linear-gradient(135deg, #b13b2e 0 5px, #f2c2b8 5px 10px);
      color: white;
    }
    .case-alerte {
      box-shadow: 0 0 0 3px rgba(177, 59, 46, 0.32);
    }
    .detail-demi-journee {
      margin-top: 14px;
      padding: 16px;
      border: 1px solid var(--trait);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.42);
    }
    dl {
      display: grid;
      grid-template-columns: minmax(130px, 220px) 1fr;
      gap: 10px 16px;
      margin: 0 0 12px;
    }
    dt {
      color: var(--accent-fort);
      font-weight: 700;
    }
    dd { margin: 0; min-width: 0; }
    .note {
      color: var(--muted);
      max-width: 760px;
    }
    details {
      margin-top: 12px;
      border-top: 1px dashed var(--trait);
      padding-top: 12px;
    }
    summary {
      cursor: pointer;
      color: var(--accent-fort);
      font-weight: 700;
    }
    @media (max-width: 720px) {
      .hero { padding: 22px; }
      dl { grid-template-columns: 1fr; }
    }
    """


def generer_html(projection: dict[str, Any]) -> str:
    periode = projection.get("periode", {}) if isinstance(projection.get("periode"), dict) else {}
    resume = projection.get("resume", {}) if isinstance(projection.get("resume"), dict) else {}
    demi_journees = projection.get("demi_journees", [])
    if not isinstance(demi_journees, list):
        demi_journees = []
    alertes = projection.get("alertes", [])
    if not isinstance(alertes, list):
        alertes = []
    soldes_initiaux = projection.get("soldes_initiaux", {})
    if not isinstance(soldes_initiaux, dict):
        soldes_initiaux = {}
    dates_cibles = projection.get("soldes_aux_dates_cibles", [])
    if not isinstance(dates_cibles, list):
        dates_cibles = []

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Vue locale de projection Chronotime</title>
  <style>{feuille_style()}</style>
</head>
<body>
  <main>
    <header class="hero">
      <h1>Vue locale de projection Chronotime</h1>
      <p class="note">
        Visualisation statique en lecture seule d'une projection <code>projection.demi_journees</code>.
        La projection reste une donnée dérivée : elle ne remplace pas le modèle événementiel source et ne modifie pas Chronotime.
      </p>
    </header>
    <section class="resume-cards">
      {cartes_resume(periode, resume, projection)}
    </section>
    <div class="grille">
      {tableau_soldes("Soldes initiaux", soldes_initiaux)}
    </div>
    {tableau_dates_cibles(dates_cibles)}
    {liste_alertes(alertes)}
    {generer_frise(demi_journees)}
    {bloc_details_demi_journees(demi_journees)}
    <section class="carte">
      <h2>Limites de cette vue</h2>
      <p>
        Cette page ne valide pas entièrement les jours fériés, la parentalité, les chevauchements d'agenda,
        les expirations fines ou l'optimisation. Elle sert seulement à vérifier la lisibilité de la projection.
      </p>
    </section>
  </main>
</body>
</html>
"""


def ecrire_html(contenu: str, chemin_sortie: Path) -> None:
    try:
        chemin_sortie.parent.mkdir(parents=True, exist_ok=True)
        chemin_sortie.write_text(contenu, encoding="utf-8")
    except OSError as erreur:
        raise SystemExit(f"Impossible d'écrire la page HTML : {chemin_sortie}") from erreur


def analyser_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(
        description="Générer une page HTML locale en lecture seule depuis une projection demi-journalière.",
    )
    analyseur.add_argument("--projection", type=Path, required=True, help="Chemin du fichier projection.demi_journees.")
    analyseur.add_argument("--sortie", type=Path, required=True, help="Chemin du fichier HTML à générer.")
    return analyseur.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = analyser_arguments(argv)
    try:
        projection = charger_projection(arguments.projection)
    except ValueError as erreur:
        raise SystemExit(str(erreur)) from erreur
    ecrire_html(generer_html(projection), arguments.sortie)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
