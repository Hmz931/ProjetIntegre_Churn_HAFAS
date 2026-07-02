"""
Package ETL — pipeline de préparation des données pour le projet de prédiction du churn.

Organisation du module (orchestration en étapes séparées, plutôt qu'un notebook monolithique) :

    config.py        Constantes partagées (chemins, date de référence, mappings métier)
    extract.py        Lecture des fichiers sources (data_churn.txt + dim_*.xlsx)
    clean.py          Nettoyage et imputation (valeurs manquantes, dates, doublons)
    dimensions.py     Construction des 6 tables de dimension du schéma en étoile
    fact.py           Construction de la table de faits FACT_ACCOUNT_EVENT
    load.py           Chargement vers PostgreSQL (SQLAlchemy), avec échec non bloquant
    pipeline.py       Orchestrateur : exécute extract -> clean -> dimensions -> fact -> load

Usage en script :
    python -m etl_pipeline.pipeline

Usage en notebook :
    from etl_pipeline.pipeline import run_pipeline
    resultats = run_pipeline()
    df_clean = resultats["df"]
    fact = resultats["fact_account_event"]
"""
