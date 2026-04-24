---
id: ADR-BCM-URBA-0011
title: "Décompression locale de la complexité par L3 tout en conservant L2 comme pivot"
status: Proposed
date: 2026-03-17

family: URBA

decision_scope:
  level: Cross-Level
  zoning:
    - SERVICES_COEUR
    - SUPPORT
    - REFERENTIEL
    - DATA_ANALYTIQUE

impacted_capabilities: []
impacted_events: []
impacted_mappings:
  - SI
  - DATA
  - ORG

related_adr:
  - ADR-BCM-URBA-0004
  - ADR-BCM-URBA-0007
  - ADR-BCM-URBA-0008
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010
  - ADR-BCM-FUNC-0002
  - ADR-BCM-FUNC-0003

supersedes: []

tags:
  - BCM
  - L2
  - L3
  - complexite
  - evenements
  - urbanisation

stability_impact: Structural
---

# ADR-BCM-URBA-0011 — Décompression locale de la complexité par L3 tout en conservant L2 comme pivot

## Contexte

Le niveau L2 a été retenu comme pivot d’urbanisation, point d’ancrage des relations du modèle, niveau de référence pour les mappings SI / DATA / ORG et pour l’ownership fonctionnel.

Dans certaines capacités L2, notamment lorsque la densité de règles, la variété des cas de gestion ou la charge cognitive deviennent trop fortes, une modélisation purement L2 peut devenir difficile à exploiter opérationnellement.

Ce risque est particulièrement visible sur des capacités comme l’instruction ou l’indemnisation dans la capacité CAP.COEUR.005 "Sinistres & Prestations", qui concentrent de nombreuses variantes métier, décisions intermédiaires et interactions externes.

## Décision

### 1) Le niveau L2 reste le pivot par défaut

Les capacités L2 demeurent :
- le niveau de référence pour l’ownership,
- le point d’ancrage des objets métier, événements métier et abonnements métier,
- le niveau canonique de lecture transverse,
- le niveau de référence des mappings SI / DATA / ORG.

### 2) Le niveau L3 est autorisé uniquement comme mécanisme local de décompression

Lorsqu’une capacité L2 devient trop complexe pour rester gouvernable à elle seule, un niveau L3 peut être introduit localement pour :
- ségréger des sous-ensembles homogènes,
- expliciter la production détaillée,
- réduire la charge cognitive et la taille des contrats opérationnels.

Le L3 ne devient pas un nouveau pivot global.

### 3) Les contrats canoniques restent exprimés au niveau L2

Les consommateurs transverses doivent continuer à s’appuyer en priorité sur les objets métier, événements métier et abonnements métier rattachés au L2.

Les éléments plus fins introduits au L3 servent à décrire la production détaillée ou spécialisée d’une capacité L2, sans remettre en cause la lisibilité transverse du modèle.

### 4) Les éléments détaillés peuvent être réagrégés vers le L2

Quand un zoom L3 est utilisé, des mécanismes d’agrégation, de normalisation ou de projection peuvent être employés pour reconstituer un jalon canonique au niveau L2.

Le L2 reste donc le niveau d’exposition transverse ; le L3 reste le niveau local de détail.

## Conséquences

### Positives

- Conservation d’une règle simple et stable : L2 reste le pivot.
- Possibilité de traiter localement les zones trop denses sans refondre tout le modèle.
- Meilleure maîtrise de la complexité sur les capacités les plus chargées.
- Maintien d’une lecture transverse homogène pour les consommateurs.

### Négatives / Risques

- Introduction d’une couche supplémentaire de dérivation entre L3 et L2.
- Risque de sur-utiliser le L3 si les critères d’entrée ne sont pas explicités.
- Nécessité de gouverner clairement les règles de réagrégation et de responsabilité.

### Dette acceptée

- Les critères précis de déclenchement d’un zoom L3 pourront être affinés par ADR locale de capacité.
- Tous les cas de décomposition L3 ne sont pas définis à ce stade.
- Certaines capacités L2 pourront rester temporairement surchargées avant formalisation de leur L3.

## Règle de gouvernance

Un zoom L3 n’est acceptable que si les trois conditions suivantes sont réunies :
1. la capacité L2 n’est plus cognitivement ou opérationnellement maîtrisable en l’état ;
2. la décomposition permet d’isoler des sous-ensembles réellement homogènes ;
3. les contrats canoniques exposés au reste du SI demeurent lisibles au niveau L2.

## Indicateurs de gouvernance

- Le niveau L2 reste le point d’ancrage de 100 % des mappings SI / DATA / ORG.
- Le recours au L3 reste justifié par exception documentée.
- Chaque capacité disposant d’un L3 conserve un contrat canonique identifiable au niveau L2.

## Traçabilité

- Références :
  - ADR-BCM-URBA-0004 — bon niveau de décision
  - ADR-BCM-URBA-0007 — méta-modèle événementiel normalisé
  - ADR-BCM-URBA-0008 — modélisation des événements à deux niveaux
  - ADR-BCM-URBA-0009 — définition complète d’une capacité
  - ADR-BCM-URBA-0010 — L2 pivot d’urbanisation
  - ADR-BCM-FUNC-0002 — découpage L2 de COEUR.005
  - ADR-BCM-FUNC-0003 — limites de DSP