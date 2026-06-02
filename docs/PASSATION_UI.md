# Passation avant interface graphique Chronotime

## Portée

Ce document sert de point d’entrée pour la prochaine phase du projet Chronotime : l’interface graphique.

Il doit être lu avant toute tâche d’interface.

Il résume l’état actuel du dépôt, les décisions d’architecture, les règles métier connues, les limites restantes et la première direction de développement pour la GUI.

Ce document ne remplace pas les fichiers de documentation détaillés du dépôt. Il sert de synthèse opérationnelle.

## Objectif général du projet

Construire un outil local permettant de mieux visualiser et simuler les absences Valeo / Chronotime.

Le cas d’usage principal est :

- importer localement les soldes et l’agenda Chronotime ;
- saisir ou charger des obligations locales ;
- ajouter, enlever, déplacer ou désactiver des blocs d’absence simulés ;
- voir l’impact sur les compteurs futurs ;
- répondre facilement à des questions comme : “que restera-t-il à Noël si je pose tel bloc en été ?” ;
- éviter de subir l’interface Chronotime actuelle, jugée trop peu lisible pour la planification.

Le projet ne doit pas modifier Chronotime.

Le projet ne doit pas faire de `POST`, `PUT`, `DELETE` ou validation réelle dans Chronotime.

Les données personnelles réelles doivent rester dans `donnees_locales/`, dossier ignoré par Git.

## État actuel du dépôt

Le socle local existe déjà.

Briques principales déjà codées :

- parseur local des soldes Chronotime `soldeabs` ;
- parseur local de l’agenda Chronotime ;
- chargeur local de scénarios ;
- chargeur local d’obligations ;
- vérificateur obligations locales ↔ agenda ;
- projecteur demi-journalier ;
- orchestrateur local de projection ;
- générateur de mouvements de solde.

Le flux local complet est :

```text
soldes Chronotime locaux
+ agenda Chronotime local
+ obligations locales
+ scénario local
+ événements de compteur optionnels
-> normalisation
-> vérification des obligations
-> projection demi-journalière
-> mouvements.soldes optionnels
-> chronologie.soldes optionnelle
```

Commande locale réaliste actuellement utilisée :

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
  --date-cible fin_noel="Fin fermeture Noël"=2026-12-31 `
  --sortie donnees_locales/projection_obligations_seules_v2.json
```

Résultat observé avec scénario vide :

```text
nombre_demi_journees      = 452
nombre_evenements_sources = 6
nombre_alertes            = 3
```

Soldes initiaux observés dans cette projection :

```text
GCP  = 23.96
JRTT = 1.9
CANC = 5.0
```

Alertes observées :

```text
2 × evenement_hors_periode_projection
1 × solde_negatif_confirmation_possible
```

Interprétation :

- les deux alertes hors période correspondent aux obligations déjà situées avant la date de départ de projection ;
- l’alerte de confirmation correspond au passage de `JRTT` à `-0.1`, compatible avec l’observation Chronotime selon laquelle un JRTT négatif peut être confirmable ;
- il n’y a plus de fausse alerte GCP, car `GCP` est lu dans la période `suivant`.

## Décision d’architecture essentielle

Le modèle éditable est événementiel.

La projection demi-journalière n’est pas la source de vérité.

La GUI doit donc respecter cette règle :

```text
action utilisateur
-> modification d’un événement source ou d’un bloc source
-> recalcul de la projection
-> rafraîchissement des vues
```

La GUI ne doit pas éditer directement `projection.demi_journees` comme si c’était le modèle source.

Exemples :

- déplacer un bloc dans la frise modifie `date_debut` et `date_fin` du bloc source ;
- redimensionner un bloc modifie la période du bloc source ;
- désactiver un bloc modifie son statut ou son champ `actif` ;
- supprimer un bloc doit probablement le désactiver ou le supprimer dans le scénario, pas supprimer des demi-journées projetées ;
- cliquer sur une case vide peut créer un nouveau bloc source ;
- après chaque modification, l’orchestrateur ou le projecteur doit produire une nouvelle projection.

## Vues cibles prévues

La cible GUI doit d’abord être pensée autour du reste global agrégé, pas autour d’une lecture primaire par compteurs.

Le détail par compteur reste utile, mais comme vue secondaire, panneau explicatif ou niveau de lecture avancé.

Le moteur devra encore préciser la formule exacte entre :

- reste agrégé total ;
- reste libre après réserves ;
- congés à conserver pour l’année suivante.

Quatre vues ou familles de vues sont prévues.

### Vue 1 : calendrier classique

Cette vue doit rester familière.

Elle doit permettre à terme :

- repérer les dates civiles ;
- distinguer jours travaillés et non travaillés ;
- créer ou sélectionner des blocs ;
- lire l’effet d’une action sur le reste agrégé dans la barre d’informations droite.

### Vue 2 : frise avec niveau de reste agrégé

C’est la vue principale d’édition.

Elle doit permettre à terme :

- afficher une période longue ;
- afficher une frise des blocs ;
- afficher une courbe ou un niveau du reste agrégé sur le même axe temporel ;
- visualiser immédiatement l’impact d’un bloc sur le reste ;
- montrer les contraintes lorsqu’un bloc ne peut plus être tiré ;
- voir les absences réelles ;
- voir les obligations non encore posées ;
- voir les blocs simulés ;
- déplacer un bloc ;
- redimensionner un bloc ;
- verrouiller un bloc ;
- désactiver un bloc ;
- ouvrir un éditeur de détail ;
- zoomer entre année, trimestre, mois, semaine.

La frise et le niveau peuvent être superposés ou placés verticalement l’un au-dessus de l’autre.

### Vue 3 : projection des soldes

Elle doit montrer l’évolution des compteurs.

Elle doit permettre :

- lire les soldes initiaux ;
- lire les soldes à des dates cibles ;
- voir les consommations par compteur ;
- voir les alertes ;
- distinguer quantité demandée, quantité réellement appliquée et quantité non couverte ;
- répondre aux questions de planification.

Elle ne doit pas inventer les crédits futurs, ouvertures de validité, expirations ou reports. Ces informations devront venir de `projection.demi_journees` si elle est enrichie, ou d’un modèle explicite d’événements de compteur.

Pour une première vue `Soldes dans le temps`, lire d’abord les données déjà dérivées par le moteur, notamment `mouvements.soldes` et `chronologie.soldes`. La GUI ne doit pas recalculer elle-même les mouvements de solde ni inventer des crédits, expirations, reports ou acquisitions.

### Vue 4 : calendrier annuel compact

Elle doit permettre :

- vérifier les dates civiles ;
- voir week-ends et jours non décomptés ;
- voir les demi-journées ;
- repérer les blocs mal placés ;
- repérer les périodes de fermeture ou de congé imposé.

## Barres communes

Les vues centrales doivent partager :

- une barre d’outils à gauche ;
- une barre d’informations à droite.

### Barre d’outils gauche

Contenu fixé actuellement :

- outil `poser des jours` ;
- outil `scinder des jours déjà posés` ;
- outil `joindre / fusionner` ;
- groupe de boutons de mode `général` et `détaillé` ;
- emplacements réservés pour outils futurs.

Mode général :

- lecture centrée sur jours travaillés, congés et blocs ;
- pas de distinction fine de compteur au premier regard.

Mode détaillé :

- affichage de la nature exacte des blocs ;
- compteur, droit parentalité, obligation, absence réelle, simulation, alerte et autres détails utiles.

### Barre d’informations droite

Contenu fixé actuellement :

- total restant ;
- dont prévus pour cette année ;
- détail compteurs ;
- prochaine expiration ;
- zone d’information sur la sélection ;
- autres champs futurs possibles.

La zone de sélection reste vide si rien n’est sélectionné.

Cette barre doit aussi permettre à la vue calendrier de montrer l’effet d’une action sur le reste agrégé, même si la courbe n’est pas visible au centre.

## Interactions communes

Interactions centrales visées :

clic sur un élément :

- sélection ;
- affichage des détails dans la barre droite.

clic-déplacement :

- déplacement du bloc dans les limites des contraintes.

déplacement du début ou de la fin :

- redimensionnement du bloc.

survol :

- infobulle légère.

action non autorisée :

- signalement, blocage ou prévisualisation comme impossible.

Ces interactions modifient les blocs sources, puis déclenchent un recalcul de la projection.

## Première GUI recommandée

Ne pas commencer par une interface complète avec glisser-déposer.

Commencer par une interface locale statique ou semi-statique qui lit une projection JSON existante.

Première version utile :

```text
entrée :
  donnees_locales/projection_obligations_seules_v2.json

sortie :
  page HTML locale ou application locale minimale
```

Fonctions minimales recommandées :

- charger un fichier `projection.demi_journees` ;
- afficher un résumé global ;
- afficher les soldes initiaux ;
- afficher les soldes aux dates cibles ;
- afficher les alertes par type et sévérité ;
- afficher une frise 1D simple ;
- colorer les demi-journées consommées ;
- afficher les détails au survol ou au clic ;
- afficher les `consommations_detaillees`.

Ne pas encore implémenter :

- glisser-déposer ;
- sauvegarde de scénario depuis l’interface ;
- édition complexe ;
- optimisation automatique ;
- récupération automatique Chronotime ;
- gestion complète de la parentalité.

## Format de projection important pour l’interface

Chaque demi-journée contient notamment :

```json
{
  "date": "2026-08-10",
  "portion": "matin",
  "index_demi_journee": 0,
  "evenements": [],
  "consommations": {},
  "consommations_detaillees": [],
  "soldes_avant": {},
  "soldes_apres": {},
  "alertes": []
}
```

`consommations` est seulement un résumé agrégé par compteur.

Pour la GUI, préférer `consommations_detaillees`.

Exemple :

```json
{
  "identifiant_evenement": "fermeture_ete",
  "source": "obligation",
  "compteur": "GCP",
  "quantite_demandee": 0.5,
  "quantite_appliquee": 0.5,
  "quantite_non_couverte": 0.0,
  "priorite": 100
}
```

L’interface doit bien distinguer :

- quantité demandée ;
- quantité appliquée ;
- quantité non couverte.

C’est indispensable pour afficher correctement les cas où un solde minimum est atteint.

## Alertes importantes pour la GUI

Chaque alerte possède une `severite`.

Valeurs actuelles :

```text
information
confirmation
bloquant
```

Types d’alertes importants :

```text
evenement_hors_periode_projection
solde_negatif_confirmation_possible
solde_minimum_depasse
periode_compteur_absente
quantite_evenement_non_projectee
unite_non_projectee
date_cible_hors_periode
```

L’interface doit traiter :

- `information` comme un signal non bloquant ;
- `confirmation` comme une situation potentiellement acceptable mais nécessitant attention ;
- `bloquant` comme une situation non validable en l’état.

## Règles métier actuellement connues

Profil de travail utilisé :

- cadre en CDI ;
- convention collective nationale de la métallurgie ;
- forfait jours 215 ;
- périmètre Valeo Comfort & Driving Assist, site de Créteil.

Compteurs Chronotime observés :

```text
GCP  : congés payés
JRTT : RTT jours
CANC : congés d’ancienneté
RECU : récup jours cadre forfait
REHV : récupération horaire variable
RCRH : récupération RCR heures
COMP : repos compensateur légal
CDIR : congé cadre dirigeant
CSRE : congé supplémentaire retraite
ASTJ : récupération astreinte en jours
EDEP : récupération déplacement
```

Hypothèses opérationnelles actuelles :

```text
GCP  -> période suivant
JRTT -> période courant
CANC -> période courant
```

Soldes minimums provisoires :

```text
GCP  -> 0.0
JRTT -> -10.0 environ
CANC -> 0.0
```

Ces valeurs sont des hypothèses opérationnelles fondées sur tests Chronotime. Elles ne sont pas juridiquement définitives.

Observations empiriques :

- une demande future GCP semble possible malgré `GCP courant = 0j00` ;
- `JRTT` peut devenir négatif avec confirmation ;
- la limite JRTT semble proche de `-10j00` ;
- `CANC` semble bloquant si le solde devient négatif ;
- un chevauchement avec `TELV` a été observé comme bloquant ;
- les jours fériés ne sont pas encore intégrés automatiquement.

## Obligations locales 2026

Obligations connues pour Créteil :

```text
vendredi 2 janvier 2026 :
  RTT à positionner

vendredi 15 mai 2026 :
  RTT à positionner

lundi 25 mai 2026 :
  RTT à positionner, journée de solidarité / Pentecôte

lundi 13 juillet 2026 :
  RTT à positionner

lundi 10 août -> vendredi 14 août 2026 :
  5 jours à prendre obligatoirement en congé payé

vendredi 25 décembre -> jeudi 31 décembre 2026 :
  4 jours minimum à prendre en GCP, JRTT ou CANC
```

Ces obligations ne créent pas de droits.

Elles consomment les compteurs existants.

Noël 2026 est un cas important : le 25 décembre doit être fourni comme jour non décompté pour que la consommation se fasse correctement du 28 au 31 décembre.

## Jours fériés et jours non décomptés

État actuel :

```text
Fait :
  exclusion manuelle via --jours-non-decomptes

Pas fait :
  calendrier automatique des jours fériés
  calendrier site Valeo
  calcul automatique des ponts
```

Le projecteur actuel sait exclure les dates fournies dans `jours_non_decomptes` pour :

```text
jours_ouvres
jours_ouvrables
```

Il ne les exclut pas automatiquement pour :

```text
jours_calendaires
```

Raison : certaines absences calendaires, comme la paternité, peuvent inclure week-ends et jours fériés.

Pour la GUI, il faudra afficher les jours non décomptés visuellement, mais ne pas prétendre qu’un calendrier férié complet existe déjà.

## Parentalité

La parentalité est documentée, mais non implémentée comme moteur de contraintes.

Éléments connus :

- congé de naissance : 3 jours ouvrables ;
- congé de paternité obligatoire : 4 jours calendaires immédiatement après le congé de naissance ;
- congé de paternité facultatif : 21 jours calendaires pour une naissance simple ;
- 3 demi-journées d’absence autorisée payée pour accompagner l’épouse aux échographies, information locale à vérifier précisément ;
- congé supplémentaire de naissance 2026 annoncé : jusqu’à 2 mois, premier mois à 70 %, deuxième mois à 60 %, à vérifier selon textes, CPAM, Valeo et convention.

Blocs futurs à prévoir :

```text
absence_autorisee_echographie
conge_naissance
conge_paternite_obligatoire
conge_paternite_facultatif
conge_supplementaire_naissance
conge_parental
```

La première GUI ne doit pas prétendre valider toutes les contraintes de parentalité.

Elle peut éventuellement afficher ou saisir des blocs parentaux simples, mais avec un statut clair :

```text
règles_parentalité_non_validées
```

Il faudra une tâche distincte pour un vrai validateur parentalité.

## Ce qui n’est pas encore fait

Avant une interface complète, les briques suivantes manquent encore :

- calendrier automatique des jours fériés ;
- validateur de chevauchement avec agenda existant ;
- validateur des blocs parentaux ;
- acquisition future automatique ;
- expiration fine des compteurs ;
- optimisation automatique ;
- récupération automatique des JSON Chronotime ;
- écriture ou soumission dans Chronotime ;
- sauvegarde éditable de scénario depuis l’interface.

## Note sur les événements de compteur

La GUI V0.3.1 affiche correctement une projection existante en lecture seule.

Elle ne doit pas gérer elle-même :

- crédits futurs ;
- ouvertures de validité ;
- expirations ;
- reports ;
- acquisitions.

`mouvements.soldes` prépare la future vue `Soldes dans le temps`.

`chronologie.soldes` existe désormais et cumule les mouvements par code de compteur.

La future vue devra lire ces informations depuis `projection.demi_journees`, `mouvements.soldes`, `chronologie.soldes` ou une projection enrichie produite par le moteur.

La GUI peut afficher `mouvements.soldes` ou `chronologie.soldes` plus tard, mais ne doit pas les traiter comme des sources éditables.

La future GUI ne doit jamais traiter `projection.demi_journees` comme une source éditable.

La cible GUI n’inclut pas à ce stade :

- communication directe avec Chronotime ;
- écriture automatique ;
- optimisation automatique ;
- allocation complète des compteurs ;
- calcul moteur définitif du reste agrégé.

Le modèle attendu est documenté dans [docs/MODÈLE_ÉVÉNEMENTS_COMPTEURS.md](./MODÈLE_ÉVÉNEMENTS_COMPTEURS.md).

## Contraintes de confidentialité

Ne jamais committer :

```text
donnees_locales/
RAPPORT_CODEX_LOCAL.md
fichiers HAR
cookies
tokens
matricules
exports Chronotime bruts réels
soldes personnels réels
dates personnelles sensibles
```

Les fichiers réels utilisateur restent dans :

```text
donnees_locales/
```

Les fichiers sous :

```text
donnees/exemples/
```

doivent rester artificiels, anonymisés ou sans donnée personnelle.

## Règles de travail avec Codex

ChatGPT prépare les tâches.

Codex exécute localement.

Les tâches Codex doivent être :

- petites ;
- concrètes ;
- testables ;
- en français ;
- avec fichiers exacts ;
- avec commandes de validation exactes ;
- avec rapport local dans `RAPPORT_CODEX_LOCAL.md`.

Codex doit signaler toute déviation.

Ne pas laisser Codex redessiner l’architecture générale sans instruction explicite.

## Première tâche GUI recommandée

Créer une première visualisation locale en lecture seule.

Objectif :

- lire un fichier `projection.demi_journees` ;
- générer une page HTML locale ;
- afficher une frise 1D simple ;
- afficher les soldes initiaux ;
- afficher les soldes aux dates cibles ;
- afficher les alertes ;
- afficher les détails d’une demi-journée sélectionnée.

Fichiers probables :

```text
docs/CONCEPTION_GUI.md
outils/chronotime/generateur_vue_projection.py
tests/test_generateur_vue_projection.py
```

Contraintes :

- pas encore de serveur ;
- pas encore de dépendance externe ;
- pas encore de glisser-déposer ;
- pas encore d’édition ;
- pas encore de parentalité avancée ;
- pas encore d’appel HTTP ;
- pas encore d’automatisation navigateur.

Entrée :

```text
donnees_locales/projection_obligations_seules_v2.json
```

Sortie :

```text
donnees_locales/vue_projection.html
```

But de cette première étape :

- vérifier que la projection est lisible visuellement ;
- vérifier que les couleurs et les alertes “parlent” ;
- préparer ensuite une interface éditable.
