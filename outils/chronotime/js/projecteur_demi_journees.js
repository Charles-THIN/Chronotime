const PORTIONS = ["matin", "apres_midi"];
const SOURCE_SORTIE = "projection.demi_journees";
const SOURCE_EVENEMENTS_COMPTEURS = "evenements_compteurs.normalises";

function estObjet(valeur) {
  return valeur !== null && typeof valeur === "object" && !Array.isArray(valeur);
}

function estNombre(valeur) {
  return typeof valeur === "number" && Number.isFinite(valeur);
}

function dateUtc(iso) {
  const date = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(date.getTime()) || date.toISOString().slice(0, 10) !== iso) {
    return null;
  }
  return date;
}

export function normaliserDateIso(valeur, nomChamp = "date") {
  if (valeur === null || valeur === undefined) {
    return null;
  }
  if (typeof valeur !== "string") {
    throw new Error(`Date ISO invalide pour ${nomChamp} : ${JSON.stringify(valeur)}`);
  }
  const date = dateUtc(valeur);
  if (!date) {
    throw new Error(`Date ISO invalide pour ${nomChamp} : ${JSON.stringify(valeur)}`);
  }
  return valeur;
}

function convertirDateIso(valeur, nomChamp) {
  const dateNormalisee = normaliserDateIso(valeur, nomChamp);
  if (dateNormalisee === null) {
    throw new Error(`Date ISO obligatoire pour ${nomChamp}.`);
  }
  return dateUtc(dateNormalisee);
}

function formatDate(date) {
  return date.toISOString().slice(0, 10);
}

function ajouterJours(date, jours) {
  const copie = new Date(date.getTime());
  copie.setUTCDate(copie.getUTCDate() + jours);
  return copie;
}

function comparerDates(a, b) {
  return a.getTime() - b.getTime();
}

function weekdayPython(date) {
  return (date.getUTCDay() + 6) % 7;
}

function arrondirQuantite(valeur) {
  return Number(Number(valeur).toFixed(10));
}

function evenementsCompteursVides() {
  return {
    source: SOURCE_EVENEMENTS_COMPTEURS,
    evenements: [],
    resume: {
      nombre_evenements: 0,
      nombres_par_type: {},
      quantites_par_compteur: {},
    },
  };
}

function extraireEvenementsCompteurs(donnees) {
  return estObjet(donnees.evenements_compteurs) ? donnees.evenements_compteurs : evenementsCompteursVides();
}

export function extraireSoldesInitiaux(donnees, periode = "courant", periodesParCompteur = null, alertes = null) {
  const soldes = estObjet(donnees.soldes) ? donnees.soldes : {};
  const compteurs = Array.isArray(soldes.compteurs) ? soldes.compteurs : [];
  const soldesInitiaux = {};
  const periodesSpecifiques = estObjet(periodesParCompteur) ? periodesParCompteur : {};

  for (const compteur of compteurs) {
    if (!estObjet(compteur)) {
      continue;
    }
    const code = compteur.code;
    const periodes = compteur.periodes;
    if (!code || !estObjet(periodes)) {
      continue;
    }
    const codeCompteur = String(code);
    const periodeSpecifique = Object.prototype.hasOwnProperty.call(periodesSpecifiques, codeCompteur);
    const periodeAUtiliser = periodeSpecifique ? periodesSpecifiques[codeCompteur] : periode;
    const periodeCompteur = periodes[periodeAUtiliser];
    if (!estObjet(periodeCompteur)) {
      if (alertes) {
        alertes.push({
          type: "periode_compteur_absente",
          severite: periodeSpecifique ? "bloquant" : "information",
          compteur: codeCompteur,
          periode_demandee: String(periodeAUtiliser),
          periodes_disponibles: Object.keys(periodes).map(String).sort(),
        });
      }
      continue;
    }
    const solde = periodeCompteur.solde;
    if (!estObjet(solde)) {
      continue;
    }
    if (estNombre(solde.valeur)) {
      soldesInitiaux[codeCompteur] = Number(solde.valeur);
    }
  }

  return soldesInitiaux;
}

export function creerVecteurDemiJournees(dateDepart, dateFin) {
  const debut = convertirDateIso(dateDepart, "parametres_projection.date_depart");
  const fin = convertirDateIso(dateFin, "parametres_projection.date_fin");
  if (comparerDates(fin, debut) < 0) {
    throw new Error("La date de fin de projection doit être postérieure ou égale à la date de départ.");
  }

  const demiJournees = [];
  let index = 0;
  for (let dateCourante = debut; comparerDates(dateCourante, fin) <= 0; dateCourante = ajouterJours(dateCourante, 1)) {
    for (const portion of PORTIONS) {
      demiJournees.push({
        date: formatDate(dateCourante),
        portion,
        index_demi_journee: index,
        evenements: [],
        consommations: {},
        consommations_detaillees: [],
        soldes_avant: {},
        soldes_apres: {},
        alertes: [],
      });
      index += 1;
    }
  }
  return demiJournees;
}

function choisirCompteur(compteursAutorises, compteurPrefere, ordreSansPreference) {
  const compteurs = Array.isArray(compteursAutorises) ? compteursAutorises.filter(Boolean).map(String) : [];
  if (compteurs.length === 0) {
    return null;
  }
  if (compteurs.length === 1) {
    return compteurs[0];
  }
  if (compteurPrefere) {
    const compteur = String(compteurPrefere);
    if (compteurs.includes(compteur)) {
      return compteur;
    }
  }
  const ordre = Array.isArray(ordreSansPreference) ? ordreSansPreference : [];
  for (const compteur of ordre) {
    const compteurTexte = String(compteur);
    if (compteurs.includes(compteurTexte)) {
      return compteurTexte;
    }
  }
  return compteurs[0];
}

function construireEvenementsObligations(donnees, ordreSansPreference) {
  const verification = estObjet(donnees.verification_obligations) ? donnees.verification_obligations : {};
  const obligations = Array.isArray(verification.obligations) ? verification.obligations : [];
  const evenements = [];

  for (const obligation of obligations) {
    if (!estObjet(obligation)) {
      continue;
    }
    if (obligation.statut_obligation === "satisfaite") {
      continue;
    }
    const quantite = estNombre(obligation.quantite_restante) ? obligation.quantite_restante : obligation.quantite_requise;
    if (!estNombre(quantite) || quantite <= 0) {
      continue;
    }
    const compteur = choisirCompteur(
      obligation.compteurs_autorises || [],
      obligation.compteur_prefere,
      ordreSansPreference,
    );
    if (compteur === null) {
      continue;
    }
    evenements.push({
      source: "obligation",
      identifiant: String(obligation.identifiant || ""),
      libelle: String(obligation.libelle || ""),
      date_debut: normaliserDateIso(obligation.date_debut, "obligation.date_debut"),
      date_fin: normaliserDateIso(obligation.date_fin, "obligation.date_fin"),
      unite: String(obligation.unite || "jours_ouvres"),
      quantite: Number(quantite),
      compteur,
      priorite: Number.parseInt(obligation.priorite ?? 100, 10),
    });
  }
  return evenements;
}

function resoudreChoixCompteurAuto(_bloc) {
  return null;
}

function choixCompteurBloc(bloc) {
  return estObjet(bloc.choix_compteur) ? bloc.choix_compteur : null;
}

function ajouterAlerteChoixCompteurAuto(alertes, bloc) {
  if (!alertes) {
    return;
  }
  alertes.push({
    type: "choix_compteur_auto_a_resoudre",
    severite: "information",
    identifiant_evenement: String(bloc.identifiant_local || ""),
    message: "Le choix automatique du compteur est une intention utilisateur qui devra être résolue par le moteur d’optimisation.",
  });
}

function construireEvenementsScenario(donnees, alertes = null) {
  const donneesScenario = estObjet(donnees.scenario) ? donnees.scenario : {};
  const scenario = estObjet(donneesScenario.scenario) ? donneesScenario.scenario : {};
  const blocs = Array.isArray(scenario.blocs) ? scenario.blocs : [];
  const evenements = [];

  for (const bloc of blocs) {
    if (!estObjet(bloc)) {
      continue;
    }
    if (bloc.actif === false || bloc.statut === "desactive") {
      continue;
    }
    const choixCompteur = choixCompteurBloc(bloc);
    let compteur = bloc.compteur_souhaite;
    let sourceDecisionCompteur = "utilisateur";
    let justificationDecisionCompteur = "Compteur demandé explicitement par l’utilisateur.";
    if (choixCompteur && choixCompteur.mode === "auto") {
      const compteurAuto = resoudreChoixCompteurAuto(bloc);
      if (!compteurAuto) {
        ajouterAlerteChoixCompteurAuto(alertes, bloc);
        continue;
      }
      compteur = compteurAuto;
      sourceDecisionCompteur = "moteur";
      justificationDecisionCompteur = "Compteur résolu automatiquement par le moteur.";
    } else if (choixCompteur && choixCompteur.mode === "manuel") {
      compteur = choixCompteur.compteur;
    }
    if (!compteur) {
      continue;
    }
    const duree = estObjet(bloc.duree) ? bloc.duree : {};
    const quantite = estNombre(duree.valeur) ? duree.valeur : bloc.fraction_jour;
    if (!estNombre(quantite) || quantite <= 0) {
      continue;
    }
    evenements.push({
      source: "scenario",
      identifiant: String(bloc.identifiant_local || ""),
      libelle: String(bloc.libelle || ""),
      date_debut: normaliserDateIso(bloc.date_debut, "bloc.date_debut"),
      date_fin: normaliserDateIso(bloc.date_fin, "bloc.date_fin"),
      unite: String(bloc.unite || duree.unite || "jours_ouvres"),
      quantite: Number(quantite),
      compteur: String(compteur),
      priorite: Number.parseInt(bloc.priorite ?? 50, 10),
      origine_bloc: String(bloc.origine_bloc || ""),
      choix_compteur: choixCompteur,
      source_decision_compteur: sourceDecisionCompteur,
      justification_decision_compteur: justificationDecisionCompteur,
    });
  }
  return evenements;
}

export function construireEvenementsSources(donnees, parametres, alertes = null) {
  const ordreSansPreference = parametres.ordre_compteurs_sans_preference || [];
  const evenements = construireEvenementsObligations(donnees, ordreSansPreference);
  evenements.push(...construireEvenementsScenario(donnees, alertes));
  return evenements.sort((a, b) => (
    a.date_debut.localeCompare(b.date_debut)
    || a.priorite - b.priorite
    || a.identifiant.localeCompare(b.identifiant)
  ));
}

function jourEstProjectable(jour, unite, joursNonDecomptes = null) {
  if (["jours_ouvres", "jours_ouvrables"].includes(unite) && joursNonDecomptes && joursNonDecomptes.has(formatDate(jour))) {
    return false;
  }
  if (unite === "jours_ouvres") {
    return weekdayPython(jour) < 5;
  }
  if (unite === "jours_ouvrables") {
    return weekdayPython(jour) < 6;
  }
  if (unite === "jours_calendaires") {
    return true;
  }
  return false;
}

function resumerEvenement(evenement, quantiteProjectee) {
  const resume = {
    source: evenement.source,
    identifiant: evenement.identifiant,
    libelle: evenement.libelle,
    compteur: evenement.compteur,
    quantite_projectee: arrondirQuantite(quantiteProjectee),
  };
  for (const champ of ["origine_bloc", "choix_compteur", "source_decision_compteur", "justification_decision_compteur"]) {
    if (Object.prototype.hasOwnProperty.call(evenement, champ)) {
      resume[champ] = evenement[champ];
    }
  }
  return resume;
}

function ajouterConsommation(demiJournee, evenement, quantite) {
  const compteur = evenement.compteur;
  demiJournee.evenements.push(resumerEvenement(evenement, quantite));
  demiJournee.consommations[compteur] = arrondirQuantite((demiJournee.consommations[compteur] || 0.0) + quantite);
  const detail = {
    identifiant_evenement: evenement.identifiant,
    source: evenement.source,
    compteur,
    quantite_demandee: arrondirQuantite(quantite),
    quantite_appliquee: null,
    quantite_non_couverte: null,
    priorite: evenement.priorite,
  };
  for (const champ of ["choix_compteur", "source_decision_compteur", "justification_decision_compteur"]) {
    if (Object.prototype.hasOwnProperty.call(evenement, champ)) {
      detail[champ] = evenement[champ];
    }
  }
  demiJournee.consommations_detaillees.push(detail);
}

function ajouterAlerteQuantiteNonProjectee(alertes, evenement, quantiteRestante) {
  if (quantiteRestante <= 0) {
    return;
  }
  alertes.push({
    type: "quantite_evenement_non_projectee",
    severite: "bloquant",
    identifiant_evenement: evenement.identifiant,
    quantite_restante: arrondirQuantite(quantiteRestante),
    unite: evenement.unite,
    date_debut: evenement.date_debut,
    date_fin: evenement.date_fin,
  });
}

function projeterEvenement(evenement, demiJournees, alertes, joursNonDecomptes = null) {
  const unite = evenement.unite;
  let quantiteRestante = Number(evenement.quantite);

  if (unite === "heures") {
    alertes.push({
      type: "unite_non_projectee",
      severite: "information",
      identifiant_evenement: evenement.identifiant,
      unite,
    });
    ajouterAlerteQuantiteNonProjectee(alertes, evenement, quantiteRestante);
    return;
  }

  const debut = convertirDateIso(evenement.date_debut, "evenement.date_debut");
  const fin = convertirDateIso(evenement.date_fin, "evenement.date_fin");

  for (const demiJournee of demiJournees) {
    if (quantiteRestante <= 0) {
      break;
    }

    const jour = convertirDateIso(demiJournee.date, "demi_journee.date");
    if (comparerDates(jour, debut) < 0 || comparerDates(jour, fin) > 0) {
      continue;
    }

    if (unite === "demi_journee") {
      if (formatDate(jour) === formatDate(debut) && demiJournee.portion === "matin") {
        const quantite = Math.min(0.5, quantiteRestante);
        ajouterConsommation(demiJournee, evenement, quantite);
        quantiteRestante = arrondirQuantite(quantiteRestante - quantite);
      }
      break;
    }

    if (!jourEstProjectable(jour, unite, joursNonDecomptes)) {
      continue;
    }

    const quantite = Math.min(0.5, quantiteRestante);
    ajouterConsommation(demiJournee, evenement, quantite);
    quantiteRestante = arrondirQuantite(quantiteRestante - quantite);
  }

  ajouterAlerteQuantiteNonProjectee(alertes, evenement, quantiteRestante);
}

export function projeterEvenements(evenements, demiJournees, alertes, dateDepart, dateFin, joursNonDecomptes = null) {
  const debutProjection = convertirDateIso(dateDepart, "parametres_projection.date_depart");
  const finProjection = convertirDateIso(dateFin, "parametres_projection.date_fin");

  for (const evenement of evenements) {
    const debutEvenement = convertirDateIso(evenement.date_debut, "evenement.date_debut");
    const finEvenement = convertirDateIso(evenement.date_fin, "evenement.date_fin");
    if (comparerDates(finEvenement, debutProjection) < 0 || comparerDates(debutEvenement, finProjection) > 0) {
      alertes.push({
        type: "evenement_hors_periode_projection",
        severite: "information",
        identifiant_evenement: evenement.identifiant,
        date_debut: evenement.date_debut,
        date_fin: evenement.date_fin,
      });
      continue;
    }
    projeterEvenement(evenement, demiJournees, alertes, joursNonDecomptes);
  }
}

export function propagerSoldes(demiJournees, soldesInitiaux, alertes, soldesMinimumsParCode = null) {
  const soldesCourants = { ...soldesInitiaux };

  for (const demiJournee of demiJournees) {
    demiJournee.soldes_avant = { ...soldesCourants };

    const consommationsParCompteur = {};
    for (const detail of demiJournee.consommations_detaillees || []) {
      const compteurDetail = String(detail.compteur);
      if (!consommationsParCompteur[compteurDetail]) {
        consommationsParCompteur[compteurDetail] = [];
      }
      consommationsParCompteur[compteurDetail].push(detail);
    }

    for (const [compteur, details] of Object.entries(consommationsParCompteur)) {
      let disponible = Number(soldesCourants[compteur] || 0.0);
      const minimumAutorise = Number((soldesMinimumsParCode || {})[compteur] || 0.0);
      const detailsTries = [...details].sort((a, b) => (
        Number.parseInt(b.priorite || 0, 10) - Number.parseInt(a.priorite || 0, 10)
        || String(b.identifiant_evenement || "").localeCompare(String(a.identifiant_evenement || ""))
      ));

      for (const detail of detailsTries) {
        const quantiteDemandee = Number(detail.quantite_demandee || 0.0);
        const quantitePossible = Math.max(arrondirQuantite(disponible - minimumAutorise), 0.0);
        const quantiteAppliquee = Math.min(quantiteDemandee, quantitePossible);
        const quantiteNonCouverte = arrondirQuantite(quantiteDemandee - quantiteAppliquee);
        const soldeApres = arrondirQuantite(disponible - quantiteAppliquee);

        detail.quantite_appliquee = arrondirQuantite(quantiteAppliquee);
        detail.quantite_non_couverte = quantiteNonCouverte;

        if (quantiteNonCouverte > 0) {
          const alerte = {
            type: "solde_minimum_depasse",
            severite: "bloquant",
            date: demiJournee.date,
            portion: demiJournee.portion,
            compteur,
            quantite_demandee: arrondirQuantite(quantiteDemandee),
            quantite_appliquee: arrondirQuantite(quantiteAppliquee),
            quantite_disponible_jusqu_au_minimum: arrondirQuantite(quantitePossible),
            quantite_non_couverte: quantiteNonCouverte,
            minimum_autorise: arrondirQuantite(minimumAutorise),
            identifiants_evenements: [detail.identifiant_evenement],
          };
          demiJournee.alertes.push(alerte);
          alertes.push(alerte);
        }

        if (quantiteAppliquee > 0 && soldeApres < 0 && quantiteNonCouverte === 0) {
          const alerte = {
            type: "solde_negatif_confirmation_possible",
            severite: "confirmation",
            date: demiJournee.date,
            portion: demiJournee.portion,
            compteur,
            solde_apres: soldeApres,
            minimum_autorise: arrondirQuantite(minimumAutorise),
            identifiants_evenements: [detail.identifiant_evenement],
          };
          demiJournee.alertes.push(alerte);
          alertes.push(alerte);
        }

        disponible = soldeApres;
        soldesCourants[compteur] = soldeApres;
      }
    }

    demiJournee.soldes_apres = { ...soldesCourants };
  }
}

function extraireSoldesAuxDatesCibles(demiJournees, datesCibles, dateDepart, dateFin, alertes) {
  const debut = convertirDateIso(dateDepart, "parametres_projection.date_depart");
  const fin = convertirDateIso(dateFin, "parametres_projection.date_fin");
  const demiJourneesParDate = new Map();
  for (const demiJournee of demiJournees) {
    demiJourneesParDate.set(demiJournee.date, demiJournee);
  }
  const soldesAuxDates = [];

  const cibles = Array.isArray(datesCibles) ? datesCibles : [];
  for (const cible of cibles) {
    if (!estObjet(cible)) {
      continue;
    }
    const dateCible = convertirDateIso(cible.date, "date_cible.date");
    if (comparerDates(dateCible, debut) < 0 || comparerDates(dateCible, fin) > 0) {
      const alerte = {
        type: "date_cible_hors_periode",
        severite: "information",
        identifiant: cible.identifiant,
        date: formatDate(dateCible),
      };
      alertes.push(alerte);
      soldesAuxDates.push({
        identifiant: cible.identifiant,
        libelle: cible.libelle,
        date: formatDate(dateCible),
        soldes: null,
      });
      continue;
    }

    const demiJournee = demiJourneesParDate.get(formatDate(dateCible));
    soldesAuxDates.push({
      identifiant: cible.identifiant,
      libelle: cible.libelle,
      date: formatDate(dateCible),
      soldes: demiJournee.soldes_apres,
    });
  }
  return soldesAuxDates;
}

export function projeterDemiJournees(donnees) {
  const parametres = donnees.parametres_projection;
  if (!estObjet(parametres)) {
    throw new Error("Les paramètres de projection sont obligatoires.");
  }

  const dateDepart = normaliserDateIso(parametres.date_depart, "parametres_projection.date_depart");
  const dateFin = normaliserDateIso(parametres.date_fin, "parametres_projection.date_fin");
  if (dateDepart === null || dateFin === null) {
    throw new Error("La projection exige une date de départ et une date de fin.");
  }

  const periodeCompteurs = String(parametres.periode_compteurs || "courant");
  const periodesCompteursParCode = estObjet(parametres.periodes_compteurs_par_code) ? parametres.periodes_compteurs_par_code : {};
  const soldesMinimumsBruts = estObjet(parametres.soldes_minimums_par_code) ? parametres.soldes_minimums_par_code : {};
  const soldesMinimumsParCode = {};
  for (const [code, minimum] of Object.entries(soldesMinimumsBruts)) {
    if (estNombre(minimum)) {
      soldesMinimumsParCode[String(code)] = Number(minimum);
    }
  }

  const joursNonDecomptesBruts = Array.isArray(parametres.jours_non_decomptes) ? parametres.jours_non_decomptes : [];
  const joursNonDecomptes = joursNonDecomptesBruts
    .map((jour) => normaliserDateIso(jour, "parametres_projection.jours_non_decomptes"))
    .filter((jour) => jour !== null);

  const alertes = [];
  const evenementsCompteurs = extraireEvenementsCompteurs(donnees);
  const soldesInitiaux = extraireSoldesInitiaux(donnees, periodeCompteurs, periodesCompteursParCode, alertes);
  const demiJournees = creerVecteurDemiJournees(dateDepart, dateFin);
  const evenementsSources = construireEvenementsSources(donnees, parametres, alertes);

  projeterEvenements(evenementsSources, demiJournees, alertes, dateDepart, dateFin, new Set(joursNonDecomptes));
  propagerSoldes(demiJournees, soldesInitiaux, alertes, soldesMinimumsParCode);

  const soldesAuxDatesCibles = extraireSoldesAuxDatesCibles(
    demiJournees,
    parametres.dates_cibles || [],
    dateDepart,
    dateFin,
    alertes,
  );

  const periodesProjection = {};
  for (const [code, periode] of Object.entries(periodesCompteursParCode)) {
    periodesProjection[String(code)] = String(periode);
  }

  return {
    source: SOURCE_SORTIE,
    periode: {
      debut: dateDepart,
      fin: dateFin,
    },
    etat_initial: {
      date: dateDepart,
      soldes: soldesInitiaux,
    },
    parametres_projection: {
      periode_compteurs: periodeCompteurs,
      periodes_compteurs_par_code: periodesProjection,
      soldes_minimums_par_code: soldesMinimumsParCode,
      jours_non_decomptes: joursNonDecomptes,
    },
    soldes_initiaux: soldesInitiaux,
    evenements_compteurs: evenementsCompteurs,
    evenements_sources: evenementsSources,
    demi_journees: demiJournees,
    soldes_aux_dates_cibles: soldesAuxDatesCibles,
    alertes,
    resume: {
      nombre_demi_journees: demiJournees.length,
      nombre_evenements_sources: evenementsSources.length,
      nombre_alertes: alertes.length,
    },
  };
}
