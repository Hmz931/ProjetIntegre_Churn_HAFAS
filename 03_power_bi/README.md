# 03_power_bi/

**Hors scope de cette régénération automatique** (décision explicite : pas de Power BI
produit par l'assistant).

## Ce qui est déjà disponible pour démarrer ce dossier

Les KPIs métier nécessaires aux dashboards sont déjà calculés et documentés dans
`01_etl/notebooks/02_ETL.ipynb` (section 3), à partir des tables produites par le
pipeline ETL :

- Taux de churn global, par segment client, par ligne de produit, par score KYC.
- Taux de churn par secteur d'activité réel (`dim_INDUSTRY`) et par motif de clôture
  réel (`dim_Closure_reason`) — nouveauté apportée par l'intégration des dimensions xlsx.

## À faire par l'équipe

- [ ] Connecter Power BI Desktop à PostgreSQL (une fois `02_data_warehouse/` validé) ou
      directement aux fichiers exportés depuis le pipeline ETL.
- [ ] Construire au minimum les 3 pages demandées par la documentation (vue d'ensemble,
      analyse du churn, segmentation client) — voir `00_documentation/4_guide_etudiant.md`,
      étape 4.
- [ ] Définir les mesures DAX correspondant aux KPIs déjà identifiés.
