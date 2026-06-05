from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from outils.chronotime.chargeur_scenarios import (
    SOURCE_PAR_DEFAUT,
    normaliser_date_iso,
    normaliser_scenario,
)


class TestChargeurScenarios(unittest.TestCase):
    def test_normaliser_date_iso(self) -> None:
        self.assertEqual(normaliser_date_iso("2026-05-01"), "2026-05-01")
        self.assertIsNone(normaliser_date_iso(None))

    def test_lecture_et_normalisation_exemple(self) -> None:
        donnees = self._charger_exemple_normalise()
        self.assertEqual(donnees["resume"]["nombre_blocs"], 6)
        self.assertEqual(donnees["resume"]["nombre_blocs_actifs"], 5)
        self.assertEqual(donnees["resume"]["nombre_blocs_inactifs"], 1)

    def test_source_simulation_locale(self) -> None:
        self.assertEqual(self._charger_exemple_normalise()["source"], SOURCE_PAR_DEFAUT)

    def test_date_cible_noel(self) -> None:
        dates_cibles = self._charger_exemple_normalise()["scenario"]["dates_cibles"]
        self.assertIn({"identifiant": "noel", "libelle": "Noël", "date": "2026-12-25"}, dates_cibles)

    def test_bloc_vacances_ete_actif(self) -> None:
        bloc = self._bloc("bloc_vacances_ete")
        self.assertTrue(bloc["actif"])

    def test_bloc_desactive_inactif(self) -> None:
        bloc = self._bloc("bloc_ignore")
        self.assertEqual(bloc["type"], "bloc_ignore")
        self.assertFalse(bloc["actif"])

    def test_duree_jours_calendaires(self) -> None:
        bloc = self._bloc("bloc_noel")
        self.assertEqual(bloc["duree"], {"unite": "jours_calendaires", "valeur": 8.0, "methode": "jours_inclus"})

    def test_duree_jours_ouvres(self) -> None:
        donnees = {
            "source": SOURCE_PAR_DEFAUT,
            "scenario": {
                "identifiant": "test",
                "periode": {"debut": "2026-01-01", "fin": "2026-01-31"},
                "blocs": [
                    {
                        "identifiant_local": "ouvres",
                        "date_debut": "2026-01-05",
                        "date_fin": "2026-01-11",
                        "unite": "jours_ouvres",
                    }
                ],
            },
        }
        bloc = normaliser_scenario(donnees)["scenario"]["blocs"][0]
        self.assertEqual(bloc["duree"], {"unite": "jours_ouvres", "valeur": 5.0, "methode": "jours_lundi_a_vendredi"})

    def test_duree_jours_ouvrables(self) -> None:
        bloc = self._bloc("bloc_vacances_ete")
        self.assertEqual(bloc["duree"], {"unite": "jours_ouvrables", "valeur": 11.0, "methode": "jours_lundi_a_samedi"})

    def test_absence_prise_en_compte_jours_feries(self) -> None:
        donnees = {
            "source": SOURCE_PAR_DEFAUT,
            "scenario": {
                "identifiant": "test",
                "periode": {"debut": "2026-12-01", "fin": "2026-12-31"},
                "blocs": [
                    {
                        "identifiant_local": "noel",
                        "date_debut": "2026-12-25",
                        "date_fin": "2026-12-25",
                        "unite": "jours_ouvres",
                    }
                ],
            },
        }
        bloc = normaliser_scenario(donnees)["scenario"]["blocs"][0]
        self.assertEqual(bloc["duree"]["valeur"], 1.0)
        self.assertEqual(bloc["duree"]["methode"], "jours_lundi_a_vendredi")

    def test_choix_compteur_auto_normalise(self) -> None:
        donnees = self._scenario_avec_bloc(
            {
                "identifiant_local": "auto",
                "date_debut": "2026-01-05",
                "date_fin": "2026-01-05",
                "unite": "jours_ouvres",
                "choix_compteur": {"mode": "auto"},
                "origine_bloc": "utilisateur",
            }
        )
        bloc = normaliser_scenario(donnees)["scenario"]["blocs"][0]

        self.assertEqual(bloc["choix_compteur"], {"mode": "auto", "compteur": None})
        self.assertEqual(bloc["origine_bloc"], "utilisateur")

    def test_choix_compteur_manuel_normalise(self) -> None:
        donnees = self._scenario_avec_bloc(
            {
                "identifiant_local": "manuel",
                "date_debut": "2026-01-05",
                "date_fin": "2026-01-05",
                "unite": "jours_ouvres",
                "choix_compteur": {"mode": "manuel", "compteur": "CANC"},
            }
        )
        bloc = normaliser_scenario(donnees)["scenario"]["blocs"][0]

        self.assertEqual(bloc["choix_compteur"], {"mode": "manuel", "compteur": "CANC"})

    def test_ancien_compteur_souhaite_devient_choix_manuel(self) -> None:
        donnees = self._scenario_avec_bloc(
            {
                "identifiant_local": "ancien",
                "date_debut": "2026-01-05",
                "date_fin": "2026-01-05",
                "unite": "jours_ouvres",
                "compteur_souhaite": "GCP",
            }
        )
        bloc = normaliser_scenario(donnees)["scenario"]["blocs"][0]

        self.assertEqual(bloc["choix_compteur"], {"mode": "manuel", "compteur": "GCP"})
        self.assertEqual(bloc["compteur_souhaite"], "GCP")

    def test_scenario_existant_reste_compatible_sans_choix_compteur(self) -> None:
        donnees = self._scenario_avec_bloc(
            {
                "identifiant_local": "sans_choix",
                "date_debut": "2026-01-05",
                "date_fin": "2026-01-05",
                "unite": "jours_ouvres",
            }
        )
        bloc = normaliser_scenario(donnees)["scenario"]["blocs"][0]

        self.assertIsNone(bloc["choix_compteur"])

    def test_script_sans_sortie(self) -> None:
        chemin_exemple = Path("donnees/exemples/scenario_simulation.exemple.json")
        resultat = subprocess.run(
            [sys.executable, "outils/chronotime/chargeur_scenarios.py", str(chemin_exemple)],
            check=True,
            capture_output=True,
            text=True,
        )
        donnees = json.loads(resultat.stdout)
        self.assertEqual(donnees["source"], SOURCE_PAR_DEFAUT)

    def test_script_avec_sortie(self) -> None:
        chemin_exemple = Path("donnees/exemples/scenario_simulation.exemple.json")
        with tempfile.TemporaryDirectory() as repertoire_temporaire:
            chemin_sortie = Path(repertoire_temporaire) / "scenario.json"
            subprocess.run(
                [
                    sys.executable,
                    "outils/chronotime/chargeur_scenarios.py",
                    str(chemin_exemple),
                    "--sortie",
                    str(chemin_sortie),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            donnees = json.loads(chemin_sortie.read_text(encoding="utf-8"))
            self.assertEqual(donnees["source"], SOURCE_PAR_DEFAUT)

    def _charger_exemple_normalise(self) -> dict[str, object]:
        chemin_exemple = Path("donnees/exemples/scenario_simulation.exemple.json")
        donnees_brutes = json.loads(chemin_exemple.read_text(encoding="utf-8"))
        return normaliser_scenario(donnees_brutes)

    def _scenario_avec_bloc(self, bloc: dict[str, object]) -> dict[str, object]:
        return {
            "source": SOURCE_PAR_DEFAUT,
            "scenario": {
                "identifiant": "test",
                "periode": {"debut": "2026-01-01", "fin": "2026-01-31"},
                "blocs": [bloc],
            },
        }

    def _bloc(self, identifiant_local: str) -> dict[str, object]:
        donnees = self._charger_exemple_normalise()
        return next(
            bloc
            for bloc in donnees["scenario"]["blocs"]
            if bloc["identifiant_local"] == identifiant_local
        )


if __name__ == "__main__":
    unittest.main()
