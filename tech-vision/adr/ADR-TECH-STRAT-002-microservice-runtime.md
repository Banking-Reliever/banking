---
id: ADR-TECH-STRAT-002
title: "Runtime Microservice — Monolithe Modulaire par Zone TOGAF"
status: Proposed
date: 2026-04-26

family: TECH
tech_domain: RUNTIME

grounded_in_urba:
  - ADR-BCM-URBA-0002   # 3 niveaux L1/L2/L3
  - ADR-BCM-URBA-0003   # 1 capacité = 1 responsabilité
  - ADR-BCM-URBA-0010   # L2 pivot d'urbanisation
  - ADR-BCM-URBA-0011   # L3 décompression locale dans le L2

grounded_in_func:
  - ADR-BCM-FUNC-0004   # L1 breakdown — 7 zones, 11 L1s
  - ADR-BCM-FUNC-0005   # BSP.001 — 4 L2s (zone la plus complexe)
  - ADR-BCM-FUNC-0008   # BSP.004 — contrainte de latence AUT

related_adr:
  - ADR-TECH-STRAT-001  # Event Infrastructure — RabbitMQ inter-L2

supersedes: []

impacted_zones:
  - PILOTAGE
  - SERVICES_COEUR
  - SUPPORT
  - REFERENTIEL
  - ECHANGE_B2B
  - CANAL
  - DATA_ANALYTIQUE

tags:
  - runtime
  - modular-monolith
  - deployment
  - pizza-team
  - togaf-zones

stability_impact: Structural
---

# ADR-TECH-STRAT-002 — Runtime Microservice — Monolithe Modulaire par Zone TOGAF

## Context

Le BCM de Reliever compte 11 L1 répartis sur 7 zones TOGAF, décomposés en 20+ L2 capabilities
(ADR-BCM-FUNC-0004 à 0015). URBA-0010 positionne le L2 comme pivot d'urbanisation et frontière
naturelle de microservice. URBA-0011 autorise la décompression locale en L3 à l'intérieur d'un L2
sans en faire une frontière de déploiement.

À l'amorçage du projet, une seule équipe opère l'ensemble du système. Créer 20+ déployables
indépendants dès le départ imposerait une charge opérationnelle (CI/CD, observabilité, gestion
des dépendances de déploiement) disproportionnée par rapport à la taille de l'équipe et au
stade de maturité du produit.

La zone TOGAF constitue une frontière d'urbanisation forte (URBA-0001) — deux L2 de zones
différentes n'ont pas les mêmes contraintes de gouvernance, de sécurité et de cycle de vie.
Elle est donc retenue comme frontière minimale de déploiement.

## Decision

- **Règle 1** : L'unité de déploiement à l'amorçage est la **zone TOGAF**. Chaque zone donne
  lieu à exactement un déployable, soit 7 déployables à l'amorçage de Reliever.
- **Règle 2** : À l'intérieur d'un déployable de zone, chaque L2 constitue une **frontière de
  module** (package, namespace, bounded context interne) — pas un processus séparé. La frontière
  de module L2 est obligatoire et non négociable : elle prépare toute future extraction.
- **Règle 3** : Les L3, lorsqu'ils existent, sont des **sous-modules** à l'intérieur de leur L2
  parent, conformément à URBA-0011. Ils ne constituent jamais une frontière de déploiement.
- **Règle 4** : L'extraction d'un L2 ou d'un L1 en déployable indépendant est déclenchée
  exclusivement par l'un des critères suivants, documenté dans un nouvel ADR-TECH-STRAT :
  - **Organisationnel** : une équipe distincte prend possession du L2
  - **Performance** : le L2 nécessite un scaling indépendant (ex. BSP.004.AUT sous charge TPE)
  - **Sécurité** : le L2 traite des données nécessitant un isolement de processus (ex. SUP.001)
  - **FinOps** : le coût d'hébergement du L2 justifie un profil de ressources distinct
  - **Complexité sémantique** : le L2 évolue à un rythme incompatible avec son déployable de zone
- **Règle 5** : Les frontières de module L2 à l'intérieur d'un déployable de zone **ne
  communiquent pas par appel direct inter-module**. Toute communication entre L2 — même
  colocalisés — transite par RabbitMQ (ADR-TECH-STRAT-001), préservant les contrats
  événementiels et rendant toute future extraction transparente.

## Justification

Le choix du monolithe modulaire par zone repose sur trois arguments :

1. **Capacité opérationnelle** : une pizza team ne peut pas opérer 20+ pipelines CI/CD,
   20+ services en observabilité et 20+ configurations de déploiement sans que la charge
   d'infrastructure dépasse la capacité de delivery produit. Le monolithe modulaire réduit
   la surface opérationnelle sans sacrifier les frontières sémantiques.

2. **Préservation des frontières** : la discipline de module L2 obligatoire (Règle 2) et
   l'interdiction de communication inter-module hors RabbitMQ (Règle 5) garantissent que
   l'extraction future d'un L2 est une opération de déploiement, pas une refactorisation.
   Le couplage reste faible même à l'intérieur d'un déployable.

3. **Zone TOGAF comme frontière minimale** : URBA-0001 établit des zones aux contraintes
   distinctes (gouvernance, cycle de vie, sécurité). Fusionner des L2 de zones différentes
   dans un même déployable mélangerait des niveaux de confidentialité et des politiques de
   déploiement incompatibles.

### Alternatives Considérées

- **1 déployable par L2 dès le départ** — rejeté : charge opérationnelle disproportionnée
  pour une équipe unique. La valeur de l'isolation de déploiement n'est réalisée que quand
  les équipes ou les contraintes le justifient.

- **1 déployable unique pour tout Reliever** — rejeté : viole les frontières de zone TOGAF
  (URBA-0001) — sécurité, gouvernance et cycles de vie des zones sont incompatibles dans
  un seul processus. Impraticable dès qu'une contrainte réglementaire (RGPD, DSP2) s'applique
  différemment selon la zone.

- **1 déployable par L1** — considéré mais écarté à l'amorçage : 11 déployables reste
  gérable, mais l'alignement sur la zone TOGAF est plus fort sémantiquement et prépare
  mieux les décisions de sécurité et de gouvernance par zone. Option à privilégier si
  l'équipe grandit avant que des L2 individuels nécessitent une extraction.

## Technical Impact

### On Service Boundaries

- 7 déployables à l'amorçage : BSP, CAN, B2B, SUP, REF, DAT, PIL
- Chaque déployable expose ses L2 comme modules internes structurés par package/namespace
- La convention de nommage des modules suit le pattern BCM : `CAP.{ZONE}.{NNN}` (URBA-0006)

### On Event Infrastructure

- La Règle 5 (communication inter-L2 via RabbitMQ même si colocalisés) implique que le
  déployable BSP publie et consomme sur RabbitMQ pour les échanges entre BSP.001, BSP.002,
  BSP.003 et BSP.004 — même s'ils partagent le même processus
- Ceci garantit que l'extraction future de BSP.004 (candidat probable pour raison de
  performance) ne nécessite aucune modification des autres L2

### On Data Ownership

- Chaque déployable de zone gère sa propre persistance. Les L2 d'une même zone peuvent
  partager un cluster de base de données, mais chaque L2 possède son propre schéma logique.

## Consequences

### Positive

- Surface opérationnelle réduite à 7 pipelines à l'amorçage
- Frontières sémantiques L2 préservées grâce à la discipline de module
- Extraction future d'un L2 = opération de déploiement uniquement (pas de refactorisation)
- Alignement fort entre zone TOGAF et déployable (gouvernance, sécurité, cycle de vie)

### Negative / Risks

- La communication RabbitMQ entre L2 colocalisés introduit une latence réseau interne
  évitable — acceptée en échange de la préservation des contrats événementiels
- Le risque de glissement des frontières de module (L2 qui s'appellent directement) doit
  être mitigé par des règles de linting d'architecture (ArchUnit ou équivalent)

### Accepted Debt

- La règle de non-communication directe inter-module (Règle 5) doit être outillée
  (contrôle statique de dépendances) pour éviter la dégradation silencieuse des frontières.
  En l'absence d'outillage, la dette s'accumule sans signal visible.

## Governance Indicators

- Review trigger : arrivée d'une deuxième équipe sur le projet ; ou constat de contention
  de déploiement entre L2 d'une même zone (cycles de release incompatibles)
- Expected stability : 18 mois — à réévaluer lors de la première revue de stabilité GOV

## Traceability

- Session : Technical brainstorming 2026-04-26
- Participants : yremy
- References :
  - ADR-BCM-URBA-0001 — Zoning TOGAF étendu
  - ADR-BCM-URBA-0002 — 3 niveaux L1/L2/L3
  - ADR-BCM-URBA-0010 — L2 pivot d'urbanisation
  - ADR-BCM-URBA-0011 — L3 décompression locale
  - ADR-TECH-STRAT-001 — Infrastructure événementielle
