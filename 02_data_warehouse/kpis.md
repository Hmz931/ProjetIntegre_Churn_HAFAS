# kpis.md — KPIs Métier et Règles de Calcul

> Conforme à la structure imposée pour `02_data_warehouse/` (voir README.md de ce dossier).
> Ces KPIs sont déjà calculés en pandas dans `01_etl/notebooks/02_ETL.ipynb`, section 3.
> Ce document donne leur **équivalent SQL**, pour l'équipe Power BI ou quiconque
> interroge directement la base PostgreSQL sans repasser par Python.

Toutes les requêtes supposent les tables créées par `schema/create_tables.sql` et
peuplées par `load/load_warehouse.py`.

---

## KPI 01 — Taux de churn global

**Définition** : pourcentage d'événements (lignes `fact_account_event`) associés à un
compte fermé. Calculé au grain événement, conformément à la documentation du projet
(`00_documentation/2_description_donnees.md`, section 4).

```sql
SELECT
    ROUND(100.0 * SUM(churn) / COUNT(*), 1) AS taux_churn_pct
FROM fact_account_event;
```

**Rappel taux de churn au niveau compte** (chaque compte compté une seule fois,
indépendamment de son nombre d'événements) :

```sql
SELECT
    ROUND(100.0 * SUM(churn) / COUNT(*), 1) AS taux_churn_pct_compte
FROM dim_account a
JOIN (
    SELECT DISTINCT account_key, churn FROM fact_account_event
) f ON a.account_key = f.account_key;
```

---

## KPI 04 — Solde moyen et médian par statut

```sql
SELECT
    a."ACCOUNT_STATUS",
    ROUND(AVG(f.acct_balance)::numeric, 2)                              AS solde_moyen,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.acct_balance)::numeric, 2) AS solde_median
FROM fact_account_event f
JOIN dim_account a ON f.account_key = a.account_key
GROUP BY a."ACCOUNT_STATUS";
```

---

## KPI 05 — Salaire moyen par statut

```sql
SELECT
    a."ACCOUNT_STATUS",
    ROUND(AVG(f.salary)::numeric, 2) AS salaire_moyen
FROM fact_account_event f
JOIN dim_account a ON f.account_key = a.account_key
GROUP BY a."ACCOUNT_STATUS";
```

---

## KPI 06 — Taux de churn par segment client (PARTYCLASS)

```sql
SELECT
    c."PARTYCLASS",
    COUNT(*)                                       AS nb_evenements,
    ROUND(100.0 * SUM(f.churn) / COUNT(*), 1)       AS taux_churn_pct
FROM fact_account_event f
JOIN dim_client c ON f.client_key = c.client_key
GROUP BY c."PARTYCLASS"
ORDER BY taux_churn_pct DESC;
```

---

## KPI 07 — Taux de churn par ligne de produit

```sql
SELECT
    p."PRODUCT_LINE",
    COUNT(*)                                       AS nb_evenements,
    ROUND(100.0 * SUM(f.churn) / COUNT(*), 1)       AS taux_churn_pct
FROM fact_account_event f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p."PRODUCT_LINE"
ORDER BY taux_churn_pct DESC;
```

---

## KPI 08 — Taux de churn par score KYC

L'ordre métier (`LR < MR < H1 < H2 < H3`) est appliqué explicitement via `CASE`
plutôt que de trier alphabétiquement.

```sql
SELECT
    c."SCORE_KYC",
    COUNT(*)                                       AS nb_evenements,
    ROUND(100.0 * SUM(f.churn) / COUNT(*), 1)       AS taux_churn_pct
FROM fact_account_event f
JOIN dim_client c ON f.client_key = c.client_key
GROUP BY c."SCORE_KYC"
ORDER BY
    CASE c."SCORE_KYC"
        WHEN 'LR' THEN 1 WHEN 'MR' THEN 2
        WHEN 'H1' THEN 3 WHEN 'H2' THEN 4 WHEN 'H3' THEN 5
        ELSE 6
    END;
```

---

## KPI 09 — Taux de churn par secteur d'activité réel (hors code 9000)

Le code `9000` ("Other") est exclu pour ne pas noyer le signal des vrais secteurs
minoritaires — voir `01_etl/notebooks/01_exploration.ipynb`, section 9.5, pour la
vérification de cette hypothèse via `dim_INDUSTRY.xlsx`.

```sql
SELECT
    c."INDUSTRY_LABEL",
    COUNT(*)                                       AS nb_evenements,
    ROUND(100.0 * SUM(f.churn) / COUNT(*), 1)       AS taux_churn_pct
FROM fact_account_event f
JOIN dim_client c ON f.client_key = c.client_key
WHERE c."INDUSTRY" != '9000'
GROUP BY c."INDUSTRY_LABEL"
HAVING COUNT(*) >= 30  -- seuil de confiance minimal, évite les taux sur petits effectifs
ORDER BY taux_churn_pct DESC
LIMIT 15;
```

---

## KPI 10 — Répartition volontaire / involontaire des clôtures

Nouveauté apportée par l'intégration de `dim_Closure_reason.xlsx` (voir
`01_etl/etl_pipeline/dimension_lookup.py`). Une partie des motifs reste `NULL`
(ambigus, non classifiés par l'heuristique) — affichée explicitement plutôt que masquée.

```sql
SELECT
    CASE
        WHEN cl.is_voluntary IS TRUE  THEN 'Volontaire'
        WHEN cl.is_voluntary IS FALSE THEN 'Involontaire'
        ELSE 'Non classifié'
    END                                             AS type_cloture,
    COUNT(*)                                        AS nb_comptes_fermes
FROM fact_account_event f
JOIN dim_closure cl ON f.closure_key = cl.closure_key
WHERE f.churn = 1
GROUP BY 1
ORDER BY nb_comptes_fermes DESC;
```

---

## Colonnes à exclure des modèles ML (rappel, voir `01_etl/notebooks/02_ETL.ipynb`)

| Colonne | Raison |
|---|---|
| `dim_account."ACCT_CLOSE_DATE"` | Data leakage — n'existe qu'après le churn |
| `dim_closure.closure_reason` / `closure_label` | Data leakage — label post-churn |
| `dim_client."CUSTOMER_NO"`, `dim_account."ACCOUNT_NO"` | Identifiants, aucune valeur prédictive |
| `dim_client."NATIONALITY"` / `"RESIDENCE"` | Quasi-constantes (>93% TN) |

---

## Note méthodologique

Ces requêtes recalculent les KPIs **directement depuis la base**, indépendamment du
notebook Python. Si un chiffre diffère entre cette page et `02_ETL.ipynb`, c'est un
signal qu'il faut investiguer (état du chargement, filtre oublié) — ne pas supposer
qu'une des deux sources a automatiquement raison.
