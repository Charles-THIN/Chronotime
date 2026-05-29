from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from outils.chronotime.generateur_synthese_planification import generer_synthese_planification


class TestGenerateurSynthesePlanification(unittest.TestCase):
    def test_source_projection_invalide_refusee(self) -> None:
        projection = self._projection()
        projection["source"] = "autre"
        with self.assertRaisesRegex(ValueError, "projection.demi_journees"):
            generer_synthese_planification(projection, self._mouvements(), self._chronologie())

    def test_source_mouvements_invalide_refusee(self) -> None:
        mouvements = self._mouvements()
        mouvements["source"] = "autre"
        with self.assertRaisesRegex(ValueError, "mouvements.soldes"):
            generer_synthese_planification(self._projection(), mouvements, self._chronologie())

    def test_source_chronologie_invalide_refusee(self) -> None:
        chronologie = self._chronologie()
        chronologie["source"] = "autre"
        with self.assertRaisesRegex(ValueError, "chronologie.soldes"):
            generer_synthese_planification(self._projection(), self._mouvements(), chronologie)

    def test_sortie_source_synthese_planification(self) -> None:
        synthese = generer_synthese_planification(self._projection(), self._mouvements(), self._chronologie())
        self.assertEqual(synthese["source"], "synthese.planification")

    def test_agregation_soldes_initiaux_et_finaux(self) -> None:
        synthese = generer_synthese_planification(self._projection(), self._mouvements(), self._chronologie())
        self.assertEqual(synthese["resume_global"]["jours_initiaux_agreges"], 25.0)
        self.assertEqual(synthese["resume_global"]["jours_finaux_agreges"], 16.5)

    def test_consommation_absence_classee_jours_consommes(self) -> None:
        synthese = generer_synthese_planification(self._projection(), self._mouvements(), self._chronologie())
        self.assertEqual(synthese["resume_global"]["jours_consommes"], 3.0)

    def test_expiration_classee_jours_expires(self) -> None:
        synthese = generer_synthese_planification(self._projection(), self._mouvements(), self._chronologie())
        self.assertEqual(synthese["resume_global"]["jours_expires"], 2.0)

    def test_credit_classe_jours_credites(self) -> None:
        synthese = generer_synthese_planification(self._projection(), self._mouvements(), self._chronologie())
        self.assertEqual(synthese["resume_global"]["jours_credites"], 1.0)

    def test_ajustement_negatif_classe_debit_technique(self) -> None:
        synthese = generer_synthese_planification(self._projection(), self._mouvements(), self._chronologie())
        self.assertEqual(synthese["resume_global"]["jours_debites_techniques"], 0.5)

    def test_regroupement_consommations_par_evenement(self) -> None:
        synthese = generer_synthese_planification(self._projection(), self._mouvements(), self._chronologie())
        consommations = synthese["consommations_par_evenement"]
        self.assertEqual(consommations[0]["identifiant"], "bloc_ete")
        self.assertEqual(consommations[0]["jours_consommes"], 3.0)
        self.assertEqual(consommations[0]["premiere_date"], "2026-08-10")
        self.assertEqual(consommations[0]["derniere_date"], "2026-08-11")
        self.assertEqual(consommations[0]["compteurs_techniques"], {"GCP": -3.0})

    def test_dates_cibles_agregees(self) -> None:
        synthese = generer_synthese_planification(self._projection(), self._mouvements(), self._chronologie())
        self.assertEqual(synthese["soldes_agreges_aux_dates_cibles"][0]["identifiant"], "noel")
        self.assertEqual(synthese["soldes_agreges_aux_dates_cibles"][0]["jours_restants_agreges"], 14.0)

    def test_signal_compteur_sous_seuil_technique_suppose(self) -> None:
        synthese = generer_synthese_planification(self._projection(), self._mouvements(), self._chronologie_bloquante())
        types = [signal["type"] for signal in synthese["signaux"]]
        self.assertIn("compteur_sous_seuil_technique_suppose", types)

    def test_signal_unite_non_agregee(self) -> None:
        mouvements = self._mouvements()
        mouvements["mouvements"].append(
            {
                "date": "2026-09-01",
                "type": "consommation_absence",
                "identifiant": "heure",
                "compteur": "GCP",
                "variation": -7.0,
                "unite": "heure",
            }
        )
        synthese = generer_synthese_planification(self._projection(), mouvements, self._chronologie())
        types = [signal["type"] for signal in synthese["signaux"]]
        self.assertIn("unite_non_agregee", types)
        self.assertEqual(synthese["resume_global"]["jours_consommes"], 3.0)

    def test_signal_jours_expires(self) -> None:
        synthese = generer_synthese_planification(self._projection(), self._mouvements(), self._chronologie())
        types = [signal["type"] for signal in synthese["signaux"]]
        self.assertIn("jours_expires", types)

    def test_statut_ok_sans_signal_bloquant_ni_attention(self) -> None:
        synthese = generer_synthese_planification(self._projection(), self._mouvements_ok(), self._chronologie_ok())
        self.assertEqual(synthese["resume_global"]["statut"], "ok")

    def test_statut_bloquant_avec_signal_bloquant(self) -> None:
        synthese = generer_synthese_planification(self._projection(), self._mouvements(), self._chronologie_bloquante())
        self.assertEqual(synthese["resume_global"]["statut"], "bloquant")

    def test_cli_avec_sortie(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire:
            rep = Path(repertoire)
            chemin_projection = rep / "projection.json"
            chemin_mouvements = rep / "mouvements.json"
            chemin_chronologie = rep / "chronologie.json"
            chemin_sortie = rep / "synthese.json"
            chemin_projection.write_text(json.dumps(self._projection()), encoding="utf-8")
            chemin_mouvements.write_text(json.dumps(self._mouvements()), encoding="utf-8")
            chemin_chronologie.write_text(json.dumps(self._chronologie()), encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    "outils/chronotime/generateur_synthese_planification.py",
                    "--projection",
                    str(chemin_projection),
                    "--mouvements",
                    str(chemin_mouvements),
                    "--chronologie",
                    str(chemin_chronologie),
                    "--sortie",
                    str(chemin_sortie),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            donnees = json.loads(chemin_sortie.read_text(encoding="utf-8"))
            self.assertEqual(donnees["source"], "synthese.planification")

    def _projection(self) -> dict[str, object]:
        return {
            "source": "projection.demi_journees",
            "periode": {"debut": "2026-05-20", "fin": "2026-12-31"},
            "parametres_projection": {"soldes_minimums_par_code": {"GCP": 0.0, "CANC": 0.0}},
            "soldes_aux_dates_cibles": [
                {
                    "identifiant": "noel",
                    "libelle": "Noël",
                    "date": "2026-12-25",
                    "soldes": {"GCP": 10.0, "JRTT": 4.0, "texte": "ignore"},
                }
            ],
            "alertes": [],
        }

    def _mouvements(self) -> dict[str, object]:
        return {
            "source": "mouvements.soldes",
            "periode": {"debut": "2026-05-20", "fin": "2026-12-31"},
            "mouvements": [
                self._mouvement("2026-08-10", "consommation_absence", "bloc_ete", "GCP", -1.5),
                self._mouvement("2026-08-11", "consommation_absence", "bloc_ete", "GCP", -1.5),
                self._mouvement("2026-10-01", "expiration_compteur", "expiration_gcp", "GCP", -2.0),
                self._mouvement("2026-06-01", "credit_compteur", "credit_gcp", "GCP", 1.0),
                self._mouvement("2026-07-01", "ajustement_compteur", "ajustement_gcp", "GCP", -0.5),
            ],
            "alertes": [],
        }

    def _mouvements_ok(self) -> dict[str, object]:
        mouvements = copy.deepcopy(self._mouvements())
        mouvements["mouvements"] = [
            self._mouvement("2026-08-10", "consommation_absence", "bloc_ete", "GCP", -1.0)
        ]
        return mouvements

    def _mouvement(
        self,
        date: str,
        type_mouvement: str,
        identifiant: str,
        compteur: str,
        variation: float,
    ) -> dict[str, object]:
        return {
            "date": date,
            "ordre": 10,
            "origine": "consommation_projection",
            "type": type_mouvement,
            "identifiant": identifiant,
            "compteur": compteur,
            "variation": variation,
            "unite": "jour",
        }

    def _chronologie(self) -> dict[str, object]:
        return {
            "source": "chronologie.soldes",
            "periode": {"debut": "2026-05-20", "fin": "2026-12-31"},
            "soldes_initiaux": {"GCP": 20.0, "JRTT": 5.0},
            "soldes_finaux": {"GCP": 11.5, "JRTT": 5.0},
            "points_chronologie": [],
            "alertes": [],
        }

    def _chronologie_ok(self) -> dict[str, object]:
        chronologie = self._chronologie()
        chronologie["soldes_finaux"] = {"GCP": 19.0, "JRTT": 5.0}
        return chronologie

    def _chronologie_bloquante(self) -> dict[str, object]:
        chronologie = self._chronologie()
        chronologie["soldes_finaux"] = {"GCP": -1.0, "JRTT": 5.0}
        return chronologie


if __name__ == "__main__":
    unittest.main()
