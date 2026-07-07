# DAX Scripts — Churn Bancaire
### Basé sur le Datawarehouse : FACT_ACCOUNT_EVENT + 6 dimensions

> **Fact table :** `FACT_ACCOUNT_EVENT`  
> **Variable cible :** colonne `churn` (int) — `1` = churned · `0` = actif  
> **Relations :** FACT → DIM_CLIENT, DIM_ACCOUNT, DIM_PRODUCT, DIM_BRANCH, DIM_DATE, DIM_CLOSURE

---

## KPI 01 — Taux de churn global

```dax
Taux Churn % =
DIVIDE(
    CALCULATE(COUNTROWS(FACT_ACCOUNT_EVENT), FACT_ACCOUNT_EVENT[churn] = 1),
    COUNTROWS(FACT_ACCOUNT_EVENT)
) * 100
```

---

## KPI 02 — Ancienneté moyenne client (par statut)

```dax
Anciennete Moyenne Churned =
CALCULATE(
    AVERAGEX(FACT_ACCOUNT_EVENT, FACT_ACCOUNT_EVENT[client_tenure_days] / 365),
    FACT_ACCOUNT_EVENT[churn] = 1
)

Anciennete Moyenne Actifs =
CALCULATE(
    AVERAGEX(FACT_ACCOUNT_EVENT, FACT_ACCOUNT_EVENT[client_tenure_days] / 365),
    FACT_ACCOUNT_EVENT[churn] = 0
)
```

---

## KPI 03 — Taux de churn par tranche d'âge

```dax
Tranche Age =
SWITCH(TRUE(),
    DIM_CLIENT[age] <= 30, "18-30",
    DIM_CLIENT[age] <= 40, "31-40",
    DIM_CLIENT[age] <= 50, "41-50",
    DIM_CLIENT[age] <= 60, "51-60",
    DIM_CLIENT[age] > 60,  "60+",
    "Inconnu"
)

Churn Rate par Age =
DIVIDE(
    CALCULATE(COUNTROWS(FACT_ACCOUNT_EVENT), FACT_ACCOUNT_EVENT[churn] = 1),
    COUNTROWS(FACT_ACCOUNT_EVENT)
) * 100
-- Utiliser avec [Tranche Age] en axe
```

---

## KPI 04 — Solde moyen par statut

```dax
Solde Moyen Churned =
CALCULATE(
    AVERAGE(FACT_ACCOUNT_EVENT[ACCT_BALANCE]),
    FACT_ACCOUNT_EVENT[churn] = 1
)

Solde Moyen Actifs =
CALCULATE(
    AVERAGE(FACT_ACCOUNT_EVENT[ACCT_BALANCE]),
    FACT_ACCOUNT_EVENT[churn] = 0
)

Ecart Solde Churned vs Actifs =
[Solde Moyen Churned] - [Solde Moyen Actifs]
```

---

## KPI 05 — Salaire moyen par statut

```dax
Salaire Moyen Churned =
CALCULATE(
    AVERAGE(FACT_ACCOUNT_EVENT[SALARY]),
    FACT_ACCOUNT_EVENT[churn] = 1
)

Salaire Moyen Actifs =
CALCULATE(
    AVERAGE(FACT_ACCOUNT_EVENT[SALARY]),
    FACT_ACCOUNT_EVENT[churn] = 0
)
```

---

## KPI 06 — Taux de churn par segment client

```dax
Churn Rate par Segment =
DIVIDE(
    CALCULATE(COUNTROWS(FACT_ACCOUNT_EVENT), FACT_ACCOUNT_EVENT[churn] = 1),
    COUNTROWS(FACT_ACCOUNT_EVENT)
) * 100
-- Utiliser avec DIM_CLIENT[PARTYCLASS] en axe
```

---

## KPI 07 — Taux de churn par ligne de produit

```dax
Churn Rate par Produit Line =
DIVIDE(
    CALCULATE(COUNTROWS(FACT_ACCOUNT_EVENT), FACT_ACCOUNT_EVENT[churn] = 1),
    COUNTROWS(FACT_ACCOUNT_EVENT)
) * 100
-- Utiliser avec DIM_PRODUCT[PRODUCT_LINE] en axe

Churn Rate par Produit Group =
DIVIDE(
    CALCULATE(COUNTROWS(FACT_ACCOUNT_EVENT), FACT_ACCOUNT_EVENT[churn] = 1),
    COUNTROWS(FACT_ACCOUNT_EVENT)
) * 100
-- Utiliser avec DIM_PRODUCT[PRODUCT_GROUP] en axe
```

---

## KPI 08 — Taux de churn par profil de risque KYC

```dax
KYC Risk Ordinal =
SWITCH(DIM_CLIENT[SCORE_KYC],
    "LR", 0,
    "MR", 1,
    "H1", 2,
    "H2", 3,
    "H3", 4,
    BLANK()
)

Churn Rate par KYC =
DIVIDE(
    CALCULATE(COUNTROWS(FACT_ACCOUNT_EVENT), FACT_ACCOUNT_EVENT[churn] = 1),
    COUNTROWS(FACT_ACCOUNT_EVENT)
) * 100
-- Utiliser avec DIM_CLIENT[SCORE_KYC] en axe (tri forcé via KYC Risk Ordinal)
```

---

## KPI 09 — Tendance du churn dans le temps

```dax
Churns par Annee =
CALCULATE(
    COUNTROWS(FACT_ACCOUNT_EVENT),
    FACT_ACCOUNT_EVENT[churn] = 1
)
-- Utiliser avec DIM_DATE[year] en axe

Churns par Mois =
CALCULATE(
    COUNTROWS(FACT_ACCOUNT_EVENT),
    FACT_ACCOUNT_EVENT[churn] = 1
)
-- Utiliser avec DIM_DATE[full_date] ou DIM_DATE[month] en axe

Croissance Churn YoY % =
VAR annee_courante = [Churns par Annee]
VAR annee_precedente =
    CALCULATE(
        [Churns par Annee],
        DATEADD(DIM_DATE[full_date], -1, YEAR)
    )
RETURN
    DIVIDE(annee_courante - annee_precedente, annee_precedente) * 100
```

---

## KPI 10 — Complétude du dossier client

```dax
Taux Dossiers Complets % =
DIVIDE(
    CALCULATE(
        COUNTROWS(FACT_ACCOUNT_EVENT),
        DIM_CLIENT[COMPLETED_FILE] = "YES"
    ),
    COUNTROWS(FACT_ACCOUNT_EVENT)
) * 100

Churn Rate Dossier Incomplet =
CALCULATE(
    DIVIDE(
        CALCULATE(COUNTROWS(FACT_ACCOUNT_EVENT), FACT_ACCOUNT_EVENT[churn] = 1),
        COUNTROWS(FACT_ACCOUNT_EVENT)
    ),
    DIM_CLIENT[COMPLETED_FILE] <> "YES"
) * 100

Churn Rate Dossier Complet =
CALCULATE(
    DIVIDE(
        CALCULATE(COUNTROWS(FACT_ACCOUNT_EVENT), FACT_ACCOUNT_EVENT[churn] = 1),
        COUNTROWS(FACT_ACCOUNT_EVENT)
    ),
    DIM_CLIENT[COMPLETED_FILE] = "YES"
) * 100
```

---

## KPI 11 — Taux de churn par situation matrimoniale

```dax
Statut Civil Label =
SWITCH(DIM_CLIENT[MARITAL_STATUS],
    "M", "Marié(e)",
    "C", "Célibataire",
    "D", "Divorcé(e)",
    "V", "Veuf/ve",
    "Inconnu"
)

Churn Rate par Statut Civil =
DIVIDE(
    CALCULATE(COUNTROWS(FACT_ACCOUNT_EVENT), FACT_ACCOUNT_EVENT[churn] = 1),
    COUNTROWS(FACT_ACCOUNT_EVENT)
) * 100
-- Utiliser avec [Statut Civil Label] en axe
```

---

## KPI 12 — Ratio solde / salaire (feature engineered)

```dax
Ratio Solde Salaire =
DIVIDE(
    FACT_ACCOUNT_EVENT[ACCT_BALANCE],
    FACT_ACCOUNT_EVENT[SALARY] + 1
)

Ratio Moyen Churned =
CALCULATE(
    AVERAGEX(FACT_ACCOUNT_EVENT, FACT_ACCOUNT_EVENT[ACCT_BALANCE] / (FACT_ACCOUNT_EVENT[SALARY] + 1)),
    FACT_ACCOUNT_EVENT[churn] = 1
)

Ratio Moyen Actifs =
CALCULATE(
    AVERAGEX(FACT_ACCOUNT_EVENT, FACT_ACCOUNT_EVENT[ACCT_BALANCE] / (FACT_ACCOUNT_EVENT[SALARY] + 1)),
    FACT_ACCOUNT_EVENT[churn] = 0
)
```

---

## KPI-N1 — Taux de rétention

```dax
Taux Retention % =
DIVIDE(
    CALCULATE(COUNTROWS(FACT_ACCOUNT_EVENT), FACT_ACCOUNT_EVENT[churn] = 0),
    COUNTROWS(FACT_ACCOUNT_EVENT)
) * 100

Retention par Segment =
CALCULATE(
    [Taux Retention %],
    ALLEXCEPT(FACT_ACCOUNT_EVENT, DIM_CLIENT[PARTYCLASS])
)
```

---

## KPI-N2 — Profondeur de relation (nombre de produits par client)

```dax
-- nb_accounts est déjà disponible dans FACT_ACCOUNT_EVENT
Churn Rate par Profondeur =
DIVIDE(
    CALCULATE(COUNTROWS(FACT_ACCOUNT_EVENT), FACT_ACCOUNT_EVENT[churn] = 1),
    COUNTROWS(FACT_ACCOUNT_EVENT)
) * 100
-- Utiliser avec FACT_ACCOUNT_EVENT[nb_accounts] en axe

Bucket Profondeur =
SWITCH(TRUE(),
    FACT_ACCOUNT_EVENT[nb_accounts] = 1, "1 produit",
    FACT_ACCOUNT_EVENT[nb_accounts] = 2, "2 produits",
    FACT_ACCOUNT_EVENT[nb_accounts] = 3, "3 produits",
    FACT_ACCOUNT_EVENT[nb_accounts] = 4, "4 produits",
    FACT_ACCOUNT_EVENT[nb_accounts] >= 5, "5+ produits",
    "Inconnu"
)
```

---

## KPI-N3 — Valeur à risque (VaR Churn) — Exposition financière

```dax
VaR Churn Total (TND) =
CALCULATE(
    SUM(FACT_ACCOUNT_EVENT[ACCT_BALANCE]),
    FACT_ACCOUNT_EVENT[churn] = 1
)

VaR Churn Corporate =
CALCULATE(
    SUM(FACT_ACCOUNT_EVENT[ACCT_BALANCE]),
    FACT_ACCOUNT_EVENT[churn] = 1,
    DIM_CLIENT[PARTYCLASS] = "Corporate"
)

VaR Churn KYC Eleve =
CALCULATE(
    SUM(FACT_ACCOUNT_EVENT[ACCT_BALANCE]),
    FACT_ACCOUNT_EVENT[churn] = 1,
    DIM_CLIENT[SCORE_KYC] IN {"H2", "H3"}
)

VaR Churn Deposits =
CALCULATE(
    SUM(FACT_ACCOUNT_EVENT[ACCT_BALANCE]),
    FACT_ACCOUNT_EVENT[churn] = 1,
    DIM_PRODUCT[PRODUCT_LINE] = "DEPOSITS"
)
```

---

## KPI-N4 — Durée moyenne avant churn (Time-to-Churn)

```dax
-- acct_tenure_days est directement disponible dans FACT_ACCOUNT_EVENT
Duree Moyenne Avant Churn (Annees) =
CALCULATE(
    AVERAGEX(FACT_ACCOUNT_EVENT, FACT_ACCOUNT_EVENT[acct_tenure_days] / 365),
    FACT_ACCOUNT_EVENT[churn] = 1
)

Duree Churn par Segment =
CALCULATE(
    [Duree Moyenne Avant Churn (Annees)],
    ALLEXCEPT(FACT_ACCOUNT_EVENT, DIM_CLIENT[PARTYCLASS])
)

Duree Churn par Produit =
CALCULATE(
    [Duree Moyenne Avant Churn (Annees)],
    ALLEXCEPT(FACT_ACCOUNT_EVENT, DIM_PRODUCT[PRODUCT_LINE])
)
```

---

## KPI-N5 — Score de risque composite (Churn Risk Index)

```dax
Risk Score Brut =
VAR kyc_score =
    SWITCH(DIM_CLIENT[SCORE_KYC],
        "LR", 0, "MR", 1, "H1", 2, "H2", 3, "H3", 4, 0)
VAR segment_score =
    SWITCH(DIM_CLIENT[PARTYCLASS],
        "Retail", 1, "Corporate Small", 1, "Elite", 2, "Corporate", 4, 0)
VAR file_score =
    IF(DIM_CLIENT[COMPLETED_FILE] = "YES", 0, 1)
VAR product_score =
    SWITCH(DIM_PRODUCT[PRODUCT_LINE],
        "DEPOSITS", 3, "LENDING", 2, "ACCOUNTS", 0, 0)
RETURN
    kyc_score + segment_score + file_score + product_score

Churn Risk Category =
SWITCH(TRUE(),
    [Risk Score Brut] >= 7, "Risque Élevé",
    [Risk Score Brut] >= 4, "Risque Moyen",
    "Risque Faible"
)

Nb Clients Risque Eleve =
CALCULATE(
    DISTINCTCOUNT(FACT_ACCOUNT_EVENT[client_key]),
    [Churn Risk Category] = "Risque Élevé"
)

VaR Risque Eleve (TND) =
CALCULATE(
    SUM(FACT_ACCOUNT_EVENT[ACCT_BALANCE]),
    [Churn Risk Category] = "Risque Élevé"
)
```

---

## Mesures utilitaires (support pour tous les KPIs)

```dax
Nb Total Comptes =
COUNTROWS(FACT_ACCOUNT_EVENT)

Nb Comptes Churned =
CALCULATE(COUNTROWS(FACT_ACCOUNT_EVENT), FACT_ACCOUNT_EVENT[churn] = 1)

Nb Comptes Actifs =
CALCULATE(COUNTROWS(FACT_ACCOUNT_EVENT), FACT_ACCOUNT_EVENT[churn] = 0)

Nb Clients Distincts =
DISTINCTCOUNT(FACT_ACCOUNT_EVENT[client_key])

Solde Total Portefeuille =
SUM(FACT_ACCOUNT_EVENT[ACCT_BALANCE])

Churn Voluntaire % =
DIVIDE(
    CALCULATE(COUNTROWS(FACT_ACCOUNT_EVENT),
        FACT_ACCOUNT_EVENT[churn] = 1,
        DIM_CLOSURE[is_voluntary] = TRUE()
    ),
    CALCULATE(COUNTROWS(FACT_ACCOUNT_EVENT), FACT_ACCOUNT_EVENT[churn] = 1)
) * 100

Churn par Raison =
DIVIDE(
    CALCULATE(COUNTROWS(FACT_ACCOUNT_EVENT), FACT_ACCOUNT_EVENT[churn] = 1),
    COUNTROWS(FACT_ACCOUNT_EVENT)
) * 100
-- Utiliser avec DIM_CLOSURE[CLOSURE_REASON] ou DIM_CLOSURE[closure_category] en axe

Churn par Region =
DIVIDE(
    CALCULATE(COUNTROWS(FACT_ACCOUNT_EVENT), FACT_ACCOUNT_EVENT[churn] = 1),
    COUNTROWS(FACT_ACCOUNT_EVENT)
) * 100
-- Utiliser avec DIM_BRANCH[region] en axe

Churn par Trimestre =
CALCULATE(
    COUNTROWS(FACT_ACCOUNT_EVENT),
    FACT_ACCOUNT_EVENT[churn] = 1
)
-- Utiliser avec DIM_DATE[quarter] et DIM_DATE[year] en axe
```
