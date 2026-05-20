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

## Agenda Chronotime

Le parseur local peut aussi transformer une réponse `agenda` en une structure normalisée des événements utiles.

Forme générale :

```json
{
  "source": "chronotime.agenda",
  "plage_dates": {
    "debut": "2026-05-17",
    "fin": "2026-05-24"
  },
  "evenements": [
    {
      "date": "2026-05-18",
      "categorie": "absence",
      "code": "CANC",
      "libelle": "ABS CP ANCIENNETE",
      "unite": {
        "code": "M",
        "libelle": "Matin",
        "fraction_jour": 0.5
      },
      "horaire": {
        "debut_brut": 0,
        "fin_brut": 1159,
        "debut": "00:00",
        "fin": "11:59"
      },
      "statut": {
        "code": "A",
        "libelle": "Accepté"
      },
      "type_evenement_source": "1"
    }
  ],
  "dictionnaires": {
    "absences": {},
    "groupes_absence": {},
    "statuts": {},
    "unites": {},
    "horaires": {}
  },
  "resume_source": {
    "types_evenements_ignores": {
      "2": 2,
      "9": 8
    }
  }
}
```

Règles principales :

- `source` vaut `chronotime.agenda` ;
- `plage_dates` reprend `datd` et `datf` au format `YYYY-MM-DD` ;
- `evt["1"]` est normalisé en événements de catégorie `absence` ;
- `evt["0"]` est normalisé en événements de catégorie `horaire` ;
- les dictionnaires utiles de `dts` sont simplifiés et nettoyés ;
- les types `evt["2"]` et `evt["9"]` sont seulement résumés dans `resume_source`.
