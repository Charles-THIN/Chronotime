from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from outils.chronotime.chargeur_obligations import normaliser_obligations


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


def convertir_date_iso(valeur: Any, nom_champ: str) -> date:
    if not isinstance(valeur, str):
        raise ValueError(f"Date ISO obligatoire pour {nom_champ} : {valeur!r}")
    try:
        return date.fromisoformat(valeur)
    except ValueError as erreur:
        raise ValueError(f"Date ISO invalide pour {nom_champ} : {valeur!r}") from erreur


def valider_agenda_normalise(agenda: Any) -> dict[str, Any]:
    if not isinstance(agenda, dict):
        raise ValueError("L'agenda normalisé doit être un objet JSON.")
    if agenda.get("source") != "chronotime.agenda":
        raise ValueError("L'agenda doit être déjà normalisé avec la source 'chronotime.agenda'.")
    if not isinstance(agenda.get("evenements"), list):
        raise ValueError("L'agenda normalisé doit contenir une liste 'evenements'.")
    return agenda


def evenement_est_compatible(obligation: dict[str, Any], evenement: dict[str, Any]) -> bool:
    if evenement.get("categorie") != "absence":
        return False
    if str(evenement.get("code")) not in obligation["compteurs_autorises"]:
        return False

    date_evenement = convertir_date_iso(evenement.get("date"), "evenement.date")
    date_debut = convertir_date_iso(obligation.get("date_debut"), "obligation.date_debut")
    date_fin = convertir_date_iso(obligation.get("date_fin"), "obligation.date_fin")
    return date_debut <= date_evenement <= date_fin


def calculer_fraction_evenement(evenement: dict[str, Any]) -> float:
    unite = evenement.get("unite")
    if isinstance(unite, dict):
        fraction_jour = unite.get("fraction_jour")
        if isinstance(fraction_jour, (int, float)):
            return float(fraction_jour)

        code_unite = unite.get("code")
        if code_unite in {"J", "D"}:
            return 1.0
    return 0.0


def normaliser_evenement_compatible(evenement: dict[str, Any], fraction_utilisee: float) -> dict[str, Any]:
    unite = evenement.get("unite") if isinstance(evenement.get("unite"), dict) else {}
    statut = evenement.get("statut") if isinstance(evenement.get("statut"), dict) else None
    return {
        "date": evenement.get("date"),
        "code": evenement.get("code"),
        "libelle": evenement.get("libelle"),
        "unite": unite,
        "fraction_utilisee": fraction_utilisee,
        "statut": statut,
    }


def verifier_obligation(obligation: dict[str, Any], evenements: list[dict[str, Any]]) -> dict[str, Any]:
    quantite_requise = float(obligation["quantite"])
    quantite_satisfaite = 0.0
    evenements_compatibles = []

    for evenement in evenements:
        if not isinstance(evenement, dict):
            continue
        if not evenement_est_compatible(obligation, evenement):
            continue

        fraction_utilisee = calculer_fraction_evenement(evenement)
        if fraction_utilisee <= 0:
            continue

        quantite_satisfaite += fraction_utilisee
        evenements_compatibles.append(normaliser_evenement_compatible(evenement, fraction_utilisee))

    quantite_satisfaite = min(quantite_satisfaite, quantite_requise)
    quantite_restante = max(quantite_requise - quantite_satisfaite, 0.0)

    if quantite_satisfaite >= quantite_requise:
        statut_obligation = "satisfaite"
    elif quantite_satisfaite > 0:
        statut_obligation = "partielle"
    else:
        statut_obligation = "a_poser"

    return {
        "identifiant": obligation["identifiant"],
        "libelle": obligation["libelle"],
        "statut_obligation": statut_obligation,
        "quantite_requise": quantite_requise,
        "quantite_satisfaite": quantite_satisfaite,
        "quantite_restante": quantite_restante,
        "compteurs_autorises": obligation["compteurs_autorises"],
        "evenements_compatibles": evenements_compatibles,
    }


def construire_resume(verifications: list[dict[str, Any]]) -> dict[str, Any]:
    quantite_totale_requise = sum(verification["quantite_requise"] for verification in verifications)
    quantite_totale_satisfaite = sum(verification["quantite_satisfaite"] for verification in verifications)
    quantite_totale_restante = sum(verification["quantite_restante"] for verification in verifications)

    return {
        "nombre_obligations": len(verifications),
        "nombre_satisfaites": sum(1 for verification in verifications if verification["statut_obligation"] == "satisfaite"),
        "nombre_partielles": sum(1 for verification in verifications if verification["statut_obligation"] == "partielle"),
        "nombre_a_poser": sum(1 for verification in verifications if verification["statut_obligation"] == "a_poser"),
        "quantite_totale_requise": quantite_totale_requise,
        "quantite_totale_satisfaite": quantite_totale_satisfaite,
        "quantite_totale_restante": quantite_totale_restante,
    }


def verifier_obligations(donnees_obligations: Any, donnees_agenda: Any) -> dict[str, Any]:
    obligations_normalisees = normaliser_obligations(donnees_obligations)
    agenda = valider_agenda_normalise(donnees_agenda)
    evenements = agenda["evenements"]
    verifications = [verifier_obligation(obligation, evenements) for obligation in obligations_normalisees["obligations"]]

    return {
        "source": "verification.obligations",
        "obligations": verifications,
        "resume": construire_resume(verifications),
    }


def analyser_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(
        description="Vérifier des obligations locales avec un agenda Chronotime normalisé.",
    )
    analyseur.add_argument("obligations", type=Path, help="Chemin du fichier JSON d'obligations locales.")
    analyseur.add_argument("agenda", type=Path, help="Chemin du fichier JSON d'agenda normalisé.")
    analyseur.add_argument("--sortie", type=Path, help="Chemin du fichier où écrire la vérification.")
    return analyseur.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = analyser_arguments(argv)
    donnees_obligations = lire_json(arguments.obligations)
    donnees_agenda = lire_json(arguments.agenda)
    verification = verifier_obligations(donnees_obligations, donnees_agenda)
    texte_json = serialiser_json(verification)
    ecrire_sortie(texte_json, arguments.sortie)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
