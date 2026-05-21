from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path
from typing import Any


SOURCE_ATTENDUE = "projection.demi_journees"


def lire_json(chemin: Path) -> Any:
    try:
        texte = chemin.read_text(encoding="utf-8-sig")
    except OSError as erreur:
        raise SystemExit(f"Impossible de lire le fichier de projection : {chemin}") from erreur

    try:
        return json.loads(texte)
    except json.JSONDecodeError as erreur:
        raise SystemExit(f"JSON invalide dans le fichier de projection : {chemin}") from erreur


def charger_projection(chemin: Path) -> dict[str, Any]:
    donnees = lire_json(chemin)
    if not isinstance(donnees, dict):
        raise ValueError("La projection doit être un objet JSON.")
    if donnees.get("source") != SOURCE_ATTENDUE:
        raise ValueError(f"Source de projection invalide : {donnees.get('source')!r}.")
    return donnees


def serialiser_objet(valeur: Any) -> str:
    return escape(json.dumps(valeur, ensure_ascii=False, indent=2))


def cellule_tableau(valeur: Any) -> str:
    if isinstance(valeur, (dict, list)):
        return f"<pre>{serialiser_objet(valeur)}</pre>"
    if valeur is None:
        return "<span class=\"valeur-nulle\">null</span>"
    return escape(str(valeur))


def tableau_cle_valeur(titre: str, donnees: dict[str, Any]) -> str:
    lignes = []
    for cle, valeur in donnees.items():
        lignes.append(
            "<tr>"
            f"<th>{escape(str(cle))}</th>"
            f"<td>{cellule_tableau(valeur)}</td>"
            "</tr>"
        )
    corps = "\n".join(lignes) if lignes else "<tr><td colspan=\"2\">Aucune donnée.</td></tr>"
    return f"""
    <section class="carte">
      <h2>{escape(titre)}</h2>
      <table>
        <tbody>
          {corps}
        </tbody>
      </table>
    </section>
    """


def tableau_soldes(titre: str, soldes: dict[str, Any]) -> str:
    lignes = []
    for compteur, valeur in soldes.items():
        lignes.append(f"<tr><th>{escape(str(compteur))}</th><td>{escape(str(valeur))}</td></tr>")
    corps = "\n".join(lignes) if lignes else "<tr><td colspan=\"2\">Aucun solde.</td></tr>"
    return f"""
    <section class="carte">
      <h2>{escape(titre)}</h2>
      <table>
        <thead><tr><th>Compteur</th><th>Solde</th></tr></thead>
        <tbody>{corps}</tbody>
      </table>
    </section>
    """


def tableau_dates_cibles(dates_cibles: list[Any]) -> str:
    lignes = []
    for cible in dates_cibles:
        if not isinstance(cible, dict):
            continue
        lignes.append(
            "<tr>"
            f"<td>{escape(str(cible.get('identifiant', '')))}</td>"
            f"<td>{escape(str(cible.get('libelle', '')))}</td>"
            f"<td>{escape(str(cible.get('date', '')))}</td>"
            f"<td>{cellule_tableau(cible.get('soldes'))}</td>"
            "</tr>"
        )
    corps = "\n".join(lignes) if lignes else "<tr><td colspan=\"4\">Aucune date cible.</td></tr>"
    return f"""
    <section class="carte">
      <h2>Soldes aux dates cibles</h2>
      <table>
        <thead>
          <tr><th>Identifiant</th><th>Libellé</th><th>Date</th><th>Soldes</th></tr>
        </thead>
        <tbody>{corps}</tbody>
      </table>
    </section>
    """


def details_alerte(alerte: dict[str, Any]) -> str:
    details = {cle: valeur for cle, valeur in alerte.items() if cle not in {"type", "severite"}}
    return serialiser_objet(details)


def liste_alertes(alertes: list[Any]) -> str:
    elements = []
    for alerte in alertes:
        if not isinstance(alerte, dict):
            continue
        severite = str(alerte.get("severite", "information"))
        elements.append(
            f"<li class=\"alerte alerte-{escape(severite)}\">"
            f"<strong>{escape(str(alerte.get('type', 'alerte')))}</strong>"
            f" <span class=\"badge\">{escape(severite)}</span>"
            f"<pre>{details_alerte(alerte)}</pre>"
            "</li>"
        )
    contenu = "\n".join(elements) if elements else "<li>Aucune alerte globale.</li>"
    return f"""
    <section class="carte">
      <h2>Alertes globales</h2>
      <ul class="liste-alertes">{contenu}</ul>
    </section>
    """


def demi_journee_a_consommation_non_couverte(demi_journee: dict[str, Any]) -> bool:
    for detail in demi_journee.get("consommations_detaillees", []):
        if isinstance(detail, dict) and float(detail.get("quantite_non_couverte") or 0.0) > 0:
            return True
    return False


def classes_demi_journee(demi_journee: dict[str, Any]) -> str:
    classes = ["case-demi-journee"]
    if demi_journee.get("consommations") or demi_journee.get("consommations_detaillees"):
        classes.append("case-consommee")
    if demi_journee_a_consommation_non_couverte(demi_journee):
        classes.append("case-non-couverte")
    if demi_journee.get("alertes"):
        classes.append("case-alerte")
    return " ".join(classes)


def generer_frise(demi_journees: list[Any]) -> str:
    cases = []
    for demi_journee in demi_journees:
        if not isinstance(demi_journee, dict):
            continue
        titre = f"{demi_journee.get('date', '')} {demi_journee.get('portion', '')}"
        contenu = "M" if demi_journee.get("portion") == "matin" else "A"
        cases.append(
            f"<span class=\"{classes_demi_journee(demi_journee)}\" "
            f"title=\"{escape(titre)}\">{escape(contenu)}</span>"
        )
    contenu_frise = "\n".join(cases) if cases else "<p>Aucune demi-journée.</p>"
    return f"""
    <section class="carte frise">
      <h2>Frise 1D des demi-journées</h2>
      <div class="legende">
        <span><i class="case-demi-journee"></i> sans consommation</span>
        <span><i class="case-demi-journee case-consommee"></i> consommation appliquée</span>
        <span><i class="case-demi-journee case-non-couverte"></i> quantité non couverte</span>
        <span><i class="case-demi-journee case-alerte"></i> alerte</span>
      </div>
      <div class="rail-frise">{contenu_frise}</div>
    </section>
    """


def demi_journees_utiles(demi_journees: list[Any]) -> list[dict[str, Any]]:
    utiles = []
    for demi_journee in demi_journees:
        if not isinstance(demi_journee, dict):
            continue
        if demi_journee.get("consommations") or demi_journee.get("consommations_detaillees") or demi_journee.get("alertes"):
            utiles.append(demi_journee)
    return utiles


def bloc_details_demi_journees(demi_journees: list[Any]) -> str:
    blocs = []
    for demi_journee in demi_journees_utiles(demi_journees):
        titre = f"{demi_journee.get('date', '')} - {demi_journee.get('portion', '')}"
        blocs.append(
            "<article class=\"detail-demi-journee\">"
            f"<h3>{escape(titre)}</h3>"
            "<dl>"
            f"<dt>Événements</dt><dd><pre>{serialiser_objet(demi_journee.get('evenements', []))}</pre></dd>"
            f"<dt>Consommations agrégées</dt><dd><pre>{serialiser_objet(demi_journee.get('consommations', {}))}</pre></dd>"
            f"<dt>Consommations détaillées</dt><dd><pre>{serialiser_objet(demi_journee.get('consommations_detaillees', []))}</pre></dd>"
            f"<dt>Soldes avant</dt><dd><pre>{serialiser_objet(demi_journee.get('soldes_avant', {}))}</pre></dd>"
            f"<dt>Soldes après</dt><dd><pre>{serialiser_objet(demi_journee.get('soldes_apres', {}))}</pre></dd>"
            f"<dt>Alertes</dt><dd><pre>{serialiser_objet(demi_journee.get('alertes', []))}</pre></dd>"
            "</dl>"
            "</article>"
        )
    contenu = "\n".join(blocs) if blocs else "<p>Aucune demi-journée consommée ou alertée.</p>"
    return f"""
    <section class="carte">
      <h2>Détails des demi-journées utiles</h2>
      {contenu}
    </section>
    """


def feuille_style() -> str:
    return """
    :root {
      --fond: #f5efe3;
      --encre: #1f2a24;
      --muted: #657168;
      --carte: #fffaf0;
      --trait: #d8c9ae;
      --accent: #146b5f;
      --accent-fort: #0d4a44;
      --alerte: #b13b2e;
      --confirmation: #9b6b00;
      --info: #35648f;
      --ombre: 0 18px 40px rgba(41, 31, 19, 0.14);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      color: var(--encre);
      background:
        radial-gradient(circle at top left, rgba(20, 107, 95, 0.18), transparent 32rem),
        linear-gradient(135deg, #f8f1e6 0%, #efe1c8 100%);
      font-family: Georgia, "Times New Roman", serif;
      line-height: 1.45;
    }

    main {
      max-width: 1180px;
      margin: 0 auto;
      padding: 32px 18px 56px;
    }

    .hero {
      padding: 32px;
      border: 1px solid var(--trait);
      border-radius: 28px;
      background: rgba(255, 250, 240, 0.82);
      box-shadow: var(--ombre);
    }

    h1 {
      margin: 0 0 10px;
      font-size: clamp(2rem, 5vw, 4.8rem);
      line-height: 0.95;
      letter-spacing: -0.05em;
    }

    h2 {
      margin: 0 0 16px;
      font-size: 1.3rem;
      color: var(--accent-fort);
    }

    h3 { margin: 0 0 10px; }

    .grille {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 18px;
      margin-top: 18px;
    }

    .carte {
      margin-top: 18px;
      padding: 22px;
      border: 1px solid var(--trait);
      border-radius: 22px;
      background: rgba(255, 250, 240, 0.9);
      box-shadow: 0 10px 26px rgba(41, 31, 19, 0.08);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      overflow: hidden;
      border-radius: 14px;
    }

    th, td {
      padding: 10px 12px;
      border-bottom: 1px solid var(--trait);
      text-align: left;
      vertical-align: top;
    }

    th {
      width: 34%;
      color: var(--accent-fort);
      background: rgba(20, 107, 95, 0.08);
    }

    pre {
      margin: 0;
      white-space: pre-wrap;
      font-family: "Cascadia Mono", Consolas, monospace;
      font-size: 0.86rem;
    }

    .liste-alertes {
      padding: 0;
      list-style: none;
    }

    .alerte {
      margin: 10px 0;
      padding: 14px;
      border-left: 6px solid var(--info);
      background: rgba(53, 100, 143, 0.08);
      border-radius: 14px;
    }

    .alerte-confirmation { border-left-color: var(--confirmation); background: rgba(155, 107, 0, 0.1); }
    .alerte-bloquant { border-left-color: var(--alerte); background: rgba(177, 59, 46, 0.1); }

    .badge {
      display: inline-block;
      margin-left: 8px;
      padding: 2px 8px;
      border-radius: 999px;
      background: var(--encre);
      color: white;
      font-size: 0.8rem;
    }

    .legende {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 14px;
      color: var(--muted);
      font-size: 0.92rem;
    }

    .legende span {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .rail-frise {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      padding: 16px;
      border-radius: 18px;
      background: #efe4d0;
    }

    .case-demi-journee {
      display: inline-flex;
      width: 22px;
      height: 22px;
      align-items: center;
      justify-content: center;
      border: 1px solid #b9aa8f;
      border-radius: 7px;
      background: #fffaf0;
      color: var(--muted);
      font-size: 0.7rem;
      font-style: normal;
    }

    .case-consommee {
      background: var(--accent);
      border-color: var(--accent-fort);
      color: white;
    }

    .case-non-couverte {
      background: repeating-linear-gradient(135deg, #b13b2e 0 5px, #f2c2b8 5px 10px);
      color: white;
    }

    .case-alerte {
      box-shadow: 0 0 0 3px rgba(177, 59, 46, 0.32);
    }

    .detail-demi-journee {
      margin-top: 14px;
      padding: 16px;
      border: 1px solid var(--trait);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.42);
    }

    dl {
      display: grid;
      grid-template-columns: minmax(130px, 220px) 1fr;
      gap: 10px 16px;
      margin: 0;
    }

    dt {
      color: var(--accent-fort);
      font-weight: 700;
    }

    dd { margin: 0; min-width: 0; }

    .note {
      color: var(--muted);
      max-width: 760px;
    }

    @media (max-width: 720px) {
      .hero { padding: 22px; }
      dl { grid-template-columns: 1fr; }
      th, td { display: block; width: 100%; }
    }
    """


def generer_html(projection: dict[str, Any]) -> str:
    periode = projection.get("periode", {}) if isinstance(projection.get("periode"), dict) else {}
    resume = projection.get("resume", {}) if isinstance(projection.get("resume"), dict) else {}
    demi_journees = projection.get("demi_journees", [])
    if not isinstance(demi_journees, list):
        demi_journees = []
    alertes = projection.get("alertes", [])
    if not isinstance(alertes, list):
        alertes = []

    resume_affiche = {
        "période": f"{periode.get('debut', '')} -> {periode.get('fin', '')}",
        "nombre_demi_journees": resume.get("nombre_demi_journees", len(demi_journees)),
        "nombre_evenements_sources": resume.get("nombre_evenements_sources", len(projection.get("evenements_sources", []))),
        "nombre_alertes": resume.get("nombre_alertes", len(alertes)),
    }

    soldes_initiaux = projection.get("soldes_initiaux", {})
    if not isinstance(soldes_initiaux, dict):
        soldes_initiaux = {}

    dates_cibles = projection.get("soldes_aux_dates_cibles", [])
    if not isinstance(dates_cibles, list):
        dates_cibles = []

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Vue locale de projection Chronotime</title>
  <style>{feuille_style()}</style>
</head>
<body>
  <main>
    <header class="hero">
      <h1>Vue locale de projection Chronotime</h1>
      <p class="note">
        Visualisation statique en lecture seule d’une projection <code>projection.demi_journees</code>.
        La projection reste une donnée dérivée : elle ne remplace pas le modèle événementiel source et ne modifie pas Chronotime.
      </p>
    </header>
    <div class="grille">
      {tableau_cle_valeur("Résumé global", resume_affiche)}
      {tableau_soldes("Soldes initiaux", soldes_initiaux)}
    </div>
    {tableau_dates_cibles(dates_cibles)}
    {liste_alertes(alertes)}
    {generer_frise(demi_journees)}
    {bloc_details_demi_journees(demi_journees)}
    <section class="carte">
      <h2>Limites de cette vue</h2>
      <p>
        Cette page ne valide pas entièrement les jours fériés, la parentalité, les chevauchements d’agenda,
        les expirations fines ou l’optimisation. Elle sert seulement à vérifier la lisibilité de la projection.
      </p>
    </section>
  </main>
</body>
</html>
"""


def ecrire_html(contenu: str, chemin_sortie: Path) -> None:
    try:
        chemin_sortie.parent.mkdir(parents=True, exist_ok=True)
        chemin_sortie.write_text(contenu, encoding="utf-8")
    except OSError as erreur:
        raise SystemExit(f"Impossible d'écrire la page HTML : {chemin_sortie}") from erreur


def analyser_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(
        description="Générer une page HTML locale en lecture seule depuis une projection demi-journalière.",
    )
    analyseur.add_argument("--projection", type=Path, required=True, help="Chemin du fichier projection.demi_journees.")
    analyseur.add_argument("--sortie", type=Path, required=True, help="Chemin du fichier HTML à générer.")
    return analyseur.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = analyser_arguments(argv)
    try:
        projection = charger_projection(arguments.projection)
    except ValueError as erreur:
        raise SystemExit(str(erreur)) from erreur
    ecrire_html(generer_html(projection), arguments.sortie)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
