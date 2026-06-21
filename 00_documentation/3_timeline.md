# Timeline du Projet — 4 Semaines

La durée totale du projet est de **4 semaines (28 jours)**. Le planning ci-dessous est indicatif : adaptez-le à la composition et à la disponibilité de votre équipe, mais respectez les jalons hebdomadaires qui correspondent aux points de suivi avec l'encadrant.

## Vue d'ensemble

| Semaine | Phase | Objectif principal | Livrable de fin de semaine |
|---|---|---|---|
| **S1** | Cadrage & Exploration | Comprendre les données, mettre en place l'environnement et l'ETL | Pipeline ETL fonctionnel + rapport d'exploration |
| **S2** | BI & Power BI | Modélisation dimensionnelle et tableaux de bord | Data Warehouse + rapports Power BI |
| **S3** | Machine Learning | Entraînement et évaluation des modèles de churn | Modèle sauvegardé + notebook d'analyse |
| **S4** | Web & Livraison | Application web, déploiement, rapport, présentation | Démo en ligne + rapport PDF + présentation |

---

## Semaine 1 — Cadrage et Exploration (J1 → J7)

### Objectifs
- Constituer l'équipe et définir les rôles.
- Comprendre le contexte métier et la définition du churn.
- Profiler les données et identifier les problèmes de qualité.
- Concevoir et implémenter le pipeline ETL.

### Jour par jour
| Jour | Activité |
|---|---|
| J1 | Lecture des documents du projet, répartition des rôles, création du dépôt GitHub, mise en place de l'environnement (Python, venv, dépendances). |
| J2 | Exploration des fichiers : volumétrie, types, valeurs manquantes, distributions. Premier notebook d'EDA (Exploratory Data Analysis). |
| J3 | Analyse des tables de dimensions, étude des codes et libellés, recensement des incohérences. |
| J4 | Définition formelle de la variable cible (churn), justification du choix. Liste des features candidates. |
| J5 | Conception du pipeline ETL : sources, transformations, cibles. Diagramme. |
| J6 | Implémentation du pipeline ETL (extraction + nettoyage + jointures). |
| J7 | Chargement vers la base de données analytique. Tests de cohérence. **Jalon S1.** |

### Livrable de la semaine
- Dépôt GitHub initialisé avec README, structure de dossiers, `.gitignore`.
- Notebook d'exploration documenté.
- Pipeline ETL exécutable et reproductible.
- Schéma de l'architecture cible (data flow).

---

## Semaine 2 — BI et Power BI (J8 → J14)

### Objectifs
- Concevoir un modèle dimensionnel en étoile.
- Définir et calculer les KPIs métier.
- Produire les rapports Power BI.

### Jour par jour
| Jour | Activité |
|---|---|
| J8 | Conception du modèle dimensionnel : table de faits, dimensions, granularité. |
| J9 | Création des tables dimensionnelles et de la table de faits dans le Data Warehouse. |
| J10 | Définition des KPIs : taux de churn global, par segment, par ancienneté, par produit, etc. |
| J11 | Connexion de Power BI à la source de données. Préparation des mesures DAX. |
| J12 | Construction du rapport Power BI — page 1 (vue d'ensemble). |
| J13 | Construction du rapport Power BI — pages d'analyse (segmentation, churn, produits). |
| J14 | Mise au point graphique, interactivité, publication. **Jalon S2.** |

### Livrable de la semaine
- Schéma dimensionnel documenté.
- Data Warehouse peuplé.
- Fichier `.pbix` (ou lien Power BI Service) avec au minimum 3 pages d'analyse.
- Liste des KPIs documentée dans le dépôt.

---

## Semaine 3 — Machine Learning (J15 → J21)

### Objectifs
- Préparer le jeu de données ML.
- Entraîner et comparer plusieurs modèles.
- Choisir et sauvegarder le modèle final.

### Jour par jour
| Jour | Activité |
|---|---|
| J15 | Préparation du dataset ML depuis le DWH : sélection des features, encodage, traitement du déséquilibre. |
| J16 | Split train/test, baseline (régression logistique). Premières métriques. |
| J17 | Entraînement de modèles avancés (Random Forest, XGBoost, LightGBM). Comparaison. |
| J18 | Optimisation des hyperparamètres (Grid Search ou Optuna) pour le meilleur candidat. |
| J19 | Évaluation finale : accuracy, precision, recall, F1, ROC-AUC, matrice de confusion. |
| J20 | Interprétabilité : importance des features, SHAP values. |
| J21 | Sauvegarde du modèle (`.pkl` ou `.joblib`). Documentation des choix. **Jalon S3.** |

### Livrable de la semaine
- Notebook ML complet (préparation → entraînement → évaluation → interprétation).
- Modèle sauvegardé.
- Tableau comparatif des modèles testés.

---

## Semaine 4 — Interface Web, Déploiement, Livraison (J22 → J28)

### Objectifs
- Construire et déployer l'application web.
- Finaliser le rapport et la présentation.

### Jour par jour
| Jour | Activité |
|---|---|
| J22 | Maquette de l'application web. Choix de la stack (Streamlit / Flask / FastAPI + frontend). |
| J23 | Développement — chargement du modèle, formulaire de prédiction client. |
| J24 | Développement — page "comptes à risque" + KPIs de synthèse. |
| J25 | Déploiement sur une plateforme cloud (Streamlit Cloud, Render, Hugging Face Spaces, Railway, etc.). Tests. |
| J26 | Rédaction du rapport PDF (toutes les parties). |
| J27 | Préparation de la présentation (slides + script + démonstration). |
| J28 | Répétition de la présentation. Finalisation du dépôt GitHub. **Soutenance finale.** |

### Livrable final
- Application web accessible en ligne via une URL publique.
- Dépôt GitHub finalisé avec README détaillé (instructions, captures d'écran, lien démo).
- Rapport PDF (25–40 pages).
- Slides de présentation.

---

## Recommandations transverses

- **Commits réguliers** : chaque membre commit au moins quotidiennement sur sa branche.
- **Branches Git** : utilisez `main` pour le code stable et des branches `feature/...` par tâche.
- **Documentation au fil de l'eau** : ne laissez pas la rédaction du rapport pour la dernière semaine. Rédigez les sections au fur et à mesure que vous terminez les phases.
- **Tests** : prévoyez du temps de buffer en fin de semaine 4 — déployer pour la première fois prend souvent plus de temps que prévu.
