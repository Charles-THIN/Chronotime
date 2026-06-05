from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

SOURCE_PAR_DEFAUT = "simulation.locale"


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


def convertir_date_iso(valeur: str | None, nom_champ: str) -> date:
    if valeur is None:
        raise ValueError(f"Le champ {nom_champ} est obligatoire pour calculer une durée.")
    try:
        return date.fromisoformat(valeur)
    except ValueError as erreur:
        raise ValueError(f"Date ISO invalide pour {nom_champ} : {valeur!r}") from erreur


def valider_scenario_minimal(donnees_brutes: Any) -> dict[str, Any]:
    if not isinstance(donnees_brutes, dict):
        raise ValueError("Le fichier de scénario doit contenir un objet JSON.")

    scenario = donnees_brutes.get("scenario")
    if not isinstance(scenario, dict):
        raise ValueError("Le fichier doit contenir la clé 'scenario'.")
    if not scenario.get("identifiant"):
        raise ValueError("Le scénario doit contenir 'scenario.identifiant'.")

    periode = scenario.get("periode")
    if not isinstance(periode, dict):
        raise ValueError("Le scénario doit contenir 'scenario.periode'.")
    if not periode.get("debut"):
        raise ValueError("Le scénario doit contenir 'scenario.periode.debut'.")
    if not periode.get("fin"):
        raise ValueError("Le scénario doit contenir 'scenario.periode.fin'.")
    if not isinstance(scenario.get("blocs"), list):
        raise ValueError("Le scénario doit contenir 'scenario.blocs' sous forme de liste.")

    return scenario


def calculer_duree(date_debut: str | None, date_fin: str | None, unite: str, fraction_jour: float | None) -> dict[str, Any]:
    if unite == "heures":
        return {"unite": unite, "valeur": None, "methode": "non_calcule"}
    if unite == "demi_journee":
        return {"unite": unite, "valeur": fraction_jour, "methode": "fraction_jour"}

    debut = convertir_date_iso(date_debut, "date_debut")
    fin = convertir_date_iso(date_fin, "date_fin")
    if fin < debut:
        raise ValueError("La date de fin d'un bloc ne peut pas précéder sa date de début.")

    jours = []
    courant = debut
    while courant <= fin:
        jours.append(courant)
        courant += timedelta(days=1)

    if unite == "jours_calendaires":
        return {"unite": unite, "valeur": float(len(jours)), "methode": "jours_inclus"}
    if unite == "jours_ouvres":
        valeur = sum(1 for jour in jours if jour.weekday() < 5)
        return {"unite": unite, "valeur": float(valeur), "methode": "jours_lundi_a_vendredi"}
    if unite == "jours_ouvrables":
        valeur = sum(1 for jour in jours if jour.weekday() < 6)
        return {"unite": unite, "valeur": float(valeur), "methode": "jours_lundi_a_samedi"}

    return {"unite": unite, "valeur": None, "methode": "unite_non_reconnue"}


def bloc_est_actif(type_bloc: str, statut: str) -> bool:
    if statut == "desactive":
        return False
    return type_bloc not in {"bloc_ignore", "bloc_desactive"}


def normaliser_nombre(valeur: Any, defaut: float) -> float:
    if valeur is None:
        return defaut
    try:
        return float(valeur)
    except (TypeError, ValueError) as erreur:
        raise ValueError(f"Nombre invalide : {valeur!r}") from erreur


def normaliser_entier(valeur: Any, defaut: int) -> int:
    if valeur is None:
        return defaut
    try:
        return int(valeur)
    except (TypeError, ValueError) as erreur:
        raise ValueError(f"Entier invalide : {valeur!r}") from erreur


def normaliser_choix_compteur(bloc_brut: dict[str, Any]) -> dict[str, Any] | None:
    choix_brut = bloc_brut.get("choix_compteur")
    if isinstance(choix_brut, dict):
        mode = str(choix_brut.get("mode") or "").strip().lower()
        if mode == "auto":
            return {"mode": "auto", "compteur": None}
        if mode == "manuel":
            compteur = choix_brut.get("compteur")
            if not isinstance(compteur, str) or not compteur.strip():
                raise ValueError("Le choix_compteur manuel exige un compteur non vide.")
            return {"mode": "manuel", "compteur": compteur.strip()}
        raise ValueError(f"Mode de choix_compteur invalide : {mode!r}")

    compteur_souhaite = bloc_brut.get("compteur_souhaite")
    if isinstance(compteur_souhaite, str) and compteur_souhaite.strip():
        return {"mode": "manuel", "compteur": compteur_souhaite.strip()}

    return None


def normaliser_bloc(bloc_brut: Any) -> dict[str, Any]:
    if not isinstance(bloc_brut, dict):
        raise ValueError(f"Bloc de scénario invalide : {bloc_brut!r}")

    type_bloc = str(bloc_brut.get("type") or "")
    statut = str(bloc_brut.get("statut") or "")
    unite = str(bloc_brut.get("unite") or "")
    fraction_jour = normaliser_nombre(bloc_brut.get("fraction_jour"), 1.0)
    date_debut = normaliser_date_iso(bloc_brut.get("date_debut"))
    date_fin = normaliser_date_iso(bloc_brut.get("date_fin"))
    date_limite = normaliser_date_iso(bloc_brut.get("date_limite"))
    choix_compteur = normaliser_choix_compteur(bloc_brut)

    return {
        "identifiant_local": str(bloc_brut.get("identifiant_local") or ""),
        "libelle": str(bloc_brut.get("libelle") or "").strip(),
        "type": type_bloc,
        "source": str(bloc_brut.get("source") or SOURCE_PAR_DEFAUT),
        "origine_bloc": str(bloc_brut.get("origine_bloc") or "").strip(),
        "date_debut": date_debut,
        "date_fin": date_fin,
        "unite": unite,
        "fraction_jour": fraction_jour,
        "choix_compteur": choix_compteur,
        "compteur_souhaite": bloc_brut.get("compteur_souhaite"),
        "compteur_reellement_consomme": bloc_brut.get("compteur_reellement_consomme"),
        "statut": statut,
        "verrouillage": bool(bloc_brut.get("verrouillage", False)),
        "priorite": normaliser_entier(bloc_brut.get("priorite"), 50),
        "date_limite": date_limite,
        "notes_locales": str(bloc_brut.get("notes_locales") or ""),
        "actif": bloc_est_actif(type_bloc, statut),
        "duree": calculer_duree(date_debut, date_fin, unite, fraction_jour),
    }


def normaliser_date_cible(date_cible_brute: Any) -> dict[str, Any]:
    if not isinstance(date_cible_brute, dict):
        raise ValueError(f"Date cible invalide : {date_cible_brute!r}")
    return {
        "identifiant": str(date_cible_brute.get("identifiant") or ""),
        "libelle": str(date_cible_brute.get("libelle") or "").strip(),
        "date": normaliser_date_iso(date_cible_brute.get("date")),
    }


def normaliser_scenario(donnees_brutes: Any) -> dict[str, Any]:
    scenario = valider_scenario_minimal(donnees_brutes)
    periode = scenario["periode"]
    blocs = [normaliser_bloc(bloc) for bloc in scenario["blocs"]]
    nombre_blocs_actifs = sum(1 for bloc in blocs if bloc["actif"])

    return {
        "source": donnees_brutes.get("source") or SOURCE_PAR_DEFAUT,
        "scenario": {
            "identifiant": str(scenario.get("identifiant")),
            "libelle": str(scenario.get("libelle") or "").strip(),
            "periode": {
                "debut": normaliser_date_iso(periode.get("debut")),
                "fin": normaliser_date_iso(periode.get("fin")),
            },
            "dates_cibles": [normaliser_date_cible(date_cible) for date_cible in scenario.get("dates_cibles", [])],
            "preferences": scenario.get("preferences") if isinstance(scenario.get("preferences"), dict) else {},
            "blocs": blocs,
        },
        "resume": {
            "nombre_blocs": len(blocs),
            "nombre_blocs_actifs": nombre_blocs_actifs,
            "nombre_blocs_inactifs": len(blocs) - nombre_blocs_actifs,
        },
    }


def analyser_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(
        description="Charger et normaliser un scénario local de simulation.",
    )
    analyseur.add_argument("entree", type=Path, help="Chemin du fichier JSON de scénario local.")
    analyseur.add_argument("--sortie", type=Path, help="Chemin du fichier où écrire le scénario normalisé.")
    return analyseur.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = analyser_arguments(argv)
    donnees_brutes = lire_json(arguments.entree)
    scenario_normalise = normaliser_scenario(donnees_brutes)
    texte_json = serialiser_json(scenario_normalise)
    ecrire_sortie(texte_json, arguments.sortie)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
