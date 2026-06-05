import test from "node:test";
import assert from "node:assert/strict";
import { readFile, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { projeterDemiJournees } from "../outils/chronotime/js/projecteur_demi_journees.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const racine = path.resolve(__dirname, "..");
const entreeComparaison = path.join(racine, "donnees", "exemples", "entrees_projection_comparaison.exemple.json");

function canoniser(objet) {
  if (Array.isArray(objet)) {
    return objet.map(canoniser);
  }
  if (objet && typeof objet === "object") {
    return Object.fromEntries(
      Object.entries(objet)
        .sort(([cleA], [cleB]) => cleA.localeCompare(cleB))
        .map(([cle, valeur]) => [cle, canoniser(valeur)]),
    );
  }
  if (typeof objet === "number") {
    return Number(objet.toFixed(10));
  }
  return objet;
}

test("importe le module JS et projette l'entrée d'exemple", async () => {
  const donnees = JSON.parse(await readFile(entreeComparaison, "utf8"));
  const projection = projeterDemiJournees(donnees);

  assert.equal(projection.source, "projection.demi_journees");
  assert.ok(projection.demi_journees.length > 0);
  assert.ok(projection.demi_journees[0].soldes_avant);
  assert.ok(projection.demi_journees[0].soldes_apres);
});

test("compare la sortie JS avec la sortie Python de référence", async () => {
  const repertoire = await mkdtemp(path.join(tmpdir(), "chronotime-js-"));
  try {
    const sortiePython = path.join(repertoire, "projection_python.json");
    const sortieJs = path.join(repertoire, "projection_js.json");

    const python = spawnSync(
      "python",
      [
        "outils/chronotime/projecteur_demi_journees.py",
        entreeComparaison,
        "--sortie",
        sortiePython,
      ],
      { cwd: racine, encoding: "utf8" },
    );
    assert.equal(python.status, 0, python.stderr || python.stdout);

    const node = spawnSync(
      "node",
      [
        "outils/chronotime/js/cli_projecteur_demi_journees.js",
        entreeComparaison,
        "--sortie",
        sortieJs,
      ],
      { cwd: racine, encoding: "utf8" },
    );
    assert.equal(node.status, 0, node.stderr || node.stdout);

    const projectionPython = JSON.parse(await readFile(sortiePython, "utf8"));
    const projectionJs = JSON.parse(await readFile(sortieJs, "utf8"));
    assert.deepEqual(canoniser(projectionJs), canoniser(projectionPython));
  } finally {
    await rm(repertoire, { recursive: true, force: true });
  }
});
