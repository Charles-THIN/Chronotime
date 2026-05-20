# Points d'entrée Chronotime

Points d’entrée observés manuellement, sous forme anonymisée :

- `GET /chronotime/rest/soldeabs/config?matricule=<MATRICULE>`
- `GET /chronotime/rest/soldeabs/<MATRICULE>%2CYYYYMMDD%2Ctrue%2Ctrue?index=1&nbrang=75`
- `GET /chronotime/rest/absence/composant/liste?matricule=<MATRICULE>&absence=true&souhait=false&statuts=...&datedeb=YYYYMMDD&index=1&nbrang=50`
- `GET /chronotime/rest/agenda/YYYYMMDD%2CYYYYMMDD%2C<MATRICULE>?type=...&combos=1`
- `GET /chronotime/rest/agenda/<MATRICULE>/avenir?statuts=...&types=A&combos=1`

Point d’entrée des soldes de congés :

- `GET /chronotime/rest/soldeabs/<MATRICULE>%2CYYYYMMDD%2Ctrue%2Ctrue?index=1&nbrang=75`
- la réponse renvoie une liste de compteurs ;
- chaque compteur contient notamment `code`, `libelle`, `precedent`, `courant` et `suivant`.

Ne pas committer :

- le vrai domaine ;
- le vrai matricule ;
- les en-têtes HTTP ;
- les cookies ;
- les jetons ;
- les noms personnels ;
- les noms de service ;
- les identifiants internes.
