# 03 — Power BI

Placez ici les livrables Power BI :

- Le fichier `.pbix` (attention : à exclure du repo s'il contient des données sensibles ; voir `.gitignore`).
- Des captures d'écran des pages du rapport.
- La documentation des mesures DAX et de la source de données.

## Contenu minimum attendu

Au moins **3 pages** dans le rapport Power BI :
1. **Vue d'ensemble** — KPIs clés, taux de churn global.
2. **Analyse du churn** — segmentation par âge, secteur, ancienneté, produit.
3. **Segmentation client** — profils et identification des comptes à risque.

## Structure suggérée

```
03_power_bi/
├── rapport.pbix         # NE PAS COMMITER si contient des données
├── screenshots/
│   ├── page1_overview.png
│   ├── page2_churn.png
│   └── page3_segments.png
├── measures_dax.md      # documentation des mesures
└── README.md
```
