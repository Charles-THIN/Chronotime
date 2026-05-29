# Architecture

Le projet reste volontairement simple.

- `donnees_locales/` contient les données privées locales, ignorées par Git.
- `donnees/exemples/` contient les exemples artificiels ou anonymisés.
- `outils/` contient les aides locales.
- les données internes sont normalisées avant usage.
- les projections dérivées alimentent les futures vues.

Flux moteur actuel :

```text
données locales Chronotime
-> normalisation des soldes et de l’agenda
-> scénario local + obligations locales + événements de compteur
-> projection.demi_journees
-> mouvements.soldes
-> chronologie.soldes
-> futures vues
```

`projection.demi_journees`, `mouvements.soldes` et `chronologie.soldes` sont des sorties dérivées. Elles ne sont pas des sources éditables.
