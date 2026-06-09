from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
import unittest


REPERTOIRE_EXEMPLES = Path("donnees/exemples")


def canoniser_json(objet: Any) -> Any:
    if isinstance(objet, dict):
        return {cle: canoniser_json(objet[cle]) for cle in sorted(objet)}
    if isinstance(objet, list):
        return [canoniser_json(element) for element in objet]
    if isinstance(objet, float):
        return round(objet, 10)
    return objet


def premiere_difference(gauche: Any, droite: Any, chemin: str = "$") -> str | None:
    if isinstance(gauche, dict) and isinstance(droite, dict):
        cles_gauche = set(gauche)
        cles_droite = set(droite)
        if cles_gauche != cles_droite:
            return f"{chemin}: clés différentes {sorted(cles_gauche ^ cles_droite)}"
        for cle in sorted(gauche):
            difference = premiere_difference(gauche[cle], droite[cle], f"{chemin}.{cle}")
            if difference:
                return difference
        return None
    if isinstance(gauche, list) and isinstance(droite, list):
        if len(gauche) != len(droite):
            return f"{chemin}: longueurs différentes {len(gauche)} != {len(droite)}"
        for index, (element_gauche, element_droite) in enumerate(zip(gauche, droite, strict=True)):
            difference = premiere_difference(element_gauche, element_droite, f"{chemin}[{index}]")
            if difference:
                return difference
        return None
    if gauche != droite:
        return f"{chemin}: {gauche!r} != {droite!r}"
    return None


@unittest.skipIf(shutil.which("node") is None, "Node.js est absent.")
class TestProjecteurJsComparaison(unittest.TestCase):
    def test_projection_js_identique_projection_python_sur_corpus(self) -> None:
        fichiers_entree = sorted(REPERTOIRE_EXEMPLES.glob("entrees_projection_comparaison*.exemple.json"))
        self.assertGreaterEqual(len(fichiers_entree), 2)
        self.assertIn(
            "entrees_projection_comparaison_quantites_decomptees.exemple.json",
            {fichier.name for fichier in fichiers_entree},
        )

        with tempfile.TemporaryDirectory() as repertoire_temporaire:
            for entree in fichiers_entree:
                with self.subTest(entree=entree.name):
                    sortie_python = Path(repertoire_temporaire) / f"{entree.stem}_python.json"
                    sortie_js = Path(repertoire_temporaire) / f"{entree.stem}_js.json"

                    subprocess.run(
                        [
                            sys.executable,
                            "outils/chronotime/projecteur_demi_journees.py",
                            str(entree),
                            "--sortie",
                            str(sortie_python),
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    subprocess.run(
                        [
                            "node",
                            "outils/chronotime/js/cli_projecteur_demi_journees.js",
                            str(entree),
                            "--sortie",
                            str(sortie_js),
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                    )

                    projection_python = canoniser_json(json.loads(sortie_python.read_text(encoding="utf-8")))
                    projection_js = canoniser_json(json.loads(sortie_js.read_text(encoding="utf-8")))
                    difference = premiere_difference(projection_js, projection_python)

                    self.assertIsNone(difference, f"{entree.name}: {difference}")


if __name__ == "__main__":
    unittest.main()
