# Projection demi-journalière

La projection demi-journalière est une sortie dérivée. Elle n’est pas la source de vérité éditable du projet.

Les sources éditables restent :

- les événements Chronotime normalisés ;
- les blocs de scénario ;
- les obligations locales ;
- les crédits futurs ;
- les expirations futures.

Le projecteur transforme ces sources en un vecteur de demi-journées destiné aux futures vues.

## Rôle

La projection sert à alimenter plus tard :

- la frise 1D ;
- le calendrier annuel compact ;
- la vue des soldes ;
- la lecture rapide des soldes à une date cible.

Chaque demi-journée contient les événements projetés, les consommations de compteurs, les consommations détaillées, les soldes avant et après, ainsi que les alertes éventuelles.

## Règles V0

La version initiale reste volontairement limitée :

- pas d’acquisition automatique future ;
- pas d’expiration fine des compteurs ;
- pas de calendrier automatique des jours fériés ;
- pas d’optimisation automatique ;
- pas de règle RH complexe ;
- pas de congé parental détaillé.

Les unités sont projetées ainsi :

- `jours_ouvres` : lundi à vendredi ;
- `jours_ouvrables` : lundi à samedi ;
- `jours_calendaires` : tous les jours ;
- `demi_journee` : première demi-journée de la date de début ;
- `heures` : non projeté en V0, avec une alerte.

Pour les événements en jours, la consommation de base est de `0.5` par demi-journée. Si une plage contient plus de demi-journées que la quantité déclarée, le projecteur s’arrête quand la quantité est atteinte.

Si une plage ne permet pas de projeter toute la quantité demandée, le projecteur ajoute une alerte `quantite_evenement_non_projectee`.

## Périodes Et Minimums Par Compteur

La période globale `periode_compteurs` est seulement un repli.

Le projecteur accepte `periodes_compteurs_par_code` pour lire certains compteurs dans une période différente. Exemple provisoire à vérifier :

```json
{
  "GCP": "suivant",
  "JRTT": "courant",
  "CANC": "courant"
}
```

Le projecteur accepte aussi `soldes_minimums_par_code`.

Ces minimums sont une approximation du comportement Chronotime observé. Ils ne doivent pas être lus comme des règles juridiques ou RH définitives.

Exemple provisoire à vérifier :

```json
{
  "GCP": 0.0,
  "JRTT": -10.0,
  "CANC": 0.0
}
```

Si une consommation rend un solde négatif tout en restant au-dessus du minimum, la projection ajoute une alerte de confirmation.

Si une consommation dépasse le minimum, la projection limite la consommation et ajoute une alerte bloquante.

Si une période explicitement demandée pour un compteur n’existe pas, la projection ajoute une alerte bloquante `periode_compteur_absente`. Le compteur n’est pas ignoré silencieusement.

## Consommations

Chaque demi-journée conserve deux niveaux de consommation.

`consommations` est un résumé agrégé par compteur, conservé pour compatibilité et pour les lectures simples :

```json
{
  "GCP": 0.5
}
```

`consommations_detaillees` est la structure destinée aux futures vues et aux diagnostics :

```json
[
  {
    "identifiant_evenement": "fermeture_ete",
    "source": "obligation",
    "compteur": "GCP",
    "quantite_demandee": 0.5,
    "quantite_appliquee": 0.5,
    "quantite_non_couverte": 0.0,
    "priorite": 100
  }
]
```

Les champs ont le sens suivant :

- `quantite_demandee` : part demandée par l’événement sur cette demi-journée ;
- `quantite_appliquee` : part réellement consommée après contrôle du minimum du compteur ;
- `quantite_non_couverte` : part refusée car elle dépasserait le minimum autorisé.

Les consommations détaillées sont traitées par priorité décroissante quand plusieurs événements consomment le même compteur sur la même demi-journée.

## Courbes de soldes futures

Les futures courbes de soldes devront être produites à partir d’une projection enrichie ou d’événements de compteur explicites.

La GUI ne doit pas inventer :

- crédits futurs ;
- acquisitions ;
- ouvertures de validité ;
- expirations ;
- reports ;
- ajustements.

Ces éléments appartiennent au modèle événementiel source décrit dans [docs/MODÈLE_ÉVÉNEMENTS_COMPTEURS.md](./MODÈLE_ÉVÉNEMENTS_COMPTEURS.md).

La vue `Soldes dans le temps` devra lire ces événements quand le moteur les produira, puis les afficher comme une courbe en marches.

## Jours Non Décomptés

Les jours non décomptés sont fournis manuellement dans `jours_non_decomptes`.

En V0/V1, cette liste s’applique seulement aux unités :

- `jours_ouvres` ;
- `jours_ouvrables`.

Elle ne s’applique pas automatiquement à `jours_calendaires`, car certaines absences calendaires peuvent inclure week-ends et jours fériés.

La gestion complète des jours fériés reste à vérifier.

## Sortie

La sortie suit la source :

```json
{
  "source": "projection.demi_journees",
  "periode": {
    "debut": "2026-05-20",
    "fin": "2026-12-31"
  },
  "etat_initial": {
    "date": "2026-05-20",
    "soldes": {}
  },
  "soldes_initiaux": {},
  "evenements_compteurs": {
    "source": "evenements_compteurs.normalises",
    "evenements": [],
    "resume": {}
  },
  "evenements_sources": [],
  "demi_journees": [],
  "soldes_aux_dates_cibles": [],
  "alertes": [],
  "resume": {
    "nombre_demi_journees": 0,
    "nombre_evenements_sources": 0,
    "nombre_alertes": 0
  }
}
```

La clé `evenements_compteurs` prépare la future vue `Soldes dans le temps`.

En l’état, ces événements sont seulement transportés. Ils ne modifient pas `soldes_initiaux`, `soldes_avant` ou `soldes_apres`.

## Limite

Cette projection ne modifie pas Chronotime. Elle ne remplace pas les règles réelles de Chronotime et ne prétend pas être juridiquement complète.

## Limites métier connues

- acquisition future non gérée ;
- expiration non gérée ;
- pose de congés non provisionnés non tranchée ;
- parentalité non détaillée ;
- règles Valeo à vérifier ;
- chevauchements d’agenda non validés par le projecteur.

Les chevauchements d’absences, par exemple avec `TELV`, seront traités par un validateur séparé.

Les limites métier sont à lire avec la mémoire des règles de congés : [docs/MÉMOIRE_RÈGLES_CONGÉS.md](./MÉMOIRE_RÈGLES_CONGÉS.md).
