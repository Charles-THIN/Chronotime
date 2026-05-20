# Mémoire des règles de congés

## Portée du document

Cette mémoire rassemble les règles, hypothèses, données observées et points d’incertitude du projet Chronotime.

Elle sert de référence de projet pour les développements futurs, mais ne constitue pas un avis juridique définitif ni un substitut aux sources officielles, aux accords d’entreprise ou aux paramétrages Chronotime réels.

## Profil de travail utilisé par le projet

- cadre en CDI ;
- convention collective nationale de la métallurgie ;
- forfait jours 215 ;
- périmètre opérationnel Valeo Comfort & Driving Assist, site de Créteil.

## Sources de données

- données Chronotime observées en lecture seule ;
- données locales saisies dans le dépôt ;
- obligations issues d’une note interne ou RH ;
- règles légales publiques ;
- règles conventionnelles ou d’entreprise à vérifier ;
- hypothèses de modélisation retenues pour faire fonctionner les outils locaux.

La mémoire distingue systématiquement :

- le fait observé ;
- la règle officielle ;
- l’hypothèse locale ;
- le point à vérifier.

## Compteurs Chronotime observés

Les compteurs connus à ce stade sont :

- `GCP` : congés payés ;
- `JRTT` : RTT jours ;
- `CANC` : congés d’ancienneté ;
- `RECU` : récup jours cadre forfait ;
- `REHV` : récupération horaire variable ;
- `RCRH` : récupération RCR heures ;
- `COMP` : repos compensateur légal ;
- `CDIR` : congé cadre dirigeant ;
- `CSRE` : congé supplémentaire retraite ;
- `ASTJ` : récupération astreinte en jours ;
- `EDEP` : récupération déplacement.

Cette liste reflète des codes observés dans Chronotime. Elle ne décrit pas des soldes personnels et ne doit pas être interprétée comme un barème juridique.

## Absences déjà posées

Une absence déjà posée dans Chronotime est récupérable via l’endpoint `agenda`.

Exemple abstrait :

- une absence `CANC` peut apparaître sur une demi-journée matin ;
- les codes Chronotime `M` et `S` correspondent respectivement à matin et après-midi ;
- ces absences sont des faits observés, distincts des obligations locales non encore posées.

## Obligations locales de fermeture

Les obligations locales 2026 connues pour Créteil sont :

- vendredi 2 janvier 2026 : RTT à positionner ;
- vendredi 15 mai 2026 : RTT à positionner ;
- lundi 25 mai 2026 : RTT à positionner, journée de solidarité / Pentecôte ;
- lundi 13 juillet 2026 : RTT à positionner ;
- lundi 10 août au vendredi 14 août 2026 inclus : 5 jours à prendre obligatoirement en congé payé ;
- vendredi 25 décembre au jeudi 31 décembre 2026 inclus : 4 jours minimum à prendre en congé payé, RTT ou congé d’ancienneté.

Ces obligations ne créent pas de droits.

Elles consomment des compteurs existants.

Les 4 jours isolés sont à positionner en `JRTT`.

La fermeture d’été consomme `GCP`.

Noël consomme au moins 4 jours parmi `GCP`, `JRTT`, `CANC`.

Elles peuvent être satisfaites si l’agenda Chronotime contient déjà une absence compatible. Sinon elles restent `a_poser`.

## Scénarios locaux

Les scénarios locaux décrivent des intentions de simulation séparées des données Chronotime.

Ils peuvent contenir :

- des blocs simulés ;
- des blocs verrouillés ;
- des blocs parentaux ;
- des blocs désactivés ;
- des préférences de consommation ;
- des dates cibles.

Ils restent distincts des obligations locales et des absences déjà posées.

## Projection demi-journalière

La source éditable du projet reste événementielle.

La projection demi-journalière est une projection dérivée, stockée sous `projection.demi_journees`.

Elle ne doit pas être éditée directement.

La V0 ne gère pas encore :

- les acquisitions futures ;
- les expirations fines ;
- les jours fériés ;
- l’optimisation ;
- la parentalité détaillée.

## Parentalité

La parentalité est un domaine séparé.

Elle ne doit pas être mélangée silencieusement avec les compteurs classiques ni avec les congés imposés ordinaires.

### Règles déjà identifiées

#### Information légale confirmée

- congé de naissance : 3 jours ouvrables ;
- congé de paternité et d’accueil de l’enfant, période obligatoire : 4 jours calendaires immédiatement après le congé de naissance ;
- congé de paternité et d’accueil de l’enfant, période facultative : 21 jours calendaires pour une naissance simple ;
- la période obligatoire et la période facultative doivent être modélisées séparément ;
- les unités doivent rester explicites : jours ouvrables pour le congé de naissance, jours calendaires pour les 4 jours obligatoires et les 21 jours facultatifs.

#### Information fournie localement

- absence autorisée payée pour accompagner son épouse aux rendez-vous d’échographie : 3 demi-journées ;
- congé supplémentaire de naissance 2026 : durée maximale annoncée de 2 mois ;
- congé supplémentaire de naissance 2026 : premier mois à 70 %, deuxième mois à 60 %.

#### Point à vérifier côté Valeo / convention / décret

- code Chronotime exact pour les échographies ;
- justificatif et modalité de saisie pour les échographies ;
- unité exacte et maintien de salaire pour les échographies ;
- validation manager ou RH pour les échographies ;
- maintien employeur ou complément conventionnel pour naissance et paternité ;
- codes Chronotime exacts pour le congé de naissance, les 4 jours obligatoires et les 21 jours facultatifs ;
- fractionnement autorisé et délais internes ;
- articulation avec les congés imposés et les compteurs existants ;
- date exacte d’entrée en vigueur du congé supplémentaire de naissance 2026 ;
- conditions d’éligibilité ;
- délai de prise ;
- fractionnement possible ou non ;
- indemnisation exacte ;
- maintien ou complément employeur ;
- articulation avec congé de paternité ;
- articulation avec congé parental ;
- code Chronotime ou workflow RH ;
- impact sur ancienneté, forfait jours, JRTT et congés payés.

#### Modélisation future

La parentalité devra être représentée comme un domaine séparé avec des blocs de type :

- `absence_autorisee_echographie`
- `conge_naissance`
- `conge_paternite_obligatoire`
- `conge_paternite_facultatif`
- `conge_supplementaire_naissance`
- `conge_parental`

Ces blocs devront porter :

- unité ;
- durée ;
- mode d’indemnisation ;
- maintien employeur éventuel ;
- source de règle ;
- statut de certitude ;
- code Chronotime si connu.

Le congé supplémentaire de naissance 2026 doit rester marqué comme à vérifier tant que les textes d’application, les règles CPAM, les règles Valeo et les règles conventionnelles ne sont pas confirmés.

## Règles légales et conventionnelles

Les règles légales publiques doivent être vérifiées sur des sources officielles.

La convention collective nationale de la métallurgie doit être vérifiée sur la version applicable et sur les avenants pertinents.

Les accords d’entreprise Valeo / VCDA doivent être vérifiés avant d’être figés dans le projet.

Le paramétrage Chronotime doit être vérifié empiriquement à partir des observations locales.

Cette mémoire ne prétend pas figer l’intégralité du droit applicable. Elle garde les hypothèses de travail en séparant les certitudes, les observations et les points à confirmer.

## Incertitudes

- la pose de congés non encore totalement provisionnés n’est pas tranchée ;
- le mode `chronotime_previsionnel` doit rester compatible ;
- les dates exactes d’expiration et de bascule des compteurs peuvent dépendre du paramétrage réel ;
- les compteurs horaires demandent encore une modélisation dédiée ;
- les cas mixtes matin / après-midi avec compteurs différents restent à préciser ;
- la stratégie par défaut pour Noël sans compteur préféré doit encore être confirmée ;
- l’intégration des jours fériés dans le projecteur V1 reste ouverte ;
- les règles opérationnelles de parentalité doivent encore être consolidées ;
- les accords Valeo et les éventuels compléments de salaire doivent être vérifiés.

## Règles de confidentialité

- aucune donnée personnelle nouvelle n’est ajoutée dans cette mémoire ;
- aucune date personnelle précise de naissance n’est stockée ;
- aucun vrai solde Chronotime personnel n’est documenté ;
- aucun export Chronotime brut n’est conservé ici ;
- les éléments sensibles restent hors dépôt dans `donnees_locales/` ;
- le document doit rester une mémoire de travail, pas une reproduction de données RH réelles.
