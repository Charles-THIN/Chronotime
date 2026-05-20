# Modèle Des Scénarios

Un scénario est un ensemble de blocs simulés séparé des données Chronotime réelles.

Il sert à décrire ce que l’utilisateur veut tester localement, sans réécrire les données importées.

## Types De Blocs

Le scénario doit distinguer au minimum :

- événement réel importé depuis Chronotime ;
- bloc simulé ;
- congé imposé déjà posé ;
- congé imposé non encore posé ;
- bloc verrouillé ;
- bloc parentalité ;
- bloc ignoré ou désactivé.

Un même bloc peut cumuler plusieurs propriétés, par exemple être simulé, verrouillé et parentalité.

## Contenu D’Un Bloc

Un bloc peut contenir :

- identifiant local ;
- libellé ;
- type ;
- source ;
- date de début ;
- date de fin ;
- unité ;
- fraction de jour ;
- compteur souhaité ;
- compteur réellement consommé après calcul ;
- statut ;
- verrouillage ;
- priorité ;
- date limite ou expiration éventuelle ;
- notes locales.

## Structure Du Scénario

Un scénario contient généralement :

- un identifiant local ;
- un libellé ;
- une période de travail ;
- des dates cibles ;
- des préférences de consommation des compteurs ;
- une liste de blocs ;
- éventuellement des règles locales de tri ou d’affichage.

## Règles De Conception

- les données Chronotime importées restent séparées du scénario ;
- les blocs simulés ne doivent jamais modifier les données brutes importées ;
- un bloc verrouillé reste présent mais protégé contre les modifications accidentelles ;
- un bloc ignoré ou désactivé reste dans le scénario mais est exclu des calculs actifs ;
- un bloc parentalité peut utiliser des unités et des durées différentes des congés classiques ;
- le scénario doit pouvoir représenter des jours ouvrés, des jours calendaires, des demi-journées et des heures sans mélange silencieux.

## Modèle Minimal

Un modèle minimal de scénario doit permettre de décrire :

- les dates cibles comme Noël ou une fin de période ;
- l’ordre de consommation des compteurs, par exemple le plus tôt à expirer d’abord ;
- les blocs simulés posés par l’utilisateur ;
- les congés imposés déjà posés ou encore à poser ;
- les préférences de conservation de certains soldes.

## Forme Normalisée

Le chargeur de scénarios produit une forme normalisée exploitable par les futurs calculs.

Il ajoute notamment :

- `actif`, pour indiquer si un bloc doit participer aux calculs futurs ;
- `duree`, pour porter une durée simple calculée à partir des dates et de l’unité ;
- `resume`, pour compter les blocs actifs et inactifs.

Le calcul de durée est provisoire. Il ne tient pas encore compte :

- des jours fériés ;
- des calendriers entreprise ;
- des fermetures ;
- des règles Chronotime exactes.

## Obligations Locales

Les obligations locales restent séparées des scénarios.

Elles représentent des contraintes de pose connues localement, par exemple une fermeture ou un RTT à positionner. Elles pourront être converties plus tard en blocs verrouillés de scénario, mais elles ne sont pas encore fusionnées avec les scénarios dans cette étape.
