from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from outils.chronotime.generateur_vue_projection import charger_projection, generer_html


class TestGenerateurVueProjection(unittest.TestCase):
    def test_chargement_projection_valide(self) -> None:
        projection = charger_projection(self._chemin_exemple())
        self.assertEqual(projection["source"], "projection.demi_journees")

    def test_refus_source_invalide(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire:
            chemin = Path(repertoire) / "projection.json"
            donnees = copy.deepcopy(self._charger_exemple())
            donnees["source"] = "chronotime.agenda"
            chemin.write_text(json.dumps(donnees), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Source de projection invalide"):
                charger_projection(chemin)

    def test_generation_html(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("Vue locale de projection Chronotime", html)
        self.assertIn("Soldes initiaux", html)
        self.assertIn("GCP", html)
        self.assertIn("Contrôle exemple", html)
        self.assertIn("solde_minimum_depasse", html)
        self.assertIn("obligation_exemple_jrtt", html)
        self.assertIn("quantite_demandee", html)
        self.assertIn("quantite_appliquee", html)
        self.assertIn("quantite_non_couverte", html)

    def test_generation_fichier_html(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire:
            chemin_sortie = Path(repertoire) / "vue.html"
            subprocess.run(
                [
                    sys.executable,
                    "outils/chronotime/generateur_vue_projection.py",
                    "--projection",
                    str(self._chemin_exemple()),
                    "--sortie",
                    str(chemin_sortie),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            html = chemin_sortie.read_text(encoding="utf-8")
            self.assertIn("<!doctype html>", html)
            self.assertIn("Frise 1D des demi-journées", html)

    def test_tests_sans_donnees_locales(self) -> None:
        self.assertNotIn("donnees_locales", str(self._chemin_exemple()))

    def _chemin_exemple(self) -> Path:
        return Path("donnees/exemples/projection_demi_journees.exemple.json")

    def _charger_exemple(self) -> dict[str, object]:
        return json.loads(self._chemin_exemple().read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
