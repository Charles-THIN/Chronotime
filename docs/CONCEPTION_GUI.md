# Conception GUI

## Portée

Ce document est la référence active de conception GUI du projet Chronotime.

Il distingue :

- la cible d’architecture GUI ;
- les règles stables à respecter ;
- l’historique du prototype HTML local `V0.x`.

Les sections `V0.1` à `V0.5.1` décrivent les étapes du prototype local. Elles restent utiles pour comprendre l’ergonomie explorée, mais elles ne définissent pas à elles seules l’architecture cible.

## Règle d’architecture

La GUI doit respecter le flux suivant :

```text
modèle événementiel source
-> projection demi-journalière dérivée
-> vues de lecture
```

La projection demi-journalière ne doit pas devenir une source de vérité éditable.

Les futures actions utilisateur devront modifier les événements sources ou les blocs de scénario, puis recalculer la projection.

## Architecture cible : état central, commandes et vues dérivées

La cible GUI repose sur un état central piloté par un moteur identifiable, séparé du rendu visuel.

Le contrat minimal d’échange entre interface et moteur est défini dans [docs/CONTRAT_MOTEUR_GUI.md](./CONTRAT_MOTEUR_GUI.md). Cette section en donne seulement le cadrage conceptuel.

Flux d’une interaction :

```text
geste utilisateur
-> commande d’intention
-> moteur / modèle central
-> résultat accepté ou refusé
-> état recalculé ou inchangé
-> diagnostics structurés
-> rendu dérivé des vues
```

Le moteur contient ou orchestre :

- les sources événementielles ;
- le scénario local ;
- les règles de validation ;
- la projection recalculée ;
- les diagnostics ;
- l’état central de planification.

Les commandes utilisateur sont des intentions nommées, par exemple :

- `ajouter_absence` ;
- `supprimer_absence` ;
- `deplacer_absence` ;
- `redimensionner_absence` ;
- `scinder_absence` ;
- `fusionner_absences` ;
- `changer_type_absence` ;
- `prevalider_action`.

Chaque commande doit produire un résultat explicite :

- acceptée, avec état central recalculé ;
- refusée, avec état inchangé ;
- acceptée partiellement seulement si ce cas est modélisé explicitement.

Les diagnostics structurés expliquent le résultat. Ils peuvent cibler :

- un bloc ;
- une date ;
- un compteur ;
- une action refusée ;
- une alerte globale.

Les vues `calendrier`, `frise`, `compteurs`, `alertes`, `sélection` et `curseur` sont des rendus dérivés de cet état central et de ces diagnostics. Elles ne doivent pas embarquer chacune leur propre logique métier de validation ou d’allocation.

L’interface garde seulement un état transitoire de manipulation :

- survol ;
- sélection ;
- fantôme de glisser-déposer ;
- mode d’outil actif.

Cet état transitoire peut aider à prévisualiser un geste, mais il ne devient pas une source métier durable.

Le moteur est actuellement implémenté en Python pour le flux local par fichiers. La cible d’architecture n’impose pas que le moteur GUI dynamique reste en Python. Ce qui est obligatoire : un moteur identifiable, testé et séparé du rendu visuel.

Formulation à conserver :

```text
interdit :
  écrire directement un congé manuel dans projection.demi_journees déjà calculée

cible :
  ajouter ou modifier un bloc source
  appeler le moteur
  recalculer la projection ou refuser la commande
  réafficher les vues depuis l’état central et les diagnostics
```

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

Ce générateur reste un outil local utile de vérification et de prototype. Il ne doit pas être lu comme l’architecture dynamique cible.

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

## V0.4.2 Sélection passive

La version `V0.4.2` ajoute une première interaction locale de consultation dans la vue `Planification`.

Éléments sélectionnables :

- clic sur un jour du calendrier ;
- clic sur un bloc projeté dans la frise ;
- clic sur un point de la courbe du reste agrégé provisoire.

La sélection met uniquement à jour la zone `Sélection` de la barre d'informations droite.

Informations affichées selon le type de sélection :

- date, consommation et alertes pour un jour calendrier ;
- période, identifiant et quantité pour un bloc projeté ;
- date, portion et niveau pour un point de reste agrégé provisoire.

Cette sélection est un état visuel local de lecture. Elle ne modifie pas :

- les sources événementielles ;
- `projection.demi_journees` ;
- les mouvements ou chronologies dérivés ;
- le scénario ;
- Chronotime.

Elle ne déclenche aucun recalcul côté navigateur et ne crée aucune capacité d'édition. Elle sert seulement de première étape avant les futures interactions de création ou modification de blocs sources.

## V0.4.3 Corrections de sélection passive

La sélection passive est corrigée pour mieux préparer la future interaction détaillée.

Corrections apportées :

- un jour du calendrier peut proposer plusieurs niveaux de sélection ;
- les clics successifs sur un même jour font tourner les niveaux disponibles ;
- niveaux visés : bloc complet, sous-bloc monotype lorsqu'il existe, puis jour seul ;
- clic dans une zone centrale vide ou touche `Escape` : désélection ;
- la zone `Sélection` de la barre droite devient une fiche structurée, avec champs courts et valeurs longues renvoyées à la ligne ;
- le bloc `Tous les compteurs` est retiré de la barre droite principale ;
- les mois du calendrier sont compactés pour tenir sur une ligne autant que possible ;
- la frise ajoute des liaisons visuelles entre blocs projetés et courbe de reste agrégé provisoire.

Cette sélection reste passive. Elle ne crée pas de bloc, ne déplace rien, ne modifie aucune projection et ne sauvegarde aucun scénario.

Note sur les crédits futurs :

La frise ne montre pas encore de remontée liée aux crédits futurs, par exemple `JRTT`, car ces crédits ne sont pas encore modélisés dans la projection ou la chronologie de soldes. La GUI devra les afficher lorsque le moteur produira des événements de crédit ou une chronologie enrichie. Elle ne doit pas inventer ces remontées côté interface.

## V0.4.4 Stabilisation de la sélection et du curseur de frise

La version `V0.4.4` stabilise l’ergonomie de la vue `Planification` sans ajouter d’édition.

Corrections apportées :

- le mode `Général` limite le cycle de sélection à `bloc complet` puis `jour` ;
- le mode `Détaillé` permet le cycle `bloc complet`, `sous-bloc monotype` puis `jour` ;
- la sélection visuelle s’étend au bloc ou au sous-bloc sélectionné, et pas seulement au jour cliqué ;
- la sélection de texte involontaire dans la zone de planification est réduite ;
- la vue `Planification` est traitée comme une coquille d’application : barres latérales stables et zone centrale défilante ;
- la zone d’informations détaillées dispose d’un défilement interne si son contenu devient long ;
- une zone `Curseur` est séparée de la zone `Sélection` dans la barre droite ;
- la frise affiche un curseur vertical de lecture au survol, avec date, portion et reste agrégé provisoire ;
- les jours de l’axe horizontal de la frise sont placés au-dessus des libellés de mois.

Ces corrections restent passives. Elles ne créent aucun bloc, ne modifient aucun scénario, ne recalculent aucune projection côté navigateur et ne sauvegardent rien.

## V0.4.5 Cloisonnement de la barre d’informations

La version `V0.4.5` corrige le cloisonnement de la barre d’informations droite.

La barre droite est structurée en lignes explicites :

- synthèse fixe ;
- zone `Sélection` / ZID, avec défilement interne ;
- séparateur ;
- zone `Curseur`, bornée et séparée.

Objectif : empêcher le curseur de frise de se dessiner par-dessus la ZID et limiter les recompositions visuelles lorsque le curseur ou la sélection changent.

Cette correction reste passive. Elle ne crée aucun bloc, ne modifie aucun scénario, ne recalcule aucune projection côté navigateur et ne sauvegarde rien.

## V0.4.6 Densification visuelle de la planification

La version `V0.4.6` réduit l’encombrement visuel de la vue `Planification`.

Corrections apportées :

- en-tête général réduit ;
- description longue de l’en-tête contrainte sur une ligne ;
- espacements, cartes, boutons et titres légèrement réduits ;
- hauteur utile de la coquille de planification augmentée ;
- barre droite compactée ;
- `Total restant` et `Cette année` affichés côte à côte ;
- compteurs principaux affichés sous forme de grille compacte ;
- zone `Curseur` conservée mais moins haute.

Cette correction reste passive. Elle ne crée aucun bloc, ne modifie aucun scénario, ne recalcule aucune projection côté navigateur et ne sauvegarde rien.

## V0.4.7 Prototype local de pose de jours

La version `V0.4.7` ajoute un prototype local de l'outil `Poser des jours`.

Capacités de prototype :

- activation de l'outil `Poser des jours` depuis la barre gauche ;
- prévisualisation locale d'un bloc fantôme dans le calendrier ;
- clic simple pour poser un bloc local d'un jour ;
- cliquer-déplacer pour poser un bloc local sur une plage de dates projetées ;
- affichage des blocs locaux dans le calendrier et dans la frise ;
- sélection d'un bloc local en mode `Sélection` ;
- suppression du bloc local sélectionné avec `Suppr` ;
- persistance provisoire via `localStorage`.

Cette persistance utilise une clé de prototype d'interface. Elle ne devient pas une source métier canonique.

Limites explicites :

- aucun recalcul moteur ;
- aucun recalcul réel de compteur ;
- compteur seulement indicatif ;
- aucune modification de `projection.demi_journees` ;
- aucune sauvegarde de scénario ;
- aucune écriture Chronotime.

La cible future reste un scénario local explicite, versionnable et recalculé par un moteur séparé du rendu. Le stockage `localStorage` devra donc être remplacé par une source événementielle locale propre avant toute utilisation métier durable.

## V0.4.8 Absences utilisateur dans le modèle commun de sélection

La version `V0.4.8` corrige le prototype local pour que les absences ajoutées par l'utilisateur soient traitées comme de futurs blocs de scénario source, et non comme de simples marqueurs visuels.

Chaque absence locale conservée dans `localStorage` porte notamment :

- `type = absence_locale_prototype` ;
- `origine = ajoute_par_utilisateur` ;
- `statut = scenario_local_prototype` ;
- un compteur seulement indicatif, non recalculé par le moteur.

Ces blocs sont intégrés au cycle commun de sélection du calendrier :

- clic sur un jour contenant un bloc utilisateur : sélection du bloc utilisateur ;
- clics successifs : retour possible au jour ou aux autres niveaux disponibles ;
- suppression avec `Suppr` uniquement si le bloc utilisateur est sélectionné ;
- aucun bloc projeté, Chronotime ou obligation locale n'est supprimable depuis ce prototype.

Le mode `Poser des jours` reste volontairement prudent :

- il prévisualise une plage libre ;
- il refuse de poser sur une journée déjà occupée par un bloc projeté ou par un bloc utilisateur ;
- il ne recalcule aucun solde réel ;
- il ne modifie pas `projection.demi_journees`.

Cette version prépare le futur remplacement par un scénario local explicite puis un recalcul par le moteur. Elle ne constitue pas encore une sauvegarde métier durable.

## V0.4.9 Stabilisation visuelle de la pose utilisateur

La version `V0.4.9` stabilise le prototype de pose locale sans changer les règles métier.

Grammaire visuelle retenue :

- la couleur de fond indique l'origine du bloc ;
- le contour indique l'état interactif, par exemple survol ou sélection ;
- le type de compteur reste un détail futur du mode détaillé ;
- le fantôme de pose n'apparaît que sur une plage entièrement libre ;
- une plage occupée est signalée dans la zone d'information, sans overlay visuel sur les jours déjà occupés.

Les jours ajoutés par l'utilisateur utilisent un style plat, sans point décoratif ni dégradé. La sélection d'un bloc utilisateur conserve sa couleur d'origine et ajoute seulement un contour renforcé ; elle ne devient pas une alerte.

Le cliquer-déplacer multi-jours est corrigé : la finalisation utilise la dernière date réellement survolée ou la position du pointeur, et non seulement le jour de départ capturé par l'événement.

La frise conserve un rendu dynamique des blocs utilisateur avec un style plat. Dette restante : le calendrier et la frise ne sont pas encore alimentés par un modèle de planification commun complet. La cible suivante reste un scénario local explicite, puis un recalcul par le moteur qui produira à nouveau les sorties dérivées.

## V0.5.0 Grammaire visuelle du calendrier

La version `V0.5.0` clarifie la lecture du calendrier de planification sans modifier le moteur.

Grammaire retenue :

- type de compteur : couleur dédiée en mode détaillé ;
- origine issue de la projection : couleur normale et contour continu ;
- origine manuelle de prototype : rendu plus clair ou plus transparent et contour pointillé ;
- survol et sélection : contour ou ombre renforcée, sans utiliser la couleur d'alerte ;
- information secondaire : texte discret dans la case.

Couleurs préparées :

- `GCP` : rouge doux distinct de la couleur d'alerte ;
- `JRTT` : bleu ;
- `CANC` : vert ;
- autre ou inconnu : couleur par défaut.

Les jours affichent aussi le libellé court du jour de semaine sous la case (`lun`, `mar`, `mer`, `jeu`, `ven`, `sam`, `dim`). Le dimanche est typographiquement renforcé.

Les absences ajoutées par l'utilisateur restent des prototypes locaux persistés via `localStorage`. Elles ne recalculent aucun compteur réel, ne modifient pas `projection.demi_journees` et devront être remplacées plus tard par un scénario local explicite puis un recalcul par le moteur.

La frise reste une dette connue : elle ne bloque pas cette clarification et devra être réalimentée plus tard par un modèle de planification commun au calendrier et à la frise.

## V0.5.1 Tranche verticale moteur GUI prototype

La version `V0.5.1` introduit une première tranche concrète de l'architecture cible `état central / commandes / diagnostics / vues dérivées`.

Dans le prototype HTML local, la pose et la suppression de blocs utilisateur ne modifient plus directement le tableau local d'affichage. Elles passent par un moteur GUI prototype centralisé qui traite des commandes :

- `ajouter_absence` en prévisualisation ;
- `ajouter_absence` en application ;
- `supprimer_absence` en application.

Ce moteur produit un résultat structuré :

- statut de commande ;
- état central partiel ;
- diagnostics ;
- sélection suggérée.

Le rendu des blocs utilisateur devient dérivé de `etatCentralGui.blocs_affichables`.

Les fantômes de manipulation restent dans `etatTransitoireInterface`. Ils ne sont pas persistés, ne deviennent pas des blocs réels et disparaissent si la commande n'est pas acceptée.

Les sous-vues `Calendrier` et `Frise` restent aujourd'hui exclusives. Elles doivent consommer le même état transitoire lorsqu'elles sont actives, chacune avec sa grammaire propre. Le calendrier reste prioritaire pour cette tranche ; la frise reçoit seulement une préparation de rendu du même fantôme transitoire.

Limites maintenues :

- aucun recalcul réel des soldes ;
- aucune allocation métier de compteur ;
- aucun recalcul de `projection.demi_journees` ;
- les blocs projetés issus de la projection ne sont pas encore convertis intégralement en `blocs_affichables` ;
- `localStorage` reste une persistance prototype, pas une source métier durable.

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
