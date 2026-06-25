#!/usr/bin/env python3
"""
run.py — Point d'entrée unique du projet, à la racine.

Lance le pipeline ETL complet (extraction -> nettoyage -> dimensions -> table de
faits -> chargement PostgreSQL) en une seule commande, sans avoir à se déplacer
dans 01_etl/ ou 02_data_warehouse/load/.

⚠️ Ce script orchestre le pipeline existant (01_etl/etl_pipeline/) — il ne
réimplémente aucune logique. Toute la logique de transformation vit dans
01_etl/etl_pipeline/, déjà validée de bout en bout sur un vrai serveur
PostgreSQL (7/7 tables chargées avec succès, voir 01_etl/README.md).

Usage :
    python run.py                  # pipeline complet + chargement PostgreSQL
    python run.py --no-db          # pipeline complet, sans tenter le chargement
                                      (utile pour itérer sans serveur PostgreSQL disponible)
    python run.py --help           # options disponibles
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
ETL_DIR = PROJECT_ROOT / "01_etl"

if not (ETL_DIR / "etl_pipeline").is_dir():
    raise ImportError(
        f"Module etl_pipeline introuvable sous {ETL_DIR} — vérifiez que ce script "
        f"est bien exécuté depuis la racine du projet (là où se trouve 01_etl/)."
    )

sys.path.insert(0, str(ETL_DIR))

from etl_pipeline.pipeline import run_pipeline  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lance le pipeline ETL complet du projet Churn Bancaire."
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="N'essaie pas de charger les résultats dans PostgreSQL "
             "(utile sans serveur disponible, ou pour itérer plus vite).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    resultats = run_pipeline(load_to_db=not args.no_db)

    print("\n" + "=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    print(f"Lignes après nettoyage       : {len(resultats['df']):,}")
    print(f"Événements (fact_account_event) : {len(resultats['fact_account_event']):,}")
    for nom, table in resultats["dimensions"].items():
        print(f"{nom:20s} : {len(table):,} lignes")

    if resultats["load_results"] is not None:
        n_ok = sum(resultats["load_results"].values())
        n_total = len(resultats["load_results"])
        print(f"\nChargement PostgreSQL : {n_ok}/{n_total} tables chargées avec succès.")
        if n_ok < n_total:
            print(
                "Certaines tables n'ont pas pu être chargées — voir les messages "
                "d'avertissement ci-dessus. Les données restent disponibles en mémoire."
            )
            return 1
    else:
        print("\nChargement PostgreSQL ignoré (--no-db).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
