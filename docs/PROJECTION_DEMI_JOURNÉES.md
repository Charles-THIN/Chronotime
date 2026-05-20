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
- pas de jours fériés ;
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
