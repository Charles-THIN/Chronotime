from __future__ import annotations

import argparse
import json
from datetime import date
from html import escape
from pathlib import Path
from typing import Any


SOURCE_ATTENDUE = "projection.demi_journees"
SOURCE_CHRONOLOGIE = "chronologie.soldes"
SOURCE_SYNTHESE = "synthese.planification"
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
VUES = (
    ("vue-ensemble", "Vue d’ensemble"),
    ("vue-planification", "Planification"),
    ("vue-frise", "Frise"),
    ("vue-soldes", "Soldes"),
    ("vue-alertes", "Alertes"),
    ("vue-evenements", "Événements projetés"),
    ("vue-technique", "Technique"),
)


def lire_json(chemin: Path) -> Any:
    try:
        texte = chemin.read_text(encoding="utf-8-sig")
    except OSError as erreur:
        raise SystemExit(f"Impossible de lire le fichier JSON : {chemin}") from erreur

    try:
        return json.loads(texte)
    except json.JSONDecodeError as erreur:
        raise SystemExit(f"JSON invalide dans le fichier JSON : {chemin}") from erreur


def charger_projection(chemin: Path) -> dict[str, Any]:
    donnees = lire_json(chemin)
    if not isinstance(donnees, dict):
        raise ValueError("La projection doit être un objet JSON.")
    if donnees.get("source") != SOURCE_ATTENDUE:
        raise ValueError(f"Source de projection invalide : {donnees.get('source')!r}.")
    return donnees


def charger_chronologie(chemin: Path) -> dict[str, Any]:
    donnees = lire_json(chemin)
    if not isinstance(donnees, dict):
        raise ValueError("La chronologie doit être un objet JSON.")
    if donnees.get("source") != SOURCE_CHRONOLOGIE:
        raise ValueError(f"Source de chronologie invalide : {donnees.get('source')!r}.")
    return donnees


def charger_synthese(chemin: Path) -> dict[str, Any]:
    donnees = lire_json(chemin)
    if not isinstance(donnees, dict):
        raise ValueError("La synthèse doit être un objet JSON.")
    if donnees.get("source") != SOURCE_SYNTHESE:
        raise ValueError(f"Source de synthèse invalide : {donnees.get('source')!r}.")
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


def type_alerte_lisible(type_alerte: Any) -> str:
    return TYPES_ALERTES.get(str(type_alerte), str(type_alerte))


def severite_lisible(severite: Any) -> str:
    return LABELS_SEVERITE.get(str(severite), str(severite))


def tableau_soldes(titre: str, soldes: dict[str, Any], libelle_colonne: str = "Solde initial") -> str:
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
      <h3>{escape(titre)}</h3>
      <div class="tableau-defilable">
      <table>
        <thead><tr><th>Compteur</th><th>{escape(libelle_colonne)}</th></tr></thead>
        <tbody>{corps}</tbody>
      </table>
      </div>
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
      <h3>Soldes aux dates cibles</h3>
      <div class="tableau-defilable">
      <table>
        <thead>
          <tr><th>Date cible</th><th>Date</th>{entetes_compteurs}</tr>
        </thead>
        <tbody>{corps}</tbody>
      </table>
      </div>
    </section>
    """


def valeur_solde_compteur(soldes: Any, compteur: str) -> Any:
    if isinstance(soldes, dict):
        return soldes.get(compteur)
    return None


def types_alertes_resume(alertes: list[Any]) -> str:
    compteurs: dict[str, int] = {}
    for alerte in alertes:
        if not isinstance(alerte, dict):
            continue
        type_alerte = str(alerte.get("type", "alerte_sans_type"))
        compteurs[type_alerte] = compteurs.get(type_alerte, 0) + 1
    if not compteurs:
        return "Aucune alerte de chronologie."
    return ", ".join(
        f"{escape(type_alerte_lisible(type_alerte))} : {nombre}"
        for type_alerte, nombre in sorted(compteurs.items())
    )


def tableau_points_chronologie(points: list[Any]) -> str:
    lignes = []
    for point in points:
        if not isinstance(point, dict):
            continue
        compteur = str(point.get("compteur", ""))
        date_point = str(point.get("date", ""))
        date_lisible = formater_date_francaise(date_point) if date_point else TIRET
        solde_avant = valeur_solde_compteur(point.get("soldes_avant"), compteur)
        solde_apres = valeur_solde_compteur(point.get("soldes_apres"), compteur)
        lignes.append(
            "<tr>"
            f"<td>{escape(date_lisible)}</td>"
            f"<td>{escape(str(point.get('portion') or TIRET))}</td>"
            f"<td>{escape(compteur or TIRET)}</td>"
            f"<td>{escape(formater_quantite_jour(point.get('variation')))}</td>"
            f"<td>{escape(formater_quantite_jour(solde_avant))}</td>"
            f"<td>{escape(formater_quantite_jour(solde_apres))}</td>"
            f"<td>{escape(str(point.get('origine') or TIRET))}</td>"
            f"<td>{escape(str(point.get('type') or TIRET))}</td>"
            f"<td>{escape(str(point.get('identifiant') or TIRET))}</td>"
            f"<td><details><summary>Détails techniques</summary><pre>{serialiser_objet(point)}</pre></details></td>"
            "</tr>"
        )
    corps = "\n".join(lignes) if lignes else "<tr><td colspan=\"10\">Aucun point de chronologie.</td></tr>"
    return f"""
    <section class="carte">
      <h3>Points de chronologie</h3>
      <div class="tableau-defilable">
      <table>
        <thead>
          <tr>
            <th>Date</th><th>Portion</th><th>Compteur</th><th>Variation</th>
            <th>Solde avant</th><th>Solde après</th><th>Origine</th><th>Type</th><th>Identifiant</th><th>Technique</th>
          </tr>
        </thead>
        <tbody>{corps}</tbody>
      </table>
      </div>
    </section>
    """


def section_chronologie_soldes(chronologie: dict[str, Any] | None) -> str:
    if chronologie is None:
        return """
        <section class="carte">
          <h2>Soldes dans le temps</h2>
          <p class="note">Aucune chronologie.soldes fournie. La vue affiche seulement les soldes initiaux et les dates cibles.</p>
        </section>
        """

    soldes_finaux = chronologie.get("soldes_finaux", {})
    if not isinstance(soldes_finaux, dict):
        soldes_finaux = {}
    points = chronologie.get("points_chronologie", [])
    if not isinstance(points, list):
        points = []
    alertes = chronologie.get("alertes", [])
    if not isinstance(alertes, list):
        alertes = []
    return f"""
    <section class="carte">
      <h2>Soldes dans le temps</h2>
      <p class="note">
        Cette section affiche une sortie dérivée <code>chronologie.soldes</code> fournie au générateur.
        Elle est en lecture seule, ne recalcule pas la chronologie et ne gère pas encore la validité fine par période
        <code>precedent</code>, <code>courant</code> ou <code>suivant</code>.
      </p>
      <p><strong>Alertes de chronologie</strong> : {types_alertes_resume(alertes)}</p>
    </section>
    <div class="grille">
      {tableau_soldes("Soldes finaux", soldes_finaux, "Solde final")}
    </div>
    {tableau_points_chronologie(points)}
    """


def ordre_portion(portion: str) -> int:
    return 0 if portion == "matin" else 1


def resume_alerte(alerte: dict[str, Any]) -> str:
    morceaux = []
    if alerte.get("date"):
        morceaux.append(f"date {formater_date_francaise(str(alerte['date']))}")
    if alerte.get("date_debut") and alerte.get("date_fin"):
        morceaux.append(
            f"période {formater_periode_francaise(str(alerte['date_debut']), str(alerte['date_fin']))}"
        )
    if alerte.get("compteur"):
        morceaux.append(f"compteur {alerte['compteur']}")
    identifiant = None
    if alerte.get("identifiant_evenement"):
        identifiant = str(alerte["identifiant_evenement"])
    elif isinstance(alerte.get("identifiants_evenements"), list) and alerte["identifiants_evenements"]:
        identifiant = str(alerte["identifiants_evenements"][0])
    if identifiant:
        morceaux.append(f"événement {identifiant}")
    if alerte.get("quantite_non_couverte") is not None:
        morceaux.append(f"non couvert {formater_quantite_jour(alerte['quantite_non_couverte'])}")
    if not morceaux:
        return "Aucun contexte supplémentaire."
    return " ; ".join(morceaux)


def carte_alerte(alerte: dict[str, Any]) -> str:
    severite = severite_lisible(alerte.get("severite", "information"))
    date_texte = ""
    if alerte.get("date"):
        date_texte = formater_date_francaise(str(alerte["date"]))
    elif alerte.get("date_debut") and alerte.get("date_fin"):
        date_texte = formater_periode_francaise(str(alerte["date_debut"]), str(alerte["date_fin"]))
    identifiant = alerte.get("identifiant_evenement")
    if not identifiant and isinstance(alerte.get("identifiants_evenements"), list) and alerte["identifiants_evenements"]:
        identifiant = alerte["identifiants_evenements"][0]
    return (
        f"<li class=\"alerte alerte-{escape(severite)}\">"
        f"<h3>{escape(type_alerte_lisible(alerte.get('type')))}</h3>"
        f"<p><strong>Sévérité</strong> : {escape(severite)}</p>"
        f"<p><strong>Date ou période</strong> : {escape(date_texte or TIRET)}</p>"
        f"<p><strong>Compteur</strong> : {escape(str(alerte.get('compteur', TIRET)))}</p>"
        f"<p><strong>Événement</strong> : {escape(str(identifiant or TIRET))}</p>"
        f"<p><strong>Résumé humain</strong> : {escape(resume_alerte(alerte))}</p>"
        f"<details><summary>Détails techniques</summary><pre>{serialiser_objet(alerte)}</pre></details>"
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
    par_date: dict[str, dict[str, dict[str, Any]]] = {}
    for demi_journee in demi_journees:
        if not isinstance(demi_journee, dict):
            continue
        date_iso = str(demi_journee.get("date", ""))
        portion = str(demi_journee.get("portion", ""))
        if not date_iso or not portion:
            continue
        par_date.setdefault(date_iso, {})[portion] = demi_journee

    dates_tries = sorted(par_date.keys())
    date_precedente = None
    for date_iso in dates_tries:
        if est_debut_de_mois(date_iso, date_precedente):
            morceaux.append(f"<div class=\"repere-mois\">{escape(formater_mois_annee(date_iso))}</div>")
        jour = date_iso_vers_objet(date_iso)
        cases = []
        for portion, etiquette in (("matin", "M"), ("apres_midi", "A")):
            demi_journee = par_date[date_iso].get(portion, {})
            titre = f"{formater_date_francaise(date_iso)} {portion}"
            classes = classes_demi_journee(demi_journee) if demi_journee else "case-demi-journee"
            cases.append(
                f"<span class=\"{classes}\" title=\"{escape(titre)}\">{etiquette}</span>"
            )
        morceaux.append(
            "<span class=\"bloc-jour\">"
            f"<span class=\"numero-jour\">{jour.day}</span>"
            f"<span class=\"cases-jour\">{''.join(cases)}</span>"
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
        ligne = (
            f"{detail.get('compteur', '?')} : demandée {formater_quantite_jour(detail.get('quantite_demandee'))}, "
            f"appliquée {formater_quantite_jour(detail.get('quantite_appliquee'))}"
        )
        if float(detail.get("quantite_non_couverte") or 0.0) > 0:
            ligne += f", non couverte {formater_quantite_jour(detail.get('quantite_non_couverte'))}"
        lignes.append(ligne)
    return "<br>".join(escape(ligne) for ligne in lignes) if lignes else "Aucune consommation détaillée."


def tableau_soldes_concernes(soldes_avant: dict[str, Any], soldes_apres: dict[str, Any], compteurs: list[str]) -> str:
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
        "<div class=\"tableau-defilable\">"
        "<table><thead><tr><th>Compteur</th><th>Avant</th><th>Après</th></tr></thead>"
        f"<tbody>{''.join(lignes)}</tbody></table>"
        "</div>"
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
        lignes_detail = [
            f"<dt>Date</dt><dd>{escape(date_lisible)}</dd>",
            f"<dt>Portion</dt><dd>{escape(str(demi_journee.get('portion', '')))}</dd>",
            f"<dt>Compteurs consommés</dt><dd>{escape(', '.join(compteurs) if compteurs else 'Aucun')}</dd>",
            f"<dt>Résumé des consommations</dt><dd>{resume_consommations_detaillees(details)}</dd>",
            f"<dt>Soldes avant/après</dt><dd>{tableau_soldes_concernes(demi_journee.get('soldes_avant', {}), demi_journee.get('soldes_apres', {}), compteurs) if compteurs else 'Aucun compteur concerné.'}</dd>",
        ]
        if alertes:
            lignes_detail.append(
                f"<dt>Alertes</dt><dd>{escape(', '.join(type_alerte_lisible(alerte.get('type')) for alerte in alertes if isinstance(alerte, dict)))}</dd>"
            )
        blocs.append(
            "<article class=\"detail-demi-journee\">"
            f"<h3>{escape(date_lisible)} - {escape(str(demi_journee.get('portion', '')))}</h3>"
            "<dl>"
            f"{''.join(lignes_detail)}"
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


def agreger_evenements_projetes(
    demi_journees: list[Any],
    alertes_globales: list[Any] | None = None,
) -> list[dict[str, Any]]:
    agregats: dict[str, dict[str, Any]] = {}

    for demi_journee in demi_journees:
        if not isinstance(demi_journee, dict):
            continue
        date_iso = str(demi_journee.get("date", ""))
        portion = str(demi_journee.get("portion", ""))
        evenements = demi_journee.get("evenements", [])
        if not isinstance(evenements, list):
            evenements = []
        infos_evenements = {
            str(evenement.get("identifiant")): evenement
            for evenement in evenements
            if isinstance(evenement, dict) and evenement.get("identifiant")
        }
        details = demi_journee.get("consommations_detaillees", [])
        if not isinstance(details, list):
            details = []
        alertes_demi = demi_journee.get("alertes", [])
        if not isinstance(alertes_demi, list):
            alertes_demi = []

        for detail in details:
            if not isinstance(detail, dict):
                continue
            identifiant = str(detail.get("identifiant_evenement", "")).strip()
            if not identifiant:
                continue
            evenement = infos_evenements.get(identifiant, {})
            agregat = agregats.setdefault(
                identifiant,
                {
                    "identifiant_evenement": identifiant,
                    "source": evenement.get("source", detail.get("source", "")),
                    "libelle": evenement.get("libelle", identifiant),
                    "dates": [],
                    "portions": [],
                    "compteurs": {},
                    "quantite_demandee_totale": 0.0,
                    "quantite_appliquee_totale": 0.0,
                    "quantite_non_couverte_totale": 0.0,
                    "priorite": detail.get("priorite"),
                    "alertes": [],
                    "alertes_vues": set(),
                    "details_techniques": [],
                },
            )

            if date_iso and date_iso not in agregat["dates"]:
                agregat["dates"].append(date_iso)
            if portion and portion not in agregat["portions"]:
                agregat["portions"].append(portion)

            compteur = str(detail.get("compteur", ""))
            if compteur:
                compteurs = agregat["compteurs"]
                compteurs.setdefault(
                    compteur,
                    {
                        "quantite_demandee": 0.0,
                        "quantite_appliquee": 0.0,
                        "quantite_non_couverte": 0.0,
                    },
                )
                compteurs[compteur]["quantite_demandee"] += float(detail.get("quantite_demandee") or 0.0)
                compteurs[compteur]["quantite_appliquee"] += float(detail.get("quantite_appliquee") or 0.0)
                compteurs[compteur]["quantite_non_couverte"] += float(detail.get("quantite_non_couverte") or 0.0)

            agregat["quantite_demandee_totale"] += float(detail.get("quantite_demandee") or 0.0)
            agregat["quantite_appliquee_totale"] += float(detail.get("quantite_appliquee") or 0.0)
            agregat["quantite_non_couverte_totale"] += float(detail.get("quantite_non_couverte") or 0.0)
            agregat["details_techniques"].append(
                {
                    "date": date_iso,
                    "portion": portion,
                    "detail": detail,
                }
            )

            for alerte in alertes_demi:
                if not isinstance(alerte, dict):
                    continue
                identifiants = []
                if alerte.get("identifiant_evenement"):
                    identifiants.append(str(alerte["identifiant_evenement"]))
                if isinstance(alerte.get("identifiants_evenements"), list):
                    identifiants.extend(str(valeur) for valeur in alerte["identifiants_evenements"])
                if identifiant in identifiants:
                    signature = json.dumps(alerte, ensure_ascii=False, sort_keys=True)
                    if signature not in agregat["alertes_vues"]:
                        agregat["alertes"].append(alerte)
                        agregat["alertes_vues"].add(signature)

    for alerte in alertes_globales or []:
        if not isinstance(alerte, dict):
            continue
        identifiants = []
        if alerte.get("identifiant_evenement"):
            identifiants.append(str(alerte["identifiant_evenement"]))
        if isinstance(alerte.get("identifiants_evenements"), list):
            identifiants.extend(str(valeur) for valeur in alerte["identifiants_evenements"])
        for identifiant in identifiants:
            if identifiant in agregats:
                signature = json.dumps(alerte, ensure_ascii=False, sort_keys=True)
                if signature not in agregats[identifiant]["alertes_vues"]:
                    agregats[identifiant]["alertes"].append(alerte)
                    agregats[identifiant]["alertes_vues"].add(signature)

    resultat = []
    for identifiant, agregat in agregats.items():
        dates_tries = sorted(agregat["dates"])
        portions_tries = sorted(agregat["portions"], key=ordre_portion)
        resultat.append(
            {
                "identifiant_evenement": identifiant,
                "source": agregat["source"],
                "libelle": agregat["libelle"],
                "date_debut": dates_tries[0] if dates_tries else None,
                "date_fin": dates_tries[-1] if dates_tries else None,
                "portions": portions_tries,
                "compteurs": agregat["compteurs"],
                "quantite_demandee_totale": agregat["quantite_demandee_totale"],
                "quantite_appliquee_totale": agregat["quantite_appliquee_totale"],
                "quantite_non_couverte_totale": agregat["quantite_non_couverte_totale"],
                "priorite": agregat["priorite"],
                "alertes": agregat["alertes"],
                "details_techniques": agregat["details_techniques"],
            }
        )

    return sorted(
        resultat,
        key=lambda evenement: (
            evenement["date_debut"] or "",
            evenement["date_fin"] or "",
            evenement["identifiant_evenement"],
        ),
    )


def titre_evenement_projete(evenement: dict[str, Any]) -> str:
    date_debut = evenement.get("date_debut")
    date_fin = evenement.get("date_fin")
    portions = evenement.get("portions", [])
    if date_debut and date_fin and date_debut == date_fin and len(portions) == 1:
        return f"{formater_date_francaise(str(date_debut))} — {portions[0]}"
    if date_debut and date_fin:
        return formater_periode_francaise(str(date_debut), str(date_fin))
    if date_debut:
        return formater_date_francaise(str(date_debut))
    return evenement.get("identifiant_evenement", "Événement projeté")


def lignes_compteurs_evenement(evenement: dict[str, Any]) -> str:
    lignes = []
    for compteur, quantites in sorted(evenement.get("compteurs", {}).items()):
        if not isinstance(quantites, dict):
            continue
        quantite_appliquee = float(quantites.get("quantite_appliquee") or 0.0)
        quantite_demandee = float(quantites.get("quantite_demandee") or 0.0)
        quantite_non_couverte = float(quantites.get("quantite_non_couverte") or 0.0)
        ligne = f"{compteur} : {formater_quantite_jour(quantite_appliquee)}"
        if quantite_non_couverte > 0:
            ligne += f" · demandé {formater_quantite_jour(quantite_demandee)}"
        lignes.append(f"<p class=\"ligne-compteur\">{escape(ligne)}</p>")
    return "".join(lignes)


def bloc_evenements_projetes(evenements: list[dict[str, Any]]) -> str:
    cartes = []
    for evenement in evenements:
        alertes = evenement.get("alertes", [])
        if not isinstance(alertes, list):
            alertes = []
        quantite_non_couverte = float(evenement.get("quantite_non_couverte_totale") or 0.0)
        resume_alertes = ""
        if alertes:
            resume_alertes = (
                f"<p class=\"resume-alerte\">⚠ {len(alertes)} alerte{'s' if len(alertes) > 1 else ''}</p>"
            )
        bloc_non_couvert = ""
        if quantite_non_couverte > 0:
            bloc_non_couvert = (
                f"<p class=\"resume-non-couvert\">Non couvert : {escape(formater_quantite_jour(quantite_non_couverte))}</p>"
            )
        cartes.append(
            "<article class=\"carte carte-evenement-projete\">"
            f"<p class=\"titre-evenement-projete\">{escape(titre_evenement_projete(evenement))}</p>"
            f"<p class=\"meta-evenement\">{escape(str(evenement.get('libelle') or evenement.get('identifiant_evenement')))}</p>"
            f"{lignes_compteurs_evenement(evenement)}"
            f"{bloc_non_couvert}"
            f"{resume_alertes}"
            f"<details><summary>Détails techniques</summary><pre>{serialiser_objet(evenement)}</pre></details>"
            "</article>"
        )
    contenu = "".join(cartes) if cartes else "<p>Aucun événement projeté.</p>"
    return f"""
    <section class="carte">
      <h2>Événements projetés</h2>
      <div class="grille-evenements">{contenu}</div>
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


def navigation_vues() -> str:
    boutons = []
    for index, (identifiant, titre) in enumerate(VUES):
        est_active = index == 0
        boutons.append(
            f"<button type=\"button\" class=\"onglet{' onglet-actif' if est_active else ''}\" "
            f"data-cible=\"{escape(identifiant)}\" aria-selected=\"{'true' if est_active else 'false'}\">"
            f"{escape(titre)}</button>"
        )
    return f"""
    <nav class="barre-vues" aria-label="Navigation des vues">
      {''.join(boutons)}
    </nav>
    """


def envelopper_vue(identifiant: str, titre: str, contenu: str, active: bool = False) -> str:
    return (
        f"<section id=\"{escape(identifiant)}\" class=\"vue-tableau-de-bord{' vue-active' if active else ''}\" "
        f"data-vue=\"{escape(identifiant)}\" data-titre=\"{escape(titre)}\">"
        f"{contenu}"
        "</section>"
    )


def script_onglets() -> str:
    return """
    <script>
    (function () {
      const boutons = Array.from(document.querySelectorAll('.onglet'));
      const vues = Array.from(document.querySelectorAll('.vue-tableau-de-bord'));
      function activerVue(id) {
        vues.forEach((vue) => {
          const active = vue.dataset.vue === id;
          vue.classList.toggle('vue-active', active);
        });
        boutons.forEach((bouton) => {
          const active = bouton.dataset.cible === id;
          bouton.classList.toggle('onglet-actif', active);
          bouton.setAttribute('aria-selected', active ? 'true' : 'false');
        });
      }
      boutons.forEach((bouton) => {
        bouton.addEventListener('click', function () {
          activerVue(bouton.dataset.cible);
        });
      });
      activerVue('vue-ensemble');
    }());
    </script>
    """


def vue_ensemble(periode: dict[str, Any], resume: dict[str, Any], projection: dict[str, Any]) -> str:
    soldes_initiaux = projection.get("soldes_initiaux", {})
    if not isinstance(soldes_initiaux, dict):
        soldes_initiaux = {}
    dates_cibles = projection.get("soldes_aux_dates_cibles", [])
    if not isinstance(dates_cibles, list):
        dates_cibles = []
    debut = str(periode.get("debut", ""))
    fin = str(periode.get("fin", ""))
    periode_lisible = formater_periode_francaise(debut, fin) if debut and fin else TIRET
    return f"""
    <div class="grille-hero">
      <section class="carte carte-majeure">
        <h2>Vue d’ensemble</h2>
        <p class="periode-lisible">{escape(periode_lisible)}</p>
        <p class="note">Cette page reste strictement en lecture seule. Elle présente une projection dérivée et n’édite ni le scénario ni Chronotime.</p>
      </section>
      <section class="resume-cards">
        {cartes_resume(periode, resume, projection)}
      </section>
    </div>
    <div class="grille">
      {tableau_soldes("Soldes initiaux", soldes_initiaux)}
      {tableau_dates_cibles(dates_cibles)}
    </div>
    """


def carte_indicateur_planification(label: str, valeur: Any) -> str:
    return (
        "<article class=\"tuile-resume\">"
        f"<p class=\"tuile-label\">{escape(label)}</p>"
        f"<p class=\"tuile-valeur\">{escape(str(valeur))}</p>"
        "</article>"
    )


def libelle_reste_fin_projection(date_fin: Any) -> str:
    if date_fin:
        return f"Reste au {formater_date_francaise(str(date_fin))}"
    return "Reste en fin de projection"


def tableau_dates_cibles_synthese(dates_cibles: list[Any]) -> str:
    lignes = []
    for cible in dates_cibles:
        if not isinstance(cible, dict):
            continue
        date_lisible = formater_date_francaise(str(cible.get("date"))) if cible.get("date") else TIRET
        lignes.append(
            "<tr>"
            f"<td>{escape(str(cible.get('libelle') or cible.get('identifiant') or TIRET))}</td>"
            f"<td>{escape(date_lisible)}</td>"
            f"<td>{escape(formater_quantite_jour(cible.get('jours_restants_agreges')))}</td>"
            "</tr>"
        )
    corps = "\n".join(lignes) if lignes else "<tr><td colspan=\"3\">Aucune date cible agrégée.</td></tr>"
    return (
        "<section class=\"carte\">"
        "<h3>Dates cibles agrégées</h3>"
        "<div class=\"tableau-defilable\">"
        "<table><thead><tr><th>Date cible</th><th>Date</th><th>Reste agrégé</th></tr></thead>"
        f"<tbody>{corps}</tbody></table>"
        "</div>"
        "</section>"
    )


def liste_echeances_planification(echeances: list[Any]) -> str:
    elements = []
    for echeance in echeances:
        if not isinstance(echeance, dict):
            continue
        date_lisible = formater_date_francaise(str(echeance["date"])) if echeance.get("date") else "Date non renseignée"
        quantite = formater_quantite_jour(echeance.get("quantite"))
        compteur = str(echeance.get("compteur_technique") or TIRET)
        action = str(echeance.get("action_suggeree") or TIRET)
        elements.append(
            "<article class=\"alerte alerte-attention\">"
            f"<h3>{escape(date_lisible)}</h3>"
            f"<p><strong>⚠ {escape(quantite)} expire</strong></p>"
            f"<p>Compteur technique : {escape(compteur)}</p>"
            f"<p>Action : {escape(action)}</p>"
            f"<p class=\"note\">{escape(str(echeance.get('message') or ''))}</p>"
            "</article>"
        )
    contenu = "\n".join(elements) if elements else "<p>Aucune échéance importante détectée.</p>"
    return (
        "<section class=\"carte\">"
        "<h3>Échéances importantes</h3>"
        f"{contenu}"
        "</section>"
    )


def tableau_evenements_consommateurs(evenements: list[Any]) -> str:
    lignes = []
    for evenement in evenements[:10]:
        if not isinstance(evenement, dict):
            continue
        periode = TIRET
        if evenement.get("premiere_date") and evenement.get("derniere_date"):
            periode = formater_periode_francaise(str(evenement["premiere_date"]), str(evenement["derniere_date"]))
        lignes.append(
            "<tr>"
            f"<td>{escape(str(evenement.get('identifiant') or TIRET))}</td>"
            f"<td>{escape(periode)}</td>"
            f"<td>{escape(formater_quantite_jour(evenement.get('jours_consommes')))}</td>"
            "</tr>"
        )
    corps = "\n".join(lignes) if lignes else "<tr><td colspan=\"3\">Aucun événement consommateur.</td></tr>"
    return (
        "<section class=\"carte\">"
        "<h3>Principaux événements consommateurs</h3>"
        "<div class=\"tableau-defilable\">"
        "<table><thead><tr><th>Événement</th><th>Période</th><th>Jours posés</th></tr></thead>"
        f"<tbody>{corps}</tbody></table>"
        "</div>"
        "</section>"
    )


def liste_signaux_planification(signaux: list[Any]) -> str:
    elements = []
    for signal in signaux:
        if not isinstance(signal, dict):
            continue
        severite = str(signal.get("severite") or "information")
        elements.append(
            f"<li class=\"alerte alerte-{escape(severite)}\">"
            f"<h3>{escape(str(signal.get('type') or 'signal'))}</h3>"
            f"<p><strong>Sévérité</strong> : {escape(severite)}</p>"
            f"<p>{escape(str(signal.get('message') or 'Signal de planification.'))}</p>"
            f"<details><summary>Détails techniques du signal</summary><pre>{serialiser_objet(signal.get('details', {}))}</pre></details>"
            "</li>"
        )
    contenu = "\n".join(elements) if elements else "<li>Aucun signal.</li>"
    return (
        "<section class=\"carte\">"
        "<h3>Signaux</h3>"
        f"<ul class=\"liste-alertes\">{contenu}</ul>"
        "</section>"
    )


def details_techniques_planification(synthese: dict[str, Any]) -> str:
    details = synthese.get("details_techniques", {})
    par_compteur = details.get("par_compteur", {}) if isinstance(details, dict) else {}
    return (
        "<section class=\"carte\">"
        "<details>"
        "<summary>Détails techniques par compteur</summary>"
        f"<pre>{serialiser_objet(par_compteur)}</pre>"
        "</details>"
        "</section>"
    )


def section_secondaire_planification(resume: dict[str, Any]) -> str:
    return (
        "<section class=\"carte\">"
        "<h3>Informations secondaires</h3>"
        f"<p><strong>Jours ajoutés dans la période</strong> : {escape(formater_quantite_jour(resume.get('jours_credites')))}</p>"
        f"<p><strong>Variation totale agrégée</strong> : {escape(formater_quantite_jour(resume.get('variation_totale')))}</p>"
        "</section>"
    )


def somme_soldes_numeriques(soldes: Any) -> float | None:
    if not isinstance(soldes, dict):
        return None
    total = 0.0
    au_moins_un_solde = False
    for valeur in soldes.values():
        if isinstance(valeur, (int, float)):
            total += float(valeur)
            au_moins_un_solde = True
    return total if au_moins_un_solde else None


def derniere_demi_journee_avec_soldes(demi_journees: list[Any]) -> dict[str, Any] | None:
    for demi_journee in reversed(demi_journees):
        if isinstance(demi_journee, dict) and isinstance(demi_journee.get("soldes_apres"), dict):
            return demi_journee
    return None


def soldes_fin_projection(projection: dict[str, Any], demi_journees: list[Any]) -> dict[str, Any]:
    derniere = derniere_demi_journee_avec_soldes(demi_journees)
    if derniere is not None:
        return derniere.get("soldes_apres", {})
    soldes_initiaux = projection.get("soldes_initiaux", {})
    return soldes_initiaux if isinstance(soldes_initiaux, dict) else {}


def barre_outils_gauche() -> str:
    return """
    <aside class="barre-outils-gauche" aria-label="Barre d’outils de planification">
      <h3>Outils</h3>
      <button type="button" class="outil-passif outil-desactive" disabled>Poser des jours</button>
      <button type="button" class="outil-passif outil-desactive" disabled>Scinder</button>
      <button type="button" class="outil-passif outil-desactive" disabled>Fusionner</button>
      <h3>Affichage</h3>
      <button type="button" class="outil-passif outil-actif" aria-pressed="true">Général</button>
      <button type="button" class="outil-passif" aria-pressed="false">Détaillé</button>
    </aside>
    """


def tableau_detail_compteurs(soldes: dict[str, Any]) -> str:
    lignes = []
    for compteur, valeur in sorted(soldes.items()):
        lignes.append(
            "<tr>"
            f"<th>{escape(str(compteur))}</th>"
            f"<td>{escape(formater_quantite_jour(valeur))}</td>"
            "</tr>"
        )
    corps = "\n".join(lignes) if lignes else "<tr><td colspan=\"2\">Aucun solde disponible.</td></tr>"
    return (
        "<div class=\"tableau-defilable\">"
        "<table><thead><tr><th>Compteur</th><th>Solde final</th></tr></thead>"
        f"<tbody>{corps}</tbody></table>"
        "</div>"
    )


def barre_infos_droite(projection: dict[str, Any], demi_journees: list[Any]) -> str:
    soldes_finaux = soldes_fin_projection(projection, demi_journees)
    total_restant = somme_soldes_numeriques(soldes_finaux)
    total_restant_texte = formater_quantite_jour(total_restant) if total_restant is not None else "Niveau non disponible"
    return f"""
    <aside class="barre-infos-droite" aria-label="Barre d’informations de planification">
      <h3>Total restant</h3>
      <p class="valeur-info">{escape(total_restant_texte)}</p>
      <p class="note">reste agrégé provisoire en fin de projection</p>
      <h3>Dont prévus pour cette année</h3>
      <p>non calculé</p>
      <h3>Détail compteurs</h3>
      {tableau_detail_compteurs(soldes_finaux)}
      <h3>Prochaine expiration</h3>
      <p>non calculée</p>
      <h3>Sélection</h3>
      <p>aucune sélection</p>
    </aside>
    """


def date_infos_calendrier(demi_journees: list[Any]) -> dict[str, dict[str, Any]]:
    infos: dict[str, dict[str, Any]] = {}
    for demi_journee in demi_journees:
        if not isinstance(demi_journee, dict):
            continue
        date_iso = str(demi_journee.get("date", ""))
        if not date_iso:
            continue
        info = infos.setdefault(
            date_iso,
            {
                "consommations": {},
                "alertes": False,
            },
        )
        if demi_journee.get("alertes"):
            info["alertes"] = True
        details = demi_journee.get("consommations_detaillees", [])
        if not isinstance(details, list):
            details = []
        for detail in details:
            if not isinstance(detail, dict):
                continue
            compteur = str(detail.get("compteur") or "")
            quantite = detail.get("quantite_appliquee")
            if compteur and isinstance(quantite, (int, float)):
                consommations = info["consommations"]
                consommations[compteur] = float(consommations.get(compteur, 0.0)) + float(quantite)
    return infos


def titre_jour_calendrier(date_iso: str, info: dict[str, Any]) -> str:
    morceaux = [formater_date_francaise(date_iso)]
    consommations = info.get("consommations", {})
    if isinstance(consommations, dict) and consommations:
        resume = ", ".join(
            f"{compteur} {formater_nombre_francais(quantite)}"
            for compteur, quantite in sorted(consommations.items())
        )
        morceaux.append(f"consommation : {resume}")
    if info.get("alertes"):
        morceaux.append("alerte")
    return " — ".join(morceaux)


def vue_calendrier_passif(demi_journees: list[Any]) -> str:
    infos = date_infos_calendrier(demi_journees)
    mois: dict[str, list[str]] = {}
    for date_iso in sorted(infos):
        mois.setdefault(formater_mois_annee(date_iso), []).append(date_iso)
    blocs_mois = []
    for libelle_mois, dates in mois.items():
        jours = []
        for date_iso in dates:
            info = infos[date_iso]
            classes = ["jour-calendrier"]
            if info.get("consommations"):
                classes.append("jour-avec-consommation")
            if info.get("alertes"):
                classes.append("jour-avec-alerte")
            jour = date_iso_vers_objet(date_iso).day
            jours.append(
                f"<span class=\"{' '.join(classes)}\" title=\"{escape(titre_jour_calendrier(date_iso, info))}\">{jour}</span>"
            )
        blocs_mois.append(
            "<section class=\"mois-calendrier\">"
            f"<h4>{escape(libelle_mois)}</h4>"
            f"<div class=\"jours-calendrier\">{''.join(jours)}</div>"
            "</section>"
        )
    contenu = "".join(blocs_mois) if blocs_mois else "<p>Aucune date projetée.</p>"
    return f"""
    <section class="vue-calendrier-passif">
      <h3>Calendrier</h3>
      {contenu}
    </section>
    """


def points_reste_agrege(demi_journees: list[Any]) -> list[dict[str, Any]]:
    points = []
    for demi_journee in demi_journees:
        if not isinstance(demi_journee, dict):
            continue
        niveau = somme_soldes_numeriques(demi_journee.get("soldes_apres"))
        if niveau is None:
            continue
        points.append(
            {
                "date": demi_journee.get("date"),
                "portion": demi_journee.get("portion"),
                "niveau": niveau,
            }
        )
    return points


def courbe_reste_agrege(points: list[dict[str, Any]]) -> str:
    if not points:
        return "<p>Niveau non disponible</p>"
    largeur = 680
    hauteur = 170
    marge = 18
    valeurs = [float(point["niveau"]) for point in points]
    minimum = min(valeurs)
    maximum = max(valeurs)
    amplitude = maximum - minimum or 1.0
    coordonnees = []
    for index, point in enumerate(points):
        x = marge + (index * (largeur - 2 * marge) / max(len(points) - 1, 1))
        y = hauteur - marge - ((float(point["niveau"]) - minimum) * (hauteur - 2 * marge) / amplitude)
        coordonnees.append((x, y, point))
    polyline = " ".join(f"{x:.2f},{y:.2f}" for x, y, _point in coordonnees)
    points_svg = []
    pas = max(1, len(coordonnees) // 24)
    for index, (x, y, point) in enumerate(coordonnees):
        if index % pas != 0 and index != len(coordonnees) - 1:
            continue
        titre = (
            f"{formater_date_francaise(str(point.get('date')))} "
            f"{point.get('portion') or ''} — reste agrégé provisoire {formater_quantite_jour(point.get('niveau'))}"
        )
        points_svg.append(
            f"<circle class=\"point-reste-agrege\" cx=\"{x:.2f}\" cy=\"{y:.2f}\" r=\"3\"><title>{escape(titre)}</title></circle>"
        )
    return (
        f"<svg class=\"courbe-reste-agrege\" viewBox=\"0 0 {largeur} {hauteur}\" role=\"img\" "
        "aria-label=\"Courbe du reste agrégé provisoire\">"
        f"<polyline points=\"{polyline}\" fill=\"none\" />"
        f"{''.join(points_svg)}"
        "</svg>"
    )


def vue_frise_niveau_passive(demi_journees: list[Any], alertes: list[Any]) -> str:
    evenements = agreger_evenements_projetes(demi_journees, alertes)
    evenements = evenements[:8]
    blocs = []
    for evenement in evenements:
        blocs.append(
            "<article class=\"bloc-frise-passif\">"
            f"<strong>{escape(titre_evenement_projete(evenement))}</strong>"
            f"<span>{escape(str(evenement.get('identifiant_evenement') or ''))}</span>"
            f"<span>{escape(formater_quantite_jour(evenement.get('quantite_appliquee_totale')))}</span>"
            "</article>"
        )
    contenu_blocs = "".join(blocs) if blocs else "<p>Aucun bloc projeté.</p>"
    points = points_reste_agrege(demi_journees)
    return f"""
    <section class="vue-frise-niveau">
      <h3>Frise + niveau</h3>
      <div class="ligne-blocs-passifs">{contenu_blocs}</div>
      <div class="niveau-reste-agrege">
        <h4>reste agrégé provisoire</h4>
        <p class="note">Formule temporaire : somme simple des soldes_apres numériques. N’inclut pas encore réserves, expirations fines, acquisitions futures ni règles d’allocation complètes.</p>
        {courbe_reste_agrege(points)}
      </div>
    </section>
    """


def bloc_synthese_planification(synthese: dict[str, Any] | None = None) -> str:
    if synthese is None:
        return "<section class=\"carte\"><p class=\"note\">Aucune synthèse de planification fournie.</p></section>"

    resume = synthese.get("resume_global", {})
    if not isinstance(resume, dict):
        resume = {}
    dates_cibles = synthese.get("soldes_agreges_aux_dates_cibles", [])
    if not isinstance(dates_cibles, list):
        dates_cibles = []
    evenements = synthese.get("consommations_par_evenement", [])
    if not isinstance(evenements, list):
        evenements = []
    echeances = synthese.get("echeances", [])
    if not isinstance(echeances, list):
        echeances = []
    signaux = synthese.get("signaux", [])
    if not isinstance(signaux, list):
        signaux = []
    indicateurs = [
        ("Statut global", resume.get("statut", TIRET)),
        ("Jours posés", formater_quantite_jour(resume.get("jours_consommes"))),
        ("Jours expirés", formater_quantite_jour(resume.get("jours_expires"))),
        (libelle_reste_fin_projection(resume.get("date_fin_projection")), formater_quantite_jour(resume.get("jours_finaux_agreges"))),
    ]
    cartes = "".join(carte_indicateur_planification(label, valeur) for label, valeur in indicateurs)
    return f"""
    <section class="carte carte-majeure">
      <h2>Planification</h2>
      <p class="note">
        Synthèse utilisateur en lecture seule issue de <code>synthese.planification</code>.
        Les compteurs Chronotime restent disponibles comme détail technique, mais la lecture principale agrège les jours.
      </p>
      <div class="resume-cards">{cartes}</div>
    </section>
    <div class="grille">
      {liste_echeances_planification(echeances)}
      {tableau_dates_cibles_synthese(dates_cibles)}
      {tableau_evenements_consommateurs(evenements)}
    </div>
    {section_secondaire_planification(resume)}
    {liste_signaux_planification(signaux)}
    {details_techniques_planification(synthese)}
    """


def vue_planification(
    projection: dict[str, Any],
    demi_journees: list[Any],
    alertes: list[Any],
    synthese: dict[str, Any] | None = None,
) -> str:
    return f"""
    <section class="interface-planification">
      {barre_outils_gauche()}
      <div class="zone-centrale-planification">
        <h2>Planification</h2>
        <div class="sous-vues-planification" aria-label="Vues passives de planification">
          <span class="sous-vue-active">Calendrier</span>
          <span>Frise + niveau</span>
        </div>
        {vue_calendrier_passif(demi_journees)}
        {vue_frise_niveau_passive(demi_journees, alertes)}
        {bloc_synthese_planification(synthese)}
      </div>
      {barre_infos_droite(projection, demi_journees)}
    </section>
    """


def vue_frise(demi_journees: list[Any]) -> str:
    return (
        generer_frise(demi_journees)
        + "<section class=\"carte\"><p class=\"note\">Seules les demi-journées projetées dans la période courante sont représentées ici.</p></section>"
    )


def vue_soldes(projection: dict[str, Any], chronologie: dict[str, Any] | None = None) -> str:
    soldes_initiaux = projection.get("soldes_initiaux", {})
    if not isinstance(soldes_initiaux, dict):
        soldes_initiaux = {}
    dates_cibles = projection.get("soldes_aux_dates_cibles", [])
    if not isinstance(dates_cibles, list):
        dates_cibles = []
    return f"""
    <div class="grille">
      {tableau_soldes("Soldes initiaux", soldes_initiaux)}
      {tableau_dates_cibles(dates_cibles)}
    </div>
    {section_chronologie_soldes(chronologie)}
    """


def vue_alertes(alertes: list[Any]) -> str:
    return liste_alertes(alertes)


def vue_evenements(demi_journees: list[Any], alertes: list[Any]) -> str:
    evenements = agreger_evenements_projetes(demi_journees, alertes)
    return bloc_evenements_projetes(evenements)


def vue_technique(
    projection: dict[str, Any],
    periode: dict[str, Any],
    resume: dict[str, Any],
    demi_journees: list[Any],
) -> str:
    parametres = projection.get("parametres_projection", {})
    if not isinstance(parametres, dict):
        parametres = {}
    resume_technique = {
        "source": projection.get("source", TIRET),
        "periode.debut": periode.get("debut", TIRET),
        "periode.fin": periode.get("fin", TIRET),
        "nombre_demi_journees": resume.get("nombre_demi_journees", TIRET),
        "nombre_evenements_sources": resume.get("nombre_evenements_sources", TIRET),
        "nombre_alertes": resume.get("nombre_alertes", TIRET),
    }
    lignes = []
    for cle, valeur in resume_technique.items():
        lignes.append(f"<tr><th>{escape(str(cle))}</th><td>{escape(str(valeur))}</td></tr>")
    return f"""
    <section class="carte">
      <h2>Technique</h2>
      <p class="note">Cette vue rassemble les paramètres et limites connus sans afficher tout le JSON complet au chargement.</p>
      <table>
        <tbody>{''.join(lignes)}</tbody>
      </table>
    </section>
    <section class="carte">
      <h3>Paramètres de projection</h3>
      <details>
        <summary>Détails techniques</summary>
        <pre>{serialiser_objet(parametres)}</pre>
      </details>
    </section>
    <section class="carte">
      <h3>Limites connues</h3>
      <ul class="liste-limites">
        <li>La vue reste en lecture seule et n’édite pas la projection.</li>
        <li>Aucune écriture Chronotime, aucun appel HTTP et aucune automatisation navigateur ne sont ajoutés.</li>
        <li>Les règles complètes sur les jours fériés, la parentalité, les chevauchements d’agenda et l’optimisation ne sont pas couvertes ici.</li>
      </ul>
    </section>
    {bloc_details_demi_journees(demi_journees)}
    <section class="carte">
      <h3>Projection complète</h3>
      <details>
        <summary>Détails techniques</summary>
        <pre>{serialiser_objet(projection)}</pre>
      </details>
    </section>
    """


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
      max-width: 1220px;
      margin: 0 auto;
      padding: 24px 18px 56px;
    }
    .hero {
      padding: 20px 22px 16px;
      border: 1px solid var(--trait);
      border-radius: 28px 28px 18px 18px;
      background: rgba(255, 250, 240, 0.82);
      box-shadow: var(--ombre);
      position: sticky;
      top: 0;
      z-index: 10;
      backdrop-filter: blur(10px);
    }
    h1 {
      margin: 0 0 6px;
      font-size: clamp(1.4rem, 2.4vw, 2.2rem);
      line-height: 1.05;
      letter-spacing: -0.02em;
    }
    h2 {
      margin: 0 0 16px;
      font-size: 1.35rem;
      color: var(--accent-fort);
    }
    h3 {
      margin: 0 0 10px;
      font-size: 1.05rem;
      color: var(--accent-fort);
    }
    .note {
      color: var(--muted);
      max-width: 820px;
      font-size: 0.95rem;
    }
    .barre-vues {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
      padding-top: 14px;
      border-top: 1px solid rgba(31, 42, 36, 0.12);
    }
    .onglet {
      border: 1px solid var(--trait);
      border-radius: 999px;
      padding: 10px 16px;
      background: rgba(255, 250, 240, 0.65);
      color: var(--accent-fort);
      font: inherit;
      cursor: pointer;
      transition: transform 120ms ease, background 120ms ease, color 120ms ease;
    }
    .onglet:hover {
      transform: translateY(-1px);
      background: rgba(20, 107, 95, 0.12);
    }
    .onglet-actif {
      background: var(--accent);
      color: white;
      border-color: var(--accent-fort);
      box-shadow: 0 10px 20px rgba(20, 107, 95, 0.22);
    }
    .vue-tableau-de-bord {
      display: none;
      margin-top: 22px;
      animation: apparition 180ms ease;
    }
    .vue-active {
      display: block;
    }
    @keyframes apparition {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .grille, .grille-hero {
      display: grid;
      gap: 18px;
    }
    .grille {
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    }
    .grille-hero {
      grid-template-columns: minmax(280px, 1.2fr) minmax(320px, 1.8fr);
      align-items: start;
    }
    .resume-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
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
      font-size: 1.3rem;
      color: var(--accent-fort);
    }
    .carte {
      margin-top: 14px;
      padding: 18px;
      border: 1px solid var(--trait);
      border-radius: 22px;
      background: rgba(255, 250, 240, 0.9);
      box-shadow: 0 10px 26px rgba(41, 31, 19, 0.08);
    }
    .carte-majeure {
      min-height: 100%;
    }
    .periode-lisible {
      margin: 0 0 12px;
      font-size: clamp(1.4rem, 2vw, 2rem);
      color: var(--accent-fort);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      overflow: hidden;
      border-radius: 14px;
    }
    .tableau-defilable {
      overflow-x: auto;
      max-width: 100%;
    }
    th, td {
      padding: 8px 10px;
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
    .liste-alertes, .liste-limites {
      padding-left: 0;
      list-style: none;
      margin: 0;
    }
    .liste-limites li {
      margin: 8px 0;
      padding-left: 16px;
      position: relative;
    }
    .liste-limites li::before {
      content: "•";
      position: absolute;
      left: 0;
      color: var(--accent);
    }
    .alerte {
      margin: 10px 0;
      padding: 14px;
      border-left: 6px solid var(--info);
      background: rgba(53, 100, 143, 0.08);
      border-radius: 14px;
    }
    .alerte-confirmation {
      border-left-color: var(--confirmation);
      background: rgba(155, 107, 0, 0.1);
    }
    .alerte-bloquant {
      border-left-color: var(--alerte);
      background: rgba(177, 59, 46, 0.1);
    }
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
    .bloc-jour {
      display: inline-flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      min-width: 30px;
    }
    .numero-jour {
      color: var(--muted);
      font-size: 0.72rem;
      line-height: 1;
      font-variant-numeric: tabular-nums;
    }
    .cases-jour {
      display: inline-flex;
      gap: 3px;
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
    .grille-evenements {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
    }
    .carte-evenement-projete {
      margin-top: 0;
      padding: 16px 18px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .titre-evenement-projete {
      margin: 0;
      font-size: 1.05rem;
      color: var(--accent-fort);
      font-weight: 700;
    }
    .meta-evenement {
      margin: 0;
      color: var(--muted);
      font-size: 0.92rem;
    }
    .ligne-compteur,
    .resume-non-couvert,
    .resume-alerte {
      margin: 0;
    }
    .resume-non-couvert {
      color: var(--alerte);
      font-weight: 700;
    }
    .resume-alerte {
      color: var(--confirmation);
      font-weight: 700;
    }
    .interface-planification {
      display: grid;
      grid-template-columns: minmax(150px, 0.7fr) minmax(360px, 2.4fr) minmax(240px, 1fr);
      gap: 16px;
      align-items: start;
    }
    .barre-outils-gauche,
    .barre-infos-droite,
    .zone-centrale-planification {
      padding: 16px;
      border: 1px solid var(--trait);
      border-radius: 18px;
      background: rgba(255, 250, 240, 0.9);
      box-shadow: 0 10px 26px rgba(41, 31, 19, 0.08);
    }
    .barre-outils-gauche,
    .barre-infos-droite {
      position: sticky;
      top: 128px;
    }
    .outil-passif {
      display: block;
      width: 100%;
      margin: 8px 0;
      padding: 9px 10px;
      border: 1px solid var(--trait);
      border-radius: 8px;
      background: #fffaf0;
      color: var(--accent-fort);
      font: inherit;
      text-align: left;
    }
    .outil-actif {
      background: var(--accent);
      color: white;
      border-color: var(--accent-fort);
    }
    .outil-desactive {
      opacity: 0.48;
      cursor: not-allowed;
    }
    .valeur-info {
      margin: 0;
      color: var(--accent-fort);
      font-size: 1.35rem;
      font-weight: 700;
    }
    .sous-vues-planification {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 14px;
    }
    .sous-vues-planification span {
      padding: 6px 10px;
      border: 1px solid var(--trait);
      border-radius: 999px;
      color: var(--muted);
      background: rgba(255, 255, 255, 0.35);
    }
    .sous-vues-planification .sous-vue-active {
      color: white;
      background: var(--accent);
      border-color: var(--accent-fort);
    }
    .vue-calendrier-passif,
    .vue-frise-niveau {
      margin-top: 14px;
      padding: 14px;
      border: 1px solid rgba(216, 201, 174, 0.8);
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.34);
    }
    .mois-calendrier {
      margin-top: 12px;
    }
    .mois-calendrier h4,
    .niveau-reste-agrege h4 {
      margin: 0 0 8px;
      color: var(--accent-fort);
      text-transform: lowercase;
    }
    .jours-calendrier {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(32px, 1fr));
      gap: 5px;
    }
    .jour-calendrier {
      min-height: 30px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 1px solid #cbbd9f;
      border-radius: 8px;
      background: #fffaf0;
      color: var(--muted);
      font-variant-numeric: tabular-nums;
    }
    .jour-avec-consommation {
      background: rgba(20, 107, 95, 0.16);
      color: var(--accent-fort);
      border-color: var(--accent);
      font-weight: 700;
    }
    .jour-avec-alerte {
      box-shadow: inset 0 0 0 2px rgba(177, 59, 46, 0.5);
    }
    .ligne-blocs-passifs {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 8px;
      margin-bottom: 14px;
    }
    .bloc-frise-passif {
      display: grid;
      gap: 4px;
      padding: 10px;
      border: 1px solid var(--trait);
      border-radius: 8px;
      background: #fffaf0;
    }
    .bloc-frise-passif span {
      color: var(--muted);
      font-size: 0.88rem;
    }
    .niveau-reste-agrege {
      padding-top: 10px;
      border-top: 1px dashed var(--trait);
    }
    .courbe-reste-agrege {
      width: 100%;
      max-height: 190px;
      margin-top: 10px;
      border: 1px solid var(--trait);
      border-radius: 8px;
      background: linear-gradient(180deg, rgba(255, 250, 240, 0.88), rgba(239, 228, 208, 0.8));
    }
    .courbe-reste-agrege polyline {
      stroke: var(--accent);
      stroke-width: 3;
      stroke-linejoin: round;
      stroke-linecap: round;
    }
    .point-reste-agrege {
      fill: var(--accent-fort);
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
    @media (max-width: 860px) {
      .hero {
        position: static;
      }
      .grille-hero {
        grid-template-columns: 1fr;
      }
      .interface-planification {
        grid-template-columns: 1fr;
      }
      .barre-outils-gauche,
      .barre-infos-droite {
        position: static;
      }
    }
    @media (max-width: 720px) {
      .hero { padding: 22px; }
      dl { grid-template-columns: 1fr; }
      .barre-vues {
        gap: 8px;
      }
      .onglet {
        width: 100%;
      }
    }
    """


def generer_html(
    projection: dict[str, Any],
    chronologie: dict[str, Any] | None = None,
    synthese: dict[str, Any] | None = None,
) -> str:
    periode = projection.get("periode", {}) if isinstance(projection.get("periode"), dict) else {}
    resume = projection.get("resume", {}) if isinstance(projection.get("resume"), dict) else {}
    demi_journees = projection.get("demi_journees", [])
    if not isinstance(demi_journees, list):
        demi_journees = []
    alertes = projection.get("alertes", [])
    if not isinstance(alertes, list):
        alertes = []

    contenu_vues = [
        envelopper_vue("vue-ensemble", "Vue d’ensemble", vue_ensemble(periode, resume, projection), active=True),
        envelopper_vue("vue-planification", "Planification", vue_planification(projection, demi_journees, alertes, synthese)),
        envelopper_vue("vue-frise", "Frise", vue_frise(demi_journees)),
        envelopper_vue("vue-soldes", "Soldes", vue_soldes(projection, chronologie)),
        envelopper_vue("vue-alertes", "Alertes", vue_alertes(alertes)),
        envelopper_vue("vue-evenements", "Événements projetés", vue_evenements(demi_journees, alertes)),
        envelopper_vue("vue-technique", "Technique", vue_technique(projection, periode, resume, demi_journees)),
    ]

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
      {navigation_vues()}
    </header>
    {''.join(contenu_vues)}
  </main>
  {script_onglets()}
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
    analyseur.add_argument("--chronologie", type=Path, help="Chemin facultatif du fichier chronologie.soldes.")
    analyseur.add_argument("--synthese", type=Path, help="Chemin facultatif du fichier synthese.planification.")
    analyseur.add_argument("--sortie", type=Path, required=True, help="Chemin du fichier HTML à générer.")
    return analyseur.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = analyser_arguments(argv)
    try:
        projection = charger_projection(arguments.projection)
        chronologie = charger_chronologie(arguments.chronologie) if arguments.chronologie else None
        synthese = charger_synthese(arguments.synthese) if arguments.synthese else None
    except ValueError as erreur:
        raise SystemExit(str(erreur)) from erreur
    ecrire_html(generer_html(projection, chronologie, synthese), arguments.sortie)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
