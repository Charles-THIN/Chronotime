# AGENTS.md

## Rôle du projet

Ce dépôt contient un outil local de visualisation et de simulation personnelle des congés.

L’objectif est d’aider à comprendre, simuler et planifier :

- les soldes de congés ;
- les congés imposés ou fortement contraints ;
- les jours de repos liés au forfait annuel en jours ;
- les congés liés à la parentalité ;
- les absences à reporter ensuite manuellement dans Chronotime.

L’outil doit rester un outil local de lecture, de calcul, de simulation et de visualisation.

Il ne doit pas devenir un outil d’écriture automatique dans Chronotime.

## Langue de travail

Utiliser le français pour :

- les rapports ;
- la documentation destinée à l’utilisateur ;
- les fichiers de tâche ;
- les noms de fichiers Markdown lorsque cela est naturel.

Les identifiants techniques, noms de paquets, commandes, API, variables et noms de fonctions peuvent rester en anglais lorsque c’est plus naturel.

## Flux de travail principal

Avant toute modification, lire :

    docs/PROCHAINE_TÂCHE.md

Ce fichier est la tâche courante faisant autorité.

Ne pas élargir la tâche.

Ne pas redessiner l’architecture sauf nécessité technique réelle et explicitement signalée dans le rapport.

Après implémentation, écrire un rapport local court dans :

    RAPPORT_CODEX_LOCAL.md

Ne pas committer `RAPPORT_CODEX_LOCAL.md` sauf instruction explicite.

Le rapport doit contenir :

- résumé des changements ;
- fichiers créés ou modifiés ;
- commandes lancées ;
- résultats des commandes ;
- état des tests ou de la compilation ;
- déviations éventuelles par rapport à la tâche ;
- blocages ou questions.

## Confidentialité et frontière du dépôt

Le dépôt peut être public.

Ne jamais committer :

- exports Chronotime réels ;
- captures d’écran ;
- journaux bruts ;
- cookies ;
- jetons de session ;
- jetons OAuth ;
- `credentials.json` ;
- `token.pickle` ;
- URL internes ;
- données personnelles de calendrier ;
- documents internes d’entreprise ;
- données RH réelles ;
- noms de collègues, managers ou RH ;
- matricules ou identifiants internes ;
- données familiales personnelles précises.

N’utiliser que des données d’exemple anonymisées.

Les données privées ou semi-privées doivent rester hors dépôt, par exemple dans :

    donnees_locales/

Ce dossier doit rester ignoré par Git.

## Règles de sécurité Chronotime

Le projet pourra inclure plus tard un import local ou une extraction en lecture seule depuis Chronotime.

Règle par défaut :

    Lire et simuler localement.
    Ne jamais écrire dans Chronotime.

Ne jamais implémenter de soumission, validation, annulation ou modification automatique de demandes Chronotime sauf demande explicite et clarification légale/contractuelle préalable.

Ne pas contourner :

- l’authentification ;
- le SSO ;
- la double authentification ;
- les politiques navigateur ;
- les politiques d’entreprise ;
- les contrôles d’accès.

Ne jamais stocker de mot de passe.

Ne jamais committer de cookie de session, jeton Bearer ou autre secret.

## Google Drive et rapports

Google Drive peut servir de document privé de pilotage du projet.

L’automatisation Google Drive ne doit être implémentée que si la tâche courante le demande explicitement.

Si des scripts Google API sont ajoutés :

- garder les identifiants OAuth et jetons hors Git ;
- préférer les permissions en lecture seule sauf nécessité explicite ;
- garder les scripts courts et ciblés ;
- ne pas envoyer de journaux bruts ni de données sensibles ;
- expurger les rapports avant partage.

## Règles Git

Garder les changements minimaux et limités à la tâche.

Ne pas reformater des fichiers sans rapport.

Ne pas renommer des fichiers sans demande explicite.

Ne pas ajouter de gros cadre logiciel, base de données, système de compilation ou dépendance lourde sans demande explicite ou nécessité clairement justifiée.

Avant de déclarer la tâche terminée :

- inspecter le diff ;
- signaler tout changement inattendu ;
- vérifier que les fichiers sensibles ne sont pas suivis par Git.

## Principes de modèle de données

Séparer autant que possible :

- données brutes importées ;
- compteurs normalisés ;
- congés imposés ;
- absences simulées ;
- règles légales ou contractuelles ;
- état d’affichage de l’interface.

Ne pas coder en dur de vraies données personnelles dans le code source.

Utiliser des fichiers JSON d’exemple pour les démonstrations.

Les compteurs tels que `GCP`, `JRTT` et `CANC` doivent être configurables.

Ne pas supposer qu’ils sont universels.

## Règles de planification des congés

L’outil doit distinguer :

- solde brut affiché par Chronotime ;
- solde après absences déjà posées ;
- solde après congés imposés non encore posés ;
- solde après absences simulées.

Les congés imposés doivent être représentés comme des obligations à planifier, non comme de simples suggestions.

Les unités doivent toujours être explicites :

- jours ouvrés ;
- jours ouvrables ;
- jours calendaires ;
- demi-journées ;
- heures si nécessaire plus tard.

Ne jamais mélanger silencieusement ces unités.

## Style d’implémentation

Préférer du code simple, explicite et testable.

Éviter les abstractions prématurées.

Séparer autant que possible :

- chargement des données ;
- normalisation ;
- règles métier ;
- calculs ;
- interface utilisateur.

Ne pas figer des hypothèses incertaines sur :

- le droit français ;
- la convention collective ;
- les accords d’entreprise ;
- le fonctionnement réel de Chronotime.

Lorsqu’une règle est incertaine, la rendre configurable ou la signaler dans le rapport.

## Tests et validation

Exécuter les commandes indiquées dans :

    docs/PROCHAINE_TÂCHE.md

Si aucune commande n’est indiquée, lancer les vérifications minimales adaptées à l’état du dépôt, par exemple :

- compilation Python des fichiers modifiés ;
- tests unitaires existants ;
- compilation TypeScript si le projet en utilise ;
- construction de l’application si elle existe.

Ne pas inventer un résultat de test.

Si une commande ne peut pas être lancée, l’indiquer explicitement.

## Format du rapport Codex

Le fichier `CODEX_REPORT_LOCAL.md` doit suivre ce format :

# Codex report

## Summary

Résumé court des changements.

## Files changed

Liste des fichiers créés ou modifiés.

## Commands run

Liste des commandes exécutées.

## Results

Résultats des commandes, tests ou compilation.

## Deviations

Déviations par rapport à la tâche.

Écrire `None.` s’il n’y en a pas.

## Blockers or questions

Blocages ou questions restantes.

Écrire `None.` s’il n’y en a pas.

## En cas d’incertitude

Ne pas deviner silencieusement.

Faire la plus petite implémentation raisonnable compatible avec `docs/PROCHAINE_TÂCHE.md`.

Si une décision a un impact architectural durable, la documenter dans le rapport au lieu de prendre une grande décision cachée.
