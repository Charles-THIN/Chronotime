# Architecture

Le projet reste volontairement simple.

- `donnees_locales/` contient les données privées locales, ignorées par Git.
- `donnees/exemples/` contient les exemples artificiels ou anonymisés.
- `outils/` contient les aides locales.
- les données internes sont normalisées avant usage.
- une future couche de visualisation consommera ces données normalisées.
