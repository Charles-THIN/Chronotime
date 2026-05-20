# PROCHAINE_TÂCHE.md

## Tâche

Vérifier et corriger l’initialisation réellement poussée sur GitHub.

## Objectif

S’assurer que le dépôt local contient bien tous les fichiers de l’initialisation, que les noms décidés en français sont cohérents partout, puis pousser l’état corrigé sur `main`.

Cette tâche ne doit ajouter aucun parseur, aucun accès Chronotime, aucune interface et aucune dépendance.

## Contexte

Le rapport précédent indique que l’initialisation a été faite, mais une vérification distante montre encore un `AGENTS.md` non aligné avec les décisions de nommage françaises.

Les décisions actuelles sont :

- `RAPPORT_CODEX_LOCAL.md` et non `CODEX_REPORT_LOCAL.md` ;
- `donnees_locales/` et non `local_data/` ;
- `donnees/exemples/` et non `data/sample/` ;
- `outils/` et non `tools/`.

Tout ce qui est sous notre contrôle doit être en français.

Exceptions admises seulement pour les noms imposés par les outils ou API externes : `.gitignore`, `AGENTS.md`, mots-clés Python, commandes Git/Python, noms d’API Chronotime observés, extensions de fichiers.

## Fichiers à vérifier ou modifier

- `.gitignore`
- `AGENTS.md`
- `LISEZ_MOI.md`
- `docs/PROCHAINE_TÂCHE.md`
- `docs/ARCHITECTURE.md`
- `docs/CONFIDENTIALITÉ_DONNÉES.md`
- `docs/POINTS_D_ENTRÉE_CHRONOTIME.md`
- `donnees/exemples/LISEZ_MOI.md`
- `outils/LISEZ_MOI.md`
- `tests/LISEZ_MOI.md`

## Instructions d’implémentation

1. Vérifier l’état Git :

    git status
    git branch --show-current
    git log --oneline --decorate -5
    git ls-tree -r --name-only HEAD

2. Vérifier que la branche courante est `main`.

3. Vérifier que les fichiers attendus existent localement :

    .gitignore
    AGENTS.md
    LISEZ_MOI.md
    docs/PROCHAINE_TÂCHE.md
    docs/ARCHITECTURE.md
    docs/CONFIDENTIALITÉ_DONNÉES.md
    docs/POINTS_D_ENTRÉE_CHRONOTIME.md
    donnees/exemples/LISEZ_MOI.md
    outils/LISEZ_MOI.md
    tests/LISEZ_MOI.md

4. Corriger `AGENTS.md` pour l’aligner sur les décisions actuelles.

   Remplacer toute mention de :

    CODEX_REPORT_LOCAL.md

   par :

    RAPPORT_CODEX_LOCAL.md

   Remplacer toute mention de :

    local_data/

   par :

    donnees_locales/

   Remplacer toute mention de :

    data/sample/

   par :

    donnees/exemples/

   Remplacer toute mention de :

    tools/

   par :

    outils/

5. Vérifier que `.gitignore` contient au minimum :

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

6. Vérifier que `RAPPORT_CODEX_LOCAL.md` n’est pas suivi par Git.

   S’il est suivi par erreur, le retirer de l’index sans le supprimer localement :

    git rm --cached RAPPORT_CODEX_LOCAL.md

7. Vérifier qu’aucun fichier de données privées n’est suivi :

    git ls-files

   Aucun fichier sous `donnees_locales/` ne doit apparaître.

8. Ne pas ajouter de vraie donnée Chronotime.

9. Ne pas ajouter de code de parseur.

10. Ne pas ajouter de dépendance.

11. Si des fichiers attendus manquent, les créer en respectant le contenu minimal demandé dans la tâche précédente.

12. Pousser l’état corrigé sur `main`.

## Contraintes

- Garder les changements minimaux.
- Corriger seulement l’initialisation et les incohérences de nommage.
- Utiliser le français partout où c’est sous notre contrôle.
- Ne pas ajouter de vraies données Chronotime.
- Ne pas ajouter d’accès HTTP direct.
- Ne pas ajouter d’automatisation navigateur.
- Ne pas ajouter d’automatisation Google Drive.
- Ne pas modifier de fichiers sans rapport.

## Validation

Lancer :

    git status
    git branch --show-current
    git ls-tree -r --name-only HEAD
    git diff --stat
    git diff -- .gitignore AGENTS.md LISEZ_MOI.md docs donnees outils tests
    git ls-files

Puis pousser :

    git push

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

La section “Confirmation de confidentialité” doit indiquer explicitement :

- qu’aucune vraie donnée Chronotime n’a été ajoutée ;
- qu’aucun fichier sous `donnees_locales/` n’est suivi par Git ;
- que `RAPPORT_CODEX_LOCAL.md` n’est pas suivi par Git.

Si aucune déviation n’a eu lieu, écrire :

    Aucune.

Si aucun blocage n’existe, écrire :

    Aucun.