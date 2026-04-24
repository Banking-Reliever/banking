---
id: ADR-BCM-URBA-0002
title: "BCM structurée en 3 niveaux (L1/L2/L3)"
status: Proposed
date: 2026-02-26

family: URBA

decision_scope:
  level: Cross-Level
  zoning:
    - PILOTAGE
    - SERVICES_COEUR
    - SUPPORT
    - REFERENTIEL
    - ECHANGE_B2B
    - CANAL
    - DATA_ANALYTIQUE

impacted_capabilities: []
impacted_events: []
impacted_mappings:
    - SI
    - ORG

related_adr:
  - ADR-BCM-GOV-0001  # hiérarchie GOV → URBA → FUNC
supersedes: []

tags:
  - BCM
  - Modélisation
  - Niveaux

stability_impact: Structural
---

# ADR-BCM-URBA-0002 — BCM structurée en 3 niveaux (L1/L2/L3)

## Contexte
La BCM doit servir :
- de langage commun métier/DSI,
- de support à l’urbanisation (alignement applications / data / investissements),
- sans devenir une process map.

Un modèle 2 niveaux manque de granularité pour certains arbitrages (allocation SI, rationalisation, ownership).

## Décision
- La BCM est structurée en 3 niveaux : L1, L2, L3.
- Les vues standards exposées sont L1/L2.
- Le niveau L3 est produit uniquement pour les domaines critiques (High criticality) ou sous transformation.

## Justification

Le 3 niveaux donne l'actionnabilité (L3) sans perdre la lisibilité (L1/L2).

### Alternatives considérées

- 2 niveaux — rejeté car trop macro pour l'urbanisation.
- 4+ niveaux — rejeté car risque de dérive en cartographie de processus.

## Impacts sur la BCM

### Structure

- Capacités impactées : toutes (règle de construction).
- Vues : générer une vue L1/L2 par défaut.

### Événements (si applicable)

- Aucun impact direct.

### Mapping SI / Data / Org

- Aucun impact direct.

## Conséquences
### Positives
- Meilleur pilotage de la couverture SI et des investissements.

### Négatives / Risques

- Risque de granularité incohérente si L3 non gouverné.

### Dette acceptée

- Cadrage plus précis du L3 reporté (voir ADR-BCM-URBA-0004).

## Indicateurs de gouvernance

- Niveau de criticité : Élevé (décision structurante).
- Date de revue recommandée : 2028-01-21.
- Indicateur de stabilité attendu : 100 % des capabilities ont un niveau L1/L2 attribué.

## Traçabilité

- Atelier : Urbanisation 2026-01-15
- Participants : EA / Urbanisation, Business Architecture
- Références : —
