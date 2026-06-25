# 04_machine_learning/

**Hors scope de cette régénération automatique** — aucun notebook de modélisation n'a
été produit ici pour le moment (par décision explicite avec l'équipe).

## Ce qui est déjà disponible pour démarrer ce dossier

Le pipeline ETL (`01_etl/etl_pipeline/`) produit une table de faits directement
exploitable pour l'entraînement :

```python
import sys
sys.path.insert(0, "../01_etl")
from etl_pipeline.pipeline import run_pipeline

resultats = run_pipeline(load_to_db=False)  # pas besoin de PostgreSQL pour le ML
fact = resultats["fact_account_event"]       # variable cible : colonne 'churn'
dim_client = resultats["dimensions"]["dim_client"]
dim_account = resultats["dimensions"]["dim_account"]
```

Colonnes à exclure du jeu d'entraînement (data leakage ou absence de valeur prédictive),
voir `01_etl/notebooks/02_ETL.ipynb` section 3 : `ACCT_CLOSE_DATE`, `CLOSURE_REASON`,
`CUSTOMER_NO`/`ACCOUNT_NO`, `NATIONALITY`/`RESIDENCE` (quasi-constantes).

Un support de cours `Classification_Lab` (fourni par ailleurs, hors structure officielle
du dépôt) couvre déjà KNN, arbre de décision, Random Forest, SVM (linéaire et noyau),
régression logistique, GridSearchCV, et l'évaluation par courbe ROC/AUC — directement
transposable à ce jeu de données.

## À faire par l'équipe

- [ ] Notebook de préparation des features (encodage des catégorielles, gestion du
      déséquilibre de classes — signalé dans la documentation comme point d'attention).
- [ ] Entraînement et comparaison d'au moins 3 modèles (régression logistique en
      baseline + 2 autres, cf. `00_documentation/4_guide_etudiant.md` étape 5).
- [ ] Évaluation avec des métriques adaptées au déséquilibre (precision, recall, F1,
      ROC-AUC, PR-AUC — pas seulement l'accuracy).
- [ ] Sauvegarde du modèle final (`.pkl` ou `.joblib`).
