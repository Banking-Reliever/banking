---
id: ADR-BCM-GOV-0002
title: "Mécanisme d’arbitrage et collège de gouvernance BCM"
status: Proposed
date: 2026-02-26

family: GOV

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
  - DATA
  - ORG

related_adr: 
  - ADR-BCM-GOV-0001

supersedes: []

tags:
  - gouvernance
  - collège
  - arbitrage 

stability_impact: Structural
---

# ADR-BCM-GOV-0002 — Collège d’arbitrage BCM

## Contexte

La BCM évolue au fil des projets et des transformations.

Afin d’assurer :
- La cohérence globale du modèle,
- La prise en compte des retours terrain,
- L’équilibre entre urbanisation et réalité opérationnelle,

un mécanisme d’arbitrage formalisé est nécessaire.

## Décision

Un **Collège BCM** est institué.

### Composition

Le collège est composé de :

- Architectes SI
- Lead Business Analysts
- Un(e) urbaniste garant(e) de la cohérence globale

La composition vise un équilibre entre :
- Vision technique
- Vision métier
- Vision systémique

### Rôle du Collège

Le collège est responsable :

- De l’instruction des ADR de gouvernance
- De l’instruction des ADR d'urbanisme
- De la validation des ADR fonctionnel
- De la cohérence transversale du modèle BCM
- De l’arbitrage en cas de désaccord entre équipes

### Processus de remontée

Les évolutions du modèle sont alimentées par :

- Retours terrain des équipes projet
- Event Storming Big Picture
- Problématiques d’intégration
- Difficultés récurrentes observées

Les équipes projet peuvent :

- Proposer des évolutions via un ADR Proposed
- Soumettre des problématiques formalisées

### Mode de décision

- Recherche du consensus prioritaire.
- En cas de désaccord persistant, décision prise à la majorité qualifiée du collège.
- L’urbaniste dispose d’un rôle de garant de cohérence, non de veto absolu.

### Transparence

- Les ADR Proposed sont visibles.
- Les décisions sont motivées et documentées.
- Les refus sont explicitement justifiés.

### Clause d’équilibre

Le collège BCM ne constitue pas une instance de contrôle des projets.

Il intervient uniquement sur les évolutions du modèle BCM.

La finalité reste la création de valeur métier et la fluidité des projets.

## Justification

Ce mécanisme permet :

- D’éviter une architecture descendante isolée.
- D’intégrer les retours opérationnels.
- De structurer les arbitrages.
- De préserver la cohérence globale.

Il formalise un équilibre entre stabilité et adaptabilité.

### Alternatives considérées

- Validation ad hoc sans instance dédiée — rejetée car peu traçable et non reproductible.
- Gouvernance exclusivement descendante — rejetée car elle limite les retours terrain.

## Impacts sur la BCM

### Structure

- Mise en place d’un mécanisme formel d’arbitrage pour les évolutions de la BCM.
- Clarification des rôles entre instruction, validation et arbitrage.

### Événements (si applicable)

- Aucun impact direct sur les événements métier.

### Mapping SI / Data / Org

- Applications impactées : gouvernance transverse (SI).
- Flux impactés : processus de remontée et d’arbitrage (DATA/ORG).

## Conséquences

### Positives

- Gouvernance claire.
- Canal structuré pour les retours terrain.
- Réduction des conflits implicites.
- Amélioration continue du modèle.

### Négatives / Risques

- Complexité organisationnelle.
- Risque de lourdeur décisionnelle.
- Risque de capture par un groupe dominant si non surveillé.

### Dette acceptée

- Coût d’animation d’une instance de gouvernance transverse.
- Besoin d’acculturation continue des équipes au processus ADR.

## Indicateurs de gouvernance

- Niveau de criticité : Élevé (gouvernance transverse).
- Date de revue recommandée : 2028-02-26.
- Indicateur de stabilité attendu :
  - Délai moyen d’arbitrage maîtrisé.
  - Décisions d’arbitrage systématiquement tracées dans les ADR.

## Traçabilité

- Atelier : Gouvernance BCM – 2026-02-26
- Participants : EA / Business Architecture
- Références : ADR-BCM-GOV-0001