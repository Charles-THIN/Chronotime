from __future__ import annotations

import argparse
import subprocess
import sys
import webbrowser
from pathlib import Path


RACINE_DEPOT = Path(__file__).resolve().parents[2]


def chemin_relatif(valeur: str) -> Path:
    chemin = Path(valeur)
    return chemin if chemin.is_absolute() else RACINE_DEPOT / chemin


def creer_parseur() -> argparse.ArgumentParser:
    analyseur = argparse.ArgumentParser(
        description="Préparer et ouvrir la vue locale de planification Chronotime.",
    )
    analyseur.add_argument("--soldes", default="donnees_locales/soldes_absences_chronotime.json")
    analyseur.add_argument("--agenda", default="donnees_locales/agenda_chronotime.json")
    analyseur.add_argument("--obligations", default="donnees_locales/obligations_conges_2026.json")
    analyseur.add_argument("--scenario", default="donnees_locales/scenario_vide.json")
    analyseur.add_argument("--evenements-compteurs", default="donnees_locales/evenements_compteurs.json")
    analyseur.add_argument("--date-depart", default="2026-05-20")
    analyseur.add_argument("--date-fin", default="2027-01-31")
    analyseur.add_argument("--periode-compteurs", default="courant")
    analyseur.add_argument("--periodes-compteurs-par-code", default="GCP=suivant,JRTT=courant,CANC=courant")
    analyseur.add_argument("--soldes-minimums-par-code", default="JRTT=-10,GCP=0,CANC=0")
    analyseur.add_argument("--jours-non-decomptes", default="2026-12-25,2026-07-14,2026-08-15")
    analyseur.add_argument(
        "--date-cible",
        action="append",
        default=None,
        help="Date cible au format identifiant=libellé=YYYY-MM-DD. Répéter l'option si nécessaire.",
    )
    analyseur.add_argument(
        "--sortie-projection",
        default="donnees_locales/projection_obligations_seules_v2.json",
    )
    analyseur.add_argument(
        "--sortie-entrees-projection",
        default="donnees_locales/entrees_projection_obligations_seules_v2.json",
    )
    analyseur.add_argument("--sortie-vue", default="donnees_locales/vue_projection.html")
    analyseur.add_argument("--ne-pas-ouvrir", action="store_true")
    return analyseur


def fichiers_obligatoires(arguments: argparse.Namespace) -> list[Path]:
    return [
        chemin_relatif(arguments.soldes),
        chemin_relatif(arguments.agenda),
        chemin_relatif(arguments.obligations),
        chemin_relatif(arguments.scenario),
    ]


def verifier_fichiers_obligatoires(arguments: argparse.Namespace) -> None:
    manquants = [chemin for chemin in fichiers_obligatoires(arguments) if not chemin.exists()]
    if manquants:
        lignes = "\n".join(f"- {chemin}" for chemin in manquants)
        raise SystemExit(f"Fichiers indispensables absents :\n{lignes}")


def construire_commande_orchestrateur(arguments: argparse.Namespace) -> list[str]:
    commande = [
        sys.executable,
        str(RACINE_DEPOT / "outils/chronotime/orchestrateur_projection.py"),
        "--soldes",
        str(chemin_relatif(arguments.soldes)),
        "--agenda",
        str(chemin_relatif(arguments.agenda)),
        "--obligations",
        str(chemin_relatif(arguments.obligations)),
        "--scenario",
        str(chemin_relatif(arguments.scenario)),
        "--date-depart",
        arguments.date_depart,
        "--date-fin",
        arguments.date_fin,
        "--periode-compteurs",
        arguments.periode_compteurs,
        "--periodes-compteurs-par-code",
        arguments.periodes_compteurs_par_code,
        "--soldes-minimums-par-code",
        arguments.soldes_minimums_par_code,
        "--jours-non-decomptes",
        arguments.jours_non_decomptes,
        "--sortie",
        str(chemin_relatif(arguments.sortie_projection)),
        "--sortie-entrees-projection",
        str(chemin_relatif(arguments.sortie_entrees_projection)),
    ]
    chemin_evenements = chemin_relatif(arguments.evenements_compteurs)
    if chemin_evenements.exists():
        commande.extend(["--evenements-compteurs", str(chemin_evenements)])
    else:
        print(f"Événements de compteur absents, option ignorée : {chemin_evenements}")
    dates_cibles = arguments.date_cible if arguments.date_cible is not None else ["noel=Noël=2026-12-25"]
    for date_cible in dates_cibles:
        commande.extend(["--date-cible", date_cible])
    return commande


def construire_commande_generateur(arguments: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(RACINE_DEPOT / "outils/chronotime/generateur_vue_projection.py"),
        "--projection",
        str(chemin_relatif(arguments.sortie_projection)),
        "--entrees-projection",
        str(chemin_relatif(arguments.sortie_entrees_projection)),
        "--sortie",
        str(chemin_relatif(arguments.sortie_vue)),
    ]


def lancer_commande(commande: list[str]) -> None:
    subprocess.run(commande, cwd=RACINE_DEPOT, check=True)


def main(argv: list[str] | None = None) -> int:
    arguments = creer_parseur().parse_args(argv)
    verifier_fichiers_obligatoires(arguments)

    sortie_projection = chemin_relatif(arguments.sortie_projection)
    sortie_entrees = chemin_relatif(arguments.sortie_entrees_projection)
    sortie_vue = chemin_relatif(arguments.sortie_vue)
    sortie_projection.parent.mkdir(parents=True, exist_ok=True)
    sortie_entrees.parent.mkdir(parents=True, exist_ok=True)
    sortie_vue.parent.mkdir(parents=True, exist_ok=True)

    lancer_commande(construire_commande_orchestrateur(arguments))
    lancer_commande(construire_commande_generateur(arguments))

    print(f"Projection générée : {sortie_projection}")
    print(f"Entrées de projection générées : {sortie_entrees}")
    print(f"Vue HTML générée : {sortie_vue}")

    if arguments.ne_pas_ouvrir:
        print("Ouverture navigateur désactivée.")
        return 0

    webbrowser.open(sortie_vue.resolve().as_uri())
    print("Ouverture navigateur demandée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
