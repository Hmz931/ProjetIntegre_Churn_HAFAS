# Projet Intégré — Analyse et Prédiction du Churn Client

> **École** : ESPRIT School of Business
> **Programme** : Master 1 — Business Analytics (M1 BA)
> **Tuteur du projet** : Aymen Ben Brik
> **Année** : 2026

## 1. Contexte

Une institution bancaire met à votre disposition un jeu de données réel et anonymisé décrivant ses clients, leurs comptes et leurs produits. La fidélisation client (lutte contre l'attrition, ou *churn*) est un enjeu majeur du secteur : acquérir un nouveau client coûte plusieurs fois plus cher que d'en conserver un existant.

Votre mission est de concevoir, de bout en bout, une **solution analytique complète** permettant de comprendre, mesurer et anticiper le churn, puis de mettre ces analyses à disposition des décideurs métier via une interface web.

## 2. Objectifs pédagogiques

Ce projet vous permet de mettre en pratique, sur un cas réel, l'ensemble de la chaîne décisionnelle :

- Concevoir une architecture de données analytique (modélisation dimensionnelle, ETL).
- Exploiter les techniques de Business Intelligence pour produire des indicateurs métier.
- Construire et évaluer un modèle de Machine Learning supervisé.
- Restituer les résultats via des tableaux de bord et une application web déployée.
- Travailler en équipe avec une démarche projet structurée (versioning, livrables, présentation).

## 3. Périmètre fonctionnel

Le projet est structuré en **cinq composantes complémentaires** qui constituent ensemble une chaîne décisionnelle complète :

### 3.1 ETL (Extract – Transform – Load)
- Extraire les données brutes (fichiers CSV et tables de dimensions Excel).
- Nettoyer, déduplicaster, gérer les valeurs manquantes et les incohérences.
- Transformer et enrichir les données (jointures avec les dimensions, calculs dérivés).
- Charger les données préparées dans un entrepôt analytique (Data Warehouse).

### 3.2 Business Intelligence (BI)
- Concevoir un modèle dimensionnel en étoile (faits + dimensions).
- Définir les KPIs métier (taux de churn, ancienneté moyenne, solde moyen, segmentation, etc.).
- Mettre en place les requêtes analytiques nécessaires aux dashboards.

### 3.3 Machine Learning
- Préparer un jeu de données d'entraînement à partir du Data Warehouse.
- Entraîner et comparer plusieurs modèles de classification supervisée pour prédire la probabilité de churn d'un client.
- Évaluer les modèles avec des métriques adaptées à un problème déséquilibré.
- Interpréter les variables explicatives les plus importantes.
- Sauvegarder le modèle final pour intégration.

### 3.4 Power BI
- Produire un ou plusieurs rapports Power BI alimentés par le Data Warehouse.
- Restituer les KPIs et permettre une exploration interactive (filtres, drill-down).
- Au minimum : vue d'ensemble, analyse du churn, segmentation client.

### 3.5 Interface Web de déploiement
- Développer une application web qui expose le modèle ML et les analyses BI.
- L'utilisateur doit pouvoir :
  - Saisir les caractéristiques d'un client et obtenir une prédiction de churn.
  - Visualiser la liste des clients actifs à risque élevé.
  - Consulter des indicateurs de synthèse.
- Déployer l'application sur une plateforme cloud accessible publiquement.

## 4. Livrables attendus

Trois livrables sont attendus à la fin du mois :

| Livrable | Format | Contenu attendu |
|---|---|---|
| **Code source** | Dépôt GitHub public | Notebooks, scripts ETL, code ML, application web, README détaillé, instructions d'installation et d'exécution |
| **Présentation orale** | Slides (PPT/PDF), 20 min + 10 min de questions | Démonstration de l'application, présentation de la démarche, principaux résultats |
| **Rapport** | PDF, 25–40 pages | Document professionnel décrivant la démarche, l'architecture, les choix techniques, les résultats, les limites et les perspectives |

## 5. Modalités

- **Composition des équipes** : 3 à 4 étudiants par groupe.
- **Durée** : 1 mois (4 semaines), à temps partagé avec les autres cours.
- **Encadrement** : un point d'avancement hebdomadaire avec l'encadrant.
- **Outils** : libre choix dans le respect des contraintes énoncées dans le guide étudiant (document 4).

## 6. Critères d'évaluation

| Critère | Pondération |
|---|---|
| Qualité de l'ETL et du modèle dimensionnel | 15 % |
| Pertinence et qualité des analyses BI / Power BI | 20 % |
| Rigueur de la démarche Machine Learning | 20 % |
| Qualité de l'interface web et du déploiement | 15 % |
| Qualité du code (lisibilité, structure, documentation) | 10 % |
| Qualité du rapport écrit | 10 % |
| Qualité de la présentation orale | 10 % |

## 7. Règles importantes

- **Confidentialité** : les données sont confidentielles. Elles ne doivent **pas** être publiées sur GitHub (utilisez un `.gitignore`). Seul le code peut être partagé publiquement.
- **Anonymat** : ne mentionnez ni le nom de l'institution dont proviennent les données, ni d'éléments permettant de l'identifier, ni dans le code, ni dans le rapport, ni dans la présentation.
- **Versioning** : le dépôt GitHub doit montrer un historique régulier de commits par chaque membre de l'équipe.
- **Reproductibilité** : tout doit pouvoir être ré-exécuté par un tiers à partir du README.
