from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from outils.chronotime.verificateur_obligations import verifier_obligations


class TestVerificateurObligations(unittest.TestCase):
    def test_lecture_des_fichiers_exemple(self) -> None:
        verification = self._charger_verification()
        self.assertEqual(verification["source"], "verification.obligations")
        self.assertEqual(verification["resume"]["nombre_obligations"], 6)

    def test_rtt_25_mai_satisfaite(self) -> None:
        obligation = self._obligation("rtt_2026_05_25")
        self.assertEqual(obligation["statut_obligation"], "satisfaite")
        self.assertEqual(obligation["quantite_satisfaite"], 1.0)
        self.assertEqual(obligation["evenements_compatibles"][0]["code"], "JRTT")

    def test_rtt_13_juillet_a_poser(self) -> None:
        obligation = self._obligation("rtt_2026_07_13")
        self.assertEqual(obligation["statut_obligation"], "a_poser")
        self.assertEqual(obligation["quantite_satisfaite"], 0.0)

    def test_fermeture_ete_partielle(self) -> None:
        obligation = self._obligation("fermeture_ete_2026_08_10_2026_08_14")
        self.assertEqual(obligation["statut_obligation"], "partielle")
        self.assertEqual(obligation["quantite_requise"], 5.0)
        self.assertEqual(obligation["quantite_satisfaite"], 3.0)
        self.assertEqual(obligation["quantite_restante"], 2.0)

    def test_code_non_autorise_ignore(self) -> None:
        obligation = self._obligation("fermeture_ete_2026_08_10_2026_08_14")
        codes = [evenement["code"] for evenement in obligation["evenements_compatibles"]]
        self.assertNotIn("TELV", codes)

    def test_resume_global(self) -> None:
        resume = self._charger_verification()["resume"]
        self.assertEqual(resume["nombre_satisfaites"], 1)
        self.assertEqual(resume["nombre_partielles"], 1)
        self.assertEqual(resume["nombre_a_poser"], 4)
        self.assertEqual(resume["quantite_totale_requise"], 13.0)
        self.assertEqual(resume["quantite_totale_satisfaite"], 4.0)
        self.assertEqual(resume["quantite_totale_restante"], 9.0)

    def test_script_sans_sortie(self) -> None:
        resultat = subprocess.run(
            [
                sys.executable,
                "outils/chronotime/verificateur_obligations.py",
                "donnees/exemples/obligations_conges_2026.exemple.json",
                "donnees/exemples/agenda_obligations_chronotime.exemple.json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        donnees = json.loads(resultat.stdout)
        self.assertEqual(donnees["source"], "verification.obligations")

    def test_script_avec_sortie(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire_temporaire:
            chemin_sortie = Path(repertoire_temporaire) / "verification.json"
            subprocess.run(
                [
                    sys.executable,
                    "outils/chronotime/verificateur_obligations.py",
                    "donnees/exemples/obligations_conges_2026.exemple.json",
                    "donnees/exemples/agenda_obligations_chronotime.exemple.json",
                    "--sortie",
                    str(chemin_sortie),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            donnees = json.loads(chemin_sortie.read_text(encoding="utf-8"))
            self.assertEqual(donnees["resume"]["nombre_obligations"], 6)

    def _charger_verification(self) -> dict[str, object]:
        obligations = json.loads(Path("donnees/exemples/obligations_conges_2026.exemple.json").read_text(encoding="utf-8"))
        agenda = json.loads(Path("donnees/exemples/agenda_obligations_chronotime.exemple.json").read_text(encoding="utf-8"))
        return verifier_obligations(obligations, agenda)

    def _obligation(self, identifiant: str) -> dict[str, object]:
        verification = self._charger_verification()
        return next(obligation for obligation in verification["obligations"] if obligation["identifiant"] == identifiant)


if __name__ == "__main__":
    unittest.main()
