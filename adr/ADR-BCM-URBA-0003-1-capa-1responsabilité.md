---
id: ADR-BCM-URBA-0003
title: "Une capacité = une responsabilité, pas une application"
status: Superseded
date: 2026-02-26
superseded_by: ADR-BCM-URBA-0009
superseded_date: 2026-03-10

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

related_adr:
  - ADR-BCM-GOV-0001  # hiérarchie GOV → URBA → FUNC
supersedes: []

tags:
  - BCM
  - Urbanisation
  - Ownership

stability_impact: Structural
---

# ADR-BCM-URBA-0003 — Une capacité = une responsabilité, pas une application

## Contexte
Lors des cartographies et de la rationalisation, une dérive fréquente est d’assimiler une capacité à une application (ex : « CRM = Relation Client »).
Cela crée :
- des recouvrements (plusieurs applications couvrent une même capacité),
- des débats stériles “outil vs métier”,
- une incapacité à comparer objectivement des options (build/buy, produit vs plateforme, trajectoire).

## Décision
- Une capacité décrit une responsabilité métier stable (le “quoi”), indépendante de la solution.
- Les applications, produits SI et composants techniques sont **mappés** sur les capabilities, mais ne les définissent pas.
- Les libellés de capabilities ne contiennent **aucune** référence à un éditeur, un outil, ou une techno.



## Justification

Cette séparation permet :
- d'éviter les biais technologiques,
- de maintenir un langage commun métier/DSI,
- de piloter une trajectoire (avant/après) sans renommer le métier,
- de mesurer la couverture SI et d'identifier les doublons.

### Alternatives considérées

- Capability = Application — rejeté car trop dépendant du paysage SI, bloque la transformation.
- Capability = Processus — rejeté car dérive en cartographie opérationnelle exhaustive.

## Impacts sur la BCM

### Structure

- Capacités impactées : toutes (règle de nommage et de périmètre).

### Événements (si applicable)

- Aucun impact direct.

### Mapping SI / Data / Org

- Maintenir une vue séparée « Capability → Applications/Produits » (et non dans la BCM).

## Conséquences
### Positives
- Rationalisation applicative plus objective (couverture, redondances, “gaps”).
- Lisibilité renforcée pour les arbitrages (build/buy, convergence, mutualisation).

### Négatives / Risques

- Discipline de gouvernance nécessaire (revues de libellés, contrôle qualité).

### Dette acceptée

- Les libellés existants hérités du legacy peuvent persister temporairement.

## Indicateurs de gouvernance

- Niveau de criticité : Élevé (règle transverse).
- Date de revue recommandée : 2028-01-21.
- Indicateur de stabilité attendu : 0 capacité portant un nom d'éditeur ou de produit.

## Traçabilité

- Atelier : Revue Architecture — application de la règle sur les cartographies capability→SI
- Participants : EA / Urbanisation, Business Architecture
- Références : —
