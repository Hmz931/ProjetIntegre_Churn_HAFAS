# KPIs Métier — Analyse du Churn Bancaire

> Basé sur le fichier `data_churn.txt` (528 883 lignes, 34 colonnes)

---

## Variable cible (Y)

| Colonne | Valeur churn | Valeur actif |
|---|---|---|
| `ACCOUNT_STATUS` | `Closed` → 1 | `Active` → 0 |

```python
df['ACCOUNT_STATUS'] = (df['ACCOUNT_STATUS'] == 'Closed').astype(int)
```

---

## KPI 01 — Taux de churn global

**Pourquoi :** KPI central du projet. Mesure le pourcentage de clients perdus sur le portefeuille total.

**Colonne source :** `ACCOUNT_STATUS`

**Calcul :**
```python
taux_churn = df['ACCOUNT_STATUS'].mean() * 100
# Résultat : 42.0%
```

---

## KPI 02 — Ancienneté moyenne client

**Pourquoi :** Identifie si les clients anciens churned plus que les nouveaux. Signal contre-intuitif : les clients 20+ ans churned à 55.8%.

**Colonne source :** `CUST_OPENING_DATE` (format `YYYYMMDD.0`)

**Calcul :**
```python
df['tenure_years'] = 2026 - (df['CUST_OPENING_DATE'].astype(int) // 10000)
df.groupby('ACCOUNT_STATUS')['tenure_years'].mean()
# Churned : 13.6 ans | Actifs : 11.6 ans
```

---

## KPI 03 — Âge moyen du client

**Pourquoi :** Segmentation démographique. Les 31–40 ans et les 60+ ans présentent les taux de churn les plus élevés.

**Colonne source :** `DATE_OF_BIRTH` (année de naissance)

**Calcul :**
```python
df['age'] = 2026 - df['DATE_OF_BIRTH']
df['age'] = df['age'].where(df['age'].between(18, 100))

# Segmentation par tranche
bins = [18, 30, 40, 50, 60, 100]
labels = ['18-30', '31-40', '41-50', '51-60', '60+']
df['age_group'] = pd.cut(df['age'], bins=bins, labels=labels)
df.groupby('age_group', observed=True)['ACCOUNT_STATUS'].mean() * 100
```

---

## KPI 04 — Solde moyen par statut

**Pourquoi :** Mesure la valeur financière des clients qui partent vs ceux qui restent. Les clients churned ont un solde moyen positif (14 768 TND) — ce sont les meilleurs clients qui s'en vont.

**Colonne source :** `ACCT_BALANCE`

**Calcul :**
```python
df.groupby('ACCOUNT_STATUS')['ACCT_BALANCE'].mean()
df.groupby('ACCOUNT_STATUS')['ACCT_BALANCE'].median()
# Churned : 14 768 TND | Actifs : -384 TND
```

---

## KPI 05 — Salaire moyen par statut

**Pourquoi :** Profil de revenus des clients churned vs actifs. Les clients à revenus élevés partent plus — probablement vers la concurrence.

**Colonne source :** `SALARY`

**Calcul :**
```python
df.groupby('ACCOUNT_STATUS')['SALARY'].mean()
df.groupby('ACCOUNT_STATUS')['SALARY'].describe()
# Churned : 8 958 TND | Actifs : 3 590 TND
```

---

## KPI 06 — Taux de churn par segment client

**Pourquoi :** Chaque segment a un profil de risque différent. Les Corporate churned à 84.7% — priorité absolue de rétention.

**Colonne source :** `PARTYCLASS`

Valeurs : `Retail`, `Corporate`, `Elite`, `Corporate Small`

**Calcul :**
```python
df.groupby('PARTYCLASS')['ACCOUNT_STATUS'].agg(['mean', 'count'])
# Corporate      : 84.7%
# Elite          : 59.8%
# Corporate Small: 34.6%
# Retail         : 35.2%
```

---

## KPI 07 — Taux de churn par ligne de produit

**Pourquoi :** Révèle quels produits bancaires sont liés aux départs. Les dépôts à terme ferment à 96% à l'échéance — produit à très faible rétention.

**Colonnes sources :** `PRODUCT_LINE`, `PRODUCT_GROUP`

Valeurs `PRODUCT_LINE` : `ACCOUNTS`, `LENDING`, `DEPOSITS`, `SAFE.DEPOSIT.BOX`

**Calcul :**
```python
df.groupby('PRODUCT_LINE')['ACCOUNT_STATUS'].mean() * 100
df.groupby('PRODUCT_GROUP')['ACCOUNT_STATUS'].mean() * 100
# DEPOSITS : 96.2%
# LENDING  : 59.4%
# ACCOUNTS : 13.9%
```

---

## KPI 08 — Taux de churn par profil de risque KYC

**Pourquoi :** Corrélation directe entre niveau de risque réglementaire et churn. Plus le score est élevé, plus le client est susceptible de partir.

**Colonne source :** `SCORE_KYC`

Valeurs (ordre croissant de risque) : `LR` → `MR` → `H1` → `H2` → `H3`

**Calcul :**
```python
# Encodage ordinal pour les modèles ML
kyc_map = {'LR': 0, 'MR': 1, 'H1': 2, 'H2': 3, 'H3': 4}
df['kyc_risk'] = df['SCORE_KYC'].map(kyc_map)

# KPI descriptif
df.groupby('SCORE_KYC')['ACCOUNT_STATUS'].mean() * 100
# H3 : 71.1% | H1 : 61.7% | H2 : 44.2% | MR : 38.4% | LR : 37.1%
```

---

## KPI 09 — Tendance du churn dans le temps

**Pourquoi :** Montre si le phénomène s'accélère ou se stabilise. Le churn est en hausse depuis 2022.

**Colonne source :** `ACCT_CLOSE_DATE` (format `YYYYMMDD.0`)

> ⚠️ **ATTENTION :** Cette colonne est utilisée uniquement pour ce KPI descriptif. Elle ne doit **jamais** être incluse comme feature dans les modèles ML (data leakage).

**Calcul :**
```python
df['close_year'] = (df['ACCT_CLOSE_DATE'].dropna().astype(int) // 10000)
df[df['ACCOUNT_STATUS'] == 1].groupby('close_year').size()
# 2022 : 37 473
# 2023 : 43 716  (+16.7%)
# 2024 : 47 630  (+9.0%)
# 2025 : 41 219  (-13.5%)
# 2026 : 51 903  (en cours, tendance forte)
```

---

## KPI 10 — Complétude du dossier client

**Pourquoi :** Un dossier incomplet indique un client peu engagé ou un risque de résiliation forcée par la conformité.

**Colonne source :** `COMPLETED_FILE`

Valeurs : `YES` ou manquant (NaN)

**Calcul :**
```python
df['file_ok'] = (df['COMPLETED_FILE'] == 'YES').astype(int)
df.groupby('file_ok')['ACCOUNT_STATUS'].mean() * 100

# Taux de dossiers complets
taux_complet = (df['COMPLETED_FILE'] == 'YES').mean() * 100
```

---

## KPI 11 — Taux de churn par situation matrimoniale

**Pourquoi :** Les divorciés churned le plus (46.6%) — changement de situation financière. Les veufs/veuves sont les plus stables (31.8%).

**Colonne source :** `MARITAL_STATUS`

Valeurs : `M` (marié), `C` (célibataire), `D` (divorcé), `V` (veuf/ve)

**Calcul :**
```python
df.groupby('MARITAL_STATUS')['ACCOUNT_STATUS'].agg(['mean', 'count'])
# D (Divorcé)   : 46.6%
# M (Marié)     : 39.2%
# C (Célibataire): 36.9%
# V (Veuf/ve)   : 31.8%
```

---

## KPI 12 — Ratio solde / salaire (feature engineered)

**Pourquoi :** Indicateur de stress financier construit à partir de deux colonnes. Un ratio très négatif = endettement excessif = risque de départ élevé. Cette colonne n'existe pas dans le fichier brut — elle est créée.

**Colonnes sources :** `ACCT_BALANCE` + `SALARY`

**Calcul :**
```python
df['bal_sal_ratio'] = df['ACCT_BALANCE'] / (df['SALARY'] + 1)
df.groupby('ACCOUNT_STATUS')['bal_sal_ratio'].mean()
```

---

## Récapitulatif — colonnes sources par KPI

| KPI | Colonne(s) source | Usage ML |
|---|---|---|
| Taux de churn global | `ACCOUNT_STATUS` | Variable cible Y |
| Ancienneté client | `CUST_OPENING_DATE` | Feature |
| Âge client | `DATE_OF_BIRTH` | Feature |
| Solde moyen | `ACCT_BALANCE` | Feature |
| Salaire moyen | `SALARY` | Feature |
| Segment client | `PARTYCLASS` | Feature (encoder) |
| Produit bancaire | `PRODUCT_LINE`, `PRODUCT_GROUP` | Feature (encoder) |
| Risque KYC | `SCORE_KYC` | Feature (ordinal) |
| Tendance temporelle | `ACCT_CLOSE_DATE` | KPI descriptif uniquement |
| Dossier complet | `COMPLETED_FILE` | Feature (binaire) |
| Situation matrimoniale | `MARITAL_STATUS` | Feature (encoder) |
| Ratio solde/salaire | `ACCT_BALANCE` + `SALARY` | Feature engineered |

---

## Colonnes à exclure des modèles ML

| Colonne | Raison |
|---|---|
| `ACCT_CLOSE_DATE` | Data leakage — existe seulement après le churn |
| `CLOSURE_REASON` | Data leakage — label post-churn |
| `CUSTOMER_NO` / `ACCOUNT_NO` | Identifiants — aucune valeur prédictive |
| `NATIONALITY` / `RESIDENCE` | Variance nulle (tous TN dans le dataset) |
