# 01_etl/ - Pipeline ETL (Extract, Transform, Load)

Ce dossier contient le pipeline qui transforme `data/data_churn.txt` (528 883 lignes brutes)
en un entrepôt analytique propre (modèle en étoile), prêt pour `02_data_warehouse/` et
`04_machine_learning/`.

## Structure

```
01_etl/
├── etl_pipeline/           Module Python - toute la logique ETL
│   ├── __init__.py
│   ├── config.py           Constantes partagées (chemins, date de référence, mappings)
│   ├── extract.py          Lecture de data_churn.txt + des 8 fichiers dim_*.xlsx
│   ├── clean.py            Nettoyage : doublons, dates, valeurs manquantes
│   ├── dimension_lookup.py Décodage des codes anonymisés via les dimensions réelles
│   ├── dimensions.py       Construction des 6 dimensions du schéma en étoile
│   ├── fact.py             Construction de FACT_ACCOUNT_EVENT
│   ├── load.py             Chargement PostgreSQL (SQLAlchemy)
│   └── pipeline.py         Orchestrateur : enchaîne toutes les étapes
├── notebooks/
│   ├── 01_exploration.ipynb   EDA - exploration et qualité des données
│   ├── 02_ETL.ipynb            Exécute etl_pipeline/, affiche les résultats, calcule les KPIs
│   └── DW.svg                  Schéma du modèle dimensionnel (référence visuelle)
└── README.md                Ce fichier
```

Les scripts SQL de création de schéma (`CREATE TABLE` explicite) et de chargement
vivent désormais dans `02_data_warehouse/`, conformément à la structure imposée par
l'encadrant - voir `02_data_warehouse/README.md`.

## Pourquoi un module plutôt qu'un notebook unique ?

Un notebook monolithique mélange logique métier et exploration : il est difficile de
réutiliser "juste le nettoyage" depuis un autre notebook (ex. `04_machine_learning`), et
impossible de tester une étape indépendamment sans rejouer toutes les cellules précédentes.

Le découpage en modules (`extract` / `clean` / `dimensions` / `fact` / `load`) suit le
principe de responsabilité unique : chaque fichier fait une seule chose, et peut être
importé isolément :

```python
from etl_pipeline.extract import extract_all
from etl_pipeline.clean import clean_all

df_raw, dims_raw = extract_all()
df_clean = clean_all(df_raw)
# inspection de df_clean ici, sans construire les dimensions ni charger en base
```

`pipeline.py` est l'orchestrateur : il appelle les quatre autres modules dans l'ordre et
transmet les résultats d'une étape à la suivante.

## Comment exécuter le pipeline

### En script

```bash
cd 01_etl
python -m etl_pipeline.pipeline
```

### Depuis un notebook (recommandé pour explorer les résultats intermédiaires)

```python
import sys
sys.path.insert(0, "..")  # depuis 01_etl/notebooks/, remonte à 01_etl/
from etl_pipeline.pipeline import run_pipeline

resultats = run_pipeline(load_to_db=True)
df = resultats["df"]
fact = resultats["fact_account_event"]
dim_client = resultats["dimensions"]["dim_client"]
```

Voir `notebooks/02_ETL.ipynb` pour un exemple complet déjà exécuté.

### Sans PostgreSQL disponible

`run_pipeline(load_to_db=False)` ignore l'étape de chargement - utile pour itérer sur le
nettoyage ou les dimensions sans dépendre d'un serveur PostgreSQL actif. Même avec
`load_to_db=True`, si aucun serveur n'est accessible ou si le pilote `psycopg2` n'est pas
installé, le pipeline **continue sans planter** : chaque table affiche un avertissement
clair et reste disponible en mémoire (voir `etl_pipeline/load.py`).

## Décisions de modélisation - pourquoi elles sont ce qu'elles sont

### Grain de `FACT_ACCOUNT_EVENT` : 1 ligne par événement source

Le fichier `data_churn.txt` a pour grain natif (client, compte, produit) - une ligne par
combinaison. Trois grains étaient possibles pour la table de faits :

1. **Grain client** : une ligne par `CUSTOMER_NO`, en agrégeant tous ses comptes/produits.
2. **Grain compte** : une ligne par `ACCOUNT_NO`.
3. **Grain événement** : pas de réduction - chaque ligne source devient une ligne de fait.

Le choix retenu est le **grain événement**, validé en équipe, pour rester fidèle au grain
natif du fichier source et ne perdre aucune information contractuelle (montant, taux,
dates par contrat). C'est aussi celui qui correspond au nom du schéma cible
(`FACT_ACCOUNT_EVENT`, pas `FACT_ACCOUNT` ni `FACT_CLIENT`).

### Grain de `DIM_PRODUCT` : contrat, pas produit catalogue

Conséquence directe du choix précédent : les colonnes `AMOUNT`, `FIXEDRATE`, `STARTDATE`,
`MATURITYDATE`, `PRODUCT_STATUS` varient réellement **par contrat**, pas par produit
catalogue. Vérifié sur les données réelles : 157 produits sur 213 (74%) ont plusieurs
valeurs `AMOUNT` distinctes. Si `DIM_PRODUCT` avait gardé un grain "produit catalogue"
(une ligne par code produit), ces colonnes auraient dû soit être retirées de la dimension,
soit recevoir une valeur agrégée (moyenne) qui aurait perdu l'information précise par
contrat. Le schéma cible (`DW.svg`) place explicitement ces colonnes dans `DIM_PRODUCT` -
la solution cohérente est donc de construire `DIM_PRODUCT` au grain contrat, ce qui lui
donne une cardinalité proche de celle de la table de faits (dimension dite "dégénérée").
C'est un choix de modélisation assumé, pas un défaut du pipeline.

### Le `churn` est un attribut de compte, propagé sur ses événements

`ACCOUNT_STATUS` (et donc le `churn` qui en dérive) est vérifié **stable à 100% par
`ACCOUNT_NO`** dans les données réelles (aucun compte n'a deux statuts différents sur ses
lignes-événements). Le flag est donc calculé une seule fois par compte
(`fact.compute_churn_by_account`), puis propagé (broadcast) sur toutes les lignes de ce
compte - jamais recalculé indépendamment ligne par ligne. Cette vérification est faite
explicitement à l'exécution : si elle venait à échouer sur une future version des données,
un avertissement serait levé plutôt que de propager silencieusement une valeur incohérente.

### Intégration des dimensions réelles (`dim_*.xlsx`)

Les 8 fichiers fournis par l'encadrant n'étaient jusqu'ici jamais exploités. Ils
permettent de remplacer des hypothèses statistiques par des vérifications réelles :

- **`dim_INDUSTRY.xlsx`** confirme que le code `9000` (61,9% des lignes) signifie
  `"Other"`. Le code `9998` (40 187 clients) **n'existe pas du tout** dans ce référentiel -
  un vrai trou de données à signaler, pas une erreur du pipeline.
- **`dim_Closure_reason.xlsx`** décode enfin les motifs `BANK.REASON.N`, jusqu'ici opaques.
  Une classification heuristique simple (volontaire / involontaire) est appliquée à partir
  du libellé métier en clair - voir `etl_pipeline/dimension_lookup.classify_closure_voluntary`
  pour le détail et ses limites (certains motifs restent ambigus et ne sont volontairement
  pas forcés dans une catégorie).
- **`dim_CATEGORY_ACCOUNT.xlsx`** et **`dim_CURRENCY.xlsx`** enrichissent `DIM_ACCOUNT`
  avec des libellés lisibles.

⚠️ **Règle d'anonymat respectée** : `dim_Closure_reason.xlsx` contient encore le nom réel
de l'institution source (sous forme d'acronyme) dans certains libellés. Le nom est retiré
systématiquement avant toute exposition (voir `dimension_lookup._scrub_bank_name`), de la
même façon que le fichier principal l'a déjà fait via `data/anonymize.py`.

## Points de vigilance transmis à l'équipe (non résolus par le pipeline)

| Point | Détail | Action recommandée |
|---|---|---|
| Imputation de `ACCOUNT_STATUS` manquant | 0 valeur manquante sur le fichier réel actuel (vérifié), mais la règle existe dans le code (`clean.py`) pour une éventuelle mise à jour des données - imputation par `'Active'` par défaut | À valider explicitement avec l'équipe avant tout entraînement ML si ce cas se présente ; alternative plus prudente : exclure ces lignes |
| `STARTDATE`/`MATURITYDATE` format hérité | Décodé comme `CYYMMDD` (siècle + année + mois + jour), vérifié cohérent avec les plages de dates observées | Décodage appliqué et testé, mais à confirmer avec l'encadrant si possible (système source réel) |
| Motifs de clôture ambigus | 6 à 7 motifs sur 20 restent classifiés `None` (ni clairement volontaire, ni involontaire) par l'heuristique de mots-clés | Décision d'équipe à prendre si une classification plus fine est nécessaire pour le rapport |
| Code `INDUSTRY` 9998 | Absent de `dim_INDUSTRY.xlsx` (40 187 clients concernés) | Signaler comme limite des données dans le rapport |
| `DATE_OF_BIRTH` postérieure à `CUST_OPENING_DATE` | 53 lignes - incohérence réelle du système source, sans cause univoque identifiable (impossible de savoir laquelle des deux dates est fausse). **Décision explicite : non corrigée**, pour ne pas remplacer une valeur incertaine par une autre valeur tout aussi incertaine | Signaler comme limite des données dans le rapport |
| `LAST_REVIEW_DATE` postérieure à `NEXT__REVIEW_DATE` | 114 lignes - incohérence opérationnelle réelle (dossier revu après la date de prochaine revue prévue, sans mise à jour de cette dernière). **Décision explicite : non corrigée**, même raisonnement que ci-dessus | Signaler comme limite des données dans le rapport |

## Tests effectués

Ce pipeline a été exécuté de bout en bout contre le fichier réel `data_churn.txt`
(528 883 lignes) dans les conditions suivantes, toutes vérifiées sans erreur :
- Avec et sans le pilote PostgreSQL (`psycopg2`) installé.
- Avec les 8 fichiers `dim_*.xlsx` présents.
- Lancé en script (`python -m etl_pipeline.pipeline`, ou `python run.py` depuis la
  racine du projet) et importé depuis un notebook.
- **Chargement réel validé contre un vrai serveur PostgreSQL** (25/06/2026) :
  7/7 tables chargées avec succès, toutes les contraintes de clé primaire et
  étrangère appliquées sans erreur. Trois bugs réels ont été trouvés et corrigés
  au cours de cette validation :
  1. Jointure pandas sur clé `NaN`/`None` produisant un produit cartésien dans
     `dim_closure` (motifs de clôture non numérotés du référentiel).
  2. Encodage UTF-8 non forcé explicitement dans la chaîne de connexion psycopg2,
     provoquant un `UnicodeDecodeError` sous Windows (locale système non-UTF-8).
  3. Coercion silencieuse `int → float` par pandas dès qu'une colonne contient un
     `NaN` (`date_key` dans `fact_account_event`), cassant la compatibilité de
     type attendue par la contrainte de clé étrangère PostgreSQL (`bigint` vs
     `double precision`) - corrigé via `pandas.Int64Dtype()` (entier nullable).
  4. **Relance du pipeline sur une base déjà peuplée** : `pandas.to_sql(if_exists=
     "replace")` exécute un `DROP TABLE` implicite avant de recréer chaque
     dimension. Sur une base où `fact_account_event` existe déjà avec ses
     contraintes de clé étrangère vers les 6 dimensions, PostgreSQL refuse de
     supprimer une dimension tant que la table de faits la référence
     (`DependentObjectsStillExist`) - corrigé en supprimant explicitement
     `fact_account_event` en tout premier, avant toute opération sur les
     dimensions (voir `load.drop_fact_table_if_exists`).

Trois bugs supplémentaires ont été trouvés grâce à un script de test de cohérence
indépendant (`test_coherence_donnees.py`, à la racine du projet - ne modifie rien
dans `etl_pipeline/`, sert uniquement à vérifier après coup) :

  5. **`MARITAL_STATUS` incohérent pour 25 lignes (6 clients PM)** : la règle
     posée pour les personnes morales (`NATURE_CLIENT == 'PM'`) ne s'appliquait
     qu'aux valeurs manquantes (`NaN`), laissant passer des valeurs déjà présentes
     dans le fichier source (`M`, `C`...) incohérentes avec un statut de personne
     morale - corrigé en forçant la règle pour tout client `PM`, qu'une valeur
     existe déjà ou non.
  6. **`ACCT_OPENING_DATE` postérieure à `ACCT_CLOSE_DATE`** (33 571 lignes,
     impossible logiquement) : vérifié que la cause est une pollution par des
     dates proches de l'extraction du fichier source (ex. `2026-01-12`, répétée
     sur 6 072 lignes) - la vraie date d'ouverture n'étant pas reconstituable,
     ces valeurs sont neutralisées en `NaT` plutôt que conservées fausses.
  7. **`STARTDATE` postérieure à `MATURITYDATE`** (2 575 lignes, même mécanisme
     que le point 6) - `MATURITYDATE` reste cohérente avec `PRODUCT_STATUS=
     'EXPIRED'` sur la quasi-totalité des cas observés, donc c'est `STARTDATE`
     qui est neutralisée en `NaT`, pas `MATURITYDATE`.

Les résultats numériques (445 803 événements, 410 587 comptes, taux de churn 36,1% au
niveau compte et 41,2% au niveau événement) sont reproductibles et documentés dans
`notebooks/02_ETL.ipynb`.

⚠️ Note d'emplacement : le notebook narratif étape par étape (avec les décisions
commentées cellule par cellule) vit en réalité dans `01_etl/notbooks ETL/02_ETL.ipynb`
(nom de dossier historique, avec une faute de frappe - "notbooks"), pas dans
`01_etl/notebooks/`, qui contient l'exploration (`01_exploration.ipynb`) et la
documentation associée (`DW.svg`, `kpis_churn_banking.md`). Les deux dossiers
coexistent depuis le début du projet ; à fusionner si l'équipe veut nettoyer
l'arborescence avant le rapport final.

## `date_key` - vérification explicite de la nullité (ajoutée)

`date_key` est la seule clé étrangère de `fact_account_event` pour laquelle une valeur
manquante est **normale et attendue**, pas une erreur de jointure : elle vient de
`ACCT_OPENING_DATE`, qui est volontairement conservée à `NaT` pour les comptes
concernés (voir `TOLERATED_MISSING_COLUMNS` dans `config.py`).

Jusqu'ici, `fact.py` gérait cette nullité silencieusement (aucun contrôle explicite,
contrairement aux quatre autres clés étrangères qui sont vérifiées orpheline par
orpheline). Un contrôle a été ajouté dans `build_fact_account_event()` : le nombre de
`date_key` manquants doit être **strictement égal** au nombre d'`ACCT_OPENING_DATE`
manquantes en amont. Si ce n'est pas le cas, un `logger.error` explicite est levé
(un écart signalerait un vrai échec de jointure - ex. une date valide en dehors de la
plage `dim_date`, ou un souci de normalisation d'heure - pas une nullité structurelle).

Vérifié contre le fichier réel (`data_churn.txt`) :

| Pipeline | `date_key` NULL | % de la table de faits |
|---|---|---|
| `etl_pipeline/` (production, avec la correction `ACCT_OPENING_DATE` > `ACCT_CLOSE_DATE`, 33 571 lignes neutralisées en plus) | 134 056 | 30,1% |
| `notbooks ETL/02_ETL.ipynb` (notebook étape par étape, sans cette correction) | 100 485 | 22,5% |

L'écart entre les deux (33 571 lignes, exactement le nombre de la correction n°6
listée plus haut) confirme que les deux pipelines sont cohérents entre eux une fois
qu'on tient compte de cette différence de traitement - mais il signale aussi que
**le notebook et le pipeline Python ne produisent pas exactement le même
`fact_account_event`** tant que cette correction n'y est pas répliquée. À harmoniser
si le notebook doit servir de référence unique pour le rapport final. `create_tables.sql`
citait auparavant "~22,5%" dans son commentaire - c'est la valeur du notebook, pas
celle de la production ; corrigé pour refléter 30,1% (voir `02_data_warehouse/README.md`).

## Ajout de la table de faits dans le notebook narratif (`notbooks ETL/02_ETL.ipynb`)

Le notebook s'arrêtait jusqu'ici après `dim_client` et `dim_produit` (pas de table de
faits construite dans ce notebook, contrairement à `etl_pipeline/fact.py`). Une section
"Table de faits - FACT_ACCOUNT_EVENT" a été ajoutée à la fin (12 nouvelles cellules),
avec le même grain et la même logique que `etl_pipeline/fact.py` (churn calculé une
fois par compte puis propagé, contrôle des clés orphelines, contrôle strict de la
nullité de `date_key`), exécutée de bout en bout contre `data_churn.txt` sans erreur.

Deux incohérences ont été repérées en construisant cette section, et sont documentées
en tête de la nouvelle partie du notebook pour que l'équipe les corrige :

- **`CLOSURE_REASON`** : la cellule de nettoyage remplit les comptes actifs avec la
  chaîne littérale `"Non fermé"` (minuscule, accentuée), alors que le message affiché
  par la même cellule et le reste du projet (`etl_pipeline/`, `create_tables.sql`)
  utilisent la convention `"NON_FERME"`. Les deux valeurs ne matcheront pas dans un
  futur merge avec `dim_Closure_reason.xlsx`.
- **`dim_produit`** : construite dans le notebook au grain **catalogue**
  (`PRODUCT_LINE`/`PRODUCT_GROUP`/`PRODUCT` dédupliqués, 226 lignes), alors que la
  décision d'équipe documentée plus haut dans ce fichier retient le grain **contrat**
  (une ligne par ligne source, 74% des produits ayant plusieurs montants `AMOUNT`
  distincts). La nouvelle section de table de faits ne réutilise donc pas ce
  `dim_produit` - elle reconstruit une clé produit au bon grain directement dans la
  section faits, avec une note explicite à ce sujet.

## Comparaison Talend vs Python (ETL graphique vs code)

Question fréquente en soutenance : pourquoi un pipeline Python plutôt qu'un outil ETL
graphique comme Talend Open Studio, plus classique dans un cursus Business Analytics.
Comparaison factuelle, basée sur l'expérience réelle de ce projet (7 bugs trouvés et
corrigés en cours de route, cf. section "Tests effectués" ci-dessus) :

| Critère | Talend Open Studio | Python (pandas, ce projet) |
|---|---|---|
| **Courbe d'apprentissage** | Interface visuelle drag & drop, prise en main rapide pour des transformations simples | Nécessite de savoir coder en Python/pandas, mais l'équipe le maîtrisait déjà (cours du programme) |
| **Traçabilité / historique Git** | Les jobs sont stockés dans un format XML propriétaire compilé - un `git diff` entre deux versions d'un job est illisible, la revue de code entre membres de l'équipe est quasi impossible | Chaque modification de règle métier est un `git diff` de quelques lignes Python, directement lisible et commentable en revue de code - décisif pour un travail à 4 avec des allers-retours fréquents |
| **Débogage** | Le débogueur visuel montre le flux de données mais isole mal une transformation précise sur 528 883 lignes ; les messages d'erreur Java sous-jacents sont peu explicites pour des étudiants | `pandas` + `logging` permettent d'isoler une colonne, une condition ou une ligne précise en une commande (`df[condition]`) - c'est ainsi que les 7 bugs réels du projet ont été trouvés et documentés avec leur nombre exact de lignes concernées |
| **Réutilisabilité / tests automatisés** | Un job Talend s'exécute comme une boîte ; l'écrire comme fonction testable unitairement (au sens `pytest`) n'est pas le mode de fonctionnement naturel de l'outil | Chaque étape est une fonction Python pure (`clean.py`, `dimensions.py`...), réutilisable indépendamment et vérifiée par `test_coherence_donnees.py` (32 tests automatisés) |
| **Installation / environnement** | Lourde : nécessite un JDK, un IDE propriétaire (~1-2 Go), version Open Studio plus activement maintenue en 2026 | Légère : `pip install -r requirements.txt`, fonctionne identiquement sur Windows/Mac/Linux, aucune dépendance propriétaire |
| **Connecteurs prêts à l'emploi** | Nombreux connecteurs graphiques (bases de données, API, fichiers) sans code à écrire | `pandas`/`sqlalchemy` couvrent CSV/Excel/PostgreSQL nativement ; un connecteur exotique demanderait d'écrire soi-même l'intégration |
| **Approche visuelle du flux** | Le flux de données (extraction → transformation → chargement) est visible d'un coup d'œil sur le canevas, utile pour présenter à un non-technicien | Le flux est linéaire dans le code (`pipeline.py` orchestre `extract → clean → dimensions → fact → load`), moins immédiatement visuel mais documenté par le diagramme `DW.svg` et ce README |
| **Volumétrie réelle du projet (528 883 lignes)** | Gérable, mais les transformations complexes (ex. décodage `CYYMMDD`, classification heuristique des motifs de clôture) demandent des composants Talend avancés (`tJavaRow`) qui reviennent, de fait, à écrire du code Java dans l'outil | Une fonction pandas vectorisée traite l'ensemble du fichier en quelques secondes (pipeline complet : ~15s hors chargement PostgreSQL) |

**Choix retenu pour ce projet : Python.** Décisif : la traçabilité Git pour un travail
d'équipe à 4 avec relecture de code, et la possibilité d'écrire des tests automatisés
(`test_coherence_donnees.py`) qui ont concrètement trouvé 3 des 7 bugs corrigés.
Inconvénient assumé : moins immédiatement lisible pour un public non-technique en
soutenance - compensé par le diagramme `DW.svg` et ce README.