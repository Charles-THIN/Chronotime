# Contrat moteur GUI

## Portée

Ce document définit le contrat minimal entre la future interface graphique Chronotime et le moteur dynamique.

Il ne décrit pas une implémentation. Il fixe un vocabulaire et des formats conceptuels pour éviter que la GUI porte des règles métier dispersées.

Flux cible :

```text
geste utilisateur
-> commande d’intention
-> moteur / état central
-> résultat accepté ou refusé
-> état recalculé ou inchangé
-> diagnostics structurés
-> vues dérivées
```

Le moteur actuel local est en Python. Le contrat GUI cible doit être indépendant de la technologie. Ce qui est obligatoire : un moteur identifiable, testé, séparé du rendu visuel.

## Principes

- La GUI traduit les gestes utilisateur en commandes d’intention.
- Le moteur accepte, refuse ou signale une erreur.
- La GUI affiche l’état central et les diagnostics renvoyés.
- La GUI conserve seulement un état transitoire d’interface.
- `projection.demi_journees`, `mouvements.soldes` et `chronologie.soldes` restent des sorties dérivées.
- Les actions utilisateur modifient des sources ou un scénario local, jamais directement une projection déjà calculée.
- La GUI ne calcule pas elle-même l’allocation des compteurs, les soldes, les expirations, les reports ou la validité métier d’un déplacement.

## État central

`etat_central` est l’objet conceptuel que les vues consomment.

Forme minimale :

```json
{
  "version_contrat": "0.1",
  "periode": {
    "date_debut": "2026-05-20",
    "date_fin": "2026-12-31"
  },
  "sources": {
    "scenario_local": {},
    "obligations_locales": [],
    "evenements_compteurs": []
  },
  "projection": {
    "demi_journees": [],
    "resume": {},
    "soldes_aux_dates_cibles": []
  },
  "mouvements_soldes": [],
  "chronologie_soldes": [],
  "blocs_affichables": [],
  "diagnostics": []
}
```

Cette forme est conceptuelle. Elle peut être matérialisée différemment selon la technologie retenue.

Règles :

- `sources` contient les éléments éditables ou modifiables par commande.
- `projection` est dérivée des sources.
- `mouvements_soldes` est dérivé.
- `chronologie_soldes` est dérivée.
- `blocs_affichables` prépare un rendu commun pour le calendrier et la frise.
- `diagnostics` décrit les informations, confirmations, blocages ou erreurs que les vues doivent afficher.

## Commandes

Une commande est une intention utilisateur structurée.

Forme minimale :

```json
{
  "type": "deplacer_absence",
  "identifiant_commande": "commande_001",
  "cible": {
    "type": "bloc_absence",
    "identifiant": "bloc_ete_001"
  },
  "parametres": {
    "date_debut": "2026-08-10",
    "date_fin": "2026-08-14"
  },
  "mode": "appliquer"
}
```

Commandes minimales :

- `ajouter_absence` ;
- `supprimer_absence` ;
- `deplacer_absence` ;
- `redimensionner_absence` ;
- `scinder_absence` ;
- `fusionner_absences` ;
- `changer_type_absence` ;
- `prevalider_action`.

Modes :

- `previsualiser` : le moteur évalue sans modifier durablement l’état central ;
- `appliquer` : le moteur accepte ou refuse la modification.

Même la prévisualisation vient du moteur. La GUI peut afficher un fantôme de manipulation, mais elle ne doit pas décider seule qu’une action est métier-validable.

## Résultat de commande

Forme minimale :

```json
{
  "identifiant_commande": "commande_001",
  "statut": "acceptee",
  "etat_central": {},
  "diagnostics": [],
  "selection_suggeree": {
    "type": "bloc_absence",
    "identifiant": "bloc_ete_001"
  }
}
```

Statuts :

- `acceptee` ;
- `refusee` ;
- `inchangee` ;
- `partielle` ;
- `erreur`.

`partielle` ne doit être utilisé que si ce cas est explicitement modélisé. Par défaut, préférer `acceptee`, `refusee` ou `inchangee`.

Exemple de refus :

```json
{
  "identifiant_commande": "commande_002",
  "statut": "refusee",
  "etat_central": "etat_inchange_ou_reference",
  "diagnostics": [
    {
      "niveau": "bloquant",
      "code": "compteur_expire",
      "message": "Déplacement impossible : le compteur indicatif n’est plus utilisable à cette date.",
      "cibles": [
        {
          "type": "bloc_absence",
          "identifiant": "bloc_ete_001"
        },
        {
          "type": "date",
          "date": "2026-08-14"
        }
      ]
    }
  ]
}
```

## Diagnostics

Un diagnostic est une information structurée produite par le moteur.

Forme minimale :

```json
{
  "niveau": "bloquant",
  "code": "solde_insuffisant",
  "message": "Solde insuffisant pour appliquer cette absence.",
  "cibles": [
    {
      "type": "compteur",
      "code": "GCP"
    }
  ],
  "details": {}
}
```

Niveaux minimaux :

- `information` ;
- `avertissement` ;
- `confirmation` ;
- `bloquant` ;
- `erreur`.

Types de cibles minimaux :

- `bloc_absence` ;
- `date` ;
- `demi_journee` ;
- `compteur` ;
- `commande` ;
- `vue` ;
- `global`.

La GUI peut rendre visuellement les diagnostics, mais ne doit pas inventer leur signification métier.

## Blocs affichables

Un bloc affichable est une lecture unifiée destinée au calendrier et à la frise.

Forme minimale :

```json
{
  "type": "bloc_absence_affichable",
  "identifiant": "bloc_ete_001",
  "date_debut": "2026-08-10",
  "date_fin": "2026-08-14",
  "origine": "scenario_local",
  "statut": "simule",
  "compteur": "GCP",
  "quantite_jours": 5,
  "diagnostics": []
}
```

Origines minimales :

- `chronotime` ;
- `obligation_locale` ;
- `scenario_local` ;
- `prototype_interface`.

`prototype_interface` est temporaire. Il peut aider à explorer l’ergonomie, mais ne doit pas devenir une source métier durable.

## État transitoire d’interface

L’interface peut conserver localement :

- `selection_courante` ;
- `survol` ;
- `outil_actif` ;
- `fantome_deplacement` ;
- `plage_en_cours` ;
- `message_temporaire`.

Ces éléments ne sont pas des sources métier.

Le fantôme de glisser-déposer peut être affiché pendant une manipulation. La validation vient ensuite d’une commande `prevalider_action` ou `appliquer`.

## Vues dérivées

Les vues consomment l’état central :

- calendrier ;
- frise ;
- compteurs ;
- alertes ;
- sélection ;
- curseur.

Elles ne recalculent pas chacune :

- allocation des compteurs ;
- soldes ;
- expirations ;
- reports ;
- validité métier d’un déplacement.

## Exemples de flux

### Ajouter une absence

```text
clic ou cliquer-déplacer dans le calendrier
-> commande ajouter_absence en mode previsualiser
-> diagnostics de faisabilité
-> fantôme affiché depuis le résultat de prévisualisation
-> commande ajouter_absence en mode appliquer
-> état central recalculé ou refusé
-> calendrier, frise, compteurs et alertes rafraîchis depuis le même état
```

### Déplacer une absence

```text
cliquer-déplacer un bloc
-> commande deplacer_absence en mode previsualiser pendant la manipulation
-> diagnostic bloquant ou confirmation si nécessaire
-> commande deplacer_absence en mode appliquer au relâchement
-> projection recalculée si acceptée
-> état inchangé si refusée
```

### Supprimer une absence

```text
sélection d’un bloc
-> commande supprimer_absence en mode appliquer
-> suppression ou désactivation dans le scénario local
-> projection recalculée
-> sélection suggérée vide ou sur le bloc voisin
```

## Points volontairement non figés

- technologie du moteur dynamique ;
- forme exacte de persistance du scénario local ;
- schéma JSON strict ;
- politique de résolution des commandes partielles ;
- granularité exacte des diagnostics ;
- stratégie de prévalidation en continu pendant le glisser-déposer ;
- formule exacte du reste agrégé ;
- validité fine par période `precedent`, `courant`, `suivant` ;
- règles RH de crédits, expirations, reports, acquisitions et parentalité.
