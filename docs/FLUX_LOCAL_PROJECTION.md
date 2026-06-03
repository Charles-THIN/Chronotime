# Flux local de projection

L’orchestrateur local assemble les fichiers JSON locaux et enchaîne les briques existantes.

Ce document décrit le flux local actuel par fichiers et commandes. Il ne définit pas à lui seul l’architecture de la future GUI dynamique.

```text
fichiers JSON locaux
-> normalisation
-> vérification des obligations
-> projection demi-journalière
-> mouvements de solde optionnels
-> chronologie cumulée optionnelle
```

## Entrées

Le flux prend quatre fichiers obligatoires :

- soldes Chronotime `soldeabs` ;
- agenda Chronotime `agenda` ;
- obligations locales ;
- scénario local.

Il accepte aussi une cinquième entrée facultative :

- événements de compteur.

Les vrais fichiers utilisateur doivent rester dans `donnees_locales/`. Les fichiers sous `donnees/exemples/` sont artificiels ou anonymisés.

## Étapes

L’orchestrateur :

- normalise les soldes avec le parseur `soldeabs` ;
- normalise l’agenda avec le parseur `agenda` ;
- normalise le scénario local ;
- normalise les obligations locales ;
- normalise les événements de compteur si un fichier est fourni ;
- vérifie les obligations avec l’agenda normalisé ;
- assemble l’entrée attendue par le projecteur ;
- lance la projection demi-journalière.

## Sortie

La sortie est directement le format `projection.demi_journees`.

Les événements de compteur sont transportés dans la projection sous `evenements_compteurs`, mais ils ne sont pas encore appliqués aux soldes.

Aucun fichier intermédiaire n’est écrit sauf si l’option `--sortie` est fournie pour la projection finale.

## Étape Aval Optionnelle : Mouvements De Solde

Une projection `projection.demi_journees` peut ensuite être transformée en mouvements signés :

```powershell
python outils/chronotime/generateur_mouvements_soldes.py donnees_locales/projection_avec_evenements_compteurs.json --sortie donnees_locales/mouvements_soldes.json
```

La sortie `mouvements.soldes` est dérivée. Elle ne calcule pas encore une chronologie cumulée des soldes.

Le fichier `donnees_locales/mouvements_soldes.json` ne doit pas être suivi par Git.

## Étape Aval Optionnelle : Chronologie Des Soldes

Les mouvements signés peuvent ensuite être cumulés :

```powershell
python outils/chronotime/generateur_chronologie_soldes.py `
  --projection donnees_locales/projection_avec_evenements_compteurs.json `
  --mouvements donnees_locales/mouvements_soldes.json `
  --sortie donnees_locales/chronologie_soldes.json
```

La sortie `chronologie.soldes` est dérivée. Elle cumule les mouvements par code de compteur, sans gérer encore la validité fine par période `precedent`, `courant` ou `suivant`.

Le fichier `donnees_locales/chronologie_soldes.json` ne doit pas être suivi par Git.

## Exemple De Commande Locale

```powershell
python outils/chronotime/orchestrateur_projection.py `
  --soldes donnees_locales/soldes_absences_chronotime.json `
  --agenda donnees_locales/agenda_chronotime.json `
  --obligations donnees_locales/obligations_conges_2026.json `
  --scenario donnees_locales/scenario_vide.json `
  --evenements-compteurs donnees_locales/evenements_compteurs.json `
  --date-depart 2026-05-20 `
  --date-fin 2026-12-31 `
  --periode-compteurs courant `
  --periodes-compteurs-par-code GCP=suivant,JRTT=courant,CANC=courant `
  --soldes-minimums-par-code JRTT=-10,GCP=0,CANC=0 `
  --jours-non-decomptes 2026-12-25,2026-07-14,2026-08-15 `
  --date-cible noel=Noël=2026-12-25 `
  --sortie donnees_locales/projection_obligations_seules.json
```

Si `--date-depart` et `--date-fin` ne sont pas fournis, l’orchestrateur utilise la période du scénario local.

Les valeurs `GCP=suivant`, `JRTT=-10` et les jours non décomptés sont des hypothèses opérationnelles à vérifier.

## Limites

L’orchestrateur reste local.

Il ne se connecte pas à Chronotime, ne fait aucun appel HTTP, n’automatise pas de navigateur et ne modifie pas Chronotime.

## Lien Avec La Future GUI Dynamique

La future GUI dynamique pourra réutiliser les mêmes concepts :

- sources événementielles ;
- scénario local ;
- projection recalculée ;
- diagnostics ;
- vues dérivées.

Elle n’est pas obligée de lancer une commande shell à chaque interaction. Le point obligatoire est de conserver une séparation claire entre moteur, état central et rendu visuel.

Un geste utilisateur devra devenir une commande d’intention, validée par le moteur, puis affichée à partir de l’état recalculé ou des diagnostics de refus.
