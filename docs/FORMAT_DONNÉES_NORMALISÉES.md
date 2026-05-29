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

## Architecture Hybride

Les données normalisées Chronotime et les scénarios locaux restent des sources distinctes.

La mémoire de référence des règles de congés est documentée dans [docs/MÉMOIRE_RÈGLES_CONGÉS.md](./MÉMOIRE_RÈGLES_CONGÉS.md).

Le format attendu sépare :

- le modèle source événementiel, éditable ;
- la projection dérivée `projection.demi_journees` ;
- les lectures prêtes pour les vues.

La projection demi-journalière peut être recalculée à tout moment. Elle ne doit pas être éditée directement comme source de vérité.

## Projection Demi-Journalière

Le projecteur demi-journalier produit une sortie dérivée à partir de données déjà normalisées.

Forme générale :

```json
{
  "source": "projection.demi_journees",
  "periode": {
    "debut": "2026-05-20",
    "fin": "2026-12-31"
  },
  "etat_initial": {
    "date": "2026-05-20",
    "soldes": {
      "GCP": 20.0,
      "JRTT": 4.0,
      "CANC": 5.0
    }
  },
  "parametres_projection": {
    "periode_compteurs": "courant",
    "periodes_compteurs_par_code": {
      "GCP": "suivant",
      "JRTT": "courant",
      "CANC": "courant"
    },
    "soldes_minimums_par_code": {
      "GCP": 0.0,
      "JRTT": -10.0,
      "CANC": 0.0
    },
    "jours_non_decomptes": ["2026-12-25"]
  },
  "soldes_initiaux": {
    "GCP": 20.0,
    "JRTT": 4.0,
    "CANC": 5.0
  },
  "evenements_compteurs": {
    "source": "evenements_compteurs.normalises",
    "evenements": [],
    "resume": {
      "nombre_evenements": 0,
      "nombres_par_type": {},
      "quantites_par_compteur": {}
    }
  },
  "evenements_sources": [],
  "demi_journees": [
    {
      "date": "2026-05-20",
      "portion": "matin",
      "index_demi_journee": 0,
      "evenements": [],
      "consommations": {},
      "consommations_detaillees": [],
      "soldes_avant": {},
      "soldes_apres": {},
      "alertes": []
    }
  ],
  "soldes_aux_dates_cibles": [],
  "alertes": [],
  "resume": {
    "nombre_demi_journees": 0,
    "nombre_evenements_sources": 0,
    "nombre_alertes": 0
  }
}
```

Règles principales :

- `projection.demi_journees` est une projection dérivée, non une source éditable ;
- chaque date contient deux portions, `matin` et `apres_midi` ;
- les événements sources viennent des obligations restantes et des blocs actifs du scénario ;
- `evenements_compteurs` transporte les événements de compteur normalisés pour une projection enrichie future ;
- les soldes sont propagés demi-journée par demi-journée ;
- `parametres_projection.periodes_compteurs_par_code` permet de choisir une période différente selon le compteur ;
- `parametres_projection.soldes_minimums_par_code` permet de définir un minimum autorisé par compteur ;
- `parametres_projection.jours_non_decomptes` exclut des dates manuelles pour les unités `jours_ouvres` et `jours_ouvrables` ;
- `consommations` est un résumé agrégé par compteur ;
- `consommations_detaillees` conserve la consommation par événement source avec `quantite_demandee`, `quantite_appliquee` et `quantite_non_couverte` ;
- chaque alerte contient une `severite` valant `information`, `confirmation` ou `bloquant` ;
- `periode_compteur_absente` indique qu’une période explicitement demandée pour un compteur n’existe pas dans les soldes normalisés ;
- `quantite_evenement_non_projectee` indique qu’un événement source n’a pas pu être entièrement réparti sur sa plage ;
- `solde_negatif_confirmation_possible` indique un solde négatif autorisé sous réserve de confirmation ;
- `solde_minimum_depasse` indique une consommation bloquée au minimum autorisé ;
- `evenement_hors_periode_projection` indique un événement source ignoré car hors période de projection ;
- les soldes aux dates cibles sont lus après la dernière demi-journée de la date.
- les événements de compteur transportés ne sont pas encore appliqués aux soldes.

Exemple de consommation détaillée :

```json
{
  "identifiant_evenement": "fermeture_noel_2026",
  "source": "obligation",
  "compteur": "GCP",
  "quantite_demandee": 0.5,
  "quantite_appliquee": 0.5,
  "quantite_non_couverte": 0.0,
  "priorite": 100
}
```

## Événements De Compteur

Les événements de compteur sont des événements sources qui expliquent une variation, une disponibilité ou une correction de compteur.

Ils ne sont pas inventés par la GUI.

Le chargeur local produit une forme normalisée avec :

- `source: "evenements_compteurs.normalises"` ;
- `evenements` ;
- `resume`.

Forme générale :

```json
{
  "source": "evenements_compteurs.normalises",
  "evenements": [
    {
      "identifiant": "credit_gcp_exemple",
      "type": "credit_compteur",
      "date_effet": "2026-06-01",
      "compteur": "GCP",
      "quantite": 2.0,
      "unite": "jour",
      "source": "exemple_artificiel",
      "statut_certitude": "a_verifier",
      "notes": ""
    }
  ]
}
```

Le `resume` contient :

- `nombre_evenements` ;
- `nombres_par_type` ;
- `quantites_par_compteur`.

Les quantités du résumé restent prudentes : une ouverture de validité n’est pas comptée comme un crédit automatique.

Dans l’entrée et la sortie de projection, la clé `evenements_compteurs` contient cette structure normalisée. Elle prépare les futures courbes de solde sans modifier encore les soldes projetés.

Types prévus :

- `credit_compteur` ;
- `ouverture_validite_compteur` ;
- `expiration_compteur` ;
- `report_compteur` ;
- `ajustement_compteur` ;
- `consommation_absence`.

Les périodes Chronotime `precedent`, `courant` et `suivant` restent des stocks observés. Elles ne doivent pas être converties automatiquement en événements de compteur sans règle explicite et vérifiable.

Le modèle détaillé est documenté dans [docs/MODÈLE_ÉVÉNEMENTS_COMPTEURS.md](./MODÈLE_ÉVÉNEMENTS_COMPTEURS.md).

Exemples d’alertes :

```json
{
  "type": "periode_compteur_absente",
  "severite": "bloquant",
  "compteur": "GCP",
  "periode_demandee": "suivnat",
  "periodes_disponibles": ["courant", "suivant"]
}
```

```json
{
  "type": "quantite_evenement_non_projectee",
  "severite": "bloquant",
  "identifiant_evenement": "fermeture_noel_2026",
  "quantite_restante": 1.0,
  "unite": "jours_ouvres",
  "date_debut": "2026-12-25",
  "date_fin": "2026-12-31"
}
```

## Orchestrateur Local De Projection

L’orchestrateur local enchaîne les formats normalisés existants.

Il lit des fichiers locaux séparés pour les soldes, l’agenda, les obligations et le scénario, puis produit directement une sortie `projection.demi_journees`.

Il n’écrit pas de fichier intermédiaire et reste limité à des données locales.
