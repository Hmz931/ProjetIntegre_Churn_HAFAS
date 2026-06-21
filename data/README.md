# data/

Ce dossier contient le **jeu de données anonymisé** fourni avec le projet.

## ⚠️ Important : Git LFS requis

Les fichiers volumineux (`data_churn.csv`, ~110 Mo) sont stockés via **Git LFS**.
Avant de cloner ce dépôt, vous **devez** installer Git LFS :

```bash
# Installation (une seule fois sur votre poste)
# Windows : https://git-lfs.com/  -> télécharger et installer
# Linux   : sudo apt install git-lfs
# macOS   : brew install git-lfs

git lfs install
```

Ensuite, clonez normalement :

```bash
git clone https://github.com/Aymenbenbrik/ProjetIntegre.git
```

Si vous avez cloné **avant** d'installer Git LFS, récupérez les fichiers réels avec :

```bash
git lfs pull
```

## Contenu du dossier

| Fichier | Format | Description |
|---|---|---|
| `data_churn.csv` | CSV (~110 Mo) | Données principales : clients, comptes et produits anonymisés |
| `dim_CATEGORY.ACCOUNT.xlsx` | Excel | Référentiel des catégories de compte |
| `dim_Closure_reason.xlsx` | Excel | Motifs de clôture de compte |
| `dim_CURRENCY.xlsx` | Excel | Devises |
| `dim_DAO.xlsx` | Excel | Référentiel DAO |
| `dim_INDUSTRY.xlsx` | Excel | Secteurs d'activité |
| `dim_SECTOR.xlsx` | Excel | Secteurs détaillés |
| `dim_TARGET.xlsx` | Excel | Segmentation cible |
| `dim_TRANSACTION.xlsx` | Excel | Référentiel de transactions |
| `anonymize.py` | Script Python | Script qui a généré ce jeu (à titre informatif) |

La description détaillée des colonnes figure dans `00_documentation/2_description_donnees.md`.

## Anonymisation appliquée

Le jeu de données distribué est **anonymisé**. Les transformations suivantes ont été appliquées au fichier source :

1. Tous les codes internes propriétaires ont été renommés en `BANK.*`.
2. `CUSTOMER_NO` → identifiants séquentiels `C000001`, `C000002`, …
3. `ACCOUNT_NO` → identifiants séquentiels `A0000001`, …
4. `BRANCH` → codes renumérotés aléatoirement `BR01`, `BR02`, …
5. `DATE_OF_BIRTH` → conservé uniquement l'**année** de naissance.
6. Volumétrie : **528 883 lignes**, 34 colonnes.

Aucune information directement identifiable (nom, email, téléphone, IBAN, CIN) n'est présente.

## Règles d'usage

- Ces données sont fournies **pour un usage pédagogique uniquement**.
- Ne les redistribuez pas en dehors du cadre du projet.
- N'essayez pas de ré-identifier les clients sous-jacents.
