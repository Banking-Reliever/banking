---
id: ADR-BCM-FUNC-0015
title: "L2 Breakdown de CAP.PIL.001 — Pilotage du Programme"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - PILOTAGE

impacted_capabilities:
  - CAP.PIL.001
  - CAP.PIL.001.GOV
  - CAP.PIL.001.KPI
  - CAP.PIL.001.AUD

impacted_events:
  - PolitiqueGouvernance.MisÀJour
  - PerformanceProgramme.Évaluée
  - ConformitéProgramme.Vérifiée

impacted_mappings:
  - SI
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010
  - ADR-BCM-FUNC-0004
  - ADR-BCM-FUNC-0014

supersedes: []

tags:
  - BCM
  - L2
  - PILOTAGE
  - gouvernance
  - KPI
  - conformité-programme

stability_impact: Moderate
---

# ADR-BCM-FUNC-0015 — L2 Breakdown de CAP.PIL.001 — Pilotage du Programme

## Contexte

CAP.PIL.001 pilote le programme de remédiation Reliever à l'échelle — au-delà du suivi individuel d'un bénéficiaire. Elle répond à la question : "Le programme est-il efficace ? Est-il conforme ? Doit-on faire évoluer les règles ?"

Per ADR-BCM-URBA-0001, la zone PILOTAGE porte les capacités de pilotage d'entreprise, conformité et gouvernance. CAP.PIL.001 est distinct de CAP.SUP.001 (conformité IS transverse) : PIL.001 pilote la conformité réglementaire du programme dans son ensemble ; SUP.001 garantit la conformité des données au niveau technique.

## Décision

CAP.PIL.001 est décomposé en **3 capacités L2** :

| ID | Nom | Responsabilité |
|----|-----|----------------|
| CAP.PIL.001.GOV | Gouvernance du Programme | Définir et faire évoluer les politiques de gouvernance du programme — règles d'éligibilité, seuils de palier, protocoles de co-décision |
| CAP.PIL.001.KPI | Suivi de Performance | Mesurer l'efficacité du dispositif à l'échelle — taux de progression, taux de rechute, taux de sortie, dignité perçue |
| CAP.PIL.001.AUD | Audit Conformité Programme | Vérifier la conformité réglementaire du programme dans son ensemble (respect des cadres bancaire, médical et social) |

### Événements métier par L2

| L2 | Événements produits | Événements consommés |
|----|---------------------|----------------------|
| CAP.PIL.001.GOV | `PolitiqueGouvernance.MisÀJour` | `ModèleScore.MisÀJour` (DAT.001.MOD) — pour valider les évolutions de modèle avant déploiement |
| CAP.PIL.001.KPI | `PerformanceProgramme.Évaluée` | `RapportProgramme.Généré` (DAT.001.REP) |
| CAP.PIL.001.AUD | `ConformitéProgramme.Vérifiée` | `AccèsDonnées.Journalisé` (SUP.001.AUD), `ConformitéProgramme.Vérifiée` — cycle d'audit périodique |

### Règle de validation des évolutions de modèle

Toute mise à jour du modèle de score (DAT.001.MOD → `ModèleScore.MisÀJour`) doit être validée par CAP.PIL.001.GOV avant déploiement en production. Cette validation produit `PolitiqueGouvernance.MisÀJour`, qui autorise BSP.001 à adopter le nouveau modèle. Cette règle prévient la dérive algorithmique non gouvernée.

### Critères vérifiables

- Chaque L2 produit au moins un événement métier (ADR-BCM-URBA-0009)
- Aucun déploiement de modèle de score sans `PolitiqueGouvernance.MisÀJour` préalable

## Justification

La séparation GOV / KPI / AUD reflète trois niveaux de pilotage distincts : la gouvernance est normative (définit les règles), les KPIs sont descriptifs (mesure les résultats), l'audit est probatoire (certifie la conformité). Ces trois activités ont des acteurs, des fréquences et des destinataires différents.

### Alternatives considérées

- **KPI dans CAP.DAT.001.REP** — rejeté car la mesure de performance programme est une décision de pilotage (quels indicateurs, quels seuils, quelle interprétation) ; la production des données sous-jacentes est DATA_ANALYTIQUE, mais la décision d'évaluation est PILOTAGE
- **AUD dans CAP.SUP.001** — rejeté car SUP.001 audite les accès données au niveau technique (RGPD) ; PIL.001.AUD audite la conformité réglementaire du programme dans son ensemble (cadres bancaire, médical, social) — ce sont deux niveaux d'audit distincts avec des acteurs différents (DPO vs Compliance Officer programme)

## Impacts sur la BCM

### Structure

- 3 L2 créés sous CAP.PIL.001
- Rôle de validation sur l'évolution du modèle de score (chaîne DAT.001 → PIL.001.GOV → BSP.001)

### Mapping SI / Data / Org

- **ORG** : owner recommandé : Direction Programme Reliever / Compliance Officer

## Conséquences

### Positives

- La gouvernance algorithmique est de première classe — aucune dérive de modèle sans validation
- L'audit réglementaire est distinct de l'audit technique

### Négatives / Risques

- PIL.001.GOV crée une dépendance humaine dans la chaîne de déploiement du modèle — latence possible

### Dette acceptée

- Les KPIs précis du programme (taux de progression acceptable, définition de "succès") ne sont pas modélisés ici

## Indicateurs de gouvernance

- Niveau de criticité : Modéré
- Date de revue recommandée : 2028-04-24
- Indicateur de stabilité attendu : 100% des évolutions de modèle validées par PIL.001.GOV avant déploiement

## Traçabilité

- Atelier : Session BCM Reliever — 2026-04-24
- Participants : yremy
- Références :
  - ADR-BCM-FUNC-0004, ADR-BCM-FUNC-0014
