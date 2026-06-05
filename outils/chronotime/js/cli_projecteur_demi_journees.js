import { readFile, writeFile } from "node:fs/promises";
import { projeterDemiJournees } from "./projecteur_demi_journees.js";

function analyserArguments(argv) {
  const argumentsCli = [...argv];
  const entree = argumentsCli.shift();
  if (!entree) {
    throw new Error("Usage : node outils/chronotime/js/cli_projecteur_demi_journees.js entree.json [--sortie sortie.json]");
  }

  let sortie = null;
  for (let index = 0; index < argumentsCli.length; index += 1) {
    const argument = argumentsCli[index];
    if (argument === "--sortie") {
      sortie = argumentsCli[index + 1] || null;
      index += 1;
      continue;
    }
    throw new Error(`Argument inconnu : ${argument}`);
  }

  return { entree, sortie };
}

async function main() {
  const { entree, sortie } = analyserArguments(process.argv.slice(2));
  const texte = await readFile(entree, "utf8");
  const donnees = JSON.parse(texte.replace(/^\uFEFF/, ""));
  const projection = projeterDemiJournees(donnees);
  const json = `${JSON.stringify(projection, null, 2)}\n`;

  if (sortie) {
    await writeFile(sortie, json, "utf8");
    return;
  }
  process.stdout.write(json);
}

main().catch((erreur) => {
  process.stderr.write(`${erreur.message}\n`);
  process.exitCode = 1;
});
