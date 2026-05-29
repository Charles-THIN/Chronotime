from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from outils.chronotime.generateur_mouvements_soldes import generer_mouvements_soldes


class TestGenerateurMouvementsSoldes(unittest.TestCase):
    def test_projection_minimale_valide(self) -> None:
        mouvements = generer_mouvements_soldes(self._projection_minimale())
        self.assertEqual(mouvements["source"], "mouvements.soldes")

    def test_source_invalide_refusee(self) -> None:
        with self.assertRaisesRegex(ValueError, "projection.demi_journees"):
            generer_mouvements_soldes({"source": "autre"})

    def test_consommation_projection_produit_variation_negative(self) -> None:
        projection = self._projection_minimale()
        projection["demi_journees"].append(self._demi_journee("2026-08-10", "matin", 0.5))
        mouvement = generer_mouvements_soldes(projection)["mouvements"][0]
        self.assertEqual(mouvement["origine"], "consommation_projection")
        self.assertEqual(mouvement["variation"], -0.5)

    def test_consommation_projection_zero_ignoree(self) -> None:
        projection = self._projection_minimale()
        projection["demi_journees"].append(self._demi_journee("2026-08-10", "matin", 0.0))
        mouvements = generer_mouvements_soldes(projection)["mouvements"]
        self.assertEqual(mouvements, [])

    def test_credit_compteur_variation_positive(self) -> None:
        mouvement = self._mouvement_unique(self._evenement("credit_compteur", quantite=2.0))
        self.assertEqual(mouvement["variation"], 2.0)

    def test_expiration_compteur_variation_negative(self) -> None:
        mouvement = self._mouvement_unique(self._evenement("expiration_compteur", quantite=2.0))
        self.assertEqual(mouvement["variation"], -2.0)

    def test_ajustement_compteur_conserve_signe(self) -> None:
        mouvement = self._mouvement_unique(self._evenement("ajustement_compteur", quantite=-1.5))
        self.assertEqual(mouvement["variation"], -1.5)

    def test_ouverture_validite_informative(self) -> None:
        projection = self._projection_avec_evenement(self._evenement("ouverture_validite_compteur", quantite=None))
        resultat = generer_mouvements_soldes(projection)
        self.assertEqual(resultat["mouvements"], [])
        self.assertEqual(resultat["evenements_informatifs"][0]["type"], "ouverture_validite_compteur")

    def test_report_informatif_informatif(self) -> None:
        projection = self._projection_avec_evenement(self._report_informatif())
        resultat = generer_mouvements_soldes(projection)
        self.assertEqual(resultat["mouvements"], [])
        self.assertEqual(resultat["evenements_informatifs"][0]["mode_report"], "informatif")

    def test_report_operationnel_complet_produit_deux_mouvements(self) -> None:
        projection = self._projection_avec_evenement(self._report_operationnel())
        mouvements = generer_mouvements_soldes(projection)["mouvements"]
        self.assertEqual(len(mouvements), 2)
        self.assertEqual([mouvement["variation"] for mouvement in mouvements], [-1.0, 1.0])
        self.assertEqual(mouvements[0]["details"]["role_report"], "source")
        self.assertEqual(mouvements[1]["details"]["role_report"], "destination")

    def test_report_operationnel_incomplet_produit_alerte(self) -> None:
        evenement = self._report_operationnel()
        del evenement["periode_destination"]
        resultat = generer_mouvements_soldes(self._projection_avec_evenement(evenement))
        self.assertEqual(resultat["mouvements"], [])
        self.assertEqual(resultat["alertes"][0]["type"], "report_operationnel_incomplet")
        self.assertEqual(resultat["alertes"][0]["severite"], "bloquant")
        self.assertIn("periode_destination", resultat["alertes"][0]["champs_manquants"])

    def test_consommation_absence_evenement_compteur_alerte_non_dedoublonnee(self) -> None:
        projection = self._projection_avec_evenement(self._evenement("consommation_absence", quantite=0.5))
        resultat = generer_mouvements_soldes(projection)
        self.assertEqual(resultat["mouvements"][0]["variation"], -0.5)
        self.assertEqual(
            resultat["alertes"][0]["type"],
            "consommation_absence_evenement_compteur_non_dedoublonnee",
        )
        self.assertEqual(resultat["alertes"][0]["severite"], "information")

    def test_mouvements_tries_deterministiquement(self) -> None:
        projection = self._projection_minimale()
        projection["demi_journees"].append(self._demi_journee("2026-08-10", "apres_midi", 0.5))
        projection["evenements_compteurs"]["evenements"].append(self._evenement("credit_compteur", date="2026-06-01"))
        projection["demi_journees"].append(self._demi_journee("2026-08-10", "matin", 0.5))
        mouvements = generer_mouvements_soldes(projection)["mouvements"]
        self.assertEqual(
            [(mouvement["date"], mouvement["ordre"]) for mouvement in mouvements],
            [("2026-06-01", 0), ("2026-08-10", 10), ("2026-08-10", 20)],
        )

    def test_script_sans_sortie(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire:
            chemin = Path(repertoire) / "projection.json"
            chemin.write_text(json.dumps(self._projection_minimale()), encoding="utf-8")
            resultat = subprocess.run(
                [sys.executable, "outils/chronotime/generateur_mouvements_soldes.py", str(chemin)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(json.loads(resultat.stdout)["source"], "mouvements.soldes")

    def test_script_avec_sortie(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire:
            chemin = Path(repertoire) / "projection.json"
            sortie = Path(repertoire) / "mouvements.json"
            chemin.write_text(json.dumps(self._projection_minimale()), encoding="utf-8")
            subprocess.run(
                [
                    sys.executable,
                    "outils/chronotime/generateur_mouvements_soldes.py",
                    str(chemin),
                    "--sortie",
                    str(sortie),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(json.loads(sortie.read_text(encoding="utf-8"))["source"], "mouvements.soldes")

    def _mouvement_unique(self, evenement: dict[str, object]) -> dict[str, object]:
        mouvements = generer_mouvements_soldes(self._projection_avec_evenement(evenement))["mouvements"]
        self.assertEqual(len(mouvements), 1)
        return mouvements[0]

    def _projection_avec_evenement(self, evenement: dict[str, object]) -> dict[str, object]:
        projection = self._projection_minimale()
        projection["evenements_compteurs"]["evenements"].append(evenement)
        return projection

    def _projection_minimale(self) -> dict[str, object]:
        return {
            "source": "projection.demi_journees",
            "periode": {"debut": "2026-05-20", "fin": "2026-12-31"},
            "soldes_initiaux": {"GCP": 10.0},
            "evenements_compteurs": {
                "source": "evenements_compteurs.normalises",
                "evenements": [],
                "resume": {},
            },
            "demi_journees": [],
        }

    def _demi_journee(self, date: str, portion: str, quantite_appliquee: float) -> dict[str, object]:
        return {
            "date": date,
            "portion": portion,
            "consommations_detaillees": [
                {
                    "identifiant_evenement": f"absence_{date}_{portion}",
                    "source": "obligation",
                    "compteur": "GCP",
                    "quantite_demandee": 0.5,
                    "quantite_appliquee": quantite_appliquee,
                    "quantite_non_couverte": 0.0,
                    "priorite": 100,
                }
            ],
        }

    def _evenement(
        self,
        type_evenement: str,
        quantite: float | None = 1.0,
        date: str = "2026-06-01",
    ) -> dict[str, object]:
        evenement = {
            "identifiant": f"{type_evenement}_test",
            "type": type_evenement,
            "date_effet": date,
            "compteur": "GCP",
            "unite": "jour",
            "source": "test",
            "statut_certitude": "a_verifier",
            "notes": "",
        }
        if quantite is not None:
            evenement["quantite"] = quantite
        return evenement

    def _report_informatif(self) -> dict[str, object]:
        return {
            "identifiant": "report_informatif_test",
            "type": "report_compteur",
            "date_effet": "2026-12-31",
            "compteur": "GCP",
            "quantite": 1.0,
            "unite": "jour",
            "mode_report": "informatif",
        }

    def _report_operationnel(self) -> dict[str, object]:
        return {
            "identifiant": "report_operationnel_test",
            "type": "report_compteur",
            "date_effet": "2026-12-31",
            "compteur_source": "GCP",
            "periode_source": "courant",
            "compteur_destination": "GCP",
            "periode_destination": "suivant",
            "quantite": 1.0,
            "unite": "jour",
            "mode_report": "operationnel",
        }


if __name__ == "__main__":
    unittest.main()
