from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
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
JOURS_SEMAINE_COURTS = ("lun", "mar", "mer", "jeu", "ven", "sam", "dim")
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
      const boutonsSousVues = Array.from(document.querySelectorAll('.bouton-sous-vue'));
      const sousVues = Array.from(document.querySelectorAll('.sous-vue-planification'));
      const boutonsMode = Array.from(document.querySelectorAll('[data-mode-planification]'));
      const boutonsOutils = Array.from(document.querySelectorAll('[data-outil-planification]'));
      const CLE_STOCKAGE_PROTO = 'chronotime.planification.prototype.v1';
      let modePlanification = 'general';
      let outilPlanification = 'selection';
      let blocsLocauxPrototype = [];
      let blocLocalSelectionne = null;
      let dateDebutPose = null;
      let dateSurvolPose = null;
      let poseEnCours = false;
      let etatCentralGui = null;
      // localStorage = persistance prototype ; etatCentralGui = état central courant de la page.
      // etatTransitoireInterface = manipulation en cours, non durable.
      let etatTransitoireInterface = {
        outil_actif: 'selection',
        pose_en_cours: false,
        date_debut_pose: null,
        date_survol_pose: null,
        plage_en_cours: null,
        fantome_calendrier: null,
        fantome_frise: null,
        dernier_resultat_previsualisation: null,
        message_temporaire: null
      };

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

      function activerSousVue(id) {
        sousVues.forEach((vue) => {
          const active = vue.dataset.sousVue === id;
          vue.classList.toggle('sous-vue-planification-active', active);
        });
        boutonsSousVues.forEach((bouton) => {
          const active = bouton.dataset.sousVueCible === id;
          bouton.classList.toggle('sous-vue-active', active);
          bouton.setAttribute('aria-selected', active ? 'true' : 'false');
        });
        if (etatTransitoireInterface && etatTransitoireInterface.plage_en_cours) {
          afficherEtatTransitoireInterface();
        }
      }

      function activerModePlanification(mode) {
        modePlanification = mode === 'detaille' ? 'detaille' : 'general';
        const interfacePlanification = document.querySelector('.interface-planification');
        if (interfacePlanification) {
          interfacePlanification.dataset.modePlanification = modePlanification;
        }
        boutonsMode.forEach((bouton) => {
          const actif = bouton.dataset.modePlanification === modePlanification;
          bouton.classList.toggle('mode-affichage-actif', actif);
          bouton.classList.toggle('outil-actif', actif);
          bouton.setAttribute('aria-pressed', actif ? 'true' : 'false');
        });
        deselectionnerPlanification();
      }

      function activerOutilPlanification(outil) {
        outilPlanification = outil === 'poser' ? 'poser' : 'selection';
        etatTransitoireInterface.outil_actif = outilPlanification;
        const interfacePlanification = document.querySelector('.interface-planification');
        if (interfacePlanification) {
          interfacePlanification.dataset.outilPlanification = outilPlanification;
        }
        boutonsOutils.forEach((bouton) => {
          const actif = bouton.dataset.outilPlanification === outilPlanification;
          bouton.classList.toggle('outil-actif', actif);
          bouton.classList.toggle('outil-selection-actif', actif);
          bouton.setAttribute('aria-pressed', actif ? 'true' : 'false');
        });
        nettoyerFantomeLocal();
        deselectionnerPlanification();
      }

      function libelleSelection(type) {
        if (type === 'jour') { return 'jour calendrier'; }
        if (type === 'bloc') { return 'bloc projeté'; }
        if (type === 'sous-bloc') { return 'sous-bloc'; }
        if (type === 'reste') { return 'reste agrégé provisoire'; }
        return type || 'élément';
      }

      function ajouterChampSelection(conteneur, libelle, valeur, long) {
        const champ = document.createElement('div');
        champ.className = 'champ-selection';
        const etiquette = document.createElement('span');
        etiquette.className = 'libelle-selection';
        etiquette.textContent = libelle;
        const contenu = document.createElement('strong');
        contenu.className = 'valeur-selection' + (long ? ' valeur-longue' : '');
        contenu.textContent = valeur || 'aucune';
        champ.appendChild(etiquette);
        champ.appendChild(contenu);
        conteneur.appendChild(champ);
      }

      function niveauxDisponibles(element) {
        const niveaux = Array.from(element.querySelectorAll('.selection-niveaux .niveau-selection'));
        if (!niveaux.length) {
          return [element];
        }
        return niveaux.filter((niveau) => {
          if (modePlanification === 'general' && niveau.dataset.selectionType === 'sous-bloc') {
            return false;
          }
          return true;
        });
      }

      function lireSelection(element) {
        const niveaux = niveauxDisponibles(element);
        if (!niveaux.length) {
          return element.dataset;
        }
        const prochain = Number(element.dataset.selectionIndex || '-1') + 1;
        const index = prochain % niveaux.length;
        element.dataset.selectionIndex = String(index);
        return niveaux[index].dataset;
      }

      function reinitialiserCyclesSelection() {
        document.querySelectorAll('.element-selectionnable[data-selection-index]').forEach((element) => {
          delete element.dataset.selectionIndex;
        });
      }

      function nettoyerSelectionVisuelle() {
        document.querySelectorAll(
          '.selection-active, .selection-plage, .selection-plage-debut, .selection-plage-fin, .selection-plage-sous-bloc, .selection-plage-bloc-utilisateur, .selection-jour-courant, .bloc-utilisateur-selectionne'
        ).forEach((element) => {
          element.classList.remove(
            'selection-active',
            'selection-plage',
            'selection-plage-debut',
            'selection-plage-fin',
            'selection-plage-sous-bloc',
            'selection-plage-bloc-utilisateur',
            'selection-jour-courant',
            'bloc-utilisateur-selectionne'
          );
        });
      }

      function appliquerSelectionCalendrier(element, donnees) {
        if (donnees.selectionType !== 'bloc' && donnees.selectionType !== 'sous-bloc') {
          element.classList.add('selection-active', 'selection-jour-courant');
          return;
        }

        const identifiant = donnees.selectionIdentifiant || donnees.selectionParent || '';
        const compteur = donnees.selectionCompteur || '';
        const dateDebut = donnees.selectionDateDebut || '';
        const dateFin = donnees.selectionDateFin || '';

        document.querySelectorAll('.jour-calendrier .niveau-selection').forEach((niveau) => {
          const memeBloc = (niveau.dataset.selectionIdentifiant || niveau.dataset.selectionParent || '') === identifiant;
          const memeType = niveau.dataset.selectionType === donnees.selectionType;
          const memeCompteur = donnees.selectionType !== 'sous-bloc' || niveau.dataset.selectionCompteur === compteur;
          if (!memeBloc || !memeType || !memeCompteur) {
            return;
          }

          const jour = niveau.closest('.jour-calendrier');
          if (!jour) {
            return;
          }

          jour.classList.add('selection-plage');
          if (donnees.selectionType === 'sous-bloc') {
            jour.classList.add('selection-plage-sous-bloc');
          }
          if (donnees.selectionOrigine === 'ajoute_par_utilisateur') {
            jour.classList.add('selection-plage-bloc-utilisateur');
          }
          if (jour.dataset.dateIso === dateDebut) {
            jour.classList.add('selection-plage-debut');
          }
          if (jour.dataset.dateIso === dateFin) {
            jour.classList.add('selection-plage-fin');
          }
        });

        element.classList.add('selection-active');
        if (element.classList.contains('jour-calendrier')) {
          element.classList.add('selection-jour-courant');
        }
      }

      function afficherSelectionPlanification(donnees) {
        const cible = document.getElementById('selection-planification');
        if (!cible) { return; }
        blocLocalSelectionne = donnees.selectionOrigine === 'ajoute_par_utilisateur'
          ? donnees.selectionIdentifiant
          : null;
        cible.textContent = '';
        const fiche = document.createElement('div');
        fiche.className = 'fiche-selection';
        const puce = document.createElement('span');
        puce.className = 'puce-selection';
        puce.textContent = donnees.selectionOrigine === 'ajoute_par_utilisateur'
          ? 'bloc utilisateur prototype'
          : libelleSelection(donnees.selectionType);
        fiche.appendChild(puce);

        if (donnees.selectionType === 'jour') {
          ajouterChampSelection(fiche, 'Date', donnees.selectionDate, false);
          ajouterChampSelection(fiche, 'Consommation', donnees.selectionConsommation, false);
          ajouterChampSelection(fiche, 'Alertes', donnees.selectionAlertes, false);
        } else if (donnees.selectionType === 'bloc') {
          ajouterChampSelection(fiche, 'Période', donnees.selectionPeriode, false);
          ajouterChampSelection(fiche, 'Libellé', donnees.selectionLibelle, false);
          ajouterChampSelection(fiche, 'Quantité', donnees.selectionQuantite, false);
          if (donnees.selectionOrigine === 'ajoute_par_utilisateur') {
            ajouterChampSelection(fiche, 'Compteur indicatif', donnees.selectionCompteurIndicatif, false);
            ajouterChampSelection(fiche, 'Source', 'prototype local localStorage', false);
            ajouterChampSelection(fiche, 'Moteur', 'non recalculé par le moteur', false);
            ajouterChampSelection(fiche, 'Instruction', 'Suppr pour supprimer', false);
          } else {
            ajouterChampSelection(fiche, 'Compteurs', donnees.selectionCompteurs, false);
            ajouterChampSelection(fiche, 'Alertes', donnees.selectionAlertes, false);
          }
          ajouterChampSelection(fiche, 'Identifiant', donnees.selectionIdentifiant, true);
        } else if (donnees.selectionType === 'sous-bloc') {
          ajouterChampSelection(fiche, 'Période', donnees.selectionPeriode, false);
          ajouterChampSelection(fiche, 'Compteur', donnees.selectionCompteur, false);
          ajouterChampSelection(fiche, 'Quantité', donnees.selectionQuantite, false);
          ajouterChampSelection(fiche, 'Bloc parent', donnees.selectionParent, true);
        } else if (donnees.selectionType === 'reste') {
          ajouterChampSelection(fiche, 'Date', donnees.selectionDate, false);
          ajouterChampSelection(fiche, 'Portion', donnees.selectionPortion, false);
          ajouterChampSelection(fiche, 'Niveau', donnees.selectionNiveau, false);
        }

        cible.appendChild(fiche);
      }

      function afficherCurseurPlanification(donnees) {
        const cible = document.getElementById('curseur-planification');
        if (!cible) { return; }
        cible.textContent = '';
        const fiche = document.createElement('div');
        fiche.className = 'fiche-selection fiche-curseur';
        ajouterChampSelection(fiche, 'Date', donnees.selectionDate, false);
        ajouterChampSelection(fiche, 'Portion', donnees.selectionPortion, false);
        ajouterChampSelection(fiche, 'Niveau', donnees.selectionNiveau, false);
        cible.appendChild(fiche);
      }

      function afficherCurseurPrototype(dateDebut, dateFin, impossible) {
        const cible = document.getElementById('curseur-planification');
        if (!cible) { return; }
        const quantite = datesProjeteesEntre(dateDebut, dateFin).length;
        cible.textContent = '';
        const fiche = document.createElement('div');
        fiche.className = 'fiche-selection fiche-curseur fiche-prototype';
        const puce = document.createElement('span');
        puce.className = 'puce-selection';
        puce.textContent = impossible ? 'pose impossible' : 'prévisualisation locale';
        fiche.appendChild(puce);
        ajouterChampSelection(fiche, 'Période', periodeLisible(dateDebut, dateFin), false);
        ajouterChampSelection(fiche, 'Quantité', quantite + ' j projeté(s)', false);
        ajouterChampSelection(fiche, 'Compteur indicatif', 'non_recalcule', false);
        ajouterChampSelection(fiche, 'Moteur', 'non recalculé par le moteur', false);
        if (impossible) {
          ajouterChampSelection(fiche, 'Raison', 'plage déjà occupée', false);
        }
        cible.appendChild(fiche);
      }

      function viderCurseurPlanification() {
        const cible = document.getElementById('curseur-planification');
        if (!cible) { return; }
        cible.textContent = '';
        const vide = document.createElement('p');
        vide.className = 'info-compacte';
        vide.textContent = 'aucun';
        cible.appendChild(vide);
      }

      function deselectionnerPlanification() {
        nettoyerSelectionVisuelle();
        reinitialiserCyclesSelection();
        blocLocalSelectionne = null;
        const cible = document.getElementById('selection-planification');
        if (cible) {
          cible.textContent = '';
          const vide = document.createElement('p');
          vide.className = 'info-compacte';
          vide.textContent = 'aucune';
          cible.appendChild(vide);
        }
      }

      function normaliserPlageDates(dateA, dateB) {
        return [dateA, dateB].sort();
      }

      function joursCalendrier() {
        return Array.from(document.querySelectorAll('.jour-calendrier[data-date-iso]'));
      }

      function datesProjeteesEntre(dateA, dateB) {
        const bornes = normaliserPlageDates(dateA, dateB);
        return joursCalendrier()
          .map((jour) => jour.dataset.dateIso)
          .filter((dateIso) => dateIso >= bornes[0] && dateIso <= bornes[1]);
      }

      function jourOccupePourPose(jour) {
        if (!jour) { return false; }
        if (jour.classList.contains('jour-avec-bloc-utilisateur')) { return true; }
        return Array.from(jour.querySelectorAll('.niveau-selection')).some((niveau) => {
          return niveau.dataset.selectionType === 'bloc';
        });
      }

      function plageLibrePourPose(dateA, dateB) {
        return datesProjeteesEntre(dateA, dateB).every((dateIso) => {
          const jour = document.querySelector('.jour-calendrier[data-date-iso="' + dateIso + '"]');
          return !jourOccupePourPose(jour);
        });
      }

      function periodeLisible(dateA, dateB) {
        const dates = datesProjeteesEntre(dateA, dateB);
        if (!dates.length) {
          return dateA;
        }
        if (dates[0] === dates[dates.length - 1]) {
          return dates[0];
        }
        return dates[0] + ' → ' + dates[dates.length - 1];
      }

      function nettoyerFantomeLocal() {
        document.querySelectorAll('.bloc-fantome-local').forEach((jour) => {
          jour.classList.remove('bloc-fantome-local', 'bloc-fantome-impossible', 'bloc-fantome-debut', 'bloc-fantome-fin');
        });
        document.querySelectorAll('.bloc-fantome-frise').forEach((element) => {
          element.remove();
        });
      }

      function afficherFantomeFrise(dateA, dateB, impossible) {
        document.querySelectorAll('.courbe-reste-agrege').forEach((svg) => {
          const groupe = svg.querySelector('.ligne-blocs-locaux');
          if (!groupe) { return; }
          const x1 = xFrisePourDate(svg, dateA);
          const x2 = xFrisePourDate(svg, dateB);
          if (x1 === null || x2 === null) { return; }
          const rect = document.createElementNS(svg.namespaceURI, 'rect');
          rect.setAttribute('class', impossible ? 'bloc-fantome-frise bloc-fantome-frise-impossible' : 'bloc-fantome-frise');
          rect.setAttribute('x', String(Math.min(x1, x2)));
          rect.setAttribute('y', '78');
          rect.setAttribute('width', String(Math.max(8, Math.abs(x2 - x1) + 8)));
          rect.setAttribute('height', '10');
          rect.setAttribute('rx', '4');
          groupe.appendChild(rect);
        });
      }

      function afficherEtatTransitoireInterface() {
        nettoyerFantomeLocal();
        const plage = etatTransitoireInterface.plage_en_cours;
        if (!plage || !plage.date_debut || !plage.date_fin) { return; }
        const dateA = plage.date_debut;
        const dateB = plage.date_fin;
        const dates = datesProjeteesEntre(dateA, dateB);
        const resultatPrevisualisation = etatTransitoireInterface.dernier_resultat_previsualisation || { diagnostics: [] };
        const impossible = (resultatPrevisualisation.diagnostics || []).some((diagnostic) => diagnostic.niveau === 'bloquant' || diagnostic.niveau === 'erreur');
        dates.forEach((dateIso, index) => {
          const jour = document.querySelector('.jour-calendrier[data-date-iso="' + dateIso + '"]');
          if (!jour) { return; }
          jour.classList.add('bloc-fantome-local');
          if (impossible) { jour.classList.add('bloc-fantome-impossible'); }
          if (index === 0) { jour.classList.add('bloc-fantome-debut'); }
          if (index === dates.length - 1) { jour.classList.add('bloc-fantome-fin'); }
        });
        afficherFantomeFrise(dateA, dateB, impossible);
        afficherCurseurPrototype(dateA, dateB, impossible);
        afficherDiagnosticsGui(resultatPrevisualisation.diagnostics || []);
      }

      function afficherFantomeLocal(dateA, dateB) {
        const dates = datesProjeteesEntre(dateA, dateB);
        const commande = {
          type: 'ajouter_absence',
          identifiant_commande: 'commande_previsualiser_' + Date.now(),
          cible: { type: 'scenario_local', identifiant: 'prototype_interface' },
          parametres: {
            date_debut: dates[0] || dateA,
            date_fin: dates[dates.length - 1] || dateB,
            compteur_indicatif: 'non_recalcule'
          },
          mode: 'previsualiser'
        };
        const resultat = traiterCommandeMoteurGui(etatCentralGui, commande);
        etatTransitoireInterface.plage_en_cours = { date_debut: dateA, date_fin: dateB };
        etatTransitoireInterface.fantome_calendrier = { date_debut: dateA, date_fin: dateB };
        etatTransitoireInterface.fantome_frise = { date_debut: dateA, date_fin: dateB };
        etatTransitoireInterface.dernier_resultat_previsualisation = resultat;
        etatTransitoireInterface.message_temporaire = resultat.diagnostics.length ? 'pose impossible' : 'prévisualisation locale';
        afficherEtatTransitoireInterface();
      }

      function lireBlocsLocauxPrototype() {
        try {
          const texte = localStorage.getItem(CLE_STOCKAGE_PROTO);
          const donnees = texte ? JSON.parse(texte) : [];
          return Array.isArray(donnees)
            ? donnees.filter((bloc) => bloc && bloc.type === 'absence_locale_prototype').map(normaliserBlocLocalPrototype)
            : [];
        } catch (_erreur) {
          return [];
        }
      }

      function sauvegarderBlocsLocauxPrototype() {
        try {
          localStorage.setItem(CLE_STOCKAGE_PROTO, JSON.stringify(blocsLocauxPrototype));
        } catch (_erreur) {
          afficherCurseurPrototype(dateSurvolPose || dateDebutPose || '', dateSurvolPose || dateDebutPose || '', true);
        }
      }

      function normaliserBlocLocalPrototype(bloc) {
        return {
          id: bloc.id || 'bloc_utilisateur_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8),
          type: 'absence_locale_prototype',
          date_debut: bloc.date_debut,
          date_fin: bloc.date_fin,
          origine: bloc.origine || 'ajoute_par_utilisateur',
          statut: bloc.statut || 'scenario_local_prototype',
          compteur_indicatif: bloc.compteur_indicatif || 'non_recalcule',
          quantite_jours: Number(bloc.quantite_jours || datesProjeteesEntre(bloc.date_debut, bloc.date_fin).length || 0),
          cree_le: bloc.cree_le || new Date().toISOString()
        };
      }

      function copierBlocsLocauxPrototype(blocs) {
        return Array.isArray(blocs) ? blocs.map(normaliserBlocLocalPrototype) : [];
      }

      function blocPrototypeVersBlocAffichable(bloc) {
        const blocNormalise = normaliserBlocLocalPrototype(bloc);
        return {
          type: 'bloc_absence_affichable',
          identifiant: blocNormalise.id,
          date_debut: blocNormalise.date_debut,
          date_fin: blocNormalise.date_fin,
          origine: 'prototype_interface',
          statut: 'simule',
          compteur: blocNormalise.compteur_indicatif || 'non_recalcule',
          quantite_jours: blocNormalise.quantite_jours,
          diagnostics: []
        };
      }

      function construireEtatCentralGui(blocsLocaux, diagnostics) {
        const blocsScenario = copierBlocsLocauxPrototype(blocsLocaux);
        return {
          version_contrat: '0.1',
          sources: {
            scenario_local: {
              blocs_absence: blocsScenario
            }
          },
          blocs_affichables: blocsScenario.map(blocPrototypeVersBlocAffichable),
          diagnostics: Array.isArray(diagnostics) ? diagnostics : []
        };
      }

      function blocsScenarioDepuisEtat(etat) {
        const scenario = etat && etat.sources && etat.sources.scenario_local;
        return copierBlocsLocauxPrototype(scenario && Array.isArray(scenario.blocs_absence) ? scenario.blocs_absence : []);
      }

      function synchroniserBlocsLocauxDepuisEtatCentral(etat) {
        blocsLocauxPrototype = blocsScenarioDepuisEtat(etat);
      }

      function diagnosticMoteurGui(niveau, code, message, cibles, details) {
        return {
          niveau: niveau,
          code: code,
          message: message,
          cibles: Array.isArray(cibles) ? cibles : [],
          details: details || {}
        };
      }

      function resultatCommandeMoteurGui(commande, statut, etat, diagnostics, selectionSuggeree) {
        return {
          identifiant_commande: commande.identifiant_commande || 'commande_' + Date.now(),
          statut: statut,
          etat_central: etat,
          diagnostics: Array.isArray(diagnostics) ? diagnostics : [],
          selection_suggeree: selectionSuggeree || null
        };
      }

      function blocLocalOccupeDate(bloc, dateIso) {
        return datesBlocLocal(bloc).includes(dateIso);
      }

      function datesOccupeesPourCommande(etat, dates) {
        const blocs = blocsScenarioDepuisEtat(etat);
        return dates.filter((dateIso) => {
          const jour = document.querySelector('.jour-calendrier[data-date-iso="' + dateIso + '"]');
          const occupeProjection = Boolean(jour && Array.from(jour.querySelectorAll('.niveau-selection')).some((niveau) => {
            return niveau.dataset.selectionType === 'bloc' && niveau.dataset.selectionOrigine !== 'ajoute_par_utilisateur';
          }));
          const occupeLocal = blocs.some((bloc) => blocLocalOccupeDate(bloc, dateIso));
          return occupeProjection || occupeLocal;
        });
      }

      function traiterCommandeMoteurGui(etat, commande) {
        const etatCourant = etat || construireEtatCentralGui([], []);
        const typeCommande = commande && commande.type;
        const modeCommande = commande && commande.mode;
        if (typeCommande === 'ajouter_absence') {
          const parametres = commande.parametres || {};
          const dates = datesProjeteesEntre(parametres.date_debut, parametres.date_fin);
          if (!dates.length) {
            return resultatCommandeMoteurGui(
              commande,
              'refusee',
              etatCourant,
              [
                diagnosticMoteurGui(
                  'bloquant',
                  'date_hors_projection',
                  'Pose impossible : la plage ne correspond à aucune date projetée.',
                  [{ type: 'commande', identifiant: commande.identifiant_commande || '' }],
                  {}
                )
              ],
              null
            );
          }
          const datesOccupees = datesOccupeesPourCommande(etatCourant, dates);
          if (datesOccupees.length) {
            return resultatCommandeMoteurGui(
              commande,
              'refusee',
              etatCourant,
              [
                diagnosticMoteurGui(
                  'bloquant',
                  'plage_deja_occupee',
                  'Pose impossible : la plage contient déjà une absence.',
                  datesOccupees.map((dateIso) => ({ type: 'date', date: dateIso })),
                  {}
                )
              ],
              null
            );
          }
          if (modeCommande === 'previsualiser') {
            return resultatCommandeMoteurGui(commande, 'inchangee', etatCourant, [], null);
          }
          if (modeCommande === 'appliquer') {
            const blocs = blocsScenarioDepuisEtat(etatCourant);
            const bloc = normaliserBlocLocalPrototype({
              id: parametres.id || 'bloc_utilisateur_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8),
              type: 'absence_locale_prototype',
              date_debut: dates[0],
              date_fin: dates[dates.length - 1],
              origine: 'ajoute_par_utilisateur',
              statut: 'scenario_local_prototype',
              compteur_indicatif: parametres.compteur_indicatif || 'non_recalcule',
              quantite_jours: dates.length,
              cree_le: new Date().toISOString()
            });
            const nouvelEtat = construireEtatCentralGui(blocs.concat([bloc]), []);
            return resultatCommandeMoteurGui(
              commande,
              'acceptee',
              nouvelEtat,
              [],
              { type: 'bloc_absence', identifiant: bloc.id }
            );
          }
        }
        if (typeCommande === 'supprimer_absence' && modeCommande === 'appliquer') {
          const cible = commande.cible || {};
          const identifiant = cible.identifiant;
          const blocs = blocsScenarioDepuisEtat(etatCourant);
          const bloc = blocs.find((blocLocal) => blocLocal.id === identifiant);
          if (!bloc) {
            return resultatCommandeMoteurGui(
              commande,
              'refusee',
              etatCourant,
              [
                diagnosticMoteurGui(
                  'bloquant',
                  'bloc_introuvable',
                  'Suppression impossible : le bloc prototype est introuvable.',
                  [{ type: 'bloc_absence', identifiant: identifiant || '' }],
                  {}
                )
              ],
              null
            );
          }
          if (bloc.origine !== 'ajoute_par_utilisateur' || bloc.statut !== 'scenario_local_prototype') {
            return resultatCommandeMoteurGui(
              commande,
              'refusee',
              etatCourant,
              [
                diagnosticMoteurGui(
                  'bloquant',
                  'bloc_non_modifiable',
                  'Suppression impossible : seul un bloc utilisateur prototype peut être supprimé.',
                  [{ type: 'bloc_absence', identifiant: identifiant || '' }],
                  {}
                )
              ],
              null
            );
          }
          const nouvelEtat = construireEtatCentralGui(
            blocs.filter((blocLocal) => blocLocal.id !== identifiant),
            []
          );
          return resultatCommandeMoteurGui(commande, 'acceptee', nouvelEtat, [], null);
        }
        return resultatCommandeMoteurGui(
          commande || {},
          'erreur',
          etatCourant,
          [
            diagnosticMoteurGui(
              'erreur',
              'commande_non_prise_en_charge',
              'Commande non prise en charge par le moteur GUI prototype.',
              [{ type: 'commande', identifiant: (commande && commande.identifiant_commande) || '' }],
              {}
            )
          ],
          null
        );
      }

      function afficherDiagnosticsGui(diagnostics) {
        const cible = document.getElementById('diagnostics-planification');
        if (!cible) { return; }
        cible.textContent = '';
        const diagnosticsAffiches = Array.isArray(diagnostics) ? diagnostics : [];
        if (!diagnosticsAffiches.length) {
          const vide = document.createElement('p');
          vide.className = 'info-compacte';
          vide.textContent = 'aucun';
          cible.appendChild(vide);
          return;
        }
        const liste = document.createElement('ul');
        liste.className = 'liste-diagnostics-planification';
        diagnosticsAffiches.forEach((diagnostic) => {
          const element = document.createElement('li');
          element.className = 'diagnostic-planification diagnostic-' + (diagnostic.niveau || 'information');
          element.textContent = (diagnostic.niveau || 'information') + ' · ' + (diagnostic.code || 'diagnostic') + ' · ' + (diagnostic.message || '');
          liste.appendChild(element);
        });
        cible.appendChild(liste);
      }

      function appliquerResultatCommandeMoteurGui(resultat, options) {
        afficherDiagnosticsGui(resultat.diagnostics || []);
        if (resultat.statut !== 'acceptee') {
          return;
        }
        etatCentralGui = resultat.etat_central || etatCentralGui;
        synchroniserBlocsLocauxDepuisEtatCentral(etatCentralGui);
        sauvegarderBlocsLocauxPrototype();
        afficherEtatCentralGui(etatCentralGui);
        if (options && options.selectionner && resultat.selection_suggeree) {
          afficherSelectionBlocLocal(blocLocalParId(resultat.selection_suggeree.identifiant));
        } else if (options && options.deselectionner) {
          deselectionnerPlanification();
        }
      }

      function creerBlocLocalPrototype(dateA, dateB) {
        const dates = datesProjeteesEntre(dateA, dateB);
        if (!dates.length) { return; }
        const commande = {
          type: 'ajouter_absence',
          identifiant_commande: 'commande_ajouter_' + Date.now(),
          cible: { type: 'scenario_local', identifiant: 'prototype_interface' },
          parametres: {
            date_debut: dates[0],
            date_fin: dates[dates.length - 1],
            compteur_indicatif: 'non_recalcule'
          },
          mode: 'appliquer'
        };
        const resultat = traiterCommandeMoteurGui(etatCentralGui, commande);
        nettoyerFantomeLocal();
        appliquerResultatCommandeMoteurGui(resultat, { selectionner: true });
      }

      function datesBlocLocal(bloc) {
        return datesProjeteesEntre(bloc.date_debut, bloc.date_fin);
      }

      function libelleBlocLocal(bloc) {
        return bloc.date_debut === bloc.date_fin ? bloc.date_debut : bloc.date_debut + ' → ' + bloc.date_fin;
      }

      function nettoyerRenduBlocsLocaux() {
        document.querySelectorAll('.bloc-utilisateur-frise').forEach((element) => {
          element.remove();
        });
        document.querySelectorAll('.bloc-utilisateur-prototype').forEach((element) => {
          element.remove();
        });
        document.querySelectorAll('.jour-avec-bloc-utilisateur').forEach((jour) => {
          jour.classList.remove(
            'jour-avec-bloc-utilisateur',
            'origine-utilisateur',
            'compteur-manuel-gcp',
            'compteur-manuel-jrtt',
            'compteur-manuel-canc',
            'compteur-manuel-defaut'
          );
          const typeCompteur = jour.querySelector('.type-compteur-jour');
          if (typeCompteur && typeCompteur.dataset.libelleProjection !== undefined) {
            typeCompteur.textContent = typeCompteur.dataset.libelleProjection;
          }
        });
      }

      function classeCompteurManuel(compteur) {
        const normalise = String(compteur || '').trim().toUpperCase();
        if (normalise === 'GCP') { return 'compteur-manuel-gcp'; }
        if (normalise === 'JRTT') { return 'compteur-manuel-jrtt'; }
        if (normalise === 'CANC') { return 'compteur-manuel-canc'; }
        return 'compteur-manuel-defaut';
      }

      function libelleCompteurManuel(compteur) {
        const normalise = String(compteur || '').trim().toUpperCase();
        if (normalise === 'NON_RECALCULE') { return 'non rec.'; }
        if (normalise === 'GCP' || normalise === 'JRTT' || normalise === 'CANC') { return normalise; }
        return normalise ? normalise.toLowerCase() : 'non rec.';
      }

      function niveauSelectionBlocUtilisateur(bloc) {
        const niveau = document.createElement('span');
        niveau.className = 'niveau-selection selection-type-bloc bloc-utilisateur-prototype';
        niveau.dataset.selectionNiveau = 'local';
        niveau.dataset.selectionType = 'bloc';
        niveau.dataset.selectionOrigine = 'ajoute_par_utilisateur';
        niveau.dataset.selectionDateDebut = bloc.date_debut;
        niveau.dataset.selectionDateFin = bloc.date_fin;
        niveau.dataset.selectionPeriode = periodeLisible(bloc.date_debut, bloc.date_fin);
        niveau.dataset.selectionIdentifiant = bloc.id;
        niveau.dataset.selectionLibelle = 'absence locale prototype';
        niveau.dataset.selectionQuantite = bloc.quantite_jours + ' j';
        niveau.dataset.selectionCompteurIndicatif = bloc.compteur_indicatif || 'non_recalcule';
        niveau.dataset.selectionAlertes = 'aucune';
        return niveau;
      }

      function blocAffichableVersBlocPrototype(blocAffichable) {
        return normaliserBlocLocalPrototype({
          id: blocAffichable.identifiant,
          type: 'absence_locale_prototype',
          date_debut: blocAffichable.date_debut,
          date_fin: blocAffichable.date_fin,
          origine: 'ajoute_par_utilisateur',
          statut: 'scenario_local_prototype',
          compteur_indicatif: blocAffichable.compteur || 'non_recalcule',
          quantite_jours: blocAffichable.quantite_jours
        });
      }

      function rendreBlocsAffichablesCalendrier(blocsAffichables) {
        (blocsAffichables || []).forEach((blocAffichable) => {
          const bloc = blocAffichableVersBlocPrototype(blocAffichable);
          datesBlocLocal(bloc).forEach((dateIso) => {
            const jour = document.querySelector('.jour-calendrier[data-date-iso="' + dateIso + '"]');
            if (!jour) { return; }
            jour.classList.add('jour-avec-bloc-utilisateur', 'origine-utilisateur', classeCompteurManuel(bloc.compteur_indicatif));
            const typeCompteur = jour.querySelector('.type-compteur-jour');
            if (typeCompteur) {
              if (typeCompteur.dataset.libelleProjection === undefined) {
                typeCompteur.dataset.libelleProjection = typeCompteur.textContent || '';
              }
              typeCompteur.textContent = libelleCompteurManuel(bloc.compteur_indicatif);
            }
            const conteneur = jour.querySelector('.selection-niveaux');
            if (!conteneur) { return; }
            conteneur.insertBefore(niveauSelectionBlocUtilisateur(bloc), conteneur.firstChild);
          });
        });
      }

      function rendreBlocsLocauxCalendrier() {
        rendreBlocsAffichablesCalendrier(etatCentralGui && Array.isArray(etatCentralGui.blocs_affichables) ? etatCentralGui.blocs_affichables : []);
      }

      function xFrisePourDate(svg, dateIso) {
        const debut = new Date(svg.dataset.friseDebut + 'T00:00:00');
        const fin = new Date(svg.dataset.friseFin + 'T00:00:00');
        const courant = new Date(dateIso + 'T00:00:00');
        const gauche = Number(svg.dataset.friseGauche || '58');
        const droite = Number(svg.dataset.friseDroite || '1092');
        const duree = Math.max(1, (fin - debut) / 86400000);
        return gauche + (((courant - debut) / 86400000) / duree) * (droite - gauche);
      }

      function rendreBlocsAffichablesFrise(blocsAffichables) {
        document.querySelectorAll('.courbe-reste-agrege').forEach((svg) => {
          const groupe = svg.querySelector('.ligne-blocs-locaux');
          if (!groupe) { return; }
          (blocsAffichables || []).forEach((blocAffichable) => {
            const bloc = blocAffichableVersBlocPrototype(blocAffichable);
            const x1 = xFrisePourDate(svg, bloc.date_debut);
            const x2 = xFrisePourDate(svg, bloc.date_fin);
            const rect = document.createElementNS(svg.namespaceURI, 'rect');
            rect.setAttribute('class', 'bloc-utilisateur-frise element-selectionnable');
            rect.setAttribute('x', String(x1));
            rect.setAttribute('y', '60');
            rect.setAttribute('width', String(Math.max(10, x2 - x1 + 8)));
            rect.setAttribute('height', '14');
            rect.setAttribute('rx', '5');
            rect.setAttribute('role', 'button');
            rect.setAttribute('tabindex', '0');
            rect.dataset.selectionType = 'bloc';
            rect.dataset.selectionOrigine = 'ajoute_par_utilisateur';
            rect.dataset.selectionDateDebut = bloc.date_debut;
            rect.dataset.selectionDateFin = bloc.date_fin;
            rect.dataset.selectionPeriode = libelleBlocLocal(bloc);
            rect.dataset.selectionIdentifiant = bloc.id;
            rect.dataset.selectionLibelle = 'absence locale prototype';
            rect.dataset.selectionQuantite = bloc.quantite_jours + ' j';
            rect.dataset.selectionCompteurIndicatif = bloc.compteur_indicatif || 'non_recalcule';
            rect.dataset.selectionAlertes = 'aucune';
            const titre = document.createElementNS(svg.namespaceURI, 'title');
            titre.textContent = 'Bloc local prototype ' + libelleBlocLocal(bloc);
            rect.appendChild(titre);
            groupe.appendChild(rect);
            connecterElementSelectionnable(rect);
          });
        });
      }

      function rendreBlocsLocauxFrise() {
        rendreBlocsAffichablesFrise(etatCentralGui && Array.isArray(etatCentralGui.blocs_affichables) ? etatCentralGui.blocs_affichables : []);
      }

      function rendreBlocsAffichablesPrototype(blocsAffichables) {
        nettoyerRenduBlocsLocaux();
        rendreBlocsAffichablesCalendrier(blocsAffichables || []);
        rendreBlocsAffichablesFrise(blocsAffichables || []);
      }

      function afficherEtatCentralGui(etat) {
        etatCentralGui = etat || construireEtatCentralGui([], []);
        synchroniserBlocsLocauxDepuisEtatCentral(etatCentralGui);
        rendreBlocsAffichablesPrototype(etatCentralGui.blocs_affichables || []);
        afficherDiagnosticsGui(etatCentralGui.diagnostics || []);
      }

      function rendreBlocsLocauxPrototype() {
        afficherEtatCentralGui(etatCentralGui || construireEtatCentralGui(blocsLocauxPrototype, []));
      }

      function blocLocalParId(id) {
        return blocsLocauxPrototype.find((bloc) => bloc.id === id);
      }

      function afficherSelectionBlocLocal(bloc) {
        if (!bloc) { return; }
        blocLocalSelectionne = bloc.id;
        nettoyerSelectionVisuelle();
        let donnees = null;
        document.querySelectorAll('.niveau-selection[data-selection-identifiant="' + bloc.id + '"]').forEach((niveau) => {
          donnees = niveau.dataset;
          const jour = niveau.closest('.jour-calendrier');
          if (jour) {
            jour.classList.add('selection-plage', 'selection-plage-bloc-utilisateur');
            if (jour.dataset.dateIso === bloc.date_debut) {
              jour.classList.add('selection-plage-debut');
            }
            if (jour.dataset.dateIso === bloc.date_fin) {
              jour.classList.add('selection-plage-fin');
            }
          }
        });
        document.querySelectorAll('.bloc-utilisateur-frise[data-selection-identifiant="' + bloc.id + '"]').forEach((element) => {
          element.classList.add('selection-active', 'bloc-utilisateur-selectionne');
        });
        if (donnees) {
          afficherSelectionPlanification(donnees);
          return;
        }
        const cible = document.getElementById('selection-planification');
        if (!cible) { return; }
        cible.textContent = '';
        const fiche = document.createElement('div');
        fiche.className = 'fiche-selection fiche-prototype';
        const puce = document.createElement('span');
        puce.className = 'puce-selection';
        puce.textContent = 'bloc local prototype';
        fiche.appendChild(puce);
        ajouterChampSelection(fiche, 'Période', libelleBlocLocal(bloc), false);
        ajouterChampSelection(fiche, 'Quantité', bloc.quantite_jours + ' j', false);
        ajouterChampSelection(fiche, 'Compteur indicatif', bloc.compteur_indicatif, false);
        ajouterChampSelection(fiche, 'Source', 'prototype local localStorage', false);
        ajouterChampSelection(fiche, 'Moteur', 'non recalculé par le moteur', false);
        ajouterChampSelection(fiche, 'Instruction', 'Suppr pour supprimer', false);
        ajouterChampSelection(fiche, 'Identifiant', bloc.id, true);
        cible.appendChild(fiche);
      }

      function supprimerBlocLocalSelectionne() {
        if (!blocLocalSelectionne) { return; }
        const identifiantSelectionne = blocLocalSelectionne;
        const commande = {
          type: 'supprimer_absence',
          identifiant_commande: 'commande_supprimer_' + Date.now(),
          cible: { type: 'bloc_absence', identifiant: identifiantSelectionne },
          parametres: {},
          mode: 'appliquer'
        };
        const resultat = traiterCommandeMoteurGui(etatCentralGui, commande);
        if (resultat.statut === 'acceptee') {
          blocLocalSelectionne = null;
        }
        appliquerResultatCommandeMoteurGui(resultat, { deselectionner: true });
      }

      function activerSelectionPlanification(element) {
        if (!element.classList.contains('selection-active') && !element.classList.contains('selection-jour-courant')) {
          reinitialiserCyclesSelection();
        }
        const donnees = lireSelection(element);
        nettoyerSelectionVisuelle();
        if (element.classList.contains('jour-calendrier')) {
          appliquerSelectionCalendrier(element, donnees);
        } else if (donnees.selectionOrigine === 'ajoute_par_utilisateur' && donnees.selectionType === 'bloc') {
          appliquerSelectionCalendrier(element, donnees);
        } else {
          element.classList.add('selection-active');
        }
        afficherSelectionPlanification(donnees);
      }

      function coordonneeSvg(svg, event) {
        const rectangle = svg.getBoundingClientRect();
        const vue = svg.viewBox.baseVal;
        return {
          x: ((event.clientX - rectangle.left) / rectangle.width) * vue.width + vue.x,
          y: ((event.clientY - rectangle.top) / rectangle.height) * vue.height + vue.y
        };
      }

      function initialiserCurseursFrise() {
        document.querySelectorAll('.courbe-reste-agrege').forEach((svg) => {
          const ligne = svg.querySelector('.ligne-curseur-frise');
          const points = Array.from(svg.querySelectorAll('.point-curseur-frise')).map((point) => ({
            x: Number(point.dataset.x || '0'),
            donnees: point.dataset
          }));
          if (!ligne || !points.length) {
            return;
          }
          svg.addEventListener('mousemove', function (event) {
            const position = coordonneeSvg(svg, event);
            let meilleur = points[0];
            let distance = Math.abs(position.x - meilleur.x);
            points.forEach((point) => {
              const candidate = Math.abs(position.x - point.x);
              if (candidate < distance) {
                meilleur = point;
                distance = candidate;
              }
            });
            ligne.setAttribute('x1', String(meilleur.x));
            ligne.setAttribute('x2', String(meilleur.x));
            ligne.style.display = 'block';
            afficherCurseurPlanification(meilleur.donnees);
          });
          svg.addEventListener('mouseleave', function () {
            ligne.style.display = 'none';
            viderCurseurPlanification();
          });
        });
      }

      function connecterElementSelectionnable(element) {
        if (!element || element.dataset.selectionConnectee === 'true') { return; }
        element.dataset.selectionConnectee = 'true';
        element.addEventListener('click', function (event) {
          event.preventDefault();
          event.stopPropagation();
          if (outilPlanification === 'poser') {
            return;
          }
          activerSelectionPlanification(element);
        });
        element.addEventListener('dblclick', function (event) {
          event.preventDefault();
          event.stopPropagation();
        });
        element.addEventListener('keydown', function (event) {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            activerSelectionPlanification(element);
          }
        });
      }

      function annulerPoseLocalePrototype() {
        dateDebutPose = null;
        dateSurvolPose = null;
        poseEnCours = false;
        etatTransitoireInterface.pose_en_cours = false;
        etatTransitoireInterface.date_debut_pose = null;
        etatTransitoireInterface.date_survol_pose = null;
        etatTransitoireInterface.plage_en_cours = null;
        etatTransitoireInterface.fantome_calendrier = null;
        etatTransitoireInterface.fantome_frise = null;
        etatTransitoireInterface.dernier_resultat_previsualisation = null;
        etatTransitoireInterface.message_temporaire = null;
        nettoyerFantomeLocal();
      }

      function finaliserPoseLocalePrototype(dateFin) {
        if (!poseEnCours || !dateDebutPose) { return; }
        const fin = dateFin || dateSurvolPose || dateDebutPose;
        creerBlocLocalPrototype(dateDebutPose, fin);
        dateDebutPose = null;
        dateSurvolPose = null;
        poseEnCours = false;
        etatTransitoireInterface.pose_en_cours = false;
        etatTransitoireInterface.date_debut_pose = null;
        etatTransitoireInterface.date_survol_pose = null;
        etatTransitoireInterface.plage_en_cours = null;
        etatTransitoireInterface.fantome_calendrier = null;
        etatTransitoireInterface.fantome_frise = null;
      }

      boutons.forEach((bouton) => {
        bouton.addEventListener('click', function () {
          activerVue(bouton.dataset.cible);
        });
      });

      boutonsSousVues.forEach((bouton) => {
        bouton.addEventListener('click', function () {
          activerSousVue(bouton.dataset.sousVueCible);
        });
      });

      boutonsMode.forEach((bouton) => {
        bouton.addEventListener('click', function () {
          activerModePlanification(bouton.dataset.modePlanification);
        });
      });

      boutonsOutils.forEach((bouton) => {
        bouton.addEventListener('click', function () {
          activerOutilPlanification(bouton.dataset.outilPlanification);
        });
      });

      document.querySelectorAll('.element-selectionnable').forEach(connecterElementSelectionnable);

      joursCalendrier().forEach((jour) => {
        jour.addEventListener('mouseenter', function () {
          jour.classList.add('jour-survol-simple');
          if (outilPlanification !== 'poser') { return; }
          const dateIso = jour.dataset.dateIso;
          if (!dateIso) { return; }
          dateSurvolPose = dateIso;
          etatTransitoireInterface.date_survol_pose = dateSurvolPose;
          afficherFantomeLocal(dateDebutPose || dateIso, dateIso);
        });
        jour.addEventListener('mouseleave', function () {
          jour.classList.remove('jour-survol-simple');
        });
        jour.addEventListener('pointerdown', function (event) {
          if (outilPlanification !== 'poser') { return; }
          event.preventDefault();
          event.stopPropagation();
          if (jourOccupePourPose(jour)) {
            activerSelectionPlanification(jour);
            return;
          }
          dateDebutPose = jour.dataset.dateIso;
          dateSurvolPose = dateDebutPose;
          poseEnCours = true;
          etatTransitoireInterface.pose_en_cours = true;
          etatTransitoireInterface.date_debut_pose = dateDebutPose;
          etatTransitoireInterface.date_survol_pose = dateSurvolPose;
          if (jour.setPointerCapture) {
            try { jour.setPointerCapture(event.pointerId); } catch (_erreur) {}
          }
          if (dateDebutPose) {
            afficherFantomeLocal(dateDebutPose, dateDebutPose);
          }
        });
        jour.addEventListener('pointerenter', function () {
          if (outilPlanification !== 'poser' || !poseEnCours) { return; }
          const dateIso = jour.dataset.dateIso;
          if (!dateIso) { return; }
          dateSurvolPose = dateIso;
          etatTransitoireInterface.date_survol_pose = dateSurvolPose;
          afficherFantomeLocal(dateDebutPose || dateIso, dateIso);
        });
      });

      document.querySelectorAll('.zone-centrale-planification').forEach((zone) => {
        zone.addEventListener('click', function (event) {
          if (!event.target.closest('.element-selectionnable, .bouton-sous-vue, [data-mode-planification], [data-outil-planification]')) {
            deselectionnerPlanification();
          }
        });
        zone.addEventListener('dblclick', function (event) {
          event.preventDefault();
        });
      });

      document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
          annulerPoseLocalePrototype();
          deselectionnerPlanification();
        } else if (event.key === 'Delete' || event.key === 'Suppr') {
          supprimerBlocLocalSelectionne();
        }
      });

      document.addEventListener('pointerup', function (event) {
        if (outilPlanification !== 'poser' || !poseEnCours) { return; }
        event.preventDefault();
        const element = document.elementFromPoint(event.clientX, event.clientY);
        const jour = element && element.closest ? element.closest('.jour-calendrier[data-date-iso]') : null;
        finaliserPoseLocalePrototype(jour ? jour.dataset.dateIso : dateSurvolPose);
      });

      document.addEventListener('pointermove', function (event) {
        if (outilPlanification !== 'poser' || !poseEnCours || !dateDebutPose) { return; }
        const element = document.elementFromPoint(event.clientX, event.clientY);
        const jour = element && element.closest ? element.closest('.jour-calendrier[data-date-iso]') : null;
        if (!jour || !jour.dataset.dateIso || jour.dataset.dateIso === dateSurvolPose) { return; }
        dateSurvolPose = jour.dataset.dateIso;
        etatTransitoireInterface.date_survol_pose = dateSurvolPose;
        afficherFantomeLocal(dateDebutPose, dateSurvolPose);
      });

      window.addEventListener('blur', function () {
        if (poseEnCours) {
          annulerPoseLocalePrototype();
        }
      });

      activerVue('vue-ensemble');
      activerSousVue('calendrier');
      activerModePlanification('general');
      activerOutilPlanification('selection');
      blocsLocauxPrototype = lireBlocsLocauxPrototype();
      etatCentralGui = construireEtatCentralGui(blocsLocauxPrototype, []);
      afficherEtatCentralGui(etatCentralGui);
      initialiserCurseursFrise();
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


def compteur_important_pour_barre_principale(code: Any) -> bool:
    texte = str(code).strip().upper()
    if texte in {"GCP", "JRTT", "CANC"}:
        return True
    return "PARENT" in texte or "PARENTAL" in texte or "PARENTALITE" in texte


def solde_numerique(valeur: Any) -> float | None:
    if isinstance(valeur, (int, float)):
        return float(valeur)
    return None


def solde_est_nul(valeur: Any) -> bool:
    nombre = solde_numerique(valeur)
    return nombre is not None and abs(nombre) < 0.000000001


def compteurs_tries_pour_affichage(soldes: dict[str, Any], inclure_tous: bool = False) -> list[tuple[str, Any]]:
    elements = []
    for compteur, valeur in soldes.items():
        code = str(compteur)
        important = compteur_important_pour_barre_principale(code)
        nul = solde_est_nul(valeur)
        if not inclure_tous and nul and not important:
            continue
        # Le tri par expiration réelle remplacera ce repli dès que les dates d’expiration
        # seront disponibles dans le modèle.
        if not nul:
            groupe = 0
        elif important:
            groupe = 1
        elif inclure_tous:
            groupe = 3
        else:
            groupe = 2
        elements.append((groupe, code.upper(), code, valeur))
    return [(code, valeur) for _groupe, _cle, code, valeur in sorted(elements)]


def barre_outils_gauche() -> str:
    return """
    <aside class="barre-outils-gauche" aria-label="Barre d’outils de planification">
      <h3>Outils</h3>
      <button type="button" class="outil-passif outil-actif outil-selection-actif" data-outil-planification="selection" aria-pressed="true">Sélection</button>
      <button type="button" class="outil-passif" data-outil-planification="poser" aria-pressed="false">Poser des jours</button>
      <button type="button" class="outil-passif outil-desactive" disabled>Scinder</button>
      <button type="button" class="outil-passif outil-desactive" disabled>Fusionner</button>
      <h3>Affichage</h3>
      <button type="button" class="outil-passif outil-actif mode-affichage-actif" data-mode-planification="general" aria-pressed="true">Général</button>
      <button type="button" class="outil-passif" data-mode-planification="detaille" aria-pressed="false">Détaillé</button>
    </aside>
    """



def liste_compteurs_compacte(soldes: dict[str, Any], inclure_tous: bool = False) -> str:
    lignes = []
    for compteur, valeur in compteurs_tries_pour_affichage(soldes, inclure_tous=inclure_tous):
        valeur_lisible = formater_nombre_francais(valeur) if isinstance(valeur, (int, float)) else str(valeur)
        lignes.append(
            "<li class=\"ligne-compteur-compacte\">"
            f"<span>{escape(str(compteur))}</span>"
            f"<strong>{escape(valeur_lisible)}</strong>"
            "</li>"
        )
    return "".join(lignes) if lignes else "<li class=\"ligne-compteur-compacte\">aucun solde disponible</li>"


def grille_compteurs_droite(soldes: dict[str, Any]) -> str:
    cellules = []
    for compteur, valeur in compteurs_tries_pour_affichage(soldes):
        valeur_lisible = formater_nombre_francais(valeur) if isinstance(valeur, (int, float)) else str(valeur)
        cellules.append(
            "<article class=\"compteur-mini\">"
            f"<span>{escape(str(compteur))}</span>"
            f"<strong>{escape(valeur_lisible)}</strong>"
            "</article>"
        )
    return "".join(cellules) if cellules else "<p class=\"info-compacte\">aucun solde disponible</p>"


def barre_infos_droite(projection: dict[str, Any], demi_journees: list[Any]) -> str:
    soldes_finaux = soldes_fin_projection(projection, demi_journees)
    total_restant = somme_soldes_numeriques(soldes_finaux)
    total_restant_texte = formater_quantite_jour(total_restant) if total_restant is not None else "Niveau non disponible"
    return f"""
    <aside class="barre-infos-droite barre-infos-droite-stable" aria-label="Barre d’informations de planification">
      <section class="bloc-info-fixe">
        <div class="resume-droite-compact">
          <article class="resume-mini">
            <span>Total restant</span>
            <strong>{escape(total_restant_texte)}</strong>
          </article>
          <article class="resume-mini">
            <span>Cette année</span>
            <strong>non calculé</strong>
          </article>
        </div>
        <section class="compteurs-droite-section">
          <h3>Compteurs</h3>
          <div class="grille-compteurs-droite">{grille_compteurs_droite(soldes_finaux)}</div>
        </section>
        <p class="expiration-mini"><span>Expiration</span><strong>non calculée</strong></p>
      </section>
      <section class="bloc-info-selection">
        <h3>Sélection</h3>
        <div id="selection-planification" class="selection-planification">
          <p class="info-compacte">aucune</p>
        </div>
        <div class="zone-diagnostics-planification">
          <h3>Diagnostics</h3>
          <div id="diagnostics-planification" class="diagnostics-planification">
            <p class="info-compacte">aucun</p>
          </div>
        </div>
      </section>
      <div class="separateur-infos" aria-hidden="true"></div>
      <section class="bloc-info-curseur">
        <h3>Curseur</h3>
        <div id="curseur-planification" class="curseur-planification">
          <p class="info-compacte">aucun</p>
        </div>
      </section>
    </aside>
    """



def date_infos_calendrier(demi_journees: list[Any]) -> dict[str, dict[str, Any]]:
    infos: dict[str, dict[str, Any]] = {}
    blocs: dict[str, dict[str, Any]] = {}
    sous_blocs: dict[tuple[str, str], dict[str, Any]] = {}
    evenements_par_date: dict[str, set[str]] = {}
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
                "evenements": set(),
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
            identifiant = str(detail.get("identifiant_evenement") or "")
            if not identifiant:
                continue
            info["evenements"].add(identifiant)
            evenements_par_date.setdefault(date_iso, set()).add(identifiant)
            bloc = blocs.setdefault(
                identifiant,
                {
                    "identifiant": identifiant,
                    "date_debut": date_iso,
                    "date_fin": date_iso,
                    "quantite": 0.0,
                    "compteurs": {},
                    "alertes": False,
                },
            )
            bloc["date_debut"] = min(str(bloc["date_debut"]), date_iso)
            bloc["date_fin"] = max(str(bloc["date_fin"]), date_iso)
            if isinstance(quantite, (int, float)):
                bloc["quantite"] = float(bloc["quantite"]) + float(quantite)
                if compteur:
                    compteurs = bloc["compteurs"]
                    compteurs[compteur] = float(compteurs.get(compteur, 0.0)) + float(quantite)
            if demi_journee.get("alertes"):
                bloc["alertes"] = True
            if compteur and isinstance(quantite, (int, float)):
                cle_sous_bloc = (identifiant, compteur)
                sous_bloc = sous_blocs.setdefault(
                    cle_sous_bloc,
                    {
                        "identifiant": identifiant,
                        "compteur": compteur,
                        "date_debut": date_iso,
                        "date_fin": date_iso,
                        "quantite": 0.0,
                    },
                )
                sous_bloc["date_debut"] = min(str(sous_bloc["date_debut"]), date_iso)
                sous_bloc["date_fin"] = max(str(sous_bloc["date_fin"]), date_iso)
                sous_bloc["quantite"] = float(sous_bloc["quantite"]) + float(quantite)
    for date_iso, info in infos.items():
        variantes = []
        for identifiant in sorted(evenements_par_date.get(date_iso, set())):
            if identifiant in blocs:
                variantes.append(("bloc", blocs[identifiant]))
            sous_blocs_evenement = [
                sous_bloc
                for (id_evenement, _compteur), sous_bloc in sous_blocs.items()
                if id_evenement == identifiant
            ]
            for sous_bloc in sorted(sous_blocs_evenement, key=lambda valeur: str(valeur["compteur"])):
                variantes.append(("sous-bloc", sous_bloc))
        variantes.append(("jour", {"date": date_iso}))
        info["variantes_selection"] = variantes
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


def resume_consommation_jour(info: dict[str, Any]) -> str:
    consommations = info.get("consommations", {})
    if not isinstance(consommations, dict) or not consommations:
        return "aucune"
    return ", ".join(
        f"{compteur} {formater_quantite_jour(quantite)}"
        for compteur, quantite in sorted(consommations.items())
    )


def resume_alertes_jour(info: dict[str, Any]) -> str:
    return "présente" if info.get("alertes") else "aucune"


def resume_compteurs_selection(compteurs: Any) -> str:
    if not isinstance(compteurs, dict) or not compteurs:
        return "aucun"
    return ", ".join(
        f"{compteur} {formater_quantite_jour(quantite)}"
        for compteur, quantite in sorted(compteurs.items())
    )


def compteur_principal_jour(consommations: Any) -> str:
    if not isinstance(consommations, dict) or not consommations:
        return ""
    compteurs = {str(compteur) for compteur in consommations.keys() if str(compteur)}
    for compteur_prioritaire in ("GCP", "JRTT", "CANC"):
        if compteur_prioritaire in compteurs:
            return compteur_prioritaire
    return sorted(compteurs)[0] if compteurs else ""


def classe_compteur_calendrier(compteur: str) -> str:
    compteur_normalise = compteur.strip().upper().replace("_", "-")
    if compteur_normalise in {"GCP", "JRTT", "CANC"}:
        return f"compteur-{compteur_normalise.lower()}"
    if compteur_normalise:
        return "compteur-defaut"
    return ""


def libelle_compteur_calendrier(compteur: str) -> str:
    compteur_normalise = compteur.strip().upper()
    if compteur_normalise == "NON_RECALCULE":
        return "non rec."
    if compteur_normalise in {"GCP", "JRTT", "CANC"}:
        return compteur_normalise
    return compteur.strip() or ""


def attributs_niveau_selection(type_selection: str, donnees: dict[str, Any], info: dict[str, Any]) -> str:
    attributs = [f"data-selection-type=\"{escape(type_selection)}\""]
    if type_selection == "jour":
        date_iso = str(donnees.get("date", ""))
        attributs.extend(
            [
                f"data-selection-date=\"{escape(formater_date_francaise(date_iso))}\"",
                f"data-selection-consommation=\"{escape(resume_consommation_jour(info))}\"",
                f"data-selection-alertes=\"{escape(resume_alertes_jour(info))}\"",
            ]
        )
    elif type_selection == "bloc":
        date_debut = str(donnees.get("date_debut"))
        date_fin = str(donnees.get("date_fin"))
        identifiant = str(donnees.get("identifiant") or "")
        attributs.extend(
            [
                f"data-selection-date-debut=\"{escape(date_debut)}\"",
                f"data-selection-date-fin=\"{escape(date_fin)}\"",
                f"data-selection-periode=\"{escape(formater_periode_francaise(date_debut, date_fin))}\"",
                f"data-selection-identifiant=\"{escape(identifiant)}\"",
                f"data-selection-libelle=\"{escape(identifiant)}\"",
                f"data-selection-quantite=\"{escape(formater_quantite_jour(donnees.get('quantite')))}\"",
                f"data-selection-compteurs=\"{escape(resume_compteurs_selection(donnees.get('compteurs')))}\"",
                f"data-selection-alertes=\"{escape('présente' if donnees.get('alertes') else 'aucune')}\"",
            ]
        )
    elif type_selection == "sous-bloc":
        date_debut = str(donnees.get("date_debut"))
        date_fin = str(donnees.get("date_fin"))
        identifiant = str(donnees.get("identifiant") or "")
        compteur = str(donnees.get("compteur") or "")
        attributs.extend(
            [
                f"data-selection-date-debut=\"{escape(date_debut)}\"",
                f"data-selection-date-fin=\"{escape(date_fin)}\"",
                f"data-selection-identifiant=\"{escape(identifiant)}\"",
                f"data-selection-periode=\"{escape(formater_periode_francaise(date_debut, date_fin))}\"",
                f"data-selection-compteur=\"{escape(compteur)}\"",
                f"data-selection-quantite=\"{escape(formater_quantite_jour(donnees.get('quantite')))}\"",
                f"data-selection-parent=\"{escape(identifiant)}\"",
            ]
        )
    return " ".join(attributs)



def niveaux_selection_jour(info: dict[str, Any]) -> str:
    variantes = info.get("variantes_selection", [])
    if not isinstance(variantes, list):
        variantes = []
    niveaux = []
    for index, variante in enumerate(variantes):
        if not isinstance(variante, tuple) or len(variante) != 2:
            continue
        type_selection, donnees = variante
        if not isinstance(donnees, dict):
            continue
        niveaux.append(
            f"<span class=\"niveau-selection selection-type-{escape(str(type_selection))}\" "
            f"data-selection-niveau=\"{index}\" "
            f"{attributs_niveau_selection(str(type_selection), donnees, info)}></span>"
        )
    return f"<span class=\"selection-niveaux\" hidden>{''.join(niveaux)}</span>"


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
            classes = ["jour-calendrier", "element-selectionnable", "jour-selectionnable"]
            if info.get("consommations"):
                classes.append("jour-avec-consommation")
            compteur_principal = compteur_principal_jour(info.get("consommations"))
            classe_compteur = classe_compteur_calendrier(compteur_principal)
            if classe_compteur:
                classes.append(classe_compteur)
            if info.get("alertes"):
                classes.append("jour-avec-alerte")
            date_jour = date_iso_vers_objet(date_iso)
            jour = date_jour.day
            libelle_semaine = JOURS_SEMAINE_COURTS[date_jour.weekday()]
            classe_libelle_semaine = "libelle-jour-semaine"
            if libelle_semaine == "dim":
                classe_libelle_semaine += " jour-dimanche"
            libelle_compteur = libelle_compteur_calendrier(compteur_principal)
            type_compteur = (
                f"<span class=\"type-compteur-jour\">{escape(libelle_compteur)}</span>"
                if libelle_compteur
                else "<span class=\"type-compteur-jour type-compteur-vide\" aria-hidden=\"true\"></span>"
            )
            jours.append(
                "<span class=\"cellule-calendrier\">"
                f"<span class=\"{' '.join(classes)}\" title=\"{escape(titre_jour_calendrier(date_iso, info))}\" "
                "role=\"button\" tabindex=\"0\" "
                "data-selection-cyclique=\"true\" "
                f"data-date-iso=\"{escape(date_iso)}\" "
                "data-selection-type=\"jour\" "
                f"data-selection-date=\"{escape(formater_date_francaise(date_iso))}\" "
                f"data-selection-consommation=\"{escape(resume_consommation_jour(info))}\" "
                f"data-selection-alertes=\"{escape(resume_alertes_jour(info))}\">"
                f"<span class=\"numero-jour-calendrier\">{jour}</span>"
                f"{type_compteur}"
                f"{niveaux_selection_jour(info)}"
                "</span>"
                f"<span class=\"{classe_libelle_semaine}\">{libelle_semaine}</span>"
                "</span>"
            )
        blocs_mois.append(
            "<section class=\"mois-calendrier\">"
            f"<h4>{escape(libelle_mois)}</h4>"
            f"<div class=\"jours-calendrier\">{''.join(jours)}</div>"
            "</section>"
        )
    contenu = "".join(blocs_mois) if blocs_mois else "<p>Aucune date projetée.</p>"
    return f"""
    <section class="vue-calendrier-passif sous-vue-planification sous-vue-planification-active" data-sous-vue="calendrier">
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


def dates_projection(demi_journees: list[Any], points: list[dict[str, Any]]) -> tuple[date, date] | None:
    valeurs = []
    for point in points:
        date_point = point.get("date")
        if isinstance(date_point, str) and date_point:
            valeurs.append(date_iso_vers_objet(date_point))
    for demi_journee in demi_journees:
        if isinstance(demi_journee, dict) and demi_journee.get("date"):
            valeurs.append(date_iso_vers_objet(str(demi_journee["date"])))
    if not valeurs:
        return None
    return min(valeurs), max(valeurs)


def x_temps(jour: date, debut: date, fin: date, gauche: float, droite: float) -> float:
    duree = max(1, (fin - debut).days)
    return gauche + ((jour - debut).days / duree) * (droite - gauche)


def bornes_reste(points: list[dict[str, Any]]) -> tuple[int, int]:
    valeurs = [float(point["niveau"]) for point in points]
    minimum = min(0.0, min(valeurs))
    maximum = max(0.0, max(valeurs))
    borne_min = int(minimum // 5 * 5)
    borne_max = int(((maximum + 4.999999) // 5) * 5)
    if borne_min == borne_max:
        borne_max = borne_min + 5
    return borne_min, borne_max


def graduations_reste(minimum: int, maximum: int) -> list[int]:
    return list(range(maximum, minimum - 1, -5))


def graduations_mois(debut: date, fin: date) -> list[date]:
    mois = date(debut.year, debut.month, 1)
    if mois < debut:
        mois = date(mois.year + 1, 1, 1) if mois.month == 12 else date(mois.year, mois.month + 1, 1)
    valeurs = []
    while mois <= fin:
        valeurs.append(mois)
        mois = date(mois.year + 1, 1, 1) if mois.month == 12 else date(mois.year, mois.month + 1, 1)
    return valeurs


def graduations_jours(debut: date, fin: date) -> list[date]:
    valeurs = []
    courant = debut
    while courant <= fin:
        valeurs.append(courant)
        courant += timedelta(days=7)
    if valeurs and valeurs[-1] != fin:
        valeurs.append(fin)
    return valeurs


def blocs_frise_svg(demi_journees: list[Any], alertes: list[Any], debut: date, fin: date, gauche: float, droite: float) -> str:
    evenements = agreger_evenements_projetes(demi_journees, alertes)
    blocs = []
    y = 34
    hauteur = 18
    for evenement in evenements:
        date_debut = evenement.get("date_debut")
        date_fin = evenement.get("date_fin")
        if not date_debut or not date_fin:
            continue
        debut_evenement = date_iso_vers_objet(str(date_debut))
        fin_evenement = date_iso_vers_objet(str(date_fin))
        x1 = x_temps(debut_evenement, debut, fin, gauche, droite)
        x2 = x_temps(fin_evenement, debut, fin, gauche, droite)
        largeur = max(8.0, x2 - x1 + 8.0)
        titre = (
            f"{titre_evenement_projete(evenement)} — "
            f"{evenement.get('identifiant_evenement') or ''} — "
            f"{formater_quantite_jour(evenement.get('quantite_appliquee_totale'))}"
        )
        periode = formater_periode_francaise(str(date_debut), str(date_fin))
        identifiant = str(evenement.get("identifiant_evenement") or "")
        quantite = formater_quantite_jour(evenement.get("quantite_appliquee_totale"))
        compteurs = {
            compteur: valeurs.get("quantite_appliquee")
            for compteur, valeurs in evenement.get("compteurs", {}).items()
            if isinstance(valeurs, dict)
        }
        compteurs_texte = resume_compteurs_selection(compteurs)
        alertes_texte = "présente" if evenement.get("alertes") else "aucune"
        liaisons = (
            f"<line class=\"liaison-bloc-courbe borne-bloc-debut\" x1=\"{x1:.2f}\" y1=\"{y + hauteur}\" x2=\"{x1:.2f}\" y2=\"276\" />"
            f"<line class=\"liaison-bloc-courbe borne-bloc-fin\" x1=\"{x1 + largeur:.2f}\" y1=\"{y + hauteur}\" x2=\"{x1 + largeur:.2f}\" y2=\"276\" />"
        )
        blocs.append(
            liaisons +
            f"<rect class=\"bloc-temporel-projete element-selectionnable\" x=\"{x1:.2f}\" y=\"{y}\" "
            f"width=\"{largeur:.2f}\" height=\"{hauteur}\" rx=\"5\" role=\"button\" tabindex=\"0\" "
            "data-selection-type=\"bloc\" "
            f"data-selection-identifiant=\"{escape(identifiant)}\" "
            f"data-selection-periode=\"{escape(periode)}\" "
            f"data-selection-libelle=\"{escape(str(evenement.get('libelle') or identifiant))}\" "
            f"data-selection-quantite=\"{escape(quantite)}\" "
            f"data-selection-compteurs=\"{escape(compteurs_texte)}\" "
            f"data-selection-alertes=\"{escape(alertes_texte)}\">"
            f"<title>{escape(titre)}</title>"
            "</rect>"
        )
    return "".join(blocs)


def courbe_reste_agrege(points: list[dict[str, Any]], demi_journees: list[Any], alertes: list[Any]) -> str:
    periode = dates_projection(demi_journees, points)
    if not points or periode is None:
        return "<p>Niveau non disponible</p>"
    debut, fin = periode
    largeur = 1120
    hauteur = 360
    marge_gauche = 58
    marge_droite = 28
    graphe_haut = 92
    graphe_bas = 282
    minimum, maximum = bornes_reste(points)
    amplitude = maximum - minimum or 1

    def y_reste(valeur: float) -> float:
        return graphe_bas - ((valeur - minimum) * (graphe_bas - graphe_haut) / amplitude)

    coordonnees = []
    for point in points:
        x = x_temps(date_iso_vers_objet(str(point["date"])), debut, fin, marge_gauche, largeur - marge_droite)
        y = y_reste(float(point["niveau"]))
        coordonnees.append((x, y, point))
    polyline = " ".join(f"{x:.2f},{y:.2f}" for x, y, _point in coordonnees)

    lignes_reste = []
    for valeur in graduations_reste(minimum, maximum):
        y = y_reste(float(valeur))
        lignes_reste.append(
            f"<g class=\"repere-reste\">"
            f"<line x1=\"{marge_gauche}\" y1=\"{y:.2f}\" x2=\"{largeur - marge_droite}\" y2=\"{y:.2f}\" />"
            f"<text x=\"{marge_gauche - 10}\" y=\"{y + 4:.2f}\" text-anchor=\"end\">{valeur}</text>"
            "</g>"
        )

    mois_svg = []
    for mois in graduations_mois(debut, fin):
        x = x_temps(mois, debut, fin, marge_gauche, largeur - marge_droite)
        mois_svg.append(
            f"<g class=\"repere-mois\">"
            f"<line x1=\"{x:.2f}\" y1=\"{graphe_haut - 18}\" x2=\"{x:.2f}\" y2=\"{graphe_bas + 14}\" />"
            f"<text x=\"{x:.2f}\" y=\"{hauteur - 14}\" text-anchor=\"middle\">{escape(MOIS_FRANCAIS[mois.month])}</text>"
            "</g>"
        )

    jours_svg = []
    for jour in graduations_jours(debut, fin):
        x = x_temps(jour, debut, fin, marge_gauche, largeur - marge_droite)
        jours_svg.append(
            f"<g class=\"repere-jour\">"
            f"<line x1=\"{x:.2f}\" y1=\"{graphe_bas}\" x2=\"{x:.2f}\" y2=\"{graphe_bas + 7}\" />"
            f"<text x=\"{x:.2f}\" y=\"{hauteur - 34}\" text-anchor=\"middle\">{jour.day:02d}</text>"
            "</g>"
        )

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
            f"<circle class=\"point-reste-agrege element-selectionnable\" cx=\"{x:.2f}\" cy=\"{y:.2f}\" r=\"4\" "
            "role=\"button\" tabindex=\"0\" data-selection-type=\"reste\" "
            f"data-selection-date=\"{escape(formater_date_francaise(str(point.get('date'))))}\" "
            f"data-selection-portion=\"{escape(str(point.get('portion') or TIRET))}\" "
            f"data-selection-niveau=\"{escape(formater_quantite_jour(point.get('niveau')))}\">"
            f"<title>{escape(titre)}</title></circle>"
        )
    points_curseur_svg = []
    for x, _y, point in coordonnees:
        points_curseur_svg.append(
            f"<circle class=\"point-curseur-frise\" data-x=\"{x:.2f}\" "
            f"data-selection-date=\"{escape(formater_date_francaise(str(point.get('date'))))}\" "
            f"data-selection-portion=\"{escape(str(point.get('portion') or TIRET))}\" "
            f"data-selection-niveau=\"{escape(formater_quantite_jour(point.get('niveau')))}\" r=\"0\"></circle>"
        )

    blocs = blocs_frise_svg(demi_journees, alertes, debut, fin, marge_gauche, largeur - marge_droite)
    return (
        f"<svg class=\"courbe-reste-agrege\" viewBox=\"0 0 {largeur} {hauteur}\" role=\"img\" "
        "aria-label=\"Courbe du reste agrégé provisoire\">"
        f"<line class=\"ligne-curseur-frise\" x1=\"{marge_gauche}\" y1=\"{graphe_haut - 20}\" "
        f"x2=\"{marge_gauche}\" y2=\"{graphe_bas + 12}\" style=\"display:none\" />"
        "<g class=\"donnees-curseur-frise\" hidden>"
        f"{''.join(points_curseur_svg)}"
        "</g>"
        "<g class=\"ligne-blocs-temporels\">"
        f"{blocs}"
        "</g>"
        "<g class=\"ligne-blocs-locaux\"></g>"
        "<g class=\"axe-vertical\">"
        f"{''.join(lignes_reste)}"
        "</g>"
        f"<line class=\"axe-horizontal\" x1=\"{marge_gauche}\" y1=\"{graphe_bas}\" x2=\"{largeur - marge_droite}\" y2=\"{graphe_bas}\" />"
        f"<line class=\"axe-vertical\" x1=\"{marge_gauche}\" y1=\"{graphe_haut}\" x2=\"{marge_gauche}\" y2=\"{graphe_bas}\" />"
        "<g class=\"axe-horizontal-reperes\">"
        f"{''.join(mois_svg)}{''.join(jours_svg)}"
        "</g>"
        f"<polyline points=\"{polyline}\" fill=\"none\" />"
        f"{''.join(points_svg)}"
        "</svg>"
    )


def vue_frise_niveau_passive(demi_journees: list[Any], alertes: list[Any]) -> str:
    points = points_reste_agrege(demi_journees)
    return f"""
    <section class="vue-frise-niveau sous-vue-planification" data-sous-vue="frise">
      <h3>Frise et reste agrégé provisoire</h3>
      <div class="niveau-reste-agrege">
        <h4>reste agrégé provisoire</h4>
        <p class="note">Formule temporaire : somme simple des soldes_apres numériques. N’inclut pas encore réserves, expirations fines, acquisitions futures ni règles d’allocation complètes.</p>
        {courbe_reste_agrege(points, demi_journees, alertes)}
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
        <div class="sous-vues-planification" role="tablist" aria-label="Vues passives de planification">
          <button type="button" class="bouton-sous-vue sous-vue-active" data-sous-vue-cible="calendrier" aria-selected="true">Calendrier</button>
          <button type="button" class="bouton-sous-vue" data-sous-vue-cible="frise" aria-selected="false">Frise</button>
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
      --compteur-gcp: #c96f75;
      --compteur-jrtt: #4f86c6;
      --compteur-canc: #4f9b73;
      --compteur-defaut: #146b5f;
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
      width: 100%;
      max-width: none;
      margin: 0 auto;
      padding: 24px clamp(14px, 2vw, 30px) 56px;
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
    .rail-frise .repere-mois {
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
      width: 100%;
      max-width: none;
      height: calc(100vh - 150px);
      min-height: 560px;
      overflow: hidden;
      grid-template-columns: minmax(150px, 180px) minmax(0, 1fr) minmax(220px, 280px);
      gap: 16px;
      align-items: stretch;
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
    .barre-infos-droite,
    .selection-planification,
    .champ-selection,
    .valeur-longue {
      max-width: 100%;
      overflow-x: hidden;
      overflow-wrap: anywhere;
      word-break: break-word;
    }
    .zone-centrale-planification {
      min-width: 0;
      min-height: 0;
      height: 100%;
      overflow-y: auto;
      overflow-x: hidden;
      overscroll-behavior: contain;
    }
    .barre-outils-gauche,
    .barre-infos-droite {
      position: static;
      height: 100%;
      min-height: 0;
    }
    .barre-outils-gauche {
      overflow-y: auto;
      overflow-x: hidden;
    }
    .barre-infos-droite {
      display: grid;
      grid-template-rows: auto minmax(0, 1fr) auto auto;
      height: 100%;
      max-height: 100%;
      overflow: hidden;
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
    .info-compacte {
      margin: 0 0 12px;
    }
    .liste-compteurs-compacte {
      padding: 0;
      margin: 0 0 10px;
      list-style: none;
    }
    .ligne-compteur-compacte {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 4px 0;
      border-bottom: 1px dashed rgba(216, 201, 174, 0.75);
      font-variant-numeric: tabular-nums;
    }
    .ligne-compteur-compacte span {
      color: var(--accent-fort);
      font-weight: 700;
    }
    .sous-vues-planification {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 14px;
    }
    .bouton-sous-vue {
      padding: 8px 14px;
      border: 1px solid var(--trait);
      border-radius: 999px;
      color: var(--muted);
      background: rgba(255, 255, 255, 0.35);
      font: inherit;
      cursor: pointer;
    }
    .bouton-sous-vue:hover {
      background: rgba(20, 107, 95, 0.1);
    }
    .bouton-sous-vue.sous-vue-active {
      color: white;
      background: var(--accent);
      border-color: var(--accent-fort);
    }
    .sous-vue-planification {
      display: none;
    }
    .sous-vue-planification-active {
      display: block;
    }
    .vue-calendrier-passif,
    .vue-frise-niveau {
      margin-top: 14px;
      padding: 16px;
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
      grid-template-columns: repeat(31, minmax(20px, 1fr));
      gap: 3px;
      width: 100%;
    }
    .cellule-calendrier {
      display: grid;
      grid-template-rows: minmax(31px, auto) auto;
      gap: 2px;
      min-width: 0;
    }
    .jour-calendrier {
      position: relative;
      min-height: 31px;
      display: grid;
      grid-template-rows: 1fr auto;
      align-items: center;
      justify-items: center;
      gap: 1px;
      padding: 2px 1px;
      border: 1px solid #cbbd9f;
      border-radius: 7px;
      background: #fffaf0;
      color: var(--muted);
      font-size: 0.82rem;
      font-variant-numeric: tabular-nums;
    }
    .numero-jour-calendrier {
      line-height: 1;
    }
    .type-compteur-jour {
      min-height: 0.7rem;
      color: var(--muted);
      font-size: 0.58rem;
      font-weight: 650;
      line-height: 1;
      opacity: 0.78;
      text-transform: lowercase;
      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .interface-planification[data-mode-planification="general"] .type-compteur-jour {
      visibility: hidden;
    }
    .interface-planification[data-mode-planification="detaille"] .type-compteur-jour {
      visibility: visible;
    }
    .libelle-jour-semaine {
      color: var(--muted);
      font-size: 0.58rem;
      line-height: 1;
      text-align: center;
      text-transform: lowercase;
      user-select: none;
    }
    .libelle-jour-semaine.jour-dimanche {
      font-weight: 800;
    }
    .element-selectionnable {
      cursor: pointer;
      outline: none;
    }
    .element-selectionnable:focus {
      outline: 3px solid rgba(20, 107, 95, 0.32);
      outline-offset: 2px;
    }
    .jour-calendrier.selection-active,
    .jour-selectionne {
      box-shadow: inset 0 0 0 3px var(--accent-fort);
      color: var(--accent-fort);
      font-weight: 700;
    }
    .jour-avec-consommation {
      background: rgba(20, 107, 95, 0.16);
      color: var(--accent-fort);
      border-color: var(--accent);
      font-weight: 700;
    }
    .interface-planification[data-mode-planification="detaille"] .jour-calendrier.compteur-gcp {
      background: rgba(201, 111, 117, 0.22);
      border-color: var(--compteur-gcp);
      color: #743c42;
    }
    .interface-planification[data-mode-planification="detaille"] .jour-calendrier.compteur-jrtt {
      background: rgba(79, 134, 198, 0.22);
      border-color: var(--compteur-jrtt);
      color: #28547f;
    }
    .interface-planification[data-mode-planification="detaille"] .jour-calendrier.compteur-canc {
      background: rgba(79, 155, 115, 0.22);
      border-color: var(--compteur-canc);
      color: #2d6b4b;
    }
    .interface-planification[data-mode-planification="detaille"] .jour-calendrier.compteur-defaut {
      background: rgba(20, 107, 95, 0.14);
      border-color: var(--compteur-defaut);
      color: var(--accent-fort);
    }
    .jour-avec-alerte {
      box-shadow: inset 0 0 0 2px rgba(177, 59, 46, 0.5);
    }
    .jour-survol-simple {
      outline: 2px solid rgba(20, 107, 95, 0.18);
      outline-offset: 2px;
    }
    .jour-avec-bloc-utilisateur {
      background: rgba(20, 107, 95, 0.08);
      border-color: rgba(20, 107, 95, 0.62);
      border-style: dashed;
      color: var(--accent-fort);
      font-weight: 700;
    }
    .interface-planification[data-mode-planification="detaille"] .jour-calendrier.origine-utilisateur.compteur-manuel-gcp {
      background: rgba(201, 111, 117, 0.12);
      border-color: rgba(201, 111, 117, 0.78);
      color: #743c42;
    }
    .interface-planification[data-mode-planification="detaille"] .jour-calendrier.origine-utilisateur.compteur-manuel-jrtt {
      background: rgba(79, 134, 198, 0.12);
      border-color: rgba(79, 134, 198, 0.78);
      color: #28547f;
    }
    .interface-planification[data-mode-planification="detaille"] .jour-calendrier.origine-utilisateur.compteur-manuel-canc {
      background: rgba(79, 155, 115, 0.12);
      border-color: rgba(79, 155, 115, 0.78);
      color: #2d6b4b;
    }
    .interface-planification[data-mode-planification="detaille"] .jour-calendrier.origine-utilisateur.compteur-manuel-defaut {
      background: rgba(20, 107, 95, 0.08);
      border-color: rgba(20, 107, 95, 0.62);
      color: var(--accent-fort);
    }
    .bloc-fantome-local {
      background: rgba(155, 107, 0, 0.18);
      box-shadow: inset 0 0 0 2px rgba(155, 107, 0, 0.55);
    }
    .bloc-fantome-local.bloc-fantome-impossible {
      background: rgba(177, 59, 46, 0.14);
      box-shadow: inset 0 0 0 2px rgba(177, 59, 46, 0.55);
      border-style: dashed;
      opacity: 0.84;
    }
    .bloc-fantome-debut {
      border-left-width: 3px;
    }
    .bloc-fantome-fin {
      border-right-width: 3px;
    }
    .bloc-fantome-frise {
      fill: rgba(155, 107, 0, 0.2);
      stroke: rgba(155, 107, 0, 0.7);
      stroke-width: 1.5;
      stroke-dasharray: 4 3;
      pointer-events: none;
    }
    .bloc-fantome-frise.bloc-fantome-frise-impossible {
      fill: rgba(177, 59, 46, 0.14);
      stroke: rgba(177, 59, 46, 0.72);
      stroke-dasharray: 2 4;
      opacity: 0.86;
    }
    .niveau-reste-agrege {
      padding-top: 4px;
    }
    .courbe-reste-agrege {
      width: 100%;
      min-height: 320px;
      margin-top: 10px;
      border: 1px solid var(--trait);
      border-radius: 8px;
      background: linear-gradient(180deg, rgba(255, 250, 240, 0.88), rgba(239, 228, 208, 0.8));
    }
    .bloc-temporel-projete {
      fill: rgba(20, 107, 95, 0.72);
      stroke: var(--accent-fort);
      stroke-width: 1;
    }
    .bloc-temporel-projete.selection-active,
    .bloc-selectionne {
      fill: var(--alerte);
      stroke: #5f1d16;
      stroke-width: 3;
    }
    .bloc-utilisateur-frise {
      fill: rgba(20, 107, 95, 0.28);
      stroke: var(--accent-fort);
      stroke-width: 1;
      cursor: pointer;
    }
    .bloc-utilisateur-frise.selection-active,
    .bloc-utilisateur-frise.bloc-utilisateur-selectionne {
      fill: rgba(20, 107, 95, 0.34);
      stroke: var(--accent-fort);
      stroke-width: 3;
    }
    .liaison-bloc-courbe {
      stroke: rgba(177, 59, 46, 0.42);
      stroke-width: 1.4;
      stroke-dasharray: 5 5;
      pointer-events: none;
    }
    .axe-horizontal,
    .axe-vertical line {
      stroke: #917f62;
      stroke-width: 1;
    }
    .repere-reste line {
      stroke: rgba(145, 127, 98, 0.25);
      stroke-width: 1;
    }
    .repere-reste text,
    .repere-mois text,
    .repere-jour text {
      fill: var(--muted);
      font-size: 12px;
      font-family: Georgia, "Times New Roman", serif;
    }
    .repere-mois line {
      stroke: rgba(20, 107, 95, 0.35);
      stroke-width: 1;
    }
    .repere-jour line {
      stroke: rgba(145, 127, 98, 0.45);
      stroke-width: 1;
    }
    .courbe-reste-agrege polyline {
      stroke: var(--accent);
      stroke-width: 4;
      stroke-linejoin: round;
      stroke-linecap: round;
    }
    .point-reste-agrege {
      fill: var(--accent-fort);
    }
    .point-reste-agrege.selection-active {
      fill: var(--alerte);
      stroke: #5f1d16;
      stroke-width: 2;
    }
    .selection-planification {
      min-height: 44px;
    }
    .zone-diagnostics-planification {
      margin-top: 10px;
      border-top: 1px dashed rgba(216, 201, 174, 0.85);
      padding-top: 8px;
    }
    .diagnostics-planification {
      max-height: 86px;
      overflow-y: auto;
      overflow-x: hidden;
      overflow-wrap: anywhere;
      word-break: break-word;
    }
    .liste-diagnostics-planification {
      display: grid;
      gap: 5px;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .diagnostic-planification {
      padding: 5px 7px;
      border-left: 3px solid var(--accent);
      border-radius: 7px;
      background: rgba(255, 255, 255, 0.34);
      font-size: 0.76rem;
      line-height: 1.2;
    }
    .diagnostic-bloquant,
    .diagnostic-erreur {
      border-left-color: var(--alerte);
    }
    .fiche-selection {
      display: grid;
      gap: 8px;
    }
    .puce-selection {
      display: inline-flex;
      width: fit-content;
      max-width: 100%;
      padding: 4px 9px;
      border-radius: 999px;
      background: rgba(20, 107, 95, 0.12);
      color: var(--accent-fort);
      font-size: 0.82rem;
      font-weight: 700;
      text-transform: lowercase;
    }
    .champ-selection {
      display: grid;
      gap: 2px;
      padding: 8px;
      border: 1px solid rgba(216, 201, 174, 0.75);
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.34);
    }
    .libelle-selection {
      color: var(--muted);
      font-size: 0.72rem;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .valeur-selection {
      color: var(--accent-fort);
      font-size: 0.95rem;
      line-height: 1.25;
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
    .vue-calendrier-passif,
    .vue-frise-niveau,
    .jour-calendrier,
    .element-selectionnable,
    .courbe-reste-agrege {
      user-select: none;
    }
    .bloc-info-fixe {
      min-height: 0;
      overflow: visible;
    }
    .bloc-info-selection {
      min-height: 0;
      overflow: hidden;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr) auto;
    }
    .selection-planification {
      min-height: 0;
      height: 100%;
      overflow-y: auto;
      overflow-x: hidden;
      padding-right: 2px;
    }
    .separateur-infos {
      min-height: 0;
      margin: 10px 0;
      border-top: 1px solid rgba(216, 201, 174, 0.95);
    }
    .bloc-info-curseur {
      min-height: 0;
      overflow: hidden;
      display: grid;
      grid-template-rows: auto minmax(0, auto);
    }
    .curseur-planification {
      min-height: 0;
      max-height: 118px;
      overflow-y: auto;
      overflow-x: hidden;
    }
    .selection-plage {
      box-shadow: inset 0 0 0 3px var(--accent-fort);
      color: var(--accent-fort);
      font-weight: 700;
    }
    .selection-plage-debut {
      border-left-width: 3px;
      border-top-left-radius: 12px;
      border-bottom-left-radius: 12px;
    }
    .selection-plage-fin {
      border-right-width: 3px;
      border-top-right-radius: 12px;
      border-bottom-right-radius: 12px;
    }
    .selection-plage-sous-bloc {
      box-shadow: inset 0 0 0 3px var(--confirmation);
    }
    .selection-plage-bloc-utilisateur {
      box-shadow: inset 0 0 0 3px var(--accent-fort);
      background: rgba(20, 107, 95, 0.22);
    }
    .selection-jour-courant {
      outline: 3px solid rgba(20, 107, 95, 0.35);
      outline-offset: 2px;
    }
    .mode-affichage-actif {
      background: var(--accent);
      color: white;
      border-color: var(--accent-fort);
    }
    .ligne-curseur-frise {
      stroke: var(--alerte);
      stroke-width: 1.5;
      stroke-dasharray: 4 4;
      pointer-events: none;
    }
    .point-curseur-frise {
      display: none;
    }
    .fiche-curseur .champ-selection {
      padding: 6px 8px;
    }
    /* V0.4.6 — densification visuelle de la planification */
    body {
      font-size: 0.92rem;
      line-height: 1.34;
    }
    main {
      padding: 12px clamp(10px, 1.4vw, 22px) 30px;
    }
    .hero {
      padding: 10px 14px 10px;
      border-radius: 20px 20px 14px 14px;
    }
    .hero .note {
      max-width: none;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      margin: 0;
      font-size: 0.86rem;
    }
    h1 {
      margin: 0 0 4px;
      font-size: clamp(1.2rem, 1.9vw, 1.75rem);
      line-height: 1;
    }
    h2 {
      margin: 0 0 10px;
      font-size: 1.18rem;
    }
    h3 {
      margin: 0 0 6px;
      font-size: 0.96rem;
    }
    .barre-vues {
      gap: 7px;
      margin-top: 10px;
      padding-top: 9px;
    }
    .onglet {
      padding: 7px 12px;
      font-size: 0.9rem;
    }
    .vue-tableau-de-bord {
      margin-top: 14px;
    }
    .carte {
      margin-top: 10px;
      padding: 13px;
      border-radius: 17px;
    }
    .tuile-resume {
      padding: 13px;
      border-radius: 15px;
    }
    .tuile-valeur {
      font-size: 1.08rem;
    }
    .interface-planification {
      height: calc(100vh - 118px);
      min-height: 500px;
      gap: 12px;
      grid-template-columns: minmax(130px, 165px) minmax(0, 1fr) minmax(250px, 310px);
      overflow: hidden;
    }
    .barre-outils-gauche,
    .barre-infos-droite,
    .zone-centrale-planification {
      padding: 12px;
      border-radius: 15px;
    }
    .barre-infos-droite {
      display: grid;
      grid-template-rows: auto minmax(0, 1fr) auto auto;
      height: 100%;
      max-height: 100%;
      overflow: hidden;
    }
    .zone-centrale-planification {
      min-height: 0;
      height: 100%;
      overflow-y: auto;
      overflow-x: hidden;
    }
    .barre-outils-gauche {
      height: 100%;
      overflow-y: auto;
      overflow-x: hidden;
    }
    .outil-passif {
      margin: 6px 0;
      padding: 7px 9px;
      font-size: 0.88rem;
    }
    .sous-vues-planification {
      gap: 6px;
      margin-bottom: 10px;
    }
    .bouton-sous-vue {
      padding: 6px 11px;
      font-size: 0.88rem;
    }
    .vue-calendrier-passif,
    .vue-frise-niveau {
      margin-top: 10px;
      padding: 12px;
      border-radius: 13px;
    }
    .niveau-reste-agrege .note {
      margin: 0 0 8px;
      max-width: none;
      font-size: 0.82rem;
    }
    .courbe-reste-agrege {
      min-height: 280px;
      margin-top: 8px;
    }
    .resume-droite-compact {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-bottom: 8px;
    }
    .resume-mini {
      min-width: 0;
      padding: 8px;
      border: 1px solid rgba(216, 201, 174, 0.75);
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.32);
    }
    .resume-mini span,
    .expiration-mini span {
      display: block;
      color: var(--muted);
      font-size: 0.68rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .resume-mini strong {
      display: block;
      margin-top: 2px;
      color: var(--accent-fort);
      font-size: 1.05rem;
      line-height: 1.1;
      overflow-wrap: anywhere;
    }
    .compteurs-droite-section {
      margin-bottom: 6px;
    }
    .compteurs-droite-section h3 {
      margin-bottom: 4px;
      font-size: 0.9rem;
    }
    .grille-compteurs-droite {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 6px;
    }
    .compteur-mini {
      min-width: 0;
      padding: 6px 5px;
      border-bottom: 1px dashed rgba(216, 201, 174, 0.9);
      text-align: center;
      font-variant-numeric: tabular-nums;
    }
    .compteur-mini span {
      display: block;
      color: var(--accent-fort);
      font-size: 0.76rem;
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .compteur-mini strong {
      display: block;
      margin-top: 2px;
      color: var(--encre);
      font-size: 0.9rem;
      line-height: 1.1;
      overflow-wrap: anywhere;
    }
    .expiration-mini {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      margin: 3px 0 8px;
      font-size: 0.84rem;
    }
    .expiration-mini strong {
      color: var(--accent-fort);
      font-size: 0.86rem;
    }
    .bloc-info-selection {
      min-height: 0;
      overflow: hidden;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr) auto;
    }
    .selection-planification {
      min-height: 0;
      height: 100%;
      overflow-y: auto;
      overflow-x: hidden;
      padding-right: 2px;
    }
    .separateur-infos {
      margin: 8px 0;
      border-top: 1px solid rgba(216, 201, 174, 0.95);
    }
    .bloc-info-curseur {
      min-height: 0;
      overflow: hidden;
      display: grid;
      grid-template-rows: auto minmax(0, auto);
    }
    .curseur-planification {
      min-height: 0;
      max-height: 96px;
      overflow-y: auto;
      overflow-x: hidden;
    }
    .fiche-selection {
      gap: 6px;
    }
    .champ-selection {
      padding: 6px;
      border-radius: 8px;
    }
    .libelle-selection {
      font-size: 0.66rem;
    }
    .valeur-selection {
      font-size: 0.86rem;
      line-height: 1.16;
    }
    .puce-selection {
      padding: 3px 7px;
      font-size: 0.74rem;
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
        height: auto;
        overflow: visible;
      }
      .zone-centrale-planification,
      .barre-outils-gauche,
      .barre-infos-droite {
        height: auto;
        max-height: none;
        overflow: visible;
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
