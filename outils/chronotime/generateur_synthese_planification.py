from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


SOURCE_PROJECTION = "projection.demi_journees"
SOURCE_MOUVEMENTS = "mouvements.soldes"
SOURCE_CHRONOLOGIE = "chronologie.soldes"
SOURCE_SORTIE = "synthese.planification"


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


def arrondir(valeur: float) -> float:
    return round(float(valeur), 10)


def valider_sources(
    projection: Any,
    mouvements: Any,
    chronologie: Any,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if not isinstance(projection, dict):
        raise ValueError("La projection doit être un objet JSON.")
    if projection.get("source") != SOURCE_PROJECTION:
        raise ValueError("La source de projection attendue est 'projection.demi_journees'.")
    if not isinstance(mouvements, dict):
        raise ValueError("Les mouvements doivent être un objet JSON.")
    if mouvements.get("source") != SOURCE_MOUVEMENTS:
        raise ValueError("La source de mouvements attendue est 'mouvements.soldes'.")
    if not isinstance(chronologie, dict):
        raise ValueError("La chronologie doit être un objet JSON.")
    if chronologie.get("source") != SOURCE_CHRONOLOGIE:
        raise ValueError("La source de chronologie attendue est 'chronologie.soldes'.")
    return projection, mouvements, chronologie


def somme_soldes(soldes: Any) -> float:
    if not isinstance(soldes, dict):
        return 0.0
    total = 0.0
    for valeur in soldes.values():
        valeur_numerique = nombre_ou_none(valeur)
        if valeur_numerique is not None:
            total += valeur_numerique
    return arrondir(total)


def unite_agregeable(unite: Any) -> bool:
    return unite is None or str(unite).strip() in {"", "jour", "jours"}


def classer_type_mouvement(type_mouvement: Any) -> str:
    texte = str(type_mouvement or "").lower()
    if "consommation" in texte:
        return "consommation_absence"
    if "expiration" in texte:
        return "expiration"
    if "credit" in texte:
        return "credit"
    if "ajustement" in texte:
        return "ajustement"
    if "report" in texte:
        return "report"
    return "autre"


def signal_unite_non_agregee(mouvement: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "unite_non_agregee",
        "severite": "information",
        "message": "Un mouvement n’a pas été inclus dans les totaux en jours.",
        "details": copy.deepcopy(mouvement),
    }


def signal_alerte_source(alerte: dict[str, Any], origine: str) -> dict[str, Any]:
    severite = str(alerte.get("severite") or "information")
    return {
        "type": "alerte_source",
        "severite": severite,
        "message": "Une alerte source est présente dans les données dérivées.",
        "details": {"origine": origine, "alerte": copy.deepcopy(alerte)},
    }


def signaux_depuis_alertes_sources(
    projection: dict[str, Any],
    mouvements: dict[str, Any],
    chronologie: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    signaux: list[dict[str, Any]] = []
    alertes_sources: list[dict[str, Any]] = []
    for origine, source in (
        ("projection.demi_journees", projection),
        ("mouvements.soldes", mouvements),
        ("chronologie.soldes", chronologie),
    ):
        alertes = source.get("alertes", [])
        if not isinstance(alertes, list):
            continue
        for alerte in alertes:
            if not isinstance(alerte, dict):
                continue
            alerte_copie = copy.deepcopy(alerte)
            alertes_sources.append({"origine": origine, "alerte": alerte_copie})
            signaux.append(signal_alerte_source(alerte_copie, origine))
    return signaux, alertes_sources


def agreger_consommation_evenement(
    agregats: dict[str, dict[str, Any]],
    mouvement: dict[str, Any],
    variation: float,
) -> None:
    identifiant = str(mouvement.get("identifiant") or "sans_identifiant")
    date_mouvement = str(mouvement.get("date") or "")
    compteur = str(mouvement.get("compteur") or "")
    agregat = agregats.setdefault(
        identifiant,
        {
            "identifiant": identifiant,
            "premiere_date": date_mouvement,
            "derniere_date": date_mouvement,
            "jours_consommes": 0.0,
            "compteurs_techniques": {},
            "origines": set(),
            "types": set(),
        },
    )
    if date_mouvement:
        dates = [date for date in (agregat["premiere_date"], agregat["derniere_date"], date_mouvement) if date]
        agregat["premiere_date"] = min(dates)
        agregat["derniere_date"] = max(dates)
    agregat["jours_consommes"] = arrondir(agregat["jours_consommes"] + abs(variation))
    if compteur:
        compteurs = agregat["compteurs_techniques"]
        compteurs[compteur] = arrondir(float(compteurs.get(compteur, 0.0)) + variation)
    agregat["origines"].add("projection.demi_journees")
    if mouvement.get("origine"):
        agregat["origines"].add(str(mouvement.get("origine")))
    if mouvement.get("type"):
        agregat["types"].add(str(mouvement.get("type")))


def finaliser_consommations(agregats: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    consommations = []
    for agregat in agregats.values():
        consommations.append(
            {
                "identifiant": agregat["identifiant"],
                "premiere_date": agregat["premiere_date"],
                "derniere_date": agregat["derniere_date"],
                "jours_consommes": arrondir(agregat["jours_consommes"]),
                "compteurs_techniques": dict(sorted(agregat["compteurs_techniques"].items())),
                "origines": sorted(agregat["origines"]),
                "types": sorted(agregat["types"]),
            }
        )
    return sorted(
        consommations,
        key=lambda evenement: (
            -float(evenement["jours_consommes"]),
            str(evenement.get("premiere_date") or ""),
            str(evenement.get("identifiant") or ""),
        ),
    )


def dates_cibles_agregees(projection: dict[str, Any]) -> list[dict[str, Any]]:
    dates_cibles = projection.get("soldes_aux_dates_cibles", [])
    if not isinstance(dates_cibles, list):
        return []
    resultat = []
    for cible in dates_cibles:
        if not isinstance(cible, dict):
            continue
        resultat.append(
            {
                "identifiant": cible.get("identifiant"),
                "libelle": cible.get("libelle"),
                "date": cible.get("date"),
                "jours_restants_agreges": somme_soldes(cible.get("soldes")),
            }
        )
    return resultat


def details_par_compteur(projection: dict[str, Any], chronologie: dict[str, Any]) -> dict[str, dict[str, Any]]:
    parametres = projection.get("parametres_projection", {})
    parametres = parametres if isinstance(parametres, dict) else {}
    seuils = parametres.get("soldes_minimums_par_code", {})
    seuils = seuils if isinstance(seuils, dict) else {}
    initiaux = chronologie.get("soldes_initiaux", {})
    finaux = chronologie.get("soldes_finaux", {})
    initiaux = initiaux if isinstance(initiaux, dict) else {}
    finaux = finaux if isinstance(finaux, dict) else {}
    compteurs = sorted(set(str(cle) for cle in initiaux) | set(str(cle) for cle in finaux))
    details: dict[str, dict[str, Any]] = {}
    for compteur in compteurs:
        initial = nombre_ou_none(initiaux.get(compteur))
        final = nombre_ou_none(finaux.get(compteur))
        details[compteur] = {
            "initial": initial,
            "final": final,
            "variation": arrondir((final or 0.0) - (initial or 0.0)),
            "seuil_technique_suppose": nombre_ou_none(seuils.get(compteur)),
        }
    return details


def ajouter_signaux_soldes(
    signaux: list[dict[str, Any]],
    par_compteur: dict[str, dict[str, Any]],
) -> None:
    for compteur, details in par_compteur.items():
        final = nombre_ou_none(details.get("final"))
        seuil = nombre_ou_none(details.get("seuil_technique_suppose"))
        if final is None:
            continue
        if seuil is not None and final < seuil:
            signaux.append(
                {
                    "type": "compteur_sous_seuil_technique_suppose",
                    "severite": "bloquant",
                    "message": "Un compteur technique finit sous son seuil supposé ; Chronotime pourrait refuser le scénario.",
                    "details": {
                        "compteur": compteur,
                        "final": final,
                        "seuil_technique_suppose": seuil,
                    },
                }
            )
        elif seuil is None and final < 0:
            signaux.append(
                {
                    "type": "compteur_final_negatif_sans_seuil_connu",
                    "severite": "attention",
                    "message": "Un compteur technique finit négatif sans seuil supposé connu.",
                    "details": {"compteur": compteur, "final": final},
                }
            )


def statut_global(signaux: list[dict[str, Any]]) -> str:
    severites = {str(signal.get("severite") or "") for signal in signaux if isinstance(signal, dict)}
    if "bloquant" in severites:
        return "bloquant"
    if "attention" in severites or "confirmation" in severites:
        return "attention"
    return "ok"


def generer_synthese_planification(projection_brute: Any, mouvements_bruts: Any, chronologie_brute: Any) -> dict[str, Any]:
    projection, mouvements_source, chronologie = valider_sources(projection_brute, mouvements_bruts, chronologie_brute)

    signaux, alertes_sources = signaux_depuis_alertes_sources(projection, mouvements_source, chronologie)
    consommations_agregees: dict[str, dict[str, Any]] = {}
    variation_totale = 0.0
    jours_consommes = 0.0
    jours_expires = 0.0
    jours_credites = 0.0
    jours_debites_techniques = 0.0

    mouvements = mouvements_source.get("mouvements", [])
    if not isinstance(mouvements, list):
        mouvements = []
    for mouvement in mouvements:
        if not isinstance(mouvement, dict):
            continue
        if not unite_agregeable(mouvement.get("unite")):
            signaux.append(signal_unite_non_agregee(mouvement))
            continue
        variation = nombre_ou_none(mouvement.get("variation"))
        if variation is None:
            continue
        classe = classer_type_mouvement(mouvement.get("type"))
        variation_totale += variation
        if classe == "consommation_absence" and variation < 0:
            jours_consommes += abs(variation)
            agreger_consommation_evenement(consommations_agregees, mouvement, variation)
        elif classe == "expiration" and variation < 0:
            jours_expires += abs(variation)
        elif classe == "credit" and variation > 0:
            jours_credites += variation
        elif classe in {"ajustement", "report", "autre"} and variation < 0:
            jours_debites_techniques += abs(variation)

    if jours_expires > 0:
        signaux.append(
            {
                "type": "jours_expires",
                "severite": "attention",
                "message": "Des jours expirent dans ce scénario.",
                "details": {"jours_expires": arrondir(jours_expires)},
            }
        )

    par_compteur = details_par_compteur(projection, chronologie)
    ajouter_signaux_soldes(signaux, par_compteur)

    resume_global = {
        "jours_initiaux_agreges": somme_soldes(chronologie.get("soldes_initiaux")),
        "jours_finaux_agreges": somme_soldes(chronologie.get("soldes_finaux")),
        "variation_totale": arrondir(variation_totale),
        "jours_consommes": arrondir(jours_consommes),
        "jours_expires": arrondir(jours_expires),
        "jours_credites": arrondir(jours_credites),
        "jours_debites_techniques": arrondir(jours_debites_techniques),
        "nombre_signaux": len(signaux),
        "statut": statut_global(signaux),
    }

    return {
        "source": SOURCE_SORTIE,
        "periode": projection.get("periode", {}),
        "resume_global": resume_global,
        "consommations_par_evenement": finaliser_consommations(consommations_agregees),
        "soldes_agreges_aux_dates_cibles": dates_cibles_agregees(projection),
        "signaux": signaux,
        "details_techniques": {
            "par_compteur": par_compteur,
            "alertes_sources": alertes_sources,
        },
    }


def analyser_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(
        description="Générer une synthèse de planification agrégée depuis les sorties dérivées locales.",
    )
    analyseur.add_argument("--projection", required=True, type=Path, help="Fichier JSON projection.demi_journees.")
    analyseur.add_argument("--mouvements", required=True, type=Path, help="Fichier JSON mouvements.soldes.")
    analyseur.add_argument("--chronologie", required=True, type=Path, help="Fichier JSON chronologie.soldes.")
    analyseur.add_argument("--sortie", type=Path, help="Chemin du fichier où écrire la synthèse.")
    return analyseur.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = analyser_arguments(argv)
    try:
        projection = lire_json(arguments.projection)
        mouvements = lire_json(arguments.mouvements)
        chronologie = lire_json(arguments.chronologie)
        synthese = generer_synthese_planification(projection, mouvements, chronologie)
    except ValueError as erreur:
        raise SystemExit(str(erreur)) from erreur
    ecrire_sortie(serialiser_json(synthese), arguments.sortie)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
