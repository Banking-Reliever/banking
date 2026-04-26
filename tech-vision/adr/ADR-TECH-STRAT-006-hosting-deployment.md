---
id: ADR-TECH-STRAT-006
title: "Hébergement & Déploiement — Kubernetes, 4 Environnements, GitOps J0"
status: Proposed
date: 2026-04-26

family: TECH
tech_domain: DEPLOYMENT

grounded_in_urba:
  - ADR-BCM-URBA-0001   # zoning TOGAF — 7 zones = 7 déployables à isoler
  - ADR-BCM-URBA-0003   # 1 capacité = 1 responsabilité — isolation de déploiement par zone

grounded_in_func:
  - ADR-BCM-FUNC-0004   # L1 breakdown — 7 zones à déployer indépendamment
  - ADR-BCM-FUNC-0008   # BSP.004.AUT — exigence de disponibilité et de reproductibilité

related_adr:
  - ADR-TECH-STRAT-001  # Event Infrastructure — RabbitMQ + Kafka (ressources plateforme)
  - ADR-TECH-STRAT-002  # Runtime — 7 déployables par zone TOGAF
  - ADR-TECH-STRAT-005  # Observabilité — OpenTelemetry, backend plateforme

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
  - kubernetes
  - docker
  - gitops
  - déploiement
  - environnements
  - IaC

stability_impact: Structural
---

# ADR-TECH-STRAT-006 — Hébergement & Déploiement

## Context

Le BCM de Reliever produit 7 déployables de zone TOGAF (ADR-TECH-STRAT-002), chacun
constitué de plusieurs L2 modules. Ces déployables consomment des ressources de plateforme
(RabbitMQ, Kafka, bases de données par L2) gérées par une équipe plateforme dédiée et
pre-existante, hors périmètre de ce projet.

La décision de déploiement porte exclusivement sur les **applicatifs L2** — leur
containerisation, leur orchestration, et le modèle de livraison sur les environnements cibles.

Une équipe unique opère l'ensemble du système à l'amorçage. Le modèle de déploiement doit
être reproductible, auditable et ne jamais laisser de divergence silencieuse entre l'état
déclaré (Git) et l'état effectif (cluster).

## Decision

### Containerisation et orchestration

- **Règle 1** : Chaque déployable de zone est packagé en **image Docker**. Aucun déployable
  n'est livré sous une autre forme (JAR nu, binaire VM, ZIP).
- **Règle 2** : L'orchestrateur de déploiement est **Kubernetes**. La plateforme fournit
  le cluster — sa gestion (provisioning, upgrade) est hors périmètre applicatif.
- **Règle 3** : Chaque déployable de zone est déployé dans son propre **namespace Kubernetes**,
  nommé selon la convention BCM : `reliever-{zone-abbrev}` (ex. `reliever-bsp`, `reliever-can`).
  Les namespaces constituent la frontière de réseau et de politique entre zones.

### Environnements

- **Règle 4** : Quatre environnements sont provisionnés dès l'amorçage :
  - `dev` — intégration continue, déploiement automatique sur chaque merge
  - `staging` — validation fonctionnelle et de performance avant promotion en prod
  - `prod` — production ; toute modification passe par staging
  - `demo` — environnement stable pour les démonstrations — promu manuellement depuis staging
- **Règle 5** : La promotion entre environnements suit le flux `dev → staging → prod`.
  L'environnement `demo` est promu depuis `staging` à la discrétion de l'équipe produit.
  Aucune modification n'est appliquée directement en `prod` ou `demo` sans passer par le
  flux de promotion.

### GitOps — exigence J0

- **Règle 6** : Le modèle de déploiement est **GitOps dès le premier déploiement**. L'état
  cible de chaque environnement est intégralement décrit dans Git (manifestes Kubernetes —
  Helm ou Kustomize, décision de la plateforme). Aucune modification manuelle (`kubectl apply`
  direct, patch ad hoc) n'est autorisée sur les environnements `staging`, `prod` et `demo`.
- **Règle 7** : Un opérateur GitOps (ArgoCD, Flux, ou équivalent plateforme) surveille en
  continu la divergence entre l'état Git et l'état effectif du cluster. Toute dérive est
  détectée et alertée. L'état Git fait foi.
- **Règle 8** : Les secrets (credentials RabbitMQ, Kafka, bases de données, OpenFGA) ne
  sont jamais commités en clair dans Git. Ils sont injectés via un mécanisme de gestion de
  secrets plateforme (Vault, Sealed Secrets, External Secrets Operator — décision plateforme).
- **Règle 9** : Chaque déployable de zone dispose de son propre pipeline de build et de
  promotion — les 7 déployables sont indépendants. Un changement dans le déployable BSP
  ne force pas le redéploiement des autres zones.

## Justification

1. **Docker + Kubernetes** : aligné sur la plateforme pre-existante. Kubernetes est le
   standard de facto pour l'orchestration de conteneurs à l'échelle d'un SI multi-zones.
   Il fournit nativement l'isolation réseau par namespace, la gestion des ressources par
   déployable, et les primitives de rolling update nécessaires à la continuité de service.

2. **4 environnements dès l'amorçage** : `dev` et `staging` sont des prérequis à toute
   livraison fiable. `demo` est une contrainte produit pour les phases de commercialisation
   et de pilote. Différer la création de `demo` crée systématiquement une urgence de
   provisionnement au mauvais moment.

3. **GitOps J0** : une équipe unique opérant 7 déployables sur 4 environnements sans GitOps
   accumule rapidement une dette de configuration non tracée. Le coût d'instaurer GitOps
   après coup (migrer l'état existant, auditer les divergences) est supérieur au coût de
   le mettre en place dès le départ. L'auditabilité est une exigence implicite d'un produit
   financier réglementé — chaque changement de configuration doit être traçable.

4. **Namespace par zone** : matérialise en Kubernetes la frontière d'urbanisation TOGAF
   (URBA-0001). Les Network Policies Kubernetes peuvent restreindre les appels inter-namespace
   pour renforcer l'accréditation inter-service décidée dans ADR-TECH-STRAT-003.

### Alternatives Considérées

- **GitOps différé (kubectl/Helm direct dans un premier temps)** — rejeté : la dette de
  configuration non tracée est immédiate sur un SI multi-zones multi-environnements. Le
  surcoût de mise en place J0 est inférieur au coût de la migration post-amorçage.

- **Namespace unique pour tous les déployables** — rejeté : supprime l'isolation réseau
  entre zones TOGAF au niveau Kubernetes, rendant impossible l'application de Network Policies
  différenciées par zone (sécurité, conformité RGPD pour SUP.001).

- **3 environnements (sans demo)** — écarté : l'environnement de démonstration est une
  contrainte produit pour les phases de pilote et de commercialisation. Son absence force
  à utiliser staging pour les démonstrations, risquant de le polluer avec des données de
  démo incompatibles avec les tests de staging.

- **PaaS managé (Heroku, Render, Railway)** — écarté : la granularité de contrôle réseau,
  de politique de sécurité et d'isolation par namespace nécessaire à un produit financier
  réglementé (RGPD, DSP2) n'est pas disponible sur les PaaS grand public.

## Technical Impact

### On Service Boundaries

- 7 namespaces Kubernetes : `reliever-bsp`, `reliever-can`, `reliever-b2b`, `reliever-sup`,
  `reliever-ref`, `reliever-dat`, `reliever-pil`
- Les Network Policies Kubernetes restreignent les appels inter-namespace selon
  l'accréditation inter-service (ADR-TECH-STRAT-003, Règle 8)

### On Event Infrastructure

- RabbitMQ et Kafka sont des ressources plateforme hors namespaces applicatifs — les
  credentials sont injectés via le mécanisme de secrets plateforme (Règle 8)

### On Observability

- Le backend OTel (ADR-TECH-STRAT-005) est une ressource plateforme — les agents de
  collecte sont déployés par la plateforme dans chaque namespace applicatif

## Consequences

### Positive

- Tout changement de configuration est traçable dans Git — auditabilité requise pour
  un produit financier réglementé
- Isolation réseau par zone TOGAF renforçant l'accréditation inter-service
- Pipelines indépendants par zone — un incident BSP ne bloque pas le déploiement CAN
- Environnement demo stable, indépendant de staging

### Negative / Risks

- GitOps J0 implique une courbe d'apprentissage immédiate pour l'équipe sur l'outillage
  (ArgoCD/Flux + Helm/Kustomize) en parallèle du delivery produit
- 4 environnements × 7 namespaces = 28 namespaces à provisionner et maintenir —
  charge plateforme significative assumée par l'équipe dédiée

### Accepted Debt

- Le choix précis de l'opérateur GitOps (ArgoCD vs. Flux) et du format de manifestes
  (Helm vs. Kustomize) est délégué à la plateforme — à aligner avant le premier déploiement
- La stratégie de gestion des secrets (Vault, Sealed Secrets, External Secrets Operator)
  est une décision plateforme — à documenter dans un ADR d'implémentation

## Governance Indicators

- Review trigger : arrivée d'une deuxième équipe nécessitant des pipelines de déploiement
  distincts par équipe ; ou exigence de multi-région imposée par une contrainte de résidence
  des données
- Expected stability : 2 ans — Kubernetes et GitOps sont des standards stables ; les
  choix d'outillage spécifiques (opérateur, format de manifestes) peuvent évoluer sans
  modifier cet ADR

## Traceability

- Session : Technical brainstorming 2026-04-26
- Participants : yremy
- References :
  - ADR-BCM-URBA-0001 — Zoning TOGAF (namespace par zone)
  - ADR-TECH-STRAT-002 — Runtime microservice (7 déployables)
  - ADR-TECH-STRAT-003 — API Contract (accréditation inter-service → Network Policies)
  - ADR-TECH-STRAT-005 — Observabilité (backend OTel plateforme)
