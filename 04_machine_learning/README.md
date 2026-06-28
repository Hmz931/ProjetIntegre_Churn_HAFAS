# 04_machine_learning/

## ✅ État actuel : notebook complet et validé

`notebooks/04_machine_learning.ipynb` implémente l'ensemble de la phase ML, de
l'import des données jusqu'à la recommandation finale — testé de bout en bout
contre les données réelles (82 cellules, 0 erreur).

## Contenu du notebook

| Section | Contenu |
|---|---|
| 1 | Import depuis PostgreSQL, avec repli automatique sur `etl_pipeline.pipeline.run_pipeline()` si aucun serveur n'est accessible |
| 2 | Analyse exploratoire orientée ML (distribution de la cible, corrélations, scatter plots) |
| 3 | Sélection des variables, avec justification individuelle de chaque exclusion |
| 4 / 4bis | Séparation X/y, traitement des valeurs manquantes (voir point de vigilance ci-dessous) |
| 5-6 | Encodage (One-Hot + fréquence selon la cardinalité), mise à l'échelle |
| 7-8 | Split train/test 80/20 stratifié, SMOTE (train uniquement) |
| 9 | Modèle de référence : régression logistique |
| 10 | 5 modèles supplémentaires : KNN, Arbre de décision, Random Forest, SVM, XGBoost — chacun avec/sans SMOTE |
| 11-12 | Tableau comparatif, importance des variables |
| 13 | Conclusion et pistes d'amélioration |

## Grain retenu

**Compte** (`ACCOUNT_NO`), pas événement ni client — conforme à la définition du
churn de `00_documentation/2_description_donnees.md`. Le notebook agrège
`fact_account_event` (grain événement) au grain compte avant tout entraînement.

## ⚠️ Fuite d'information détectée et corrigée pendant la construction du notebook

En testant une première version, l'analyse d'importance des variables (section 12)
a révélé qu'un indicateur de nullité (`acct_tenure_days_missing`) représentait
**89,5%** du poids de décision d'XGBoost — un chiffre anormal qui a déclenché une
vérification.

**Cause confirmée** : un correctif de nettoyage de dates dans
`01_etl/etl_pipeline/clean.py` (neutralisation de `ACCT_OPENING_DATE` quand elle
est postérieure à `ACCT_CLOSE_DATE`) ne s'applique qu'à des comptes déjà fermés —
rendant la nullité résultante de `acct_tenure_days`/`acct_balance` un proxy
quasi-parfait du label à prédire (100% de ces comptes sont `Closed`, vérifié), pas
un vrai signal métier.

**Correction appliquée** (section 4bis du notebook) : les indicateurs
`acct_tenure_days_missing` et `acct_balance_missing` ont été retirés des features.
`salary_missing` a été conservé après vérification qu'il s'agit d'un signal
légitime (taux de churn quasi identique, ~37% vs ~35%, que la donnée soit
manquante ou non).

**Résultat rassurant** : le F1-score d'XGBoost n'a quasiment pas changé après cette
correction (0,9465 contre 0,9460 avant) — le modèle disposait déjà de signaux
légitimes suffisants (`amount_total`, `nb_produits`, `acct_tenure_days` lui-même).

Cette découverte illustre une leçon générale : **toujours vérifier qu'une fuite de
performance apparente n'est pas un artefact du pipeline de nettoyage amont avant
de faire confiance à un résultat de modélisation.**

## Limitations connues et choix de performance

- **KNN** est évalué sur un sous-échantillon de 10 000 comptes de test (au lieu des
  82 118 utilisés par les autres modèles) — la prédiction KNN sur le jeu complet
  prend ~150 secondes, jugé disproportionné. Documenté explicitement dans le
  notebook (section 10.1), pour ne pas comparer KNN aux autres modèles comme si
  c'était à armes rigoureusement égales.
- **SVM** est entraîné sur un sous-échantillon de 20 000 comptes (sur les 328 469
  disponibles) — la complexité du noyau RBF rend l'entraînement sur le jeu complet
  trop coûteux en temps. Documenté de la même façon (section 10.4).
- **Temps d'exécution complet du notebook : ~15-20 minutes**, principalement dû à
  Random Forest (200 arbres, ~2 minutes pour les deux variantes avec/sans SMOTE).

## Comment exécuter

```bash
cd 04_machine_learning/notebooks
jupyter notebook 04_machine_learning.ipynb
```

Fonctionne avec ou sans serveur PostgreSQL actif (repli automatique sur le
pipeline ETL en mémoire si la connexion échoue — voir section 1 du notebook).

## Reste à faire (pistes documentées en section 13.6 du notebook)

- [ ] Optimisation des hyperparamètres (`GridSearchCV` / Optuna), non explorée
      par souci de temps d'exécution.
- [ ] Validation croisée (k-fold) plutôt qu'un seul découpage train/test.
- [ ] Explicabilité via SHAP pour des explications par prédiction individuelle.
- [ ] Revue systématique des autres corrections de l'ETL pour d'éventuels effets
      de bord similaires à la fuite détectée en section 4bis.
- [ ] Sauvegarde du modèle final (`.pkl` ou `.joblib`) pour réutilisation dans
      `05_web_app/`.
