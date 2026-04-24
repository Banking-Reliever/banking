---
id: ADR-BCM-GOV-0003
title: "Revue de stabilité périodique de la BCM"
status: Proposed
date: 2026-03-05

family: GOV

decision_scope:
  level: Cross-Level
  zoning: []

impacted_capabilities: []
impacted_events: []
impacted_mappings:
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-GOV-0002
  - ADR-BCM-URBA-0004
supersedes: []

tags:
  - gouvernance
  - stabilite
  - revue-periodique

stability_impact: Structural
---

# ADR-BCM-GOV-0003 — Revue de stabilité périodique de la BCM

## Contexte

Le référentiel BCM évolue rapidement (capabilities, événements, ADR, mappings).
Sans rituel de revue périodique, le risque est d'accumuler des décisions obsolètes,
des incohérences transverses et une dette de gouvernance difficile à résorber.

Le besoin est d'installer un mécanisme simple, répétable et auditable de revue
de stabilité pour sécuriser la cohérence du modèle dans la durée.

## Décision

Le Collège BCM met en place une **revue de stabilité périodique** avec les règles suivantes :

- **Rythme standard** : une revue trimestrielle.
- **Déclencheurs exceptionnels** : revue anticipée en cas de changement structurant
	(nouvelle zone, refonte L1/L2, évolution majeure du méta-modèle).
- **Périmètre minimum** : ADR GOV/URBA/FUNC, cohérence capacités/événements,
	conformité des validations automatiques et dette de documentation.
- **Sortie obligatoire** : un compte-rendu formel incluant décisions, écarts,
	actions, responsables et échéances.

Critères vérifiables :

- au moins une revue réalisée par trimestre ;
- existence d'un compte-rendu daté et tracé ;
- taux de traitement des actions ouvertes suivi à la revue suivante.

## Justification

Cette décision réduit le risque de dérive progressive du modèle et améliore
la capacité d'arbitrage du Collège BCM sur des faits objectivables.

### Alternatives considérées

- **Revue ad hoc uniquement** — rejetée : trop dépendante des urgences projet.
- **Revue mensuelle** — rejetée : charge trop élevée au regard du niveau de maturité actuel.

## Impacts sur la BCM

### Structure

- Aucun changement direct de structure L1/L2/L3.
- Amélioration de la qualité et de la stabilité des décisions d'évolution.

### Événements (si applicable)

- Vérification périodique de la cohérence des liens événements/objets/ressources/abonnements.

### Mapping SI / Data / Org

- ORG : formalisation du rituel de pilotage et des responsabilités de suivi.

## Conséquences

### Positives

- Gouvernance plus prévisible et traçable.
- Détection plus précoce des incohérences.
- Réduction de la dette documentaire dans le temps.

### Négatives / Risques

- Charge de coordination supplémentaire pour les parties prenantes.
- Risque de revue formelle sans décisions actionnables si le cadrage est insuffisant.

### Dette acceptée

- Le format détaillé de compte-rendu et les indicateurs cibles seront affinés
	dans une itération ultérieure, après deux cycles de revue.

## Indicateurs de gouvernance

- Niveau de criticité : élevé.
- Date de revue recommandée : 2026-06-30.
- Indicateur de stabilité attendu : amélioration continue trimestrielle.

## Traçabilité

- Atelier : Gouvernance BCM — cadrage du rituel de stabilité.
- Participants : Collège BCM (Architecture, Urbanisme, BA Lead).
- Références : ADR-BCM-GOV-0001, ADR-BCM-GOV-0002, ADR-BCM-URBA-0004.
