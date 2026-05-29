# Modèle des événements de compteur

## Portée

Ce document définit un modèle source pour les événements qui modifient ou qualifient les compteurs de congés.

Il prépare la future vue `Soldes dans le temps`, sans ajouter de règle métier automatique.

Les événements de compteur font partie du modèle événementiel source. Ils ne sont pas inventés par la GUI.

## Principe

Le projet distingue :

- les stocks observés dans Chronotime ;
- les événements sources qui expliquent ou modifient ces stocks ;
- les projections dérivées utilisées pour l’affichage.

La GUI doit lire les événements de compteur fournis par le moteur ou par une projection enrichie. Elle ne doit pas générer elle-même des crédits futurs, des ouvertures de validité, des expirations ou des reports.

## Types d’événements

Les types prévus sont :

- `credit_compteur` ;
- `ouverture_validite_compteur` ;
- `expiration_compteur` ;
- `report_compteur` ;
- `ajustement_compteur` ;
- `consommation_absence`.

Ces types décrivent des faits ou hypothèses explicites. Ils ne valident pas une règle RH ou Chronotime tant que celle-ci n’est pas vérifiée.

## `credit_compteur`

Un `credit_compteur` augmente un compteur à une date donnée.

Il peut représenter :

- une acquisition ;
- une dotation annuelle ;
- une régularisation ;
- un crédit manuel.

Champs proposés :

- `identifiant` ;
- `type` ;
- `date_effet` ;
- `compteur` ;
- `quantite` ;
- `unite` ;
- `source` ;
- `statut_certitude` ;
- `notes`.

Exemple conceptuel :

```json
{
  "identifiant": "credit_gcp_exemple_2026",
  "type": "credit_compteur",
  "date_effet": "2026-06-01",
  "compteur": "GCP",
  "quantite": 2.0,
  "unite": "jour",
  "source": "hypothese_locale",
  "statut_certitude": "a_verifier",
  "notes": "Exemple artificiel, non issu d'un vrai solde."
}
```

## `ouverture_validite_compteur`

Une `ouverture_validite_compteur` indique qu’un stock existe ou est connu, mais devient utilisable à partir d’une date.

Ce type est utile pour modéliser prudemment un compteur comme `GCP suivant`, sans affirmer encore la règle exacte d’ouverture.

Il ne doit pas être confondu avec un crédit : le stock peut déjà être visible dans Chronotime, mais pas nécessairement disponible selon les règles opérationnelles.

## `expiration_compteur`

Une `expiration_compteur` indique qu’une quantité cesse d’être utilisable à une date donnée.

Dans une future courbe des soldes, elle peut produire une chute de solde.

Ce type doit rester explicite, car les dates d’expiration ne sont pas encore déduites automatiquement du triplet `precedent`, `courant`, `suivant`.

## `report_compteur`

Un `report_compteur` représente le transfert d’une quantité non consommée d’une période vers une autre.

Exemple conceptuel :

```text
reliquat 2026 reporté vers 2027
```

Le projet ne doit pas supposer que `precedent`, `courant` et `suivant` correspondent automatiquement à un report. La conversion en `report_compteur` doit être explicite et vérifiable.

Deux formes sont acceptées :

- forme simple, avec `compteur`, `quantite` et `unite` ;
- forme détaillée, avec `compteur_source`, `periode_source`, `compteur_destination`, `periode_destination`, `quantite` et `unite`.

La forme simple reste informative. Elle sert à noter qu’un report existe ou est supposé, sans préciser encore la source et la destination exactes.

La forme détaillée est la seule forme destinée à devenir opérationnelle plus tard.

Le champ normalisé `mode_report` n’existe que pour `report_compteur` :

- `mode_report: "informatif"` pour la forme simple ;
- `mode_report: "operationnel"` pour la forme détaillée.

Un report informatif ne modifie pas les soldes et ne contribue pas au résumé des variations par compteur.

Un report opérationnel pourra être interprété plus tard comme un transfert source -> destination.

L’application réelle des reports aux soldes n’est pas encore implémentée. Les champs `periode_source` et `periode_destination` devront être précisés avant cette application effective, même si le chargeur n’en dépend pas encore strictement pour accepter un report détaillé.

## `ajustement_compteur`

Un `ajustement_compteur` représente une correction ponctuelle, manuelle ou administrative.

Il sert à rester compatible avec Chronotime si un compteur est corrigé sans règle connue ou si une régularisation apparaît dans les soldes.

## `consommation_absence`

Une `consommation_absence` représente une consommation issue :

- d’une absence réelle ;
- d’une obligation locale ;
- d’un bloc de scénario ;
- d’un événement assimilé projeté.

Ce type peut être dérivé des `consommations_detaillees` déjà produites par le projecteur demi-journalier.

Il doit conserver le lien vers l’événement source lorsque cet identifiant est disponible.

## Lien avec `precedent`, `courant` et `suivant`

Les périodes `precedent`, `courant` et `suivant` viennent de Chronotime.

Elles doivent être traitées comme des stocks observés.

Elles ne doivent pas être interprétées automatiquement comme :

- reports ;
- crédits ;
- ouvertures de validité ;
- expirations.

La conversion d’un stock observé en événement de compteur doit rester explicite, documentée et vérifiable compteur par compteur.

## Future vue `Soldes dans le temps`

La future vue `Soldes dans le temps` devra lire :

- les soldes initiaux ;
- les consommations détaillées ;
- les crédits ;
- les ouvertures de validité ;
- les expirations ;
- les reports ;
- les ajustements ;
- les alertes.

Elle devra produire une courbe en marches :

- montée lors d’un crédit ;
- descente lors d’une consommation ;
- chute lors d’une expiration ;
- transfert ou montée différée lors d’un report ;
- correction ponctuelle lors d’un ajustement.

Cette vue ne doit pas inventer les crédits futurs, les expirations ou les reports. Ces informations doivent venir du moteur ou d’une projection enrichie.

## Limites

Ce modèle ne confirme pas :

- l’existence d’une acquisition mensuelle de `JRTT` ;
- le mode d’ouverture de `GCP suivant` ;
- les dates de validité de `GCP`, `CANC` ou `JRTT` ;
- les règles d’expiration ;
- les règles de report.

Ces points restent à vérifier avant toute génération automatique.

## Chargeur local

Le chargeur local `outils/chronotime/chargeur_evenements_compteurs.py` lit un fichier JSON d’événements de compteur et produit une forme normalisée.

Source normalisée :

```json
{
  "source": "evenements_compteurs.normalises",
  "evenements": [],
  "resume": {
    "nombre_evenements": 0,
    "nombres_par_type": {},
    "quantites_par_compteur": {}
  }
}
```

Validations minimales :

- chaque événement doit avoir un `identifiant` non vide ;
- chaque événement doit avoir un `type` non vide et autorisé ;
- `date_effet` doit être normalisé strictement en date ISO `YYYY-MM-DD` ;
- `compteur` est obligatoire pour `credit_compteur`, `ouverture_validite_compteur`, `expiration_compteur`, `ajustement_compteur` et `consommation_absence` ;
- `report_compteur` exige soit `compteur`, soit `compteur_source` et `compteur_destination` ;
- `report_compteur` normalise `mode_report` à `informatif` ou `operationnel` selon la forme fournie ;
- `quantite` et `unite` sont obligatoires pour `credit_compteur`, `expiration_compteur`, `report_compteur`, `ajustement_compteur` et `consommation_absence` ;
- `ouverture_validite_compteur` peut rester sans quantité, car elle peut qualifier un stock sans créer de crédit ;
- les unités acceptées sont `jour`, `heure` et `demi_journee` ;
- les quantités sont normalisées en nombres flottants.

Le chargeur ne projette rien.

Il ne génère pas de crédits automatiques, d’expirations automatiques ou de reports automatiques.

Les événements de compteur ne sont pas encore intégrés au projecteur demi-journalier.
