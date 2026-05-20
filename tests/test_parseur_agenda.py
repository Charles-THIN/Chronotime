from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from outils.chronotime.parseur_agenda import (
    MODELE_SOURCE,
    construire_dictionnaires_normalises,
    indexer_par_code,
    normaliser_date_chronotime,
    normaliser_donnees,
    normaliser_horaire_chronotime,
    normaliser_statut,
    normaliser_unite,
)


class TestParseurAgenda(unittest.TestCase):
    def test_normaliser_date_20260518(self) -> None:
        self.assertEqual(normaliser_date_chronotime("20260518"), "2026-05-18")

    def test_normaliser_horaire_0(self) -> None:
        self.assertEqual(normaliser_horaire_chronotime(0), "00:00")

    def test_normaliser_horaire_916(self) -> None:
        self.assertEqual(normaliser_horaire_chronotime(916), "09:16")

    def test_normaliser_horaire_1159(self) -> None:
        self.assertEqual(normaliser_horaire_chronotime(1159), "11:59")

    def test_normaliser_horaire_2359(self) -> None:
        self.assertEqual(normaliser_horaire_chronotime(2359), "23:59")

    def test_normaliser_unite_m(self) -> None:
        self.assertEqual(
            normaliser_unite("M", {"M": "Matin"}),
            {"code": "M", "libelle": "Matin", "fraction_jour": 0.5},
        )

    def test_normaliser_unite_s(self) -> None:
        self.assertEqual(
            normaliser_unite("S", {"S": "Après-midi"}),
            {"code": "S", "libelle": "Après-midi", "fraction_jour": 0.5},
        )

    def test_normaliser_unite_j(self) -> None:
        self.assertEqual(
            normaliser_unite("J", {"J": "Jour complet"}),
            {"code": "J", "libelle": "Jour complet", "fraction_jour": 1.0},
        )

    def test_normaliser_statut_a(self) -> None:
        self.assertEqual(
            normaliser_statut("A", {"A": {"code": "A", "libelle": "Accepté"}}),
            {"code": "A", "libelle": "Accepté"},
        )

    def test_indexer_liste_par_cod(self) -> None:
        self.assertEqual(indexer_par_code([{"cod": "A", "lib": "Accepté"}]), {"A": {"cod": "A", "lib": "Accepté"}})

    def test_indexer_liste_par_code(self) -> None:
        self.assertEqual(indexer_par_code([{"code": "M", "libelle": "Matin"}]), {"M": {"code": "M", "libelle": "Matin"}})

    def test_dictionnaires_sous_forme_de_listes(self) -> None:
        donnees = self._charger_exemple_normalise()
        self.assertEqual(donnees["dictionnaires"]["absences"]["CANC"]["groupe_code"], "C")
        self.assertEqual(donnees["dictionnaires"]["statuts"]["A"]["libelle"], "Accepté")
        self.assertEqual(donnees["dictionnaires"]["unites"]["M"]["libelle"], "Matin")
        self.assertEqual(donnees["dictionnaires"]["unites"]["S"]["libelle"], "Après-midi")
        self.assertEqual(donnees["dictionnaires"]["unites"]["J"]["libelle"], "Jour complet")
        self.assertEqual(donnees["dictionnaires"]["unites"]["H"]["libelle"], "Heure")

    def test_compatibilite_dictionnaires_indexes(self) -> None:
        dictionnaires = construire_dictionnaires_normalises(
            {
                "abs": {"CANC": {"lib": "ABS CP ANCIENNETE", "grp": "C"}},
                "wkf": {"A": {"lib": "Accepté"}},
                "untabs": {"M": {"lib": "Matin"}},
                "hor": {"JTRAV": {"lib": "Jour travaillé", "re": False}},
            }
        )
        self.assertEqual(dictionnaires["absences"]["CANC"]["libelle"], "ABS CP ANCIENNETE")
        self.assertEqual(dictionnaires["statuts"]["A"]["libelle"], "Accepté")
        self.assertEqual(dictionnaires["unites"]["M"]["libelle"], "Matin")
        self.assertEqual(dictionnaires["horaires"]["JTRAV"]["repos"], False)

    def test_parsing_absence_canc_matin(self) -> None:
        donnees = self._charger_exemple_normalise()
        evenement = next(
            evenement
            for evenement in donnees["evenements"]
            if evenement["categorie"] == "absence" and evenement["code"] == "CANC"
        )
        self.assertEqual(evenement["date"], "2026-05-18")
        self.assertEqual(evenement["libelle"], "ABS CP ANCIENNETE (CANC)")
        self.assertEqual(evenement["unite"]["code"], "M")
        self.assertEqual(evenement["unite"]["fraction_jour"], 0.5)
        self.assertEqual(evenement["horaire"]["debut_brut"], 0)
        self.assertEqual(evenement["horaire"]["fin_brut"], 1159)
        self.assertEqual(evenement["horaire"]["debut"], "00:00")
        self.assertEqual(evenement["horaire"]["fin"], "11:59")
        self.assertEqual(evenement["statut"]["code"], "A")

    def test_parsing_absence_telv_apres_midi(self) -> None:
        donnees = self._charger_exemple_normalise()
        evenement = next(
            evenement
            for evenement in donnees["evenements"]
            if evenement["categorie"] == "absence" and evenement["code"] == "TELV"
        )
        self.assertEqual(evenement["date"], "2026-05-18")
        self.assertEqual(evenement["libelle"], "TELE CONTRA VARIABLE (TELV)")
        self.assertEqual(evenement["unite"]["code"], "S")
        self.assertEqual(evenement["unite"]["libelle"], "Après-midi")
        self.assertEqual(evenement["horaire"]["debut_brut"], 1159)
        self.assertEqual(evenement["horaire"]["fin_brut"], 2359)
        self.assertEqual(evenement["statut"]["libelle"], "Accepté")

    def test_parsing_evenement_horaire(self) -> None:
        donnees = self._charger_exemple_normalise()
        evenement = next(
            evenement
            for evenement in donnees["evenements"]
            if evenement["categorie"] == "horaire" and evenement["code"] == "230019001"
        )
        self.assertEqual(evenement["libelle"], "4CRC Rep calendaire")
        self.assertTrue(evenement["repos"])

    def test_code_horaire_numerique_jour_travaille(self) -> None:
        donnees = self._charger_exemple_normalise()
        evenement = next(
            evenement
            for evenement in donnees["evenements"]
            if evenement["categorie"] == "horaire" and evenement["code"] == "230010003"
        )
        self.assertEqual(evenement["libelle"], "4C01 Forfait jour 7h/j")
        self.assertFalse(evenement["repos"])

    def test_sortie_sans_identifiants_internes(self) -> None:
        texte = json.dumps(self._charger_exemple_normalise(), ensure_ascii=False)
        for cle_interdite in ("uid", "row", "acn", "acp", "<ID>", "<USER>"):
            self.assertNotIn(cle_interdite, texte)

    def test_resume_types_ignores(self) -> None:
        donnees = self._charger_exemple_normalise()
        self.assertEqual(donnees["resume_source"]["types_evenements_ignores"], {"2": 2, "9": 8})

    def test_script_en_ligne_de_commande_sans_sortie(self) -> None:
        chemin_exemple = Path("donnees/exemples/agenda_chronotime.exemple.json")
        resultat = subprocess.run(
            [sys.executable, "outils/chronotime/parseur_agenda.py", str(chemin_exemple)],
            check=True,
            capture_output=True,
            text=True,
        )
        donnees = json.loads(resultat.stdout)
        self.assertEqual(donnees["source"], MODELE_SOURCE)

    def test_script_en_ligne_de_commande_avec_sortie(self) -> None:
        chemin_exemple = Path("donnees/exemples/agenda_chronotime.exemple.json")
        with tempfile.TemporaryDirectory() as repertoire_temporaire:
            chemin_sortie = Path(repertoire_temporaire) / "sortie.json"
            subprocess.run(
                [
                    sys.executable,
                    "outils/chronotime/parseur_agenda.py",
                    str(chemin_exemple),
                    "--sortie",
                    str(chemin_sortie),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            donnees = json.loads(chemin_sortie.read_text(encoding="utf-8"))
            self.assertEqual(donnees["source"], MODELE_SOURCE)

    def _charger_exemple_normalise(self) -> dict[str, object]:
        chemin_exemple = Path("donnees/exemples/agenda_chronotime.exemple.json")
        donnees_brutes = json.loads(chemin_exemple.read_text(encoding="utf-8"))
        return normaliser_donnees(donnees_brutes)


if __name__ == "__main__":
    unittest.main()
