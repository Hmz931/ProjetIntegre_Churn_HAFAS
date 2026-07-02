"""
Aide à la décodification des codes du fichier principal via les tables de dimensions.

⚠️ Règle de confidentialité stricte : les fichiers dim_*.xlsx fournis par l'encadrant
contiennent encore le nom réel de la banque source (sous la forme "ATB") dans certains
libellés texte (ex. dim_Closure_reason.xlsx). Le fichier principal anonymisé a déjà
remplacé ce nom par "BANK" partout (cf. data/anonymize.py). Ce module retire
systématiquement toute occurrence du nom réel avant de exposer un libellé, afin que
la confidentialité exigée par la documentation (`2_description_donnees.md`, section 8)
soit respectée même quand on enrichit les données avec les dimensions d'origine.
"""
from __future__ import annotations

import re

import pandas as pd

# Nom réel de l'institution, tel qu'il apparaît encore dans les fichiers dim_*.xlsx
# fournis par l'encadrant. Centralisé ici pour qu'un seul endroit du code connaisse
# cette valeur, et que le remplacement soit appliqué de façon cohérente partout.
_REAL_BANK_NAME_PATTERN = re.compile(r"\bATB\b", flags=re.IGNORECASE)


def _scrub_bank_name(text: str) -> str:
    """Remplace toute occurrence du nom réel de la banque par 'BANK', comme le fait
    déjà data/anonymize.py sur le fichier principal — pour ne jamais réintroduire
    l'information par les dimensions alors que le fichier principal l'a retirée.
    """
    if not isinstance(text, str):
        return text
    return _REAL_BANK_NAME_PATTERN.sub("BANK", text)


def build_closure_reason_lookup(dim_closure_reason: pd.DataFrame) -> pd.DataFrame:
    """Construit une table de correspondance code anonymisé -> libellé métier propre,
    à partir de dim_Closure_reason.xlsx.

    Le fichier principal anonymisé encode les motifs de clôture comme `BANK.REASON.N`
    (où N est un numéro). dim_Closure_reason.xlsx liste les motifs sous la forme
    `CLOSURE.REASON*ATB.REASON.N` avec une description en clair. On extrait le numéro
    commun aux deux pour faire la jointure, sans jamais exposer le préfixe `ATB`.

    Quelques codes de dim_Closure_reason.xlsx ne suivent pas ce schéma numéroté
    (ex. `CLOSURE.REASON*CUSTOMER.REQUEST`, `CLOSURE.REASON*DECEASED.CUSTOMER`) — ils
    sont conservés tels quels, scrubbés, sans tentative de les faire correspondre à un
    numéro qu'ils n'ont pas.
    """
    lookup = dim_closure_reason.copy()
    lookup["DESCRIPTION"] = lookup["DESCRIPTION"].apply(_scrub_bank_name)

    # Extrait le numéro depuis "...REASON.N" quand il existe.
    lookup["reason_number"] = lookup["RECID"].str.extract(r"REASON\.(\d+)$")

    # Reconstruit la clé anonymisée attendue dans le fichier principal : BANK.REASON.N
    lookup["closure_code_anonymized"] = lookup["reason_number"].apply(
        lambda n: f"BANK.REASON.{n}" if pd.notna(n) else None
    )

    return lookup[["RECID", "reason_number", "closure_code_anonymized", "DESCRIPTION"]]


def classify_closure_voluntary(description: str) -> bool | None:
    """Classifie un motif de clôture comme volontaire (départ choisi par le client) ou
    non (décès, faillite, contentieux, transfert administratif), à partir du libellé
    en clair désormais disponible grâce à dim_Closure_reason.xlsx.

    Cette classification reste une heuristique métier simple basée sur des mots-clés du
    libellé français — pas une vérité absolue. Elle remplace le placeholder non
    documenté utilisé tant que le libellé réel n'était pas disponible (cf. version
    précédente de DIM_CLOSURE), mais reste à valider avec l'équipe / l'encadrant si une
    classification plus fine est nécessaire pour le rapport final.
    """
    if not isinstance(description, str):
        return None

    text = description.lower()

    involuntary_markers = [
        "décéd", "decéd", "deced", "décdé", "decde", "passed away",  # décès (inclut variante avec faute de frappe source)
        "faillite",  # faillite
        "contentieux",  # litige
        "gelé", "gele",  # compte gelé (décision de la banque, pas du client)
        "transferred", "transferre",  # transfert administratif
        "undesirable",  # client jugé indésirable par la banque
        "délictueux", "delictueux",  # fraude / usage frauduleux
        "refus de crédit", "refus de credit", "refus d octroi", "refus d'octroi",  # credit refuse par la banque
    ]
    if any(marker in text for marker in involuntary_markers):
        return False

    voluntary_markers = [
        "tarification", "chère", "chere",  # prix trop élevé
        "délais", "delais", "non respect",  # délais non respectés
        "personnel non interactif", "interactivite",  # qualité de service perçue
        "réclamation", "reclamation",  # réclamation non traitée
        "recherche", "convention avec une autre banque",  # parti chez un concurrent
        "cessation", "changement d employeur", "changement d'employeur",
        "non satisfied", "dissatisfied",
        "customer request", "requested",
    ]
    if any(marker in text for marker in voluntary_markers):
        return True

    return None  # motif ambigu ou non classifiable avec cette heuristique simple
