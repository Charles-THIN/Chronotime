# Conception GUI

## Portée

Cette première étape ajoute une visualisation locale statique et en lecture seule d’une projection `projection.demi_journees`.

Elle sert à vérifier que la projection demi-journalière est exploitable pour une future interface graphique.

Elle ne crée pas encore d’interface éditable.

## Règle d’architecture

La GUI doit respecter le flux suivant :

```text
modèle événementiel source
-> projection demi-journalière dérivée
-> vues de lecture
```

La projection demi-journalière ne doit pas devenir une source de vérité éditable.

Les futures actions utilisateur devront modifier les événements sources ou les blocs de scénario, puis recalculer la projection.

## Concept primaire

La vue primaire ne doit pas être organisée d’abord par compteurs individuels.

Concept primaire :

- reste global agrégé.

Concepts secondaires :

- détail par compteur ;
- mouvements de solde ;
- expirations ;
- règles d’allocation ;
- justification des alertes.

Le détail par compteur reste utile, mais comme vue avancée, panneau explicatif ou détail repliable.

Le reste agrégé devra probablement distinguer plus tard :

- le reste agrégé total ;
- le reste libre après réserves ;
- les congés à conserver pour l’année suivante.

La formule exacte du reste agrégé n’est pas encore figée côté moteur. La GUI doit donc traiter cette notion comme une cible de conception, pas comme une règle déjà stabilisée.

## Vues centrales principales

La cible GUI à moyen terme repose sur deux vues centrales principales.

### Vue calendrier

Rôle :

- vue familière ;
- repérage civil des congés ;
- affichage des jours travaillés et non travaillés ;
- création ou sélection de blocs ;
- effet sur le reste agrégé visible dans la barre d’informations.

### Vue frise avec niveau

Rôle :

- vue principale de planification ;
- frise des blocs de congés ;
- courbe ou niveau du reste agrégé aligné sur le même axe temporel ;
- visualisation immédiate de l’impact d’un bloc sur le reste ;
- indication des contraintes lorsque le bloc ne peut plus être tiré.

La frise et le niveau pourront être superposés ou placés verticalement l’un au-dessus de l’autre.

Schéma conceptuel :

```text
[ blocs de congés / obligations / scénarios ]
-----------------------------------------------------> temps

[ niveau de reste agrégé ]
-----------------------------------------------------> temps
```

## Barre d’outils gauche commune

La GUI cible doit partager une barre d’outils gauche commune entre les vues centrales.

Contenu fixé actuellement :

- outil `poser des jours` ;
- outil `scinder des jours déjà posés` ;
- outil `joindre / fusionner` ;
- groupe de boutons de mode `général` et `détaillé` ;
- emplacements réservés pour outils futurs.

Mode général :

- affichage sans distinction fine de compteur ;
- lecture centrée sur jours travaillés, congés et blocs.

Mode détaillé :

- affichage de la nature exacte des blocs ;
- compteur, droit parentalité, obligation, absence réelle, simulation, alerte et autres détails utiles.

## Barre d’informations droite commune

La GUI cible doit partager une barre d’informations droite commune entre les vues centrales.

Contenu fixé actuellement :

- total restant ;
- dont prévus pour cette année ;
- détail compteurs ;
- prochaine expiration ;
- zone d’information sur la sélection ;
- autres champs futurs possibles.

La zone de sélection reste vide si rien n’est sélectionné.

Cette barre doit aussi permettre à la vue calendrier de montrer l’effet d’une action sur le reste agrégé, même si la courbe de niveau n’est pas visible au centre.

## Interactions communes des vues centrales

Les interactions centrales visées sont les suivantes :

clic sur un élément :

- sélectionne l’élément ;
- affiche ses détails dans la barre droite.

clic-déplacement d’un élément :

- déplace le bloc dans les limites des contraintes.

clic-déplacement du début ou de la fin :

- modifie la période ou la durée du bloc.

survol :

- affiche une infobulle légère.

action non autorisée :

- doit être signalée, bloquée ou prévisualisée comme impossible.

Ces interactions doivent modifier les blocs sources, puis déclencher un recalcul de la projection.

## Points ouverts de conception

Points encore ouverts à documenter côté moteur et GUI :

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

## Générateur statique V0

Le générateur local lit un fichier JSON déjà produit par l’orchestrateur local, puis écrit une page HTML autonome.

Commande avec données locales privées :

```powershell
python outils/chronotime/generateur_vue_projection.py `
  --projection donnees_locales/projection_obligations_seules_v2.json `
  --sortie donnees_locales/vue_projection.html
```

Commande de démonstration avec données artificielles :

```powershell
python outils/chronotime/generateur_vue_projection.py `
  --projection donnees/exemples/projection_demi_journees.exemple.json `
  --sortie donnees_locales/vue_projection_exemple.html
```

## Contenu affiché

La page HTML affiche :

- un titre clair ;
- le résumé global de projection ;
- les soldes initiaux ;
- les soldes aux dates cibles ;
- les alertes globales avec leur sévérité ;
- une frise 1D simple des demi-journées ;
- les détails des demi-journées consommées ou alertées.

## V0.1 Lisibilité

La version `V0.1` améliore la lisibilité sans changer le rôle de la vue :

- dates françaises lisibles ;
- tableaux de soldes lisibles ;
- alertes humanisées ;
- frise avec repères temporels ;
- détails techniques repliables.

Cette vue reste strictement en lecture seule.

La projection reste une sortie dérivée et non la source de vérité éditable.

## V0.2 Tableau de bord local

La version `V0.2` réorganise la page en vues séparées :

- `Vue d’ensemble`
- `Frise`
- `Soldes`
- `Alertes`
- `Détails`
- `Technique`

La navigation reste entièrement locale.

Le JavaScript éventuel ne sert qu’à afficher ou masquer les vues. Il ne charge aucune ressource externe et n’écrit aucun fichier.

La page reste strictement en lecture seule.

Aucune édition du scénario ou de la projection n’est réalisée.

## V0.3 Événements projetés compacts

La version `V0.3` remplace la vue `Détails` par `Événements projetés`.

Les demi-journées utiles y sont agrégées par identifiant d’événement pour produire des cartes compactes de lecture.

Ces cartes n’affichent que les informations utiles :

- période projetée ;
- compteur ou compteurs consommés ;
- quantité appliquée ;
- quantité non couverte seulement si elle est non nulle ;
- alertes seulement si elles existent.

Les détails techniques complets restent disponibles dans des blocs repliables.

La frise regroupe plus clairement les paires matin / après-midi par jour, avec le numéro du jour au-dessus des deux cases.

Cette vue reste strictement en lecture seule.

L’agrégation `Événements projetés` est une aide de consultation dérivée de `projection.demi_journees`. Elle ne devient pas un modèle éditable.

## V0.3.1 Finition visuelle

La version `V0.3.1` compacte le bandeau supérieur et contient les tableaux larges dans des zones de défilement horizontal locales.

Les objectifs sont limités à la lisibilité :

- titre principal plus compact ;
- tableaux larges contenus dans la carte ;
- aucune nouvelle logique métier ;
- vue toujours strictement en lecture seule.

## V0.4 Planification passive

La version `V0.4` ajoute une première structure concrète de planification en trois zones :

- barre d’outils gauche passive ;
- zone centrale de planification ;
- barre d’informations droite passive.

La barre d’outils gauche affiche les outils prévus, sans interaction réelle :

- poser des jours ;
- scinder ;
- fusionner ;
- mode général ;
- mode détaillé.

La zone centrale affiche deux vues passives :

- calendrier ;
- frise avec niveau.

Le niveau affiché est un `reste agrégé provisoire`.

Cette formule est temporaire. Elle sert uniquement à tester la lecture visuelle de la future interface et n’inclut pas encore :

- réserves ;
- expirations fines ;
- acquisitions futures ;
- règles d’allocation complètes.

La barre d’informations droite affiche une première lecture passive :

- total restant ;
- dont prévus pour cette année, non calculé à ce stade ;
- détail compteurs ;
- prochaine expiration, non calculée à ce stade ;
- sélection, vide si rien n’est sélectionné.

Cette version ne fait aucune édition :

- aucune création de bloc ;
- aucun déplacement ;
- aucun redimensionnement ;
- aucune scission ;
- aucune fusion ;
- aucune sauvegarde ;
- aucune écriture Chronotime.

## V0.4.1 Corrections visuelles de la planification passive

La version `V0.4.1` corrige les premiers défauts visuels de la vue `Planification`.

Corrections d'affichage :

- la structure de planification utilise davantage la largeur disponible ;
- la sous-vue `Frise` devient accessible par un bouton local cliquable ;
- les cartes textuelles qui encombraient la frise sont retirées de cette sous-vue ;
- la frise est agrandie ;
- l'axe horizontal affiche des repères de mois et des graduations de jours ;
- l'axe vertical du reste agrégé provisoire affiche des graduations numériques ;
- la barre d'informations droite est compactée.

La barre droite affiche uniquement une synthèse de consultation :

- total restant ;
- cette année, non calculé à ce stade ;
- compteurs principaux ;
- expiration, non calculée à ce stade ;
- sélection courante.

Les compteurs nuls sont masqués dans la barre principale, sauf compteurs courants importants comme `GCP`, `JRTT` et `CANC`, ou compteur explicitement lié à la parentalité dans les données.

Le tri cible des compteurs est un tri par proximité d'expiration réelle. Cette information n'est pas encore disponible de façon fiable dans le modèle ; la V0.4.1 utilise donc un repli temporaire :

- compteurs non nuls ;
- compteurs importants ;
- autres compteurs ;
- compteurs nuls ;
- ordre alphabétique à l'intérieur d'un groupe.

Ce repli sera remplacé lorsque les dates d'expiration explicites seront disponibles dans les données moteur.

Ces corrections restent purement visuelles. Elles ne stabilisent pas la formule métier du reste agrégé et n'ajoutent aucune édition, optimisation, sauvegarde ou écriture Chronotime.

## Vue future des soldes dans le temps

Une future vue `Soldes dans le temps` devra représenter :

- les descentes de soldes dues aux consommations ;
- plus tard, les montées dues aux crédits, acquisitions, ouvertures de validité et reports.

Ces événements de compteur ne sont pas encore produits par le projecteur actuel. Cette tâche ne les implémente pas.

## Frise 1D

Chaque demi-journée est représentée par une petite case.

Les états visuels minimaux sont :

- demi-journée sans consommation ;
- demi-journée avec consommation appliquée ;
- demi-journée avec quantité non couverte ;
- demi-journée avec alerte.

Cette frise est une vue de lecture. Elle ne doit pas être interprétée comme une grille éditable du modèle source.

## Détails des consommations

Pour les détails, l’interface doit préférer `consommations_detaillees` à `consommations`.

Le résumé `consommations` reste utile pour des lectures rapides, mais il ne suffit pas pour diagnostiquer les cas de solde minimum.

Les champs suivants doivent rester visibles :

- `quantite_demandee` ;
- `quantite_appliquee` ;
- `quantite_non_couverte`.

## Alertes

Les sévérités affichées sont :

- `information` ;
- `confirmation` ;
- `bloquant`.

La première vue doit montrer les alertes sans décider automatiquement si la situation est acceptable.

Les détails techniques complets peuvent rester visibles, mais seulement dans des zones repliables pour ne pas écraser le résumé humain.

## Limites assumées

La V0 ne gère pas :

- glisser-déposer ;
- édition de blocs ;
- sauvegarde de scénario ;
- serveur local ;
- dépendance externe ;
- appel HTTP ;
- automatisation Chronotime ;
- validation complète de la parentalité ;
- optimisation automatique.

Elle ne prétend pas que les jours fériés, la parentalité, les chevauchements d’agenda, les expirations fines ou l’optimisation sont entièrement gérés.

## Confidentialité

Les vrais fichiers utilisateur doivent rester dans `donnees_locales/`.

Les exemples committés sous `donnees/exemples/` doivent rester artificiels et ne doivent contenir aucune donnée personnelle ni aucun export Chronotime réel.
