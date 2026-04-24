---
id: ADR-BCM-FUNC-0014
title: "L2 Breakdown de CAP.DAT.001 — Analytique Comportementale"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - DATA_ANALYTIQUE

impacted_capabilities:
  - CAP.DAT.001
  - CAP.DAT.001.ING
  - CAP.DAT.001.MOD
  - CAP.DAT.001.REP

impacted_events:
  - DonnéesComportementales.Ingérées
  - ModèleScore.MisÀJour
  - RapportProgramme.Généré

impacted_mappings:
  - SI
  - DATA
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010
  - ADR-BCM-FUNC-0004
  - ADR-BCM-FUNC-0005

supersedes: []

tags:
  - BCM
  - L2
  - DATA_ANALYTIQUE
  - scoring
  - analytique
  - BI

stability_impact: Moderate
---

# ADR-BCM-FUNC-0014 — L2 Breakdown de CAP.DAT.001 — Analytique Comportementale

## Contexte

CAP.DAT.001 est la capacité d'amélioration continue du dispositif Reliever. Elle se distingue de CAP.BSP.001 (Remédiation Comportementale) sur un point clé : BSP.001 calcule le score opérationnel en temps réel pour chaque transaction ; DAT.001 analyse les patterns comportementaux agrégés pour améliorer le modèle de score dans le temps.

Per ADR-BCM-URBA-0001, les flux analytiques (décorrélés, batch/stream) sont DATA_ANALYTIQUE ; les flux transactionnels opérationnels sont SERVICES_COEUR. Cette séparation est fondamentale pour éviter de coupler le moteur de décision temps réel avec les processus d'apprentissage et de reporting.

## Décision

CAP.DAT.001 est décomposé en **3 capacités L2** :

| ID | Nom | Responsabilité |
|----|-----|----------------|
| CAP.DAT.001.ING | Ingestion des Événements | Collecter et consolider les événements comportementaux produits par l'ensemble du dispositif pour alimenter les pipelines analytiques |
| CAP.DAT.001.MOD | Modèle Analytique du Score | Analyser les patterns comportementaux agrégés, améliorer le modèle de score et proposer des évolutions des seuils de palier |
| CAP.DAT.001.REP | Reporting Programme | Produire les tableaux de bord et rapports de suivi de l'efficacité globale du programme de remédiation |

### Événements métier par L2

| L2 | Événements produits | Événements consommés |
|----|---------------------|----------------------|
| CAP.DAT.001.ING | `DonnéesComportementales.Ingérées` | Tous les événements métier du dispositif (BSP.001, BSP.002, BSP.003, BSP.004) en mode analytique décorrélé |
| CAP.DAT.001.MOD | `ModèleScore.MisÀJour` | `DonnéesComportementales.Ingérées` (DAT.001.ING) |
| CAP.DAT.001.REP | `RapportProgramme.Généré` | `DonnéesComportementales.Ingérées` (DAT.001.ING), `ModèleScore.MisÀJour` (DAT.001.MOD) |

### Règle de séparation analytique/opérationnel

`ModèleScore.MisÀJour` produit par DAT.001.MOD est consommé par CAP.PIL.001 (décision de gouvernance programme) mais **pas directement par BSP.001.SCO**. Le modèle opérationnel de scoring est mis à jour de façon contrôlée, après validation — jamais en flux direct depuis l'analytique. Cette règle prévient la rétroaction incontrôlée entre analytique et opérationnel.

### Critères vérifiables

- Chaque L2 produit au moins un événement métier (ADR-BCM-URBA-0009)
- DAT.001 ne produit pas d'événements consommés en temps réel par BSP.004.AUT (séparation analytique/transactionnel)

## Justification

La séparation ING / MOD / REP reflète trois étapes du pipeline analytique avec des rhythmes et des responsabilités distincts. L'ingestion est continue (near real-time). L'amélioration du modèle est périodique (mensuelle, trimestrielle). Le reporting est à la demande ou planifié.

### Alternatives considérées

- **MOD dans BSP.001.SCO** — rejeté car l'amélioration du modèle est un processus analytique offline avec validation humaine ; le scoring opérationnel est temps réel sans intervention humaine ; les confondre créerait un risque de dérive incontrôlée du modèle
- **REP dans CAP.PIL.001** — rejeté car la production des données de reporting est DATA_ANALYTIQUE (ingestion, transformation, agrégation) ; la consommation de ces données pour les décisions de gouvernance est PILOTAGE

## Impacts sur la BCM

### Structure

- 3 L2 créés sous CAP.DAT.001
- Consomme les événements de tout le dispositif en mode décorrélé

### Mapping SI / Data / Org

- **DATA** : pipeline analytique séparé du pipeline transactionnel
- **ORG** : owner recommandé : équipe "Data Science & BI"

## Conséquences

### Positives

- Amélioration continue du modèle de score sans risque de rétroaction sur l'opérationnel
- Reporting programme disponible pour les décisions de gouvernance

### Négatives / Risques

- La frontière entre le modèle opérationnel (BSP.001.SCO) et le modèle analytique (DAT.001.MOD) nécessite une procédure de mise en production contrôlée

### Dette acceptée

- Le pipeline d'ingestion et les technologies analytiques ne sont pas modélisés ici

## Indicateurs de gouvernance

- Niveau de criticité : Modéré
- Date de revue recommandée : 2028-04-24
- Indicateur de stabilité attendu : modèle de score versionné avec historique des évolutions documenté

## Traçabilité

- Atelier : Session BCM Reliever — 2026-04-24
- Participants : yremy
- Références :
  - ADR-BCM-URBA-0001 — Séparation DATA_ANALYTIQUE / SERVICES_COEUR
  - ADR-BCM-FUNC-0004, ADR-BCM-FUNC-0005
