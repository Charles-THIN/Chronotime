from __future__ import annotations

import sys
import unittest

from outils.chronotime import lancer_planificateur


class TestLancerPlanificateur(unittest.TestCase):
    def test_parseur_expose_option_ne_pas_ouvrir(self) -> None:
        arguments = lancer_planificateur.creer_parseur().parse_args(["--ne-pas-ouvrir"])

        self.assertTrue(arguments.ne_pas_ouvrir)

    def test_valeurs_par_defaut_restent_locales(self) -> None:
        arguments = lancer_planificateur.creer_parseur().parse_args([])

        self.assertEqual(arguments.soldes, "donnees_locales/soldes_absences_chronotime.json")
        self.assertEqual(arguments.agenda, "donnees_locales/agenda_chronotime.json")
        self.assertEqual(arguments.obligations, "donnees_locales/obligations_conges_2026.json")
        self.assertEqual(arguments.scenario, "donnees_locales/scenario_vide.json")
        self.assertEqual(arguments.date_fin, "2027-01-31")
        self.assertEqual(arguments.sortie_vue, "donnees_locales/vue_projection.html")

    def test_construction_commandes(self) -> None:
        arguments = lancer_planificateur.creer_parseur().parse_args(["--ne-pas-ouvrir"])

        commande_orchestrateur = lancer_planificateur.construire_commande_orchestrateur(arguments)
        commande_generateur = lancer_planificateur.construire_commande_generateur(arguments)

        self.assertEqual(commande_orchestrateur[0], sys.executable)
        self.assertIn("--sortie-entrees-projection", commande_orchestrateur)
        self.assertIn("--date-fin", commande_orchestrateur)
        self.assertIn("2027-01-31", commande_orchestrateur)
        self.assertEqual(commande_generateur[0], sys.executable)
        self.assertIn("--entrees-projection", commande_generateur)
        self.assertIn("vue_projection.html", " ".join(commande_generateur))

    def test_fichiers_obligatoires(self) -> None:
        arguments = lancer_planificateur.creer_parseur().parse_args([])

        chemins = lancer_planificateur.fichiers_obligatoires(arguments)

        self.assertEqual(len(chemins), 4)
        self.assertTrue(all(str(chemin).endswith(".json") for chemin in chemins))


if __name__ == "__main__":
    unittest.main()
