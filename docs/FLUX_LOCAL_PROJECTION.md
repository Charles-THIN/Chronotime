# Flux local de projection

L’orchestrateur local assemble les fichiers JSON locaux et enchaîne les briques existantes.

```text
fichiers JSON locaux
-> normalisation
-> vérification des obligations
-> projection demi-journalière
```

## Entrées

Le flux prend quatre fichiers :

- soldes Chronotime `soldeabs` ;
- agenda Chronotime `agenda` ;
- obligations locales ;
- scénario local.

Les vrais fichiers utilisateur doivent rester dans `donnees_locales/`. Les fichiers sous `donnees/exemples/` sont artificiels ou anonymisés.

## Étapes

L’orchestrateur :

- normalise les soldes avec le parseur `soldeabs` ;
- normalise l’agenda avec le parseur `agenda` ;
- normalise le scénario local ;
- normalise les obligations locales ;
- vérifie les obligations avec l’agenda normalisé ;
- assemble l’entrée attendue par le projecteur ;
- lance la projection demi-journalière.

## Sortie

La sortie est directement le format `projection.demi_journees`.

Aucun fichier intermédiaire n’est écrit sauf si l’option `--sortie` est fournie pour la projection finale.

## Limites

L’orchestrateur reste local.

Il ne se connecte pas à Chronotime, ne fait aucun appel HTTP, n’automatise pas de navigateur et ne modifie pas Chronotime.
