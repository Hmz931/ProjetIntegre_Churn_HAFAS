"""
Étape CLEAN : nettoyage et imputation des valeurs manquantes.

Chaque fonction documente la décision métier prise (suppression de lignes, imputation par
le mode/la médiane, ou règle conditionnelle) et pourquoi — voir le notebook 01_etl/notebooks
pour le détail de l'investigation qui a mené à chaque choix (taux de missing, corrélation
avec d'autres colonnes, etc.). Ce module applique les décisions déjà validées, il ne les
re-découvre pas : le diagnostic exploratoire reste dans 01_exploration.ipynb.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from . import config

logger = logging.getLogger(__name__)


def decode_cyymmdd(series: pd.Series) -> pd.Series:
    """Décode le format hérité CYYMMDD (7 chiffres, le 1er chiffre code le siècle 2000),
    en mélange avec le format standard YYYYMMDD (8 chiffres) déjà correct.

    Utilisé pour STARTDATE et MATURITYDATE, qui partagent ce même format hérité dans le
    fichier source — vérifié sur les données réelles : 7 chiffres pour ~74% des valeurs,
    8 chiffres pour le reste. Un parsing YYYYMMDD naïf sur les valeurs à 7 chiffres produit
    des dates absurdes (ex. année 1131 au lieu de 2011) — bug réel détecté en testant une
    version précédente de ce module contre les vraies données.
    """
    texte = series.astype(str).str.split(".").str[0]
    condition_7_chiffres = (texte.str.len() == 7) & (texte.str.startswith("1"))
    harmonise = np.where(condition_7_chiffres, "20" + texte.str[1:], texte)
    return pd.to_datetime(harmonise, format="%Y%m%d", errors="coerce")


def remove_strict_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Supprime les lignes parfaitement identiques sur toutes les colonnes.

    Les doublons partiels sur (CUSTOMER_NO, ACCOUNT_NO) sont volontairement laissés
    intacts : avec le grain événement retenu pour la table de faits, ces lignes
    deviennent légitimement plusieurs événements distincts pour le même compte
    (probablement des extractions à dates différentes du système source).
    """
    before = len(df)
    df = df.drop_duplicates()
    logger.info("Doublons stricts supprimés : %s (%s -> %s lignes)",
                f"{before - len(df):,}", f"{before:,}", f"{len(df):,}")
    return df


def clean_qualitative_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Applique les règles d'imputation pour toutes les colonnes qualitatives.

    Chaque règle est commentée individuellement car le choix n'est jamais générique
    ("toujours le mode") : il dépend de ce que signifie une valeur manquante pour
    cette colonne précise (nullité structurelle, vraie donnée inconnue, ou règle
    métier conditionnelle sur une autre colonne).
    """
    df = df.copy()

    # ACCOUNT_NO : sans numéro de compte, la ligne ne peut être rattachée à aucune
    # dimension ni à la table de faits (dont le grain est le compte) -> suppression.
    before = len(df)
    df = df.dropna(subset=["ACCOUNT_NO"])
    logger.info("[ACCOUNT_NO] Lignes sans compte supprimées : %s -> %s restantes",
                f"{before - len(df):,}", f"{len(df):,}")

    # MARITAL_STATUS : règle conditionnelle sur NATURE_CLIENT. Une personne morale
    # (PM) n'a pas de statut marital par nature (non applicable), ce qui est
    # différent d'une personne physique (PPH) dont le statut est simplement inconnu.
    # Imputer les deux par le mode global gonflerait artificiellement une catégorie.
    df.loc[(df["NATURE_CLIENT"] == "PM") & (df["MARITAL_STATUS"].isna()),
           "MARITAL_STATUS"] = "NON_APPLICABLE"
    df.loc[(df["NATURE_CLIENT"] == "PPH") & (df["MARITAL_STATUS"].isna()),
           "MARITAL_STATUS"] = "INCONNU"
    df["MARITAL_STATUS"] = df["MARITAL_STATUS"].fillna("INCONNU")  # sécurité résiduelle

    # SCORE_KYC, CURRENCY, NATIONALITY, RESIDENCE, NATURE_CLIENT : taux de nuls
    # faible avec une catégorie largement dominante -> imputation par le mode,
    # biais minime car elle ne fait que renforcer une tendance déjà majoritaire.
    for col in ["SCORE_KYC", "CURRENCY", "NATIONALITY", "RESIDENCE", "NATURE_CLIENT"]:
        mode_val = df[col].mode()[0]
        n_missing = df[col].isna().sum()
        df[col] = df[col].fillna(mode_val)
        logger.info("[%s] %s valeurs imputées par le mode '%s'", col, f"{n_missing:,}", mode_val)

    # COMPLETED_FILE : règle métier explicite, pas un mode statistique. Une valeur
    # manquante signifie ici que le dossier n'a pas été complété.
    df["COMPLETED_FILE"] = df["COMPLETED_FILE"].fillna("NO")

    # Colonnes produit : nullité structurelle confirmée en EDA (87,9% des lignes
    # ont soit toutes ces colonnes vides, soit toutes renseignées) -> catégorie
    # explicite plutôt que suppression (les colonnes client/compte restent valides).
    df["ACCOUNTNATURE"] = df["ACCOUNTNATURE"].fillna("SANS_PRODUIT")
    df["PRODUCT"] = df["PRODUCT"].fillna("SANS_PRODUIT")
    df["PRODUCT_GROUP"] = df["PRODUCT_GROUP"].fillna("SANS_PRODUIT")
    df["PRODUCT_LINE"] = df["PRODUCT_LINE"].fillna("SANS_LIGNE")
    df["PRODUCT_STATUS"] = df["PRODUCT_STATUS"].fillna("NON_APPLICABLE")

    # CLOSURE_REASON : règle conditionnelle sur ACCOUNT_STATUS. Un compte actif n'a
    # logiquement pas de motif de clôture ; un compte fermé sans motif documenté est
    # un cas différent (potentiellement un signal en soi : délai administratif...).
    df.loc[df["ACCOUNT_STATUS"] == "Active", "CLOSURE_REASON"] = (
        df.loc[df["ACCOUNT_STATUS"] == "Active", "CLOSURE_REASON"].fillna("NON_FERME")
    )
    df.loc[df["ACCOUNT_STATUS"] == "Closed", "CLOSURE_REASON"] = (
        df.loc[df["ACCOUNT_STATUS"] == "Closed", "CLOSURE_REASON"].fillna("INCONNUE")
    )

    # INDUSTRY : traité comme catégorie malgré son type numérique apparent. Les nuls
    # deviennent 'INCONNU', distinct du code 9000 ("Other" au sens propre, vérifié
    # dans dim_INDUSTRY.xlsx) -> ne jamais fusionner les deux dans une analyse.
    df["INDUSTRY"] = df["INDUSTRY"].astype(str)
    df["INDUSTRY"] = df["INDUSTRY"].replace("nan", "INCONNU")

    # ACCOUNT_CATEGORY, ACCOUNT_TYPE_DESC : même taux de nuls que les colonnes
    # produit (nullité structurelle liée à l'absence de compte produit) -> mode.
    mode_category = df["ACCOUNT_CATEGORY"].mode()[0]
    mode_desc = df["ACCOUNT_TYPE_DESC"].mode()[0]
    df["ACCOUNT_CATEGORY"] = df["ACCOUNT_CATEGORY"].fillna(mode_category)
    df["ACCOUNT_TYPE_DESC"] = df["ACCOUNT_TYPE_DESC"].fillna(mode_desc)

    # ACCOUNT_STATUS : variable source du churn. Imputer une cible manquante par une
    # valeur fixe est une décision sensible — voir avertissement dans le README.
    # Choix retenu : 'Active' par défaut (cohérent avec l'absence de ACCT_CLOSE_DATE
    # pour ces lignes), À VALIDER EXPLICITEMENT AVEC L'ÉQUIPE avant tout entraînement
    # ML — l'alternative plus prudente est d'exclure ces lignes du jeu d'entraînement.
    n_missing_status = df["ACCOUNT_STATUS"].isna().sum()
    n_with_close_date = df.loc[df["ACCOUNT_STATUS"].isna(), "ACCT_CLOSE_DATE"].notna().sum()
    if n_with_close_date > 0:
        logger.warning(
            "%s lignes ont un ACCT_CLOSE_DATE renseigné malgré un ACCOUNT_STATUS "
            "manquant — incohérence à investiguer avant l'imputation.", n_with_close_date
        )
    df["ACCOUNT_STATUS"] = df["ACCOUNT_STATUS"].fillna("Active")
    logger.info("[ACCOUNT_STATUS] %s valeurs imputées par 'Active' (À VALIDER AVEC L'ÉQUIPE)",
                f"{n_missing_status:,}")

    return df


def clean_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Convertit toutes les colonnes de date et applique les imputations validées.

    Deux familles de format coexistent dans le fichier source :
    - YYYYMMDD standard (8 chiffres) pour CUST_OPENING_DATE, LAST_REVIEW_DATE,
      NEXT__REVIEW_DATE, ACCT_OPENING_DATE, ACCT_CLOSE_DATE.
    - CYYMMDD hérité (7 ou 8 chiffres mélangés) pour STARTDATE et MATURITYDATE —
      voir decode_cyymmdd() ci-dessus pour le détail de cet encodage.
    """
    df = df.copy()

    date_cols_standard = [
        "CUST_OPENING_DATE", "LAST_REVIEW_DATE", "NEXT__REVIEW_DATE",
        "ACCT_OPENING_DATE", "ACCT_CLOSE_DATE",
    ]
    for col in date_cols_standard:
        df[col] = pd.to_datetime(
            df[col].dropna().astype("int64").astype(str).reindex(df.index),
            format="%Y%m%d", errors="coerce",
        )

    # DATE_OF_BIRTH ne contient que l'année (anonymisation, cf. data/anonymize.py).
    df["DATE_OF_BIRTH"] = pd.to_numeric(df["DATE_OF_BIRTH"], errors="coerce")
    df["DATE_OF_BIRTH"] = pd.to_datetime(
        df["DATE_OF_BIRTH"].dropna().astype("int64").astype(str).reindex(df.index),
        format="%Y", errors="coerce",
    )

    # STARTDATE et MATURITYDATE : format hérité, voir decode_cyymmdd().
    df["STARTDATE"] = decode_cyymmdd(df["STARTDATE"])
    df["MATURITYDATE"] = decode_cyymmdd(df["MATURITYDATE"])

    # --- Imputations ---
    # CUST_OPENING_DATE : distribution quasi symétrique -> médiane (robuste aux
    # extrêmes résiduels, équivalente à la moyenne ici).
    df["CUST_OPENING_DATE"] = df["CUST_OPENING_DATE"].fillna(df["CUST_OPENING_DATE"].median())

    # DATE_OF_BIRTH : on neutralise d'abord les valeurs aberrantes (âge > 100 ans,
    # cf. EDA) en NaT AVANT d'imputer par la médiane — sinon la médiane elle-même
    # serait calculée sur des données polluées par ces aberrations.
    aberrantes = df["DATE_OF_BIRTH"].dt.year < config.MIN_PLAUSIBLE_BIRTH_YEAR
    df.loc[aberrantes, "DATE_OF_BIRTH"] = pd.NaT
    df["DATE_OF_BIRTH"] = df["DATE_OF_BIRTH"].fillna(df["DATE_OF_BIRTH"].median())

    # LAST_REVIEW_DATE, NEXT__REVIEW_DATE : chacune imputée par sa propre médiane
    # (pas l'une par l'autre, pour ne pas mélanger deux distributions différentes).
    df["LAST_REVIEW_DATE"] = df["LAST_REVIEW_DATE"].fillna(df["LAST_REVIEW_DATE"].median())
    df["NEXT__REVIEW_DATE"] = df["NEXT__REVIEW_DATE"].fillna(df["NEXT__REVIEW_DATE"].median())

    # STARTDATE, ACCT_OPENING_DATE, ACCT_CLOSE_DATE : nullité structurelle vérifiée
    # (corrélation à 100% avec l'absence de produit / le statut Active) -> laissées
    # en l'état, voir TOLERATED_MISSING_COLUMNS dans config.py.

    return df


def clean_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie les colonnes numériques restantes (montants, taux, solde, salaire)."""
    df = df.copy()

    df["ACCT_BALANCE"] = pd.to_numeric(df["ACCT_BALANCE"], errors="coerce")
    df["SALARY"] = pd.to_numeric(df["SALARY"], errors="coerce")
    # NaN volontairement conservés pour ces deux colonnes : asymétrie (skew) trop
    # forte pour qu'une moyenne ou une médiane soit représentative — voir
    # TOLERATED_MISSING_COLUMNS. Le ML devra gérer ces NaN explicitement.

    # AMOUNT : montant structurellement nul hors crédit/dépôt (pas une approximation,
    # une vraie absence de montant pour ces lignes).
    filtre_sans_produit = ~df["PRODUCT_GROUP"].isin(["LENDING", "DEPOSITS"])
    df.loc[filtre_sans_produit, "AMOUNT"] = df.loc[filtre_sans_produit, "AMOUNT"].fillna(0)

    # FIXEDRATE : taux nul pour les comptes courants (ACCOUNTS), puis 0 par défaut
    # pour les nuls résiduels (clients sans produit ou produits non rémunérés).
    df.loc[df["PRODUCT_GROUP"] == "ACCOUNTS", "FIXEDRATE"] = (
        df.loc[df["PRODUCT_GROUP"] == "ACCOUNTS", "FIXEDRATE"].fillna(0)
    )
    df["FIXEDRATE"] = df["FIXEDRATE"].fillna(0)

    return df


def verify_no_unplanned_missing(df: pd.DataFrame) -> dict:
    """Vérifie qu'aucune colonne, en dehors de la liste blanche documentée, ne
    contient encore de valeurs manquantes après nettoyage.

    Retourne un dictionnaire de diagnostic plutôt que de lever une exception : un
    pipeline ETL ne doit pas planter silencieusement sur un avertissement de
    qualité de données, mais l'appelant (pipeline.py) doit pouvoir réagir.
    """
    missing = df.isna().sum()
    unplanned = missing.drop(labels=config.TOLERATED_MISSING_COLUMNS, errors="ignore")
    unplanned = unplanned[unplanned > 0]

    if len(unplanned) == 0:
        logger.info("BILAN qualité : aucune valeur manquante non planifiée.")
    else:
        logger.warning("BILAN qualité : valeurs manquantes non planifiées détectées :\n%s",
                        unplanned.to_string())

    return {"ok": len(unplanned) == 0, "unplanned_missing": unplanned}


def clean_all(df: pd.DataFrame) -> pd.DataFrame:
    """Point d'entrée unique de l'étape Clean : enchaîne toutes les transformations
    dans l'ordre validé (doublons -> qualitatif -> dates -> numérique -> vérification).
    """
    df = remove_strict_duplicates(df)
    df = clean_qualitative_columns(df)
    df = clean_dates(df)
    df = clean_numeric_columns(df)
    verify_no_unplanned_missing(df)
    return df
