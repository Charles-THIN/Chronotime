# PROCHAINE_TÂCHE.md

## Tâche

Initialiser le dépôt local Chronotime en français.

## Objectif

Créer la structure minimale sûre du dépôt pour un outil local de visualisation et de simulation des congés.

Cette tâche doit mettre en place :

- les dossiers de base ;
- les règles d’exclusion Git ;
- une documentation minimale ;
- les emplacements prévus pour les données d’exemple anonymisées ;
- une règle claire : tout ce qui est sous notre contrôle doit être nommé en français.

Ne pas encore implémenter de parseur, d’accès direct à Chronotime, de synchronisation Google Drive ou d’interface utilisateur.

## Contexte

Ce dépôt sert à développer un outil personnel local de planification et de visualisation des congés.

Le projet utilisera plus tard des réponses JSON Chronotime observées manuellement, notamment :

- les réponses `soldeabs` pour les compteurs de congés ;
- les réponses `agenda` pour le calendrier et les événements d’absence.

Le dépôt peut être public. Par conséquent, seules des données d’exemple anonymisées peuvent être committées.

Les données Chronotime réelles, fichiers HAR, journaux bruts, captures d’écran, cookies, jetons, données personnelles, URL internes et fichiers OAuth doivent rester hors Git.

## Règle de langue

Tout ce qui est sous notre contrôle doit être en français :

- noms de dossiers ;
- noms de fichiers ;
- noms de fonctions ;
- noms de classes ;
- noms de variables ;
- clés JSON internes ;
- documentation ;
- rapports ;
- commentaires ;
- libellés visibles par l’utilisateur.

Exceptions admises uniquement quand le nom est imposé par un outil, un langage ou une API externe :

- `.gitignore` ;
- `AGENTS.md` ;
- mots-clés Python ;
- noms d’API Chronotime observés, par exemple `soldeabs`, `agenda`, `matricule` ;
- commandes Git ou Python ;
- extensions de fichiers ;
- noms de paquets externes.

## Fichiers à créer ou modifier

- `.gitignore`
- `LISEZ_MOI.md`
- `AGENTS.md` si une mise à jour est nécessaire
- `docs/PROCHAINE_TÂCHE.md`
- `docs/ARCHITECTURE.md`
- `docs/POINTS_D_ENTRÉE_CHRONOTIME.md`
- `docs/CONFIDENTIALITÉ_DONNÉES.md`
- `donnees/exemples/LISEZ_MOI.md`
- `outils/LISEZ_MOI.md`
- `tests/LISEZ_MOI.md`

## Instructions d’implémentation

1. Vérifier ou créer les dossiers suivants :

    docs/
    donnees/exemples/
    outils/
    tests/
    donnees_locales/

2. Créer ou mettre à jour `.gitignore`.

   Il doit contenir au minimum :

    donnees_locales/
    *.har
    RAPPORT_CODEX_LOCAL.md
    credentials.json
    token.pickle
    **/credentials.json
    **/token.pickle
    .env
    .venv/
    __pycache__/
    *.pyc

3. Créer ou mettre à jour `LISEZ_MOI.md`.

   Le fichier doit expliquer brièvement, en français, que le dépôt contient un outil local personnel de visualisation et de simulation des congés.

   Il doit préciser que l’outil :

   - sert à simuler localement des absences ;
   - utilise seulement des données d’exemple anonymisées dans le dépôt ;
   - ne doit jamais contenir de vraies données Chronotime ;
   - ne doit jamais écrire automatiquement dans Chronotime ;
   - sert à préparer des actions que l’utilisateur reporte ensuite manuellement dans Chronotime.

4. Vérifier `AGENTS.md`.

   Si `AGENTS.md` existe déjà, le mettre à jour pour préciser que tout ce qui est sous notre contrôle doit être en français.

   Il doit aussi indiquer que le rapport local Codex doit s’appeler :

    RAPPORT_CODEX_LOCAL.md

   et non :

    CODEX_REPORT_LOCAL.md

5. Créer `docs/ARCHITECTURE.md`.

   Garder le document court.

   Décrire les couches prévues :

   - données privées locales dans `donnees_locales/` ;
   - données d’exemple anonymisées dans `donnees/exemples/` ;
   - outils locaux dans `outils/` ;
   - données internes normalisées ;
   - future couche de visualisation.

6. Créer `docs/POINTS_D_ENTRÉE_CHRONOTIME.md`.

   Documenter uniquement les formes anonymisées de points d’entrée déjà observées manuellement :

    GET /chronotime/rest/soldeabs/config?matricule=<MATRICULE>

    GET /chronotime/rest/soldeabs/<MATRICULE>%2CYYYYMMDD%2Ctrue%2Ctrue?index=1&nbrang=75

    GET /chronotime/rest/absence/composant/liste?matricule=<MATRICULE>&absence=true&souhait=false&statuts=...&datedeb=YYYYMMDD&index=1&nbrang=50

    GET /chronotime/rest/agenda/YYYYMMDD%2CYYYYMMDD%2C<MATRICULE>?type=...&combos=1

    GET /chronotime/rest/agenda/<MATRICULE>/avenir?statuts=...&types=A&combos=1

   Ne pas inclure :

   - le vrai domaine ;
   - le vrai matricule ;
   - les en-têtes HTTP ;
   - les cookies ;
   - les jetons ;
   - les noms personnels ;
   - les noms de service ;
   - les identifiants internes.

7. Créer `docs/CONFIDENTIALITÉ_DONNÉES.md`.

   Le document doit dire explicitement qu’il ne faut jamais committer :

   - exports Chronotime réels ;
   - fichiers HAR ;
   - captures d’écran ;
   - journaux bruts ;
   - cookies ;
   - en-têtes d’autorisation ;
   - jetons de session ;
   - identifiants OAuth ;
   - URL internes ;
   - données personnelles de calendrier ;
   - données internes d’entreprise ;
   - noms de collègues, managers ou RH ;
   - matricules ou identifiants internes.

8. Créer `donnees/exemples/LISEZ_MOI.md`.

   Le fichier doit indiquer que les fichiers d’exemple doivent être artificiels ou anonymisés.

9. Créer `outils/LISEZ_MOI.md`.

   Le fichier doit indiquer que les outils sont des aides locales.

   Il doit préciser qu’ils ne doivent pas écrire dans Chronotime.

10. Créer `tests/LISEZ_MOI.md`.

   Le fichier doit indiquer que les tests doivent utiliser uniquement des données artificielles ou anonymisées.

11. Ne pas créer de code de parseur dans cette tâche.

12. Ne pas créer de code d’interface utilisateur dans cette tâche.

13. Ne pas ajouter de dépendance dans cette tâche.

14. Ne pas committer `donnees_locales/`.

## Contraintes

- Garder les changements minimaux.
- Utiliser le français partout où c’est sous notre contrôle.
- Ne pas ajouter de vraies données Chronotime.
- Ne pas ajouter d’appels HTTP directs vers Chronotime.
- Ne pas ajouter d’automatisation navigateur.
- Ne pas ajouter d’automatisation Google Drive.
- Ne pas modifier de fichiers sans rapport.

## Validation

Lancer :

    git status
    git diff --stat
    git diff -- .gitignore LISEZ_MOI.md AGENTS.md docs donnees outils tests

Aucune commande de compilation ou de test n’est attendue pour cette tâche.

## Rapport attendu

Écrire `RAPPORT_CODEX_LOCAL.md` avec les sections suivantes :

    # Rapport Codex

    ## Résumé

    ## Fichiers créés ou modifiés

    ## Commandes lancées

    ## Résultats

    ## Confirmation de confidentialité

    ## Déviations

    ## Blocages ou questions

La section “Confirmation de confidentialité” doit indiquer explicitement qu’aucune vraie donnée Chronotime n’a été ajoutée.

Si aucune déviation n’a eu lieu, écrire :

    Aucune.

Si aucun blocage n’existe, écrire :

    Aucun.