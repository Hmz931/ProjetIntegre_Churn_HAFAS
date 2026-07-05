"""
Étape FACT : construction de la table de faits FACT_ACCOUNT_EVENT.

Grain retenu (validé en équipe) : 1 ligne par événement compte/produit du fichier
source — pas de réduction par compte ni par client. Voir README.md du dossier
01_etl pour la discussion complète des grains alternatifs envisagés.
"""
from __future__ import annotations

import logging

import pandas as pd

from . import config

logger = logging.getLogger(__name__)


def compute_churn_by_account(df: pd.DataFrame) -> pd.Series:
    """Calcule le flag churn une seule fois par compte, à partir de ACCOUNT_STATUS.

    ⚠️ Important : `churn` est un attribut de COMPTE, pas d'événement. Il est calculé
    ici une seule fois, puis propagé (broadcast) sur toutes les lignes-événements de
    ce compte dans build_fact_account_event() — jamais recalculé indépendamment
    ligne par ligne, ce qui garantirait une valeur instable si ACCOUNT_STATUS variait
    par erreur entre deux lignes d'un même compte.

    La stabilité de ACCOUNT_STATUS par ACCOUNT_NO est vérifiée explicitement : si elle
    ne tient pas (incohérence dans les données), un avertissement est levé plutôt que
    de propager silencieusement une valeur peut-être incorrecte.
    """
    n_inconsistent = (df.groupby("ACCOUNT_NO")["ACCOUNT_STATUS"].nunique() > 1).sum()
    if n_inconsistent > 0:
        logger.warning(
            "%s compte(s) ont un ACCOUNT_STATUS incohérent entre leurs différentes "
            "lignes-événements — le churn calculé peut être instable pour ces comptes.",
            n_inconsistent,
        )
    else:
        logger.info("ACCOUNT_STATUS vérifié stable à 100%% par ACCOUNT_NO.")

    churn_by_account = (
        df.drop_duplicates(subset="ACCOUNT_NO")
          .set_index("ACCOUNT_NO")["ACCOUNT_STATUS"]
          .eq("Closed")
          .astype(int)
          .rename("churn")
    )
    logger.info("Taux de churn (niveau compte) : %.1f%%", churn_by_account.mean() * 100)
    return churn_by_account


def build_fact_account_event(
    df: pd.DataFrame,
    dim_client: pd.DataFrame,
    dim_account: pd.DataFrame,
    dim_branch: pd.DataFrame,
    dim_product: pd.DataFrame,
    dim_closure: pd.DataFrame,
    dim_date: pd.DataFrame,
) -> pd.DataFrame:
    """Construit FACT_ACCOUNT_EVENT au grain événement (1 ligne par ligne source).

    DIM_PRODUCT étant construite au même grain que df après nettoyage (voir
    dimensions.build_dim_product), la jointure se fait par alignement positionnel
    direct plutôt que par valeur — vérifié par une assertion de longueur égale,
    qui échouerait bruyamment si ce grain venait à changer plus tard.
    """
    churn_by_account = compute_churn_by_account(df)

    fact = df.copy()
    fact = fact.merge(dim_client[["client_key", "CUSTOMER_NO"]], on="CUSTOMER_NO", how="left")
    fact = fact.merge(dim_account[["account_key", "ACCOUNT_NO"]], on="ACCOUNT_NO", how="left")
    fact = fact.merge(dim_branch[["branch_key", "BRANCH"]], on="BRANCH", how="left")
    fact = fact.merge(
        dim_closure[["closure_key", "closure_reason"]],
        left_on="CLOSURE_REASON", right_on="closure_reason", how="left",
    )

    assert len(fact) == len(dim_product), (
        "fact et dim_product n'ont pas la même longueur — l'alignement positionnel "
        "n'est plus valide (le grain de DIM_PRODUCT a probablement changé)."
    )
    fact["product_key"] = dim_product["product_key"].values

    date_to_key = dim_date.set_index("full_date")["date_key"]
    # date_key est maintenant une clé textuelle (ex. "DATE_00001"), plus un entier :
    # plus besoin de forcer un type numérique nullable ici. Les comptes sans
    # ACCT_OPENING_DATE (nullité structurelle, cf. 01_etl/README.md) obtiennent
    # simplement NaN/None via .map(), ce que pandas gère nativement pour du texte.
    fact["date_key"] = fact["ACCT_OPENING_DATE"].dt.normalize().map(date_to_key)

    for fk_col, source_col in [
        ("client_key", "CUSTOMER_NO"), ("account_key", "ACCOUNT_NO"),
        ("branch_key", "BRANCH"), ("closure_key", "CLOSURE_REASON"),
    ]:
        orphans = fact[fk_col].isna() & fact[source_col].notna()
        if orphans.sum() > 0:
            logger.warning("%s ligne(s) avec %s orphelin — à investiguer.", orphans.sum(), fk_col)

    # ⚠️ date_key n'est PAS vérifiée par la boucle ci-dessus : contrairement aux
    # autres clés étrangères, une valeur nulle ici n'est jamais un orphelin
    # (un échec de jointure imprévu), mais un cas structurel prévu — voir
    # ACCT_OPENING_DATE dans clean.py. On la contrôle donc séparément, avec une
    # règle différente : le nombre de date_key manquants doit être EXACTEMENT
    # égal au nombre d'ACCT_OPENING_DATE manquants en amont, ni plus ni moins.
    # Si ce n'est pas le cas, ce n'est plus de la nullité structurelle attendue
    # mais un vrai échec de jointure (ex. une date valide absente de dim_date,
    # ou un problème de normalisation d'heure) qu'il faut corriger.
    n_date_key_null = fact["date_key"].isna().sum()
    n_opening_date_null = fact["ACCT_OPENING_DATE"].isna().sum()
    if n_date_key_null != n_opening_date_null:
        logger.error(
            "INCOHÉRENCE : %s date_key manquant(s) dans FACT_ACCOUNT_EVENT, mais "
            "%s ACCT_OPENING_DATE manquant(e)s en amont. Ces deux nombres devraient "
            "être identiques (nullité structurelle uniquement). L'écart de %s "
            "ligne(s) signale un échec de jointure réel avec dim_date à investiguer "
            "(date présente mais absente de la plage dim_date, ou problème de "
            "normalisation d'heure).",
            n_date_key_null, n_opening_date_null, abs(n_date_key_null - n_opening_date_null),
        )
    else:
        logger.info(
            "date_key : %s ligne(s) manquante(s) (%.1f%% de la table de faits), "
            "vérifié strictement égal aux ACCT_OPENING_DATE manquantes en amont — "
            "nullité 100%% structurelle, aucun échec de jointure.",
            f"{n_date_key_null:,}", n_date_key_null / len(fact) * 100,
        )

    fact["churn"] = fact["ACCOUNT_NO"].map(churn_by_account)

    end_date_acct = fact["ACCT_CLOSE_DATE"].fillna(config.REFERENCE_DATE)
    fact["acct_tenure_days"] = (end_date_acct - fact["ACCT_OPENING_DATE"]).dt.days
    fact["acct_tenure_days"] = fact["acct_tenure_days"].where(fact["acct_tenure_days"] >= 0)

    fact["client_tenure_days"] = (config.REFERENCE_DATE - fact["CUST_OPENING_DATE"]).dt.days

    nb_accounts_map = df.groupby("CUSTOMER_NO")["ACCOUNT_NO"].nunique()
    fact["nb_accounts"] = fact["CUSTOMER_NO"].map(nb_accounts_map)

    fact_cols = [
        "client_key", "account_key", "product_key", "branch_key", "date_key", "closure_key",
        "ACCT_BALANCE", "SALARY", "AMOUNT", "FIXEDRATE",
        "acct_tenure_days", "client_tenure_days", "nb_accounts", "churn",
    ]
    fact_account_event = fact[fact_cols].rename(columns={
        "ACCT_BALANCE": "acct_balance", "SALARY": "salary",
        "AMOUNT": "amount", "FIXEDRATE": "fixedrate",
    })

    n_churn_null = fact_account_event["churn"].isna().sum()
    if n_churn_null > 0:
        logger.warning("%s ligne(s) sans churn assigné — à investiguer.", n_churn_null)

    logger.info("FACT_ACCOUNT_EVENT construite : %s événements", f"{len(fact_account_event):,}")
    logger.info("Taux de churn (pondéré par événement) : %.1f%% (rappel, niveau compte : %.1f%%)",
                fact_account_event["churn"].mean() * 100, churn_by_account.mean() * 100)

    return fact_account_event
