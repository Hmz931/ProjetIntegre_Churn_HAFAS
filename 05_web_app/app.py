"""
Application Streamlit — Suite Churn Client
============================================
Pages :
  - Accueil          : écran de chargement corporate + résumé du dataset
  - Prédiction        : formulaire de scoring individuel (modèle XGBoost + SMOTE)
  - Dashboard KPI      : indicateurs métier interactifs (basés sur data/churn.csv)
  - À propos de nous  : présentation du projet / équipe

Respecte le flow de traitement du notebook machine_learning2.ipynb :
  - Features numériques : salary, amount_total, fixedrate_mean, nb_produits, age, salary_missing
  - Features catégorielles One-Hot (pd.get_dummies, drop_first=True) :
        MARITAL_STATUS, NATURE_CLIENT, PARTYCLASS, SCORE_KYC, COMPLETED_FILE, LOB
  - Features catégorielles encodées par fréquence : BRANCH, INDUSTRY
  - Modèle final : XGBoost entraîné avec SMOTE, sur données NON standardisées
    (donc pas de scaler.pkl nécessaire ici)

NOTE IMPORTANTE : model.pkl est un XGBClassifier -> le paquet "xgboost"
doit être présent dans requirements.txt, sinon joblib.load(model.pkl) échoue.
"""

import time

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------
# Config générale de la page
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Suite Churn Client",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

FEATURES_ONEHOT = ["MARITAL_STATUS", "NATURE_CLIENT", "PARTYCLASS", "SCORE_KYC",
                    "COMPLETED_FILE", "LOB"]
FEATURES_FREQUENCE = ["BRANCH", "INDUSTRY"]
FEATURES_NUMERIQUES = ["salary", "amount_total", "fixedrate_mean", "nb_produits", "age"]

# Couleurs "corporate" réutilisées pour tout l'habillage
COULEUR_PRIMAIRE = "#0B3D91"
COULEUR_SECONDAIRE = "#118AB2"
COULEUR_ALERTE = "#EF476F"
COULEUR_OK = "#06A77D"


# ----------------------------------------------------------------------
# Chargement des artefacts modèle (mis en cache, chargé une seule fois)
# ----------------------------------------------------------------------
@st.cache_resource
def charger_artefacts():
    model = joblib.load("models/model.pkl")
    feature_columns = joblib.load("models/feature_columns.pkl")
    frequency_encoders = joblib.load("models/frequency_encoder.pkl")
    return model, feature_columns, frequency_encoders


@st.cache_data
def charger_donnees():
    """Charge le CSV utilisé pour le dashboard KPI (indépendant du modèle)."""
    return pd.read_csv("../data/DW.csv")


# ----------------------------------------------------------------------
# Écran de chargement corporate (affiché une seule fois par session)
# ----------------------------------------------------------------------
def ecran_de_chargement():
    conteneur = st.empty()
    with conteneur.container():
        st.markdown(
            f"""
            <div style="text-align:center; padding-top:120px;">
                <h1 style="color:{COULEUR_PRIMAIRE}; font-size:48px;">🏦 Suite Churn Client</h1>
                <p style="color:gray; font-size:18px;">Chargement des modèles et des données...</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        barre = st.progress(0)
        etapes = ["Connexion aux artefacts modèle...", "Chargement du jeu de données...",
                  "Préparation du tableau de bord...", "Finalisation..."]
        for i, etape in enumerate(etapes):
            st.markdown(f"<p style='text-align:center; color:gray;'>{etape}</p>", unsafe_allow_html=True)
            time.sleep(0.3)
            barre.progress(int((i + 1) / len(etapes) * 100))
    conteneur.empty()


if "app_chargee" not in st.session_state:
    ecran_de_chargement()
    st.session_state["app_chargee"] = True

try:
    model, feature_columns, frequency_encoders = charger_artefacts()
    artefacts_ok = True
except FileNotFoundError as e:
    artefacts_ok = False
    erreur_artefacts = e

try:
    df_data = charger_donnees()
    data_ok = True
except FileNotFoundError as e:
    data_ok = False
    erreur_data = e


# ----------------------------------------------------------------------
# Menu latéral
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"<h2 style='color:{COULEUR_PRIMAIRE};'>🏦 Suite Churn</h2>", unsafe_allow_html=True)
    st.caption("Projet Intégré — Prédiction & Analyse du Churn Bancaire")
    st.divider()
    page = st.radio(
        "Navigation",
        ["🏠 Accueil", "🔮 Prédiction individuelle", "📊 Dashboard KPI", "ℹ️ À propos de nous"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("© 2026 — Projet Intégré ESB")


# ----------------------------------------------------------------------
# Fonctions utilitaires (partagées par les pages)
# ----------------------------------------------------------------------
def options_onehot(prefixe):
    prefixe_ = prefixe + "_"
    valeurs = [col[len(prefixe_):] for col in feature_columns if col.startswith(prefixe_)]
    return ["(valeur de référence)"] + valeurs


def options_frequence(colonne):
    return list(frequency_encoders.get(colonne, {}).keys())


def construire_features(donnees_saisies):
    df_input = pd.DataFrame([donnees_saisies])
    df_encoded = pd.get_dummies(df_input, columns=FEATURES_ONEHOT)
    for col in FEATURES_FREQUENCE:
        freq_map = frequency_encoders.get(col, {})
        df_encoded[col] = df_encoded[col].map(freq_map).fillna(0)
    return df_encoded.reindex(columns=feature_columns, fill_value=0)


# ----------------------------------------------------------------------
# PAGE : ACCUEIL
# ----------------------------------------------------------------------
if page == "🏠 Accueil":
    st.markdown(f"<h1 style='color:{COULEUR_PRIMAIRE};'>Bienvenue sur la Suite Churn Client</h1>",
                unsafe_allow_html=True)
    st.write(
        "Cette application regroupe les outils développés dans le cadre du projet intégré "
        "de prédiction et d'analyse du churn bancaire."
    )

    col1, col2, col3 = st.columns(3)
    if data_ok:
        with col1:
            st.metric("Comptes dans le jeu de données", f"{len(df_data):,}".replace(",", " "))
        with col2:
            taux_churn = df_data["churn"].mean() * 100 if "churn" in df_data.columns else None
            st.metric("Taux de churn global des comptes", f"{taux_churn:.1f}%" if taux_churn is not None else "N/A")
        with col3:
            st.metric("Variables disponibles", len(df_data.columns))
    else:
        st.warning(f"Impossible de charger `data/churn.csv` pour afficher le résumé : {erreur_data}")

    st.divider()
    st.subheader("Ce que vous pouvez faire ici")
    st.markdown(
        """
        - 🔮 **Prédiction individuelle** — estimer la probabilité de churn d'un client précis
        - 📊 **Dashboard KPI** — explorer les indicateurs métier de manière interactive
        - ℹ️ **À propos de nous** — en savoir plus sur le projet et l'équipe
        """
    )

# ----------------------------------------------------------------------
# PAGE : PRÉDICTION INDIVIDUELLE
# ----------------------------------------------------------------------
elif page == "🔮 Prédiction individuelle":
    st.title("🔮 Prédiction du risque de churn client")

    if not artefacts_ok:
        st.error(
            "Fichier manquant : impossible de trouver `models/model.pkl`, "
            "`models/feature_columns.pkl` ou `models/frequency_encoder.pkl`.\n\n"
            f"Détail : {erreur_artefacts}"
        )
        st.stop()

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

    st.divider()
    if st.button("🔮 Prédire", type="primary", use_container_width=True):
        salary_val = 0.0 if salaire_inconnu else salary
        salary_missing_val = 1 if salaire_inconnu else 0

        donnees_saisies = {
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

        X_input = construire_features(donnees_saisies)
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

# ----------------------------------------------------------------------
# PAGE : DASHBOARD KPI
# ----------------------------------------------------------------------
elif page == "📊 Dashboard KPI":
    st.title("📊 Dashboard KPI — Analyse du Churn")

    if not data_ok:
        st.error(f"Impossible de charger `data/churn.csv` : {erreur_data}")
        st.stop()

    if "churn" not in df_data.columns:
        st.error("La colonne `churn` est introuvable dans `data/churn.csv` — impossible de calculer les KPIs.")
        st.stop()

    # --- Filtres interactifs ---
    with st.expander("🔍 Filtres", expanded=False):
        colf1, colf2 = st.columns(2)
        with colf1:
            if "PARTYCLASS" in df_data.columns:
                segments = st.multiselect(
                    "Segment client (PARTYCLASS)",
                    options=sorted(df_data["PARTYCLASS"].dropna().unique().tolist()),
                    default=None,
                )
            else:
                segments = []
        with colf2:
            if "LOB" in df_data.columns:
                lobs = st.multiselect(
                    "Ligne de métier (LOB)",
                    options=sorted(df_data["LOB"].dropna().unique().tolist()),
                    default=None,
                )
            else:
                lobs = []

    df_filtre = df_data.copy()
    if segments:
        df_filtre = df_filtre[df_filtre["PARTYCLASS"].isin(segments)]
    if lobs:
        df_filtre = df_filtre[df_filtre["LOB"].isin(lobs)]

    # --- KPI 01 : Taux de churn global ---
    st.subheader("KPI 01 — Taux de churn global")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nombre de lignes analysées", f"{len(df_filtre):,}".replace(",", " "))
    with col2:
        taux = df_filtre["churn"].mean() * 100
        st.metric("Taux de churn", f"{taux:.1f}%")
    with col3:
        st.metric("Comptes non-churnés", f"{(1 - df_filtre['churn'].mean()) * 100:.1f}%")

    st.divider()

    # --- KPI 06 : Taux de churn par segment (PARTYCLASS) ---
    if "PARTYCLASS" in df_filtre.columns:
        st.subheader("KPI 06 — Taux de churn par segment client")
        kpi_segment = (
            df_filtre.groupby("PARTYCLASS")["churn"]
            .agg(nb_evenements="count", taux_churn_pct="mean")
            .reset_index()
        )
        kpi_segment["taux_churn_pct"] = (kpi_segment["taux_churn_pct"] * 100).round(1)
        kpi_segment = kpi_segment.sort_values("taux_churn_pct", ascending=False)

        fig = px.bar(
            kpi_segment, x="PARTYCLASS", y="taux_churn_pct",
            text="taux_churn_pct", color="taux_churn_pct",
            color_continuous_scale=[COULEUR_OK, COULEUR_ALERTE],
            labels={"taux_churn_pct": "Taux de churn (%)", "PARTYCLASS": "Segment"},
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    # --- KPI 08 : Taux de churn par score KYC ---
    if "SCORE_KYC" in df_filtre.columns:
        st.subheader("KPI 08 — Taux de churn par score KYC")
        ordre_kyc = ["LR", "MR", "H1", "H2", "H3"]
        kpi_kyc = (
            df_filtre.groupby("SCORE_KYC")["churn"]
            .agg(nb_evenements="count", taux_churn_pct="mean")
            .reset_index()
        )
        kpi_kyc["taux_churn_pct"] = (kpi_kyc["taux_churn_pct"] * 100).round(1)
        kpi_kyc["ordre"] = kpi_kyc["SCORE_KYC"].apply(lambda x: ordre_kyc.index(x) if x in ordre_kyc else 99)
        kpi_kyc = kpi_kyc.sort_values("ordre")

        fig = px.bar(
            kpi_kyc, x="SCORE_KYC", y="taux_churn_pct",
            text="taux_churn_pct", color="taux_churn_pct",
            color_continuous_scale=[COULEUR_OK, COULEUR_ALERTE],
            labels={"taux_churn_pct": "Taux de churn (%)", "SCORE_KYC": "Score KYC"},
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    # --- KPI 07-like : Taux de churn par ligne de métier (LOB) ---
    if "LOB" in df_filtre.columns:
        st.subheader("Taux de churn par ligne de métier (LOB)")
        kpi_lob = (
            df_filtre.groupby("LOB")["churn"]
            .agg(nb_evenements="count", taux_churn_pct="mean")
            .reset_index()
        )
        kpi_lob["taux_churn_pct"] = (kpi_lob["taux_churn_pct"] * 100).round(1)
        kpi_lob = kpi_lob.sort_values("taux_churn_pct", ascending=False)

        fig = px.bar(
            kpi_lob, x="LOB", y="taux_churn_pct",
            text="taux_churn_pct", color="taux_churn_pct",
            color_continuous_scale=[COULEUR_OK, COULEUR_ALERTE],
            labels={"taux_churn_pct": "Taux de churn (%)", "LOB": "Ligne de métier"},
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    # --- KPI 05 : Salaire moyen churné vs non-churné ---
    if "salary" in df_filtre.columns:
        st.subheader("KPI 05 — Salaire moyen selon le statut de churn")
        kpi_salaire = df_filtre.groupby("churn")["salary"].mean().reset_index()
        kpi_salaire["churn"] = kpi_salaire["churn"].map({0: "Non churné", 1: "Churné"})
        fig = px.bar(
            kpi_salaire, x="churn", y="salary", color="churn",
            color_discrete_map={"Non churné": COULEUR_OK, "Churné": COULEUR_ALERTE},
            labels={"salary": "Salaire moyen", "churn": ""},
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- Distribution de l'âge selon le churn ---
    if "age" in df_filtre.columns:
        st.subheader("Distribution de l'âge selon le statut de churn")
        df_plot = df_filtre.copy()
        df_plot["churn_label"] = df_plot["churn"].map({0: "Non churné", 1: "Churné"})
        fig = px.histogram(
            df_plot, x="age", color="churn_label", barmode="overlay", nbins=30,
            color_discrete_map={"Non churné": COULEUR_OK, "Churné": COULEUR_ALERTE},
            labels={"age": "Âge", "churn_label": ""},
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("Voir les données filtrées (aperçu)"):
        st.dataframe(df_filtre.head(200))

# ----------------------------------------------------------------------
# PAGE : À PROPOS DE NOUS
# ----------------------------------------------------------------------
elif page == "ℹ️ À propos de nous":
    st.title("ℹ️ À propos de ce projet")
    st.markdown(
        f"""
        <div style="background-color:#F0F4F8; padding:25px; border-radius:10px; border-left:6px solid black;">
        <h3 style="color:black;">Projet Intégré Prédiction du Churn Bancaire</h3>
        <p>
        Ce projet a été réalisé dans le cadre d'un projet intégré universitaire. Il couvre l'ensemble
        de la chaîne data : construction d'un entrepôt de données (Data Warehouse), pipeline ETL,
        modélisation supervisée (prédiction du churn) et non supervisée (segmentation client),
        et enfin cette application de restitution.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.subheader("Ce que couvre le projet")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            **Data Engineering**
            - Pipeline ETL (extraction, nettoyage, dimensions)
            - Modélisation en schéma en étoile (PostgreSQL)
            - KPIs métier documentés en SQL
            """
        )
    with col2:
        st.markdown(
            """
            **Data Science**
            - Modèle supervisé : XGBoost + SMOTE
            - Analyse non supervisée : ACP, ACM, CAH, K-means
            - Application de restitution : Streamlit
            """
        )

    st.divider()
    st.subheader("Équipe")
    st.write("Aisha Soltani , Eya Bahrouni , Hamza Bouguerra, Fares Messedi")
    # Exemple de structure à adapter :
    # col_a, col_b, col_c = st.columns(3)
    # with col_a:
    #     st.markdown("**Nom Prénom**\n\nData Engineering")
    # with col_b:
    #     st.markdown("**Nom Prénom**\n\nData Science")
    # with col_c:
    #     st.markdown("**Nom Prénom**\n\nWeb App")

    st.divider()
    st.caption("Application développée avec Streamlit — © 2026")