from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from outils.chronotime.generateur_chronologie_soldes import generer_chronologie_soldes


class TestGenerateurChronologieSoldes(unittest.TestCase):
    def test_projection_et_mouvements_minimaux(self) -> None:
        chronologie = generer_chronologie_soldes(self._projection(), self._mouvements([]))
        self.assertEqual(chronologie["source"], "chronologie.soldes")

    def test_projection_source_invalide_refusee(self) -> None:
        with self.assertRaisesRegex(ValueError, "projection.demi_journees"):
            generer_chronologie_soldes({"source": "autre"}, self._mouvements([]))

    def test_mouvements_source_invalide_refusee(self) -> None:
        with self.assertRaisesRegex(ValueError, "mouvements.soldes"):
            generer_chronologie_soldes(self._projection(), {"source": "autre"})

    def test_mouvement_gcp_diminue_solde(self) -> None:
        chronologie = generer_chronologie_soldes(self._projection(), self._mouvements([self._mouvement(-0.5)]))
        point = chronologie["points_chronologie"][0]
        self.assertEqual(point["soldes_avant"]["GCP"], 20.0)
        self.assertEqual(point["soldes_apres"]["GCP"], 19.5)

    def test_deux_mouvements_successifs_sont_cumules(self) -> None:
        chronologie = generer_chronologie_soldes(
            self._projection(),
            self._mouvements([self._mouvement(-0.5), self._mouvement(-1.0, identifiant="mouvement_2")]),
        )
        self.assertEqual(chronologie["soldes_finaux"]["GCP"], 18.5)

    def test_compteur_absent_initialise_zero_et_alerte(self) -> None:
        chronologie = generer_chronologie_soldes(
            self._projection(),
            self._mouvements([self._mouvement(1.0, compteur="RECU")]),
        )
        self.assertEqual(chronologie["points_chronologie"][0]["soldes_avant"]["RECU"], 0.0)
        self.assertEqual(chronologie["soldes_finaux"]["RECU"], 1.0)
        self.assertEqual(chronologie["alertes"][0]["type"], "compteur_absent_des_soldes_initiaux")
        self.assertEqual(chronologie["alertes"][0]["severite"], "information")

    def test_mouvement_sans_compteur_ignore(self) -> None:
        mouvement = self._mouvement(-0.5)
        mouvement["compteur"] = ""
        chronologie = generer_chronologie_soldes(self._projection(), self._mouvements([mouvement]))
        self.assertEqual(chronologie["points_chronologie"], [])
        self.assertEqual(chronologie["alertes"][0]["type"], "mouvement_invalide_ignore")

    def test_mouvement_sans_variation_numerique_ignore(self) -> None:
        mouvement = self._mouvement(-0.5)
        mouvement["variation"] = "x"
        chronologie = generer_chronologie_soldes(self._projection(), self._mouvements([mouvement]))
        self.assertEqual(chronologie["points_chronologie"], [])
        self.assertEqual(chronologie["alertes"][0]["raison"], "compteur_ou_variation_invalide")

    def test_alertes_existantes_conservees(self) -> None:
        mouvements = self._mouvements(
            [self._mouvement(-0.5)],
            alertes=[{"type": "alerte_existante", "severite": "information"}],
        )
        chronologie = generer_chronologie_soldes(self._projection(), mouvements)
        self.assertEqual(chronologie["alertes"][0]["type"], "alerte_existante")

    def test_mouvements_tries_avant_application(self) -> None:
        mouvements = [
            self._mouvement(-1.0, date="2026-08-10", portion="apres_midi", ordre=20, identifiant="apres"),
            self._mouvement(-0.5, date="2026-06-01", portion=None, ordre=0, identifiant="avant"),
            self._mouvement(-0.25, date="2026-08-10", portion="matin", ordre=10, identifiant="matin"),
        ]
        chronologie = generer_chronologie_soldes(self._projection(), self._mouvements(mouvements))
        self.assertEqual(
            [(point["date"], point["ordre"]) for point in chronologie["points_chronologie"]],
            [("2026-06-01", 0), ("2026-08-10", 10), ("2026-08-10", 20)],
        )
        self.assertEqual(chronologie["soldes_finaux"]["GCP"], 18.25)

    def test_details_conserves(self) -> None:
        mouvement = self._mouvement(-0.5)
        mouvement["details"] = {"role_report": "source"}
        chronologie = generer_chronologie_soldes(self._projection(), self._mouvements([mouvement]))
        self.assertEqual(chronologie["points_chronologie"][0]["details"]["role_report"], "source")

    def test_soldes_finaux_correspondent_au_dernier_etat(self) -> None:
        chronologie = generer_chronologie_soldes(
            self._projection(),
            self._mouvements([self._mouvement(-0.5), self._mouvement(2.0, compteur="JRTT")]),
        )
        self.assertEqual(chronologie["soldes_finaux"], {"GCP": 19.5, "JRTT": 6.0})

    def test_script_sans_sortie(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire:
            projection, mouvements, _ = self._ecrire_entrees(Path(repertoire))
            resultat = subprocess.run(
                [
                    sys.executable,
                    "outils/chronotime/generateur_chronologie_soldes.py",
                    "--projection",
                    str(projection),
                    "--mouvements",
                    str(mouvements),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(json.loads(resultat.stdout)["source"], "chronologie.soldes")

    def test_script_avec_sortie(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire:
            projection, mouvements, sortie = self._ecrire_entrees(Path(repertoire))
            subprocess.run(
                [
                    sys.executable,
                    "outils/chronotime/generateur_chronologie_soldes.py",
                    "--projection",
                    str(projection),
                    "--mouvements",
                    str(mouvements),
                    "--sortie",
                    str(sortie),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(json.loads(sortie.read_text(encoding="utf-8"))["source"], "chronologie.soldes")

    def _projection(self) -> dict[str, object]:
        return {
            "source": "projection.demi_journees",
            "periode": {"debut": "2026-05-20", "fin": "2026-12-31"},
            "soldes_initiaux": {"GCP": 20.0, "JRTT": 4.0},
        }

    def _mouvements(
        self,
        mouvements: list[dict[str, object]],
        alertes: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        return {
            "source": "mouvements.soldes",
            "periode": {"debut": "2026-05-20", "fin": "2026-12-31"},
            "mouvements": mouvements,
            "alertes": alertes or [],
        }

    def _mouvement(
        self,
        variation: float,
        compteur: str = "GCP",
        date: str = "2026-08-10",
        portion: str | None = "matin",
        ordre: int = 10,
        identifiant: str = "mouvement_1",
    ) -> dict[str, object]:
        mouvement = {
            "date": date,
            "ordre": ordre,
            "origine": "consommation_projection",
            "type": "consommation_absence",
            "identifiant": identifiant,
            "compteur": compteur,
            "variation": variation,
            "unite": "jour",
            "details": {"source": "test"},
        }
        if portion is not None:
            mouvement["portion"] = portion
        return mouvement

    def _ecrire_entrees(self, repertoire: Path) -> tuple[Path, Path, Path]:
        projection = repertoire / "projection.json"
        mouvements = repertoire / "mouvements.json"
        sortie = repertoire / "chronologie.json"
        projection.write_text(json.dumps(self._projection()), encoding="utf-8")
        mouvements.write_text(json.dumps(self._mouvements([self._mouvement(-0.5)])), encoding="utf-8")
        return projection, mouvements, sortie


if __name__ == "__main__":
    unittest.main()
