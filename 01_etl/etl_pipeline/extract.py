"""
Étape EXTRACT : lecture des fichiers sources.

Sépare volontairement la lecture (ce module) de la transformation (clean.py) : si demain
le format source change (autre CSV, base de données, API), seul ce module a besoin d'être
modifié — le reste du pipeline n'a aucune connaissance du format d'origine.
"""
from __future__ import annotations

import logging

import pandas as pd

from . import config

logger = logging.getLogger(__name__)


def extract_raw_data() -> pd.DataFrame:
    """Lit le fichier principal data_churn.txt tel quel, sans transformation.

    Returns
    -------
    DataFrame brut, types inférés par pandas (dates encore en YYYYMMDD numérique,
    valeurs manquantes encore présentes).
    """
    if not config.RAW_DATA_FILE.exists():
        raise FileNotFoundError(
            f"Fichier de données introuvable : {config.RAW_DATA_FILE}\n"
            f"Vérifiez que data_churn.txt a bien été placé dans le dossier data/ "
            f"(il n'est volontairement pas versionné sur GitHub, voir .gitignore)."
        )

    df = pd.read_csv(config.RAW_DATA_FILE, sep=",")
    logger.info("Extraction terminée : %s lignes, %s colonnes", f"{len(df):,}", df.shape[1])
    return df


def extract_dimension_tables() -> dict[str, pd.DataFrame]:
    """Lit les 8 fichiers dim_*.xlsx fournis par l'encadrant.

    Ces tables donnent le libellé métier associé aux codes du fichier principal
    (ex. INDUSTRY_CODE 9000 -> "Other"). Un fichier manquant ne fait pas échouer
    tout le pipeline : il est simplement absent du dictionnaire retourné, avec un
    avertissement explicite — préférable à un crash total si un seul référentiel
    optionnel n'est pas disponible sur la machine de l'utilisateur.
    """
    dimensions: dict[str, pd.DataFrame] = {}
    for name, path in config.DIM_FILES.items():
        if not path.exists():
            logger.warning("Dimension '%s' introuvable (%s) — ignorée.", name, path)
            continue
        try:
            dimensions[name] = pd.read_excel(path)
            logger.info(
                "Dimension '%s' chargée : %s lignes", name, f"{len(dimensions[name]):,}"
            )
        except Exception as exc:  # noqa: BLE001 — on veut continuer même en cas d'erreur
            logger.warning("Échec de lecture de la dimension '%s' : %s", name, exc)

    return dimensions


def extract_all() -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """Point d'entrée unique de l'étape Extract : fichier principal + dimensions."""
    df = extract_raw_data()
    dimensions = extract_dimension_tables()
    return df, dimensions
