"""
Application Streamlit — Prédiction du churn client
Respecte le flow de traitement du notebook machine_learning2.ipynb :
  - Features numériques : salary, amount_total, fixedrate_mean, nb_produits, age, salary_missing
  - Features catégorielles One-Hot (pd.get_dummies, drop_first=True) :
        MARITAL_STATUS, NATURE_CLIENT, PARTYCLASS, SCORE_KYC, COMPLETED_FILE, LOB
  - Features catégorielles encodées par fréquence : BRANCH, INDUSTRY
  - Modèle final : XGBoost entraîné avec SMOTE, sur données NON standardisées
    (donc pas de scaler.pkl nécessaire ici)
"""

# NOTE IMPORTANTE : model.pkl est un XGBClassifier -> le paquet "xgboost"
# doit être présent dans requirements.txt, sinon joblib.load(model.pkl) échoue.
import joblib
import numpy as np
import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------
# Config générale de la page
# ----------------------------------------------------------------------
st.set_page_config(page_title="Prédiction Churn Client", page_icon="📊", layout="centered")

# Colonnes qui ont été encodées en One-Hot dans le notebook (pd.get_dummies)
FEATURES_ONEHOT = ["MARITAL_STATUS", "NATURE_CLIENT", "PARTYCLASS", "SCORE_KYC",
                    "COMPLETED_FILE", "LOB"]
# Colonnes encodées par fréquence
FEATURES_FREQUENCE = ["BRANCH", "INDUSTRY"]
# Colonnes numériques (salary_missing est un flag dérivé, pas saisi tel quel)
FEATURES_NUMERIQUES = ["salary", "amount_total", "fixedrate_mean", "nb_produits", "age"]


# ----------------------------------------------------------------------
# Chargement des artefacts sauvegardés par le notebook (mis en cache)
# ----------------------------------------------------------------------
@st.cache_resource
def charger_artefacts():
    model = joblib.load("models/model.pkl")
    feature_columns = joblib.load("models/feature_columns.pkl")   # liste des colonnes de X_encoded
    frequency_encoders = joblib.load("models/frequency_encoder.pkl")  # dict {colonne: {valeur: freq}}
    return model, feature_columns, frequency_encoders


try:
    model, feature_columns, frequency_encoders = charger_artefacts()
except FileNotFoundError as e:
    st.error(
        "Fichier manquant : impossible de trouver `models/model.pkl`, "
        "`models/feature_columns.pkl` ou `models/frequency_encoder.pkl`.\n\n"
        f"Détail : {e}"
    )
    st.stop()


def options_onehot(prefixe):
    """Reconstruit la liste des catégories connues du modèle pour une variable One-Hot,
    à partir des noms de colonnes encodées (ex: 'MARITAL_STATUS_Marié' -> 'Marié').
    Une catégorie n'apparaît pas dans les colonnes : c'est la catégorie de référence
    (celle supprimée par drop_first=True) -> on l'ajoute comme option par défaut."""
    prefixe_ = prefixe + "_"
    valeurs = [col[len(prefixe_):] for col in feature_columns if col.startswith(prefixe_)]
    return ["(valeur de référence)"] + valeurs


def options_frequence(colonne):
    """Liste des catégories vues à l'entraînement pour une variable encodée par fréquence."""
    return list(frequency_encoders.get(colonne, {}).keys())


# ----------------------------------------------------------------------
# Interface utilisateur
# ----------------------------------------------------------------------
st.title("📊 Prédiction du risque de churn client")
st.write(
    "Renseignez les informations du client ci-dessous, puis cliquez sur **Prédire** "
    "pour estimer sa probabilité de fermer tous ses comptes (churn)."
)

st.subheader("Informations numériques")
col1, col2 = st.columns(2)
with col1:
    age = st.number_input("Âge du client", min_value=18, max_value=100, value=40)
    nb_produits = st.number_input("Nombre de produits détenus", min_value=0, max_value=50, value=2)
    fixedrate_mean = st.number_input("Taux fixe moyen (fixedrate_mean)", value=0.0, format="%.4f")
with col2:
    amount_total = st.number_input("Montant total des transactions (amount_total)", value=0.0, format="%.2f")
    salaire_inconnu = st.checkbox("Salaire inconnu / non renseigné")
    salary = st.number_input(
        "Salaire (salary)", min_value=0.0, value=0.0, format="%.2f",
        disabled=salaire_inconnu,
        help="Décochez la case ci-dessus si vous connaissez le salaire du client.",
    )

st.subheader("Informations catégorielles")
col3, col4 = st.columns(2)
with col3:
    marital_status = st.selectbox("Statut marital (MARITAL_STATUS)", options_onehot("MARITAL_STATUS"))
    nature_client = st.selectbox("Nature du client (NATURE_CLIENT)", options_onehot("NATURE_CLIENT"))
    partyclass = st.selectbox("Classe de partie (PARTYCLASS)", options_onehot("PARTYCLASS"))
    lob = st.selectbox("Ligne de métier (LOB)", options_onehot("LOB"))
with col4:
    score_kyc = st.selectbox("Score KYC (SCORE_KYC)", options_onehot("SCORE_KYC"))
    completed_file = st.selectbox("Dossier complété (COMPLETED_FILE)", options_onehot("COMPLETED_FILE"))
    branch = st.selectbox("Agence (BRANCH)", options_frequence("BRANCH"))
    industry = st.selectbox("Secteur d'activité (INDUSTRY)", options_frequence("INDUSTRY"))

# ----------------------------------------------------------------------
# Construction du vecteur de features en respectant EXACTEMENT le flow
# du notebook : mêmes colonnes, même ordre, même encodage.
# ----------------------------------------------------------------------
def construire_features():
    salary_val = 0.0 if salaire_inconnu else salary
    salary_missing_val = 1 if salaire_inconnu else 0

    donnees_brutes = {
        "salary": salary_val,
        "amount_total": amount_total,
        "fixedrate_mean": fixedrate_mean,
        "nb_produits": nb_produits,
        "age": age,
        "salary_missing": salary_missing_val,
        "MARITAL_STATUS": None if marital_status == "(valeur de référence)" else marital_status,
        "NATURE_CLIENT": None if nature_client == "(valeur de référence)" else nature_client,
        "PARTYCLASS": None if partyclass == "(valeur de référence)" else partyclass,
        "SCORE_KYC": None if score_kyc == "(valeur de référence)" else score_kyc,
        "COMPLETED_FILE": None if completed_file == "(valeur de référence)" else completed_file,
        "LOB": None if lob == "(valeur de référence)" else lob,
        "BRANCH": branch,
        "INDUSTRY": industry,
    }

    df_input = pd.DataFrame([donnees_brutes])

    # 1. One-Hot Encoding (comme pd.get_dummies dans le notebook)
    df_encoded = pd.get_dummies(df_input, columns=FEATURES_ONEHOT)

    # 2. Encodage par fréquence (mapping appris sur X_train dans le notebook)
    for col in FEATURES_FREQUENCE:
        freq_map = frequency_encoders.get(col, {})
        df_encoded[col] = df_encoded[col].map(freq_map).fillna(0)

    # 3. Alignement strict sur les colonnes vues à l'entraînement
    #    (ajoute les colonnes manquantes à 0, supprime celles en trop, remet le bon ordre)
    df_final = df_encoded.reindex(columns=feature_columns, fill_value=0)

    return df_final


# ----------------------------------------------------------------------
# Prédiction
# ----------------------------------------------------------------------
st.divider()
if st.button("🔮 Prédire", type="primary", use_container_width=True):
    X_input = construire_features()

    proba_churn = float(model.predict_proba(X_input)[0, 1])
    prediction = int(proba_churn >= 0.5)

    st.subheader("Résultat")
    if prediction == 1:
        st.error(f"⚠️ Client à risque de churn — probabilité estimée : **{proba_churn*100:.1f}%**")
    else:
        st.success(f"✅ Client jugé fidèle — probabilité de churn estimée : **{proba_churn*100:.1f}%**")

    st.progress(min(max(proba_churn, 0.0), 1.0))

    with st.expander("Voir le détail technique (features envoyées au modèle)"):
        st.dataframe(X_input.T.rename(columns={0: "valeur"}))