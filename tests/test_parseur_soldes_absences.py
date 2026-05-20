from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from outils.chronotime.parseur_soldes_absences import (
    MODELE_SOURCE,
    analyser_quantite_chronotime,
    normaliser_compteur,
    normaliser_donnees,
    normaliser_periode,
)


class TestParseurSoldesAbsences(unittest.TestCase):
    def test_parser_25j00(self) -> None:
        self.assertEqual(
            analyser_quantite_chronotime("25j00"),
            {"brut": "25j00", "unite": "jour", "valeur": 25.0},
        )

    def test_parser_1j90(self) -> None:
        self.assertEqual(
            analyser_quantite_chronotime("1j90"),
            {"brut": "1j90", "unite": "jour", "valeur": 1.9},
        )

    def test_parser_23j96(self) -> None:
        self.assertEqual(
            analyser_quantite_chronotime("23j96"),
            {"brut": "23j96", "unite": "jour", "valeur": 23.96},
        )

    def test_parser_0h00m(self) -> None:
        self.assertEqual(
            analyser_quantite_chronotime("0h00m"),
            {"brut": "0h00m", "unite": "heure", "valeur": 0.0},
        )

    def test_parser_2h30m(self) -> None:
        self.assertEqual(
            analyser_quantite_chronotime("2h30m"),
            {"brut": "2h30m", "unite": "heure", "valeur": 2.5},
        )

    def test_parser_null(self) -> None:
        self.assertIsNone(analyser_quantite_chronotime(None))

    def test_nettoyage_libelle(self) -> None:
        compteur = normaliser_compteur(
            {
                "code": "GCP",
                "libelle": "  CONGES PAYES  ",
                "precedent": None,
                "courant": None,
                "suivant": None,
            }
        )
        self.assertEqual(compteur["libelle"], "CONGES PAYES")

    def test_normalisation_periode_absente(self) -> None:
        self.assertIsNone(normaliser_periode(None))

    def test_normalisation_fichier_exemple(self) -> None:
        chemin_exemple = Path("donnees/exemples/soldes_absences_chronotime.exemple.json")
        donnees_brutes = json.loads(chemin_exemple.read_text(encoding="utf-8"))
        donnees_normalisees = normaliser_donnees(donnees_brutes)

        self.assertEqual(donnees_normalisees["source"], MODELE_SOURCE)
        self.assertEqual(len(donnees_normalisees["compteurs"]), 4)

        compteur_gcp = donnees_normalisees["compteurs"][0]
        self.assertEqual(compteur_gcp["code"], "GCP")
        self.assertEqual(compteur_gcp["libelle"], "CONGES PAYES")
        self.assertIsNone(compteur_gcp["periodes"]["precedent"])
        self.assertEqual(
            compteur_gcp["periodes"]["courant"]["droit"],
            {"brut": "25j00", "unite": "jour", "valeur": 25.0},
        )
        self.assertEqual(
            compteur_gcp["periodes"]["courant"]["pris"],
            {"brut": "1j90", "unite": "jour", "valeur": 1.9},
        )
        self.assertEqual(
            compteur_gcp["periodes"]["courant"]["solde"],
            {"brut": "23j96", "unite": "jour", "valeur": 23.96},
        )

    def test_script_en_ligne_de_commande_sans_sortie(self) -> None:
        chemin_exemple = Path("donnees/exemples/soldes_absences_chronotime.exemple.json")
        resultat = subprocess.run(
            [sys.executable, "outils/chronotime/parseur_soldes_absences.py", str(chemin_exemple)],
            check=True,
            capture_output=True,
            text=True,
        )
        donnees = json.loads(resultat.stdout)
        self.assertEqual(donnees["source"], MODELE_SOURCE)

    def test_script_en_ligne_de_commande_avec_sortie(self) -> None:
        chemin_exemple = Path("donnees/exemples/soldes_absences_chronotime.exemple.json")
        with tempfile.TemporaryDirectory() as repertoire_temporaire:
            chemin_sortie = Path(repertoire_temporaire) / "sortie.json"
            subprocess.run(
                [
                    sys.executable,
                    "outils/chronotime/parseur_soldes_absences.py",
                    str(chemin_exemple),
                    "--sortie",
                    str(chemin_sortie),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            donnees = json.loads(chemin_sortie.read_text(encoding="utf-8"))
            self.assertEqual(donnees["source"], MODELE_SOURCE)


if __name__ == "__main__":
    unittest.main()
