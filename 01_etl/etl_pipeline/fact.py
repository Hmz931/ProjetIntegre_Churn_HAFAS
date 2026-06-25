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
    # ⚠️ Bug réel trouvé en test (rapporté par un membre de l'équipe, chargement
    # PostgreSQL réussi mais contrainte FK rejetée) : 100 485 lignes n'ont pas de
    # ACCT_OPENING_DATE (nullité structurelle, comptes sans produit attaché - cf.
    # 01_etl/README.md). Le .map() produit donc des NaN pour ces lignes, et pandas
    # convertit alors TOUTE la colonne en float64 dès qu'elle contient un NaN, même
    # si toutes les autres valeurs sont des entiers. Résultat : PostgreSQL créait
    # fact_account_event.date_key en "double precision" alors que dim_date.date_key
    # est en "bigint" -> la contrainte de clé étrangère ne pouvait pas s'appliquer.
    # pandas.Int64Dtype() (le "Int64" avec un I majuscule) est un entier *nullable* :
    # il garde les valeurs manquantes comme <NA> sans forcer un passage en float.
    fact["date_key"] = (
        fact["ACCT_OPENING_DATE"].dt.normalize().map(date_to_key).astype("Int64")
    )

    for fk_col, source_col in [
        ("client_key", "CUSTOMER_NO"), ("account_key", "ACCOUNT_NO"),
        ("branch_key", "BRANCH"), ("closure_key", "CLOSURE_REASON"),
    ]:
        orphans = fact[fk_col].isna() & fact[source_col].notna()
        if orphans.sum() > 0:
            logger.warning("%s ligne(s) avec %s orphelin — à investiguer.", orphans.sum(), fk_col)

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
