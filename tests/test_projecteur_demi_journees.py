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

    def test_extraction_avec_periode_globale(self) -> None:
        donnees = self._donnees_soldes_periodes()
        self.assertEqual(extraire_soldes_initiaux(donnees, "suivant")["GCP"], 23.96)

    def test_extraction_avec_periode_par_compteur(self) -> None:
        donnees = self._donnees_soldes_periodes()
        soldes = extraire_soldes_initiaux(donnees, "courant", {"GCP": "suivant", "JRTT": "courant"})
        self.assertEqual(soldes["GCP"], 23.96)
        self.assertEqual(soldes["JRTT"], 1.9)

    def test_priorite_periode_par_compteur_sur_periode_globale(self) -> None:
        donnees = self._donnees_soldes_periodes()
        soldes = extraire_soldes_initiaux(donnees, "suivant", {"JRTT": "courant"})
        self.assertEqual(soldes["JRTT"], 1.9)

    def test_periode_par_compteur_inexistante(self) -> None:
        donnees = self._donnees_projection_minimum("GCP", 1.0, 0.5)
        donnees["soldes"]["compteurs"][0]["periodes"]["suivant"] = {"solde": {"valeur": 2.0}}
        donnees["parametres_projection"]["periodes_compteurs_par_code"] = {"GCP": "suivnat"}
        projection = projeter_demi_journees(donnees)
        alerte = projection["alertes"][0]
        self.assertEqual(alerte["type"], "periode_compteur_absente")
        self.assertEqual(alerte["severite"], "bloquant")
        self.assertEqual(alerte["compteur"], "GCP")
        self.assertEqual(alerte["periode_demandee"], "suivnat")
        self.assertEqual(alerte["periodes_disponibles"], ["courant", "suivant"])

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

    def test_consommations_detaillees_presentes(self) -> None:
        projection = projeter_demi_journees(self._donnees_projection_minimum("GCP", 1.0, 0.5))
        detail = projection["demi_journees"][0]["consommations_detaillees"][0]
        self.assertEqual(detail["identifiant_evenement"], "obligation_test")
        self.assertEqual(detail["compteur"], "GCP")
        self.assertEqual(detail["quantite_demandee"], 0.5)

    def test_consommation_entierement_appliquee(self) -> None:
        projection = projeter_demi_journees(self._donnees_projection_minimum("GCP", 1.0, 0.5))
        detail = projection["demi_journees"][0]["consommations_detaillees"][0]
        self.assertEqual(detail["quantite_appliquee"], 0.5)
        self.assertEqual(detail["quantite_non_couverte"], 0.0)

    def test_consommation_partiellement_appliquee_au_minimum(self) -> None:
        projection = projeter_demi_journees(self._donnees_projection_minimum("CANC", 0.25, 0.5))
        detail = projection["demi_journees"][0]["consommations_detaillees"][0]
        self.assertEqual(detail["quantite_appliquee"], 0.25)
        self.assertEqual(detail["quantite_non_couverte"], 0.25)
        self.assertEqual(projection["alertes"][0]["quantite_appliquee"], 0.25)

    def test_consommation_non_couverte(self) -> None:
        projection = projeter_demi_journees(self._donnees_projection_minimum("CANC", 0.0, 0.5))
        detail = projection["demi_journees"][0]["consommations_detaillees"][0]
        self.assertEqual(detail["quantite_appliquee"], 0.0)
        self.assertEqual(detail["quantite_non_couverte"], 0.5)

    def test_priorite_decroissante_entre_evenements_meme_demi_journee(self) -> None:
        donnees = self._donnees_projection_minimum("GCP", 0.5, 0.5)
        obligation_basse = copy.deepcopy(donnees["verification_obligations"]["obligations"][0])
        obligation_basse["identifiant"] = "obligation_basse"
        obligation_basse["priorite"] = 10
        obligation_haute = copy.deepcopy(donnees["verification_obligations"]["obligations"][0])
        obligation_haute["identifiant"] = "obligation_haute"
        obligation_haute["priorite"] = 100
        donnees["verification_obligations"]["obligations"] = [obligation_basse, obligation_haute]

        projection = projeter_demi_journees(donnees)
        details = {
            detail["identifiant_evenement"]: detail
            for detail in projection["demi_journees"][0]["consommations_detaillees"]
        }
        self.assertEqual(details["obligation_haute"]["quantite_appliquee"], 0.5)
        self.assertEqual(details["obligation_basse"]["quantite_appliquee"], 0.0)
        self.assertEqual(details["obligation_basse"]["quantite_non_couverte"], 0.5)

    def test_compatibilite_resume_consommations(self) -> None:
        projection = projeter_demi_journees(self._donnees_projection_minimum("GCP", 1.0, 0.5))
        self.assertEqual(projection["demi_journees"][0]["consommations"]["GCP"], 0.5)

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
        self.assertEqual(projection["alertes"][0]["type"], "solde_minimum_depasse")
        self.assertEqual(projection["alertes"][0]["severite"], "bloquant")
        self.assertEqual(projection["alertes"][0]["quantite_non_couverte"], 0.25)

    def test_minimum_par_defaut_a_zero(self) -> None:
        projection = projeter_demi_journees(self._donnees_projection_minimum("CANC", 0.25, 0.5))
        self.assertEqual(projection["alertes"][0]["minimum_autorise"], 0.0)

    def test_minimum_jrtt_moins_dix(self) -> None:
        donnees = self._donnees_projection_minimum("JRTT", 0.5, 1.0, {"JRTT": -10.0})
        projection = projeter_demi_journees(donnees)
        self.assertEqual(projection["parametres_projection"]["soldes_minimums_par_code"]["JRTT"], -10.0)

    def test_jrtt_negatif_avec_confirmation(self) -> None:
        donnees = self._donnees_projection_minimum("JRTT", 0.5, 1.0, {"JRTT": -10.0})
        projection = projeter_demi_journees(donnees)
        alertes = [alerte for alerte in projection["alertes"] if alerte["type"] == "solde_negatif_confirmation_possible"]
        self.assertEqual(len(alertes), 1)
        self.assertEqual(alertes[0]["severite"], "confirmation")
        self.assertEqual(alertes[0]["solde_apres"], -0.5)

    def test_jrtt_depasse_minimum_bloquant(self) -> None:
        donnees = self._donnees_projection_minimum("JRTT", -9.75, 0.5, {"JRTT": -10.0})
        projection = projeter_demi_journees(donnees)
        self.assertEqual(projection["alertes"][0]["type"], "solde_minimum_depasse")
        self.assertEqual(projection["alertes"][0]["severite"], "bloquant")
        self.assertEqual(projection["alertes"][0]["quantite_appliquee"], 0.25)
        self.assertEqual(projection["alertes"][0]["quantite_non_couverte"], 0.25)

    def test_canc_bloque_a_zero(self) -> None:
        projection = projeter_demi_journees(self._donnees_projection_minimum("CANC", 0.25, 0.5))
        self.assertEqual(projection["alertes"][0]["type"], "solde_minimum_depasse")
        self.assertEqual(projection["demi_journees"][0]["soldes_apres"]["CANC"], 0.0)

    def test_exclusion_jour_non_decompte(self) -> None:
        projection = projeter_demi_journees(self._donnees_noel_jour_non_decompte())
        demi_journees = self._demi_journees_pour_evenement(projection, "fermeture_noel")
        self.assertNotIn("2026-12-25", {demi_journee["date"] for demi_journee in demi_journees})

    def test_noel_consomme_apres_le_25_decembre(self) -> None:
        projection = projeter_demi_journees(self._donnees_noel_jour_non_decompte())
        dates = [demi_journee["date"] for demi_journee in self._demi_journees_pour_evenement(projection, "fermeture_noel")]
        self.assertEqual(sorted(set(dates)), ["2026-12-28", "2026-12-29", "2026-12-30", "2026-12-31"])

    def test_quantite_evenement_non_projectee_plage_trop_courte(self) -> None:
        donnees = self._donnees_projection_minimum("GCP", 10.0, 2.0)
        projection = projeter_demi_journees(donnees)
        alertes = [alerte for alerte in projection["alertes"] if alerte["type"] == "quantite_evenement_non_projectee"]
        self.assertEqual(len(alertes), 1)
        self.assertEqual(alertes[0]["quantite_restante"], 1.0)
        self.assertEqual(alertes[0]["severite"], "bloquant")

    def test_quantite_evenement_non_projectee_jours_non_decomptes(self) -> None:
        donnees = self._donnees_projection_minimum("GCP", 10.0, 1.0)
        donnees["parametres_projection"]["date_depart"] = "2026-12-25"
        donnees["parametres_projection"]["date_fin"] = "2026-12-25"
        donnees["parametres_projection"]["jours_non_decomptes"] = ["2026-12-25"]
        obligation = donnees["verification_obligations"]["obligations"][0]
        obligation["date_debut"] = "2026-12-25"
        obligation["date_fin"] = "2026-12-25"
        projection = projeter_demi_journees(donnees)
        alertes = [alerte for alerte in projection["alertes"] if alerte["type"] == "quantite_evenement_non_projectee"]
        self.assertEqual(len(alertes), 1)
        self.assertEqual(alertes[0]["quantite_restante"], 1.0)

    def test_evenement_avant_periode_signale(self) -> None:
        donnees = self._donnees_projection_minimum("JRTT", 1.0, 1.0)
        donnees["verification_obligations"]["obligations"][0]["date_debut"] = "2026-05-19"
        donnees["verification_obligations"]["obligations"][0]["date_fin"] = "2026-05-19"
        projection = projeter_demi_journees(donnees)
        self.assertEqual(projection["alertes"][0]["type"], "evenement_hors_periode_projection")

    def test_evenement_apres_periode_signale(self) -> None:
        donnees = self._donnees_projection_minimum("JRTT", 1.0, 1.0)
        donnees["verification_obligations"]["obligations"][0]["date_debut"] = "2026-05-21"
        donnees["verification_obligations"]["obligations"][0]["date_fin"] = "2026-05-21"
        projection = projeter_demi_journees(donnees)
        self.assertEqual(projection["alertes"][0]["type"], "evenement_hors_periode_projection")

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

    def _donnees_soldes_periodes(self) -> dict[str, object]:
        return {
            "soldes": {
                "compteurs": [
                    {
                        "code": "GCP",
                        "periodes": {
                            "courant": {"solde": {"valeur": 0.0}},
                            "suivant": {"solde": {"valeur": 23.96}},
                        },
                    },
                    {
                        "code": "JRTT",
                        "periodes": {
                            "courant": {"solde": {"valeur": 1.9}},
                            "suivant": {"solde": {"valeur": 9.0}},
                        },
                    },
                ]
            }
        }

    def _donnees_projection_minimum(
        self,
        compteur: str,
        solde_initial: float,
        quantite: float,
        minimums: dict[str, float] | None = None,
    ) -> dict[str, object]:
        return {
            "source": "projection.demi_journees.entrees",
            "soldes": {
                "source": "chronotime.soldeabs",
                "compteurs": [
                    {
                        "code": compteur,
                        "libelle": compteur,
                        "periodes": {
                            "courant": {
                                "solde": {
                                    "brut": f"{solde_initial}j",
                                    "unite": "jour",
                                    "valeur": solde_initial,
                                }
                            }
                        },
                    }
                ],
            },
            "scenario": {"source": "simulation.locale", "scenario": {"blocs": []}, "resume": {}},
            "verification_obligations": {
                "source": "verification.obligations",
                "obligations": [
                    {
                        "identifiant": "obligation_test",
                        "libelle": "Obligation test",
                        "date_debut": "2026-05-20",
                        "date_fin": "2026-05-20",
                        "unite": "jours_ouvres",
                        "compteur_prefere": compteur,
                        "priorite": 100,
                        "statut_obligation": "a_poser",
                        "quantite_requise": quantite,
                        "quantite_satisfaite": 0.0,
                        "quantite_restante": quantite,
                        "compteurs_autorises": [compteur],
                        "evenements_compatibles": [],
                    }
                ],
                "resume": {},
            },
            "parametres_projection": {
                "periode_compteurs": "courant",
                "date_depart": "2026-05-20",
                "date_fin": "2026-05-20",
                "dates_cibles": [],
                "ordre_compteurs_sans_preference": ["CANC", "JRTT", "GCP"],
                "soldes_minimums_par_code": minimums or {},
            },
        }

    def _donnees_noel_jour_non_decompte(self) -> dict[str, object]:
        donnees = self._donnees_projection_minimum("CANC", 10.0, 4.0)
        obligation = donnees["verification_obligations"]["obligations"][0]
        obligation["identifiant"] = "fermeture_noel"
        obligation["date_debut"] = "2026-12-25"
        obligation["date_fin"] = "2026-12-31"
        donnees["parametres_projection"]["date_depart"] = "2026-12-25"
        donnees["parametres_projection"]["date_fin"] = "2026-12-31"
        donnees["parametres_projection"]["jours_non_decomptes"] = ["2026-12-25"]
        return donnees

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
