---
id: ADR-BCM-URBA-0004
title: "Décider au bon niveau (L1/L2/L3)"
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
  - ADR-BCM-GOV-0002  # collège d'arbitrage
  - ADR-BCM-URBA-0002

supersedes: []

tags:
  - BCM
  - Gouvernance
  - Décisions

stability_impact: Structural
---

# ADR-BCM-URBA-0004 — Décider au bon niveau (L1/L2/L3)

## Contexte
Sans règle explicite de “niveau de décision”, les arbitrages se font :
- trop macro (au L1) : décisions floues, non actionnables,
- trop fin (au L3) : micro-optimisation, discussions interminables, instabilité du modèle.

Cela impacte directement :
- la priorisation des roadmaps,
- la rationalisation applicative,
- la définition des services et contrats d’intégration.

## Décision
- **L1** sert au cadrage stratégique, à la communication et au pilotage “valeur”.
- **L2** sert aux arbitrages d’urbanisation : ownership, rationalisation, budgets, priorisation, trajectoires.
- **L3** sert au design actionnable : services métiers, contrats (API/événements), règles détaillées, tests de couverture.

Le domaine L3 ne doit être explicité que dans des cas exceptionnels :
- Très fort axe d'avantage cométitif, axe prioritaire de developpement stratégique de l'entreprise
- Niveau de complexité nécessitant de descendre encore d'un niveau pour permettre d'appréhender cette complexité et de réaliser les arbitrages généralement réalisé au niveau 2

Le niveau 3 ne doit pas resté en l'état, c'est un stade transitoire :
- Il doit suivre la stratégie du moment et ne pas alourdir la carto avec des visions passées
- s'effacer pour revoir l'organistion en niveau L1 et niveau L2 pour résoudre la complexité accidentelle qui aura été trouvée.

Cette carte doit permettre de servir de guide et rester à un certain niveau de simplicité pour permettre à tous les acteurs s'en emparer simplement et ainsi d'appuyer les challenges stratégiques de l'entreprise.

## Justification
- **L1** offre la vision stratégique et la communication : stable, pérenne, compréhensible par tous.
- **L2** est le niveau pivot pour l'urbanisation : suffisamment stable pour organiser responsabilités, investissements et transformation, suffisamment granulaire pour arbitrer la rationalisation applicative.
- **L3** existe dans le modèle mais est **utilisé de manière exceptionnelle et transitoire** :
  - **Exceptionnel** : uniquement sur les axes d'avantage compétitif ou les zones de forte complexité où L2 ne suffit plus pour arbitrer
  - **Transitoire** : une fois les arbitrages faits et la complexité accidentelle résolue, L3 doit soit s'effacer (retour à L2), soit conduire à une réorganisation L1/L2 plus pertinente
  - **Guidant** : L3 sert à éclairer temporairement des décisions de design (services métiers, contrats API/événements, règles détaillées) mais ne doit pas alourdir durablement la carte

L'objectif est de **garder la BCM simple et appropriable** par tous les acteurs, tout en permettant des zooms ponctuels sur les zones critiques.

### Alternatives considérées

- **Décider tout au L1** — rejeté car insuffisant pour l'urbanisation, trop macro pour les arbitrages.
- **Décider tout au L3** — rejeté car instable, trop coûteux, favorise la dérive “process map”, perte de lisibilité.
- **L3 permanent et exhaustif** — rejeté car complexité excessive, maintenance coûteuse, risque de cartographie encyclopédique non actuelle.

## Impacts sur la BCM

### Structure

- **Roadmaps** : structurées par capabilities **L2** (niveau de pilotage par défaut).
- **Backlogs de transformation** : détaillés en **L3** uniquement sur les domaines critiques / en transformation / à fort avantage compétitif.
- **Revues d'architecture** : décisions de découpage au **L2**, décisions de contrats/intégration au **L3**.
- **Gouvernance du L3** :
  - Création d'un L3 nécessite justification explicite (complexité, criticité, enjeu stratégique)
  - Revue périodique pour supprimer ou "remonter" les L3 devenus non pertinents
  - Les vues par défaut (BCM L1/L2) ne montrent **pas** les L3 pour garder la lisibilité

### Événements (si applicable)

- Aucun impact direct.

### Mapping SI / Data / Org

- Aucun impact direct.

## Conséquences
### Positives
- Arbitrages plus rapides et comparables (concentration sur L2).
- Réduction des débats de granularité (règle claire : L2 par défaut, L3 si justifié).
- Meilleure cohérence des contrats d'intégration (API/événements) avec le modèle.
- **BCM agile** : possibilité de zoomer temporairement (L3) sans alourdir durablement la carte.
- **Alignement priorités stratégiques** : L3 suit la stratégie du moment, évite l'accumulation de dette de modélisation.

### Négatives / Risques
- Nécessite une discipline de gouvernance (templates d'ateliers, règles de modélisation).
- **Discipline de nettoyage** : risque d'oublier de faire "remonter" ou supprimer les L3 devenus obsolètes.
- **Débats sur le seuil** : quand déclencher un L3 ? Critères subjectifs (complexité, criticité) peuvent créer des désaccords.
- **Tentation du détail** : risque de vouloir tout détailler en L3 malgré la règle (nécessite des revues régulières).

### Dette acceptée

- Critères de déclenchement du L3 partiellement subjectifs (complexité, criticité) ; à affiner avec la pratique.
- Discipline de nettoyage du L3 à instaurer progressivement.

## Indicateurs de gouvernance

- Niveau de criticité : Élevé (règle structurante transverse).
- Date de revue recommandée : 2028-01-21.
- Indicateur de stabilité attendu : aucun L3 présent dans les vues par défaut sans justification formalisée.

## Traçabilité

- Atelier : Guide d'urbanisation BCM v1 — section "Niveaux de décision"
- Participants : EA / Urbanisation, Business Architecture
- Références : ADR-BCM-URBA-0002
