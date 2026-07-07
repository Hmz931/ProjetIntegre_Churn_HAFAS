#!/usr/bin/env python3
"""
app.py — Point d'entrée réservé pour l'application web (05_web_app/).

⚠️ STUB — non implémenté. Ce fichier existe pour fixer l'emplacement conventionnel
du point d'entrée de l'application web à la racine du projet (pattern usuel pour
une app Streamlit/Flask/FastAPI), avant même que 04_machine_learning/ et
05_web_app/ ne soient développés.

Quand l'équipe sera prête à développer l'application :

- Si Streamlit (recommandé par 00_documentation/4_guide_etudiant.md, étape 6,
  pour un déploiement rapide) : remplacer le contenu de ce fichier par l'app
  Streamlit elle-même, et lancer avec `streamlit run app.py`.
- Si FastAPI/Flask : ce fichier peut devenir le point d'entrée ASGI/WSGI, ou
  simplement importer et lancer l'app définie dans 05_web_app/.

Le modèle ML entraîné (à produire dans 04_machine_learning/, non encore fait)
et les données du Data Warehouse (01_etl/etl_pipeline/, déjà fonctionnel — voir
run.py) sont les deux dépendances que cette app devra charger.

Usage prévu une fois implémenté :
    streamlit run app.py
    # ou
    python app.py
"""
from __future__ import annotations


def main() -> None:
    print(
        "app.py n'est pas encore implémenté.\n"
        "Ce stub réserve l'emplacement conventionnel du point d'entrée de "
        "l'application web — voir 05_web_app/README.md et "
        "04_machine_learning/README.md pour l'état d'avancement de ces deux "
        "dossiers, dont dépend cette application (modèle entraîné + données du "
        "Data Warehouse via 01_etl/etl_pipeline/, déjà fonctionnel)."
    )


if __name__ == "__main__":
    main()
