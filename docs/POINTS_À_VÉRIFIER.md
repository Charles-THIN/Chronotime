# Points à vérifier

Ce document liste les points encore ouverts avant de figer un moteur de calcul plus strict.

## Congés et provisionnement

- Valeo autorise-t-il la pose de congés non encore totalement provisionnés ?
- Faut-il un mode `chronotime_previsionnel` par défaut ?
- Comment Chronotime traite-t-il `precedent`, `courant` et `suivant` pour chaque compteur ?
- Quelles sont les dates exactes d’ouverture, d’expiration et de bascule de chaque compteur ?
- Les jours fériés doivent-ils être intégrés au projecteur V1 ?
- Comment traiter les compteurs horaires dans la projection ?
- Comment traiter les cas mixtes matin / après-midi avec compteurs différents ?
- Quelle est la stratégie par défaut pour Noël sans compteur préféré ?

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
