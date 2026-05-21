from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

MODELE_SOURCE = "chronotime.soldeabs"

MODELE_JOUR = re.compile(r"^(?P<jours>\d+)j(?P<centiemes>\d{2})$")
MODELE_HEURE = re.compile(r"^(?P<heures>\d+)h(?P<minutes>\d{2})m$")


def analyser_quantite_chronotime(valeur_brute: Any) -> dict[str, Any] | None:
    if valeur_brute is None:
        return None
    if not isinstance(valeur_brute, str):
        raise ValueError(f"Quantité Chronotime non reconnue : {valeur_brute!r}")

    valeur_brute = valeur_brute.strip()

    correspondance_jour = MODELE_JOUR.fullmatch(valeur_brute)
    if correspondance_jour is not None:
        jours = int(correspondance_jour.group("jours"))
        centiemes = int(correspondance_jour.group("centiemes"))
        return {
            "brut": valeur_brute,
            "unite": "jour",
            "valeur": jours + centiemes / 100.0,
        }

    correspondance_heure = MODELE_HEURE.fullmatch(valeur_brute)
    if correspondance_heure is not None:
        heures = int(correspondance_heure.group("heures"))
        minutes = int(correspondance_heure.group("minutes"))
        return {
            "brut": valeur_brute,
            "unite": "heure",
            "valeur": heures + minutes / 60.0,
        }

    raise ValueError(f"Format Chronotime non reconnu : {valeur_brute!r}")


def normaliser_periode(periode_brute: Any) -> dict[str, Any] | None:
    if periode_brute is None:
        return None
    if not isinstance(periode_brute, dict):
        raise ValueError(f"Période Chronotime non reconnue : {periode_brute!r}")

    return {
        "droit": analyser_quantite_chronotime(periode_brute.get("droit")),
        "pris": analyser_quantite_chronotime(periode_brute.get("pris")),
        "solde": analyser_quantite_chronotime(periode_brute.get("solde")),
    }


def nettoyer_libelle(libelle_brut: Any) -> str:
    if libelle_brut is None:
        return ""
    if not isinstance(libelle_brut, str):
        return str(libelle_brut).strip()
    return libelle_brut.strip()


def normaliser_compteur(compteur_brut: Any) -> dict[str, Any]:
    if not isinstance(compteur_brut, dict):
        raise ValueError(f"Compteur Chronotime non reconnu : {compteur_brut!r}")

    return {
        "code": compteur_brut.get("code"),
        "libelle": nettoyer_libelle(compteur_brut.get("libelle")),
        "periodes": {
            "precedent": normaliser_periode(compteur_brut.get("precedent")),
            "courant": normaliser_periode(compteur_brut.get("courant")),
            "suivant": normaliser_periode(compteur_brut.get("suivant")),
        },
    }


def normaliser_compteurs(compteurs_bruts: Any) -> list[dict[str, Any]]:
    if not isinstance(compteurs_bruts, list):
        raise ValueError("La réponse Chronotime doit contenir une liste de compteurs.")
    return [normaliser_compteur(compteur_brut) for compteur_brut in compteurs_bruts]


def extraire_compteurs(donnees_brutes: Any) -> list[dict[str, Any]]:
    if isinstance(donnees_brutes, dict):
        if "compteurs" in donnees_brutes:
            return normaliser_compteurs(donnees_brutes["compteurs"])
        raise ValueError("Le document JSON doit contenir la clé 'compteurs' ou être une liste.")
    return normaliser_compteurs(donnees_brutes)


def normaliser_donnees(donnees_brutes: Any) -> dict[str, Any]:
    return {
        "source": MODELE_SOURCE,
        "compteurs": extraire_compteurs(donnees_brutes),
    }


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


def analyser_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(
        description="Normaliser une réponse Chronotime soldeabs depuis un fichier local.",
    )
    analyseur.add_argument(
        "entree",
        type=Path,
        help="Chemin du fichier JSON Chronotime local à normaliser.",
    )
    analyseur.add_argument(
        "--sortie",
        type=Path,
        help="Chemin du fichier où écrire le JSON normalisé.",
    )
    return analyseur.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = analyser_arguments(argv)
    donnees_brutes = lire_json(arguments.entree)
    donnees_normalisees = normaliser_donnees(donnees_brutes)
    texte_json = serialiser_json(donnees_normalisees)
    ecrire_sortie(texte_json, arguments.sortie)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
