---
id: ADR-TECH-STRAT-003
title: "Stratégie de Contrats API — REST/HTTP, BFF par Canal, Sécurité Bi-Couche"
status: Proposed
date: 2026-04-26

family: TECH
tech_domain: API_CONTRACT

grounded_in_urba:
  - ADR-BCM-URBA-0003   # 1 capacité = 1 responsabilité — pas d'appel direct à la DB d'un L2
  - ADR-BCM-URBA-0005   # contrats d'interface guidés par la BCM (suspendu, intention conservée)
  - ADR-BCM-URBA-0010   # L2 pivot — frontière de contrat

grounded_in_func:
  - ADR-BCM-FUNC-0004   # L1 breakdown — zones CANAL et SERVICES_COEUR
  - ADR-BCM-FUNC-0009   # CAN.001 — Parcours bénéficiaire (surface externe)
  - ADR-BCM-FUNC-0010   # CAN.002 — Portail prescripteur (surface externe)
  - ADR-BCM-FUNC-0007   # BSP.003 — Coordination prescripteurs / gestion des rôles
  - ADR-BCM-FUNC-0012   # SUP.001 — Conformité données (RGPD, droits d'accès)

related_adr:
  - ADR-TECH-STRAT-001  # Event Infrastructure — rail opérationnel RabbitMQ
  - ADR-TECH-STRAT-002  # Runtime — monolithe modulaire par zone

supersedes: []

impacted_zones:
  - SERVICES_COEUR
  - CANAL
  - REFERENTIEL
  - SUPPORT
  - ECHANGE_B2B

tags:
  - api
  - rest
  - bff
  - security
  - openFGA
  - authorization
  - inter-service

stability_impact: Structural
---

# ADR-TECH-STRAT-003 — Stratégie de Contrats API

## Context

Le BCM de Reliever expose deux types de surface API distincts :

1. **Surface interne** : appels synchrones entre L2 de zones différentes, là où RabbitMQ
   (ADR-TECH-STRAT-001) ne suffit pas — typiquement les lectures de référentiel (REF.001)
   ou les queries d'état ponctuelles. Ces échanges sont inter-déployables (ADR-TECH-STRAT-002)
   et restent invisibles des clients externes.

2. **Surface externe** : les zones CANAL (CAN.001 — parcours bénéficiaire, CAN.002 — portail
   prescripteur) exposent des interfaces aux utilisateurs finaux (bénéficiaires, prescripteurs).
   Ces surfaces ont des exigences de sécurité, d'UX et de cycle de vie distinctes du cœur IS.

Le product.md identifie un risque explicite sur la visibilité différenciée des données entre
acteurs hétérogènes (banque, psychiatre, travailleur social). `CAP.BSP.003.ROL` est la capacité
responsable de la gestion des rôles et accréditations prescripteurs. `CAP.SUP.001` gouverne
la conformité RGPD et les droits d'accès. Ces deux L2 imposent un modèle d'autorisation
fin, propagé jusqu'au cœur IS — pas seulement appliqué en façade.

URBA-0005 (contrats guidés par la BCM) est suspendu mais son intention reste valide : les
contrats API doivent suivre les frontières de capacité L2, pas la structure applicative interne.

## Decision

### Appels synchrones inter-L2 (surface interne)

- **Règle 1** : Le protocole de communication synchrone inter-L2 est **REST/HTTP**. Aucun
  appel direct à la base de données d'un autre L2 n'est autorisé (URBA-0003).
- **Règle 2** : Les contrats REST suivent les frontières de capacité L2 — un endpoint est
  publié par un L2, pas par un module interne ou une entité de données. L'URL suit le
  nommage BCM : `/{zone}/{capability-id}/{resource}`.
- **Règle 3** : gRPC ou tout protocole binaire peut être introduit dans un L2 spécifique si
  une contrainte de performance l'exige, documentée dans un ADR-TECH-STRAT dédié. REST/HTTP
  reste le défaut.

### Surface externe — BFF par application CANAL

- **Règle 4** : Chaque application de la zone CANAL dispose de son propre **BFF**
  (Backend For Frontend) : un BFF pour CAN.001 (application mobile bénéficiaire), un BFF
  pour CAN.002 (portail prescripteur web). Aucune application frontend ne communique
  directement avec les déployables de zone BSP, REF ou SUP.
- **Règle 5** : Le BFF est la **frontière de sécurité externe** : il valide les tokens
  utilisateurs entrants, applique le rate limiting et agrège les appels multi-L2 nécessaires
  à la vue frontend. Il traduit les besoins d'expérience (UX-driven) en appels REST vers
  les L2 du cœur IS.
- **Règle 6** : Le BFF est **canal-spécifique** — il évolue au rythme de l'expérience
  utilisateur, indépendamment du rythme du cœur IS. Il ne contient aucune logique métier :
  toute règle métier réside dans les L2 du cœur IS.
- **Règle 7** : La vision produit permet de déclarer de nouveaux BFF/produits API composés
  sur les services cœur, customisés pour un usage dédié — sans modifier le cœur IS.

### Sécurité bi-couche

- **Règle 8 — Inter-service** : Chaque déployable de zone déclare explicitement la liste
  des appelants autorisés à invoquer ses endpoints REST. Un service ne répond pas à un
  appelant non accrédité, quel que soit le token utilisateur porté dans la requête.
  Le mécanisme d'accréditation inter-service (mTLS, OAuth2 client credentials, ou équivalent
  plateforme) est délégué à l'ADR d'implémentation.
- **Règle 9 — Droits utilisateur dans le cœur IS** : L'identité et les accréditations de
  l'utilisateur final sont propagées du BFF jusqu'aux L2 du cœur IS via le token de la
  requête. Les L2 appliquent un contrôle d'accès fin sur les données en fonction de ces droits.
- **Règle 10 — Modèle d'autorisation** : Le contrôle d'accès fin est gouverné par
  **OpenFGA** (implémentation open-source du modèle Zanzibar). OpenFGA modélise les
  relations entre acteurs et ressources : "ce prescripteur a-t-il le droit de voir les
  données de ce bénéficiaire ?", "cette accréditation permet-elle l'action d'override ?".
  `CAP.BSP.003.ROL` est le L2 propriétaire du modèle de relations OpenFGA.
- **Règle 11** : Aucune donnée de bénéficiaire ne traverse une frontière de zone sans que
  le modèle OpenFGA ait validé le droit de l'appelant sur cette relation. `CAP.SUP.001`
  est responsable de l'audit de ces accès (ADR-BCM-FUNC-0012).

## Justification

1. **REST/HTTP par défaut** : minimise le gap cognitif pour une équipe unique en phase
   d'amorçage. L'outillage (Swagger/OpenAPI, clients HTTP standard, debugging réseau) est
   universel. La migration vers gRPC sur un L2 spécifique est toujours possible sous
   contrainte de performance documentée.

2. **BFF par canal** : URBA-0001 distingue la zone CANAL de la zone SERVICES_COEUR. Les
   exigences de sécurité sont structurellement différentes : la zone CANAL est exposée
   à l'internet public, le cœur IS ne l'est jamais directement. Le BFF matérialise cette
   frontière. Il protège également le cœur IS des volatilités UX (changements fréquents
   de l'expérience frontend sans impact sur les L2 métier).

3. **OpenFGA pour l'autorisation fine** : le modèle multi-acteurs de Reliever (banque,
   psychiatre, travailleur social) avec visibilité différenciée par rôle est exactement
   le cas d'usage de Zanzibar. Un RBAC classique (rôles statiques) ne peut pas modéliser
   "le psychiatre voit les données comportementales mais pas les données bancaires de ce
   bénéficiaire spécifique". OpenFGA peut. `CAP.BSP.003.ROL` devient le gestionnaire du
   graphe de relations, pas une table de rôles statiques.

4. **Accréditation inter-service** : le cœur IS ne doit jamais être accessible directement
   depuis l'extérieur — même via un token utilisateur valide. La couche inter-service garantit
   que seuls des appelants connus (BFF accrédités, L2 accrédités) peuvent joindre un
   déployable de zone. C'est un principe de défense en profondeur indépendant du token
   utilisateur.

### Alternatives Considérées

- **GraphQL en façade CANAL** — écarté à l'amorçage : la flexibilité de GraphQL est utile
  quand les clients ont des besoins de projection très variables. Avec deux BFF dédiés
  (bénéficiaire / prescripteur), les projections sont connues et stables. GraphQL peut être
  introduit ultérieurement si la diversité des clients l'exige.

- **RBAC classique (rôles statiques) pour l'autorisation** — rejeté : incapable de modéliser
  les relations contextuelles multi-acteurs de Reliever (visibilité par bénéficiaire, par
  type de prescripteur, par type de donnée). OpenFGA couvre ce cas nativement.

- **Exposition directe du cœur IS sans BFF** — rejeté : fusionne les cycles de vie UX et
  métier, expose le cœur IS à l'internet public, et empêche la différenciation de sécurité
  entre zone CANAL et zone SERVICES_COEUR.

- **BFF unique pour tous les canaux** — rejeté : CAN.001 (mobile bénéficiaire) et CAN.002
  (portail prescripteur) ont des modèles de sécurité, des rythmes d'évolution et des
  agrégations de données fondamentalement différents. Un BFF partagé crée un couplage
  artificiel entre deux expériences qui n'ont pas à évoluer ensemble.

## Technical Impact

### On API Contracts

- Convention d'URL interne : `/{zone-abbrev}/{cap-id}/{resource}` alignée sur le nommage BCM
- Les BFF exposent des APIs orientées expérience (pas de fuite de la structure interne L2)
- OpenAPI / contrat-first est recommandé pour les endpoints inter-L2 internes — à formaliser
  dans l'ADR d'implémentation

### On Service Boundaries

- Les BFF sont des déployables de zone CANAL — structurés comme les autres déployables
  (ADR-TECH-STRAT-002), pas des proxies légers sans frontière
- `CAP.BSP.003.ROL` devient un L2 critique : il détient le modèle OpenFGA et est appelé
  sur chaque requête nécessitant une vérification de relation

### On Data Ownership

- Le token utilisateur propagé dans le cœur IS ne doit pas porter les données de
  l'utilisateur — seulement son identité et ses accréditations. `CAP.REF.001.PRE` est la
  source de vérité des prescripteurs ; `CAP.REF.001.BEN` pour les bénéficiaires.

## Consequences

### Positive

- Cœur IS protégé de l'internet public par deux frontières (inter-service + BFF)
- Autorisation fine adaptée au modèle multi-acteurs sans RBAC statique
- BFF permet l'évolution UX indépendante du rythme de release du cœur IS
- Base pour une offre produit API composable sur les services cœur

### Negative / Risks

- `CAP.BSP.003.ROL` / OpenFGA devient un point de passage critique — sa disponibilité
  conditionne toutes les requêtes autorisées ; son SLA doit être dimensionné en conséquence
- La propagation du token utilisateur jusqu'au cœur IS complexifie le débogage distribué
  (quel layer a refusé la requête ?)

### Accepted Debt

- Le mécanisme exact d'accréditation inter-service (mTLS vs. OAuth2 client credentials vs.
  solution plateforme) est délégué à l'ADR d'implémentation — à décider avec l'équipe
  plateforme
- La stratégie de versioning des APIs REST inter-L2 (URL versioning vs. header versioning)
  n'est pas décidée ici — à formaliser lors de la première API inter-L2 mise en production

## Governance Indicators

- Review trigger : introduction d'un troisième type de client CANAL (ex. API partenaire B2B) ;
  ou montée en charge d'OpenFGA impactant la latence des requêtes autorisées
- Expected stability : 2 ans — la topologie BFF est stable ; OpenFGA peut évoluer en modèle
  de relations sans changer l'ADR stratégique

## Traceability

- Session : Technical brainstorming 2026-04-26
- Participants : yremy
- References :
  - ADR-BCM-URBA-0003 — 1 capacité = 1 responsabilité
  - ADR-BCM-URBA-0005 — Contrats guidés par BCM (suspendu)
  - ADR-BCM-FUNC-0007 — BSP.003 Coordination prescripteurs / rôles
  - ADR-BCM-FUNC-0009 — CAN.001 Parcours bénéficiaire
  - ADR-BCM-FUNC-0010 — CAN.002 Portail prescripteur
  - ADR-BCM-FUNC-0012 — SUP.001 Conformité données
  - ADR-TECH-STRAT-001 — Infrastructure événementielle
  - ADR-TECH-STRAT-002 — Runtime microservice
  - OpenFGA — https://openfga.dev (implémentation Zanzibar)
