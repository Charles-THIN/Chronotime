import test from "node:test";
import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { projeterDemiJournees } from "../outils/chronotime/js/projecteur_demi_journees.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const racine = path.resolve(__dirname, "..");
const repertoireExemples = path.join(racine, "donnees", "exemples");

async function fichiersCorpus() {
  const noms = await readdir(repertoireExemples);
  return noms
    .filter((nom) => /^entrees_projection_comparaison.*\.exemple\.json$/.test(nom))
    .sort()
    .map((nom) => path.join(repertoireExemples, nom));
}

const alertesAttendues = {
  "entrees_projection_comparaison.exemple.json": [
    "periode_compteur_absente",
    "choix_compteur_auto_a_resoudre",
    "unite_non_projectee",
    "quantite_evenement_non_projectee",
    "evenement_hors_periode_projection",
    "solde_minimum_depasse",
    "solde_negatif_confirmation_possible",
    "date_cible_hors_periode",
  ],
  "entrees_projection_comparaison_choix_compteur.exemple.json": ["choix_compteur_auto_a_resoudre"],
  "entrees_projection_comparaison_dates_cibles.exemple.json": [
    "evenement_hors_periode_projection",
    "date_cible_hors_periode",
  ],
  "entrees_projection_comparaison_minimum.exemple.json": [],
  "entrees_projection_comparaison_minimums_soldes.exemple.json": [
    "solde_minimum_depasse",
    "solde_negatif_confirmation_possible",
  ],
  "entrees_projection_comparaison_periodes_compteurs.exemple.json": ["periode_compteur_absente"],
  "entrees_projection_comparaison_priorites.exemple.json": ["solde_minimum_depasse"],
  "entrees_projection_comparaison_unites.exemple.json": [
    "unite_non_projectee",
    "quantite_evenement_non_projectee",
  ],
};

test("projette tout le corpus artificiel", async () => {
  const fichiers = await fichiersCorpus();
  assert.ok(fichiers.length >= 2);

  for (const fichier of fichiers) {
    const nom = path.basename(fichier);
    const donnees = JSON.parse(await readFile(fichier, "utf8"));
    const projection = projeterDemiJournees(donnees);

    assert.equal(projection.source, "projection.demi_journees", nom);
    assert.ok(Array.isArray(projection.demi_journees), nom);
    assert.ok(projection.demi_journees.length > 0, nom);
    assert.equal(projection.resume.nombre_demi_journees, projection.demi_journees.length, nom);
    assert.ok(projection.demi_journees[0].soldes_avant, nom);
    assert.ok(projection.demi_journees[0].soldes_apres, nom);

    const typesAlertes = new Set(projection.alertes.map((alerte) => alerte.type));
    for (const typeAlerte of alertesAttendues[nom] || []) {
      assert.ok(typesAlertes.has(typeAlerte), `${nom} devrait contenir ${typeAlerte}`);
    }
  }
});
