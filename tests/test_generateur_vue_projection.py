from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from outils.chronotime.generateur_vue_projection import (
    charger_projection,
    formater_date_francaise,
    formater_periode_francaise,
    generer_html,
)


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

    def test_formatage_date_francaise(self) -> None:
        self.assertEqual(formater_date_francaise("2026-05-20"), "20 mai 2026")

    def test_formatage_periode_meme_annee(self) -> None:
        self.assertEqual(
            formater_periode_francaise("2026-05-20", "2026-12-31"),
            "du 20 mai au 31 décembre 2026",
        )

    def test_formatage_periode_deux_annees(self) -> None:
        self.assertEqual(
            formater_periode_francaise("2026-05-20", "2027-04-30"),
            "du 20 mai 2026 au 30 avril 2027",
        )

    def test_generation_html_contient_vues(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("Vue d’ensemble", html)
        self.assertIn("Frise", html)
        self.assertIn("Soldes", html)
        self.assertIn("Alertes", html)
        self.assertIn("Détails", html)
        self.assertIn("Technique", html)

    def test_generation_html_contient_navigation(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn('class="barre-vues"', html)
        self.assertIn('class="onglet onglet-actif"', html)
        self.assertIn('data-cible="vue-ensemble"', html)

    def test_premiere_vue_par_defaut_vue_ensemble(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn('id="vue-ensemble" class="vue-tableau-de-bord vue-active"', html)
        self.assertIn("activerVue('vue-ensemble')", html)

    def test_generation_html_informations_historiques(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("Soldes initiaux", html)
        self.assertIn("Soldes aux dates cibles", html)
        self.assertIn("Alertes globales", html)
        self.assertIn("Frise 1D des demi-journées", html)
        self.assertIn("Détails des demi-journées utiles", html)

    def test_generation_html_libelles_lisibles(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("Vue locale de projection Chronotime", html)
        self.assertIn("Solde minimum dépassé", html)
        self.assertIn("Événement hors période de projection", html)
        self.assertIn("Détails techniques", html)
        self.assertIn("Demi-journées projetées", html)
        self.assertIn("Événements sources", html)
        self.assertIn("Alertes globales", html)
        self.assertIn("Soldes initiaux", html)
        self.assertIn("Soldes aux dates cibles", html)

    def test_generation_html_dates_cibles_non_brutes(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("Contrôle exemple", html)
        self.assertIn("2 juin 2026", html)
        self.assertIn("<th>CANC</th><th>GCP</th><th>JRTT</th>", html)
        self.assertIn("<td>1,5 j</td><td>9 j</td><td>-1 j</td>", html)

    def test_generation_html_repere_mois_frise(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("mai 2026", html)
        self.assertIn("juin 2026", html)

    def test_generation_html_details_repliables(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("<details>", html)

    def test_generation_html_sans_ressource_externe(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)
        self.assertNotIn("<script src=", html)
        self.assertNotIn("<link rel=", html)

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
