from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from outils.chronotime.orchestrateur_projection import (
    analyser_arguments,
    analyser_jours_non_decomptes,
    analyser_periodes_compteurs_par_code,
    analyser_soldes_minimums_par_code,
    lire_json,
    orchestrer_projection,
)


class TestOrchestrateurProjection(unittest.TestCase):
    def test_execution_avec_quatre_fichiers_exemple(self) -> None:
        projection = self._orchestrer_avec_date_cible()
        self.assertEqual(projection["source"], "projection.demi_journees")

    def test_presence_demi_journees(self) -> None:
        projection = self._orchestrer_avec_date_cible()
        self.assertGreater(len(projection["demi_journees"]), 0)

    def test_presence_soldes_initiaux(self) -> None:
        projection = self._orchestrer_avec_date_cible()
        self.assertIn("GCP", projection["soldes_initiaux"])

    def test_presence_soldes_noel(self) -> None:
        projection = self._orchestrer_avec_date_cible()
        dates = {entree["identifiant"]: entree for entree in projection["soldes_aux_dates_cibles"]}
        self.assertIn("noel", dates)
        self.assertIsInstance(dates["noel"]["soldes"], dict)

    def test_dates_cibles_du_scenario_si_aucune_option(self) -> None:
        projection = self._orchestrer_sans_date_cible()
        self.assertEqual(projection["soldes_aux_dates_cibles"][0]["identifiant"], "noel")
        self.assertEqual(projection["soldes_aux_dates_cibles"][0]["date"], "2026-12-25")

    def test_parsing_periodes_compteurs_par_code(self) -> None:
        self.assertEqual(
            analyser_periodes_compteurs_par_code("GCP=suivant,JRTT=courant,CANC=courant"),
            {"GCP": "suivant", "JRTT": "courant", "CANC": "courant"},
        )

    def test_parsing_soldes_minimums_par_code(self) -> None:
        self.assertEqual(
            analyser_soldes_minimums_par_code("JRTT=-10,GCP=0,CANC=0"),
            {"JRTT": -10.0, "GCP": 0.0, "CANC": 0.0},
        )

    def test_parsing_jours_non_decomptes(self) -> None:
        self.assertEqual(
            analyser_jours_non_decomptes("2026-12-25,2026-07-14"),
            ["2026-12-25", "2026-07-14"],
        )

    def test_projection_periodes_par_compteur(self) -> None:
        projection = orchestrer_projection(analyser_arguments(self._arguments_communs(options_projection=True)))
        self.assertEqual(projection["parametres_projection"]["periodes_compteurs_par_code"]["GCP"], "suivant")
        self.assertGreater(projection["soldes_initiaux"]["GCP"], 20.0)

    def test_projection_jrtt_autorise_sous_zero(self) -> None:
        projection = orchestrer_projection(
            analyser_arguments(
                [
                    *self._arguments_communs(options_projection=True),
                    "--date-depart",
                    "2026-08-17",
                    "--date-fin",
                    "2026-08-21",
                ]
            )
        )
        self.assertEqual(projection["parametres_projection"]["soldes_minimums_par_code"]["JRTT"], -10.0)

    def test_lecture_json_avec_bom_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire_temporaire:
            chemin = Path(repertoire_temporaire) / "bom.json"
            chemin.write_text('{"source": "test"}', encoding="utf-8-sig")
            self.assertEqual(lire_json(chemin), {"source": "test"})

    def test_script_sans_sortie(self) -> None:
        resultat = subprocess.run(
            [sys.executable, "outils/chronotime/orchestrateur_projection.py", *self._arguments_communs()],
            check=True,
            capture_output=True,
            text=True,
        )
        projection = json.loads(resultat.stdout)
        self.assertEqual(projection["source"], "projection.demi_journees")

    def test_script_avec_sortie(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire_temporaire:
            chemin_sortie = Path(repertoire_temporaire) / "projection.json"
            subprocess.run(
                [
                    sys.executable,
                    "outils/chronotime/orchestrateur_projection.py",
                    *self._arguments_communs(),
                    "--sortie",
                    str(chemin_sortie),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            projection = json.loads(chemin_sortie.read_text(encoding="utf-8"))
            self.assertGreater(projection["resume"]["nombre_demi_journees"], 0)

    def _orchestrer_avec_date_cible(self) -> dict[str, object]:
        return orchestrer_projection(analyser_arguments(self._arguments_communs()))

    def _orchestrer_sans_date_cible(self) -> dict[str, object]:
        return orchestrer_projection(analyser_arguments(self._arguments_communs(sans_date_cible=True)))

    def _arguments_communs(self, sans_date_cible: bool = False, options_projection: bool = False) -> list[str]:
        arguments = [
            "--soldes",
            "donnees/exemples/soldes_absences_chronotime.exemple.json",
            "--agenda",
            "donnees/exemples/agenda_chronotime.exemple.json",
            "--obligations",
            "donnees/exemples/obligations_conges_2026.exemple.json",
            "--scenario",
            "donnees/exemples/scenario_simulation.exemple.json",
            "--date-depart",
            "2026-05-20",
            "--date-fin",
            "2026-12-31",
        ]
        if not sans_date_cible:
            arguments.extend(["--date-cible", "noel=Noël=2026-12-25"])
        if options_projection:
            arguments.extend(
                [
                    "--periodes-compteurs-par-code",
                    "GCP=suivant,JRTT=courant,CANC=courant",
                    "--soldes-minimums-par-code",
                    "JRTT=-10,GCP=0,CANC=0",
                    "--jours-non-decomptes",
                    "2026-12-25,2026-07-14",
                ]
            )
        return arguments


if __name__ == "__main__":
    unittest.main()
