---
id: ADR-TECH-STRAT-005
title: "Observabilité & Gouvernance — L2 comme Unité Primaire, OpenTelemetry, EventCatalog"
status: Proposed
date: 2026-04-26

family: TECH
tech_domain: OBSERVABILITY

grounded_in_urba:
  - ADR-BCM-URBA-0009   # capacité = unité d'émission événementielle — même principe pour les métriques
  - ADR-BCM-URBA-0010   # L2 pivot d'urbanisation — pivot d'observabilité
  - ADR-BCM-GOV-0003    # revue de stabilité périodique — nécessite des indicateurs par L2

grounded_in_func:
  - ADR-BCM-FUNC-0004   # L1 breakdown — 11 L1s, 20+ L2s à instrumenter
  - ADR-BCM-FUNC-0008   # BSP.004.AUT — chemin critique latence TPE, SLO strict
  - ADR-BCM-FUNC-0005   # BSP.001.SCO — volume élevé, calcul de score continu

related_adr:
  - ADR-TECH-STRAT-001  # Event Infrastructure — RabbitMQ + Kafka (canaux à tracer)
  - ADR-TECH-STRAT-002  # Runtime — monolithe modulaire par zone (déployable = agrégation)
  - ADR-TECH-STRAT-003  # API Contract — BFF + REST inter-L2 (chaînes à tracer)
  - ADR-TECH-STRAT-004  # Data Layer — bases par L2 (métriques de persistance par L2)

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
  - observabilité
  - opentelemetry
  - tracing
  - slo
  - eventcatalog
  - l2-pivot
  - gouvernance-schéma

stability_impact: Structural
---

# ADR-TECH-STRAT-005 — Observabilité & Gouvernance

## Context

Le BCM de Reliever déploie 20+ L2 capabilities regroupées dans 7 déployables de zone
(ADR-TECH-STRAT-002). Une transaction bénéficiaire peut traverser plusieurs L2 via des
canaux hétérogènes : appel REST synchrone (BFF → BSP), puis messages RabbitMQ asynchrones
(BSP.004.AUT → BSP.001.SCO → BSP.001.PAL), avec publication parallèle sur Kafka pour
l'analytique (DAT.001).

URBA-0010 positionne le L2 comme pivot d'urbanisation. Cette primauté doit se retrouver
dans l'observabilité : un L2 doit pouvoir être évalué indépendamment du déployable qui
l'héberge. La surveillance au niveau du seul déployable de zone masque les dégradations
intra-zone et rend impossible l'évaluation de la santé d'une capacité métier précise.

ADR-BCM-GOV-0003 impose des revues de stabilité périodiques du BCM. Ces revues nécessitent
des indicateurs de santé par L2 (événements produits, SLOs respectés, anomalies) pour
être outillées et non anecdotiques.

La gouvernance des contrats événementiels est assurée en design-time par les artefacts YAML
BCM et leur projection EventCatalog (ADR-TECH-STRAT-001). L'observabilité complète cette
gouvernance en runtime : elle détecte les écarts entre le contrat déclaré et les messages
effectivement produits.

## Decision

### Tracing distribué — exigence J0

- **Règle 1** : Le tracing distribué est une **exigence du premier jour** — aucun L2 ne
  peut être mis en production sans instrumentation de tracing active.
- **Règle 2** : Le standard d'instrumentation est **OpenTelemetry** (OTel). Toute
  instrumentation propriétaire est exclue. Le backend de collecte et de visualisation
  est une décision de la plateforme (hors périmètre de cet ADR).
- **Règle 3** : Le **trace ID** est propagé sur tous les canaux sans exception :
  - **HTTP** : header standard `traceparent` (W3C Trace Context)
  - **RabbitMQ** : header de message `traceparent` — chaque consommateur extrait le
    contexte de trace parent avant de créer son span enfant
  - **Kafka** : header de record `traceparent` — même principe pour le rail analytique
- **Règle 4** : La corrélation entre le chemin synchrone (autorisation BSP.004.AUT) et
  les effets asynchrones (score BSP.001.SCO, palier BSP.001.PAL) est garantie par la
  propagation du trace ID dans les headers RabbitMQ des messages publiés après la décision
  synchrone. Le chemin complet d'une transaction est reconstituable en un seul trace.

### Granularité d'observabilité — L2 comme unité primaire

- **Règle 5** : Chaque L2 instrumente ses métriques, logs et traces avec son **identifiant
  de capacité BCM comme dimension primaire** : `capability_id = CAP.BSP.004.AUT`. Cette
  dimension est obligatoire sur toute métrique, tout log structuré et tout span OTel produit
  par un L2.
- **Règle 6** : Les **SLOs sont définis et alertés au niveau L2** — pas au niveau du
  déployable de zone. Un SLO de disponibilité ou de latence s'exprime sur `CAP.BSP.004.AUT`,
  pas sur le déployable BSP.
- **Règle 7** : Le déployable de zone constitue une **vue agrégée secondaire** — un tableau
  de bord de zone agrégeant les L2 qu'il héberge. Cette vue est utile opérationnellement
  mais ne remplace pas les SLOs L2.
- **Règle 8** : Les dimensions minimales obligatoires sur toute métrique ou log structuré :
  `capability_id`, `zone`, `deployable`, `environment`. Le `capability_id` permet le
  filtrage et l'agrégation indépendamment de la topologie de déploiement.

### Gouvernance des contrats événementiels

- **Règle 9** : **EventCatalog** (généré depuis les artefacts YAML BCM) est la source de
  vérité design-time des contrats événementiels — types d'événements, routing keys,
  ownership par L2. Il n'existe pas de registry de schéma runtime (ADR-TECH-STRAT-001).
- **Règle 10** : L'observabilité runtime complète la gouvernance design-time en surveillant
  les écarts : volume d'événements produits par L2 par rapport aux contrats déclarés,
  présence de routing keys non référencées dans le BCM, messages sans `traceparent`.
  Ces écarts sont des alertes de gouvernance, pas seulement des alertes opérationnelles.
- **Règle 11** : Les revues de stabilité périodiques (ADR-BCM-GOV-0003) s'appuient sur
  les métriques d'observabilité par L2 pour évaluer la santé du BCM en production :
  un L2 qui ne produit aucun événement depuis N jours est un signal de revue.

## Justification

1. **Tracing J0** : le chemin d'une transaction Reliever est asynchrone et multi-L2 dès
   le premier cas d'usage (achat → score → palier). Sans tracing distribué dès le départ,
   le débogage des anomalies en production nécessite une corrélation manuelle de logs
   disparates — inacceptable sur un système financier avec des obligations de traçabilité.

2. **L2 comme unité primaire** : URBA-0010 fait du L2 le pivot de toutes les décisions
   d'urbanisation. L'observabilité au niveau déployable ne correspond à aucune frontière
   sémantique métier — elle cache les dégradations intra-zone. Un SLO sur `CAP.BSP.004.AUT`
   est actionnable par l'équipe métier ; un SLO sur le déployable BSP ne l'est pas.

3. **OpenTelemetry** : standard CNCF vendor-neutral, supporté nativement par tous les
   frameworks modernes (.NET, Java, Go, Node) et tous les backends d'observabilité
   (Jaeger, Tempo, Datadog, Honeycomb). Évite le lock-in sur un vendeur d'APM et laisse
   la décision de backend à la plateforme.

4. **EventCatalog comme gouvernance design-time** : un registry runtime ajoute une
   dépendance opérationnelle sur le chemin de publication des messages. L'approche
   design-time (YAML BCM → EventCatalog) découple la gouvernance du runtime tout en
   rendant les contrats auditables et versionnés dans Git.

### Alternatives Considérées

- **Observabilité au niveau déployable de zone uniquement** — rejeté : masque les
  dégradations intra-zone, incompatible avec les revues de stabilité BCM (GOV-0003),
  et rend impossible l'évaluation de la santé d'une capacité métier précise sans
  fouiller les logs manuellement.

- **Registry de schéma runtime (Confluent Schema Registry)** — écarté à ce stade :
  ajoute une dépendance opérationnelle sur le chemin critique de publication RabbitMQ.
  La gouvernance design-time (YAML BCM) est suffisante à l'amorçage. Option à
  reconsidérer si le nombre de producteurs d'événements rend la coordination
  design-time impraticable.

- **Tracing différé (post-MVP)** — rejeté : le système est asynchrone et multi-L2
  dès le premier cas d'usage en production. Ajouter le tracing après coup nécessite
  de modifier tous les L2 simultanément — coût élevé, risque de régression.

## Technical Impact

### On Event Infrastructure

- Chaque message RabbitMQ doit porter le header `traceparent` — à la charge du L2
  producteur lors de la publication
- Chaque data product Kafka doit porter le header `traceparent` dans le record

### On Service Boundaries

- Le `capability_id` comme dimension obligatoire implique que chaque module L2 à
  l'intérieur d'un déployable de zone est identifiable dans les métriques — renforçant
  la discipline de frontière de module (ADR-TECH-STRAT-002, Règle 2)

### On API Contracts

- Les appels REST inter-L2 et BFF → BSP propagent le `traceparent` via le header
  W3C Trace Context — standard HTTP, aucune convention propriétaire

## Consequences

### Positive

- Chemin complet d'une transaction reconstituable en un seul trace (synchrone + asynchrone)
- SLOs alignés sur les frontières métier L2 — actionnables par les équipes produit
- Revues de stabilité BCM outillées par les métriques de production
- Gouvernance événementielle auditée en continu sans registry runtime

### Negative / Risks

- Discipline d'instrumentation obligatoire J0 : chaque L2 doit être instrumenté avant
  mise en production — augmente le coût initial de delivery
- La propagation du `traceparent` dans RabbitMQ est manuelle (pas native au broker) —
  risque d'oubli sur un L2 ; à mitiger par un test d'intégration vérifiant la présence
  du header sur les messages produits

### Accepted Debt

- Le backend de collecte OTel (Jaeger, Grafana Tempo, ou équivalent) est une décision
  de la plateforme — à aligner avec l'équipe plateforme avant le premier déploiement
- La définition précise des SLOs par L2 (latence p99, taux d'erreur, disponibilité)
  est déléguée aux ADRs d'implémentation de chaque L2

## Governance Indicators

- Review trigger : introduction d'un registry runtime imposée par une exigence réglementaire
  ou par un volume de producteurs rendant la coordination design-time ingérable ; ou
  constat que les SLOs L2 sont systématiquement violés sans corrélation avec les SLOs zone
- Expected stability : 3 ans — OpenTelemetry est un standard stable ; la granularité
  L2 est structurelle

## Traceability

- Session : Technical brainstorming 2026-04-26
- Participants : yremy
- References :
  - ADR-BCM-URBA-0010 — L2 pivot d'urbanisation
  - ADR-BCM-GOV-0003 — Revue de stabilité périodique
  - ADR-BCM-FUNC-0008 — BSP.004 Transaction Control (SLO latence critique)
  - ADR-TECH-STRAT-001 — Infrastructure événementielle (canaux à tracer)
  - ADR-TECH-STRAT-002 — Runtime microservice (déployable = agrégation secondaire)
  - W3C Trace Context — https://www.w3.org/TR/trace-context/
  - OpenTelemetry — https://opentelemetry.io
