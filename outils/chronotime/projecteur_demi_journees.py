from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any


PORTIONS = ("matin", "apres_midi")
SOURCE_SORTIE = "projection.demi_journees"


def lire_json(chemin_entree: Path) -> Any:
    try:
        texte = chemin_entree.read_text(encoding="utf-8")
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


def normaliser_date_iso(valeur: Any, nom_champ: str = "date") -> str | None:
    if valeur is None:
        return None
    if not isinstance(valeur, str):
        raise ValueError(f"Date ISO invalide pour {nom_champ} : {valeur!r}")
    try:
        return date.fromisoformat(valeur).isoformat()
    except ValueError as erreur:
        raise ValueError(f"Date ISO invalide pour {nom_champ} : {valeur!r}") from erreur


def convertir_date_iso(valeur: Any, nom_champ: str) -> date:
    date_normalisee = normaliser_date_iso(valeur, nom_champ)
    if date_normalisee is None:
        raise ValueError(f"Date ISO obligatoire pour {nom_champ}.")
    return date.fromisoformat(date_normalisee)


def arrondir_quantite(valeur: float) -> float:
    return round(float(valeur), 10)


def extraire_soldes_initiaux(donnees: dict[str, Any], periode: str = "courant") -> dict[str, float]:
    soldes = donnees.get("soldes", {})
    compteurs = soldes.get("compteurs", []) if isinstance(soldes, dict) else []
    soldes_initiaux: dict[str, float] = {}

    for compteur in compteurs:
        if not isinstance(compteur, dict):
            continue
        code = compteur.get("code")
        periodes = compteur.get("periodes")
        if not code or not isinstance(periodes, dict):
            continue
        periode_compteur = periodes.get(periode)
        if not isinstance(periode_compteur, dict):
            continue
        solde = periode_compteur.get("solde")
        if not isinstance(solde, dict):
            continue
        valeur = solde.get("valeur")
        if isinstance(valeur, (int, float)):
            soldes_initiaux[str(code)] = float(valeur)

    return soldes_initiaux


def creer_vecteur_demi_journees(date_depart: str, date_fin: str) -> list[dict[str, Any]]:
    debut = convertir_date_iso(date_depart, "parametres_projection.date_depart")
    fin = convertir_date_iso(date_fin, "parametres_projection.date_fin")
    if fin < debut:
        raise ValueError("La date de fin de projection doit être postérieure ou égale à la date de départ.")

    demi_journees: list[dict[str, Any]] = []
    index = 0
    date_courante = debut
    while date_courante <= fin:
        for portion in PORTIONS:
            demi_journees.append(
                {
                    "date": date_courante.isoformat(),
                    "portion": portion,
                    "index_demi_journee": index,
                    "evenements": [],
                    "consommations": {},
                    "soldes_avant": {},
                    "soldes_apres": {},
                    "alertes": [],
                }
            )
            index += 1
        date_courante += timedelta(days=1)
    return demi_journees


def choisir_compteur(compteurs_autorises: list[Any], compteur_prefere: Any, ordre_sans_preference: list[Any]) -> str | None:
    compteurs = [str(compteur) for compteur in compteurs_autorises if compteur]
    if not compteurs:
        return None
    if len(compteurs) == 1:
        return compteurs[0]
    if compteur_prefere:
        compteur = str(compteur_prefere)
        if compteur in compteurs:
            return compteur
    for compteur in ordre_sans_preference:
        compteur_texte = str(compteur)
        if compteur_texte in compteurs:
            return compteur_texte
    return compteurs[0]


def construire_evenements_obligations(donnees: dict[str, Any], ordre_sans_preference: list[Any]) -> list[dict[str, Any]]:
    verification = donnees.get("verification_obligations", {})
    obligations = verification.get("obligations", []) if isinstance(verification, dict) else []
    evenements: list[dict[str, Any]] = []

    for obligation in obligations:
        if not isinstance(obligation, dict):
            continue
        if obligation.get("statut_obligation") == "satisfaite":
            continue
        quantite = obligation.get("quantite_restante", obligation.get("quantite_requise"))
        if not isinstance(quantite, (int, float)) or quantite <= 0:
            continue
        compteur = choisir_compteur(
            obligation.get("compteurs_autorises", []),
            obligation.get("compteur_prefere"),
            ordre_sans_preference,
        )
        if compteur is None:
            continue
        evenements.append(
            {
                "source": "obligation",
                "identifiant": str(obligation.get("identifiant", "")),
                "libelle": str(obligation.get("libelle", "")),
                "date_debut": normaliser_date_iso(obligation.get("date_debut"), "obligation.date_debut"),
                "date_fin": normaliser_date_iso(obligation.get("date_fin"), "obligation.date_fin"),
                "unite": str(obligation.get("unite", "jours_ouvres")),
                "quantite": float(quantite),
                "compteur": compteur,
                "priorite": int(obligation.get("priorite", 100)),
            }
        )
    return evenements


def construire_evenements_scenario(donnees: dict[str, Any]) -> list[dict[str, Any]]:
    donnees_scenario = donnees.get("scenario", {})
    scenario = donnees_scenario.get("scenario", {}) if isinstance(donnees_scenario, dict) else {}
    blocs = scenario.get("blocs", []) if isinstance(scenario, dict) else []
    evenements: list[dict[str, Any]] = []

    for bloc in blocs:
        if not isinstance(bloc, dict):
            continue
        if bloc.get("actif") is False or bloc.get("statut") == "desactive":
            continue
        compteur = bloc.get("compteur_souhaite")
        if not compteur:
            continue
        duree = bloc.get("duree") if isinstance(bloc.get("duree"), dict) else {}
        quantite = duree.get("valeur", bloc.get("fraction_jour"))
        if not isinstance(quantite, (int, float)) or quantite <= 0:
            continue
        evenements.append(
            {
                "source": "scenario",
                "identifiant": str(bloc.get("identifiant_local", "")),
                "libelle": str(bloc.get("libelle", "")),
                "date_debut": normaliser_date_iso(bloc.get("date_debut"), "bloc.date_debut"),
                "date_fin": normaliser_date_iso(bloc.get("date_fin"), "bloc.date_fin"),
                "unite": str(bloc.get("unite", duree.get("unite", "jours_ouvres"))),
                "quantite": float(quantite),
                "compteur": str(compteur),
                "priorite": int(bloc.get("priorite", 50)),
            }
        )
    return evenements


def construire_evenements_sources(donnees: dict[str, Any], parametres: dict[str, Any]) -> list[dict[str, Any]]:
    ordre_sans_preference = parametres.get("ordre_compteurs_sans_preference", [])
    evenements = construire_evenements_obligations(donnees, ordre_sans_preference)
    evenements.extend(construire_evenements_scenario(donnees))
    return sorted(evenements, key=lambda evenement: (evenement["date_debut"], evenement["priorite"], evenement["identifiant"]))


def jour_est_projectable(jour: date, unite: str) -> bool:
    if unite == "jours_ouvres":
        return jour.weekday() < 5
    if unite == "jours_ouvrables":
        return jour.weekday() < 6
    if unite == "jours_calendaires":
        return True
    return False


def resumer_evenement(evenement: dict[str, Any], quantite_projectee: float) -> dict[str, Any]:
    return {
        "source": evenement["source"],
        "identifiant": evenement["identifiant"],
        "libelle": evenement["libelle"],
        "compteur": evenement["compteur"],
        "quantite_projectee": arrondir_quantite(quantite_projectee),
    }


def ajouter_consommation(demi_journee: dict[str, Any], evenement: dict[str, Any], quantite: float) -> None:
    compteur = evenement["compteur"]
    demi_journee["evenements"].append(resumer_evenement(evenement, quantite))
    consommations = demi_journee["consommations"]
    consommations[compteur] = arrondir_quantite(consommations.get(compteur, 0.0) + quantite)


def projeter_evenement(evenement: dict[str, Any], demi_journees: list[dict[str, Any]], alertes: list[dict[str, Any]]) -> None:
    unite = evenement["unite"]
    quantite_restante = float(evenement["quantite"])

    if unite == "heures":
        alertes.append(
            {
                "type": "unite_non_projectee",
                "identifiant_evenement": evenement["identifiant"],
                "unite": unite,
            }
        )
        return

    debut = convertir_date_iso(evenement["date_debut"], "evenement.date_debut")
    fin = convertir_date_iso(evenement["date_fin"], "evenement.date_fin")

    for demi_journee in demi_journees:
        if quantite_restante <= 0:
            break

        jour = convertir_date_iso(demi_journee["date"], "demi_journee.date")
        if jour < debut or jour > fin:
            continue

        if unite == "demi_journee":
            if jour == debut and demi_journee["portion"] == "matin":
                quantite = min(0.5, quantite_restante)
                ajouter_consommation(demi_journee, evenement, quantite)
            break

        if not jour_est_projectable(jour, unite):
            continue

        quantite = min(0.5, quantite_restante)
        ajouter_consommation(demi_journee, evenement, quantite)
        quantite_restante = arrondir_quantite(quantite_restante - quantite)


def projeter_evenements(evenements: list[dict[str, Any]], demi_journees: list[dict[str, Any]], alertes: list[dict[str, Any]]) -> None:
    for evenement in evenements:
        projeter_evenement(evenement, demi_journees, alertes)


def propager_soldes(demi_journees: list[dict[str, Any]], soldes_initiaux: dict[str, float], alertes: list[dict[str, Any]]) -> None:
    soldes_courants = dict(soldes_initiaux)

    for demi_journee in demi_journees:
        demi_journee["soldes_avant"] = dict(soldes_courants)

        for compteur, quantite_demandee in demi_journee["consommations"].items():
            disponible = float(soldes_courants.get(compteur, 0.0))
            quantite_demandee = float(quantite_demandee)
            identifiants = [
                evenement["identifiant"]
                for evenement in demi_journee["evenements"]
                if evenement.get("compteur") == compteur
            ]

            if disponible >= quantite_demandee:
                soldes_courants[compteur] = arrondir_quantite(disponible - quantite_demandee)
                continue

            quantite_non_couverte = arrondir_quantite(quantite_demandee - disponible)
            alerte = {
                "type": "solde_insuffisant",
                "date": demi_journee["date"],
                "portion": demi_journee["portion"],
                "compteur": compteur,
                "quantite_demandee": arrondir_quantite(quantite_demandee),
                "quantite_disponible": arrondir_quantite(disponible),
                "quantite_non_couverte": quantite_non_couverte,
                "identifiants_evenements": identifiants,
            }
            demi_journee["alertes"].append(alerte)
            alertes.append(alerte)
            soldes_courants[compteur] = 0.0

        demi_journee["soldes_apres"] = dict(soldes_courants)


def extraire_soldes_aux_dates_cibles(
    demi_journees: list[dict[str, Any]],
    dates_cibles: list[Any],
    date_depart: str,
    date_fin: str,
    alertes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    debut = convertir_date_iso(date_depart, "parametres_projection.date_depart")
    fin = convertir_date_iso(date_fin, "parametres_projection.date_fin")
    demi_journees_par_date = {demi_journee["date"]: demi_journee for demi_journee in demi_journees}
    soldes_aux_dates: list[dict[str, Any]] = []

    for cible in dates_cibles:
        if not isinstance(cible, dict):
            continue
        date_cible = convertir_date_iso(cible.get("date"), "date_cible.date")
        if date_cible < debut or date_cible > fin:
            alerte = {
                "type": "date_cible_hors_periode",
                "identifiant": cible.get("identifiant"),
                "date": date_cible.isoformat(),
            }
            alertes.append(alerte)
            soldes_aux_dates.append(
                {
                    "identifiant": cible.get("identifiant"),
                    "libelle": cible.get("libelle"),
                    "date": date_cible.isoformat(),
                    "soldes": None,
                }
            )
            continue

        demi_journee = demi_journees_par_date[date_cible.isoformat()]
        soldes_aux_dates.append(
            {
                "identifiant": cible.get("identifiant"),
                "libelle": cible.get("libelle"),
                "date": date_cible.isoformat(),
                "soldes": demi_journee["soldes_apres"],
            }
        )

    return soldes_aux_dates


def projeter_demi_journees(donnees: dict[str, Any]) -> dict[str, Any]:
    parametres = donnees.get("parametres_projection")
    if not isinstance(parametres, dict):
        raise ValueError("Les paramètres de projection sont obligatoires.")

    date_depart = normaliser_date_iso(parametres.get("date_depart"), "parametres_projection.date_depart")
    date_fin = normaliser_date_iso(parametres.get("date_fin"), "parametres_projection.date_fin")
    if date_depart is None or date_fin is None:
        raise ValueError("La projection exige une date de départ et une date de fin.")

    periode_compteurs = str(parametres.get("periode_compteurs", "courant"))
    soldes_initiaux = extraire_soldes_initiaux(donnees, periode_compteurs)
    demi_journees = creer_vecteur_demi_journees(date_depart, date_fin)
    alertes: list[dict[str, Any]] = []
    evenements_sources = construire_evenements_sources(donnees, parametres)

    projeter_evenements(evenements_sources, demi_journees, alertes)
    propager_soldes(demi_journees, soldes_initiaux, alertes)

    soldes_aux_dates_cibles = extraire_soldes_aux_dates_cibles(
        demi_journees,
        parametres.get("dates_cibles", []),
        date_depart,
        date_fin,
        alertes,
    )

    return {
        "source": SOURCE_SORTIE,
        "periode": {
            "debut": date_depart,
            "fin": date_fin,
        },
        "etat_initial": {
            "date": date_depart,
            "soldes": soldes_initiaux,
        },
        "soldes_initiaux": soldes_initiaux,
        "evenements_sources": evenements_sources,
        "demi_journees": demi_journees,
        "soldes_aux_dates_cibles": soldes_aux_dates_cibles,
        "alertes": alertes,
        "resume": {
            "nombre_demi_journees": len(demi_journees),
            "nombre_evenements_sources": len(evenements_sources),
            "nombre_alertes": len(alertes),
        },
    }


def analyser_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(
        description="Projeter des soldes en demi-journées à partir de données normalisées.",
    )
    analyseur.add_argument("entrees", type=Path, help="Chemin du fichier JSON d'entrées de projection.")
    analyseur.add_argument("--sortie", type=Path, help="Chemin du fichier où écrire la projection.")
    return analyseur.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = analyser_arguments(argv)
    donnees = lire_json(arguments.entrees)
    projection = projeter_demi_journees(donnees)
    texte_json = serialiser_json(projection)
    ecrire_sortie(texte_json, arguments.sortie)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
