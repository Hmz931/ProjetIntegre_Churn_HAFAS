# 05 — Application Web

Placez ici le code de l'**interface web** et les instructions de déploiement.

## Fonctionnalités minimales attendues

1. **Prédiction individuelle** : un formulaire pour saisir un profil client et obtenir un score de churn.
2. **Liste des comptes à risque** : prédiction en lot sur les clients actifs.
3. **KPIs de synthèse** : indicateurs principaux affichés sur la page d'accueil.

## Déploiement

L'application doit être **déployée publiquement**. L'URL doit figurer dans le README principal du projet.

Suggestions d'hébergement gratuit : Streamlit Community Cloud, Hugging Face Spaces, Render, Railway.

## Structure suggérée (Streamlit)

```
05_web_app/
├── app.py               # point d'entrée Streamlit
├── pages/               # pages additionnelles (Streamlit multi-pages)
├── utils/
│   ├── model.py         # chargement et inférence du modèle
│   └── preprocessing.py
├── assets/              # logos, captures
├── requirements.txt     # dépendances spécifiques à l'app
├── DEPLOY.md            # procédure de déploiement
└── README.md
```
