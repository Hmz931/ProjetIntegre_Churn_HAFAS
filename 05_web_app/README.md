# 05_web_app/

Application **Streamlit** de restitution du modèle de churn — 4 pages (Accueil,
Prédiction, Dashboard KPI, À propos), branchée sur le pipeline `machine_learning2.ipynb`.

## État actuel

✅ **Fait** — `app.py` (465 lignes) + modèles entraînés déjà sérialisés dans `models/` :

```
05_web_app/
├── app.py                      Application Streamlit (4 pages)
├── Data/
│   └── clients.csv             Extrait de données pour le Dashboard KPI
├── models/
│   ├── model.pkl                XGBoost entraîné (avec SMOTE)
│   ├── feature_columns.pkl      Ordre des colonnes attendu par le modèle
│   ├── frequency_encoder.pkl    Encodage fréquence (BRANCH, INDUSTRY)
│   └── scaler.pkl                Conservé mais non utilisé (modèle final = XGBoost
│                                  entraîné sur données NON standardisées, cf. app.py)
├── requirements.txt
└── README.md                    Ce fichier
```

⚠️ Le modèle chargé (`model.pkl`) attend exactement les features listées en tête de
`app.py` (features numériques + one-hot + fréquence). Si `04_machine_learning/` change
de features (ex. passage du grain compte au grain client, voir la discussion sur
`churn = min(...)` par client), **`model.pkl` et `feature_columns.pkl` doivent être
régénérés et remplacés ici** — sinon l'app plantera silencieusement sur un mauvais
alignement de colonnes ou donnera des prédictions incohérentes.

## Lancer l'application en local

```bash
cd 05_web_app
pip install -r requirements.txt
streamlit run app.py
```

## 🔗 Lien de déploiement (Streamlit Community Cloud)

**À compléter** — aucun lien de déploiement n'est actuellement documenté nulle part
dans le dépôt (ni ici, ni dans le `README.md` racine). Une fois l'app déployée sur
Streamlit Community Cloud (recommandé dans `00_documentation/4_guide_etudiant.md`,
étape 6) :

1. Remplacez la ligne ci-dessous par l'URL réelle (format
   `https://<nom-app>.streamlit.app`).
2. Reportez le même lien dans le `README.md` à la racine du projet (section à créer,
   ou badge en haut du fichier), pour qu'il soit visible sans ouvrir ce sous-dossier.

> **App en ligne :** _(lien à renseigner — ex. `https://churn-hafas.streamlit.app`)_

## Reste à faire

- [ ] Déployer sur Streamlit Community Cloud et renseigner le lien ci-dessus.
- [ ] Vérifier que `requirements.txt` liste bien `xgboost` (nécessaire au
      chargement de `model.pkl`, voir la note en tête de `app.py`).
- [ ] Revalider `model.pkl` / `feature_columns.pkl` si le grain ou les features du
      notebook ML changent.