from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

MODELE_SOURCE = "chronotime.agenda"


def nettoyer_libelle(libelle_brut: Any) -> str:
    if libelle_brut is None:
        return ""
    if not isinstance(libelle_brut, str):
        return str(libelle_brut).strip()
    return libelle_brut.strip()


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


def normaliser_date_chronotime(valeur_brute: Any) -> str | None:
    if valeur_brute is None:
        return None

    texte = str(valeur_brute).strip()
    if len(texte) != 8 or not texte.isdigit():
        raise ValueError(f"Date Chronotime invalide : {valeur_brute!r}")

    annee = texte[0:4]
    mois = texte[4:6]
    jour = texte[6:8]

    mois_entier = int(mois)
    jour_entier = int(jour)
    if mois_entier < 1 or mois_entier > 12:
        raise ValueError(f"Mois Chronotime invalide : {valeur_brute!r}")
    if jour_entier < 1 or jour_entier > 31:
        raise ValueError(f"Jour Chronotime invalide : {valeur_brute!r}")

    return f"{annee}-{mois}-{jour}"


def normaliser_horaire_chronotime(valeur_brute: Any) -> str | None:
    if valeur_brute is None:
        return None

    if isinstance(valeur_brute, str):
        texte = valeur_brute.strip()
        if texte == "":
            raise ValueError("Horaire Chronotime invalide : chaîne vide")
        if not texte.isdigit():
            raise ValueError(f"Horaire Chronotime invalide : {valeur_brute!r}")
        valeur = int(texte)
    elif isinstance(valeur_brute, int):
        valeur = valeur_brute
    else:
        raise ValueError(f"Horaire Chronotime invalide : {valeur_brute!r}")

    if valeur < 0 or valeur > 2359:
        raise ValueError(f"Horaire Chronotime invalide : {valeur_brute!r}")

    heures = valeur // 100
    minutes = valeur % 100
    if heures > 23 or minutes > 59:
        raise ValueError(f"Horaire Chronotime invalide : {valeur_brute!r}")

    return f"{heures:02d}:{minutes:02d}"


def _extraire_libelle_depuis_entree(entree: Any) -> str:
    if isinstance(entree, dict):
        for cle in ("lib", "libelle", "label", "nom"):
            if cle in entree:
                return nettoyer_libelle(entree.get(cle))
    if isinstance(entree, str):
        return nettoyer_libelle(entree)
    return ""


def _extraire_repos_depuis_entree(entree: Any) -> bool | None:
    if isinstance(entree, dict) and "re" in entree:
        valeur = entree.get("re")
        if isinstance(valeur, bool):
            return valeur
        if valeur in (0, 1):
            return bool(valeur)
        if isinstance(valeur, str):
            texte = valeur.strip().lower()
            if texte in {"0", "false", "non", "n"}:
                return False
            if texte in {"1", "true", "oui", "o"}:
                return True
    return None


def _extraire_groupe_depuis_entree(entree: Any) -> str | None:
    if isinstance(entree, dict):
        for cle in ("grp", "groupe", "grpabs"):
            valeur = entree.get(cle)
            if valeur:
                return str(valeur)
    return None


def indexer_par_code(objets: Any, cles_code: tuple[str, ...] = ("cod", "code")) -> dict[str, Any]:
    if isinstance(objets, dict):
        return {str(code): entree for code, entree in objets.items()}
    if not isinstance(objets, list):
        return {}

    resultat = {}
    for entree in objets:
        if not isinstance(entree, dict):
            continue
        for cle_code in cles_code:
            if cle_code in entree and entree.get(cle_code) is not None:
                resultat[str(entree[cle_code])] = entree
                break
    return resultat


def construire_dictionnaires_normalises(dictionnaires_bruts: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(dictionnaires_bruts, dict):
        dictionnaires_bruts = {}

    absences = {}
    for code, entree in indexer_par_code(dictionnaires_bruts.get("abs")).items():
        groupe_code = _extraire_groupe_depuis_entree(entree)
        absences[str(code)] = {
            "code": str(code),
            "libelle": _extraire_libelle_depuis_entree(entree),
            "groupe_code": groupe_code,
        }

    groupes_absence = {}
    for code, entree in indexer_par_code(dictionnaires_bruts.get("grpabs")).items():
        groupes_absence[str(code)] = {
            "code": str(code),
            "libelle": _extraire_libelle_depuis_entree(entree),
        }

    statuts = {}
    for code, entree in indexer_par_code(dictionnaires_bruts.get("wkf")).items():
        statuts[str(code)] = {
            "code": str(code),
            "libelle": _extraire_libelle_depuis_entree(entree),
        }

    unite_sources = {}
    for nom_source in ("unt", "untabs"):
        for code, entree in indexer_par_code(dictionnaires_bruts.get(nom_source)).items():
            unite_sources[str(code)] = _extraire_libelle_depuis_entree(entree)

    unites = {}
    for code, libelle in unite_sources.items():
        unites[code] = normaliser_unite(code, unite_sources)

    horaires = {}
    for code, entree in indexer_par_code(dictionnaires_bruts.get("hor")).items():
        horaires[str(code)] = {
            "code": str(code),
            "libelle": _extraire_libelle_depuis_entree(entree),
            "repos": _extraire_repos_depuis_entree(entree),
        }

    return {
        "absences": absences,
        "groupes_absence": groupes_absence,
        "statuts": statuts,
        "unites": unites,
        "horaires": horaires,
    }


def normaliser_unite(code_unite: Any, dictionnaire_unites: dict[str, str] | None = None) -> dict[str, Any] | None:
    if code_unite is None:
        return None

    code = str(code_unite).strip()
    if code == "":
        return None

    correspondances = {
        "M": ("Matin", 0.5),
        "S": ("Après-midi", 0.5),
        "J": ("Jour complet", 1.0),
        "D": ("Jour complet", 1.0),
        "H": ("Heure", None),
    }

    libelle_par_defaut, fraction_jour = correspondances.get(code, (code, None))
    libelle = nettoyer_libelle((dictionnaire_unites or {}).get(code)) or libelle_par_defaut

    return {
        "code": code,
        "libelle": libelle,
        "fraction_jour": fraction_jour,
    }


def normaliser_statut(code_statut: Any, dictionnaire_statuts: dict[str, dict[str, Any]] | None = None) -> dict[str, Any] | None:
    if code_statut is None:
        return None

    code = str(code_statut).strip()
    if code == "":
        return None

    libelle = ""
    if dictionnaire_statuts and code in dictionnaire_statuts:
        libelle = nettoyer_libelle(dictionnaire_statuts[code].get("libelle"))

    if libelle == "" and code == "A":
        libelle = "Accepté"

    return {
        "code": code,
        "libelle": libelle,
    }


def normaliser_horaire_intervalle(debut_brut: Any, fin_brut: Any) -> dict[str, Any]:
    return {
        "debut_brut": debut_brut,
        "fin_brut": fin_brut,
        "debut": normaliser_horaire_chronotime(debut_brut),
        "fin": normaliser_horaire_chronotime(fin_brut),
    }


def normaliser_absences(
    evenements_bruts: Any,
    dictionnaires_normalises: dict[str, dict[str, Any]],
    dictionnaires_bruts: dict[str, Any],
) -> list[dict[str, Any]]:
    resultat = []
    if not isinstance(evenements_bruts, list):
        return resultat

    unites_sources = {}
    for nom_source in ("untabs", "unt"):
        for code, entree in indexer_par_code(dictionnaires_bruts.get(nom_source)).items():
            unites_sources[str(code)] = _extraire_libelle_depuis_entree(entree)

    for groupe in evenements_bruts:
        if not isinstance(groupe, dict):
            continue
        date = normaliser_date_chronotime(groupe.get("dat"))
        for evenement in (groupe.get("evt") or []):
            if not isinstance(evenement, dict):
                continue
            details = evenement.get("dts") or {}
            if not isinstance(details, dict):
                details = {}
            parametres = details.get("par") if isinstance(details, dict) else {}
            if not isinstance(parametres, dict):
                parametres = {}

            code = evenement.get("cod")
            code_texte = "" if code is None else str(code)
            dictionnaire_absence = dictionnaires_normalises["absences"].get(code_texte, {})

            libelle = nettoyer_libelle(parametres.get("@absLibelleMotif"))
            if libelle == "":
                libelle = nettoyer_libelle(dictionnaire_absence.get("libelle"))

            code_unite = parametres.get("@absUniteDate") or evenement.get("val")
            code_statut = details.get("sta") or details.get("eta") or evenement.get("sta") or evenement.get("eta")
            debut_brut = details.get("hed") if "hed" in details else evenement.get("hed")
            fin_brut = details.get("hef") if "hef" in details else evenement.get("hef")
            resultat.append(
                {
                    "date": date,
                    "categorie": "absence",
                    "code": code_texte,
                    "libelle": libelle,
                    "unite": normaliser_unite(code_unite, unites_sources),
                    "horaire": normaliser_horaire_intervalle(debut_brut, fin_brut),
                    "statut": normaliser_statut(code_statut, dictionnaires_normalises["statuts"]),
                    "type_evenement_source": "1",
                }
            )
    return resultat


def normaliser_horaires_jours_types(
    evenements_bruts: Any,
    dictionnaires_normalises: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    resultat = []
    if not isinstance(evenements_bruts, list):
        return resultat

    for groupe in evenements_bruts:
        if not isinstance(groupe, dict):
            continue
        date = normaliser_date_chronotime(groupe.get("dat"))
        for evenement in (groupe.get("evt") or []):
            if not isinstance(evenement, dict):
                continue
            code = evenement.get("cod")
            code_texte = "" if code is None else str(code)
            dictionnaire_horaire = dictionnaires_normalises["horaires"].get(code_texte, {})

            evenement_normalise = {
                "date": date,
                "categorie": "horaire",
                "code": code_texte,
                "libelle": nettoyer_libelle(dictionnaire_horaire.get("libelle")),
                "type_evenement_source": "0",
            }
            if "repos" in dictionnaire_horaire and dictionnaire_horaire.get("repos") is not None:
                evenement_normalise["repos"] = dictionnaire_horaire.get("repos")

            resultat.append(evenement_normalise)
    return resultat


def compter_evenements_ignores(evenements_par_type: Any) -> dict[str, int]:
    resultat = {}
    if not isinstance(evenements_par_type, dict):
        return resultat

    for type_evenement, groupes in evenements_par_type.items():
        if type_evenement in {"0", "1"}:
            continue
        compteur = 0
        if isinstance(groupes, list):
            for groupe in groupes:
                if isinstance(groupe, dict) and isinstance(groupe.get("evt"), list):
                    compteur += len(groupe["evt"])
                else:
                    compteur += 1
        resultat[str(type_evenement)] = compteur
    return resultat


def normaliser_donnees(donnees_brutes: Any) -> dict[str, Any]:
    if not isinstance(donnees_brutes, dict):
        raise ValueError("La réponse agenda doit être un objet JSON.")

    evenements_par_type = donnees_brutes.get("evt")
    if not isinstance(evenements_par_type, dict):
        raise ValueError("La réponse agenda doit contenir un objet 'evt'.")

    dictionnaires_bruts = donnees_brutes.get("dts")
    if not isinstance(dictionnaires_bruts, dict):
        dictionnaires_bruts = {}

    dictionnaires_normalises = construire_dictionnaires_normalises(dictionnaires_bruts)
    evenements = []
    evenements.extend(normaliser_horaires_jours_types(evenements_par_type.get("0"), dictionnaires_normalises))
    evenements.extend(
        normaliser_absences(
            evenements_par_type.get("1"),
            dictionnaires_normalises,
            dictionnaires_bruts,
        )
    )

    return {
        "source": MODELE_SOURCE,
        "plage_dates": {
            "debut": normaliser_date_chronotime(donnees_brutes.get("datd")),
            "fin": normaliser_date_chronotime(donnees_brutes.get("datf")),
        },
        "evenements": evenements,
        "dictionnaires": dictionnaires_normalises,
        "resume_source": {
            "types_evenements_ignores": compter_evenements_ignores(evenements_par_type),
        },
    }


def analyser_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(
        description="Normaliser une réponse Chronotime agenda depuis un fichier local.",
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
