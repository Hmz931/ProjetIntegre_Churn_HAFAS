-- =============================================================================
-- create_tables.sql — Schéma en étoile du Data Warehouse Churn Bancaire
-- =============================================================================
-- Ce script documente explicitement le schéma déjà créé implicitement par
-- 01_etl/etl_pipeline/load.py (via pandas.DataFrame.to_sql). Les deux chemins
-- créent le même schéma — celui-ci sert de référence indépendante du code
-- Python, utilisable directement avec psql ou pgAdmin sans repasser par Python.
--
-- Types vérifiés contre une base réelle (chargement validé : 7/7 tables,
-- contraintes appliquées avec succès le 25/06/2026).
--
-- Ordre d'exécution : dimensions d'abord (aucune dépendance), puis la table de
-- faits en dernier (ses clés étrangères référencent toutes les dimensions).
-- =============================================================================

-- -----------------------------------------------------------------------------
-- DIM_CLIENT — grain : 1 ligne par CUSTOMER_NO
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_client CASCADE;

CREATE TABLE dim_client (
    client_key          BIGINT       PRIMARY KEY,
    "CUSTOMER_NO"       VARCHAR(20)  NOT NULL UNIQUE,
    "DATE_OF_BIRTH"     TIMESTAMP,
    age                 INTEGER,
    "MARITAL_STATUS"    VARCHAR(30),
    "NATIONALITY"       VARCHAR(10),
    "RESIDENCE"         VARCHAR(10),
    "NATURE_CLIENT"     VARCHAR(10),
    "PARTYCLASS"        VARCHAR(30),
    "LOB"               INTEGER,
    "INDUSTRY"          VARCHAR(10),
    "SCORE_KYC"         VARCHAR(5),
    "COMPLETED_FILE"    VARCHAR(5),
    "CUST_OPENING_DATE" TIMESTAMP,
    "LAST_REVIEW_DATE"  TIMESTAMP,
    "INDUSTRY_LABEL"    TEXT  -- décodé via data/dim_INDUSTRY.xlsx (cf. 01_etl/README.md)
);

COMMENT ON TABLE dim_client IS
    'Attributs client stables. Voir 01_etl/README.md section "Décisions de modélisation".';

-- -----------------------------------------------------------------------------
-- DIM_BRANCH — grain : 1 ligne par BRANCH
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_branch CASCADE;

CREATE TABLE dim_branch (
    branch_key      BIGINT       PRIMARY KEY,
    "BRANCH"        VARCHAR(10)  NOT NULL UNIQUE,
    branch_label    VARCHAR(10),
    region          VARCHAR(50),  -- NULL : non présent dans le fichier source, à enrichir si disponible
    "LOB"           INTEGER,
    "PARTYCLASS"    VARCHAR(30)
);

-- -----------------------------------------------------------------------------
-- DIM_ACCOUNT — grain : 1 ligne par ACCOUNT_NO
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_account CASCADE;

CREATE TABLE dim_account (
    account_key             BIGINT       PRIMARY KEY,
    "ACCOUNT_NO"            VARCHAR(20)  NOT NULL UNIQUE,
    "ACCOUNT_STATUS"        VARCHAR(20),
    "ACCOUNT_CATEGORY"      VARCHAR(20),
    "ACCOUNT_TYPE_DESC"     VARCHAR(100),
    "CURRENCY"              VARCHAR(10),
    "ACCT_OPENING_DATE"     TIMESTAMP,
    "ACCT_CLOSE_DATE"       TIMESTAMP,   -- NULL pour tout compte Active (nullité structurelle vérifiée)
    acct_tenure_days        INTEGER,
    nb_accounts_per_client  INTEGER,
    "NEXT__REVIEW_DATE"     TIMESTAMP,
    "CATEGORY_LABEL"        TEXT,   -- décodé via data/dim_CATEGORY_ACCOUNT.xlsx
    "CURRENCY_LABEL"        TEXT    -- décodé via data/dim_CURRENCY.xlsx
);

-- -----------------------------------------------------------------------------
-- DIM_PRODUCT — grain : 1 ligne par CONTRAT (compte x produit), PAS par produit
-- catalogue. Voir 01_etl/README.md pour la justification de ce choix de grain.
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_product CASCADE;

CREATE TABLE dim_product (
    product_key         BIGINT  PRIMARY KEY,
    "PRODUCT_GROUP"      VARCHAR(50),
    "PRODUCT_LINE"        VARCHAR(30),
    "PRODUCT"             VARCHAR(50),
    "ACCOUNTNATURE"       VARCHAR(100),
    "FIXEDRATE"           DOUBLE PRECISION,
    "STARTDATE"           TIMESTAMP,
    "MATURITYDATE"        TIMESTAMP,
    "PRODUCT_STATUS"      VARCHAR(20),
    "AMOUNT"              DOUBLE PRECISION,
    product_line_risk    INTEGER  -- encodage ordinal du risque de churn par ligne de produit
);

COMMENT ON TABLE dim_product IS
    'Grain contrat (dimension dégénérée, cardinalité proche de fact_account_event). '
    'AMOUNT/FIXEDRATE/dates varient par contrat (74%% des produits ont >1 valeur AMOUNT) : '
    'voir 01_etl/README.md, section "Décisions de modélisation".';

-- -----------------------------------------------------------------------------
-- DIM_CLOSURE — grain : 1 ligne par motif de clôture
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_closure CASCADE;

CREATE TABLE dim_closure (
    closure_key        BIGINT       PRIMARY KEY,
    closure_reason      VARCHAR(30)  NOT NULL UNIQUE,
    closure_label       TEXT,
    closure_category    VARCHAR(20),
    is_voluntary        BOOLEAN,     -- NULL si non classifiable, voir dimension_lookup.py
    churn_type           VARCHAR(20)
);

COMMENT ON TABLE dim_closure IS
    'Libellés réels et classification volontaire/involontaire décodés via '
    'data/dim_Closure_reason.xlsx. Certains motifs restent classifiés NULL '
    '(ambigus) — choix délibéré, voir etl_pipeline/dimension_lookup.py.';

-- -----------------------------------------------------------------------------
-- DIM_DATE — grain : 1 ligne par jour calendaire
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_date CASCADE;

CREATE TABLE dim_date (
    date_key    BIGINT     PRIMARY KEY,
    full_date   TIMESTAMP  NOT NULL UNIQUE,
    year        INTEGER,
    quarter     INTEGER,
    month       INTEGER
);

-- -----------------------------------------------------------------------------
-- FACT_ACCOUNT_EVENT — grain : 1 ligne par événement (= 1 ligne du fichier
-- source après nettoyage). PAS de réduction par compte ni par client.
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_account_event CASCADE;

CREATE TABLE fact_account_event (
    client_key            BIGINT  NOT NULL REFERENCES dim_client(client_key),
    account_key           BIGINT  NOT NULL REFERENCES dim_account(account_key),
    product_key           BIGINT  NOT NULL REFERENCES dim_product(product_key),
    branch_key             BIGINT  NOT NULL REFERENCES dim_branch(branch_key),
    date_key               BIGINT  REFERENCES dim_date(date_key),  -- NULL si ACCT_OPENING_DATE absent (~22.5% des lignes, nullité structurelle)
    closure_key            BIGINT  NOT NULL REFERENCES dim_closure(closure_key),
    acct_balance           DOUBLE PRECISION,  -- NaN volontairement conservés, voir 01_etl/README.md
    salary                  DOUBLE PRECISION,  -- idem
    amount                  DOUBLE PRECISION,
    fixedrate               DOUBLE PRECISION,
    acct_tenure_days       INTEGER,
    client_tenure_days     INTEGER,
    nb_accounts             INTEGER,
    churn                   INTEGER  NOT NULL  -- 0 ou 1 ; calculé au niveau compte, propagé sur l'événement (voir fact.py)
);

COMMENT ON TABLE fact_account_event IS
    'Table de faits, grain événement (= grain natif du fichier source). '
    '445 803 lignes sur le jeu de données réel (528 883 lignes brutes, '
    'après nettoyage). Voir 01_etl/README.md pour le détail du pipeline.';

CREATE INDEX idx_fact_client_key ON fact_account_event(client_key);
CREATE INDEX idx_fact_account_key ON fact_account_event(account_key);
CREATE INDEX idx_fact_churn ON fact_account_event(churn);
