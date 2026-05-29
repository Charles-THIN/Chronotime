from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


SOURCE_NORMALISEE = "evenements_compteurs.normalises"
TYPES_AUTORISES = {
    "credit_compteur",
    "ouverture_validite_compteur",
    "expiration_compteur",
    "report_compteur",
    "ajustement_compteur",
    "consommation_absence",
}
UNITES_AUTORISEES = {"jour", "heure", "demi_journee"}


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


def normaliser_date_iso(valeur_brute: Any) -> str:
    if not isinstance(valeur_brute, str) or not valeur_brute.strip():
        raise ValueError(f"Date ISO obligatoire ou invalide : {valeur_brute!r}")

    texte = valeur_brute.strip()
    try:
        date.fromisoformat(texte)
    except ValueError as erreur:
        raise ValueError(f"Date ISO invalide : {valeur_brute!r}") from erreur
    return texte


def normaliser_quantite(valeur_brute: Any, unite_brute: Any) -> tuple[float | None, str | None]:
    if valeur_brute is None:
        return None, None

    if isinstance(valeur_brute, dict):
        unite_brute = valeur_brute.get("unite", unite_brute)
        valeur_brute = valeur_brute.get("valeur")

    try:
        quantite = float(valeur_brute)
    except (TypeError, ValueError) as erreur:
        raise ValueError(f"Quantité invalide : {valeur_brute!r}") from erreur

    if not isinstance(unite_brute, str) or not unite_brute.strip():
        raise ValueError("Une unité est obligatoire quand une quantité est fournie.")
    unite = unite_brute.strip()
    if unite not in UNITES_AUTORISEES:
        raise ValueError(f"Unité invalide : {unite!r}")

    return quantite, unite


def valider_texte_non_vide(evenement: dict[str, Any], champ: str) -> str:
    valeur = evenement.get(champ)
    if not isinstance(valeur, str) or not valeur.strip():
        raise ValueError(f"L'événement doit contenir un champ '{champ}' non vide.")
    return valeur.strip()


def normaliser_evenement(evenement_brut: Any) -> dict[str, Any]:
    if not isinstance(evenement_brut, dict):
        raise ValueError(f"Événement de compteur invalide : {evenement_brut!r}")

    identifiant = valider_texte_non_vide(evenement_brut, "identifiant")
    type_evenement = valider_texte_non_vide(evenement_brut, "type")
    if type_evenement not in TYPES_AUTORISES:
        raise ValueError(f"Type d'événement de compteur inconnu : {type_evenement!r}")

    quantite, unite = normaliser_quantite(evenement_brut.get("quantite"), evenement_brut.get("unite"))

    evenement = {
        "identifiant": identifiant,
        "type": type_evenement,
        "date_effet": normaliser_date_iso(evenement_brut.get("date_effet")),
        "source": str(evenement_brut.get("source") or "").strip(),
        "statut_certitude": str(evenement_brut.get("statut_certitude") or "").strip(),
        "notes": str(evenement_brut.get("notes") or ""),
    }

    if evenement_brut.get("compteur") not in (None, ""):
        evenement["compteur"] = str(evenement_brut["compteur"]).strip()
    if quantite is not None:
        evenement["quantite"] = quantite
        evenement["unite"] = unite

    for champ in ("compteur_source", "periode_source", "compteur_destination", "periode_destination"):
        if evenement_brut.get(champ) not in (None, ""):
            evenement[champ] = str(evenement_brut[champ]).strip()

    return evenement


def variation_resume(evenement: dict[str, Any]) -> dict[str, float]:
    quantite = evenement.get("quantite")
    if not isinstance(quantite, (int, float)):
        return {}

    type_evenement = evenement["type"]
    compteur = evenement.get("compteur")

    if type_evenement == "credit_compteur" and compteur:
        return {str(compteur): float(quantite)}
    if type_evenement == "expiration_compteur" and compteur:
        return {str(compteur): -float(quantite)}
    if type_evenement == "ajustement_compteur" and compteur:
        return {str(compteur): float(quantite)}
    if type_evenement == "consommation_absence" and compteur:
        return {str(compteur): -float(quantite)}
    if type_evenement == "report_compteur":
        variations: dict[str, float] = {}
        compteur_source = evenement.get("compteur_source")
        compteur_destination = evenement.get("compteur_destination")
        if compteur_source:
            variations[str(compteur_source)] = variations.get(str(compteur_source), 0.0) - float(quantite)
        if compteur_destination:
            variations[str(compteur_destination)] = variations.get(str(compteur_destination), 0.0) + float(quantite)
        return variations

    return {}


def construire_resume(evenements: list[dict[str, Any]]) -> dict[str, Any]:
    nombres_par_type: dict[str, int] = {}
    quantites_par_compteur: dict[str, float] = {}

    for evenement in evenements:
        type_evenement = evenement["type"]
        nombres_par_type[type_evenement] = nombres_par_type.get(type_evenement, 0) + 1
        for compteur, variation in variation_resume(evenement).items():
            quantites_par_compteur[compteur] = quantites_par_compteur.get(compteur, 0.0) + variation

    return {
        "nombre_evenements": len(evenements),
        "nombres_par_type": nombres_par_type,
        "quantites_par_compteur": quantites_par_compteur,
    }


def extraire_evenements(donnees_brutes: Any) -> list[Any]:
    if not isinstance(donnees_brutes, dict):
        raise ValueError("Le fichier d'événements de compteur doit contenir un objet JSON.")
    evenements = donnees_brutes.get("evenements_compteurs", donnees_brutes.get("evenements"))
    if not isinstance(evenements, list):
        raise ValueError("Le fichier doit contenir 'evenements_compteurs' ou 'evenements' sous forme de liste.")
    return evenements


def normaliser_evenements_compteurs(donnees_brutes: Any) -> dict[str, Any]:
    evenements = [normaliser_evenement(evenement) for evenement in extraire_evenements(donnees_brutes)]
    return {
        "source": SOURCE_NORMALISEE,
        "evenements": evenements,
        "resume": construire_resume(evenements),
    }


def analyser_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(
        description="Charger et normaliser des événements locaux de compteur.",
    )
    analyseur.add_argument("entree", type=Path, help="Chemin du fichier JSON d'événements de compteur.")
    analyseur.add_argument("--sortie", type=Path, help="Chemin du fichier où écrire les événements normalisés.")
    return analyseur.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = analyser_arguments(argv)
    try:
        donnees_brutes = lire_json(arguments.entree)
        donnees_normalisees = normaliser_evenements_compteurs(donnees_brutes)
    except ValueError as erreur:
        raise SystemExit(str(erreur)) from erreur
    ecrire_sortie(serialiser_json(donnees_normalisees), arguments.sortie)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
