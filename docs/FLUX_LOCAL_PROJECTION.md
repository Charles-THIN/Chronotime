# Flux local de projection

L’orchestrateur local assemble les fichiers JSON locaux et enchaîne les briques existantes.

```text
fichiers JSON locaux
-> normalisation
-> vérification des obligations
-> projection demi-journalière
```

## Entrées

Le flux prend quatre fichiers :

- soldes Chronotime `soldeabs` ;
- agenda Chronotime `agenda` ;
- obligations locales ;
- scénario local.

Les vrais fichiers utilisateur doivent rester dans `donnees_locales/`. Les fichiers sous `donnees/exemples/` sont artificiels ou anonymisés.

## Étapes

L’orchestrateur :

- normalise les soldes avec le parseur `soldeabs` ;
- normalise l’agenda avec le parseur `agenda` ;
- normalise le scénario local ;
- normalise les obligations locales ;
- vérifie les obligations avec l’agenda normalisé ;
- assemble l’entrée attendue par le projecteur ;
- lance la projection demi-journalière.

## Sortie

La sortie est directement le format `projection.demi_journees`.

Aucun fichier intermédiaire n’est écrit sauf si l’option `--sortie` est fournie pour la projection finale.

## Exemple De Commande Locale

```powershell
python outils/chronotime/orchestrateur_projection.py `
  --soldes donnees_locales/soldes_absences_chronotime.json `
  --agenda donnees_locales/agenda_chronotime.json `
  --obligations donnees_locales/obligations_conges_2026.json `
  --scenario donnees_locales/scenario_vide.json `
  --date-depart 2026-05-20 `
  --date-fin 2026-12-31 `
  --periode-compteurs courant `
  --periodes-compteurs-par-code GCP=suivant,JRTT=courant,CANC=courant `
  --soldes-minimums-par-code JRTT=-10,GCP=0,CANC=0 `
  --jours-non-decomptes 2026-12-25,2026-07-14,2026-08-15 `
  --date-cible noel=Noël=2026-12-25 `
  --sortie donnees_locales/projection_obligations_seules.json
```

Les valeurs `GCP=suivant`, `JRTT=-10` et les jours non décomptés sont des hypothèses opérationnelles à vérifier.

## Limites

L’orchestrateur reste local.

Il ne se connecte pas à Chronotime, ne fait aucun appel HTTP, n’automatise pas de navigateur et ne modifie pas Chronotime.
