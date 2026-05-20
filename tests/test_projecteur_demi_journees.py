from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from outils.chronotime.projecteur_demi_journees import (
    creer_vecteur_demi_journees,
    extraire_soldes_initiaux,
    projeter_demi_journees,
)


class TestProjecteurDemiJournees(unittest.TestCase):
    def test_extraction_des_soldes_initiaux(self) -> None:
        donnees = self._charger_entrees()
        self.assertEqual(extraire_soldes_initiaux(donnees, "courant"), {"GCP": 20.0, "JRTT": 4.0, "CANC": 5.0})

    def test_creation_deux_demi_journees_par_date(self) -> None:
        demi_journees = creer_vecteur_demi_journees("2026-05-20", "2026-05-21")
        self.assertEqual(len(demi_journees), 4)

    def test_presence_matin_et_apres_midi(self) -> None:
        demi_journees = creer_vecteur_demi_journees("2026-05-20", "2026-05-20")
        self.assertEqual([demi_journee["portion"] for demi_journee in demi_journees], ["matin", "apres_midi"])

    def test_projection_obligation_jrtt_un_jour(self) -> None:
        projection = self._projeter_exemple()
        demi_journees = self._demi_journees_pour_evenement(projection, "rtt_2026_05_25")
        self.assertEqual(len(demi_journees), 2)
        self.assertEqual(sum(demi_journee["consommations"]["JRTT"] for demi_journee in demi_journees), 1.0)

    def test_projection_fermeture_ete_gcp_cinq_jours(self) -> None:
        projection = self._projeter_exemple()
        demi_journees = self._demi_journees_pour_evenement(projection, "fermeture_ete_2026_08_10_2026_08_14")
        self.assertEqual(len(demi_journees), 10)
        self.assertEqual(sum(demi_journee["consommations"]["GCP"] for demi_journee in demi_journees), 5.0)

    def test_projection_noel_limitee_a_quatre_jours(self) -> None:
        projection = self._projeter_exemple()
        demi_journees = self._demi_journees_pour_evenement(projection, "fermeture_noel_2026_12_25_2026_12_31")
        self.assertEqual(len(demi_journees), 8)
        self.assertNotIn("2026-12-31", {demi_journee["date"] for demi_journee in demi_journees})
        self.assertEqual(sum(demi_journee["consommations"]["CANC"] for demi_journee in demi_journees), 4.0)

    def test_exclusion_bloc_scenario_inactif(self) -> None:
        projection = self._projeter_exemple()
        identifiants = {evenement["identifiant"] for evenement in projection["evenements_sources"]}
        self.assertIn("bloc_scenario_gcp", identifiants)
        self.assertNotIn("bloc_scenario_desactive", identifiants)

    def test_consommation_solde_suffisant(self) -> None:
        projection = self._projeter_exemple()
        self.assertEqual(projection["resume"]["nombre_alertes"], 0)
        self.assertEqual(self._demi_journee(projection, "2026-05-25", "apres_midi")["soldes_apres"]["JRTT"], 3.0)

    def test_alerte_solde_insuffisant(self) -> None:
        donnees = self._charger_entrees()
        donnees["soldes"]["compteurs"][1]["periodes"]["courant"]["solde"]["valeur"] = 0.25
        donnees["parametres_projection"]["date_depart"] = "2026-05-25"
        donnees["parametres_projection"]["date_fin"] = "2026-05-25"
        donnees["verification_obligations"]["obligations"] = [
            obligation
            for obligation in donnees["verification_obligations"]["obligations"]
            if obligation["identifiant"] == "rtt_2026_05_25"
        ]
        donnees["verification_obligations"]["obligations"][0]["quantite_requise"] = 0.5
        donnees["verification_obligations"]["obligations"][0]["quantite_restante"] = 0.5
        donnees["scenario"]["scenario"]["blocs"] = []
        donnees["parametres_projection"]["dates_cibles"] = []

        projection = projeter_demi_journees(donnees)
        self.assertEqual(projection["resume"]["nombre_alertes"], 1)
        self.assertEqual(projection["alertes"][0]["type"], "solde_insuffisant")
        self.assertEqual(projection["alertes"][0]["quantite_non_couverte"], 0.25)

    def test_soldes_a_la_date_cible_noel(self) -> None:
        projection = self._projeter_exemple()
        soldes_noel = projection["soldes_aux_dates_cibles"][0]["soldes"]
        self.assertEqual(soldes_noel, {"GCP": 13.0, "JRTT": 3.0, "CANC": 4.0})

    def test_script_sans_sortie(self) -> None:
        resultat = subprocess.run(
            [
                sys.executable,
                "outils/chronotime/projecteur_demi_journees.py",
                "donnees/exemples/projection_demi_journees_entrees.exemple.json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        donnees = json.loads(resultat.stdout)
        self.assertEqual(donnees["source"], "projection.demi_journees")

    def test_script_avec_sortie(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire_temporaire:
            chemin_sortie = Path(repertoire_temporaire) / "projection.json"
            subprocess.run(
                [
                    sys.executable,
                    "outils/chronotime/projecteur_demi_journees.py",
                    "donnees/exemples/projection_demi_journees_entrees.exemple.json",
                    "--sortie",
                    str(chemin_sortie),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            donnees = json.loads(chemin_sortie.read_text(encoding="utf-8"))
            self.assertEqual(donnees["resume"]["nombre_evenements_sources"], 4)

    def _charger_entrees(self) -> dict[str, object]:
        chemin = Path("donnees/exemples/projection_demi_journees_entrees.exemple.json")
        return json.loads(chemin.read_text(encoding="utf-8"))

    def _projeter_exemple(self) -> dict[str, object]:
        return projeter_demi_journees(copy.deepcopy(self._charger_entrees()))

    def _demi_journees_pour_evenement(self, projection: dict[str, object], identifiant: str) -> list[dict[str, object]]:
        return [
            demi_journee
            for demi_journee in projection["demi_journees"]
            if any(evenement["identifiant"] == identifiant for evenement in demi_journee["evenements"])
        ]

    def _demi_journee(self, projection: dict[str, object], date: str, portion: str) -> dict[str, object]:
        return next(
            demi_journee
            for demi_journee in projection["demi_journees"]
            if demi_journee["date"] == date and demi_journee["portion"] == portion
        )


if __name__ == "__main__":
    unittest.main()
