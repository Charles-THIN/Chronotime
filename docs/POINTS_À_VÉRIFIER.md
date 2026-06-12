# Points à vérifier

Ce document liste les points encore ouverts avant de figer un moteur de calcul plus strict.

## Congés et provisionnement

- Valeo autorise-t-il la pose de congés non encore totalement provisionnés ?
- Faut-il un mode `chronotime_previsionnel` par défaut ?
- Comment Chronotime traite-t-il `precedent`, `courant` et `suivant` pour chaque compteur ?
- Confirmer que `GCP` futur consomme bien le compteur `suivant`.
- Quelles sont les dates exactes d’ouverture, d’expiration et de bascule de chaque compteur ?
- Confirmer que `JRTT` peut être négatif jusqu’à environ `-10j00`.
- Confirmer si `-10j00` est une limite fixe, annuelle ou dépendante du profil.
- Confirmer que `CANC` ne peut jamais devenir négatif.
- Les jours fériés doivent-ils être intégrés au projecteur V1 ?
- Confirmer la liste exacte des jours fériés / jours non décomptés à utiliser pour 2026.
- Confirmer si le 25 décembre 2026 doit bien être exclu de la fermeture Noël.
- Confirmer si le 15 août 2026, férié mais samedi, a un impact nul pour le site.
- Comment traiter les compteurs horaires dans la projection ?
- Comment traiter les cas mixtes matin / après-midi avec compteurs différents ?
- Quelle est la stratégie par défaut pour Noël sans compteur préféré ?
- Confirmer si les chevauchements d’absences sont toujours bloquants ou selon motif.

## Obligations locales

- Comment vérifier automatiquement qu’une obligation locale est déjà satisfaite par l’agenda normalisé ?
- Quel est le code Chronotime exact à utiliser pour les RTT à positionner ?
- Les obligations locales doivent-elles rester distinctes des absences déjà posées dans Chronotime ?

## Parentalité

- Confirmer les 3 demi-journées d’échographie et leur code Chronotime.
- Confirmer les codes Chronotime des 3 jours de naissance, des 4 jours obligatoires et des 21 jours facultatifs.
- Vérifier l’entrée en vigueur et l’indemnisation du congé supplémentaire de naissance 2026.
- Vérifier si Valeo ou la convention métallurgie prévoit un complément de salaire.
- Vérifier si ces absences impactent les JRTT ou le forfait jours.
- Vérifier si le congé supplémentaire de naissance 2026 doit être modélisé comme un bloc distinct du congé de paternité.

## Projection

- Les acquis futurs doivent-ils être modélisés comme événements datés ou comme compteurs périodiques ?
- Les expirations futures doivent-elles être projetées au jour près ou seulement par période ?
- Les alertes doivent-elles distinguer manque de solde, incompatibilité de compteur et unité non projetée ?
- Le projecteur V1 doit-il gérer les jours fériés publics ?
- Vérifier si `chronologie.soldes` doit devenir sensible aux périodes `precedent`, `courant` et `suivant` pour les reports et expirations fines.
- Définir la formule exacte du reste agrégé à afficher dans la future GUI.
- Distinguer précisément reste total, reste libre après réserves et réserve pour l’année suivante.
- Définir le comportement exact de scission et de fusion des blocs dans la future GUI.
- Définir la forme exacte de la courbe ou du niveau de reste agrégé dans la vue frise.

## Architecture GUI dynamique

- Choisir la technique du moteur dynamique : Python local, JavaScript/TypeScript ou autre.
- Stabiliser le contrat V0.1 des commandes moteur après premier prototype.
- Stabiliser le format V0.1 des diagnostics structurés après premier prototype.
- Définir la frontière entre état moteur et état transitoire d’interface.
- Remplacer `localStorage` prototype par une source de scénario locale ou un état moteur persistant.
- Définir la stratégie de prévalidation pendant le glisser-déposer.
- Définir comment calendrier, frise, compteurs et alertes consomment un même état central sans logique métier dupliquée.
- Confirmer la parité complète Python / JS sur un corpus croissant de scénarios artificiels avant de brancher la GUI sur le moteur JS ou de supprimer le moteur Python.
- Fait : les compteurs principaux et le total restant de la barre droite peuvent être mis à jour depuis la projection vivante recalculée en mémoire.
- Fait : l’autosauvegarde locale du scénario GUI est déclenchée après modification acceptée.
- Fait : nettoyage des messages de succès et du vocabulaire prototype dans la vue Calendrier.
- Fait : curseur compact toujours visible.
- Fait : indicateur `Posés {année}`.
- Fait : frise synchronisée en lecture avec la projection active.
- Reste : définir le total métier final, le reste libre et les réserves `N+1`.
- Reste : ajouter une sauvegarde explicite vers fichier.
- Reste : ajouter un chargement explicite depuis fichier.
- Reste : permettre un retour à l’état à l’ouverture.
- Reste : permettre l’annulation des changements depuis le lancement.
- Reste : pose de jours depuis la frise.
- Reste : déplacement / allongement / raccourcissement depuis la frise.
- Reste : Auto réel.
- Reste : congés parentaux.
- Reste : expirations fines par compteur.
- Reste : mise à jour régulière depuis Chronotime.
- Reste : liste d’actions Chronotime à réaliser.
- Reste : écriture automatique Chronotime, seulement en toute dernière étape éventuelle.
- Reste : journal technique consultable.
- Reste : intégrer les familles de compteurs liées à la parentalité lorsque les blocs parentalité seront modélisés.

## Événements de compteur

- Existe-t-il une preuve exacte d’une acquisition mensuelle de `JRTT` ?
- Quel est le mode réel d’ouverture de `GCP suivant` ?
- Quelles sont les dates de début de validité de `GCP`, `CANC` et `JRTT` ?
- Quelles sont les règles d’expiration exactes par compteur ?
- Quelles sont les règles de report exactes par compteur ?
- Confirmer la sémantique opérationnelle complète des reports avant de les appliquer aux soldes cumulés.
- Quelle est la signification exacte de `precedent`, `courant` et `suivant` selon chaque compteur ?
- Quels événements doivent être considérés comme `credit_compteur`, `ouverture_validite_compteur`, `expiration_compteur`, `report_compteur` ou `ajustement_compteur` ?
