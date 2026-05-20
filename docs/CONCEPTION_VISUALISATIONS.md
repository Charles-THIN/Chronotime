# Conception des visualisations

L’outil Chronotime s’appuie sur trois vues synchronisées. Elles partagent le même scénario local, les mêmes blocs et la même projection des soldes.

## Vue 1 : Frise Temporelle 1D

La frise temporelle est la vue principale.

Elle sert à :

- afficher une période longue, par exemple une année civile ou une période glissante ;
- afficher des blocs d’absence ;
- distinguer absence réelle, absence simulée, congé imposé non posé et congé imposé posé ;
- déplacer un bloc ;
- redimensionner un bloc ;
- verrouiller un bloc ;
- ouvrir un éditeur détaillé ;
- zoomer entre année, trimestre, mois et semaine.

La frise est la vue principale d’édition, mais ses modifications doivent être traduites en modifications du modèle événementiel. La frise affiche ensuite la projection demi-journalière recalculée.

## Vue 2 : Projection Des Soldes

La projection des soldes montre l’impact futur des blocs sur chaque compteur.

Elle sert à :

- afficher les soldes par compteur ;
- afficher les soldes bruts Chronotime ;
- afficher les soldes après congés déjà posés ;
- afficher les soldes après congés imposés non encore posés ;
- afficher les soldes après simulation ;
- voir les dates d’expiration ;
- répondre à des questions du type : « que restera-t-il à Noël ? ».

Cette vue compare plusieurs états successifs du même scénario, sans mélanger données importées, règles de scénario et résultat calculé.

## Vue 3 : Calendrier Annuel Compact

Le calendrier annuel compact sert à vérifier rapidement l’année entière.

Il permet de :

- vérifier les dates civiles ;
- voir week-ends, jours fériés, repos et jours travaillés ;
- visualiser les demi-journées ;
- repérer les blocs qui mordent sur des jours non travaillés ;
- vérifier rapidement l’année entière.

## Synchronisation

Les trois vues sont synchronisées.

Exemples :

- déplacer un bloc dans la frise met à jour la projection des soldes ;
- cliquer sur un jour dans le calendrier sélectionne le bloc correspondant ;
- modifier un bloc dans l’éditeur met à jour les trois vues.

## Règles De Base

La conception repose sur quelques règles simples :

- un bloc simulé agit sur une période donnée et sur un compteur ciblé ;
- un bloc verrouillé ne peut pas être modifié sans action explicite ;
- une absence réelle importée depuis Chronotime reste distincte d’une absence simulée ;
- les congés imposés doivent pouvoir être distingués entre « déjà posés » et « non encore posés » ;
- les fractions de jour, les demi-journées, les jours calendaires et les heures doivent rester visibles et non ambiguës ;
- la projection doit montrer l’impact immédiat et l’impact futur selon les dates d’expiration.
