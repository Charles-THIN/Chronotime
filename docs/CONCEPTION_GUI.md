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
