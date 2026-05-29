from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SOURCE_PROJECTION = "projection.demi_journees"
SOURCE_SORTIE = "mouvements.soldes"


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
        chemin_sortie.parent.mkdir(parents=True, exist_ok=True)
        chemin_sortie.write_text(f"{texte_json}\n", encoding="utf-8")
    except OSError as erreur:
        raise SystemExit(f"Impossible d'écrire le fichier de sortie : {chemin_sortie}") from erreur


def nombre_strictement_positif(valeur: Any) -> float | None:
    if not isinstance(valeur, (int, float)):
        return None
    nombre = float(valeur)
    if nombre <= 0:
        return None
    return nombre


def texte_non_vide(valeur: Any) -> str | None:
    if valeur is None:
        return None
    texte = str(valeur).strip()
    return texte or None


def ordre_portion(portion: Any) -> int:
    if portion == "matin":
        return 10
    if portion == "apres_midi":
        return 20
    return 99


def mouvement_consommation(demi_journee: dict[str, Any], consommation: dict[str, Any]) -> dict[str, Any] | None:
    quantite_appliquee = nombre_strictement_positif(consommation.get("quantite_appliquee"))
    if quantite_appliquee is None:
        return None

    compteur = texte_non_vide(consommation.get("compteur"))
    identifiant = texte_non_vide(consommation.get("identifiant_evenement"))
    if compteur is None or identifiant is None:
        return None

    return {
        "date": demi_journee.get("date"),
        "portion": demi_journee.get("portion"),
        "ordre": ordre_portion(demi_journee.get("portion")),
        "origine": "consommation_projection",
        "type": "consommation_absence",
        "identifiant": identifiant,
        "compteur": compteur,
        "variation": -quantite_appliquee,
        "unite": "jour",
        "details": {
            "quantite_demandee": consommation.get("quantite_demandee"),
            "quantite_appliquee": quantite_appliquee,
            "quantite_non_couverte": consommation.get("quantite_non_couverte"),
            "source": consommation.get("source"),
            "priorite": consommation.get("priorite"),
        },
    }


def extraire_mouvements_consommations(projection: dict[str, Any]) -> list[dict[str, Any]]:
    mouvements: list[dict[str, Any]] = []
    for demi_journee in projection.get("demi_journees", []):
        if not isinstance(demi_journee, dict):
            continue
        for consommation in demi_journee.get("consommations_detaillees", []):
            if not isinstance(consommation, dict):
                continue
            mouvement = mouvement_consommation(demi_journee, consommation)
            if mouvement is not None:
                mouvements.append(mouvement)
    return mouvements


def mouvement_evenement_compteur(
    evenement: dict[str, Any],
    variation: float,
    compteur: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "date": evenement.get("date_effet"),
        "ordre": 0,
        "origine": "evenement_compteur",
        "type": evenement.get("type"),
        "identifiant": evenement.get("identifiant"),
        "compteur": compteur,
        "variation": variation,
        "unite": evenement.get("unite"),
        "details": details or {},
    }


def champs_report_manquants(evenement: dict[str, Any]) -> list[str]:
    champs = ("compteur_source", "compteur_destination", "periode_source", "periode_destination")
    return [champ for champ in champs if texte_non_vide(evenement.get(champ)) is None]


def extraire_mouvements_evenements_compteurs(
    projection: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    mouvements: list[dict[str, Any]] = []
    evenements_informatifs: list[dict[str, Any]] = []
    alertes: list[dict[str, Any]] = []

    evenements = projection.get("evenements_compteurs", {}).get("evenements", [])
    for evenement in evenements:
        if not isinstance(evenement, dict):
            continue

        type_evenement = evenement.get("type")
        quantite = evenement.get("quantite")
        compteur = texte_non_vide(evenement.get("compteur"))
        quantite_numerique = float(quantite) if isinstance(quantite, (int, float)) else None

        if type_evenement == "credit_compteur" and quantite_numerique is not None and compteur:
            mouvements.append(mouvement_evenement_compteur(evenement, quantite_numerique, compteur))
        elif type_evenement == "expiration_compteur" and quantite_numerique is not None and compteur:
            mouvements.append(mouvement_evenement_compteur(evenement, -quantite_numerique, compteur))
        elif type_evenement == "ajustement_compteur" and quantite_numerique is not None and compteur:
            mouvements.append(mouvement_evenement_compteur(evenement, quantite_numerique, compteur))
        elif type_evenement == "consommation_absence" and quantite_numerique is not None and compteur:
            mouvements.append(mouvement_evenement_compteur(evenement, -quantite_numerique, compteur))
            alertes.append(
                {
                    "type": "consommation_absence_evenement_compteur_non_dedoublonnee",
                    "severite": "information",
                    "identifiant": evenement.get("identifiant"),
                }
            )
        elif type_evenement == "ouverture_validite_compteur":
            evenements_informatifs.append(evenement)
        elif type_evenement == "report_compteur":
            if evenement.get("mode_report") != "operationnel":
                evenements_informatifs.append(evenement)
                continue

            manquants = champs_report_manquants(evenement)
            if manquants:
                alertes.append(
                    {
                        "type": "report_operationnel_incomplet",
                        "severite": "bloquant",
                        "identifiant": evenement.get("identifiant"),
                        "champs_manquants": manquants,
                    }
                )
                continue

            if quantite_numerique is None:
                continue
            compteur_source = str(evenement["compteur_source"])
            compteur_destination = str(evenement["compteur_destination"])
            details_communs = {
                "periode_source": evenement.get("periode_source"),
                "periode_destination": evenement.get("periode_destination"),
            }
            mouvements.append(
                mouvement_evenement_compteur(
                    evenement,
                    -quantite_numerique,
                    compteur_source,
                    {**details_communs, "role_report": "source"},
                )
            )
            mouvements.append(
                mouvement_evenement_compteur(
                    evenement,
                    quantite_numerique,
                    compteur_destination,
                    {**details_communs, "role_report": "destination"},
                )
            )

    return mouvements, evenements_informatifs, alertes


def trier_mouvements(mouvements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        mouvements,
        key=lambda mouvement: (
            str(mouvement.get("date") or ""),
            int(mouvement.get("ordre") or 0),
            str(mouvement.get("origine") or ""),
            str(mouvement.get("type") or ""),
            str(mouvement.get("identifiant") or ""),
            str(mouvement.get("compteur") or ""),
        ),
    )


def generer_mouvements_soldes(projection: Any) -> dict[str, Any]:
    if not isinstance(projection, dict):
        raise ValueError("La projection doit être un objet JSON.")
    if projection.get("source") != SOURCE_PROJECTION:
        raise ValueError("La source attendue est 'projection.demi_journees'.")

    mouvements = extraire_mouvements_consommations(projection)
    mouvements_evenements, evenements_informatifs, alertes = extraire_mouvements_evenements_compteurs(projection)
    mouvements.extend(mouvements_evenements)
    mouvements = trier_mouvements(mouvements)

    return {
        "source": SOURCE_SORTIE,
        "periode": projection.get("periode", {}),
        "mouvements": mouvements,
        "evenements_informatifs": evenements_informatifs,
        "alertes": alertes,
        "resume": {
            "nombre_mouvements": len(mouvements),
            "nombre_evenements_informatifs": len(evenements_informatifs),
            "nombre_alertes": len(alertes),
        },
    }


def analyser_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(
        description="Générer des mouvements de solde depuis une projection demi-journalière.",
    )
    analyseur.add_argument("projection", type=Path, help="Chemin du fichier JSON projection.demi_journees.")
    analyseur.add_argument("--sortie", type=Path, help="Chemin du fichier où écrire les mouvements de solde.")
    return analyseur.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = analyser_arguments(argv)
    try:
        projection = lire_json(arguments.projection)
        mouvements = generer_mouvements_soldes(projection)
    except ValueError as erreur:
        raise SystemExit(str(erreur)) from erreur
    ecrire_sortie(serialiser_json(mouvements), arguments.sortie)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
