from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from outils.chronotime.chargeur_obligations import (
    SOURCE_ATTENDUE,
    normaliser_obligations,
)


class TestChargeurObligations(unittest.TestCase):
    def test_lecture_et_normalisation_exemple(self) -> None:
        donnees = self._charger_exemple_normalise()
        self.assertEqual(donnees["source"], SOURCE_ATTENDUE)
        self.assertEqual(donnees["annee"], 2026)

    def test_presence_six_obligations(self) -> None:
        self.assertEqual(len(self._charger_exemple_normalise()["obligations"]), 6)

    def test_quantite_totale(self) -> None:
        self.assertEqual(self._charger_exemple_normalise()["resume"]["quantite_totale"], 13.0)

    def test_quantite_preferee_jrtt(self) -> None:
        resume = self._charger_exemple_normalise()["resume"]
        self.assertEqual(resume["quantites_par_compteur_prefere"]["JRTT"], 4.0)

    def test_quantite_preferee_gcp(self) -> None:
        resume = self._charger_exemple_normalise()["resume"]
        self.assertEqual(resume["quantites_par_compteur_prefere"]["GCP"], 5.0)

    def test_quantite_sans_preference(self) -> None:
        resume = self._charger_exemple_normalise()["resume"]
        self.assertEqual(resume["quantites_par_compteur_prefere"]["sans_preference"], 4.0)

    def test_fermeture_ete(self) -> None:
        obligation = self._obligation("fermeture_ete_2026_08_10_2026_08_14")
        self.assertEqual(obligation["date_debut"], "2026-08-10")
        self.assertEqual(obligation["date_fin"], "2026-08-14")
        self.assertEqual(obligation["quantite"], 5.0)
        self.assertEqual(obligation["compteurs_autorises"], ["GCP"])

    def test_fermeture_noel(self) -> None:
        obligation = self._obligation("fermeture_noel_2026_12_25_2026_12_31")
        self.assertEqual(obligation["date_debut"], "2026-12-25")
        self.assertEqual(obligation["date_fin"], "2026-12-31")
        self.assertEqual(obligation["quantite"], 4.0)
        self.assertEqual(obligation["compteurs_autorises"], ["GCP", "JRTT", "CANC"])
        self.assertIsNone(obligation["compteur_prefere"])

    def test_rtt_25_mai(self) -> None:
        obligation = self._obligation("rtt_2026_05_25")
        self.assertEqual(obligation["compteurs_autorises"], ["JRTT"])
        self.assertEqual(obligation["duree_calculee"], {"unite": "jours_ouvres", "valeur": 1.0, "methode": "quantite_declaree"})

    def test_toutes_les_obligations_sont_en_jours_ouvres(self) -> None:
        donnees_brutes = self._charger_exemple_brut()
        self.assertTrue(all(obligation["unite"] == "jours_ouvres" for obligation in donnees_brutes["obligations"]))

    def test_script_sans_sortie(self) -> None:
        chemin_exemple = Path("donnees/exemples/obligations_conges_2026.exemple.json")
        resultat = subprocess.run(
            [sys.executable, "outils/chronotime/chargeur_obligations.py", str(chemin_exemple)],
            check=True,
            capture_output=True,
            text=True,
        )
        donnees = json.loads(resultat.stdout)
        self.assertEqual(donnees["resume"]["nombre_obligations"], 6)

    def test_script_avec_sortie(self) -> None:
        chemin_exemple = Path("donnees/exemples/obligations_conges_2026.exemple.json")
        with tempfile.TemporaryDirectory() as repertoire_temporaire:
            chemin_sortie = Path(repertoire_temporaire) / "obligations.json"
            subprocess.run(
                [
                    sys.executable,
                    "outils/chronotime/chargeur_obligations.py",
                    str(chemin_exemple),
                    "--sortie",
                    str(chemin_sortie),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            donnees = json.loads(chemin_sortie.read_text(encoding="utf-8"))
            self.assertEqual(donnees["source"], SOURCE_ATTENDUE)

    def _charger_exemple_brut(self) -> dict[str, object]:
        chemin_exemple = Path("donnees/exemples/obligations_conges_2026.exemple.json")
        return json.loads(chemin_exemple.read_text(encoding="utf-8"))

    def _charger_exemple_normalise(self) -> dict[str, object]:
        return normaliser_obligations(self._charger_exemple_brut())

    def _obligation(self, identifiant: str) -> dict[str, object]:
        donnees = self._charger_exemple_normalise()
        return next(
            obligation
            for obligation in donnees["obligations"]
            if obligation["identifiant"] == identifiant
        )


if __name__ == "__main__":
    unittest.main()
