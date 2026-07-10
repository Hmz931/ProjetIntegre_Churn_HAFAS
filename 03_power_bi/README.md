# Documentation des KPI - Analyse du Churn Bancaire
### Banque ESPRIT - Modèle DAX / Power BI

---

## Introduction

Ce document présente l'ensemble des indicateurs clés de performance (KPI) définis dans le modèle DAX du tableau de bord d'analyse du churn (attrition client) de la Banque ESPRIT. Pour chaque KPI, on trouvera :

- **Importance et signification** : pourquoi ce KPI compte pour le pilotage métier.
- **Mode de calcul** : la logique métier derrière la mesure.
- **Formule DAX** : le code exact utilisé dans le modèle.
- **Interprétation** : comment lire et exploiter le résultat.

---

## 1. Taux de Churn Global

### Importance et signification
C'est le KPI fondateur de tout le tableau de bord. Il mesure la proportion de comptes ayant clôturé/quitté la banque par rapport au portefeuille total. Il sert de baromètre global de la santé de la relation client et de référence pour comparer tous les autres axes d'analyse (segment, produit, âge, etc.).

### Mode de calcul
Nombre de comptes en churn (`churn = 1`) divisé par le nombre total de comptes, exprimé en pourcentage.

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Taux Churn %] =
    DIVIDE(
        CALCULATE(COUNTROWS('public fact_account_event'), 'public fact_account_event'[churn] = 1),
        COUNTROWS('public fact_account_event')
    ) * 100
```

### Interprétation
Un taux élevé (par exemple > 20 %) signale un problème structurel de fidélisation nécessitant une action corrective immédiate. Ce chiffre doit toujours être lu avec son évolution dans le temps (voir KPI 9) et non de façon isolée.

---

## 2. Taux de Rétention

### Importance et signification
Complément symétrique du taux de churn, il met l'accent sur la performance positive (clients conservés) plutôt que sur la perte. Il est souvent préféré en communication à la direction car il valorise les efforts de fidélisation.

### Mode de calcul
Nombre de comptes actifs (`churn = 0`) divisé par le nombre total de comptes.

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Taux Retention %] =
    DIVIDE(
        CALCULATE(COUNTROWS('public fact_account_event'), 'public fact_account_event'[churn] = 0),
        COUNTROWS('public fact_account_event')
    ) * 100

MEASURE 'public fact_account_event'[Retention par Segment] =
    CALCULATE(
        [Taux Retention %],
        ALLEXCEPT('public fact_account_event', 'public dim_client'[PARTYCLASS])
    )
```

### Interprétation
`Taux Retention % = 100 - Taux Churn %`. La déclinaison par segment (`Retention par Segment`) permet d'identifier quels types de clientèle (Retail, Corporate, Elite, etc.) restent le plus fidèles, indépendamment des autres filtres actifs dans le rapport grâce à `ALLEXCEPT`.

---

## 3. Ancienneté Moyenne des Clients (Churned vs Actifs)

### Importance et signification
Ce KPI permet de savoir si le churn touche davantage les nouveaux clients (signe d'un problème d'intégration/onboarding) ou les clients historiques (signe d'une érosion de la fidélité à long terme).

### Mode de calcul
Moyenne de l'ancienneté (`client_tenure_days` convertie en années), calculée séparément pour les clients churnés et les clients actifs.

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Anciennete Moyenne Churned] =
    CALCULATE(
        AVERAGEX('public fact_account_event', 'public fact_account_event'[client_tenure_days] / 365),
        'public fact_account_event'[churn] = 1
    )

MEASURE 'public fact_account_event'[Anciennete Moyenne Actifs] =
    CALCULATE(
        AVERAGEX('public fact_account_event', 'public fact_account_event'[client_tenure_days] / 365),
        'public fact_account_event'[churn] = 0
    )
```

### Interprétation
Si l'ancienneté moyenne des churnés est nettement inférieure à celle des actifs, cela indique un déficit d'engagement dans les premières années de la relation (opportunité de renforcer le parcours d'accueil). À l'inverse, une ancienneté élevée chez les churnés indique une lassitude progressive de la clientèle fidèle.

---

## 4. Taux de Churn par Tranche d'Âge

### Importance et signification
Permet d'identifier les générations de clients les plus exposées au risque de départ, afin d'adapter les offres et la communication marketing (ex. digitalisation pour les jeunes, accompagnement personnalisé pour les seniors).

### Mode de calcul
Taux de churn calculé sur l'ensemble du périmètre, puis ventilé par tranche d'âge construite dynamiquement via une logique conditionnelle.

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Churn Rate par Age] =
    DIVIDE(
        CALCULATE(COUNTROWS('public fact_account_event'), 'public fact_account_event'[churn] = 1),
        COUNTROWS('public fact_account_event')
    ) * 100
```
```dax
EVALUATE
ADDCOLUMNS(
    SUMMARIZECOLUMNS(
        'public dim_client'[age],
        "Churn Rate %", [Churn Rate par Age]
    ),
    "Tranche Age",
    SWITCH(
        TRUE(),
        'public dim_client'[age] <= 30, "18-30",
        'public dim_client'[age] <= 40, "31-40",
        'public dim_client'[age] <= 50, "41-50",
        'public dim_client'[age] <= 60, "51-60",
        'public dim_client'[age] > 60,  "60+",
        "Inconnu"
    )
)
```

### Interprétation
Un pic de churn chez les 18-30 ans suggère un manque d'attractivité des offres pour les jeunes actifs (souvent plus sensibles aux banques en ligne). Un pic chez les 60+ peut révéler des problématiques d'accessibilité ou de succession patrimoniale.

---

## 5. Solde Moyen par Statut (Churned vs Actifs)

### Importance et signification
Ce KPI évalue l'impact financier du churn : perd-on des clients à faible valeur ou des clients à fort solde ? Il conditionne la priorisation des actions de rétention (un client à solde élevé mérite un traitement prioritaire).

### Mode de calcul
Moyenne du solde de compte (`ACCT_BALANCE`) calculée séparément pour les comptes churnés et actifs, puis écart entre les deux.

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Solde Moyen Churned] =
    CALCULATE(
        AVERAGE('public fact_account_event'[ACCT_BALANCE]),
        'public fact_account_event'[churn] = 1
    )

MEASURE 'public fact_account_event'[Solde Moyen Actifs] =
    CALCULATE(
        AVERAGE('public fact_account_event'[ACCT_BALANCE]),
        'public fact_account_event'[churn] = 0
    )

MEASURE 'public fact_account_event'[Ecart Solde Churned vs Actifs] =
    [Solde Moyen Churned] - [Solde Moyen Actifs]
```

### Interprétation
Un écart négatif important (solde des churnés très inférieur à celui des actifs) est plutôt rassurant : la banque perd des clients à faible valeur ajoutée. Un écart positif ou proche de zéro est un signal d'alerte : des clients à forte valeur quittent également la banque.

---

## 6. Salaire Moyen par Statut

### Importance et signification
Complète l'analyse du profil socio-économique des clients qui partent, utile pour le ciblage des offres de fidélisation (crédit, épargne, packages premium).

### Mode de calcul
Moyenne du salaire déclaré (`SALARY`), séparée entre clients churnés et actifs.

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Salaire Moyen Churned] =
    CALCULATE(
        AVERAGE('public fact_account_event'[SALARY]),
        'public fact_account_event'[churn] = 1
    )

MEASURE 'public fact_account_event'[Salaire Moyen Actifs] =
    CALCULATE(
        AVERAGE('public fact_account_event'[SALARY]),
        'public fact_account_event'[churn] = 0
    )
```

### Interprétation
Si le salaire moyen des churnés est significativement plus élevé, cela peut indiquer que la banque perd sa clientèle la plus solvable, potentiellement au profit de concurrents offrant de meilleures conditions (taux, avantages).

---

## 7. Taux de Churn par Segment Client

### Importance et signification
Le segment (`PARTYCLASS` : Retail, Corporate, Corporate Small, Elite…) reflète des besoins et des niveaux de rentabilité très différents. Ce KPI oriente les stratégies de rétention différenciées par typologie de clientèle.

### Mode de calcul
Taux de churn recalculé dans le contexte de filtre de chaque segment via `SUMMARIZECOLUMNS`.

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Churn Rate par Segment] =
    DIVIDE(
        CALCULATE(COUNTROWS('public fact_account_event'), 'public fact_account_event'[churn] = 1),
        COUNTROWS('public fact_account_event')
    ) * 100
```
```dax
EVALUATE
SUMMARIZECOLUMNS(
    'public dim_client'[PARTYCLASS],
    "Churn Rate %",      [Churn Rate par Segment],
    "Taux Retention %",  [Retention par Segment],
    "Duree Churn (ans)", [Duree Churn par Segment],
    "VaR (TND)",         [VaR Churn Total (TND)]
)
ORDER BY [Churn Rate %] DESC
```

### Interprétation
Le tri décroissant met immédiatement en évidence le segment le plus à risque. Un churn élevé sur le segment « Corporate » est particulièrement critique compte tenu des montants généralement plus importants en jeu (voir également le KPI VaR).

---

## 8. Taux de Churn par Ligne / Groupe de Produit

### Importance et signification
Permet d'identifier les produits bancaires (dépôts, crédits, comptes courants…) les plus associés à la résiliation, afin de revoir leur tarification, leurs conditions ou leur accompagnement commercial.

### Mode de calcul
Taux de churn ventilé par `PRODUCT_LINE` et par `PRODUCT_GROUP`.

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Churn Rate par Produit Line] =
    DIVIDE(
        CALCULATE(COUNTROWS('public fact_account_event'), 'public fact_account_event'[churn] = 1),
        COUNTROWS('public fact_account_event')
    ) * 100

MEASURE 'public fact_account_event'[Churn Rate par Produit Group] =
    DIVIDE(
        CALCULATE(COUNTROWS('public fact_account_event'), 'public fact_account_event'[churn] = 1),
        COUNTROWS('public fact_account_event')
    ) * 100
```
```dax
EVALUATE
SUMMARIZECOLUMNS(
    'public dim_product'[PRODUCT_LINE],
    "Churn Rate %",      [Churn Rate par Produit Line],
    "VaR (TND)",         [VaR Churn Deposits],
    "Duree Churn (ans)", [Duree Churn par Produit]
)
ORDER BY [Churn Rate %] DESC
```

### Interprétation
Si la ligne « DEPOSITS » affiche à la fois un taux de churn élevé et une VaR importante, cela signale une fuite de liquidités préoccupante pour la banque, à traiter en priorité (voir KPI 15 — VaR Churn).

---

## 9. Taux de Churn par Score KYC (Know Your Customer)

### Importance et signification
Le score KYC (`LR`, `MR`, `H1`, `H2`, `H3`) reflète le niveau de risque réglementaire/conformité du client. Croiser ce score avec le churn permet de vérifier si les procédures de conformité (plus lourdes pour les profils à risque élevé) génèrent de l'insatisfaction et du départ client.

### Mode de calcul
Taux de churn ventilé par modalité de `SCORE_KYC`, avec un ordre ordinal reconstitué (LR=0 → H3=4) pour un tri logique croissant du risque.

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Churn Rate par KYC] =
    DIVIDE(
        CALCULATE(COUNTROWS('public fact_account_event'), 'public fact_account_event'[churn] = 1),
        COUNTROWS('public fact_account_event')
    ) * 100
```
```dax
EVALUATE
ADDCOLUMNS(
    SUMMARIZECOLUMNS(
        'public dim_client'[SCORE_KYC],
        "Churn Rate %", [Churn Rate par KYC]
    ),
    "KYC Risk Ordinal",
    SWITCH(
        'public dim_client'[SCORE_KYC],
        "LR", 0, "MR", 1, "H1", 2, "H2", 3, "H3", 4,
        BLANK()
    )
)
ORDER BY [KYC Risk Ordinal]
```

### Interprétation
Une corrélation positive entre le niveau de risque KYC et le taux de churn peut indiquer que les contraintes de conformité (justificatifs, blocages, contrôles renforcés) pèsent sur l'expérience client des profils à risque élevé.

---

## 10. Tendance du Churn dans le Temps (Annuel / Mensuel / YoY)

### Importance et signification
Un KPI statique ne dit rien sur la dynamique. Ce KPI permet de suivre l'évolution du churn dans la durée, de détecter les saisonnalités et de mesurer l'impact des actions correctives mises en place.

### Mode de calcul
Comptage des churns par année et par mois, complété par un calcul de croissance d'une année sur l'autre (Year-over-Year) via `DATEADD`.

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Churns par Annee] =
    CALCULATE(
        COUNTROWS('public fact_account_event'),
        'public fact_account_event'[churn] = 1
    )

MEASURE 'public fact_account_event'[Churns par Mois] =
    CALCULATE(
        COUNTROWS('public fact_account_event'),
        'public fact_account_event'[churn] = 1
    )

MEASURE 'public fact_account_event'[Croissance Churn YoY %] =
    VAR annee_courante = [Churns par Annee]
    VAR annee_precedente =
        CALCULATE(
            [Churns par Annee],
            DATEADD('public dim_date'[full_date], -1, YEAR)
        )
    RETURN
        DIVIDE(annee_courante - annee_precedente, annee_precedente) * 100
```

### Interprétation
Une croissance YoY positive indique une aggravation de l'attrition d'une année sur l'autre ; une valeur négative indique une amélioration. C'est le KPI de référence pour évaluer l'efficacité des plans d'action de fidélisation dans la durée.

---

## 11. Complétude du Dossier Client (KYC/Onboarding)

### Importance et signification
Un dossier client incomplet (`COMPLETED_FILE ≠ "YES"`) peut être à la fois une cause et une conséquence du désengagement. Ce KPI teste l'hypothèse selon laquelle la qualité du dossier administratif est corrélée à la fidélité.

### Mode de calcul
Pourcentage de comptes ayant un dossier complet, puis comparaison du taux de churn entre dossiers complets et incomplets.

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Taux Dossiers Complets %] =
    DIVIDE(
        CALCULATE(
            COUNTROWS('public fact_account_event'),
            'public dim_client'[COMPLETED_FILE] = "YES"
        ),
        COUNTROWS('public fact_account_event')
    ) * 100

MEASURE 'public fact_account_event'[Churn Rate Dossier Incomplet] =
    CALCULATE(
        DIVIDE(
            CALCULATE(COUNTROWS('public fact_account_event'), 'public fact_account_event'[churn] = 1),
            COUNTROWS('public fact_account_event')
        ),
        'public dim_client'[COMPLETED_FILE] <> "YES"
    ) * 100

MEASURE 'public fact_account_event'[Churn Rate Dossier Complet] =
    CALCULATE(
        DIVIDE(
            CALCULATE(COUNTROWS('public fact_account_event'), 'public fact_account_event'[churn] = 1),
            COUNTROWS('public fact_account_event')
        ),
        'public dim_client'[COMPLETED_FILE] = "YES"
    ) * 100
```

### Interprétation
Si `Churn Rate Dossier Incomplet` est significativement supérieur à `Churn Rate Dossier Complet`, cela plaide pour un renforcement des processus d'onboarding et de mise à jour documentaire, qui deviendrait un levier direct de rétention.

---

## 12. Taux de Churn par Situation Matrimoniale

### Importance et signification
Indicateur socio-démographique complémentaire, utile pour affiner le profilage client dans les modèles de scoring et personnaliser la communication (ex. offres familiales, produits d'épargne).

### Mode de calcul
Taux de churn ventilé par modalité de `MARITAL_STATUS`, avec libellés reconstitués (M, C, D, V).

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Churn Rate par Statut Civil] =
    DIVIDE(
        CALCULATE(COUNTROWS('public fact_account_event'), 'public fact_account_event'[churn] = 1),
        COUNTROWS('public fact_account_event')
    ) * 100
```
```dax
EVALUATE
ADDCOLUMNS(
    SUMMARIZECOLUMNS(
        'public dim_client'[MARITAL_STATUS],
        "Churn Rate %", [Churn Rate par Statut Civil]
    ),
    "Libellé Statut Civil",
    SWITCH(
        'public dim_client'[MARITAL_STATUS],
        "M", "Marié(e)",
        "C", "Célibataire",
        "D", "Divorcé(e)",
        "V", "Veuf/ve",
        "Inconnu"
    )
)
ORDER BY [Churn Rate %] DESC
```

### Interprétation
À utiliser avec prudence : ce KPI est indicatif et ne doit pas fonder de décisions discriminatoires. Il sert surtout à enrichir des personas clients dans une logique de marketing relationnel.

---

## 13. Ratio Solde / Salaire

### Importance et signification
Ce ratio mesure la capacité d'épargne relative du client (combien de fois son salaire il conserve en solde). Il aide à détecter des comportements financiers atypiques précédant un départ (par ex. vidage progressif du compte).

### Mode de calcul
Moyenne du ratio `ACCT_BALANCE / (SALARY + 1)` (le +1 évite la division par zéro), calculée séparément pour churnés et actifs.

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Ratio Moyen Churned] =
    CALCULATE(
        AVERAGEX(
            'public fact_account_event',
            'public fact_account_event'[ACCT_BALANCE] / ('public fact_account_event'[SALARY] + 1)
        ),
        'public fact_account_event'[churn] = 1
    )

MEASURE 'public fact_account_event'[Ratio Moyen Actifs] =
    CALCULATE(
        AVERAGEX(
            'public fact_account_event',
            'public fact_account_event'[ACCT_BALANCE] / ('public fact_account_event'[SALARY] + 1)
        ),
        'public fact_account_event'[churn] = 0
    )
```

### Interprétation
Un ratio anormalement bas chez les clients churnés juste avant la clôture peut indiquer un « vidage » progressif du compte, signal précurseur exploitable pour une alerte préventive (early warning).

---

## 14. Profondeur de Relation (Nombre de Produits Détenus)

### Importance et signification
Principe classique en banque de détail : plus un client détient de produits (compte, carte, crédit, épargne…), plus son coût de sortie est élevé et sa fidélité forte. Ce KPI teste directement cette hypothèse.

### Mode de calcul
Taux de churn ventilé par nombre de comptes/produits détenus (`nb_accounts`), regroupé en buckets (1, 2, 3, 4, 5+ produits).

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Churn Rate par Profondeur] =
    DIVIDE(
        CALCULATE(COUNTROWS('public fact_account_event'), 'public fact_account_event'[churn] = 1),
        COUNTROWS('public fact_account_event')
    ) * 100
```
```dax
EVALUATE
ADDCOLUMNS(
    SUMMARIZECOLUMNS(
        'public fact_account_event'[nb_accounts],
        "Churn Rate %", [Churn Rate par Profondeur]
    ),
    "Bucket Profondeur",
    SWITCH(
        TRUE(),
        'public fact_account_event'[nb_accounts] = 1, "1 produit",
        'public fact_account_event'[nb_accounts] = 2, "2 produits",
        'public fact_account_event'[nb_accounts] = 3, "3 produits",
        'public fact_account_event'[nb_accounts] = 4, "4 produits",
        'public fact_account_event'[nb_accounts] >= 5, "5+ produits",
        "Inconnu"
    )
)
ORDER BY 'public fact_account_event'[nb_accounts]
```

### Interprétation
Si le taux de churn décroît régulièrement à mesure que le nombre de produits augmente, cela confirme l'intérêt stratégique du cross-selling comme levier de rétention.

---

## 15. Valeur à Risque du Churn (VaR Churn)

### Importance et signification
C'est le KPI qui traduit le churn en impact financier concret (en TND). Il permet de prioriser les actions de rétention non pas selon le nombre de clients perdus, mais selon les montants réellement en jeu — essentiel pour arbitrer les ressources commerciales.

### Mode de calcul
Somme des soldes de compte (`ACCT_BALANCE`) des comptes churnés, globalement puis déclinée par segment Corporate, par niveau de risque KYC élevé (H2/H3) et par ligne de produit Deposits.

### Formule DAX
```dax
MEASURE 'public fact_account_event'[VaR Churn Total (TND)] =
    CALCULATE(
        SUM('public fact_account_event'[ACCT_BALANCE]),
        'public fact_account_event'[churn] = 1
    )

MEASURE 'public fact_account_event'[VaR Churn Corporate] =
    CALCULATE(
        SUM('public fact_account_event'[ACCT_BALANCE]),
        'public fact_account_event'[churn] = 1,
        'public dim_client'[PARTYCLASS] = "Corporate"
    )

MEASURE 'public fact_account_event'[VaR Churn KYC Eleve] =
    CALCULATE(
        SUM('public fact_account_event'[ACCT_BALANCE]),
        'public fact_account_event'[churn] = 1,
        'public dim_client'[SCORE_KYC] IN {"H2", "H3"}
    )

MEASURE 'public fact_account_event'[VaR Churn Deposits] =
    CALCULATE(
        SUM('public fact_account_event'[ACCT_BALANCE]),
        'public fact_account_event'[churn] = 1,
        'public dim_product'[PRODUCT_LINE] = "DEPOSITS"
    )
```

### Interprétation
Une VaR Corporate élevée, même avec peu de clients concernés, justifie un traitement VIP individualisé (contact direct du chargé de compte). C'est un KPI clé pour le comité de direction, car il exprime le churn en langage financier plutôt qu'en volume.

---

## 16. Time-to-Churn (Durée Moyenne Avant Churn)

### Importance et signification
Ce KPI mesure la durée de vie moyenne d'un compte avant sa clôture. Il permet d'identifier le moment critique du cycle de vie client où le risque de départ est maximal, afin de déclencher des actions préventives ciblées dans le temps.

### Mode de calcul
Moyenne de `acct_tenure_days` (converti en années) uniquement sur les comptes churnés, déclinée par segment et par produit.

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Duree Moyenne Avant Churn (Annees)] =
    CALCULATE(
        AVERAGEX('public fact_account_event', 'public fact_account_event'[acct_tenure_days] / 365),
        'public fact_account_event'[churn] = 1
    )

MEASURE 'public fact_account_event'[Duree Churn par Segment] =
    CALCULATE(
        [Duree Moyenne Avant Churn (Annees)],
        ALLEXCEPT('public fact_account_event', 'public dim_client'[PARTYCLASS])
    )

MEASURE 'public fact_account_event'[Duree Churn par Produit] =
    CALCULATE(
        [Duree Moyenne Avant Churn (Annees)],
        ALLEXCEPT('public fact_account_event', 'public dim_product'[PRODUCT_LINE])
    )
```

### Interprétation
Une durée moyenne courte (par ex. moins d'un an) indique un problème d'intégration initiale des nouveaux comptes. Une durée longue indique plutôt une érosion progressive de la satisfaction, nécessitant des points de contact réguliers tout au long de la relation.

---

## 17. Churn Risk Index (Score de Risque Composite)

### Importance et signification
C'est le KPI le plus avancé du modèle : un score prédictif composite combinant quatre dimensions de risque (KYC, segment, complétude du dossier, produit) en un seul indicateur actionnable, permettant de cibler proactivement les clients à surveiller avant même qu'ils ne churnent.

### Mode de calcul
Somme pondérée de quatre sous-scores :
- **Score KYC** : de 0 (LR) à 4 (H3).
- **Score Segment** : Retail/Corporate Small = 1, Elite = 2, Corporate = 4.
- **Score Dossier** : +1 si le dossier n'est pas complet, 0 sinon.
- **Score Produit** : Deposits = 3, Lending = 2, Accounts = 0.

Le score total est ensuite classé en trois catégories de risque.

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Risk Score Brut] =
    VAR kyc_score =
        SWITCH(
            MAX('public dim_client'[SCORE_KYC]),
            "LR", 0, "MR", 1, "H1", 2, "H2", 3, "H3", 4, 0
        )
    VAR segment_score =
        SWITCH(
            MAX('public dim_client'[PARTYCLASS]),
            "Retail", 1, "Corporate Small", 1, "Elite", 2, "Corporate", 4, 0
        )
    VAR file_score =
        IF(MAX('public dim_client'[COMPLETED_FILE]) = "YES", 0, 1)
    VAR product_score =
        SWITCH(
            MAX('public dim_product'[PRODUCT_LINE]),
            "DEPOSITS", 3, "LENDING", 2, "ACCOUNTS", 0, 0
        )
    RETURN
        kyc_score + segment_score + file_score + product_score

MEASURE 'public fact_account_event'[Churn Risk Category] =
    SWITCH(
        TRUE(),
        [Risk Score Brut] >= 7, "Risque Élevé",
        [Risk Score Brut] >= 4, "Risque Moyen",
        "Risque Faible"
    )

MEASURE 'public fact_account_event'[Nb Clients Risque Eleve] =
    -- (logique identique à Risk Score Brut)
    -- retourne DISTINCTCOUNT(client_key) si score >= 7, sinon BLANK()

MEASURE 'public fact_account_event'[VaR Risque Eleve (TND)] =
    -- (logique identique à Risk Score Brut)
    -- retourne SUM(ACCT_BALANCE) si score >= 7, sinon BLANK()
```

### Interprétation
- **Risque Élevé (score ≥ 7)** : clients à surveiller en priorité absolue, à intégrer dans une campagne de rétention proactive.
- **Risque Moyen (4 ≤ score < 7)** : clients à suivre, actions de fidélisation standard.
- **Risque Faible (score < 4)** : clients stables, pas d'action urgente nécessaire.

Croisé avec `Nb Clients Risque Eleve` et `VaR Risque Eleve (TND)`, ce KPI permet de dimensionner concrètement l'effort commercial nécessaire (combien de clients, pour quel montant en jeu).

---

## 18. Churn Volontaire vs Involontaire

### Importance et signification
Distingue les départs choisis par le client (insatisfaction, concurrence) des clôtures subies ou administratives (décès, radiation, fraude). Cette distinction est essentielle : seul le churn volontaire est réellement « pilotable » par des actions de rétention.

### Mode de calcul
Pourcentage de churns marqués comme volontaires (`is_voluntary = TRUE()`) parmi l'ensemble des churns.

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Churn Voluntaire %] =
    DIVIDE(
        CALCULATE(
            COUNTROWS('public fact_account_event'),
            'public fact_account_event'[churn] = 1,
            'public dim_closure'[is_voluntary] = TRUE()
        ),
        CALCULATE(COUNTROWS('public fact_account_event'), 'public fact_account_event'[churn] = 1)
    ) * 100
```

### Interprétation
Un taux élevé de churn volontaire (par ex. > 70 %) indique que la majorité des pertes est liée à l'insatisfaction ou à la concurrence, et donc potentiellement évitable par des actions commerciales ciblées.

---

## 19. Churn par Raison, Région et Trimestre

### Importance et signification
Ces déclinaisons complémentaires du taux de churn permettent une analyse fine des causes (motif de clôture), de la répartition géographique (agence/région) et de la saisonnalité trimestrielle, utile pour le pilotage opérationnel des agences.

### Mode de calcul
Même logique de calcul que le taux de churn global, simplement recontextualisée par le filtre implicite de la colonne analysée (raison de clôture, région, trimestre) via `SUMMARIZECOLUMNS`.

### Formule DAX
```dax
MEASURE 'public fact_account_event'[Churn par Raison] =
    DIVIDE(
        CALCULATE(COUNTROWS('public fact_account_event'), 'public fact_account_event'[churn] = 1),
        COUNTROWS('public fact_account_event')
    ) * 100

MEASURE 'public fact_account_event'[Churn par Region] =
    DIVIDE(
        CALCULATE(COUNTROWS('public fact_account_event'), 'public fact_account_event'[churn] = 1),
        COUNTROWS('public fact_account_event')
    ) * 100

MEASURE 'public fact_account_event'[Churn par Trimestre] =
    CALCULATE(
        COUNTROWS('public fact_account_event'),
        'public fact_account_event'[churn] = 1
    )
```

### Interprétation
Ces mesures gagnent en pertinence lorsqu'elles sont insérées dans des visuels (tableaux/graphiques) filtrés par la dimension correspondante (raison, région, trimestre) : le contexte de filtre du visuel Power BI fait alors le travail de segmentation, la mesure restant générique.

---

## Synthèse des Familles de KPI

| Famille | KPI concernés | Objectif métier |
|---|---|---|
| **Vue d'ensemble** | Taux de Churn Global, Taux de Rétention | Piloter la santé globale du portefeuille |
| **Profil client** | Ancienneté, Âge, Statut civil, Salaire | Comprendre qui part |
| **Valeur financière** | Solde moyen, Ratio solde/salaire, VaR Churn | Mesurer l'impact financier du churn |
| **Produits & Segments** | Churn par segment, par produit, par profondeur | Identifier où agir en priorité |
| **Conformité & Qualité** | Churn par KYC, Complétude du dossier | Vérifier l'impact des process internes |
| **Temporalité** | Tendance annuelle, YoY, Time-to-Churn, Trimestre | Suivre la dynamique et le bon moment d'action |
| **Prédictif** | Churn Risk Index, Nb Clients Risque Élevé | Anticiper et cibler proactivement |
| **Nature du churn** | Churn Volontaire %, Raison, Région | Distinguer le churn pilotable du churn subi |

---

*Document généré à partir du modèle DAX du tableau de bord Churn Analytics — Banque ESPRIT.*
