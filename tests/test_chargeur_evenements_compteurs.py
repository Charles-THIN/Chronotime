from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from outils.chronotime.chargeur_evenements_compteurs import (
    SOURCE_NORMALISEE,
    lire_json,
    normaliser_evenements_compteurs,
)


class TestChargeurEvenementsCompteurs(unittest.TestCase):
    def test_fichier_exemple_se_charge_et_se_normalise(self) -> None:
        donnees = self._charger_exemple_normalise()
        self.assertEqual(donnees["source"], SOURCE_NORMALISEE)
        self.assertEqual(len(donnees["evenements"]), 5)

    def test_sortie_contient_structure_stable(self) -> None:
        donnees = self._charger_exemple_normalise()
        self.assertIn("source", donnees)
        self.assertIn("evenements", donnees)
        self.assertIn("resume", donnees)

    def test_types_presents_dans_exemple_acceptes(self) -> None:
        types = {evenement["type"] for evenement in self._charger_exemple_normalise()["evenements"]}
        self.assertEqual(
            types,
            {
                "credit_compteur",
                "ouverture_validite_compteur",
                "expiration_compteur",
                "report_compteur",
                "ajustement_compteur",
            },
        )

    def test_consommation_absence_acceptee(self) -> None:
        donnees = self._donnees_minimales({"type": "consommation_absence"})
        evenement = normaliser_evenements_compteurs(donnees)["evenements"][0]
        self.assertEqual(evenement["type"], "consommation_absence")

    def test_report_compteur_conserve_source_et_destination(self) -> None:
        donnees = self._donnees_minimales(
            {
                "type": "report_compteur",
                "compteur": "",
                "compteur_source": "GCP",
                "periode_source": "courant",
                "compteur_destination": "GCP",
                "periode_destination": "suivant",
            }
        )
        evenement = normaliser_evenements_compteurs(donnees)["evenements"][0]
        self.assertEqual(evenement["compteur_source"], "GCP")
        self.assertEqual(evenement["periode_source"], "courant")
        self.assertEqual(evenement["compteur_destination"], "GCP")
        self.assertEqual(evenement["periode_destination"], "suivant")

    def test_type_inconnu_provoque_erreur(self) -> None:
        donnees = self._donnees_minimales({"type": "type_inconnu"})
        with self.assertRaisesRegex(ValueError, "Type d'événement de compteur inconnu"):
            normaliser_evenements_compteurs(donnees)

    def test_identifiant_manquant_provoque_erreur(self) -> None:
        donnees = self._donnees_minimales({"identifiant": ""})
        with self.assertRaisesRegex(ValueError, "identifiant"):
            normaliser_evenements_compteurs(donnees)

    def test_date_invalide_provoque_erreur(self) -> None:
        donnees = self._donnees_minimales({"date_effet": "2026-99-99"})
        with self.assertRaisesRegex(ValueError, "Date ISO invalide"):
            normaliser_evenements_compteurs(donnees)

    def test_date_normalisee_stricte(self) -> None:
        evenement = self._charger_exemple_normalise()["evenements"][0]
        self.assertEqual(evenement["date_effet"], "2026-06-01")

    def test_quantite_numerique_normalisee_en_float(self) -> None:
        evenement = self._charger_exemple_normalise()["evenements"][0]
        self.assertIsInstance(evenement["quantite"], float)
        self.assertEqual(evenement["quantite"], 2.0)

    def test_compteur_obligatoire_pour_types_a_compteur_unique(self) -> None:
        for type_evenement in (
            "credit_compteur",
            "ouverture_validite_compteur",
            "expiration_compteur",
            "ajustement_compteur",
            "consommation_absence",
        ):
            with self.subTest(type_evenement=type_evenement):
                donnees = self._donnees_minimales({"type": type_evenement, "compteur": "   "})
                with self.assertRaisesRegex(ValueError, f"Le type '{type_evenement}' exige"):
                    normaliser_evenements_compteurs(donnees)

    def test_report_compteur_avec_compteur_simple_accepte(self) -> None:
        donnees = self._donnees_minimales({"type": "report_compteur", "compteur": "GCP"})
        evenement = normaliser_evenements_compteurs(donnees)["evenements"][0]
        self.assertEqual(evenement["compteur"], "GCP")

    def test_report_compteur_sans_compteur_ni_source_destination_refuse(self) -> None:
        donnees = self._donnees_minimales({"type": "report_compteur", "compteur": ""})
        with self.assertRaisesRegex(ValueError, "report_compteur"):
            normaliser_evenements_compteurs(donnees)

    def test_quantite_obligatoire_pour_types_quantifies(self) -> None:
        for type_evenement in (
            "credit_compteur",
            "expiration_compteur",
            "report_compteur",
            "ajustement_compteur",
            "consommation_absence",
        ):
            with self.subTest(type_evenement=type_evenement):
                surcharge = {"type": type_evenement, "quantite": None}
                if type_evenement == "report_compteur":
                    surcharge["compteur"] = "GCP"
                donnees = self._donnees_minimales(surcharge)
                with self.assertRaisesRegex(ValueError, f"Le type '{type_evenement}' exige une quantité"):
                    normaliser_evenements_compteurs(donnees)

    def test_ouverture_validite_sans_quantite_acceptee(self) -> None:
        donnees = self._donnees_minimales({"type": "ouverture_validite_compteur", "quantite": None, "unite": None})
        evenement = normaliser_evenements_compteurs(donnees)["evenements"][0]
        self.assertEqual(evenement["type"], "ouverture_validite_compteur")
        self.assertNotIn("quantite", evenement)

    def test_resume_compte_evenements_par_type(self) -> None:
        resume = self._charger_exemple_normalise()["resume"]
        self.assertEqual(resume["nombre_evenements"], 5)
        self.assertEqual(resume["nombres_par_type"]["credit_compteur"], 1)
        self.assertEqual(resume["nombres_par_type"]["expiration_compteur"], 1)

    def test_resume_agrege_quantites_par_compteur(self) -> None:
        quantites = self._charger_exemple_normalise()["resume"]["quantites_par_compteur"]
        self.assertEqual(quantites["GCP"], 1.5)
        self.assertEqual(quantites["CANC"], -1.0)
        self.assertNotIn("JRTT", quantites)

    def test_lecture_bom_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire:
            chemin = Path(repertoire) / "evenements.json"
            chemin.write_text("\ufeff" + json.dumps(self._charger_exemple_brut()), encoding="utf-8")
            donnees = lire_json(chemin)
            self.assertEqual(donnees["source"], "simulation.evenements_compteurs")

    def test_script_sans_sortie(self) -> None:
        resultat = subprocess.run(
            [sys.executable, "outils/chronotime/chargeur_evenements_compteurs.py", str(self._chemin_exemple())],
            check=True,
            capture_output=True,
            text=True,
        )
        donnees = json.loads(resultat.stdout)
        self.assertEqual(donnees["source"], SOURCE_NORMALISEE)

    def test_script_avec_sortie(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire:
            chemin_sortie = Path(repertoire) / "evenements_normalises.json"
            subprocess.run(
                [
                    sys.executable,
                    "outils/chronotime/chargeur_evenements_compteurs.py",
                    str(self._chemin_exemple()),
                    "--sortie",
                    str(chemin_sortie),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            donnees = json.loads(chemin_sortie.read_text(encoding="utf-8"))
            self.assertEqual(donnees["source"], SOURCE_NORMALISEE)

    def _donnees_minimales(self, surcharge: dict[str, object]) -> dict[str, object]:
        evenement = {
            "identifiant": "evt_test",
            "type": "credit_compteur",
            "date_effet": "2026-06-01",
            "compteur": "GCP",
            "quantite": 1,
            "unite": "jour",
        }
        evenement.update(surcharge)
        return {"source": "test", "evenements_compteurs": [evenement]}

    def _chemin_exemple(self) -> Path:
        return Path("donnees/exemples/evenements_compteurs.exemple.json")

    def _charger_exemple_brut(self) -> dict[str, object]:
        return json.loads(self._chemin_exemple().read_text(encoding="utf-8"))

    def _charger_exemple_normalise(self) -> dict[str, object]:
        return normaliser_evenements_compteurs(self._charger_exemple_brut())


if __name__ == "__main__":
    unittest.main()
