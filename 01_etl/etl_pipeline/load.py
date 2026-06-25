"""
Étape LOAD : chargement des dimensions et de la table de faits vers PostgreSQL.

✅ Chargement validé contre un vrai serveur PostgreSQL (25/06/2026) : 7/7 tables
chargées avec succès, contraintes appliquées, sur un premier chargement ET sur une
relance contre une base déjà peuplée (voir drop_fact_table_if_exists ci-dessous pour
le bug de dépendance de clé étrangère trouvé et corrigé sur ce second cas).
"""
from __future__ import annotations

import logging
import os

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from . import config

logger = logging.getLogger(__name__)

_engine: Engine | None = None


def get_engine() -> Engine:
    """Crée (ou retourne) l'engine SQLAlchemy, de façon différée.

    create_engine() importe le pilote psycopg2 immédiatement : sur une machine sans
    ce pilote installé, l'appeler au niveau module ferait planter l'import de tout
    le pipeline avant même d'avoir touché aux données. On retarde donc la création
    au premier appel réel de load_table(), dans son propre bloc try/except.

    ⚠️ encoding='utf-8' et connect_args sont forcés explicitement : sur certaines
    configurations Windows (locale système en cp1252, courant en français), psycopg2
    peut tenter de décoder des informations de session en UTF-8 alors que le système
    utilise un autre encodage, ce qui lève un UnicodeDecodeError même quand les
    DONNÉES elles-mêmes ne contiennent aucun caractère problématique — bug réel
    rencontré et confirmé sur une machine Windows lors des tests de ce module.
    """
    global _engine
    if _engine is None:
        # PGCLIENTENCODING : variable d'environnement lue par libpq avant même
        # l'ouverture de la connexion. La fixer explicitement évite que libpq ne
        # retombe sur l'encodage de la console Windows (souvent cp1252).
        os.environ.setdefault("PGCLIENTENCODING", "UTF8")
        _engine = create_engine(
            config.CONNECTION_STRING,
            connect_args={"client_encoding": "utf8"},
        )
    return _engine


def drop_fact_table_if_exists() -> None:
    """Supprime fact_account_event avant de recharger les dimensions, si elle existe.

    ⚠️ Bug réel trouvé en test (rapporté par un membre de l'équipe en relançant le
    pipeline sur une base déjà peuplée) : pandas.to_sql(if_exists="replace") exécute
    un DROP TABLE implicite avant de recréer chaque table. Sur un premier chargement
    (base vide), ça fonctionne. Sur une relance, fact_account_event existe déjà avec
    des contraintes de clé étrangère vers les 6 dimensions — PostgreSQL refuse alors
    de supprimer une dimension tant qu'une table dépendante (la table de faits) la
    référence encore (DependentObjectsStillExist), ce qui fait planter le rechargement
    des dimensions avant même d'arriver à fact_account_event.

    La table de faits est donc explicitement supprimée AVANT toute opération sur les
    dimensions — elle est de toute façon recréée à la fin du chargement (load_all).
    CASCADE n'est pas nécessaire ici car aucune autre table ne dépend de
    fact_account_event ; il est omis pour ne supprimer que ce qui est explicitement
    visé, pas par prudence excessive mais parce qu'un DROP non-CASCADE qui échouerait
    signalerait un problème de modélisation qu'on voudrait voir, pas masquer.
    """
    try:
        engine = get_engine()
        with engine.connect() as connection:
            connection.execute(text("DROP TABLE IF EXISTS fact_account_event;"))
            connection.commit()
        logger.info("Table 'fact_account_event' existante supprimée (si présente), "
                    "avant rechargement des dimensions.")
    except Exception as exc:  # noqa: BLE001 — meme logique de tolerance que load_table
        logger.warning(
            "Impossible de vérifier/supprimer 'fact_account_event' avant rechargement : "
            "%s (%s). Si les dimensions ont déjà été chargées lors d'un run précédent, "
            "le rechargement risque d'échouer sur une dépendance de clé étrangère.",
            type(exc).__name__, exc,
        )


def load_table(
    frame: pd.DataFrame,
    table_name: str,
    primary_key: str | None = None,
    foreign_keys: dict[str, tuple[str, str]] | None = None,
) -> bool:
    """Charge un DataFrame dans PostgreSQL avec clé primaire / clés étrangères.

    En cas d'échec (pilote manquant, serveur non lancé, identifiants invalides...),
    affiche un message clair et retourne False plutôt que de lever une exception qui
    interromprait tout le pipeline — le DataFrame en mémoire reste exploitable pour
    les étapes suivantes (ex. les KPIs du notebook EDA) même sans base disponible.
    """
    try:
        engine = get_engine()
        frame.to_sql(
            name=table_name, con=engine, if_exists="replace",
            index=False, chunksize=10000, method="multi",
        )
        logger.info("'%s' chargée dans PostgreSQL (%s lignes).", table_name, f"{len(frame):,}")

        with engine.connect() as connection:
            if primary_key:
                connection.execute(text(
                    f'ALTER TABLE {table_name} ADD PRIMARY KEY ("{primary_key}");'
                ))
            for fk_col, (ref_table, ref_col) in (foreign_keys or {}).items():
                connection.execute(text(
                    f'ALTER TABLE {table_name} ADD CONSTRAINT fk_{table_name}_{fk_col} '
                    f'FOREIGN KEY ("{fk_col}") REFERENCES {ref_table}("{ref_col}");'
                ))
            connection.commit()
        if primary_key or foreign_keys:
            logger.info("Contraintes appliquées sur '%s'.", table_name)
        return True

    except Exception as exc:  # noqa: BLE001 — volontairement large : on veut continuer
        logger.warning(
            "Chargement PostgreSQL de '%s' impossible : %s (%s). "
            "Le DataFrame reste disponible en mémoire ; seul le chargement en base a échoué.",
            table_name, type(exc).__name__, exc,
        )
        return False


def load_all(dimensions: dict[str, pd.DataFrame], fact_account_event: pd.DataFrame) -> dict[str, bool]:
    """Charge les 6 dimensions puis la table de faits, dans cet ordre — les
    dimensions doivent exister en base avant que les clés étrangères de la table
    de faits ne puissent les référencer.

    La table de faits est explicitement supprimée en tout premier (voir
    drop_fact_table_if_exists) pour que les dimensions puissent elles-mêmes être
    supprimées/recréées sans violer une contrainte de clé étrangère existante sur
    une relance du pipeline contre une base déjà peuplée.
    """
    drop_fact_table_if_exists()

    results = {}
    results["dim_client"] = load_table(dimensions["dim_client"], "dim_client", primary_key="client_key")
    results["dim_branch"] = load_table(dimensions["dim_branch"], "dim_branch", primary_key="branch_key")
    results["dim_account"] = load_table(dimensions["dim_account"], "dim_account", primary_key="account_key")
    results["dim_product"] = load_table(dimensions["dim_product"], "dim_product", primary_key="product_key")
    results["dim_closure"] = load_table(dimensions["dim_closure"], "dim_closure", primary_key="closure_key")
    results["dim_date"] = load_table(dimensions["dim_date"], "dim_date", primary_key="date_key")

    results["fact_account_event"] = load_table(
        fact_account_event, "fact_account_event",
        foreign_keys={
            "client_key": ("dim_client", "client_key"),
            "account_key": ("dim_account", "account_key"),
            "product_key": ("dim_product", "product_key"),
            "branch_key": ("dim_branch", "branch_key"),
            "closure_key": ("dim_closure", "closure_key"),
            "date_key": ("dim_date", "date_key"),
        },
    )

    n_ok = sum(results.values())
    logger.info("Chargement PostgreSQL : %s/%s tables chargées avec succès.", n_ok, len(results))
    return results
