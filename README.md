# Projet Intégré — Analyse et Prédiction du Churn Client

> **École** : ESPRIT School of Business
> **Programme** : Master 1 — Business Analytics (M1 BA)
> **Tuteur du projet** : Aymen Ben Brik
> **Équipe** : Hamza, Eya, Fares, Aïcha
> **Branche de travail** : `ETL_EyaFares`
> **Application Streamlit** : _(lien à renseigner une fois déployée — voir `05_web_app/README.md`)_


## État actuel du projet

| Phase | État |
|---|---|
| `00_documentation/` | ✅ Fournie par l'encadrant |
| `01_etl/` | ✅ Pipeline ETL complet (module Python orchestré), EDA documentée |
| `02_data_warehouse/` | ✅ Validé sur un vrai serveur PostgreSQL (7/7 tables chargées, contraintes appliquées) |
| `03_power_bi/` | ✅ 3 dashboards |
| `04_machine_learning/` | ✅ Fait|
| `05_web_app/` | ✅ Fait (`app.py` réservé à la racine) |
| `06_rapport/` | ✅ rédigé |
| `07_presentation/` | ✅ Préparée |

## Par où commencer

1. Lisez les documents du dossier **`00_documentation/`** dans l'ordre (description du
   projet, description des données, timeline, guide étudiant).
2. Placez les fichiers de données fournis séparément dans **`data/`** (voir
   `data/README.md` — ce dossier n'est pas versionné, conformément à la règle de
   confidentialité).
3. Installez les dépendances : `pip install -r requirements.txt`.
4. Lancez tout le pipeline ETL + chargement PostgreSQL en une commande, depuis la
   racine du projet :
   ```bash
   python run.py            # pipeline complet + chargement PostgreSQL
   python run.py --no-db    # pipeline complet, sans PostgreSQL (pour itérer rapidement)
   ```
5. Ouvrez `01_etl/notebooks/01_exploration.ipynb` puis `01_etl/notebooks/02_ETL.ipynb`
   pour l'exploration des données et l'exécution commentée du pipeline.

## Structure du dépôt

```
PROJETINTEGRE_CHURN_HAFAS/
├── 00_documentation/        Documents fournis par l'encadrant (ne pas modifier)
├── 01_etl/
│   ├── etl_pipeline/         Module Python — extract, clean, dimensions, fact, load
│   ├── notebooks/             01_exploration.ipynb, 02_ETL.ipynb, DW.svg
│   └── README.md              Documentation détaillée du pipeline et de ses décisions
├── 02_data_warehouse/
│   ├── schema/
│   │   └── create_tables.sql  DDL explicite des 7 tables (référence indépendante de SQLAlchemy)
│   ├── load/
│   │   └── load_warehouse.py  Point d'entrée du chargement (appelle 01_etl/etl_pipeline/)
│   ├── kpis.md                 KPIs métier en SQL (équivalent des KPIs pandas de 02_ETL.ipynb)
│   └── README.md
├── 03_power_bi/              
├── 04_machine_learning/      
├── 05_web_app/               
├── 06_rapport/               
├── 07_presentation/           
├── data/                      Données brutes (non versionnées, voir data/README.md)
├── run.py                     Point d'entrée : pipeline ETL complet + chargement DWH
├── app.py                     Stub réservé pour l'application web (05_web_app/)
├── requirements.txt
├── .gitignore
└── .gitattributes
```

## Définition du churn retenue

Conforme à `00_documentation/2_description_donnees.md`, section 4 :

```
churn = 1  si  ACCOUNT_STATUS == "Closed"
churn = 0  si  ACCOUNT_STATUS == "Active"
```

Calculée au niveau **compte** (`ACCOUNT_NO`), puis propagée sur tous les
événements de ce compte dans `FACT_ACCOUNT_EVENT` — voir `01_etl/README.md` pour le
détail de cette décision et sa vérification sur les données réelles.

## Règles importantes

- **Confidentialité** : les données ne doivent **pas** être publiées sur GitHub
  (`.gitignore` exclut `data/`). Seul le code peut être partagé publiquement.
- **Anonymat** : ne mentionnez ni le nom de l'institution source, ni d'éléments
  permettant de l'identifier, dans le code, le rapport ou la présentation. Le module
  `01_etl/etl_pipeline/dimension_lookup.py` retire automatiquement le nom de
  l'institution des libellés issus des fichiers `dim_*.xlsx` avant toute exposition.
- **Versioning** : chaque membre commite régulièrement sur sa branche.
- **Reproductibilité** : tout le pipeline ETL est ré-exécutable à partir de ce README,
  de `01_etl/README.md` et de `requirements.txt`.

## Composition de l'équipe

| Nom | Rôle principal  
|---|---
| Fares | ETL / ML 
| Eya | ETL / PowerBI
| Aïcha | ETL / POWER BI
| Hamza | ETL / ML
| Sahar | ETL / POWER BI