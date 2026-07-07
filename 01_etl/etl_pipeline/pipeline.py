"""
Orchestrateur du pipeline ETL.

Enchaîne les étapes dans l'ordre : EXTRACT -> CLEAN -> DIMENSIONS -> FACT -> LOAD.

Chaque étape vit dans son propre module (extract.py, clean.py, dimensions.py, fact.py,
load.py) avec une responsabilité unique — ce fichier ne fait qu'orchestrer l'appel dans
le bon ordre et transmettre les résultats d'une étape à la suivante. C'est ce découpage
qui permet de réutiliser chaque étape indépendamment (ex. dans un notebook, pour
inspecter le résultat intermédiaire d'une seule étape sans rejouer tout le pipeline).

Usage en script :
    python -m etl_pipeline.pipeline

Usage en notebook :
    from etl_pipeline.pipeline import run_pipeline
    resultats = run_pipeline()
    df_clean = resultats["df"]
    fact = resultats["fact_account_event"]
    dim_client = resultats["dimensions"]["dim_client"]
"""
from __future__ import annotations

import logging

from . import clean, dimensions, extract, fact, load

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_pipeline(load_to_db: bool = True) -> dict:
    """Exécute le pipeline ETL complet et retourne tous les résultats intermédiaires.

    Parameters
    ----------
    load_to_db : si False, n'exécute pas l'étape LOAD (utile pour itérer rapidement
        sur les étapes de nettoyage/modélisation sans dépendre d'une base disponible).

    Returns
    -------
    Dictionnaire avec les clés :
        "df"                 DataFrame nettoyé, grain événement (sortie de clean.py)
        "raw_dimensions"     dict des dim_*.xlsx bruts (sortie de extract.py)
        "dimensions"         dict des 6 dimensions construites (sortie de dimensions.py)
        "fact_account_event" table de faits (sortie de fact.py)
        "load_results"       dict {nom_table: succès booléen} si load_to_db=True, sinon None
    """
    logger.info("=" * 70)
    logger.info("DÉBUT DU PIPELINE ETL")
    logger.info("=" * 70)

    logger.info("--- ÉTAPE 1/5 : EXTRACT ---")
    df_raw, raw_dimensions = extract.extract_all()

    logger.info("--- ÉTAPE 2/5 : CLEAN ---")
    df_clean = clean.clean_all(df_raw)

    logger.info("--- ÉTAPE 3/5 : DIMENSIONS ---")
    dims = dimensions.build_all_dimensions(df_clean, raw_dimensions)

    logger.info("--- ÉTAPE 4/5 : FACT ---")
    fact_account_event = fact.build_fact_account_event(
        df_clean,
        dim_client=dims["dim_client"],
        dim_account=dims["dim_account"],
        dim_branch=dims["dim_branch"],
        dim_product=dims["dim_product"],
        dim_closure=dims["dim_closure"],
        dim_date=dims["dim_date"],
    )

    load_results = None
    if load_to_db:
        logger.info("--- ÉTAPE 5/5 : LOAD ---")
        load_results = load.load_all(dims, fact_account_event)
    else:
        logger.info("--- ÉTAPE 5/5 : LOAD (ignorée, load_to_db=False) ---")

    logger.info("=" * 70)
    logger.info("PIPELINE ETL TERMINÉ")
    logger.info("=" * 70)

    return {
        "df": df_clean,
        "raw_dimensions": raw_dimensions,
        "dimensions": dims,
        "fact_account_event": fact_account_event,
        "load_results": load_results,
    }


if __name__ == "__main__":
    run_pipeline()
