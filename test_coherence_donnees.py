"""
test_coherence_donnees.py — Tests de cohérence sur le dataset nettoyé.

⚠️ Ce script est volontairement INDÉPENDANT du pipeline ETL (01_etl/etl_pipeline/) :
il ne modifie rien dans clean.py, dimensions.py ou fact.py. Il sert uniquement à
VÉRIFIER, après coup, que le résultat du nettoyage est cohérent — pas à imposer une
nouvelle logique de traitement. Le plafonnement SALARY ci-dessous (99e percentile,
winsorisation) est local à ce script de diagnostic ; il ne remplace pas la décision
déjà prise dans clean.py (99,9e centile, mise à NaN) — voir la note en tête de
section pour la distinction.

Usage :
    cd 01_etl
    python ../test_coherence_donnees.py
ou, depuis n'importe où, en adaptant le chemin inséré dans sys.path ci-dessous.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# Localise le module etl_pipeline en remontant depuis ce fichier, comme run.py
# et load_warehouse.py le font déjà — pour rester utilisable peu importe d'où on
# lance ce script.
_THIS_DIR = Path(__file__).resolve().parent
_search_dir = _THIS_DIR
for _ in range(4):
    if (_search_dir / "01_etl" / "etl_pipeline").is_dir():
        sys.path.insert(0, str(_search_dir / "01_etl"))
        break
    if (_search_dir / "etl_pipeline").is_dir():
        sys.path.insert(0, str(_search_dir))
        break
    _search_dir = _search_dir.parent
else:
    raise ImportError(
        "Impossible de localiser etl_pipeline/ en remontant depuis "
        f"{_THIS_DIR} — vérifiez l'emplacement de ce script dans le projet."
    )

from etl_pipeline.pipeline import run_pipeline  # noqa: E402

# =============================================================================
# Chargement des données NETTOYÉES (sortie de clean.clean_all, via le pipeline)
# =============================================================================
print("Exécution du pipeline ETL (extract + clean) pour obtenir le DataFrame nettoyé...")
resultats = run_pipeline(load_to_db=False)
df = resultats["df"].copy()
print(f"DataFrame nettoyé chargé : {len(df):,} lignes, {df.shape[1]} colonnes.\n")

# =============================================================================
# Plafonnement SALARY — LOCAL à ce script, ne modifie pas etl_pipeline/clean.py
# =============================================================================
# Note de cohérence avec le pipeline : clean.py a déjà mis à NaN les valeurs de
# SALARY au-delà du 99,9e centile (~1 099 599, voir log "[SALARY] ... mises à NaN").
# Ce script applique ICI, en plus et seulement pour ses propres calculs de
# diagnostic, un plafonnement (winsorisation) au 99e percentile des valeurs
# RESTANTES — un seuil différent et une méthode différente (clip plutôt que NaN),
# choisis volontairement pour ce diagnostic. Cela n'écrit rien dans le pipeline.
salary_cap = df['SALARY'].quantile(0.99)
nb_outliers_salary = (df['SALARY'] > salary_cap).sum()
df['SALARY'] = df['SALARY'].clip(upper=salary_cap)

print(f"[SALARY outliers] Plafonnement local (diagnostic only) au 99e percentile : "
      f"{salary_cap:,.0f}")
print(f"  -> {nb_outliers_salary:,} valeurs écrêtées pour les calculs de ce script "
      f"(le DataFrame du pipeline lui-même n'est pas modifié).")
print(f"  -> Nouveau max (local) : {df['SALARY'].max():,.0f}\n")

# =============================================================================
# Initialisation du rapport
# =============================================================================
anomalies = []  # liste de tuples (catégorie, test, nb_lignes, gravité)


def log(categorie, test, nb, gravite="ATTENTION"):
    anomalies.append((categorie, test, nb, gravite))
    statut = "OK" if nb == 0 else gravite
    print(f"  [{statut}]  [{categorie}] {test} : {nb:,} anomalie(s)")


print("=" * 70)
print("TESTS DE COHÉRENCE — DATASET CHURN BANCAIRE (après nettoyage ETL)")
print("=" * 70)


# ══════════════════════════════════════════════════════════════
# 1. TESTS DE COMPLÉTUDE — colonnes critiques jamais nulles
# ══════════════════════════════════════════════════════════════
print("\n1. COMPLÉTUDE")

log("Complétude", "CUSTOMER_NO null", df['CUSTOMER_NO'].isna().sum(), "BLOQUANT")
log("Complétude", "ACCOUNT_NO null", df['ACCOUNT_NO'].isna().sum(), "BLOQUANT")
log("Complétude", "ACCOUNT_STATUS null", df['ACCOUNT_STATUS'].isna().sum(), "BLOQUANT")

# PRODUCT_LINE et SCORE_KYC sont imputés par clean_all (mode, ou catégorie
# explicite type 'SANS_LIGNE') -> ce test devrait toujours renvoyer 0 sur les
# données nettoyées. S'il renvoie autre chose, c'est une régression du pipeline.
log("Complétude", "PRODUCT_LINE null (devrait être 0 après clean_all)",
    df['PRODUCT_LINE'].isna().sum(), "ATTENTION")
log("Complétude", "SCORE_KYC null (devrait être 0 après clean_all)",
    df['SCORE_KYC'].isna().sum(), "ATTENTION")


# ══════════════════════════════════════════════════════════════
# 2. TESTS DE DOMAINE — valeurs hors référentiel
# ══════════════════════════════════════════════════════════════
print("\n2. DOMAINE (valeurs autorisées)")

log("Domaine", "ACCOUNT_STATUS hors {Active, Closed}",
    (~df['ACCOUNT_STATUS'].isin(['Active', 'Closed'])).sum(), "BLOQUANT")

log("Domaine", "SCORE_KYC hors {LR, MR, H1, H2, H3}",
    (~df['SCORE_KYC'].isin(['LR', 'MR', 'H1', 'H2', 'H3'])).sum(), "ATTENTION")

# Référentiel élargi avec SANS_LIGNE (catégorie explicite posée par clean_all
# pour la nullité structurelle des colonnes produit) — voir 01_etl/README.md.
log("Domaine", "PRODUCT_LINE hors référentiel connu",
    (~df['PRODUCT_LINE'].isin(
        ['ACCOUNTS', 'LENDING', 'DEPOSITS', 'SAFE.DEPOSIT.BOX', 'SANS_LIGNE']
    )).sum(), "ATTENTION")

# Référentiel élargi avec INCONNU et NON_APPLICABLE, les deux catégories que
# clean_all pose explicitement selon NATURE_CLIENT (PM -> NON_APPLICABLE,
# PPH -> INCONNU) — voir clean.clean_qualitative_columns.
log("Domaine", "MARITAL_STATUS hors {M, C, D, V, INCONNU, NON_APPLICABLE}",
    (~df['MARITAL_STATUS'].isin(
        ['M', 'C', 'D', 'V', 'INCONNU', 'NON_APPLICABLE']
    )).sum(), "ATTENTION")

# COMPLETED_FILE : clean_all impute uniquement les NaN -> 'NO' ; toute autre
# valeur que 'YES'/'NO' viendrait du fichier source lui-même.
log("Domaine", "COMPLETED_FILE hors {YES, NO}",
    (~df['COMPLETED_FILE'].isin(['YES', 'NO'])).sum(), "ATTENTION")

log("Domaine", "CURRENCY null ou vide (devrait être 0 après clean_all)",
    (df['CURRENCY'].isna() | (df['CURRENCY'].astype(str).str.strip() == '')).sum(),
    "ATTENTION")


# ══════════════════════════════════════════════════════════════
# 3. TESTS DE COHÉRENCE INTER-COLONNES
# ══════════════════════════════════════════════════════════════
print("\n3. COHÉRENCE INTER-COLONNES")

# 3.1 ACCOUNT_STATUS <-> ACCT_CLOSE_DATE
# Vérifié dans l'EDA (01_exploration.ipynb) comme une nullité structurelle
# PARFAITE sur les données réelles (100% Active = vide, 100% Closed = rempli).
# Ce test devrait donc renvoyer 0 sur le fichier réel actuel ; un résultat non
# nul signalerait une nouvelle version des données qui romprait cette régularité.
log("Inter-colonnes", "Closed SANS ACCT_CLOSE_DATE",
    ((df['ACCOUNT_STATUS'] == 'Closed') & df['ACCT_CLOSE_DATE'].isna()).sum(), "BLOQUANT")

log("Inter-colonnes", "Active AVEC ACCT_CLOSE_DATE renseignée",
    ((df['ACCOUNT_STATUS'] == 'Active') & df['ACCT_CLOSE_DATE'].notna()).sum(), "BLOQUANT")

# 3.2 ACCOUNT_STATUS <-> CLOSURE_REASON
# ⚠️ Valeurs réelles posées par clean_all : 'NON_FERME' (Active) / 'INCONNUE'
# (Closed sans motif), PAS 'Non fermé' — corrigé ici par rapport à la version
# initiale de ce test, qui utilisait un libellé qui n'existe pas dans le pipeline.
log("Inter-colonnes", "Active AVEC une vraie CLOSURE_REASON (ni NON_FERME)",
    ((df['ACCOUNT_STATUS'] == 'Active') &
     df['CLOSURE_REASON'].notna() &
     (df['CLOSURE_REASON'] != 'NON_FERME')).sum(), "BLOQUANT")

log("Inter-colonnes", "Closed AVEC CLOSURE_REASON = 'NON_FERME'",
    ((df['ACCOUNT_STATUS'] == 'Closed') &
     (df['CLOSURE_REASON'] == 'NON_FERME')).sum(), "BLOQUANT")

# 3.3 ACCOUNT_STATUS <-> PRODUCT_STATUS
# Valeurs réelles vérifiées dans PRODUCT_STATUS : CURRENT, UNAUTH, NON_APPLICABLE,
# PENDING.CLOSURE, EXPIRED, CLOSE, AUTH, AUTH-FWD (pas seulement CURRENT/CLOSE).
log("Inter-colonnes", "Closed AVEC PRODUCT_STATUS = 'CURRENT'",
    ((df['ACCOUNT_STATUS'] == 'Closed') &
     (df['PRODUCT_STATUS'] == 'CURRENT')).sum(), "ATTENTION")

log("Inter-colonnes", "Active AVEC PRODUCT_STATUS = 'CLOSE'",
    ((df['ACCOUNT_STATUS'] == 'Active') &
     (df['PRODUCT_STATUS'] == 'CLOSE')).sum(), "ATTENTION")

# 3.4 DEPOSITS <-> MATURITYDATE
# Investigué : ces lignes ont systématiquement AMOUNT=0 et PRODUCT_STATUS dans
# {UNAUTH, PENDING.CLOSURE, CLOSE} (jamais CURRENT) — des dépôts jamais réellement
# activés, qui n'ont logiquement pas d'échéance. Nullité structurelle confirmée,
# pas une vraie anomalie -> reclassé en INFO (était BLOQUANT dans une version
# précédente de ce test, avant investigation).
log("Inter-colonnes", "DEPOSITS sans MATURITYDATE (structurel : AMOUNT=0, jamais activé)",
    ((df['PRODUCT_LINE'] == 'DEPOSITS') & df['MATURITYDATE'].isna()).sum(), "INFO")

# 3.5 NATURE_CLIENT <-> MARITAL_STATUS
# Devrait être 0 par construction : clean_all force MARITAL_STATUS='NON_APPLICABLE'
# pour toute ligne PM, donc aucune ligne PM ne devrait plus porter M/C/D/V ici.
log("Inter-colonnes", "PM (Personne Morale) avec MARITAL_STATUS personnel (M/C/D/V) "
    "(devrait être 0 après clean_all)",
    ((df['NATURE_CLIENT'] == 'PM') &
     df['MARITAL_STATUS'].isin(['M', 'C', 'D', 'V'])).sum(), "BLOQUANT")

# 3.6 SALARY négatif
log("Inter-colonnes", "SALARY négatif", (df['SALARY'] < 0).sum(), "ATTENTION")

# 3.7 FIXEDRATE > 100% (probablement saisi en % au lieu de décimal)
log("Inter-colonnes", "FIXEDRATE > 100 (erreur d'unité ?)",
    (df['FIXEDRATE'] > 100).sum(), "ATTENTION")

# 3.8 ACCT_BALANCE doublon de AMOUNT sur ACCOUNTS
mask_accounts = df['PRODUCT_LINE'] == 'ACCOUNTS'
if mask_accounts.sum() > 0:
    nb_confusion = (
        df.loc[mask_accounts, 'AMOUNT'] == df.loc[mask_accounts, 'ACCT_BALANCE']
    ).sum()
    log("Inter-colonnes",
        "ACCOUNTS avec AMOUNT == ACCT_BALANCE (confusion probable)",
        nb_confusion, "INFO")


# ══════════════════════════════════════════════════════════════
# 4. TESTS DE COHÉRENCE TEMPORELLE
# ══════════════════════════════════════════════════════════════
print("\n4. COHÉRENCE TEMPORELLE")

# Les colonnes de date sont déjà converties en datetime64 par clean_all (voir
# clean.clean_dates) — pas besoin de reconversion défensive ici, contrairement
# à un script qui tournerait sur le fichier brut.
df_t = df

log("Temporelle", "ACCT_CLOSE_DATE < ACCT_OPENING_DATE",
    (df_t['ACCT_CLOSE_DATE'].notna() &
     df_t['ACCT_OPENING_DATE'].notna() &
     (df_t['ACCT_CLOSE_DATE'] < df_t['ACCT_OPENING_DATE'])).sum(), "BLOQUANT")

log("Temporelle", "DATE_OF_BIRTH > CUST_OPENING_DATE (né après entrée en relation)",
    (df_t['DATE_OF_BIRTH'].notna() &
     df_t['CUST_OPENING_DATE'].notna() &
     (df_t['DATE_OF_BIRTH'] > df_t['CUST_OPENING_DATE'])).sum(), "ATTENTION")

# MATURITYDATE/STARTDATE sont décodées du format hérité CYYMMDD par clean_all
# (voir clean.decode_cyymmdd) — ce test vérifie la cohérence APRÈS ce décodage.
log("Temporelle", "MATURITYDATE < STARTDATE (échéance avant début)",
    (df_t['MATURITYDATE'].notna() &
     df_t['STARTDATE'].notna() &
     (df_t['MATURITYDATE'] < df_t['STARTDATE'])).sum(), "BLOQUANT")

log("Temporelle", "LAST_REVIEW_DATE > NEXT__REVIEW_DATE",
    (df_t['LAST_REVIEW_DATE'].notna() &
     df_t['NEXT__REVIEW_DATE'].notna() &
     (df_t['LAST_REVIEW_DATE'] > df_t['NEXT__REVIEW_DATE'])).sum(), "ATTENTION")

# Référence temporelle alignée sur config.REFERENCE_DATE du pipeline plutôt
# qu'une date codée en dur différente ici, pour éviter deux notions de
# "aujourd'hui" incohérentes entre le pipeline et ce script de diagnostic.
from etl_pipeline import config  # noqa: E402

ref_future = config.REFERENCE_DATE

log("Temporelle", f"ACCT_OPENING_DATE dans le futur (> {ref_future.date()})",
    (df_t['ACCT_OPENING_DATE'].notna() &
     (df_t['ACCT_OPENING_DATE'] > ref_future)).sum(), "ATTENTION")

log("Temporelle", f"CUST_OPENING_DATE dans le futur (> {ref_future.date()})",
    (df_t['CUST_OPENING_DATE'].notna() &
     (df_t['CUST_OPENING_DATE'] > ref_future)).sum(), "ATTENTION")

# DATE_OF_BIRTH : clean_all neutralise déjà les années aberrantes (< année-100)
# mais ne plafonne pas explicitement le futur — ce test reste donc pertinent
# même après nettoyage, contrairement à plusieurs tests ci-dessus.
log("Temporelle", f"DATE_OF_BIRTH dans le futur (> {ref_future.date()})",
    (df_t['DATE_OF_BIRTH'].notna() &
     (df_t['DATE_OF_BIRTH'] > ref_future)).sum(), "BLOQUANT")


# ══════════════════════════════════════════════════════════════
# 5. TESTS DE CARDINALITÉ
# ══════════════════════════════════════════════════════════════
print("\n5. CARDINALITÉ")

# ⚠️ Sur les données nettoyées, ACCOUNT_NO N'EST PAS censé être unique : le
# grain retenu pour fact_account_event est l'ÉVÉNEMENT (1 ligne source = 1
# ligne de fait), donc un même compte peut légitimement apparaître plusieurs
# fois (plusieurs produits/contrats liés à un même compte). Voir 01_etl/README.md,
# section "Grain de FACT_ACCOUNT_EVENT". Ce test mesure donc une INFORMATION,
# pas une anomalie — la gravité est volontairement abaissée à INFO.
nb_dupl_account = df.duplicated(subset='ACCOUNT_NO', keep=False).sum()
log("Cardinalité", "ACCOUNT_NO répété (attendu : grain événement, pas une anomalie)",
    nb_dupl_account, "INFO")

# Celui-ci reste une vraie anomalie potentielle : un compte ne devrait jamais
# changer de propriétaire au sein du même fichier.
nb_acct_multi_client = (
    df.groupby('ACCOUNT_NO')['CUSTOMER_NO'].nunique().gt(1).sum()
)
log("Cardinalité", "ACCOUNT_NO lié à plusieurs CUSTOMER_NO",
    nb_acct_multi_client, "BLOQUANT")

# Un compte avec plusieurs PRODUCT distincts est cohérent avec le grain contrat
# de DIM_PRODUCT (voir 01_etl/README.md) — informatif plutôt que bloquant.
nb_acct_multi_product = (
    df.groupby('ACCOUNT_NO')['PRODUCT'].nunique().gt(1).sum()
)
log("Cardinalité", "ACCOUNT_NO lié à plusieurs PRODUCT (cohérent avec le grain contrat)",
    nb_acct_multi_product, "INFO")


# ══════════════════════════════════════════════════════════════
# TABLEAU DE BORD FINAL
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("TABLEAU DE BORD FINAL")
print("=" * 70)

anomalies_detectees = [(c, t, n, g) for c, t, n, g in anomalies if n > 0]
total_ok = len(anomalies) - len(anomalies_detectees)

print(f"\n  Tests passés         : {total_ok} / {len(anomalies)}")
print(f"  Anomalies détectées  : {len(anomalies_detectees)}")

if anomalies_detectees:
    print("\n  Détail des anomalies :")
    print(f"  {'Catégorie':<18} {'Test':<60} {'Nb':>8}  Gravité")
    print("  " + "-" * 94)
    for cat, test, nb, grav in sorted(anomalies_detectees, key=lambda x: x[2], reverse=True):
        print(f"  {cat:<18} {test:<60} {nb:>8,}  {grav}")
else:
    print("\n  Aucune anomalie détectée — dataset cohérent.")

n_bloquant = sum(1 for c, t, n, g in anomalies_detectees if g == "BLOQUANT")
print("\n" + "=" * 70)
print("  Légende : BLOQUANT  ATTENTION (à investiguer)  INFO (pour information)")
if n_bloquant > 0:
    print(f"  /!\\ {n_bloquant} anomalie(s) BLOQUANTE(S) détectée(s) — à corriger avant le ML.")
print("=" * 70)
