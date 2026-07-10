"""
Configuration centralisée du pipeline ETL.

Toutes les constantes "magiques" (chemins, dates de référence, mappings métier) vivent ici,
plutôt que dispersées dans chaque module — un seul endroit à corriger si une valeur change.
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------
# Racine du projet = deux niveaux au-dessus de ce fichier (01_etl/etl_pipeline/config.py
# -> 01_etl/etl_pipeline -> 01_etl -> racine du projet).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

RAW_DATA_FILE = DATA_DIR / "data_churn.txt"

DIM_FILES = {
    "category_account": DATA_DIR / "dim_CATEGORY_ACCOUNT.xlsx",
    "currency": DATA_DIR / "dim_CURRENCY.xlsx",
    "closure_reason": DATA_DIR / "dim_Closure_reason.xlsx",
    "dao": DATA_DIR / "dim_DAO.xlsx",
    "industry": DATA_DIR / "dim_INDUSTRY.xlsx",
    "sector": DATA_DIR / "dim_SECTOR.xlsx",
    "target": DATA_DIR / "dim_TARGET.xlsx",
    "transaction": DATA_DIR / "dim_TRANSACTION.xlsx",
}

# ---------------------------------------------------------------------------
# Date de référence unique pour tous les calculs d'âge / d'ancienneté
# ---------------------------------------------------------------------------
# Centralisée ici pour éviter d'avoir plusieurs dates "aujourd'hui" différentes
# éparpillées dans le code (source de résultats incohérents entre modules).
REFERENCE_DATE = pd.Timestamp("2026-06-24")

# ---------------------------------------------------------------------------
# Connexion PostgreSQL — lue depuis l'environnement, jamais codée en clair
# ---------------------------------------------------------------------------
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "PIProject2")

CONNECTION_STRING = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    f"?client_encoding=utf8"
)

# ---------------------------------------------------------------------------
# Mappings métier
# ---------------------------------------------------------------------------
# Encodage ordinal du score KYC : l'ordre porte une information (H3 pire que H1),
# qu'un encodage one-hot perdrait pour un modèle de ML.
KYC_RISK_MAP = {"LR": 0, "MR": 1, "H1": 2, "H2": 3, "H3": 4}

# Encodage ordinal du risque de churn par ligne de produit, basé sur les taux de
# churn mesurés sur les données réelles (cf. 01_exploration.ipynb section 10) :
# ACCOUNTS 13.9% -> LENDING 59.4% -> DEPOSITS 96.2%.
PRODUCT_LINE_RISK_MAP = {
    "ACCOUNTS": 0,
    "SAFE.DEPOSIT.BOX": 1,
    "LENDING": 2,
    "DEPOSITS": 3,
}

# Bornes de plausibilité pour une année de naissance (cf. EDA : valeurs aberrantes
# comme 1190, 1373 détectées dans le fichier source).
MIN_PLAUSIBLE_BIRTH_YEAR = REFERENCE_DATE.year - 100
MAX_PLAUSIBLE_BIRTH_YEAR = REFERENCE_DATE.year

# Colonnes pour lesquelles des valeurs manquantes résiduelles sont des décisions
# métier validées (pas des oublis) — voir clean.py pour la justification détaillée
# de chacune.
TOLERATED_MISSING_COLUMNS = [
    "SALARY", "ACCT_BALANCE", "STARTDATE", "AMOUNT", "MATURITYDATE",
    "ACCT_OPENING_DATE", "ACCT_CLOSE_DATE",
]
