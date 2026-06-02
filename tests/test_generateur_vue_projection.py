from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from outils.chronotime.generateur_vue_projection import (
    agreger_evenements_projetes,
    charger_chronologie,
    charger_projection,
    charger_synthese,
    compteurs_tries_pour_affichage,
    compteur_important_pour_barre_principale,
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
        self.assertIn("Planification", html)
        self.assertIn("Frise", html)
        self.assertIn("Soldes", html)
        self.assertIn("Alertes", html)
        self.assertIn("Événements projetés", html)
        self.assertIn("Technique", html)
        self.assertNotIn('data-cible="vue-details"', html)
        self.assertNotIn('id="vue-details"', html)
        self.assertNotIn(">Détails<", html)

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
        self.assertIn("Événements projetés", html)
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
        self.assertIn("Planification", html)
        self.assertIn("Événements projetés", html)

    def test_generation_html_tableaux_defilables(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("tableau-defilable", html)
        self.assertIn("Soldes aux dates cibles", html)
        self.assertIn("overflow-x: auto", html)

    def test_generation_html_sans_chronologie_affiche_note(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn(
            "Aucune chronologie.soldes fournie. La vue affiche seulement les soldes initiaux et les dates cibles.",
            html,
        )

    def test_generation_html_sans_synthese_affiche_note(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("Aucune synthèse de planification fournie.", html)

    def test_generation_html_planification_passive_structure(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("Planification", html)
        self.assertIn("interface-planification", html)
        self.assertIn("barre-outils-gauche", html)
        self.assertIn("zone-centrale-planification", html)
        self.assertIn("barre-infos-droite", html)

    def test_generation_html_planification_barre_outils(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("Poser des jours", html)
        self.assertIn("Scinder", html)
        self.assertIn("Fusionner", html)
        self.assertIn("Général", html)
        self.assertIn("Détaillé", html)
        self.assertIn("outil-desactive", html)
        self.assertIn("disabled", html)

    def test_generation_html_planification_barre_infos(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("Total restant", html)
        self.assertIn("Cette année", html)
        self.assertIn("Compteurs", html)
        self.assertIn("Expiration", html)
        self.assertIn("Sélection", html)
        self.assertIn("non calculé", html)
        self.assertIn("non calculée", html)
        self.assertIn("aucune", html)
        self.assertNotIn("Détail compteurs", html)
        self.assertNotIn("Compteur</th><th>Solde final", html)

    def test_generation_html_planification_calendrier_passif(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("vue-calendrier-passif", html)
        self.assertIn("mois-calendrier", html)
        self.assertIn("jour-calendrier", html)
        self.assertIn("jour-avec-consommation", html)
        self.assertIn("jours-calendrier", html)
        self.assertIn("grid-template-columns: repeat(31, minmax", html)

    def test_generation_html_planification_frise_niveau(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("vue-frise-niveau", html)
        self.assertIn("niveau-reste-agrege", html)
        self.assertIn("courbe-reste-agrege", html)
        self.assertIn("point-reste-agrege", html)
        self.assertIn("reste agrégé provisoire", html)
        self.assertIn("Formule temporaire", html)

    def test_generation_html_planification_largeur_flexible(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("interface-planification", html)
        self.assertIn("zone-centrale-planification", html)
        self.assertIn("width: 100%", html)
        self.assertIn("max-width: none", html)
        self.assertIn("grid-template-columns", html)

    def test_generation_html_planification_navigation_calendrier_frise(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("bouton-sous-vue", html)
        self.assertIn("data-sous-vue-cible=\"calendrier\"", html)
        self.assertIn("data-sous-vue-cible=\"frise\"", html)
        self.assertIn(">Calendrier</button>", html)
        self.assertIn(">Frise</button>", html)
        self.assertIn("function activerSousVue", html)
        self.assertIn("sous-vue-planification-active", html)

    def test_generation_html_planification_frise_sans_cartes_textuelles(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertNotIn("bloc-frise-passif", html)
        self.assertNotIn("ligne-blocs-passifs", html)
        self.assertIn("bloc-temporel-projete", html)

    def test_generation_html_planification_axes_frise(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("axe-horizontal", html)
        self.assertIn("repere-mois", html)
        self.assertIn("repere-jour", html)
        self.assertIn("axe-vertical", html)
        self.assertIn("repere-reste", html)
        self.assertIn("liaison-bloc-courbe", html)
        self.assertIn("borne-bloc-debut", html)
        self.assertIn("borne-bloc-fin", html)

    def test_generation_html_planification_structure_selection(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("selection-planification", html)
        self.assertIn("data-selection-type", html)
        self.assertIn("selection-active", html)
        self.assertIn("selection-niveaux", html)
        self.assertIn("data-selection-niveau", html)
        self.assertIn("selection-type-jour", html)
        self.assertIn("selection-type-bloc", html)

    def test_generation_html_selection_calendrier(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("jour-selectionnable", html)
        self.assertIn("element-selectionnable", html)
        self.assertIn('data-selection-type="jour"', html)
        self.assertIn("data-selection-date=", html)
        self.assertIn("data-selection-consommation=", html)
        self.assertIn("data-selection-alertes=", html)
        self.assertIn('role="button"', html)
        self.assertIn('tabindex="0"', html)
        self.assertIn('data-selection-cyclique="true"', html)
        self.assertIn('data-selection-type="sous-bloc"', html)

    def test_generation_html_selection_frise_bloc(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("bloc-temporel-projete element-selectionnable", html)
        self.assertIn('data-selection-type="bloc"', html)
        self.assertIn("data-selection-identifiant=", html)
        self.assertIn("data-selection-periode=", html)
        self.assertIn("data-selection-quantite=", html)
        self.assertIn("data-selection-compteurs=", html)
        self.assertIn("data-selection-alertes=", html)

    def test_generation_html_selection_courbe_reste(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("point-reste-agrege element-selectionnable", html)
        self.assertIn('data-selection-type="reste"', html)
        self.assertIn("data-selection-niveau=", html)
        self.assertIn("data-selection-portion=", html)

    def test_generation_html_javascript_selection_passive(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("function activerSelectionPlanification", html)
        self.assertIn("function deselectionnerPlanification", html)
        self.assertIn("function lireSelection", html)
        self.assertIn("selection-planification", html)
        self.assertIn("selection-active", html)
        self.assertIn("addEventListener('keydown'", html)
        self.assertIn("event.key === 'Enter'", html)
        self.assertIn("Escape", html)
        self.assertIn("selectionIndex", html)
        self.assertIn("niveau", html)

    def test_generation_html_selection_infos_contraintes(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("fiche-selection", html)
        self.assertIn("puce-selection", html)
        self.assertIn("champ-selection", html)
        self.assertIn("libelle-selection", html)
        self.assertIn("valeur-selection", html)
        self.assertIn("valeur-longue", html)
        self.assertIn("overflow-wrap", html)
        self.assertIn("word-break", html)
        self.assertIn("max-width", html)
        self.assertIn("overflow-x: hidden", html)

    def test_generation_html_barre_droite_sans_tous_les_compteurs(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertNotIn("Tous les compteurs", html)
        self.assertNotIn("details-compteurs-complets", html)

    def test_compteurs_barre_principale_filtre_les_nuls_non_importants(self) -> None:
        soldes = {"GCP": 10.0, "JRTT": 0.0, "CANC": 0.0, "REHV": 0.0, "RECU": 3.0}

        comptes = [compteur for compteur, _valeur in compteurs_tries_pour_affichage(soldes)]

        self.assertIn("GCP", comptes)
        self.assertIn("JRTT", comptes)
        self.assertIn("CANC", comptes)
        self.assertIn("RECU", comptes)
        self.assertNotIn("REHV", comptes)

    def test_compteurs_detail_affiche_tout_avec_nuls_a_la_fin(self) -> None:
        soldes = {"GCP": 10.0, "JRTT": 0.0, "REHV": 0.0, "RECU": 3.0}

        comptes = [compteur for compteur, _valeur in compteurs_tries_pour_affichage(soldes, inclure_tous=True)]

        self.assertEqual(set(comptes), {"GCP", "JRTT", "REHV", "RECU"})
        self.assertGreater(comptes.index("REHV"), comptes.index("GCP"))
        self.assertGreater(comptes.index("REHV"), comptes.index("RECU"))
        self.assertTrue(compteur_important_pour_barre_principale("GCP"))
        self.assertTrue(compteur_important_pour_barre_principale("JRTT"))
        self.assertTrue(compteur_important_pour_barre_principale("CANC"))

    def test_chargement_chronologie_valide(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire:
            chemin = Path(repertoire) / "chronologie.json"
            chemin.write_text(json.dumps(self._chronologie_factice()), encoding="utf-8")

            chronologie = charger_chronologie(chemin)

            self.assertEqual(chronologie["source"], "chronologie.soldes")

    def test_refus_chronologie_source_invalide(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire:
            chemin = Path(repertoire) / "chronologie.json"
            donnees = self._chronologie_factice()
            donnees["source"] = "mouvements.soldes"
            chemin.write_text(json.dumps(donnees), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Source de chronologie invalide"):
                charger_chronologie(chemin)

    def test_refus_synthese_source_invalide(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire:
            chemin = Path(repertoire) / "synthese.json"
            donnees = self._synthese_factice()
            donnees["source"] = "chronologie.soldes"
            chemin.write_text(json.dumps(donnees), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Source de synthèse invalide"):
                charger_synthese(chemin)

    def test_generation_html_avec_chronologie(self) -> None:
        html = generer_html(self._charger_exemple(), self._chronologie_factice())

        self.assertIn("Soldes dans le temps", html)
        self.assertIn("Soldes finaux", html)
        self.assertIn("GCP", html)
        self.assertIn("38,75 j", html)
        self.assertIn("10 août 2026", html)
        self.assertIn("-3,25 j", html)
        self.assertIn("chrono_factice", html)
        self.assertIn("alerte_chronologie_test", html)
        self.assertIn("chronologie_factice", html)
        self.assertIn("Solde après", html)

    def test_generation_html_utilise_chronologie_fournie_sans_recalcul(self) -> None:
        html = generer_html(self._charger_exemple(), self._chronologie_factice())

        self.assertIn("42 j", html)
        self.assertIn("38,75 j", html)
        self.assertIn("preuve", html)

    def test_generation_html_avec_synthese_planification(self) -> None:
        html = generer_html(self._charger_exemple(), synthese=self._synthese_factice())

        self.assertIn("Planification", html)
        self.assertIn("Statut global", html)
        self.assertIn("attention", html)
        self.assertIn("Jours posés", html)
        self.assertIn("4,5 j", html)
        self.assertIn("Jours expirés", html)
        self.assertIn("2 j", html)
        self.assertIn("Reste au 31 décembre 2026", html)
        self.assertIn("bloc_noel", html)
        self.assertIn("Signaux", html)
        self.assertIn("jours_expires", html)
        self.assertIn("Détails techniques par compteur", html)

    def test_generation_html_planification_actionnable(self) -> None:
        html = generer_html(self._charger_exemple(), synthese=self._synthese_factice())

        self.assertIn("Échéances importantes", html)
        self.assertIn("31 décembre 2026", html)
        self.assertIn("1 j expire", html)
        self.assertIn("Compteur technique : CANC", html)
        self.assertIn("Action : À utiliser avant cette date si possible.", html)
        self.assertNotIn("Jours crédités", html)
        self.assertIn("Jours ajoutés dans la période", html)
        self.assertIn("Détails techniques du signal", html)

    def test_generation_html_titre_compact(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("font-size: clamp(1.4rem, 2.4vw, 2.2rem);", html)
        self.assertIn("line-height: 1.05;", html)

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
        self.assertIn("bloc-jour", html)
        self.assertIn("numero-jour", html)
        self.assertIn("cases-jour", html)

    def test_generation_html_details_repliables(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("<details>", html)

    def test_agregation_evenement_multi_demi_journees(self) -> None:
        projection = self._charger_exemple()
        agregats = agreger_evenements_projetes(
            projection["demi_journees"],
            projection["alertes"],
        )
        agregat_ete = next(
            evenement
            for evenement in agregats
            if evenement["identifiant_evenement"] == "bloc_exemple_ete"
        )
        self.assertEqual(agregat_ete["date_debut"], "2026-05-20")
        self.assertEqual(agregat_ete["date_fin"], "2026-05-20")
        self.assertAlmostEqual(agregat_ete["quantite_appliquee_totale"], 1.0)
        self.assertAlmostEqual(agregat_ete["compteurs"]["GCP"]["quantite_appliquee"], 1.0)

    def test_generation_html_cartes_evenements_compactes(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("carte-evenement-projete", html)
        self.assertIn("GCP : 1 j", html)
        self.assertNotIn("Alertes : aucune", html)
        self.assertNotIn("Non couvert : 0 j", html)
        self.assertNotIn("non couverte 0 j", html)

    def test_generation_html_sans_ressource_externe(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)
        self.assertNotIn("<script src=", html)
        self.assertNotIn("<link rel=", html)

    def test_generation_html_sans_persistance_ni_acces_fichier(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertNotIn("fetch(", html)
        self.assertNotIn("localStorage", html)
        self.assertNotIn("indexedDB", html)
        self.assertNotIn("FileSystem", html)

    def test_generation_html_planification_non_regression_vues_et_outils(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("Vue d’ensemble", html)
        self.assertIn("Planification", html)
        self.assertIn("Calendrier", html)
        self.assertIn("Frise", html)
        self.assertIn("Soldes", html)
        self.assertIn("Alertes", html)
        self.assertIn("Événements projetés", html)
        self.assertIn("Technique", html)
        self.assertIn("Poser des jours", html)
        self.assertIn("Scinder", html)
        self.assertIn("Fusionner", html)
        self.assertIn("disabled", html)

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

    def test_generation_fichier_html_avec_chronologie(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire:
            chemin_chronologie = Path(repertoire) / "chronologie.json"
            chemin_sortie = Path(repertoire) / "vue.html"
            chemin_chronologie.write_text(json.dumps(self._chronologie_factice()), encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    "outils/chronotime/generateur_vue_projection.py",
                    "--projection",
                    str(self._chemin_exemple()),
                    "--chronologie",
                    str(chemin_chronologie),
                    "--sortie",
                    str(chemin_sortie),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            html = chemin_sortie.read_text(encoding="utf-8")
            self.assertIn("Soldes dans le temps", html)
            self.assertIn("chrono_factice", html)

    def test_generation_fichier_html_avec_synthese(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire:
            chemin_synthese = Path(repertoire) / "synthese.json"
            chemin_sortie = Path(repertoire) / "vue.html"
            chemin_synthese.write_text(json.dumps(self._synthese_factice()), encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    "outils/chronotime/generateur_vue_projection.py",
                    "--projection",
                    str(self._chemin_exemple()),
                    "--synthese",
                    str(chemin_synthese),
                    "--sortie",
                    str(chemin_sortie),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            html = chemin_sortie.read_text(encoding="utf-8")
            self.assertIn("Planification", html)
            self.assertIn("bloc_noel", html)

    def test_tests_sans_donnees_locales(self) -> None:
        self.assertNotIn("donnees_locales", str(self._chemin_exemple()))

    def _chemin_exemple(self) -> Path:
        return Path("donnees/exemples/projection_demi_journees.exemple.json")

    def _charger_exemple(self) -> dict[str, object]:
        return json.loads(self._chemin_exemple().read_text(encoding="utf-8"))

    def _chronologie_factice(self) -> dict[str, object]:
        return {
            "source": "chronologie.soldes",
            "periode": {"debut": "2026-05-20", "fin": "2026-12-31"},
            "soldes_initiaux": {"GCP": 99.0},
            "points_chronologie": [
                {
                    "date": "2026-08-10",
                    "portion": "matin",
                    "ordre": 10,
                    "origine": "consommation_projection",
                    "type": "consommation_absence",
                    "identifiant": "chrono_factice",
                    "compteur": "GCP",
                    "variation": -3.25,
                    "soldes_avant": {"GCP": 42.0},
                    "soldes_apres": {"GCP": 38.75},
                    "details": {"preuve": "chronologie_factice"},
                }
            ],
            "soldes_finaux": {"GCP": 38.75, "JRTT": 7.0},
            "alertes": [{"type": "alerte_chronologie_test", "severite": "information"}],
            "resume": {
                "nombre_mouvements": 1,
                "nombre_points_chronologie": 1,
                "nombre_alertes": 1,
            },
        }

    def _synthese_factice(self) -> dict[str, object]:
        return {
            "source": "synthese.planification",
            "periode": {"debut": "2026-05-20", "fin": "2026-12-31"},
            "resume_global": {
                "jours_initiaux_agreges": 30.0,
                "jours_finaux_agreges": 18.5,
                "variation_totale": -11.5,
                "jours_consommes": 4.5,
                "jours_expires": 2.0,
                "jours_credites": 1.0,
                "jours_debites_techniques": 0.0,
                "nombre_signaux": 1,
                "statut": "attention",
                "date_fin_projection": "2026-12-31",
            },
            "echeances": [
                {
                    "type": "expiration",
                    "date": "2026-12-31",
                    "quantite": 1.0,
                    "compteur_technique": "CANC",
                    "identifiant": "expiration_canc_2026",
                    "message": "1 j expire le 2026-12-31.",
                    "action_suggeree": "À utiliser avant cette date si possible.",
                }
            ],
            "consommations_par_evenement": [
                {
                    "identifiant": "bloc_noel",
                    "premiere_date": "2026-12-28",
                    "derniere_date": "2026-12-31",
                    "jours_consommes": 4.5,
                    "compteurs_techniques": {"GCP": -4.5},
                    "origines": ["projection.demi_journees"],
                    "types": ["consommation_absence"],
                }
            ],
            "soldes_agreges_aux_dates_cibles": [
                {
                    "identifiant": "noel",
                    "libelle": "Noël",
                    "date": "2026-12-25",
                    "jours_restants_agreges": 18.5,
                }
            ],
            "signaux": [
                {
                    "type": "jours_expires",
                    "severite": "attention",
                    "message": "Des jours expirent dans ce scénario.",
                    "details": {
                        "jours_expires": 2.0,
                        "echeances": [
                            {
                                "type": "expiration",
                                "date": "2026-12-31",
                                "quantite": 1.0,
                                "compteur_technique": "CANC",
                            }
                        ],
                    },
                }
            ],
            "details_techniques": {
                "par_compteur": {"GCP": {"initial": 20.0, "final": 15.5, "seuil_technique_suppose": 0.0}},
                "alertes_sources": [],
            },
        }


if __name__ == "__main__":
    unittest.main()
