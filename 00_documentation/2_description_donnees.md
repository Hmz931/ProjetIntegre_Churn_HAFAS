# Description des Données

Les données mises à votre disposition proviennent du système d'information d'une institution bancaire. Elles ont été **anonymisées** : aucun identifiant personnel direct n'est exploitable, mais elles conservent leur structure et leur cohérence métier réelle.

## 1. Vue d'ensemble

Le jeu de données est composé de :

- **1 fichier de données principal** au format CSV (~130 Mo, plusieurs centaines de milliers de lignes) contenant les informations clients, comptes et produits.
- **8 tables de dimensions** au format Excel (`.xlsx`) qui donnent le libellé descriptif associé aux codes présents dans le fichier principal.

Chaque ligne du fichier principal correspond à un **couple (client, compte produit)** : un même client peut donc apparaître plusieurs fois s'il possède plusieurs comptes.

## 2. Fichier principal — Description des colonnes

### 2.1 Identifiants
| Colonne | Type | Description |
|---|---|---|
| `CUSTOMER_NO` | Numérique | Identifiant unique du client |
| `ACCOUNT_NO` | Numérique | Identifiant unique du compte |
| `BRANCH` | Code | Agence de rattachement |

### 2.2 Informations client
| Colonne | Type | Description |
|---|---|---|
| `NATIONALITY` | Code ISO | Nationalité du client |
| `RESIDENCE` | Code ISO | Pays de résidence |
| `MARITAL_STATUS` | Code | Statut marital (C = célibataire, M = marié(e), D = divorcé(e), V = veuf/veuve) |
| `DATE_OF_BIRTH` | Date (YYYYMMDD) | Date de naissance |
| `CUST_OPENING_DATE` | Date (YYYYMMDD) | Date d'entrée en relation avec la banque |
| `NATURE_CLIENT` | Code | Type de client (personne physique, personne morale, etc.) |
| `PARTYCLASS` | Code | Classification commerciale (Retail, Corporate, etc.) |
| `LOB` | Code | Ligne métier (Line of Business) |
| `SCORE_KYC` | Code | Score de connaissance client (Know Your Customer) |
| `COMPLETED_FILE` | Booléen (YES/NO) | Dossier client complet |
| `LAST_REVIEW_DATE` | Date | Date de dernière revue du dossier |
| `NEXT__REVIEW_DATE` | Date | Date de prochaine revue prévue |
| `INDUSTRY` | Code | Secteur d'activité du client (FK vers `dim_INDUSTRY`) |
| `SALARY` | Numérique | Salaire ou revenu déclaré |

### 2.3 Informations compte
| Colonne | Type | Description |
|---|---|---|
| `ACCOUNT_STATUS` | Texte | Statut du compte (`Active`, `Closed`, etc.) — **variable cible pour le churn** |
| `ACCT_OPENING_DATE` | Date | Date d'ouverture du compte |
| `ACCT_CLOSE_DATE` | Date | Date de clôture du compte (si applicable) |
| `ACCOUNT_CATEGORY` | Code | Catégorie du compte (FK vers `dim_CATEGORY.ACCOUNT`) |
| `ACCOUNT_TYPE_DESC` | Texte | Description du type de compte |
| `CURRENCY` | Code ISO | Devise du compte (FK vers `dim_CURRENCY`) |
| `CLOSURE_REASON` | Code | Motif de clôture (FK vers `dim_Closure_reason`) |
| `ACCT_BALANCE` | Numérique | Solde du compte |

### 2.4 Informations produit
| Colonne | Type | Description |
|---|---|---|
| `PRODUCT_GROUP` | Code | Groupe de produits |
| `PRODUCT_LINE` | Code | Ligne de produits |
| `PRODUCT` | Code | Produit spécifique |
| `ACCOUNTNATURE` | Texte | Nature du produit |
| `STARTDATE` | Date | Date de début du produit |
| `MATURITYDATE` | Date | Date d'échéance |
| `AMOUNT` | Numérique | Montant du produit (crédit, dépôt, etc.) |
| `FIXEDRATE` | Numérique | Taux fixe associé |
| `PRODUCT_STATUS` | Texte | Statut du produit |

## 3. Tables de dimensions

Les fichiers `dim_*.xlsx` fournissent les libellés descriptifs associés aux codes du fichier principal. Elles sont à utiliser pour enrichir les données lors de la phase ETL.

| Fichier | Clé | Contenu |
|---|---|---|
| `dim_CATEGORY.ACCOUNT.xlsx` | `CATEGORY_id` | Description des catégories de compte |
| `dim_CURRENCY.xlsx` | Code devise | Description des devises |
| `dim_Closure_reason.xlsx` | `RECID` | Motifs de clôture de compte |
| `dim_DAO.xlsx` | Code | Référentiel DAO |
| `dim_INDUSTRY.xlsx` | `INDUSTRY_CODE` | Secteurs d'activité économique |
| `dim_SECTOR.xlsx` | Code | Secteurs détaillés |
| `dim_TARGET.xlsx` | Code | Segmentation cible client |
| `dim_TRANSACTION.xlsx` | Code | Référentiel de types de transactions |

## 4. Définition de la variable cible (churn)

Le **churn** se définit ici comme la **clôture d'un compte client**. La variable cible peut être construite à partir de la colonne `ACCOUNT_STATUS` :

```
churn = 1  si  ACCOUNT_STATUS contient "Closed"
churn = 0  sinon
```

Vous pouvez aussi proposer une définition plus fine (par exemple : churn d'un client = clôture de **tous** ses comptes), à justifier dans le rapport.

## 5. Variables potentiellement intéressantes pour le ML

Quelques pistes (non exhaustives) à explorer :

- **Variables démographiques** : âge (à calculer depuis `DATE_OF_BIRTH`), statut marital, nationalité.
- **Variables d'ancienneté** : ancienneté du client (`CUST_OPENING_DATE`), ancienneté du compte (`ACCT_OPENING_DATE`).
- **Variables financières** : solde (`ACCT_BALANCE`), salaire (`SALARY`), montant du produit (`AMOUNT`).
- **Variables comportementales** : nombre de comptes par client, diversité des produits détenus, secteur d'activité, segment commercial.
- **Variables de conformité** : score KYC, dossier complet ou non, ancienneté de la dernière revue.

## 6. Qualité des données — points d'attention

Le jeu de données est issu d'un système opérationnel réel. Vous rencontrerez donc :

- Des **valeurs manquantes** dans plusieurs colonnes (`SALARY`, `INDUSTRY`, dates, etc.).
- Des **valeurs `NULL` textuelles** à distinguer des `NaN`.
- Des **dates au format `YYYYMMDD` numérique** à convertir.
- Des **incohérences** possibles (dates de clôture sans statut `Closed`, soldes négatifs, etc.).
- Un **déséquilibre de classes** entre comptes actifs et clos qu'il faudra prendre en compte dans le modèle ML.

Une phase de **profilage et d'analyse exploratoire** est donc indispensable avant toute modélisation.

## 7. Volumétrie indicative

- Fichier principal : ~130 Mo, plusieurs centaines de milliers de lignes.
- Tables de dimensions : entre 6 ko et 80 ko chacune.

La volumétrie est suffisamment importante pour justifier une approche structurée (Pandas avec chunks, ou base de données analytique), mais reste manipulable sur une machine standard.

## 8. Précautions

- **Ne pas publier les données** sur GitHub ou tout autre dépôt public.
- **Ne pas mentionner** l'origine des données dans aucun livrable.
- Utiliser un `.gitignore` qui exclut au minimum : `*.csv`, `*.xlsx`, `*.pkl`, `data/`.
