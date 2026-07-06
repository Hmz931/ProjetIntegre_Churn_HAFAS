# Documentation : Analyse Exploratoire des Données — Churn Bancaire

> **Notebook** : `01_exploration.ipynb`  
> **Langage** : Python 3  
> **Bibliothèques principales** : `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`  
> **Nombre de cellules** : 45 (markdown + code)

---

## Objectif du notebook

Ce notebook constitue la première phase d'un projet de **prédiction du churn bancaire**. Il explore le jeu de données `data_churn.csv`, qui contient des informations sur des comptes bancaires (caractéristiques clients, caractéristiques de compte, statut). L'objectif est d'identifier les facteurs associés à la **fermeture de compte** (`ACCOUNT_STATUS = Closed`), assimilée au churn.

---

## Structure générale

| Section | Titre | Type |
|---------|-------|------|
| 1 | Importation des bibliothèques | Setup |
| 2 | Chargement des données | Ingestion |
| 3 | Aperçu des données et types | Exploration initiale |
| 4 | Analyse des valeurs manquantes | Qualité des données |
| 5 | Analyse de la variable cible `ACCOUNT_STATUS` | Variable cible |
| 6 | Analyse univariée des variables numériques | EDA quantitative |
| 7 | Analyse univariée des variables catégorielles | EDA qualitative |
| 8 | Relation churn / variables | Analyse bivariée |
| 9 | Matrice de corrélation | Analyse multivariée |
| 10 | Analyse temporelle | Dimension temporelle |

---

## Section 1 — Importation des bibliothèques

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
```

**Configurations globales :**
- Suppression des warnings avec `warnings.filterwarnings('ignore')`
- Désactivation de la notation scientifique : `pd.set_option("display.float_format", "{:.2f}".format)`
- Style des graphiques : `sns.set_style('whitegrid')`, taille par défaut `(12, 6)`, police `12`
- Affichage inline avec `%matplotlib inline`

---

## Section 2 — Chargement des données

```python
df = pd.read_csv("../../data/data_churn.csv", sep=",")
```

Le fichier est lu depuis un chemin relatif. Le notebook affiche :
- Le nombre de lignes (`df.shape[0]`)
- Le nombre de colonnes (`df.shape[1]`)
- Un aperçu via `df.head()`

---

## Section 3 — Aperçu des données et types

Trois niveaux d'inspection sont réalisés :

1. **`df.info()`** — types de données, présence de valeurs nulles, usage mémoire
2. **`df.describe()`** — statistiques descriptives des colonnes numériques (min, max, moyenne, écart-type, quartiles)
3. **`df.describe(include=['object']).T`** — statistiques des colonnes catégorielles (compte, unique, top, freq), transposées pour une meilleure lisibilité

---

## Section 4 — Analyse des valeurs manquantes

### 4.1. Valeurs manquantes par colonne

```python
missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(2)
```

- Création d'un DataFrame `missing_df` listant les colonnes avec au moins une valeur manquante, triées par pourcentage décroissant
- **Heatmap** via `sns.heatmap(df.isnull(), ...)` : visualise la structure des NaN sur l'ensemble du dataset (jaune = manquant, violet = présent)
- **Barplot horizontal** des 15 colonnes les plus lacunaires, avec palette `Reds_r`

### 4.2. Distribution des valeurs manquantes par ligne

```python
row_missing_count = df.isnull().sum(axis=1)
```

- **Histogramme** du nombre de NaN par ligne (axe X : nb de NaN, axe Y : nb de lignes)
- Affichage du nombre de lignes avec au moins un NaN vs sans aucun NaN

### 4.3. Analyse des doublons

Trois niveaux d'analyse :

| Contrôle | Méthode |
|----------|---------|
| Doublons stricts (toutes colonnes) | `df.duplicated()` |
| Doublons sur clés (`CUSTOMER_NO`, `ACCOUNT_NO`) | `df.duplicated(subset=key_cols, keep=False)` |
| Détail d'un groupe doublon | Filtrage par `CUSTOMER_NO` + `ACCOUNT_NO` |

---

## Section 5 — Variable cible : `ACCOUNT_STATUS`

```python
status_counts = df['ACCOUNT_STATUS'].value_counts()
```

- **Tableau** : effectifs et pourcentages par modalité
- **Camembert** : proportion des statuts (`Active` vs `Closed`) avec `plt.pie()`
- Les comptes `Closed` = **événement de churn**

---

## Section 6 — Analyse univariée des variables numériques

### 6.1. Distribution des âges (`DATE_OF_BIRTH`)

```python
def age_from_date_of_birth(dob):
    year = int(str(dob)[:4])
    return 2026 - year  # année de référence
```

- Calcul de l'âge approximatif à partir de la date de naissance au format `AAAAMMJJ`
- **Histogramme + KDE** avec `sns.histplot(..., kde=True)`
- Affichage de l'âge moyen et médian
- Détection d'anomalies : clients avec `DATE_OF_BIRTH < 1900` (valeurs aberrantes probables)

### 6.2. Distribution du `SCORE_KYC`

**Interprétation métier du score :**

| Code | Signification |
|------|--------------|
| `LR` | Low Risk — clients standards, sources de revenus claires |
| `MR` | Medium Risk — vigilance accrue, pas d'alerte majeure |
| `H1` | High Risk (niveau 1) — le moins critique parmi les H |
| `H2` | High Risk (niveau 2) |
| `H3` | High Risk (niveau 3) — le plus sévère, peut inclure des PEP ou zones sensibles |

**Analyses :**
- `sns.countplot` pour la répartition des modalités
- **Matrice de contingence** `pd.crosstab(SCORE_KYC, ACCOUNT_STATUS)` en effectifs et en %
- **Barres empilées** de la proportion de statuts par niveau KYC
- **Barplot** du taux de churn (% de comptes fermés) par niveau KYC

### 6.3. Distribution du `SALARY`

Analyse approfondie en 5 étapes :

1. **Statistiques descriptives** avec percentiles détaillés : P1, P5, P10, P25, P50, P75, P90, P95, P99
2. **Quantiles** imprimés individuellement
3. **Détection des outliers par méthode IQR** :
   - `Q1 - 1.5 * IQR` → borne inférieure
   - `Q3 + 1.5 * IQR` → borne supérieure
   - Nombre et pourcentage d'outliers détectés
4. **Visualisations en 4 sous-graphiques** (`2×2`) :
   - Histogramme + KDE (distribution brute)
   - Boxplot (avec outliers)
   - Boxplot sans outliers (distribution centrale)
   - **QQ-plot** via `scipy.stats.probplot` (test de normalité)
5. **Comparaison salaire vs statut de compte** : boxplot `SALARY` par `ACCOUNT_STATUS`

### 6.4. Distribution du `ACCT_BALANCE`

```python
sns.histplot(df['ACCT_BALANCE'].dropna(), bins=50, kde=True, color='green')
```

- Histogramme + KDE du solde des comptes
- Affichage du solde moyen et médian (formatés à 5 décimales)

---

## Section 7 — Analyse univariée des variables catégorielles

Variables analysées dans une grille `2×3` :

| Variable | Description |
|----------|-------------|
| `MARITAL_STATUS` | Situation matrimoniale du client |
| `NATURE_CLIENT` | Nature/type de client |
| `ACCOUNT_TYPE_DESC` | Description du type de compte |
| `PRODUCT_STATUS` | Statut du produit |
| `INDUSTRY` | Secteur d'activité |
| `PARTYCLASS` | Classe de la contrepartie |

Chaque sous-graphique affiche les **10 modalités les plus fréquentes** sous forme de barplot horizontal avec palette `viridis`.

---

## Section 8 — Analyse bivariée : Churn vs Variables

### 8.1. Churn par statut marital

```python
churn_by_marital = df.groupby('MARITAL_STATUS')['ACCOUNT_STATUS'].apply(
    lambda x: (x == 'Closed').mean() * 100
)
```

Barplot du taux de churn (%) par modalité de `MARITAL_STATUS`.

### 8.2. Churn par `NATURE_CLIENT`

Barplot du taux de churn trié par ordre décroissant pour les différents groupes de produits/natures clients.

### 8.3. Churn par `INDUSTRY`

Analyse des 50 industries avec le plus fort taux de churn, affichées en barplot horizontal avec rotation des étiquettes.

### 8.4. Distribution de l'âge selon le statut

```python
sns.boxplot(data=df, x='ACCOUNT_STATUS', y='AGE', palette='Set3')
```

- Boxplot comparatif `AGE` vs `ACCOUNT_STATUS`
- Tableau de statistiques descriptives (min, max, moyenne, écart-type, quartiles) de l'âge par statut

### 8.5. Solde moyen selon le statut

```python
sns.boxplot(data=df, x='ACCOUNT_STATUS', y='ACCT_BALANCE', palette='Set2')
plt.yscale('log')
```

- Boxplot `ACCT_BALANCE` vs `ACCOUNT_STATUS` en **échelle logarithmique** (gestion des valeurs extrêmes)
- Tableau de statistiques descriptives du solde par statut

---

## Section 9 — Matrice de corrélation

> ⚠️ Cette section est mentionnée dans les titres markdown mais **ne contient pas de code** dans le notebook actuel. Elle constitue une étape à implémenter.

---

## Section 10 — Analyse temporelle

### 10.1. Évolution des ouvertures de comptes

```python
df['OPENING_YEAR'] = pd.to_numeric(df['ACCT_OPENING_DATE'].astype(str).str[:4], errors='coerce')
openings_by_year = df.groupby('OPENING_YEAR')['ACCOUNT_NO'].count()
```

- Extraction de l'année depuis `ACCT_OPENING_DATE` (format `AAAAMMJJ`)
- Barplot du nombre d'ouvertures de comptes par année (couleur `mediumseagreen`)

### 10.2. Taux de churn par année d'ouverture

```python
df['YEAR_OPENING'] = df['ACCT_OPENING_DATE'].dropna().astype(str).str[:4]
churn_by_open_year = df.groupby('YEAR_OPENING')['ACCOUNT_STATUS'].apply(
    lambda x: (x == 'Closed').mean() * 100
)
```

- Barplot du taux de churn (%) par année d'ouverture (couleur `salmon`)
- Permet d'identifier des **cohortes** plus ou moins susceptibles au churn selon leur ancienneté

---

## Variables clés identifiées

| Variable | Type | Rôle |
|----------|------|------|
| `ACCOUNT_STATUS` | Catégorielle | **Variable cible** (Closed = churn) |
| `CUSTOMER_NO` | Identifiant | Numéro client |
| `ACCOUNT_NO` | Identifiant | Numéro de compte |
| `DATE_OF_BIRTH` | Numérique (AAAAMMJJ) | Calcul de l'âge |
| `SCORE_KYC` | Catégorielle ordinale | Niveau de risque de conformité |
| `SALARY` | Numérique | Salaire déclaré |
| `ACCT_BALANCE` | Numérique | Solde du compte |
| `MARITAL_STATUS` | Catégorielle | Situation matrimoniale |
| `NATURE_CLIENT` | Catégorielle | Nature/type de client |
| `ACCOUNT_TYPE_DESC` | Catégorielle | Type de compte |
| `PRODUCT_STATUS` | Catégorielle | Statut du produit |
| `INDUSTRY` | Catégorielle | Secteur d'activité |
| `PARTYCLASS` | Catégorielle | Classe de contrepartie |
| `ACCT_OPENING_DATE` | Numérique (AAAAMMJJ) | Date d'ouverture du compte |

---

## Points méthodologiques notables

- **Année de référence 2026** utilisée pour le calcul d'âge à partir de `DATE_OF_BIRTH`
- **Outliers** détectés par méthode IQR sur `SALARY` ; visualisés avant/après exclusion
- **Échelle logarithmique** appliquée sur `ACCT_BALANCE` pour neutraliser les valeurs extrêmes
- **Analyse KYC** : les scores `H` (haut risque) ferment souvent plus tard ou présentent des soldes négatifs
- **Doublons** vérifiés à deux niveaux : strict (toutes colonnes) et sur les clés (`CUSTOMER_NO`, `ACCOUNT_NO`)
- La **matrice de corrélation** (Section 9) est déclarée mais non implémentée dans ce notebook

---

## Prochaines étapes suggérées

1. Implémenter la matrice de corrélation (Section 9)
2. Traitement des valeurs manquantes (imputation ou suppression selon le taux et l'importance de la variable)
3. Gestion des outliers identifiés dans `SALARY`
4. Correction des anomalies de `DATE_OF_BIRTH` (valeurs < 1900)
5. Encodage des variables catégorielles pour la modélisation
6. Construction d'un modèle de classification (churn = `Closed`)
