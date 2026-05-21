from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from outils.chronotime.chargeur_obligations import normaliser_obligations
from outils.chronotime.chargeur_scenarios import normaliser_scenario
from outils.chronotime.parseur_agenda import normaliser_donnees as normaliser_agenda
from outils.chronotime.parseur_soldes_absences import normaliser_donnees as normaliser_soldes
from outils.chronotime.projecteur_demi_journees import projeter_demi_journees
from outils.chronotime.verificateur_obligations import verifier_obligations


def lire_json(chemin_entree: Path) -> Any:
    try:
        texte = chemin_entree.read_text(encoding="utf-8-sig")
    except OSError as erreur:
        raise SystemExit(f"Impossible de lire le fichier d'entrée : {chemin_entree}") from erreur

    try:
        return json.loads(texte)
    except json.JSONDecodeError as erreur:
        raise SystemExit(f"JSON invalide dans le fichier d'entrée : {chemin_entree}") from erreur


def serialiser_json(donnees: Any) -> str:
    return json.dumps(donnees, ensure_ascii=False, indent=2)


def ecrire_sortie(texte_json: str, chemin_sortie: Path | None) -> None:
    if chemin_sortie is None:
        print(texte_json)
        return

    try:
        chemin_sortie.write_text(f"{texte_json}\n", encoding="utf-8")
    except OSError as erreur:
        raise SystemExit(f"Impossible d'écrire le fichier de sortie : {chemin_sortie}") from erreur


def analyser_date_cible(valeur: str) -> dict[str, str]:
    morceaux = valeur.split("=", 2)
    if len(morceaux) != 3 or any(morceau == "" for morceau in morceaux):
        raise ValueError("Une date cible doit suivre le format identifiant=libelle=YYYY-MM-DD.")
    return {
        "identifiant": morceaux[0],
        "libelle": morceaux[1],
        "date": morceaux[2],
    }


def analyser_dates_cibles(valeurs: list[str] | None, scenario_normalise: dict[str, Any]) -> list[dict[str, Any]]:
    if valeurs:
        return [analyser_date_cible(valeur) for valeur in valeurs]

    scenario = scenario_normalise.get("scenario")
    if isinstance(scenario, dict) and isinstance(scenario.get("dates_cibles"), list):
        return scenario["dates_cibles"]
    return []


def analyser_ordre_compteurs(valeur: str) -> list[str]:
    return [compteur.strip() for compteur in valeur.split(",") if compteur.strip()]


def analyser_dictionnaire_texte(valeur: str | None, nom_option: str) -> dict[str, str]:
    if not valeur:
        return {}

    resultat = {}
    for morceau in valeur.split(","):
        element = morceau.strip()
        if element == "":
            continue
        if "=" not in element:
            raise ValueError(f"Format invalide pour {nom_option} : {element!r}.")
        cle, valeur_element = element.split("=", 1)
        cle = cle.strip()
        valeur_element = valeur_element.strip()
        if cle == "" or valeur_element == "":
            raise ValueError(f"Format invalide pour {nom_option} : {element!r}.")
        resultat[cle] = valeur_element
    return resultat


def analyser_periodes_compteurs_par_code(valeur: str | None) -> dict[str, str]:
    return analyser_dictionnaire_texte(valeur, "--periodes-compteurs-par-code")


def analyser_soldes_minimums_par_code(valeur: str | None) -> dict[str, float]:
    valeurs_texte = analyser_dictionnaire_texte(valeur, "--soldes-minimums-par-code")
    resultat = {}
    for code, minimum in valeurs_texte.items():
        try:
            resultat[code] = float(minimum)
        except ValueError as erreur:
            raise ValueError(f"Solde minimum invalide pour {code} : {minimum!r}.") from erreur
    return resultat


def analyser_jours_non_decomptes(valeur: str | None) -> list[str]:
    if not valeur:
        return []
    return [jour.strip() for jour in valeur.split(",") if jour.strip()]


def enrichir_verification_obligations(
    verification_obligations: dict[str, Any],
    obligations_normalisees: dict[str, Any],
) -> dict[str, Any]:
    obligations_par_identifiant = {
        obligation["identifiant"]: obligation
        for obligation in obligations_normalisees.get("obligations", [])
        if isinstance(obligation, dict) and obligation.get("identifiant")
    }

    obligations_enrichies = []
    for verification in verification_obligations.get("obligations", []):
        if not isinstance(verification, dict):
            continue
        obligation = obligations_par_identifiant.get(verification.get("identifiant"), {})
        verification_enrichie = dict(verification)
        for champ in ("date_debut", "date_fin", "unite", "compteur_prefere", "priorite"):
            if champ not in verification_enrichie and champ in obligation:
                verification_enrichie[champ] = obligation[champ]
        obligations_enrichies.append(verification_enrichie)

    resultat = dict(verification_obligations)
    resultat["obligations"] = obligations_enrichies
    return resultat


def construire_entrees_projection(
    soldes_normalises: dict[str, Any],
    scenario_normalise: dict[str, Any],
    verification_obligations: dict[str, Any],
    date_depart: str,
    date_fin: str,
    periode_compteurs: str,
    periodes_compteurs_par_code: dict[str, str],
    soldes_minimums_par_code: dict[str, float],
    jours_non_decomptes: list[str],
    dates_cibles: list[dict[str, Any]],
    ordre_compteurs_sans_preference: list[str],
) -> dict[str, Any]:
    return {
        "source": "projection.demi_journees.entrees",
        "soldes": soldes_normalises,
        "scenario": scenario_normalise,
        "verification_obligations": verification_obligations,
        "parametres_projection": {
            "periode_compteurs": periode_compteurs,
            "periodes_compteurs_par_code": periodes_compteurs_par_code,
            "soldes_minimums_par_code": soldes_minimums_par_code,
            "jours_non_decomptes": jours_non_decomptes,
            "date_depart": date_depart,
            "date_fin": date_fin,
            "dates_cibles": dates_cibles,
            "ordre_compteurs_sans_preference": ordre_compteurs_sans_preference,
        },
    }


def orchestrer_projection(arguments: argparse.Namespace) -> dict[str, Any]:
    soldes_normalises = normaliser_soldes(lire_json(arguments.soldes))
    agenda_normalise = normaliser_agenda(lire_json(arguments.agenda))
    scenario_normalise = normaliser_scenario(lire_json(arguments.scenario))
    obligations_normalisees = normaliser_obligations(lire_json(arguments.obligations))

    verification = verifier_obligations(obligations_normalisees, agenda_normalise)
    verification = enrichir_verification_obligations(verification, obligations_normalisees)
    dates_cibles = analyser_dates_cibles(arguments.date_cible, scenario_normalise)

    entrees_projection = construire_entrees_projection(
        soldes_normalises=soldes_normalises,
        scenario_normalise=scenario_normalise,
        verification_obligations=verification,
        date_depart=arguments.date_depart,
        date_fin=arguments.date_fin,
        periode_compteurs=arguments.periode_compteurs,
        periodes_compteurs_par_code=analyser_periodes_compteurs_par_code(arguments.periodes_compteurs_par_code),
        soldes_minimums_par_code=analyser_soldes_minimums_par_code(arguments.soldes_minimums_par_code),
        jours_non_decomptes=analyser_jours_non_decomptes(arguments.jours_non_decomptes),
        dates_cibles=dates_cibles,
        ordre_compteurs_sans_preference=analyser_ordre_compteurs(arguments.ordre_compteurs_sans_preference),
    )
    return projeter_demi_journees(entrees_projection)


def analyser_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(
        description="Orchestrer localement la normalisation, la vérification et la projection demi-journalière.",
    )
    analyseur.add_argument("--soldes", required=True, type=Path, help="Fichier JSON local des soldes Chronotime.")
    analyseur.add_argument("--agenda", required=True, type=Path, help="Fichier JSON local de l'agenda Chronotime.")
    analyseur.add_argument("--obligations", required=True, type=Path, help="Fichier JSON local des obligations.")
    analyseur.add_argument("--scenario", required=True, type=Path, help="Fichier JSON local du scénario.")
    analyseur.add_argument("--date-depart", required=True, help="Date de départ de projection au format YYYY-MM-DD.")
    analyseur.add_argument("--date-fin", required=True, help="Date de fin de projection au format YYYY-MM-DD.")
    analyseur.add_argument("--date-cible", action="append", help="Date cible au format identifiant=libelle=YYYY-MM-DD.")
    analyseur.add_argument("--periode-compteurs", default="courant", help="Période de compteurs à utiliser.")
    analyseur.add_argument(
        "--periodes-compteurs-par-code",
        help="Périodes par compteur au format GCP=suivant,JRTT=courant.",
    )
    analyseur.add_argument(
        "--soldes-minimums-par-code",
        help="Soldes minimums par compteur au format JRTT=-10,GCP=0.",
    )
    analyseur.add_argument(
        "--jours-non-decomptes",
        help="Dates non décomptées au format YYYY-MM-DD,YYYY-MM-DD.",
    )
    analyseur.add_argument(
        "--ordre-compteurs-sans-preference",
        default="CANC,JRTT,GCP",
        help="Ordre des compteurs pour les obligations sans compteur préféré.",
    )
    analyseur.add_argument("--sortie", type=Path, help="Chemin du fichier où écrire la projection.")
    return analyseur.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = analyser_arguments(argv)
    try:
        projection = orchestrer_projection(arguments)
    except ValueError as erreur:
        raise SystemExit(str(erreur)) from erreur
    ecrire_sortie(serialiser_json(projection), arguments.sortie)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
