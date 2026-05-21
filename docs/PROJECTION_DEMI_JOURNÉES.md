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

Chaque demi-journée contient les événements projetés, les consommations de compteurs, les soldes avant et après, ainsi que les alertes éventuelles.

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
