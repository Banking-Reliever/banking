---
id: ADR-TECH-STRAT-004
title: "Couche Données et Référentiel — Isolation par L2, Double Accès Référentiel, Gouvernance PII"
status: Proposed
date: 2026-04-26

family: TECH
tech_domain: DATA_PERSISTENCE

grounded_in_urba:
  - ADR-BCM-URBA-0003   # 1 capacité = 1 responsabilité — pas de base partagée
  - ADR-BCM-URBA-0010   # L2 pivot — frontière de données
  - ADR-BCM-URBA-0012   # concept métier canonique (CPT) — propriété du REFERENTIEL
  - ADR-BCM-URBA-0013   # processus externes à la BCM — état de processus hors modèle L2

grounded_in_func:
  - ADR-BCM-FUNC-0013   # REF.001 — Référentiels communs (bénéficiaire, prescripteur, palier)
  - ADR-BCM-FUNC-0012   # SUP.001 — Conformité données, RGPD, droit à l'oubli
  - ADR-BCM-FUNC-0005   # BSP.001 — scoring comportemental (fort volume, données PII potentielles)
  - ADR-BCM-FUNC-0014   # DAT.001 — Analytique comportementale (consommateur de données)

related_adr:
  - ADR-TECH-STRAT-001  # Event Infrastructure — RabbitMQ hot path, Kafka data products
  - ADR-TECH-STRAT-002  # Runtime — monolithe modulaire par zone
  - ADR-TECH-STRAT-003  # API Contract — REST cold path, provenance dans les publications

supersedes: []

impacted_zones:
  - SERVICES_COEUR
  - REFERENTIEL
  - SUPPORT
  - DATA_ANALYTIQUE
  - CANAL
  - ECHANGE_B2B
  - PILOTAGE

tags:
  - data-ownership
  - referentiel
  - cache
  - pii
  - rgpd
  - droit-a-loubli
  - mapping
  - provenance

stability_impact: Structural
---

# ADR-TECH-STRAT-004 — Couche Données et Référentiel

## Context

Le BCM de Reliever introduit deux catégories de données fondamentalement distinctes :

1. **Données opérationnelles** : produites et possédées par chaque L2 dans le cadre de sa
   responsabilité propre (score comportemental pour BSP.001.SCO, palier actif pour BSP.001.PAL,
   transaction autorisée pour BSP.004.AUT). Ces données ne sont accessibles qu'au L2 qui les
   possède.

2. **Données référentielles** : les concepts métier canoniques (CPT) au sens d'URBA-0012 —
   bénéficiaire, prescripteur, palier de définition. Ils vivent dans `CAP.REF.001` (zone
   REFERENTIEL) et constituent la source de vérité partagée. Aucun autre L2 n'en est
   propriétaire.

Le monolithe modulaire par zone (ADR-TECH-STRAT-002) regroupe plusieurs L2 dans un même
déployable, ce qui pourrait inciter à partager une base de données entre L2 colocalisés.
URBA-0003 interdit ce partage : chaque L2 doit être extractible sans migration de données.

Par ailleurs, la nature multi-acteurs de Reliever (banque, psychiatre, travailleur social)
et la sensibilité des données comportementales imposent des règles strictes sur l'ownership,
la provenance et la conformité RGPD de toute donnée publiée ou stockée.

## Decision

### Isolation des données par L2

- **Règle 1** : Chaque L2 dispose d'une **base de données dédiée**, physiquement distincte
  de celles des autres L2 — y compris ceux colocalisés dans le même déployable de zone.
  Aucun accès direct à la base d'un autre L2 n'est autorisé, quelle que soit la colocation.
- **Règle 2** : Un L2 ne stocke que :
  - Les **données dont il est propriétaire** (produites par sa propre logique métier)
  - Les **mappings** vers des données d'autres L2 (clés de liaison uniquement — jamais les
    attributs du L2 référencé)
  - Les **caches locaux** de données référentielles, sous les contraintes définies ci-dessous

### Double accès au référentiel (cold + hot)

- **Règle 3 — Cold path (REST)** : `CAP.REF.001` expose un endpoint REST permettant à tout
  L2 consommateur d'obtenir l'état complet d'un concept référentiel à un instant T.
  Ce chemin est utilisé pour l'hydratation initiale du cache local et pour sa reconstruction
  complète après purge.
- **Règle 4 — Hot path (RabbitMQ)** : `CAP.REF.001` publie ses changements sur son exchange
  RabbitMQ dédié (ADR-TECH-STRAT-001). Un L2 consommateur peut s'abonner aux changements
  uniquement pour maintenir son cache local à jour de manière incrémentale et légère.
- **Règle 5 — Cache purgeable** : tout entrepôt local de données référentielles est un
  **cache et uniquement un cache**. Il doit pouvoir être purgé et intégralement reconstruit
  depuis `CAP.REF.001` à tout instant, sans perte d'information et sans dépendance à l'état
  historique du cache. Un L2 ne peut jamais considérer son cache local comme source de vérité.

### Séparation donnée référentielle / mapping

- **Règle 6** : La **donnée référentielle** (attributs du bénéficiaire, du prescripteur, du
  palier de définition) reste la propriété exclusive de `CAP.REF.001`. Aucun autre L2 ne
  stocke ces attributs dans sa base propre — même temporairement.
- **Règle 7** : Le **mapping** est la seule duplication autorisée : un L2 peut stocker la
  clé d'un concept référentiel (ex. `beneficiary_id`) pour exprimer une relation, mais
  jamais les attributs associés à cette clé (nom, adresse, données démographiques).
- **Règle 8** : Toute **vue agrégée** publiée par un L2 (via REST, RabbitMQ ou Kafka) qui
  inclut des attributs d'un concept référentiel doit **indiquer explicitement la provenance**
  de ces attributs. Le L2 émetteur n'en revendique pas l'ownership. Le format de provenance
  est : `"source": "CAP.REF.001.BEN"` dans le payload ou les headers du message.

### Gouvernance des publications (tous canaux)

- **Règle 9** : Toute information publiée par un L2 — quel que soit le canal (RabbitMQ,
  Kafka, REST) — obéit à la règle d'ownership : si l'information n'est pas sous la
  responsabilité du L2 émetteur, sa provenance est déclarée explicitement.
- **Règle 10** : Un L2 ne publie jamais des données d'un autre L2 sans provenance déclarée.
  La publication silencieuse de données étrangères est une violation de gouvernance.

### Conformité PII

- **Règle 11** : Tout L2 qui stocke localement des **données à caractère personnel (PII)**
  — y compris dans un cache référentiel ou un data product Kafka — devient responsable de :
  - L'implémentation d'un mécanisme de **droit à l'oubli** (RGPD Art. 17) sur cette copie
  - L'application des règles d'**anonymisation ou de pseudonymisation** conformes lors du
    stockage
- **Règle 12** : `CAP.SUP.001` (zone SUPPORT) définit les règles de conformité PII
  applicables à l'ensemble de l'IS et audite leur application. Chaque L2 exécute ces règles
  sous sa propre responsabilité — `CAP.SUP.001` gouverne mais ne substitue pas.
- **Règle 13** : Les **data products Kafka** (ADR-TECH-STRAT-001) qui contiennent des PII
  doivent implémenter un mécanisme de crypto-shredding ou d'effacement sur le topic Kafka
  lors d'un exercice du droit à l'oubli.

## Justification

1. **Base dédiée par L2** : l'isolation physique des bases est la seule garantie que
   l'extraction future d'un L2 (ADR-TECH-STRAT-002, critères de découpage) est une opération
   de déploiement et non une migration de données. Une base partagée entre L2 colocalisés
   crée un couplage de schéma invisible qui rend l'extraction coûteuse.

2. **Double porte référentielle** : le cold path (REST) garantit la reconstructibilité
   du cache — un L2 peut toujours repartir d'un état propre. Le hot path (RabbitMQ) évite
   le polling et maintient la fraîcheur du cache à coût minimal. Les deux chemins sont
   complémentaires et nécessaires : l'un seul ne suffit pas.

3. **Séparation donnée / mapping** : stocker les attributs référentiels dans un L2 tiers
   crée une dépendance de données qui viole URBA-0003 et URBA-0012. Si REF.001 modifie
   un attribut, tous les L2s qui l'auraient dupliqué deviennent incohérents. Le mapping
   (clé seulement) est stable et ne nécessite pas de synchronisation.

4. **Règle de provenance** : la zone CANAL (BFF, ADR-TECH-STRAT-003) est susceptible de
   produire des vues agrégées combinant données BSP et données REF. Sans règle de provenance,
   le consommateur (frontend, analytique) ne peut pas distinguer ce que le L2 possède de
   ce qu'il relaie — rendant la gouvernance des données impossible.

5. **PII à la charge du L2 stockeur** : la RGPD impose l'obligation au niveau du contrôleur
   de données effectif — le L2 qui stocke. Déléguer la conformité PII uniquement à SUP.001
   serait insuffisant juridiquement : chaque entrepôt de données PII, même un cache, est
   un traitement au sens RGPD.

### Alternatives Considérées

- **Schéma partagé par zone dans un cluster commun** — rejeté : couplage de schéma entre
  L2, extraction future complexifiée, risque de requêtes cross-L2 via jointures SQL directes
  contournant les frontières de responsabilité.

- **Accès référentiel uniquement synchrone (REST seul)** — rejeté : polling systématique
  ou appel à chaque requête sur REF.001 crée une dépendance de disponibilité forte entre
  le cœur IS et le référentiel. Le hot path RabbitMQ découple les cycles de vie.

- **Accès référentiel uniquement événementiel (RabbitMQ seul)** — rejeté : sans cold path,
  la reconstruction complète du cache après purge nécessiterait de rejouer l'intégralité
  de l'historique d'événements REF — ce qui impose une rétention infinie sur l'exchange,
  incompatible avec la légèreté opérationnelle de RabbitMQ.

- **Conformité PII centralisée dans SUP.001 uniquement** — rejeté : SUP.001 ne peut pas
  exécuter le droit à l'oubli sur les bases des autres L2 sans violer leur isolation
  (Règle 1). La gouvernance est centrale, l'exécution est locale.

## Technical Impact

### On Data Ownership

- REF.001 devient un L2 critique à haute disponibilité : son cold path est sollicité à
  chaque reconstruction de cache et son hot path alimente en continu tous les L2 consommateurs
- `CAP.BSP.003.ROL` stocke les mappings prescripteur ↔ bénéficiaire (relations OpenFGA),
  pas les attributs prescripteur (propriété de REF.001.PRE)

### On Event Infrastructure

- L'exchange RabbitMQ de REF.001 est un exchange de référentiel — ses événements suivent
  la même convention de routing key `{BusinessEventName}.{ResourceEventName}` mais sont
  de nature référentielle (changement de définition, pas de transaction métier)
- Les data products Kafka (DAT.001) qui contiennent des PII doivent implémenter le
  crypto-shredding — le L2 producteur gère les clés de chiffrement par sujet de données

### On API Contracts

- La provenance dans les vues agrégées (Règle 8) s'applique aux réponses REST des BFF
  (ADR-TECH-STRAT-003) : tout champ issu d'un L2 tiers est tagué de sa source

## Consequences

### Positive

- Extraction future de tout L2 sans migration de données (bases isolées)
- REF.001 reste la seule source de vérité — pas de risque de divergence entre L2
- Conformité RGPD structurellement intégrée — pas ajoutée en fin de projet
- Traçabilité de provenance sur toutes les publications — gouvernance des données auditable

### Negative / Risks

- N bases de données à provisionner (une par L2) — charge de plateforme élevée, assumée
  par l'équipe plateforme dédiée
- Le crypto-shredding sur Kafka est une complexité d'implémentation non négligeable pour
  les L2 producteurs de data products contenant des PII
- REF.001 est un point de disponibilité critique pour tous les L2 qui dépendent de son
  cold path pour la reconstruction de cache

### Accepted Debt

- La technologie de base de données par L2 (relationnelle, document, time-series, event
  store) n'est pas décidée ici — chaque L2 choisit la technologie adaptée à son modèle
  de données dans son ADR d'implémentation, sous contrainte d'isolation physique
- Le format exact de déclaration de provenance dans les payloads (champ, header, enveloppe)
  est à standardiser dans un ADR d'implémentation transverse

## Governance Indicators

- Review trigger : exercice de droit à l'oubli révélant qu'un L2 a stocké des attributs
  référentiels (violation Règle 6) ; ou latence REF.001 cold path impactant les temps
  de démarrage des L2
- Expected stability : 3 ans — les principes d'ownership et de conformité sont stables ;
  les mécanismes d'implémentation (crypto-shredding, format provenance) peuvent évoluer

## Traceability

- Session : Technical brainstorming 2026-04-26
- Participants : yremy
- References :
  - ADR-BCM-URBA-0003 — 1 capacité = 1 responsabilité
  - ADR-BCM-URBA-0012 — Concept métier canonique (CPT)
  - ADR-BCM-FUNC-0013 — REF.001 Référentiels communs
  - ADR-BCM-FUNC-0012 — SUP.001 Conformité données
  - ADR-TECH-STRAT-001 — Infrastructure événementielle (hot path RabbitMQ, Kafka PII)
  - ADR-TECH-STRAT-002 — Runtime microservice (isolation par zone)
  - ADR-TECH-STRAT-003 — Stratégie API (provenance dans les publications)
  - RGPD Art. 17 — Droit à l'effacement
