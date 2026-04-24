---
id: ADR-BCM-GOV-0001
title: "Gouvernance des décisions BCM – hiérarchie GOV / URBA / FUNC"
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

related_adr: []

supersedes: []

tags:
  - gouvernance
  - hiérarchie
  - GOV
  - URBA
  - FUNC

stability_impact: Structural
---

# ADR-BCM-GOV-0001 — Gouvernance des décisions BCM

## Contexte

Le plan d'occupation des sols (POS, une BCM qui ne dit pas son nom) constitue le référentiel fonctionnel structurant du Système d’Information.

Trois types de décisions distinctes sont identifiés :

1. **Décisions de gouvernance (GOV)**
   - Organisation du cadre décisionnel
   - Hiérarchie des ADR
   - Mécanismes d'arbitrage
   - Cycle de vie et revue périodique des décisions

2. **Décisions d'urbanisation (URBA)**
   - Définition des principes de modélisation
   - Règles de zoning
   - Règles de niveau L1/L2/L3
   - Règles de découplage logique / physique
   - Principes d'ownership et de responsabilité

3. **Décisions de modélisation fonctionnelle (FUNC)**
   - Split / merge de capabilities
   - Placement d'une capacité dans une zone
   - Création ou suppression de L3
   - Ajustement de périmètre fonctionnel

Ces décisions relèvent de compétences différentes et doivent être gouvernées de manière explicite afin d’éviter :
- La divergence du modèle,
- Les contradictions entre principes et implémentations,
- La dérive progressive de la BCM.

## Décision

La gouvernance des ADR BCM est structurée selon une hiérarchie explicite à **trois niveaux** :

### 1. ADR de niveau GOV (Gouvernance)

- Définissent les **méta-règles** du cadre décisionnel BCM lui-même.
- Portée : transverse, applicable à l’ensemble du référentiel.
- Exemples : hiérarchie des ADR, collège d’arbitrage, revue périodique.
- Très peu fréquents, très stables.
- Ne peuvent être modifiés que par un autre ADR GOV.
- Validés par le collège BCM ou l’équivalent d’une cellule d’urbanisme d’entreprise.

### 2. ADR de niveau URBA (Urbanisme)

- Définissent les **règles structurantes du modèle BCM**.
- Portée : transverse, applicable à l’ensemble des capabilities.
- Exemples : zoning en 7 zones, découpage L1/L2/L3, principe 1 capacité = 1 responsabilité.
- Peu fréquents, fortement stables.
- Ne peuvent être modifiés que par un autre ADR URBA ou GOV.
- Validés par les architectes d’entreprise.

### 3. ADR de niveau FUNC (Fonctionnel)

- Appliquent les règles URBA à un **périmètre fonctionnel précis**.
- Impactent explicitement une ou plusieurs capabilities.
- Peuvent évoluer plus fréquemment.
- Doivent obligatoirement référencer les ADR URBA applicables.
- Validés par les architectes fonctionnels ou les équipes métier concernées.

### Règle de classification

| Critère                       | GOV | URBA | FUNC |
|-------------------------------|-----|------|------|
| Porte sur le cadre décisionnel | ✅  |      |      |
| Porte sur la structure du modèle |   | ✅   |      |
| Porte sur un périmètre fonctionnel |  |    | ✅   |

### Règles de hiérarchie

- Un ADR FUNC **ne peut pas contredire** un ADR URBA.
- Un ADR URBA **ne peut pas contredire** un ADR GOV.
- Tout ADR FUNC doit inclure un champ `related_adr` pointant vers les ADR URBA concernés.
- La BCM (capabilities.yaml) est modifiée uniquement à la suite d’un ADR accepté.

```text
ADR GOV  — Méta-règles du cadre décisionnel
  ↓ encadre
ADR URBA — Principes structurants du modèle
  ↓ contraint
ADR FUNC — Décisions de modélisation fonctionnelle
  ↓ matérialise
BCM (capabilities.yaml)
```

### Organisation documentaire

- Tous les ADR sont stockés dans un référentiel unique.
- Un template commun est utilisé.
- La distinction est assurée par le champ `family`.

### Clause d’évolutivité et anti-dogme

La BCM est un modèle vivant.

Aucun ADR (GOV, URBA ou FUNC) ne constitue une règle intangible ou définitive.

Afin d'éviter toute dérive dogmatique :

- Tout ADR doit pouvoir être challengé par un ADR ultérieur de même niveau ou supérieur.
- Un mécanisme formel de remise en question est autorisé à l'initiative :
  - d'un membre du collège BCM,
  - d'une équipe projet,
  - ou d'un représentant métier impacté.
- Les ADR GOV et URBA doivent faire l'objet d'une revue périodique (minimum tous les 24 mois).

Le principe directeur est :

> La cohérence du modèle ne doit jamais primer sur la valeur métier.

La BCM est un outil d’alignement, non une finalité en soi.

## Justification

Cette structuration en trois niveaux permet :

- De clarifier les responsabilités décisionnelles à chaque niveau.
- De séparer gouvernance institutionnelle (GOV), principes d'urbanisation (URBA) et modélisation opérationnelle (FUNC).
- D'éviter les conflits entre équipes (gouvernance vs urbanisation vs métier).
- D'assurer la cohérence du modèle dans le temps.
- De permettre un pilotage de la stabilité du modèle.

Elle introduit une analogie explicite :

- ADR GOV = Constitution du modèle (comment on décide)
- ADR URBA = Lois fondamentales (les règles du jeu)
- ADR FUNC = Décrets d'application (les décisions opérationnelles)

### Alternatives considérées

- Approche non hiérarchisée (un seul type d'ADR) — rejetée car elle mélange gouvernance, principes structurants et décisions opérationnelles.
- Hiérarchie à 2 niveaux (Structural / Functional) — rejetée car elle ne distingue pas explicitement les décisions de gouvernance (comment on décide) des décisions d'urbanisation (les règles du modèle).
- Gouvernance uniquement centralisée par urbanisation — rejetée car elle réduit l’appropriation par les équipes fonctionnelles.

## Impacts sur la BCM

### Structure

- Formalisation d'une hiérarchie décisionnelle à trois niveaux : GOV → URBA → FUNC.
- Obligation de traçabilité croisée entre niveaux via le champ `related_adr`.
- Stabilisation des principes de gouvernance (GOV) et d'urbanisation (URBA), sécurisation des évolutions fonctionnelles (FUNC).

### Événements (si applicable)

- Aucun impact direct sur les événements métier.

### Mapping SI / Data / Org

- Applications impactées : gouvernance transverse (SI).
- Flux impactés : gouvernance et traçabilité des décisions (DATA/ORG).

## Conséquences

### Positives

- Gouvernance claire.
- Responsabilités explicites.
- Modèle plus robuste.
- Réduction des conflits décisionnels.
- Meilleure auditabilité des évolutions.

### Négatives / Risques

- Complexité de gouvernance accrue.
- Nécessite discipline documentaire.
- Risque de rigidité si trop formalisé.

### Dette acceptée

- Nécessité d’acculturation des équipes.
- Ajustements possibles dans la pratique.

## Indicateurs de gouvernance

- Niveau de criticité : Élevé (décision structurante transverse).
- Date de revue recommandée : 2028-02-26.
- Indicateur de stabilité attendu :
  - Nombre d'ADR FUNC non rattachés à un ADR URBA = 0.
  - Nombre d'ADR URBA non rattachés à un ADR GOV = 0.
  - Toute modification structurelle du modèle passe par un ADR URBA ou GOV.
  - Chaque famille (GOV, URBA, FUNC) est correctement affectée via le champ `family`.

## Traçabilité

- Atelier Gouvernance BCM – 2026-02-26
- Participants : EA / Business Architecture
- Références : 