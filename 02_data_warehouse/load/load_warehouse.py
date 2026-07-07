"""
02_data_warehouse/load/load_warehouse.py

Point d'entrée du chargement du Data Warehouse, conforme à la structure imposée
par l'encadrant (cf. README.md de ce dossier).

⚠️ Ce script ne réimplémente PAS la logique de chargement : il appelle le module
01_etl/etl_pipeline/, qui contient déjà tout le pipeline (extraction, nettoyage,
construction des dimensions et de la table de faits, chargement PostgreSQL) —
validé de bout en bout sur un vrai serveur PostgreSQL le 25/06/2026 (7/7 tables
chargées avec contraintes appliquées). Dupliquer cette logique ici créerait deux
sources de vérité à maintenir en parallèle, avec le risque qu'elles divergent.

Pour le détail des étapes et des décisions de modélisation, voir
01_etl/README.md.

Usage :
    cd 02_data_warehouse/load
    python load_warehouse.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Localise le module etl_pipeline en remontant depuis ce fichier, quel que soit
# le répertoire de travail courant — évite de supposer un chemin relatif fixe.
_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parents[1]  # 02_data_warehouse/load -> racine du projet
_ETL_DIR = _PROJECT_ROOT / "01_etl"

if not (_ETL_DIR / "etl_pipeline").is_dir():
    raise ImportError(
        f"Module etl_pipeline introuvable sous {_ETL_DIR} — vérifiez que "
        f"01_etl/etl_pipeline/ existe bien à la racine du projet."
    )

sys.path.insert(0, str(_ETL_DIR))

from etl_pipeline.pipeline import run_pipeline  # noqa: E402


def main() -> None:
    print("Chargement du Data Warehouse via etl_pipeline (voir 01_etl/README.md)...")
    resultats = run_pipeline(load_to_db=True)

    load_results = resultats["load_results"]
    if load_results is None:
        print("Aucun résultat de chargement (load_to_db=False ?) — vérifiez l'appel.")
        return

    n_ok = sum(load_results.values())
    n_total = len(load_results)
    print(f"\nRésumé : {n_ok}/{n_total} tables chargées avec succès dans PostgreSQL.")
    for table_name, success in load_results.items():
        statut = "OK" if success else "ECHEC"
        print(f"  [{statut}] {table_name}")

    if n_ok < n_total:
        print(
            "\nCertaines tables n'ont pas pu être chargées — voir les messages "
            "d'avertissement ci-dessus pour le détail (serveur non démarré, "
            "identifiants invalides, etc.). Le pipeline ETL lui-même a réussi : "
            "les données restent disponibles via resultats['dimensions'] et "
            "resultats['fact_account_event'] même sans base de données."
        )


if __name__ == "__main__":
    main()
