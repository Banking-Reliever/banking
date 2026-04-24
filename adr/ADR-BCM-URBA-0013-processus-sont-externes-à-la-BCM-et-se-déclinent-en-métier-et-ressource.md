---
id: ADR-BCM-URBA-0013
title: "Les processus restent externes à la BCM et se déclinent en processus métier et processus ressource"
status: Proposed
date: 2026-03-23

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
  - DATA
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0007
  - ADR-BCM-URBA-0008
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010

supersedes: []

tags:
  - BCM
  - processus
  - orthogonalite
  - objet-metier
  - evenement-metier
  - ressource
  - abstraction
  - orchestration

stability_impact: Structural
---

# ADR-BCM-URBA-0013 — Les processus restent externes à la BCM et se déclinent en processus métier et processus ressource

## Contexte

La BCM décrit un modèle structurel de capacités, d'objets, d'événements, de ressources et de relations.

Le référentiel introduit déjà deux niveaux d'abstraction :
- un niveau **métier** fondé sur les objets métier, événements métier et abonnements métier ;
- un niveau **ressource** fondé sur les ressources, événements ressource et abonnements ressource.

En parallèle, les artefacts de processus servent à décrire des enchaînements d'orchestration.
Ils consomment la BCM mais ne doivent pas devenir un axe de découpage de sa structure.

Une clarification est nécessaire pour distinguer explicitement :
- la **structure** du modèle BCM ;
- les **vues processuelles** qui s'appuient sur ce modèle.

## Décision

Les processus **ne font pas partie de la structure de la BCM**.

Ils constituent des **vues externes d'orchestration** s'appuyant sur les éléments du modèle BCM.

Deux familles de processus sont reconnues :

1. **Processus métier**
   - Fondés sur les abstractions de niveau métier :
     `objet métier`, `événement métier`, `abonnement métier`.
   - Ils décrivent des orchestrations métier généralistes, stables et orientées valeur.

2. **Processus ressource**
   - Fondés sur les abstractions de niveau ressource :
     `ressource`, `événement ressource`, `abonnement ressource`.
   - Ils décrivent des orchestrations appliquées, explicites et soumises à des contraintes opérationnelles fortes.

### Règles structurantes

1. La BCM reste structurée par les **capacités** et non par les processus.
2. Les **capacités L2** demeurent le pivot d'urbanisation et le point d'ancrage principal des relations du modèle.
3. Un processus ne crée pas, à lui seul, une capacité, une frontière de capacité ou un niveau L1/L2/L3.
4. Un processus métier ne doit référencer que des éléments de type métier.
5. Un processus ressource ne doit référencer que des éléments de type ressource.
6. Le passage du niveau métier au niveau ressource relève d'une relation d'alignement ou de traçabilité, pas d'une fusion des deux niveaux.
7. Les artefacts de processus restent documentaires et descriptifs ; ils ne remplacent ni les ADR URBA ni les ADR FUNC.

### Critères vérifiables

- Aucun processus n'est utilisé comme critère de découpage principal d'une capacité BCM.
- Tout processus publié est typé soit `processus métier`, soit `processus ressource`.
- Tout processus métier référence exclusivement des objets/événements/abonnements métier.
- Tout processus ressource référence exclusivement des ressources/événements/abonnements ressource.
- Les relations structurantes du modèle restent ancrées sur les capacités, en priorité au niveau L2.

## Justification

Cette décision permet :
- de préserver la stabilité de la BCM comme référentiel structurel ;
- de distinguer clairement l'abstraction métier de la déclinaison opérationnelle ;
- d'éviter qu'un flux processuel conjoncturel déforme les frontières capacitaires ;
- de conserver les processus comme vues de lecture, d'explication et d'orchestration.

Elle rend également compatible :
- une lecture métier généraliste, utile pour la compréhension transverse ;
- une lecture ressource, utile pour l'explicitation des contraintes d'exécution.

### Alternatives considérées

- **Intégrer les processus dans la structure de la BCM** — rejeté : mélange entre vue processuelle et structure du référentiel.
- **Ne conserver qu'un seul type de processus** — rejeté : perte de distinction entre abstraction métier et contraintes opérationnelles.
- **Rattacher directement les processus aux niveaux L1/L2/L3 comme axe de structuration** — rejeté : contradiction avec le rôle pivot des capacités.

## Impacts sur la BCM

### Structure

- Aucun changement du découpage L1/L2/L3.
- Aucune capacité nouvelle n'est créée du seul fait d'un processus.
- Confirmation du rôle structurel des capacités et du rôle externe des processus.

### Événements (si applicable)

- Aucun changement du méta-modèle événementiel.
- Clarification du fait que les événements métier alimentent les processus métier, et les événements ressource les processus ressource.

### Mapping SI / Data / Org

- **SI** : les processus ressource peuvent expliciter les contraintes d'orchestration appliquée sans modifier les frontières capacitaires.
- **DATA** : la distinction métier / ressource améliore la lisibilité des objets manipulés.
- **ORG** : les processus restent des vues d'explication et de coordination, non des unités structurelles de responsabilité.

## Conséquences

### Positives

- Clarification nette entre structure BCM et orchestration.
- Cohérence renforcée avec le méta-modèle à deux niveaux.
- Réduction du risque de dérive process-centric de la BCM.
- Meilleure lisibilité des artefacts de processus.

### Négatives / Risques

- Nécessite une discipline documentaire explicite entre vues structurelles et vues processuelles.
- Peut demander des règles complémentaires de traçabilité entre processus métier et processus ressource.

### Dette acceptée

- Le formalisme détaillé des liens de traçabilité entre processus métier et processus ressource reste à préciser dans un guide ou un template complémentaire.
- Les conventions de nommage et de publication des artefacts de processus pourront être affinées ultérieurement.

## Indicateurs de gouvernance

- Niveau de criticité : Élevé.
- Date de revue recommandée : 2027-03-23.
- Indicateur de stabilité attendu :
  - aucun découpage capacitaire justifié uniquement par un processus ;
  - typage explicite de 100% des processus publiés ;
  - absence de mélange entre abstractions métier et ressource dans un même artefact de processus.

## Traçabilité

- Atelier : cadrage urbanisation BCM — structure vs orchestration.
- Participants : Urbanisme SI, Architecture, Référents métier.
- Références :
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0007
  - ADR-BCM-URBA-0008
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010
  - Template `externals-templates/processus-metier/template-processus-metier.yaml`