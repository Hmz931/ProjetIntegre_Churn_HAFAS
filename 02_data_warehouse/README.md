# 02 — Data Warehouse

Placez ici tout ce qui concerne le **modèle dimensionnel** et le Data Warehouse :

- Scripts SQL de création des tables (faits + dimensions).
- Scripts de chargement des données transformées.
- Diagramme du modèle en étoile.
- Documentation des KPIs et des règles de calcul.

## Structure suggérée

```
02_data_warehouse/
├── schema/
│   ├── create_tables.sql
│   └── star_schema.png
├── load/
│   └── load_warehouse.py
├── kpis.md              # liste et formule de chaque KPI
└── README.md
```
