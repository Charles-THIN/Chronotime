# Format des données normalisées

Le parseur local transforme une réponse `soldeabs` en une structure normalisée simple et lisible.

Forme générale :

```json
{
  "source": "chronotime.soldeabs",
  "compteurs": [
    {
      "code": "GCP",
      "libelle": "CONGES PAYES",
      "periodes": {
        "precedent": {
          "droit": { "brut": "0j00", "unite": "jour", "valeur": 0.0 },
          "pris": { "brut": "0j00", "unite": "jour", "valeur": 0.0 },
          "solde": { "brut": "0j00", "unite": "jour", "valeur": 0.0 }
        },
        "courant": {
          "droit": { "brut": "25j00", "unite": "jour", "valeur": 25.0 },
          "pris": { "brut": "1j90", "unite": "jour", "valeur": 1.9 },
          "solde": { "brut": "23j96", "unite": "jour", "valeur": 23.96 }
        },
        "suivant": {
          "droit": { "brut": "25j00", "unite": "jour", "valeur": 25.0 },
          "pris": { "brut": "2j00", "unite": "jour", "valeur": 2.0 },
          "solde": { "brut": "23j00", "unite": "jour", "valeur": 23.0 }
        }
      }
    }
  ]
}
```

Règles principales :

- `source` vaut toujours `chronotime.soldeabs` ;
- chaque compteur conserve son `code` ;
- `libelle` est nettoyé des espaces inutiles en début et fin ;
- les périodes `precedent`, `courant` et `suivant` sont conservées ;
- une période absente reste `null` ;
- une période présente contient `droit`, `pris` et `solde` normalisés ;
- chaque quantité garde sa forme brute et reçoit une unité (`jour` ou `heure`) ainsi qu’une valeur numérique.
