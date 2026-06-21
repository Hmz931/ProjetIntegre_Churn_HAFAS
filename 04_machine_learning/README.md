# 04 — Machine Learning

Placez ici tout ce qui concerne la **modélisation prédictive du churn** :

- Notebooks de préparation, d'entraînement et d'évaluation.
- Scripts d'entraînement réutilisables.
- Modèle final sauvegardé (`.pkl` ou `.joblib`) — **à exclure du repo s'il est volumineux**.
- Tableau comparatif des modèles testés.
- Analyses d'interprétabilité (importance des features, SHAP).

## Contenu minimum attendu

- **Au moins 3 modèles** comparés (par ex. : régression logistique, Random Forest, XGBoost).
- Métriques adaptées au déséquilibre : precision, recall, F1, ROC-AUC, PR-AUC.
- Justification du modèle final retenu.

## Structure suggérée

```
04_machine_learning/
├── notebooks/
│   ├── 01_preparation.ipynb
│   ├── 02_entrainement.ipynb
│   └── 03_evaluation.ipynb
├── src/
│   └── train.py
├── models/
│   └── model_final.pkl   # exclu du repo si trop volumineux
├── comparison.md         # tableau comparatif des modèles
└── README.md
```
