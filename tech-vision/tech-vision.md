# Technical Vision — Reliever IS

## Service Offer (anchored on)

> **Reliever** enables financially vulnerable individuals to progressively regain control of their daily financial lives through a system of increasing autonomy tiers, anchored on a dedicated card and a behavioral score coordinated between prescribers via open banking, even when preserving their dignity is as important as constraining their behaviors.

## Technical Intent

Delivering this offer requires an IS that can react to every purchase event in real time while maintaining a continuous, asynchronous behavioral assessment loop across 20+ L2 microservices. The two non-negotiable technical properties are: **event-driven decoupling** between L2 capabilities (no shared mutable state, no direct inter-L2 calls) and **analytical autonomy** (the data layer must be self-sufficient and never block on operational sources).

## Technology Stack Summary

| Domain | Decision | Grounded in |
|--------|----------|-------------|
| **Event Infrastructure** | Dual-rail : RabbitMQ (opérationnel, domain events DDD) + Kafka (analytique, ECST / Data Mesh) | URBA-0007/0008/0009/0010 |
| **Microservice Runtime** | Monolithe modulaire par zone TOGAF — 7 déployables à l'amorçage ; L2 = frontière de module ; extraction sous critère explicite | URBA-0002/0003/0010/0011 |
| **API Contract Strategy** | REST/HTTP inter-L2 ; BFF par application CANAL ; sécurité bi-couche inter-service + OpenFGA pour droits utilisateur | URBA-0003/0005/0010 |
| **Data & Referential Layer** | 1 base dédiée par L2 ; double accès REF (REST cold + RabbitMQ hot) ; cache toujours purgeable ; mapping seul autorisé hors propriété ; provenance obligatoire sur toute publication ; PII à la charge du L2 stockeur (droit à l'oubli, anonymisation) | URBA-0003/0012/0013 |
| **Observability & Governance** | OpenTelemetry J0 ; trace ID sur tous les canaux (HTTP + RabbitMQ + Kafka) ; SLOs par L2 (capability_id dimension primaire) ; EventCatalog gouvernance design-time | GOV-0003 / URBA-0010 |
| **Hosting & Deployment** | Docker + Kubernetes (plateforme dédiée) ; 4 environnements (dev/staging/prod/demo) ; GitOps J0 ; 1 namespace Kubernetes par zone TOGAF | URBA-0001/0003 |

## Key Technical Tensions

- **Latence TPE vs. cohérence événementielle** : l'autorisation de transaction (BSP.004.AUT) est synchrone et hors du broker ; les effets de bord (score, enveloppe, signal) transitent via RabbitMQ après la décision — le broker n'est jamais sur le chemin critique.
- **Légèreté opérationnelle vs. complétude analytique** : le rail opérationnel porte des domain events DDD (transition d'agrégat, payload minimal) ; le rail analytique porte des ECST (état complet). Deux rails distincts, deux contrats distincts.
- **Gouvernance schéma design-time vs. runtime** : les contrats d'événements sont gouvernés par les artefacts YAML BCM, sans registry runtime. Acceptable en phase initiale ; à réévaluer si la réglementation ou le volume l'impose.

## Decisions Not Yet Made

Tous les 6 domaines ont été couverts en session initiale. Les décisions d'implémentation
restantes (choix de l'opérateur GitOps, format de manifestes, backend OTel, technologie
de base de données par L2, mécanisme d'accréditation inter-service) sont déléguées aux
ADRs d'implémentation produits lors des sessions suivantes.

## ADR Index

| ADR | Domaine | Statut |
|-----|---------|--------|
| [ADR-TECH-STRAT-001](adr/ADR-TECH-STRAT-001-event-infrastructure.md) | EVENT_INFRASTRUCTURE | Proposed |
| [ADR-TECH-STRAT-002](adr/ADR-TECH-STRAT-002-microservice-runtime.md) | RUNTIME | Proposed |
| [ADR-TECH-STRAT-003](adr/ADR-TECH-STRAT-003-api-contract-strategy.md) | API_CONTRACT | Proposed |
| [ADR-TECH-STRAT-004](adr/ADR-TECH-STRAT-004-data-referential-layer.md) | DATA_PERSISTENCE | Proposed |
| [ADR-TECH-STRAT-005](adr/ADR-TECH-STRAT-005-observability-governance.md) | OBSERVABILITY | Proposed |
| [ADR-TECH-STRAT-006](adr/ADR-TECH-STRAT-006-hosting-deployment.md) | DEPLOYMENT | Proposed |

## Traceability

- Session : Technical brainstorming 2026-04-26
- Participants : yremy
- Anchored on : `product-vision/product.md`, URBA ADRs (0001–0013), FUNC ADRs (0004–0015)
- Session complète : 6 domaines couverts, 6 ADRs produits (ADR-TECH-STRAT-001 à 006)
