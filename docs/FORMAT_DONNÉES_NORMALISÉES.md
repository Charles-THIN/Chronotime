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
- les dictionnaires Chronotime fournis sous forme de listes sont indexés par `cod` ou `code` ;
- les types `evt["2"]` et `evt["9"]` sont seulement résumés dans `resume_source`.

## Séparation Des Scénarios

Les données normalisées Chronotime restent distinctes des scénarios locaux.

Il faut distinguer :

- les données importées ou normalisées depuis Chronotime ;
- le scénario local, qui contient les blocs simulés et les préférences de l’utilisateur ;
- le résultat de calcul futur, qui dépend du scénario mais ne doit pas se confondre avec lui.

Cette séparation évite de mélanger les faits importés, les hypothèses de simulation et les projections calculées.

## Scénario Local Normalisé

Le chargeur de scénarios transforme un fichier de simulation local en scénario normalisé.

Forme générale :

```json
{
  "source": "simulation.locale",
  "scenario": {
    "identifiant": "scenario_exemple",
    "libelle": "Scénario exemple anonymisé",
    "periode": {
      "debut": "2026-05-01",
      "fin": "2027-04-30"
    },
    "dates_cibles": [],
    "preferences": {},
    "blocs": [
      {
        "identifiant_local": "bloc_vacances_ete",
        "libelle": "Vacances d'été",
        "type": "bloc_simule",
        "source": "simulation.locale",
        "date_debut": "2026-08-03",
        "date_fin": "2026-08-14",
        "unite": "jours_ouvrables",
        "fraction_jour": 1.0,
        "compteur_souhaite": "GCP",
        "compteur_reellement_consomme": null,
        "statut": "simule",
        "verrouillage": false,
        "priorite": 50,
        "date_limite": "2026-12-31",
        "notes_locales": "",
        "actif": true,
        "duree": {
          "unite": "jours_ouvrables",
          "valeur": 10.0,
          "methode": "jours_lundi_a_samedi"
        }
      }
    ]
  },
  "resume": {
    "nombre_blocs": 1,
    "nombre_blocs_actifs": 1,
    "nombre_blocs_inactifs": 0
  }
}
```

Les durées sont des estimations locales provisoires. Elles ne tiennent pas encore compte des jours fériés, des calendriers entreprise, des fermetures ou des règles Chronotime exactes.

## Obligations Locales Normalisées

Le chargeur d’obligations transforme un fichier local d’obligations de congés en contraintes normalisées.

Forme générale :

```json
{
  "source": "obligations.locales",
  "annee": 2026,
  "perimetre": {
    "site": "creteil",
    "societe": "vcda"
  },
  "obligations": [
    {
      "identifiant": "rtt_2026_01_02",
      "libelle": "Fermeture du vendredi 2 janvier 2026",
      "type": "rtt_a_positionner",
      "date_debut": "2026-01-02",
      "date_fin": "2026-01-02",
      "unite": "jours_ouvres",
      "quantite": 1.0,
      "compteurs_autorises": ["JRTT"],
      "compteur_prefere": "JRTT",
      "statut": "a_poser",
      "verrouillage": true,
      "priorite": 100,
      "notes": "",
      "duree_calculee": {
        "unite": "jours_ouvres",
        "valeur": 1.0,
        "methode": "quantite_declaree"
      }
    }
  ],
  "resume": {
    "nombre_obligations": 1,
    "quantite_totale": 1.0,
    "quantites_par_compteur_prefere": {
      "JRTT": 1.0
    }
  }
}
```

Les obligations locales ne créent pas de droits. Elles indiquent seulement des quantités à poser sur des compteurs existants.

## Vérification Des Obligations Locales

Le vérificateur compare des obligations locales normalisées avec un agenda Chronotime normalisé.

Forme générale :

```json
{
  "source": "verification.obligations",
  "obligations": [
    {
      "identifiant": "rtt_2026_05_25",
      "libelle": "Journée de solidarité du lundi 25 mai 2026",
      "statut_obligation": "satisfaite",
      "quantite_requise": 1.0,
      "quantite_satisfaite": 1.0,
      "quantite_restante": 0.0,
      "compteurs_autorises": ["JRTT"],
      "evenements_compatibles": [
        {
          "date": "2026-05-25",
          "code": "JRTT",
          "libelle": "RTT posé",
          "unite": {
            "code": "J",
            "libelle": "Jour complet",
            "fraction_jour": 1.0
          },
          "fraction_utilisee": 1.0,
          "statut": {
            "code": "A",
            "libelle": "Accepté"
          }
        }
      ]
    }
  ],
  "resume": {
    "nombre_obligations": 1,
    "nombre_satisfaites": 1,
    "nombre_partielles": 0,
    "nombre_a_poser": 0,
    "quantite_totale_requise": 1.0,
    "quantite_totale_satisfaite": 1.0,
    "quantite_totale_restante": 0.0
  }
}
```

La vérification ne conserve que les champs utiles des événements compatibles et ne modifie pas Chronotime.
