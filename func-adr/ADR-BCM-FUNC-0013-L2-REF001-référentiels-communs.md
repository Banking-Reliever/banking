---
id: ADR-BCM-FUNC-0013
title: "L2 Breakdown de CAP.REF.001 — Référentiels Communs"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - REFERENTIEL

impacted_capabilities:
  - CAP.REF.001
  - CAP.REF.001.BEN
  - CAP.REF.001.PRE
  - CAP.REF.001.PAL

impacted_events:
  - Bénéficiaire.RéférentielMisÀJour
  - Prescripteur.RéférentielMisÀJour
  - Palier.DéfinitionMisÀJour

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
  - ADR-BCM-URBA-0012
  - ADR-BCM-FUNC-0004

supersedes: []

tags:
  - BCM
  - L2
  - REFERENTIEL
  - master-data
  - bénéficiaire
  - prescripteur
  - palier

stability_impact: Structural
---

# ADR-BCM-FUNC-0013 — L2 Breakdown de CAP.REF.001 — Référentiels Communs

## Contexte

CAP.REF.001 porte les données de référence partagées par toutes les capacités de Reliever. Per ADR-BCM-URBA-0001, les référentiels master sont isolés dans la zone REFERENTIEL pour éviter la duplication et garantir une gouvernance claire de la master data.

Trois concepts métier canoniques (ADR-BCM-URBA-0012) structurent l'ensemble du dispositif : le Bénéficiaire (l'individu en remédiation), le Prescripteur (l'acteur prescrivant le dispositif), et le Palier (le niveau d'autonomie avec ses règles). Ces trois concepts sont consommés par toutes les zones — ils doivent avoir une définition canonique unique.

## Décision

CAP.REF.001 est décomposé en **3 capacités L2** :

| ID | Nom | Responsabilité |
|----|-----|----------------|
| CAP.REF.001.BEN | Référentiel Bénéficiaire | Porter et maintenir l'identité canonique du bénéficiaire, partagée par toutes les capacités |
| CAP.REF.001.PRE | Référentiel Prescripteur | Porter et maintenir l'identité canonique des prescripteurs et de leurs organisations |
| CAP.REF.001.PAL | Référentiel Paliers | Porter et maintenir les définitions canoniques des paliers, leurs règles et leurs seuils de transition |

### Événements métier par L2

| L2 | Événements produits | Consommateurs principaux |
|----|---------------------|--------------------------|
| CAP.REF.001.BEN | `Bénéficiaire.RéférentielMisÀJour` | BSP.002, BSP.003, BSP.004, CAN.001, CAN.002, B2B.001 |
| CAP.REF.001.PRE | `Prescripteur.RéférentielMisÀJour` | BSP.003, CAN.002 |
| CAP.REF.001.PAL | `Palier.DéfinitionMisÀJour` | BSP.001.PAL, BSP.004.AUT, B2B.001.CRT |

### Règle de golden record

CAP.REF.001.BEN est la source de vérité unique pour l'identité d'un bénéficiaire. Aucune autre capacité ne peut maintenir sa propre copie de l'identité bénéficiaire — elle doit souscrire à `Bénéficiaire.RéférentielMisÀJour`.

CAP.REF.001.PAL est la source de vérité unique pour les définitions de palier. Toute modification des règles d'un palier passe par ce L2 et déclenche `Palier.DéfinitionMisÀJour`, consommé par toutes les capacités applicant des règles de palier.

### Critères vérifiables

- Chaque L2 produit au moins un événement métier (ADR-BCM-URBA-0009)
- Aucune capacité hors CAP.REF.001.BEN ne maintient une identité bénéficiaire authoritative
- Toute modification de définition de palier passe par CAP.REF.001.PAL

## Justification

La séparation BEN / PRE / PAL reflète trois domaines de master data distincts avec des cycles de vie, des sources et des gouvernances différents. L'identité bénéficiaire est créée à l'enrôlement et archivée à la sortie. L'identité prescripteur est gérée par les organisations prescriptrices. Les définitions de palier sont gouvernées par le programme lui-même.

### Alternatives considérées

- **PAL dans BSP.001.PAL** — rejeté car les définitions de palier sont consommées par plusieurs capacités (BSP.001, BSP.004, B2B.001) ; leur ownership dans un seul L2 COEUR créerait une dépendance transverse non gouvernée vers une capacité qui devrait être autonome
- **BEN + PRE fusionnés** — rejeté car les bénéficiaires et les prescripteurs ont des cycles de vie et des sources de vérité différents ; leur identité ne provient pas des mêmes systèmes sources

## Impacts sur la BCM

### Structure

- 3 L2 créés sous CAP.REF.001
- Capacité consommée par la quasi-totalité des autres L2 du dispositif

### Mapping SI / Data / Org

- **DATA** : CAP.REF.001 est le MDM (Master Data Management) de Reliever
- **ORG** : owner recommandé : équipe "Data & Référentiels"

## Conséquences

### Positives

- Source de vérité unique pour les trois concepts canoniques du dispositif
- Évolution des définitions de palier sans impact sur l'identité des acteurs

### Négatives / Risques

- CAP.REF.001.PAL est critique opérationnellement : une modification de définition de palier impacte en cascade BSP.001, BSP.004, B2B.001

### Dette acceptée

- La stratégie de synchronisation entre REF.001.BEN et les sources d'identité externes (banques, hôpitaux, services sociaux) n'est pas modélisée ici

## Indicateurs de gouvernance

- Niveau de criticité : Élevé (infrastructure de données du dispositif)
- Date de revue recommandée : 2028-04-24
- Indicateur de stabilité attendu : 0 doublon d'identité bénéficiaire entre capacités

## Traçabilité

- Atelier : Session BCM Reliever — 2026-04-24
- Participants : yremy
- Références :
  - ADR-BCM-URBA-0012 — Concept métier canonique
  - ADR-BCM-FUNC-0004
