# Architecture hybride événements / demi-journées

Le modèle éditable du dépôt reste événementiel. La demi-journée n’est pas la source de vérité, c’est une projection dérivée.

Voir aussi la mémoire dédiée des règles de congés : [docs/MÉMOIRE_RÈGLES_CONGÉS.md](./MÉMOIRE_RÈGLES_CONGÉS.md).

## Source De Vérité Éditable

La source de vérité éditable contient :

- les événements ;
- les blocs ;
- les obligations ;
- les crédits ;
- les expirations ;
- les scénarios.

Ces objets représentent les intentions, les contraintes et les faits locaux ou importés. Ils sont modifiables directement.

## Sorties Dérivées

Les sorties dérivées contiennent :

- `projection.demi_journees`, vecteur de demi-journées avec consommations, soldes propagés et alertes ;
- `mouvements.soldes`, liste de mouvements de solde signés ;
- `chronologie.soldes`, chronologie cumulée dérivée des mouvements de solde ;
- les données prêtes pour les vues.

Ces sorties sont recalculées à partir du modèle événementiel. Elles ne sont pas éditées directement comme source de vérité.

`mouvements.soldes` ne calcule pas encore les soldes cumulés. Il prépare seulement une liste stable de variations élémentaires.

`chronologie.soldes` applique ces mouvements aux soldes initiaux. Elle reste dérivée et non éditable.

## Pourquoi Garder Le Modèle Événementiel

Le modèle événementiel est plus sûr pour les calculs métier :

- un bloc de congé reste un objet unique ;
- les quantités déclarées restent attachées à l’événement ;
- les obligations comme Noël peuvent avoir une plage civile et une quantité déclarée différente ;
- l’annulation et l’historique sont plus simples ;
- les crédits et expirations sont naturellement des événements datés ;
- on évite les demi-journées orphelines ou incohérentes.

## Pourquoi Garder La Projection Demi-Journalière

La projection demi-journalière reste utile pour l’affichage et la lecture rapide :

- une case correspond à une demi-journée ;
- les demi-journées correspondent bien aux unités Chronotime `M` et `S` ;
- la frise peut colorer directement les cases ;
- la lecture du solde à Noël devient immédiate ;
- les vues n’ont pas besoin de recalculer la logique métier.

## Actions Utilisateur

Les actions utilisateur modifient le modèle événementiel source.

Exemples :

- déplacer un bloc de vacances modifie `date_debut` et `date_fin` du bloc source ;
- redimensionner un bloc modifie sa période source ;
- désactiver un bloc modifie son statut ou son type ;
- cliquer sur une demi-journée vide crée un nouvel événement source ;
- supprimer un bloc supprime ou désactive l’événement source.

Après modification, le vecteur de demi-journées est recalculé.

## Rôle Du Vecteur De Demi-Journées

Le vecteur de demi-journées sert à :

- afficher la frise 1D ;
- afficher le calendrier annuel compact ;
- afficher la projection des soldes ;
- lire directement les soldes à une date cible ;
- afficher les conflits et alertes.

## Flux De Calcul Cible

```text
soldes Chronotime normalisés
+ agenda Chronotime normalisé
+ obligations locales
+ scénario local
+ événements de compteur
-> projection.demi_journees
-> mouvements.soldes
-> chronologie.soldes
-> vues
```

## Forme Cible D’Une Demi-Journée

```json
{
  "date": "2026-08-10",
  "portion": "matin",
  "index_demi_journee": 0,
  "evenements": [],
  "consommations": {
    "GCP": 0.5
  },
  "soldes_avant": {
    "GCP": 20.0,
    "JRTT": 4.0,
    "CANC": 5.0
  },
  "soldes_apres": {
    "GCP": 19.5,
    "JRTT": 4.0,
    "CANC": 5.0
  },
  "alertes": []
}
```

## Forme Cible Globale

```json
{
  "source": "projection.demi_journees",
  "periode": {
    "debut": "2026-05-20",
    "fin": "2027-04-30"
  },
  "soldes_initiaux": {},
  "evenements_sources": [],
  "demi_journees": [],
  "soldes_aux_dates_cibles": [],
  "alertes": []
}
```

## Règle D’Architecture

Les événements sources sont la vérité éditable.

`projection.demi_journees` est dérivée, recalculée, et destinée à l’affichage et aux lectures rapides.

`mouvements.soldes` est dérivé de `projection.demi_journees` et des événements de compteur transportés. Il n’est pas éditable et ne calcule pas encore les soldes cumulés.

`chronologie.soldes` est dérivé de `projection.demi_journees` et de `mouvements.soldes`. Il cumule les mouvements par code de compteur, sans gérer encore la validité fine par période.

Les actions utilisateur futures modifieront les sources événementielles, jamais directement les sorties dérivées.
