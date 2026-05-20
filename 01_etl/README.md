# 01 — ETL

Placez ici tout ce qui concerne l'**Extract – Transform – Load** :

- Notebook(s) d'exploration des données (EDA).
- Scripts Python du pipeline ETL (extraction, nettoyage, jointures, dérivation de features).
- Schéma du pipeline (diagramme).
- Tests de cohérence sur les données transformées.

## Structure suggérée

```
01_etl/
├── notebooks/
│   └── 01_exploration.ipynb
├── src/
│   ├── extract.py
│   ├── transform.py
│   └── load.py
├── pipeline.py          # orchestrateur principal
└── README.md            # ce fichier
```
