from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

SOURCE_ATTENDUE = "obligations.locales"


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


def normaliser_date_iso(valeur_brute: Any) -> str | None:
    if valeur_brute is None:
        return None
    if not isinstance(valeur_brute, str):
        raise ValueError(f"Date ISO invalide : {valeur_brute!r}")

    texte = valeur_brute.strip()
    try:
        date.fromisoformat(texte)
    except ValueError as erreur:
        raise ValueError(f"Date ISO invalide : {valeur_brute!r}") from erreur
    return texte


def normaliser_nombre(valeur: Any, nom_champ: str) -> float:
    try:
        return float(valeur)
    except (TypeError, ValueError) as erreur:
        raise ValueError(f"Nombre invalide pour {nom_champ} : {valeur!r}") from erreur


def normaliser_entier(valeur: Any, defaut: int) -> int:
    if valeur is None:
        return defaut
    try:
        return int(valeur)
    except (TypeError, ValueError) as erreur:
        raise ValueError(f"Entier invalide : {valeur!r}") from erreur


def valider_obligation_minimale(obligation: Any) -> dict[str, Any]:
    if not isinstance(obligation, dict):
        raise ValueError(f"Obligation invalide : {obligation!r}")

    champs_obligatoires = (
        "identifiant",
        "date_debut",
        "date_fin",
        "unite",
        "quantite",
        "statut",
    )
    for champ in champs_obligatoires:
        if champ not in obligation or obligation.get(champ) in ("", None):
            raise ValueError(f"L'obligation doit contenir le champ '{champ}'.")

    compteurs = obligation.get("compteurs_autorises")
    if not isinstance(compteurs, list) or len(compteurs) == 0:
        raise ValueError("L'obligation doit contenir 'compteurs_autorises' sous forme de liste non vide.")

    return obligation


def valider_obligations_minimales(donnees_brutes: Any) -> dict[str, Any]:
    if not isinstance(donnees_brutes, dict):
        raise ValueError("Le fichier d'obligations doit contenir un objet JSON.")
    if not donnees_brutes.get("source"):
        raise ValueError("Le fichier d'obligations doit contenir 'source'.")
    if "annee" not in donnees_brutes:
        raise ValueError("Le fichier d'obligations doit contenir 'annee'.")
    if not isinstance(donnees_brutes.get("obligations"), list):
        raise ValueError("Le fichier d'obligations doit contenir 'obligations' sous forme de liste.")
    return donnees_brutes


def normaliser_obligation(obligation_brute: Any) -> dict[str, Any]:
    obligation = valider_obligation_minimale(obligation_brute)
    unite = str(obligation["unite"])
    quantite = normaliser_nombre(obligation["quantite"], "quantite")

    return {
        "identifiant": str(obligation["identifiant"]),
        "libelle": str(obligation.get("libelle") or "").strip(),
        "type": str(obligation.get("type") or "").strip(),
        "date_debut": normaliser_date_iso(obligation["date_debut"]),
        "date_fin": normaliser_date_iso(obligation["date_fin"]),
        "unite": unite,
        "quantite": quantite,
        "compteurs_autorises": [str(compteur) for compteur in obligation["compteurs_autorises"]],
        "compteur_prefere": obligation.get("compteur_prefere"),
        "statut": str(obligation["statut"]),
        "verrouillage": bool(obligation.get("verrouillage", False)),
        "priorite": normaliser_entier(obligation.get("priorite"), 50),
        "notes": str(obligation.get("notes") or ""),
        "duree_calculee": {
            "unite": unite,
            "valeur": quantite,
            "methode": "quantite_declaree",
        },
    }


def construire_resume(obligations: list[dict[str, Any]]) -> dict[str, Any]:
    quantite_totale = sum(obligation["quantite"] for obligation in obligations)
    quantites_par_compteur_prefere: dict[str, float] = {}

    for obligation in obligations:
        cle = obligation["compteur_prefere"] or "sans_preference"
        quantites_par_compteur_prefere[cle] = quantites_par_compteur_prefere.get(cle, 0.0) + obligation["quantite"]

    return {
        "nombre_obligations": len(obligations),
        "quantite_totale": quantite_totale,
        "quantites_par_compteur_prefere": quantites_par_compteur_prefere,
    }


def normaliser_obligations(donnees_brutes: Any) -> dict[str, Any]:
    donnees = valider_obligations_minimales(donnees_brutes)
    obligations = [normaliser_obligation(obligation) for obligation in donnees["obligations"]]

    return {
        "source": str(donnees["source"]),
        "annee": int(donnees["annee"]),
        "perimetre": donnees.get("perimetre") if isinstance(donnees.get("perimetre"), dict) else {},
        "obligations": obligations,
        "resume": construire_resume(obligations),
    }


def analyser_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(
        description="Charger et normaliser des obligations locales de congés.",
    )
    analyseur.add_argument("entree", type=Path, help="Chemin du fichier JSON d'obligations locales.")
    analyseur.add_argument("--sortie", type=Path, help="Chemin du fichier où écrire les obligations normalisées.")
    return analyseur.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = analyser_arguments(argv)
    donnees_brutes = lire_json(arguments.entree)
    obligations_normalisees = normaliser_obligations(donnees_brutes)
    texte_json = serialiser_json(obligations_normalisees)
    ecrire_sortie(texte_json, arguments.sortie)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
