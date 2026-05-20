# Projet Intégré — Analyse et Prédiction du Churn Client

> **École** : ESPRIT School of Business
> **Programme** : Master 1 — Business Analytics (M1 BA)
> **Tuteur du projet** : Aymen Ben Brik
> **Année** : 2026

Bienvenue. Ce dossier contient l'ensemble des supports nécessaires pour réaliser le projet.

## Par où commencer

1. Lisez les documents du dossier **`00_documentation/`** dans l'ordre :
   - `1_description_projet.md` — ce qu'on vous demande de faire et les livrables attendus.
   - `2_description_donnees.md` — la structure des données fournies.
   - `3_timeline.md` — le planning sur 4 semaines.
   - `4_guide_etudiant.md` — la démarche et les outils proposés étape par étape.
2. Placez les fichiers de données qui vous seront remis dans le dossier **`data/`** (ce dossier est ignoré par Git, voir `.gitignore`).
3. Travaillez dans les dossiers numérotés correspondants à chaque phase.

## Structure du dossier

| Dossier | Contenu attendu |
|---|---|
| `00_documentation/` | Documents fournis par l'encadrant (ne pas modifier) |
| `01_etl/` | Scripts et notebooks ETL (extraction, nettoyage, transformation) |
| `02_data_warehouse/` | Scripts SQL de création du schéma, modèle dimensionnel, scripts de chargement |
| `03_power_bi/` | Fichiers `.pbix`, captures d'écran, documentation des KPIs |
| `04_machine_learning/` | Notebooks ML, scripts d'entraînement, modèles sauvegardés (`.pkl`) |
| `05_web_app/` | Code de l'application web et instructions de déploiement |
| `06_rapport/` | Sources du rapport (Word, LaTeX, etc.) et version PDF finale |
| `07_presentation/` | Slides de présentation |
| `data/` | Données brutes (**ne sera pas versionnée**) |

## Règles à respecter

- **Données confidentielles** : aucun fichier de données ne doit être commité sur GitHub. Le dossier `data/` est exclu via `.gitignore`.
- **Anonymat** : ne mentionnez l'origine des données dans aucun livrable (code, rapport, présentation).
- **Versioning régulier** : chaque membre de l'équipe doit commiter régulièrement, sur sa branche.
- **Reproductibilité** : votre code doit pouvoir être ré-exécuté à partir des instructions de ce README et du `requirements.txt`.

## Installation

```bash
# 1. Cloner le dépôt
git clone <url-de-votre-depot>
cd <nom-du-depot>

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Placer les fichiers de données dans data/
# (les fichiers vous seront fournis séparément)
```

## Livrables finaux

À la fin du projet, vous devez fournir :

1. **Le lien vers votre dépôt GitHub** (public, propre, documenté).
2. **Le rapport PDF** (dans `06_rapport/`).
3. **Les slides de présentation** (dans `07_presentation/`).
4. **L'URL publique** de votre application web déployée (mentionnée dans ce README).

## Composition de l'équipe

| Nom | Rôle principal | Email |
|---|---|---|
| _À compléter_ | _À compléter_ | _À compléter_ |
| _À compléter_ | _À compléter_ | _À compléter_ |
| _À compléter_ | _À compléter_ | _À compléter_ |

## Contact tuteur

Aymen Ben Brik — _coordonnées à compléter par le tuteur_.
