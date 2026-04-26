---
id: ADR-TECH-STRAT-001
title: "Dual-Rail Event Infrastructure — Operational (RabbitMQ) and Analytical (Kafka / Data Mesh)"
status: Proposed
date: 2026-04-26

family: TECH
tech_domain: EVENT_INFRASTRUCTURE

grounded_in_urba:
  - ADR-BCM-URBA-0007   # normalized event meta-model (business event → resource event)
  - ADR-BCM-URBA-0008   # two-level event modeling
  - ADR-BCM-URBA-0009   # capability owns its event production
  - ADR-BCM-URBA-0010   # L2 as urbanization pivot

grounded_in_func:
  - ADR-BCM-FUNC-0004   # L1 breakdown — all zones
  - ADR-BCM-FUNC-0005   # BSP.001 — Behavioral Remediation (high event frequency)
  - ADR-BCM-FUNC-0008   # BSP.004 — Transaction Control (operational critical path)
  - ADR-BCM-FUNC-0014   # DAT.001 — Behavioral Analytics (analytical consumer)

related_adr: []
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
  - event-infrastructure
  - rabbitmq
  - kafka
  - domain-events
  - ecst
  - data-mesh
  - dual-rail

stability_impact: Structural
---

# ADR-TECH-STRAT-001 — Dual-Rail Event Infrastructure

## Context

Le BCM de Reliever définit un méta-modèle événementiel à deux niveaux (ADR-BCM-URBA-0007/0008) :
- **Business events** : faits métier abstraits nommés en langage domaine
- **Resource events** : projection opérationnelle typée, portant l'état d'une ressource

Chaque L2 est propriétaire de sa production événementielle (URBA-0009). Le pivot d'urbanisation
est le L2 (URBA-0010) : c'est à ce niveau que les contrats d'événements sont définis et honorés.

Deux besoins distincts émergent de l'analyse des FUNC ADRs :

1. **Communication inter-L2 opérationnelle** : réactivité, couplage faible, transitions d'état
   DDD. Le L2 `CAP.BSP.004.AUT` (autorisation de transaction) exige une réponse synchrone au
   TPE, mais tous les effets de bord (score, enveloppe, signal) transitent de manière asynchrone.
   Le broker n'est pas sur le chemin critique de l'autorisation.

2. **Alimentation analytique** : le L2 `CAP.DAT.001` (Behavioral Analytics) et les futurs
   consommateurs analytiques ont besoin d'un état complet auto-suffisant, sans requête vers
   les sources opérationnelles — pour garantir leur indépendance de déploiement et de montée
   en charge.

Ces deux besoins ont des propriétés contradictoires (légèreté vs. complétude, réactivité vs.
débit analytique) et justifient deux rails distincts.

La plateforme est gérée par une équipe dédiée indépendante de ce projet. RabbitMQ et Kafka
sont des ressources de plateforme — non possédées par les applicatifs L2.

## Decision

### Rail opérationnel — RabbitMQ

- **Règle 1** : Chaque L2 possède exactement un topic exchange RabbitMQ qui lui est propre.
  Cet exchange est le seul point de publication des resource events que ce L2 émet.
- **Règle 2** : Seuls les **resource events** (niveau RES du méta-modèle) donnent lieu à des
  messages sur RabbitMQ. Les business events ne produisent pas de messages autonomes.
- **Règle 3** : Le format des messages est le **domain event DDD** — payload de transition
  d'agrégat cohérente et atomique : toutes les données qui font sens pour cette transition
  d'état, et uniquement celles-là. Ni snapshot complet, ni patch technique de champs.
- **Règle 4** : La routing key suit la convention `{BusinessEventName}.{ResourceEventName}`.
  Un consommateur peut s'abonner à `{BusinessEventName}.#` pour agréger tous les resource
  events rattachés au même fait métier, ou à `{BusinessEventName}.{ResourceEventName}` pour
  un type précis.
- **Règle 5** : La souscription s'effectue par création d'une queue par le L2 consommateur
  sur l'exchange du L2 émetteur. Aucun L2 ne peut publier sur l'exchange d'un autre L2.
- **Règle 6** : La gouvernance de schéma est design-time : les artefacts YAML BCM
  (`business-event-*.yaml`, `resource-event-*.yaml`, `resource-subscription-*.yaml`)
  constituent la source de vérité des contrats. Il n'existe pas de registry de schéma runtime.

### Rail analytique — Kafka / Data Mesh

- **Règle 7** : Chaque L2 peut posséder un ou plusieurs **data products**, chacun publié sur
  un topic Kafka dédié. Un L2 peut être propriétaire de plusieurs topics.
- **Règle 8** : Le format des messages analytiques est **ECST** (Event-Carried State Transfer)
  — l'événement porte l'état complet de la ressource au moment de la transition, rendant le
  consommateur autonome vis-à-vis de la source opérationnelle.
- **Règle 9** : La conception des data products suit les principes du *Event-Driven Data Mesh*
  (référence : *Building an Event-Driven Data Mesh*, O'Reilly). Chaque L2 est domain owner
  de ses data products.
- **Règle 10** : Le rail analytique est consommé par `CAP.DAT.001` et tout futur composant
  analytique. Il ne doit jamais être utilisé pour de la communication opérationnelle inter-L2.

## Justification

Le découplage opérationnel/analytique est motivé par trois contraintes :

1. **URBA-0009 + domaine cœur** : `CAP.BSP.001` (scoring comportemental) génère un événement
   à chaque transaction autorisée. Le volume opérationnel est élevé mais les payloads sont
   légers (delta de transition). Les consommateurs analytiques ont besoin d'un état reconstituable
   sans interroger `BSP.001` — ce qui imposerait un couplage fort incompatible avec URBA-0003.

2. **DDD domain events pour l'opérationnel** : le méta-modèle BCM (URBA-0007/0008) distingue
   fait métier (business event) et projection technique (resource event). Le domain event DDD
   est la traduction naturelle de cette distinction : il porte la sémantique de la transition,
   pas un diff technique. Le business event devient le préfixe de routing key — visible dans
   RabbitMQ sans nécessiter de registry runtime.

3. **Data Mesh pour l'analytique** : `CAP.DAT.001` doit pouvoir reconstruire des modèles
   comportementaux sans dépendre de la disponibilité des L2 opérationnels. L'ECST garantit
   cette autonomie. Le pattern Data Mesh aligne le ownership des data products sur le ownership
   des capacités L2 — cohérent avec URBA-0010.

### Alternatives Considérées

- **Rail unique (broker unique pour opérationnel et analytique)** — rejeté : les exigences
  sont contradictoires. Un broker optimisé pour l'analytique (rétention longue, replay massif)
  est surdimensionné pour l'opérationnel ; un broker léger opérationnel ne suffit pas pour
  les consumers analytiques qui ont besoin d'état complet et de replay long terme.

- **ECST sur le rail opérationnel** — rejeté : le payload état-complet alourdit tous les
  messages opérationnels, même ceux dont les consommateurs n'ont besoin que de la transition.
  Contraire à l'esprit DDD (un event porte la sémantique de *ce qui s'est passé*, pas l'état
  global de l'agrégat).

- **Kafka pour les deux rails** — rejeté à ce stade : Kafka est adapté à l'analytique et au
  débit élevé, mais son modèle de consommation (consumer groups, offsets) est moins naturel
  que les queues RabbitMQ pour la communication inter-L2 opérationnelle orientée DDD. Le
  choix RabbitMQ reste ouvert à révision si le volume transactionnel dépasse les capacités
  opérationnelles constatées.

- **Architecture sans broker (appels synchrones directs)** — rejeté : viole URBA-0003
  (couplage direct entre L2) et URBA-0009 (chaque L2 doit pouvoir émettre des événements
  consommables par d'autres sans accord bilatéral).

## Technical Impact

### On Event Infrastructure

- Deux ressources de plateforme distinctes à provisionner : RabbitMQ (opérationnel) + Kafka
  (analytique)
- Chaque L2 applicatif doit être configuré avec les credentials de son exchange RabbitMQ
  et, s'il produit des data products, avec les credentials de ses topics Kafka
- La convention de routing key `{BusinessEventName}.{ResourceEventName}` doit être documentée
  et respectée par tous les L2 — c'est un contrat de plateforme

### On Service Boundaries

- Le L2 `CAP.BSP.004.AUT` (autorisation transaction) traite la décision d'autorisation en
  synchrone ; le domain event `Transaction.Autorisée` / `Transaction.Refusée` est publié
  sur RabbitMQ après la décision, hors du chemin critique de latence TPE

### On Data Ownership

- `CAP.DAT.001` consomme exclusivement le rail Kafka — il ne subscrit jamais à RabbitMQ
- Les L2 producteurs de data products sont responsables du format ECST de leurs topics

## Consequences

### Positive

- Couplage faible entre L2 opérationnels (URBA-0003 respecté)
- Autonomie complète des consommateurs analytiques — pas de requête vers les sources
- Routing key lisible en langage métier dans RabbitMQ — opérabilité sans outil externe
- Ownership des data products aligné sur l'ownership des capacités L2 (URBA-0010)

### Negative / Risks

- Deux brokers à opérer : complexité de plateforme accrue — assumée par l'équipe plateforme
- La convention de routing key est un contrat informel (pas de registry runtime) : risque de
  dérive si les L2 ne respectent pas la convention — mitigé par la validation design-time BCM
- Le volume Kafka (ECST = payload complet) peut être élevé pour les L2 à fort débit
  transactionnel (BSP.004)

### Accepted Debt

- Pas de schema registry runtime : la cohérence des contrats repose sur les artefacts YAML BCM
  et la discipline des équipes L2. Un registry runtime (Confluent Schema Registry ou équivalent)
  pourra être ajouté à la plateforme si la gouvernance design-time s'avère insuffisante.

## Governance Indicators

- Review trigger : volume transactionnel RabbitMQ dépassant la capacité opérationnelle constatée
  en production ; ou besoin de registry runtime imposé par une exigence réglementaire
- Expected stability : 3 ans — sauf évolution majeure de la stratégie plateforme ou changement
  du modèle d'événements BCM (modification URBA-0007/0008)

## Traceability

- Session : Technical brainstorming 2026-04-26
- Participants : yremy
- References :
  - ADR-BCM-URBA-0007 — Méta-modèle événementiel normalisé
  - ADR-BCM-URBA-0008 — Modélisation événements deux niveaux
  - ADR-BCM-URBA-0009 — Définition capacité événementielle
  - ADR-BCM-URBA-0010 — L2 pivot d'urbanisation
  - *Building an Event-Driven Data Mesh*, O'Reilly
