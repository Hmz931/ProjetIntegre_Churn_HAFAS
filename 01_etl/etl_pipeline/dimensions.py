"""
Étape DIMENSIONS : construction des 6 tables de dimension du schéma en étoile.

Schéma cible (validé en équipe, voir 01_etl/notebooks/DW.svg) :
    DIM_CLIENT    grain client (CUSTOMER_NO)
    DIM_DATE      grain jour calendaire
    DIM_BRANCH    grain agence (BRANCH)
    DIM_ACCOUNT   grain compte (ACCOUNT_NO)
    DIM_PRODUCT   grain CONTRAT (compte x produit) — voir note de grain dans le README
    DIM_CLOSURE   grain motif de clôture

Chaque fonction retourne un DataFrame avec sa clé primaire en première colonne et un
nom explicite, prêt à être chargé par load.py.
"""
from __future__ import annotations

import logging

import pandas as pd

from . import config
from .dimension_lookup import build_closure_reason_lookup, classify_closure_voluntary

logger = logging.getLogger(__name__)


def build_dim_client(df: pd.DataFrame) -> pd.DataFrame:
    """DIM_CLIENT — grain client. Une ligne par CUSTOMER_NO.

    En l'absence d'un ordre garanti dans le fichier source, on garde la ligne la
    plus récente par date de dernière revue (LAST_REVIEW_DATE) plutôt que la
    première rencontrée — résultat déterministe et documenté, pas dépendant de
    l'ordre des lignes du CSV.
    """
    dim_client = (
        df.sort_values("LAST_REVIEW_DATE")
          .drop_duplicates(subset="CUSTOMER_NO", keep="last")
          .copy()
    )

    dim_client["age"] = config.REFERENCE_DATE.year - dim_client["DATE_OF_BIRTH"].dt.year
    dim_client["age"] = dim_client["age"].where(dim_client["age"].between(0, 100))

    dim_client = dim_client[[
        "CUSTOMER_NO", "DATE_OF_BIRTH", "age",
        "MARITAL_STATUS", "NATIONALITY", "RESIDENCE", "NATURE_CLIENT",
        "PARTYCLASS", "LOB", "INDUSTRY", "SCORE_KYC", "COMPLETED_FILE",
        "CUST_OPENING_DATE", "LAST_REVIEW_DATE",
    ]].reset_index(drop=True)

    width = len(str(len(dim_client)))
    dim_client.insert(0, "client_key", "CLI_" + pd.Series(range(1, len(dim_client) + 1)).astype(str).str.zfill(width).values)

    assert dim_client["CUSTOMER_NO"].is_unique, "CUSTOMER_NO n'est pas unique dans dim_client !"
    logger.info("DIM_CLIENT construite : %s clients uniques", f"{len(dim_client):,}")
    return dim_client


def enrich_dim_client_with_industry_labels(
    dim_client: pd.DataFrame, dim_industry_raw: pd.DataFrame | None
) -> pd.DataFrame:
    """Enrichit DIM_CLIENT avec le libellé métier du secteur d'activité, à partir de
    dim_INDUSTRY.xlsx. Sans effet si la dimension n'a pas été fournie (le pipeline
    reste utilisable, simplement moins enrichi).
    """
    if dim_industry_raw is None:
        logger.warning("dim_INDUSTRY non fournie — INDUSTRY_LABEL non ajouté à DIM_CLIENT.")
        return dim_client

    dim_client = dim_client.copy()
    lookup = dim_industry_raw.rename(
        columns={"INDUSTRY_CODE": "INDUSTRY", "INDUSTRY DESCRIPTION": "INDUSTRY_LABEL"}
    )
    # INDUSTRY est stocké comme texte dans le fichier principal (cf. clean.py) ;
    # le code de la dimension est numérique -> conversion explicite pour la jointure.
    lookup["INDUSTRY"] = lookup["INDUSTRY"].astype(str)
    dim_client = dim_client.merge(lookup[["INDUSTRY", "INDUSTRY_LABEL"]], on="INDUSTRY", how="left")

    n_unmatched = dim_client["INDUSTRY_LABEL"].isna().sum() - (dim_client["INDUSTRY"] == "INCONNU").sum()
    if n_unmatched > 0:
        logger.warning(
            "%s client(s) avec un code INDUSTRY non trouvé dans dim_INDUSTRY.xlsx "
            "(hors 'INCONNU', qui est attendu) — ex. code 9998 vérifié absent du référentiel.",
            n_unmatched,
        )
    return dim_client


def build_dim_branch(df: pd.DataFrame) -> pd.DataFrame:
    """DIM_BRANCH — grain agence. Une ligne par BRANCH.

    'region' n'est pas présent dans le fichier source ni dans aucune dimension
    fournie : laissé à None, à enrichir si un référentiel agences->région existe.
    """
    dim_branch = df.drop_duplicates(subset="BRANCH").copy()

    for col in ["BRANCH", "LOB", "PARTYCLASS"]:
        dim_branch[col] = dim_branch[col].astype(str).str.strip().replace("nan", None)

    dim_branch["branch_label"] = dim_branch["BRANCH"]
    dim_branch["region"] = None

    dim_branch = dim_branch[
        ["BRANCH", "branch_label", "region", "LOB", "PARTYCLASS"]
    ].reset_index(drop=True)
    width = len(str(len(dim_branch)))
    dim_branch.insert(0, "branch_key", "BRA_" + pd.Series(range(1, len(dim_branch) + 1)).astype(str).str.zfill(width).values)

    assert dim_branch["BRANCH"].is_unique, "BRANCH n'est pas unique dans dim_branch !"
    logger.info("DIM_BRANCH construite : %s agences uniques", f"{len(dim_branch):,}")
    return dim_branch


def build_dim_account(df: pd.DataFrame) -> pd.DataFrame:
    """DIM_ACCOUNT — grain compte. Une ligne par ACCOUNT_NO.

    Le flag `churn` n'est volontairement PAS stocké ici : le schéma cible le place
    uniquement dans FACT_ACCOUNT_EVENT (voir fact.py). DIM_ACCOUNT garde uniquement
    les attributs descriptifs du compte.
    """
    dim_account = df.drop_duplicates(subset="ACCOUNT_NO").copy()

    end_date = dim_account["ACCT_CLOSE_DATE"].fillna(config.REFERENCE_DATE)
    dim_account["acct_tenure_days"] = (end_date - dim_account["ACCT_OPENING_DATE"]).dt.days
    dim_account["acct_tenure_days"] = dim_account["acct_tenure_days"].where(
        dim_account["acct_tenure_days"] >= 0
    )  # valeurs négatives -> NaN (erreur de saisie probable)

    nb_accounts = df.groupby("CUSTOMER_NO")["ACCOUNT_NO"].nunique().rename("nb_accounts_per_client")
    dim_account = dim_account.merge(nb_accounts, on="CUSTOMER_NO", how="left")

    dim_account = dim_account[[
        "ACCOUNT_NO", "ACCOUNT_STATUS", "ACCOUNT_CATEGORY", "ACCOUNT_TYPE_DESC", "CURRENCY",
        "ACCT_OPENING_DATE", "ACCT_CLOSE_DATE", "acct_tenure_days",
        "nb_accounts_per_client", "NEXT__REVIEW_DATE",
    ]].reset_index(drop=True)
    width = len(str(len(dim_account)))
    dim_account.insert(0, "account_key", "ACC_" + pd.Series(range(1, len(dim_account) + 1)).astype(str).str.zfill(width).values)

    assert dim_account["ACCOUNT_NO"].is_unique, "ACCOUNT_NO n'est pas unique dans dim_account !"
    logger.info("DIM_ACCOUNT construite : %s comptes uniques", f"{len(dim_account):,}")
    return dim_account


def enrich_dim_account_with_category_labels(
    dim_account: pd.DataFrame, dim_category_raw: pd.DataFrame | None,
    dim_currency_raw: pd.DataFrame | None,
) -> pd.DataFrame:
    """Enrichit DIM_ACCOUNT avec les libellés de catégorie de compte et de devise."""
    dim_account = dim_account.copy()

    if dim_category_raw is not None:
        lookup = dim_category_raw.rename(
            columns={"CATEGORY_id": "ACCOUNT_CATEGORY", "CATEGORY DESCRIPTION": "CATEGORY_LABEL"}
        )
        dim_account = dim_account.merge(
            lookup[["ACCOUNT_CATEGORY", "CATEGORY_LABEL"]], on="ACCOUNT_CATEGORY", how="left"
        )
    else:
        logger.warning("dim_CATEGORY_ACCOUNT non fournie — CATEGORY_LABEL non ajouté.")

    if dim_currency_raw is not None:
        lookup_ccy = dim_currency_raw.rename(
            columns={"CURRENCY_CODE": "CURRENCY", "CCY_NAME": "CURRENCY_LABEL"}
        )
        dim_account = dim_account.merge(
            lookup_ccy[["CURRENCY", "CURRENCY_LABEL"]], on="CURRENCY", how="left"
        )
    else:
        logger.warning("dim_CURRENCY non fournie — CURRENCY_LABEL non ajouté.")

    return dim_account


def build_dim_product(df: pd.DataFrame) -> pd.DataFrame:
    """DIM_PRODUCT — grain CONTRAT (décision de modélisation validée en équipe).

    ⚠️ Une ligne par combinaison (compte, produit) du fichier source, PAS par code
    produit catalogue. Raison : AMOUNT, FIXEDRATE, STARTDATE, MATURITYDATE,
    PRODUCT_STATUS varient réellement par contrat — vérifié sur les données réelles,
    157 produits sur 213 (74%) ont plusieurs valeurs AMOUNT distinctes. Le schéma
    cible place ces colonnes dans DIM_PRODUCT ; les y mettre à un grain "produit
    catalogue" aurait silencieusement assigné un montant arbitraire et faux à la
    majorité des comptes liés à ce produit.

    Conséquence acceptée : DIM_PRODUCT aura une cardinalité proche de celle de la
    table de faits (dimension dite "dégénérée") — un choix de modélisation assumé,
    pas un bug.
    """
    dim_product = df[[
        "PRODUCT_GROUP", "PRODUCT_LINE", "PRODUCT", "ACCOUNTNATURE",
        "FIXEDRATE", "STARTDATE", "MATURITYDATE", "PRODUCT_STATUS", "AMOUNT",
    ]].copy().reset_index(drop=True)

    dim_product["product_line_risk"] = dim_product["PRODUCT_LINE"].map(config.PRODUCT_LINE_RISK_MAP)

    width = len(str(len(dim_product)))
    dim_product.insert(0, "product_key", "PROD_" + pd.Series(range(1, len(dim_product) + 1)).astype(str).str.zfill(width).values)

    assert dim_product["product_key"].is_unique
    logger.info("DIM_PRODUCT construite : %s contrats (grain = compte x produit)",
                f"{len(dim_product):,}")
    return dim_product


def build_dim_closure(df: pd.DataFrame, dim_closure_reason_raw: pd.DataFrame | None) -> pd.DataFrame:
    """DIM_CLOSURE — grain motif de clôture.

    Si dim_Closure_reason.xlsx est fournie, les libellés réels et une classification
    is_voluntary basée sur le libellé métier (cf. dimension_lookup.classify_closure_voluntary)
    sont utilisés. Sinon, des placeholders explicitement marqués comme tels sont
    utilisés à la place — le pipeline reste utilisable mais avec une information moins
    riche, et un avertissement clair est levé.
    """
    dim_closure = df[["CLOSURE_REASON"]].drop_duplicates().reset_index(drop=True)
    dim_closure = dim_closure.rename(columns={"CLOSURE_REASON": "closure_reason"})

    if dim_closure_reason_raw is not None:
        reason_lookup = build_closure_reason_lookup(dim_closure_reason_raw)

        # ⚠️ Bug réel trouvé en test (rapporté par un membre de l'équipe sur sa propre
        # machine) : reason_lookup contient des lignes dont closure_code_anonymized
        # est None (motifs non numérotés, ex. "CUSTOMER.REQUEST", "DECEASED.CUSTOMER").
        # Si dim_closure["closure_reason"] contenait lui-même une valeur NaN (donnée
        # imprévue dans CLOSURE_REASON après nettoyage), un merge naïf joindrait cette
        # ligne NaN à TOUTES les lignes de reason_lookup où closure_code_anonymized est
        # aussi NaN — produisant un produit cartésien de doublons. On retire donc les
        # lignes sans code anonymisé valide avant la jointure : elles n'ont de toute
        # façon rien à apporter ici (pas de correspondance numérique possible avec
        # CLOSURE_REASON, qui est toujours soit BANK.REASON.N, soit NON_FERME/INCONNUE).
        reason_lookup_valid = reason_lookup.dropna(subset=["closure_code_anonymized"])

        n_closure_nan = dim_closure["closure_reason"].isna().sum()
        if n_closure_nan > 0:
            logger.warning(
                "%s ligne(s) de CLOSURE_REASON sont NaN après nettoyage (valeur "
                "imprévue, ni 'NON_FERME' ni 'INCONNUE') — à investiguer dans clean.py. "
                "Ces lignes sont exclues de DIM_CLOSURE pour éviter un merge incorrect.",
                n_closure_nan,
            )
            dim_closure = dim_closure.dropna(subset=["closure_reason"])

        dim_closure = dim_closure.merge(
            reason_lookup_valid[["closure_code_anonymized", "DESCRIPTION"]],
            left_on="closure_reason", right_on="closure_code_anonymized", how="left",
        )
        # Contrôle explicite : si malgré tout la jointure a dupliqué des lignes
        # (autre cause non anticipée), on le détecte ici avec un message clair
        # plutôt que de laisser l'assertion finale échouer sans contexte.
        if dim_closure["closure_reason"].duplicated().any():
            n_dupes = dim_closure["closure_reason"].duplicated().sum()
            dupe_examples = dim_closure.loc[
                dim_closure["closure_reason"].duplicated(keep=False), "closure_reason"
            ].unique()[:5]
            raise ValueError(
                f"La jointure avec dim_Closure_reason.xlsx a produit {n_dupes} ligne(s) "
                f"dupliquée(s) sur closure_reason (ex. : {list(dupe_examples)}). "
                f"Vérifiez dim_Closure_reason.xlsx pour des codes RECID en double."
            )

        dim_closure["closure_label"] = dim_closure["DESCRIPTION"].fillna(dim_closure["closure_reason"])
        dim_closure["is_voluntary"] = dim_closure["closure_label"].apply(classify_closure_voluntary)
        dim_closure = dim_closure.drop(columns=["closure_code_anonymized", "DESCRIPTION"])

        # Cas particuliers non décodés par la jointure numérique (motifs métier, pas
        # de clôture du tout) : on les corrige explicitement plutôt que de laisser
        # une classification automatique incertaine sur ces cas connus.
        dim_closure.loc[dim_closure["closure_reason"] == "NON_FERME", "closure_label"] = (
            "Compte actif (pas de clôture)"
        )
        dim_closure.loc[dim_closure["closure_reason"] == "NON_FERME", "is_voluntary"] = False
        dim_closure.loc[dim_closure["closure_reason"] == "INCONNUE", "closure_label"] = (
            "Clôturé, motif non documenté dans le système source"
        )

        n_unclassified = dim_closure["is_voluntary"].isna().sum()
        logger.info(
            "DIM_CLOSURE enrichie via dim_Closure_reason.xlsx : %s/%s motifs classifiés "
            "volontaire/involontaire (%s restent ambigus, classification heuristique "
            "non forcée — voir dimension_lookup.classify_closure_voluntary).",
            len(dim_closure) - n_unclassified, len(dim_closure), n_unclassified,
        )
    else:
        logger.warning(
            "dim_Closure_reason.xlsx non fournie — utilisation de placeholders non "
            "documentés pour closure_label/is_voluntary (sens réel des codes inconnu)."
        )
        dim_closure["closure_label"] = dim_closure["closure_reason"]
        dim_closure["is_voluntary"] = None
        dim_closure.loc[dim_closure["closure_reason"] == "NON_FERME", "is_voluntary"] = False

    dim_closure["closure_category"] = "INCONNU"
    dim_closure["churn_type"] = "INCONNU"
    dim_closure.loc[dim_closure["closure_reason"] == "NON_FERME", "churn_type"] = "NON_APPLICABLE"

    width = len(str(len(dim_closure)))
    dim_closure.insert(0, "closure_key", "CLO_" + pd.Series(range(1, len(dim_closure) + 1)).astype(str).str.zfill(width).values)

    assert dim_closure["closure_reason"].is_unique
    logger.info("DIM_CLOSURE construite : %s motifs uniques", f"{len(dim_closure):,}")
    return dim_closure


def build_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    """DIM_DATE — une ligne par jour calendaire sur toute la plage couverte par les
    colonnes de date du fichier source.
    """
    date_cols_for_range = [
        "CUST_OPENING_DATE", "ACCT_OPENING_DATE", "ACCT_CLOSE_DATE",
        "LAST_REVIEW_DATE", "NEXT__REVIEW_DATE", "STARTDATE", "MATURITYDATE", "DATE_OF_BIRTH",
    ]
    all_dates = pd.concat([df[col] for col in date_cols_for_range if col in df.columns])

    min_date = all_dates.min()
    max_date = max(all_dates.max(), config.REFERENCE_DATE)

    dim_date = pd.DataFrame({"full_date": pd.date_range(start=min_date, end=max_date)})
    dim_date["year"] = dim_date["full_date"].dt.year
    dim_date["quarter"] = dim_date["full_date"].dt.quarter
    dim_date["month"] = dim_date["full_date"].dt.month
    width = len(str(len(dim_date)))
    dim_date.insert(0, "date_key", "DATE_" + pd.Series(range(1, len(dim_date) + 1)).astype(str).str.zfill(width).values)

    logger.info("DIM_DATE construite : %s jours (%s -> %s)",
                f"{len(dim_date):,}", min_date.date(), max_date.date())
    return dim_date


def build_all_dimensions(
    df: pd.DataFrame, raw_dimensions: dict[str, pd.DataFrame]
) -> dict[str, pd.DataFrame]:
    """Point d'entrée unique de l'étape Dimensions : construit les 6 dimensions et
    les enrichit avec les fichiers dim_*.xlsx quand ils sont disponibles.
    """
    dim_client = build_dim_client(df)
    dim_client = enrich_dim_client_with_industry_labels(
        dim_client, raw_dimensions.get("industry")
    )

    dim_branch = build_dim_branch(df)

    dim_account = build_dim_account(df)
    dim_account = enrich_dim_account_with_category_labels(
        dim_account, raw_dimensions.get("category_account"), raw_dimensions.get("currency")
    )

    dim_product = build_dim_product(df)
    dim_closure = build_dim_closure(df, raw_dimensions.get("closure_reason"))
    dim_date = build_dim_date(df)

    return {
        "dim_client": dim_client,
        "dim_branch": dim_branch,
        "dim_account": dim_account,
        "dim_product": dim_product,
        "dim_closure": dim_closure,
        "dim_date": dim_date,
    }
