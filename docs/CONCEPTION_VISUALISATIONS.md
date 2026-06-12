# Conception des visualisations

L’outil Chronotime s’appuie sur plusieurs vues synchronisées. Elles partagent le même scénario local, les mêmes blocs et la même projection des soldes.

Les vues doivent rester des rendus dérivés d’un état central et de diagnostics produits par le moteur. Calendrier, frise, compteurs et alertes ne doivent pas maintenir chacun une logique métier séparée.

## Concept primaire

La vue primaire ne doit pas être une vue par compteurs.

Le concept central visé est le reste global agrégé.

Les compteurs techniques individuels restent utiles pour expliquer une situation, une contrainte ou une alerte, mais ils ne doivent pas être le premier niveau de lecture.

Le moteur devra préciser plus tard la formule exacte entre :

- reste agrégé total ;
- reste libre après réserves ;
- congés à conserver pour l’année suivante.

## Vue 1 : Vue calendrier

La vue calendrier est une vue centrale familière.

Elle sert à :

- repérer les dates civiles ;
- distinguer jours travaillés et non travaillés ;
- créer ou sélectionner des blocs ;
- montrer l’effet d’une action sur le reste agrégé via la barre d’informations ;
- rester un point d’entrée simple pour les utilisateurs qui raisonnent d’abord en calendrier.

## Vue 2 : Frise avec niveau de reste agrégé

La frise temporelle avec niveau est la vue principale de planification.

Elle sert à :

- afficher une période longue, par exemple une année civile ou une période glissante ;
- afficher des blocs d’absence ;
- distinguer absence réelle, absence simulée, congé imposé non posé et congé imposé posé ;
- superposer ou juxtaposer une courbe ou un niveau du reste agrégé sur le même axe temporel ;
- visualiser immédiatement l’impact d’un bloc sur le reste ;
- indiquer les contraintes lorsqu’un bloc ne peut plus être tiré ;
- déplacer un bloc ;
- redimensionner un bloc ;
- verrouiller un bloc ;
- ouvrir un éditeur détaillé ;
- zoomer entre année, trimestre, mois et semaine.

La frise et le niveau peuvent être superposés ou placés verticalement l’un au-dessus de l’autre.

Schéma conceptuel :

```text
[ blocs de congés / obligations / scénarios ]
-----------------------------------------------------> temps

[ niveau de reste agrégé ]
-----------------------------------------------------> temps
```

La frise est la vue principale d’édition, mais ses modifications doivent être traduites en modifications du modèle événementiel. La frise affiche ensuite la projection demi-journalière recalculée.

## Vue 3 : Projection Des Soldes

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

La future vue des soldes pourra s’appuyer sur :

- `projection.demi_journees` ;
- `mouvements.soldes` ;
- `chronologie.soldes`.

La GUI ne doit pas recalculer elle-même cette chronologie. Elle doit lire la sortie dérivée produite par le moteur.

La vue HTML locale peut afficher `chronologie.soldes` dans l’onglet `Soldes` lorsqu’un fichier est fourni au générateur. Cet affichage reste en lecture seule : il présente les soldes finaux, les points de chronologie et les alertes produits par le moteur sans recalculer les mouvements ni inventer de règles métier.

## Vue Planification Agrégée

La vue de planification agrégée est une lecture utilisateur de `synthese.planification`.

Elle doit afficher d’abord :

- les jours posés ;
- les jours expirés ;
- le reste agrégé final daté ;
- les échéances importantes, notamment les expirations ;
- les principaux blocs consommateurs ;
- les signaux utilisateur.

Les échéances datées préfigurent les futurs repères graphiques de la vue en écluses. Les compteurs techniques Chronotime restent disponibles ensuite, dans des détails repliables. Cette vue ne fait pas d’optimisation, ne modifie pas le scénario et ne recalcule pas les règles métier.

## Vue 4 : Calendrier Annuel Compact

Le calendrier annuel compact sert à vérifier rapidement l’année entière.

Il permet de :

- vérifier les dates civiles ;
- voir week-ends, jours fériés, repos et jours travaillés ;
- visualiser les demi-journées ;
- repérer les blocs qui mordent sur des jours non travaillés ;
- vérifier rapidement l’année entière.

## Barres communes

Les vues centrales doivent partager :

- une barre d’outils à gauche ;
- une barre d’informations à droite.

La barre d’outils gauche commune doit contenir au minimum :

- `poser des jours` ;
- `scinder des jours déjà posés` ;
- `joindre / fusionner` ;
- un mode `général` ;
- un mode `détaillé` ;
- des emplacements réservés pour des outils futurs.

Le mode général privilégie une lecture simple des jours travaillés, congés et blocs, sans distinction fine de compteur.

Le mode détaillé expose la nature exacte des blocs : compteur, droit parentalité, obligation, absence réelle, simulation, alerte et autres détails utiles.

La barre d’informations droite commune doit contenir au minimum :

- total restant ;
- dont prévus pour cette année ;
- détail compteurs ;
- prochaine expiration ;
- zone d’information sur la sélection ;
- autres champs futurs possibles.

La zone de sélection reste vide si rien n’est sélectionné.

Cette barre permet aussi à la vue calendrier de montrer l’effet d’une action sur le reste agrégé, même si la courbe de niveau n’est pas visible dans la zone centrale.

En état normal, la barre droite doit afficher seulement les résultats utiles. Les succès techniques de sauvegarde, restauration ou recalcul ne sont pas affichés ; les erreurs réelles et diagnostics bloquants restent visibles avec un message court.

## Interactions communes

Les interactions communes des vues centrales sont :

clic :

- sélection d’un élément ;
- affichage des détails dans la barre droite.

clic-déplacement :

- déplacement d’un bloc dans les limites des contraintes.

déplacement du début ou de la fin :

- redimensionnement du bloc.

survol :

- affichage d’une infobulle légère.

action non autorisée :

- signalement, blocage ou prévisualisation comme impossible.

Ces interactions modifient les blocs sources, puis déclenchent le recalcul de la projection.

En cible dynamique, le geste est d’abord converti en commande d’intention. Le moteur accepte ou refuse la commande, produit un état central recalculé ou inchangé, puis les vues se rafraîchissent depuis cet état et les diagnostics structurés.

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

## Points ouverts

- formule exacte du reste agrégé ;
- distinction entre reste total, reste libre et réserve pour l’année suivante ;
- règles d’allocation automatique des compteurs ;
- comportement précis de scission ;
- comportement précis de fusion ;
- affichage exact des contraintes pendant un déplacement ;
- degré d’édition autorisé dans la vue calendrier ;
- forme exacte de la courbe de niveau ;
- futur mode `préparer les actions Chronotime` ;
- éventuelle communication directe avec Chronotime, non prévue à ce stade.

## Confidentialité et limites

La GUI cible :

- reste locale ;
- ne doit pas écrire automatiquement dans Chronotime ;
- ne doit pas faire de `POST`, `PUT` ou `DELETE` vers Chronotime ;
- ne doit pas committer de vraies données ;
- ne doit pas intégrer de cookies, jetons, fichiers HAR, matricules ou exports réels.
