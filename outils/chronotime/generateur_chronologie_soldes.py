from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


SOURCE_PROJECTION = "projection.demi_journees"
SOURCE_MOUVEMENTS = "mouvements.soldes"
SOURCE_SORTIE = "chronologie.soldes"


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


def nombre_ou_none(valeur: Any) -> float | None:
    if isinstance(valeur, bool) or not isinstance(valeur, (int, float)):
        return None
    return float(valeur)


def texte_non_vide(valeur: Any) -> str | None:
    if valeur is None:
        return None
    texte = str(valeur).strip()
    return texte or None


def arrondir(valeur: float) -> float:
    return round(float(valeur), 10)


def copier_soldes(soldes: dict[str, float]) -> dict[str, float]:
    return {compteur: arrondir(valeur) for compteur, valeur in soldes.items()}


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


def valider_sources(projection: Any, mouvements: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(projection, dict):
        raise ValueError("La projection doit être un objet JSON.")
    if projection.get("source") != SOURCE_PROJECTION:
        raise ValueError("La source de projection attendue est 'projection.demi_journees'.")
    if not isinstance(mouvements, dict):
        raise ValueError("Les mouvements doivent être un objet JSON.")
    if mouvements.get("source") != SOURCE_MOUVEMENTS:
        raise ValueError("La source de mouvements attendue est 'mouvements.soldes'.")
    return projection, mouvements


def extraire_soldes_initiaux(projection: dict[str, Any]) -> dict[str, float]:
    soldes_initiaux: dict[str, float] = {}
    for compteur, valeur in projection.get("soldes_initiaux", {}).items():
        valeur_numerique = nombre_ou_none(valeur)
        if valeur_numerique is not None:
            soldes_initiaux[str(compteur)] = arrondir(valeur_numerique)
    return soldes_initiaux


def alerte_mouvement_invalide(mouvement: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "mouvement_invalide_ignore",
        "severite": "information",
        "identifiant": mouvement.get("identifiant"),
        "raison": "compteur_ou_variation_invalide",
    }


def creer_point_chronologie(
    mouvement: dict[str, Any],
    compteur: str,
    variation: float,
    soldes_avant: dict[str, float],
    soldes_apres: dict[str, float],
) -> dict[str, Any]:
    point = {
        "date": mouvement.get("date"),
        "ordre": mouvement.get("ordre"),
        "origine": mouvement.get("origine"),
        "type": mouvement.get("type"),
        "identifiant": mouvement.get("identifiant"),
        "compteur": compteur,
        "variation": arrondir(variation),
        "soldes_avant": soldes_avant,
        "soldes_apres": soldes_apres,
        "details": copy.deepcopy(mouvement.get("details", {})),
    }
    if "portion" in mouvement:
        point["portion"] = mouvement.get("portion")
    return point


def generer_chronologie_soldes(projection_brute: Any, mouvements_bruts: Any) -> dict[str, Any]:
    projection, mouvements_source = valider_sources(projection_brute, mouvements_bruts)

    soldes_courants = extraire_soldes_initiaux(projection)
    soldes_initiaux = copier_soldes(soldes_courants)
    alertes = list(copy.deepcopy(mouvements_source.get("alertes", [])))
    compteurs_absents_signales: set[str] = set()
    points_chronologie: list[dict[str, Any]] = []

    mouvements = [mouvement for mouvement in mouvements_source.get("mouvements", []) if isinstance(mouvement, dict)]
    for mouvement in trier_mouvements(mouvements):
        compteur = texte_non_vide(mouvement.get("compteur"))
        variation = nombre_ou_none(mouvement.get("variation"))
        if compteur is None or variation is None:
            alertes.append(alerte_mouvement_invalide(mouvement))
            continue

        if compteur not in soldes_courants:
            soldes_courants[compteur] = 0.0
            if compteur not in compteurs_absents_signales:
                alertes.append(
                    {
                        "type": "compteur_absent_des_soldes_initiaux",
                        "severite": "information",
                        "compteur": compteur,
                    }
                )
                compteurs_absents_signales.add(compteur)

        soldes_avant = copier_soldes(soldes_courants)
        soldes_courants[compteur] = arrondir(soldes_courants[compteur] + variation)
        soldes_apres = copier_soldes(soldes_courants)
        points_chronologie.append(creer_point_chronologie(mouvement, compteur, variation, soldes_avant, soldes_apres))

    return {
        "source": SOURCE_SORTIE,
        "periode": projection.get("periode", {}),
        "soldes_initiaux": soldes_initiaux,
        "points_chronologie": points_chronologie,
        "soldes_finaux": copier_soldes(soldes_courants),
        "alertes": alertes,
        "resume": {
            "nombre_mouvements": len(mouvements_source.get("mouvements", [])),
            "nombre_points_chronologie": len(points_chronologie),
            "nombre_alertes": len(alertes),
        },
    }


def analyser_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(
        description="Générer une chronologie cumulée des soldes depuis une projection et des mouvements.",
    )
    analyseur.add_argument("--projection", required=True, type=Path, help="Fichier JSON projection.demi_journees.")
    analyseur.add_argument("--mouvements", required=True, type=Path, help="Fichier JSON mouvements.soldes.")
    analyseur.add_argument("--sortie", type=Path, help="Chemin du fichier où écrire la chronologie.")
    return analyseur.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = analyser_arguments(argv)
    try:
        projection = lire_json(arguments.projection)
        mouvements = lire_json(arguments.mouvements)
        chronologie = generer_chronologie_soldes(projection, mouvements)
    except ValueError as erreur:
        raise SystemExit(str(erreur)) from erreur
    ecrire_sortie(serialiser_json(chronologie), arguments.sortie)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
