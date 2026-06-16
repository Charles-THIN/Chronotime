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
    charger_entrees_projection,
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

    def test_chargement_entrees_projection_valide(self) -> None:
        entrees = charger_entrees_projection(self._chemin_entrees_projection_minimum())
        self.assertEqual(entrees["source"], "projection.demi_journees.entrees")

    def test_refus_entrees_projection_source_invalide(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire:
            chemin = Path(repertoire) / "entrees.json"
            donnees = copy.deepcopy(self._charger_entrees_projection_minimum())
            donnees["source"] = "projection.demi_journees"
            chemin.write_text(json.dumps(donnees), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Source d'entrées de projection invalide"):
                charger_entrees_projection(chemin)

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

    def test_premiere_vue_par_defaut_planification(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("activerVue('vue-planification')", html)
        self.assertNotIn("activerVue('vue-ensemble')", html)

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

        self.assertIn("Sélection", html)
        self.assertIn("Poser des jours", html)
        self.assertIn("Général", html)
        self.assertIn("Détaillé", html)
        self.assertIn('data-outil-planification="selection"', html)
        self.assertIn('data-outil-planification="poser"', html)
        self.assertNotIn('data-outil-planification="poser" aria-pressed="false" disabled', html)
        self.assertNotIn("Scinder", html)
        self.assertNotIn("Fusionner", html)
        self.assertNotIn("Relancer orchestrateur_projection.py", html)
        self.assertNotIn("Régénérer la vue HTML", html)
        self.assertNotIn("Placer le fichier dans", html)

    def test_generation_html_planification_barre_infos(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("Total restant", html)
        self.assertIn("Posés 2026", html)
        self.assertIn("data-poses-annee", html)
        self.assertIn("data-poses-annee-valeur", html)
        self.assertIn("Compteurs", html)
        self.assertIn("Sélection", html)
        self.assertIn("data-total-restant", html)
        self.assertIn("data-total-restant-valeur", html)
        self.assertIn("data-compteur-code", html)
        self.assertNotIn("Cette année", html)
        self.assertNotIn("Expiration", html)
        self.assertNotIn("non calculé", html)
        self.assertNotIn("non calculée", html)
        self.assertNotIn("Recalculé ·", html)
        self.assertNotIn("Projection statique", html)
        self.assertNotIn("Recalcul direct indisponible", html)
        self.assertNotIn("Détail compteurs", html)
        self.assertNotIn("Compteur</th><th>Solde final", html)

    def test_generation_html_planification_calendrier_passif(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("vue-calendrier-passif", html)
        self.assertIn("mois-calendrier", html)
        self.assertIn("cellule-calendrier", html)
        self.assertIn("jour-calendrier", html)
        self.assertIn("numero-jour-calendrier", html)
        self.assertIn("type-compteur-jour", html)
        self.assertIn("libelle-jour-semaine", html)
        self.assertIn("jour-dimanche", html)
        self.assertIn("jour-avec-consommation", html)
        self.assertIn("jours-calendrier", html)
        self.assertIn("grid-template-columns: repeat(31, minmax", html)

    def test_generation_html_calendrier_grammaire_visuelle_compteurs(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("--compteur-gcp", html)
        self.assertIn("--compteur-jrtt", html)
        self.assertIn("--compteur-canc", html)
        self.assertIn("--compteur-defaut", html)
        self.assertIn("compteur-gcp", html)
        self.assertIn("compteur-jrtt", html)
        self.assertIn("compteur-canc", html)
        self.assertIn("compteur-defaut", html)
        self.assertIn('data-mode-planification="detaille"', html)

    def test_generation_html_calendrier_origine_utilisateur_distincte(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("origine-utilisateur", html)
        self.assertIn("compteur-manuel-gcp", html)
        self.assertIn("compteur-manuel-jrtt", html)
        self.assertIn("compteur-manuel-canc", html)
        self.assertIn("compteur-manuel-defaut", html)
        self.assertIn("border-style: dashed", html)
        self.assertNotIn(".jour-avec-bloc-utilisateur::after", html)
        self.assertNotIn(".jour-avec-bloc-utilisateur {\n      background: linear-gradient", html)

    def test_generation_html_calendrier_libelles_jours_semaine(self) -> None:
        projection = copy.deepcopy(self._charger_exemple())
        modele = copy.deepcopy(projection["demi_journees"][0])
        projection["demi_journees"] = []
        for jour in range(1, 8):
            demi_journee = copy.deepcopy(modele)
            demi_journee["date"] = f"2026-06-0{jour}"
            demi_journee["portion"] = "matin"
            demi_journee["consommations"] = {}
            demi_journee["consommations_detaillees"] = []
            demi_journee["alertes"] = []
            projection["demi_journees"].append(demi_journee)
        html = generer_html(projection)

        for libelle in ("lun", "mar", "mer", "jeu", "ven", "sam", "dim"):
            self.assertIn(f">{libelle}</span>", html)
        self.assertIn(".libelle-jour-semaine.jour-dimanche", html)
        self.assertIn("font-weight: 800", html)

    def test_generation_html_planification_frise_niveau(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("vue-frise-niveau", html)
        self.assertIn("niveau-reste-agrege", html)
        self.assertIn("courbe-reste-agrege", html)
        self.assertIn("point-reste-agrege", html)
        self.assertIn("data-frise-planification", html)
        self.assertIn("data-frise-blocs", html)
        self.assertIn("data-frise-source", html)
        self.assertIn("data-identifiant-bloc", html)
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
        self.assertIn("axe-horizontal-superieur", html)
        self.assertIn("axe-horizontal-superieur-reperes", html)
        self.assertIn("repere-mois", html)
        self.assertIn("repere-jour", html)
        self.assertIn("repere-jour-superieur", html)
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

    def test_generation_html_sans_reseau_ni_acces_fichier_navigateur(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertNotIn("fetch(", html)
        self.assertNotIn("XMLHttpRequest", html)
        self.assertNotIn("indexedDB", html)
        self.assertNotIn("FileSystem", html)

    def test_generation_html_prototype_pose_locale(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("chronotime.planification.prototype.v1", html)
        self.assertIn("absence_locale_prototype", html)
        self.assertIn("ajoute_par_utilisateur", html)
        self.assertIn("scenario_local_prototype", html)
        self.assertIn("function creerBlocLocalPrototype", html)
        self.assertIn("function supprimerBlocLocalSelectionne", html)
        self.assertIn("localStorage.getItem", html)
        self.assertIn("localStorage.setItem", html)
        self.assertIn("data-outil-planification=\"poser\"", html)
        self.assertIn("data-outil-planification=\"selection\"", html)
        self.assertIn("bloc-utilisateur-prototype", html)
        self.assertIn("jour-avec-bloc-utilisateur", html)
        self.assertIn("bloc-utilisateur-frise", html)
        self.assertIn("selection-plage-bloc-utilisateur", html)
        self.assertIn("bloc-fantome-local", html)
        self.assertIn("bloc-fantome-impossible", html)
        self.assertIn("pose impossible", html)
        self.assertIn("Pose impossible : plage déjà occupée", html)
        self.assertIn("jours ouvrés possibles", html)
        self.assertNotIn("prévisualisation locale", html)
        self.assertNotIn("afficherFantomeFrise(dateA, dateB, impossible);", html)
        self.assertNotIn("Compteur indicatif", html)
        self.assertNotIn("non recalculé par le moteur", html)
        self.assertNotIn("j projeté(s)", html)
        self.assertIn("Suppr pour supprimer", html)
        self.assertIn("jourOccupePourPose", html)
        self.assertIn("plageLibrePourPose", html)
        self.assertIn("pointerdown", html)
        self.assertIn("pointerup", html)
        self.assertIn("pointermove", html)
        self.assertIn("elementFromPoint", html)
        self.assertIn("finaliserPoseLocalePrototype(jour ? jour.dataset.dateIso : dateSurvolPose)", html)
        self.assertIn("window.addEventListener('blur'", html)
        self.assertIn("jour-survol-simple", html)
        self.assertIn("jour-avec-bloc-utilisateur", html)
        self.assertNotIn(".jour-avec-bloc-utilisateur::after", html)
        self.assertNotIn("background: linear-gradient(180deg, rgba(255, 250, 240, 0.95), rgba(230, 244, 240, 0.92));", html)
        self.assertNotIn("bloc-utilisateur-selectionne {\n      fill: var(--alerte)", html)
        self.assertIn("afficherCurseurPrototype(dateA, dateB, impossible)", html)
        self.assertNotIn("bloc-local-calendrier", html)

    def test_generation_html_moteur_gui_prototype_centralise(self) -> None:
        html = generer_html(self._charger_exemple())

        for marqueur in (
            "function traiterCommandeMoteurGui",
            "function construireEtatCentralGui",
            "function afficherEtatCentralGui",
            "etatTransitoireInterface",
            "afficherEtatTransitoireInterface",
            "fantome_calendrier",
            "fantome_frise",
            "version_contrat",
            "blocs_affichables",
            "diagnostics",
            "ajouter_absence",
            "supprimer_absence",
            "previsualiser",
            "appliquer",
            "plage_deja_occupee",
            "date_hors_projection",
            "bloc_non_modifiable",
            "bloc_introuvable",
            "diagnostics-planification",
            "bloc_absence_affichable",
            "prototype_interface",
        ):
            self.assertIn(marqueur, html)

    def test_generation_html_etat_transitoire_separe_du_central(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("localStorage = autosauvegarde prototype du scénario source", html)
        self.assertIn("etatCentralGui = état central courant de la page", html)
        self.assertIn("etatTransitoireInterface = manipulation en cours, non durable", html)
        self.assertIn("bloc-fantome-local", html)
        self.assertIn("bloc-fantome-frise", html)
        self.assertIn("dernier_resultat_previsualisation", html)
        self.assertIn("traiterCommandeMoteurGui(etatCentralGui, commande)", html)
        self.assertIn("afficherEtatCentralGui(etatCentralGui)", html)
        self.assertIn("nettoyerCurseurPose", html)
        self.assertIn("afficherDiagnosticsGui([])", html)
        self.assertNotIn("etatTransitoireFrise", html)

    def test_generation_html_fantome_refuse_reste_visible(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("bloc-fantome-impossible", html)
        self.assertIn(".bloc-fantome-local.bloc-fantome-impossible", html)
        self.assertIn("jour.classList.add('bloc-fantome-local')", html)
        self.assertIn("if (impossible) { jour.classList.add('bloc-fantome-impossible'); }", html)
        self.assertIn("afficherFantomeFrise(dateA, dateB, impossible)", html)
        self.assertIn("bloc-fantome-frise-impossible", html)
        self.assertIn("afficherCurseurPrototype(dateA, dateB, impossible)", html)
        self.assertIn("plage_deja_occupee", html)
        self.assertIn("diagnostics-planification", html)
        self.assertNotIn("localStorage.setItem(CLE_STOCKAGE_PROTO, JSON.stringify(etatTransitoireInterface", html)
        self.assertNotIn("localStorage.setItem(CLE_STOCKAGE_PROTO, JSON.stringify(resultatPrevisualisation", html)

    def test_generation_html_choix_compteur_gui(self) -> None:
        html = generer_html(self._charger_exemple())

        for marqueur in (
            "choix-compteur-planification",
            "Compteur",
            "Auto",
            "choix_compteur",
            "mode: 'auto'",
            "mode: 'manuel'",
            "obtenirOptionsCompteurMoteurGui",
            "source_decision_compteur",
            "justification_decision_compteur",
            "moteur_gui_prototype",
        ):
            self.assertIn(marqueur, html)
        self.assertNotIn("Priorité non déterminée dans cette vue.", html)
        self.assertNotIn("Source de décision du compteur", html)
        self.assertNotIn("Origine du bloc", html)

    def test_generation_html_export_scenario_local(self) -> None:
        html = generer_html(self._charger_exemple())

        for marqueur in (
            "exporter-scenario-local",
            "Exporter scénario local",
            "scenario_gui_chronotime.json",
            "simulation.locale",
            "scenario_gui_chronotime",
            "prototype_gui",
            "jours_ouvres",
            "construireScenarioLocalExportable",
            "exporterScenarioLocalGui",
            "compteur_souhaite",
            "compteur_reellement_consomme",
        ):
            self.assertIn(marqueur, html)
        self.assertNotIn("orchestrateur_projection.py", html)
        self.assertNotIn("--scenario donnees_locales/scenario_gui_chronotime.json", html)

        self.assertNotIn("fetch(", html)
        self.assertNotIn("XMLHttpRequest", html)
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)

    def test_generation_html_recalcul_js_vivant_avec_entrees(self) -> None:
        html = generer_html(self._charger_exemple(), entrees_projection=self._charger_entrees_projection_minimum())

        for marqueur in (
            "ChronotimeProjecteur",
            "projeterDemiJournees",
            "projectionVivante",
            "construireEntreesProjectionVivantes",
            "blocGuiVersBlocScenario",
            "recalculerProjectionVivante",
            "projection-vivante-planification",
            "projection.demi_journees.entrees",
            "prototype_gui",
            "source_decision_compteur",
            "choix_compteur",
            "infosBlocDepuisProjectionVivante",
            "jours_calendaires_selectionnes",
            "jours_decomptes",
            "jours_consommes",
            "consommations_par_compteur",
            "mettreAJourCompteursDepuisProjectionVivante",
            "mettreAJourTotalRestantDepuisProjectionVivante",
            "mettreAJourTotalRestantDepuisProjectionVivante(projectionVivante)",
            "mettreAJourFriseDepuisProjectionActive",
            "mettreAJourFriseDepuisProjectionActive(projectionVivante)",
            "blocsFriseDepuisProjectionActive",
            "data-frise-blocs",
            "data-frise-source",
            "data-identifiant-bloc",
            "projection_active",
            "data-total-restant",
            "data-total-restant-valeur",
            "data-total-restant-delta",
            "data-compteur-code",
            "projection_vivante",
            "compteur-vivant-recalcule",
            "mettreAJourPosesDepuisProjectionVivante",
            "data-poses-annee",
            "à résoudre",
            "famille_compteur",
            "standard",
            "periode_selon_unite",
            "window.ChronotimeEntreesProjectionInitiales",
        ):
            self.assertIn(marqueur, html)

        self.assertNotIn("Parentalité", html)
        self.assertNotIn("Soldes fin : ", html)
        self.assertNotIn("Soldes fin : ASTJ", html)
        self.assertNotIn("Projection vivante", html)
        self.assertNotIn("vivant · Δ", html)
        self.assertNotIn("Projection recalculée", html)
        self.assertNotIn("Recalculé ·", html)
        self.assertNotIn("Moteur non recalculé", html)
        self.assertNotIn("bloc utilisateur prototype", html)
        self.assertNotIn("prévisualisation locale", html)
        self.assertNotIn("afficherFantomeFrise(dateA, dateB, impossible);", html)

    def test_generation_html_frise_synchronisee_projection_active(self) -> None:
        html = generer_html(self._charger_exemple(), entrees_projection=self._charger_entrees_projection_minimum())

        for marqueur in (
            "function mettreAJourFriseDepuisProjectionActive",
            "function memoriserFrisesStatiquesInitiales",
            "function restaurerFriseStatique",
            "function blocsFriseDepuisProjectionActive",
            "function creerBlocFriseProjection",
            "function creerLiaisonBlocFrise",
            "function definirDonneesSelectionBlocFrise",
            "function origineFriseBloc",
            "function classeOrigineFrise",
            "function classeCompteurTechnique",
            "function classeVisuelleCompteurCode",
            "function classesCompteurManuel",
            "function compteurPrincipalDepuisCompteurs",
            "function classesVisuellesBlocFrise",
            "function classeVisuelleTraitOrigineBloc",
            "function libelleCompteursFriseDetaille",
            "visuel-origine-utilisateur",
            "visuel-origine-projection",
            "visuel-compteur-gcp",
            "visuel-compteur-jrtt",
            "visuel-compteur-canc",
            "visuel-trait-pointille",
            "visuel-trait-epais",
            "libelle-compteur-frise",
            "libelle-compteur-frise-interieur",
            "libelle-compteur-frise-dessus",
            "classeLibelleCompteurFrise",
            "yLibelleCompteurFrise",
            "axe-horizontal-superieur",
            "repere-jour-superieur",
            "memoriserSelectionPlanification",
            "reappliquerSelectionPlanification",
            "derniereSelectionPlanification",
            "trouverElementFrisePourSelection",
            "trouverElementCalendrierPourSelection",
            "diagnostiquerDispositionCurseurPlanification",
            "Décisions visuelles communes calendrier/frise",
            "element.dataset.friseOrigine",
            "origine-frise-utilisateur",
            "data-mode-planification=\"general\"] .bloc-frise-groupe.origine-frise-utilisateur",
            "data-mode-planification=\"detaille\"] .bloc-frise-groupe.compteur-frise-gcp .bloc-temporel-projete",
            "rgba(201, 111, 117, 0.22)",
            "rgba(79, 134, 198, 0.22)",
            "rgba(79, 155, 115, 0.22)",
            "mettreAJourCompteursDepuisProjectionVivante(projectionVivante)",
            "mettreAJourTotalRestantDepuisProjectionVivante(projectionVivante)",
            "mettreAJourPosesDepuisProjectionVivante(projectionVivante)",
            "mettreAJourFriseDepuisProjectionActive(projectionVivante)",
            "blocGuiVersBlocScenario",
            "identifiant_evenement",
            "origine_bloc",
            "bloc-utilisateur-frise",
            "Bloc utilisateur",
            "jours consommés au total",
            "Posés",
        ):
            self.assertIn(marqueur, html)

        self.assertIn('data-frise-planification="projection"', html)
        self.assertIn("data-frise-blocs", html)
        self.assertIn("data-frise-source=\"projection_initiale\"", html)
        self.assertIn("data-identifiant-bloc=", html)
        self.assertIn("definirDonneesSelectionBlocFrise(groupeBloc, bloc, utilisateur)", html)
        self.assertIn("definirDonneesSelectionBlocFrise(rect, bloc, utilisateur)", html)
        self.assertIn("element.dataset.friseSource = 'projection_active'", html)
        self.assertIn("element.dataset.identifiantBloc = bloc.identifiant", html)
        self.assertIn("borne-bloc-debut", html)
        self.assertIn("borne-bloc-fin", html)
        self.assertIn("bloc-frise-groupe", html)
        self.assertIn("bloc-frise-rectangle", html)
        self.assertIn("groupe.textContent = ''", html)
        self.assertIn("coucheLocale.textContent = ''", html)
        self.assertIn("svg.dataset.friseSource = 'projection_active'", html)

        self.assertNotIn("Projection recalculée", html)
        self.assertNotIn("Recalculé ·", html)
        self.assertNotIn("Moteur non recalculé", html)
        self.assertNotIn("bloc utilisateur prototype", html)
        self.assertNotIn("prévisualisation locale", html)
        self.assertNotIn("afficherFantomeFrise(dateA, dateB, impossible);", html)

    def test_generation_html_quantites_bloc_utilisateur_explicitent_decompte(self) -> None:
        html = generer_html(self._charger_exemple(), entrees_projection=self._charger_entrees_projection_minimum())

        self.assertIn("Bloc utilisateur", html)
        self.assertIn("jours calendaires", html)
        self.assertIn("jours consommés au total", html)
        self.assertIn("Suppr pour supprimer", html)
        self.assertIn("resumeConsommationsCompactes", html)
        self.assertNotIn("ajouterChampSelection(fiche, 'Quantité', bloc.quantite_jours + ' j'", html)
        self.assertNotIn("Compteur connu dans la projection ; règle de priorité non déterminée dans cette vue.", html)
        self.assertNotIn("bloc utilisateur prototype", html)
        self.assertNotIn("Source de décision du compteur", html)
        self.assertNotIn("scénario GUI autosauvegardé localement", html)

    def test_generation_html_sans_entrees_recalcul_indisponible(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn("projection-vivante-planification", html)
        self.assertIn('class="projection-vivante-section" hidden', html)
        self.assertNotIn("Recalcul direct indisponible : entrées de projection non fournies.", html)
        self.assertIn("window.ChronotimeEntreesProjectionInitiales = null", html)

    def test_generation_html_recalcul_js_sans_reseau(self) -> None:
        html = generer_html(self._charger_exemple(), entrees_projection=self._charger_entrees_projection_minimum())

        self.assertNotIn("fetch(", html)
        self.assertNotIn("XMLHttpRequest", html)
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)
        self.assertNotIn("<script src=", html)

    def test_generation_html_options_compteur_compactes(self) -> None:
        html = generer_html(self._charger_exemple())

        self.assertIn('for="choix-compteur-planification">Compteur</label>', html)
        self.assertIn('<option value="auto">Auto</option>', html)
        self.assertIn("selectChoixCompteur.value !== 'auto'", html)
        self.assertIn(": 'GCP';", html)
        self.assertIn("selectChoixCompteur.value = 'GCP';", html)
        self.assertNotIn("Auto — laisser le moteur choisir", html)
        self.assertNotIn("Compteur connu dans la projection ; règle de priorité non déterminée dans cette vue.", html)

    def test_generation_html_autosauvegarde_scenario_gui(self) -> None:
        html = generer_html(self._charger_exemple())

        for marqueur in (
            "chronotime.scenario_gui.v1",
            "chronotime.gui.autosauvegarde",
            "sauvegarderScenarioGuiAutomatiquement",
            "restaurerScenarioGuiAutosauvegarde",
            "etat-sauvegarde-scenario",
            "Sauvegarde impossible",
            "Restauration impossible",
            "localStorage.setItem(CLE_SCENARIO_GUI",
            "localStorage.getItem(CLE_SCENARIO_GUI)",
            "blocScenarioVersBlocLocalPrototype",
            "simulation.locale",
            "gui_locale",
        ):
            self.assertIn(marqueur, html)

        self.assertIn("chronotime.planification.prototype.v1", html)
        self.assertNotIn("Sauvegardé", html)
        self.assertNotIn("Restauré", html)
        self.assertNotIn("Aucun scénario local sauvegardé", html)
        self.assertNotIn("localStorage.setItem(CLE_STOCKAGE_PROTO", html)

    def test_generation_html_sans_libelle_visible_vivant(self) -> None:
        html = generer_html(self._charger_exemple(), entrees_projection=self._charger_entrees_projection_minimum())

        self.assertNotIn("vivant · Δ", html)
        self.assertNotIn(">vivant<", html)
        self.assertNotIn("Projection vivante", html)
        self.assertIn("projectionVivante", html)
        self.assertIn("projection_vivante", html)

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
        self.assertNotIn("Scinder", html)
        self.assertNotIn("Fusionner", html)

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

    def test_generation_fichier_html_avec_entrees_projection(self) -> None:
        with tempfile.TemporaryDirectory() as repertoire:
            chemin_sortie = Path(repertoire) / "vue.html"
            subprocess.run(
                [
                    sys.executable,
                    "outils/chronotime/generateur_vue_projection.py",
                    "--projection",
                    str(self._chemin_exemple()),
                    "--entrees-projection",
                    str(self._chemin_entrees_projection_minimum()),
                    "--sortie",
                    str(chemin_sortie),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            html = chemin_sortie.read_text(encoding="utf-8")
            self.assertIn("ChronotimeProjecteur", html)
            self.assertIn("projection.demi_journees.entrees", html)
            self.assertIn("projection-vivante-planification", html)

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


    def test_generation_html_modes_general_detaille_planification(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn('data-mode-planification="general"', html)
        self.assertIn('data-mode-planification="detaille"', html)
        self.assertIn("mode-affichage-actif", html)
        self.assertIn("modePlanification === 'general'", html)
        self.assertIn("selectionType === 'sous-bloc'", html)

    def test_generation_html_mise_en_valeur_plage_selection(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("selection-plage", html)
        self.assertIn("selection-plage-debut", html)
        self.assertIn("selection-plage-fin", html)
        self.assertIn("selection-jour-courant", html)
        self.assertIn("data-date-iso", html)

    def test_generation_html_barre_droite_stable_et_zid(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("barre-infos-droite-stable", html)
        self.assertIn("bloc-info-selection", html)
        self.assertIn("curseur-planification", html)
        self.assertIn("separateur-infos", html)
        self.assertIn("height: calc(100dvh", html)
        self.assertIn("max-height: calc(100dvh", html)
        self.assertIn("diagnostiquerDispositionCurseurPlanification", html)
        self.assertIn("rectangleMesureSelectionPlanification", html)
        self.assertIn("barreDepasseFenetre", html)
        self.assertIn("overflow-y: auto", html)
        self.assertIn("overflow-x: hidden", html)

    def test_generation_html_curseur_frise(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("ligne-curseur-frise", html)
        self.assertIn("point-curseur-frise", html)
        self.assertIn("mousemove", html)
        self.assertIn("mouseleave", html)
        self.assertIn("afficherCurseurPlanification", html)

    def test_generation_html_anti_selection_texte_planification(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("user-select: none", html)
        self.assertIn("dblclick", html)
        self.assertIn("event.preventDefault()", html)


    def test_generation_html_barre_droite_cloisonnee_zid_curseur(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("barre-infos-droite-stable", html)
        self.assertIn("grid-template-rows: minmax(0, auto) minmax(0, 1fr) auto", html)
        self.assertIn("bloc-info-selection", html)
        self.assertIn("grid-template-rows: auto minmax(0, 1fr)", html)
        self.assertIn("selection-planification", html)
        self.assertIn("height: 100%", html)
        self.assertIn("curseur-planification", html)
        self.assertIn("curseur-toujours-visible", html)
        self.assertIn("max-height: 86px", html)
        self.assertIn("window.diagnostiquerDispositionCurseurPlanification", html)
        self.assertIn("separateurInfos", html)
        self.assertIn("align-self: end", html)
        self.assertIn("overflow-y: hidden", html)
        self.assertIn("overflow: hidden", html)


    def test_generation_html_planification_barre_droite_compacte(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("resume-droite-compact", html)
        self.assertIn("resume-mini", html)
        self.assertIn("grille-compteurs-droite", html)
        self.assertIn("compteur-mini", html)
        self.assertNotIn("expiration-mini", html)
        self.assertIn("grid-template-columns: repeat(3, minmax(0, 1fr))", html)

    def test_generation_html_planification_densification_visuelle(self) -> None:
        html = generer_html(self._charger_exemple())
        self.assertIn("V0.4.6", html)
        self.assertIn("height: calc(100dvh - 118px)", html)
        self.assertIn("max-height: calc(100dvh - 118px)", html)
        self.assertNotIn("min-height: 500px", html)
        self.assertIn("font-size: 0.92rem", html)
        self.assertIn("white-space: nowrap", html)
        self.assertIn("text-overflow: ellipsis", html)
        self.assertIn("max-height: 76px", html)

    def _chemin_exemple(self) -> Path:
        return Path("donnees/exemples/projection_demi_journees.exemple.json")

    def _charger_exemple(self) -> dict[str, object]:
        return json.loads(self._chemin_exemple().read_text(encoding="utf-8"))

    def _chemin_entrees_projection_minimum(self) -> Path:
        return Path("donnees/exemples/entrees_projection_comparaison_minimum.exemple.json")

    def _charger_entrees_projection_minimum(self) -> dict[str, object]:
        return json.loads(self._chemin_entrees_projection_minimum().read_text(encoding="utf-8"))

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
