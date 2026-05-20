# Obligations locales

Les obligations locales sont des contraintes de pose connues par note RH ou saisie utilisateur.

Elles représentent des jours que l’utilisateur doit poser manuellement dans Chronotime.

Elles ne créent pas de droits :

- elles ne sont pas des congés offerts ;
- elles réservent ou consomment des compteurs existants ;
- elles peuvent être déjà satisfaites si une absence compatible est déjà visible dans l’agenda Chronotime ;
- elles peuvent rester à poser si Chronotime ne contient encore rien à cette date.

## Séparations importantes

Une obligation locale est distincte :

- d’une absence Chronotime déjà posée ;
- d’un bloc de simulation ;
- d’un résultat futur de vérification.

Le futur moteur pourra comparer les obligations locales avec l’agenda normalisé pour savoir si elles sont satisfaites, mais ce document ne définit pas encore ce calcul.

## Interprétation

Une obligation locale décrit une contrainte à respecter.

Exemples :

- fermeture de site ;
- pont ;
- RTT à positionner ;
- congé payé imposé ;
- minimum de jours à poser sur une période.

Les quantités indiquées dans les obligations locales sont des quantités déclarées. Elles ne doivent pas être recalculées automatiquement dans le chargeur.

## Vérification

La vérification compare les obligations locales à un agenda Chronotime déjà normalisé.

Un événement d’agenda est compatible avec une obligation si :

- il est de catégorie `absence` ;
- sa date est comprise dans la période de l’obligation ;
- son code fait partie des compteurs autorisés par l’obligation.

Une obligation peut être :

- `satisfaite` si la quantité compatible couvre la quantité requise ;
- `partielle` si une partie seulement est couverte ;
- `a_poser` si aucune absence compatible n’est visible.

Ce résultat ne modifie pas Chronotime. Il sert seulement à préparer les actions que l’utilisateur reporte ensuite manuellement.
