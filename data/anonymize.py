"""
Script d'anonymisation du jeu de données source.

Transformations appliquees :
  1. ATB.*               -> BANK.*    dans toutes les colonnes texte
  2. CUSTOMER_NO         -> C000001, C000002, ...
  3. ACCOUNT_NO          -> A0000001, A0000002, ...
  4. BRANCH              -> BR01, BR02, ... (renumérotation aléatoire)
  5. DATE_OF_BIRTH       -> annee uniquement (YYYY)
  6. Un seul CSV en sortie (data_churn.csv)
  7. Copie des dim_*.xlsx telles quelles (deja propres)

Le script est deterministe : meme entree -> meme sortie.
"""
from __future__ import annotations

import shutil
import random
from pathlib import Path

import pandas as pd

# Reglages -------------------------------------------------------------------
SRC_CSV = Path(r"C:\Users\aymen\OneDrive\Bureau\Developpement\Haythem PFE Buggy Code still need fixing\jupy\DATA copy.csv")
SRC_DIM_DIR = Path(r"C:\Users\aymen\OneDrive\Bureau\Developpement\Haythem PFE Buggy Code still need fixing\jupy")
DST_DIR = Path(__file__).parent
DST_CSV = DST_DIR / "data_churn.csv"

RANDOM_SEED = 42


def anonymize() -> None:
    print(f"[1/5] Lecture de {SRC_CSV.name}...")
    df = pd.read_csv(SRC_CSV, low_memory=False)
    n = len(df)
    print(f"      {n:,} lignes, {len(df.columns)} colonnes")

    print("[2/5] Remplacement ATB -> BANK (toutes formes)...")
    # Regex avec word boundaries pour attraper ATB partout :
    #   "ATB.GRP.X" -> "BANK.GRP.X"
    #   "AVA ATB"   -> "AVA BANK"
    #   "NON ATB"   -> "NON BANK"
    text_cols = df.select_dtypes(include="object").columns
    for col in text_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(r"\bATB\b", "BANK", regex=True, case=False)
            .replace("nan", pd.NA)
        )

    print("[3/5] Renumerotation des identifiants...")
    # CUSTOMER_NO -> C000001 ...
    cust_map = {
        old: f"C{i+1:06d}"
        for i, old in enumerate(sorted(df["CUSTOMER_NO"].dropna().unique()))
    }
    df["CUSTOMER_NO"] = df["CUSTOMER_NO"].map(cust_map)
    print(f"      {len(cust_map):,} clients renumerotes")

    # ACCOUNT_NO -> A0000001 ...
    acc_map = {
        old: f"A{i+1:07d}"
        for i, old in enumerate(sorted(df["ACCOUNT_NO"].dropna().unique()))
    }
    df["ACCOUNT_NO"] = df["ACCOUNT_NO"].map(acc_map)
    print(f"      {len(acc_map):,} comptes renumerotes")

    # BRANCH -> BR01, BR02 ... (ordre aleatoire)
    rng = random.Random(RANDOM_SEED)
    branches = list(df["BRANCH"].dropna().unique())
    rng.shuffle(branches)
    branch_map = {old: f"BR{i+1:02d}" for i, old in enumerate(branches)}
    df["BRANCH"] = df["BRANCH"].map(branch_map)
    print(f"      {len(branch_map)} agences renumerotees")

    print("[4/5] Reduction DATE_OF_BIRTH a l'annee...")

    def keep_year(v):
        if pd.isna(v) or v in ("NULL", "nan"):
            return pd.NA
        s = str(int(float(v))) if str(v).replace(".", "").isdigit() else str(v)
        return s[:4] if len(s) >= 4 else pd.NA

    df["DATE_OF_BIRTH"] = df["DATE_OF_BIRTH"].apply(keep_year)

    print(f"[5/5] Ecriture de {DST_CSV.name}...")
    df.to_csv(DST_CSV, index=False)
    size_mb = DST_CSV.stat().st_size / 1024 / 1024
    print(f"      {size_mb:.1f} Mo")

    # Copie des dimensions (deja propres)
    print("[+]   Copie des fichiers dim_*.xlsx...")
    for dim_file in SRC_DIM_DIR.glob("dim_*.xlsx"):
        shutil.copy(dim_file, DST_DIR / dim_file.name)
        print(f"      {dim_file.name}")

    print("\nTermine. Sortie dans", DST_DIR)


if __name__ == "__main__":
    anonymize()
