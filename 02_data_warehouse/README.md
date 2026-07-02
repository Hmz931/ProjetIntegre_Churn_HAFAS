# 02_data_warehouse/

Modèle dimensionnel et Data Warehouse — structure conforme à celle indiquée par
l'encadrant (`02_data_warehouse/README.md` du dépôt original).

## ✅ État actuel : validé sur un vrai serveur PostgreSQL

Le chargement complet a été testé et confirmé le 25/06/2026 : **7/7 tables chargées
avec succès, toutes les contraintes de clé primaire et étrangère appliquées**
(`dim_client`, `dim_branch`, `dim_account`, `dim_product`, `dim_closure`, `dim_date`,
`fact_account_event`). Trois bugs réels ont été trouvés et corrigés au cours de cette
validation (jointure sur clé nulle, encodage UTF-8 sous Windows, incompatibilité de
type entier/flottant sur une clé étrangère) — voir l'historique de
`01_etl/etl_pipeline/` pour le détail de chaque correction.

## Structure

```
02_data_warehouse/
├── schema/
│   └── create_tables.sql      DDL explicite des 7 tables (dimensions + faits)
├── load/
│   └── load_warehouse.py      Point d'entrée du chargement (appelle 01_etl/etl_pipeline/)
├── kpis.md                    Liste et formule SQL de chaque KPI métier
└── README.md                  Ce fichier
```

Le diagramme du modèle en étoile (`star_schema.png` dans la structure suggérée par
l'encadrant) est fourni sous forme de `.svg` plutôt que `.png`, dans
`01_etl/notebooks/DW.svg` — référencé ici plutôt que dupliqué, pour n'avoir qu'une
seule version à maintenir.

## Pourquoi `load_warehouse.py` est un simple appel à `01_etl/etl_pipeline/`

Le chargement réel (connexion SQLAlchemy, gestion des échecs, application des
contraintes) est déjà entièrement implémenté et validé dans
`01_etl/etl_pipeline/load.py`. `load_warehouse.py` ne réimplémente rien : il importe
et appelle ce module, pour respecter l'emplacement attendu par la structure du projet
sans dupliquer une logique qui devrait rester unique. Toute correction future du
chargement se fait donc dans un seul endroit (`01_etl/etl_pipeline/load.py`), pas
dans deux fichiers qui risqueraient de diverger.

## Comment peupler la base

```bash
export DB_USER=postgres
export DB_PASSWORD=votre_mot_de_passe
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=PIProject

cd 02_data_warehouse/load
python load_warehouse.py
```

Ou directement avec le DDL explicite (si vous préférez créer le schéma vous-même
plutôt que de laisser SQLAlchemy le générer implicitement) :

```bash
psql -U postgres -d PIProject -f schema/create_tables.sql
```

⚠️ Si vous utilisez `create_tables.sql`, relancez ensuite `load_warehouse.py` en
modifiant `01_etl/etl_pipeline/load.py` pour utiliser `if_exists="append"` au lieu de
`"replace"` — sinon `pandas.to_sql` recréera les tables et perdra les contraintes
posées par le DDL explicite. Pour un usage standard (laisser SQLAlchemy créer les
tables), `create_tables.sql` sert uniquement de référence/documentation indépendante.

## Schéma dimensionnel

Voir `01_etl/notebooks/DW.svg` pour le diagramme visuel, et `01_etl/README.md`
(section "Décisions de modélisation") pour la justification détaillée de chaque
choix de grain — notamment pourquoi `DIM_PRODUCT` est au grain contrat et non
catalogue, et pourquoi `churn` est calculé au niveau compte puis propagé.

```
DIM_CLIENT ──┐
DIM_DATE ────┤
DIM_BRANCH ──┼──► FACT_ACCOUNT_EVENT (grain : 1 ligne par événement compte/produit)
DIM_ACCOUNT ─┤
DIM_PRODUCT ─┤
DIM_CLOSURE ─┘
```

## KPIs

Voir `kpis.md` pour la liste complète avec leur équivalent SQL — utile pour
Power BI ou pour interroger la base sans repasser par Python/pandas.

## Reste à faire

- [ ] Décider si le "junk dimension" `DIM_PRODUCT` (grain contrat, cardinalité
      ~445 000 lignes) doit être repensé une fois les rapports Power BI conçus.
- [ ] Index supplémentaires si les requêtes Power BI s'avèrent lentes en pratique
      (3 index de base déjà créés dans `create_tables.sql` : `client_key`,
      `account_key`, `churn` sur `fact_account_event`).
- [ ] `region` dans `dim_branch` reste vide (non présent dans le fichier source) —
      à enrichir si un référentiel agences→région devient disponible.

