---
id: ADR-BCM-URBA-0007
title: "Normalized Event Meta-Model Guided by Capabilities"
status: Proposed
date: 2026-03-05

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
  - DATA
  - ORG

related_adr:
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0003
  
supersedes: []

tags:
  - event-driven
  - metamodel
  - normalization
  - is-mapping

stability_impact: Structural
---

# ADR-BCM-URBA-0007 — Normalized Event Meta-Model Guided by Capabilities

## Context

The BCM is evolving toward an IS mapping built **by model** rather than by projection (views, cartographies). Projections are based on a set of data produced according to rules. A projection is then only a reading model, a usage to support an intent. What is defined here is the writing model, the rules governing how the data describing the IS is assembled in a normalized manner.
The event assets already exist (`EVT`, `OBJ`, `RES`, `ABO.*`) but the
structural links are not yet explicited as a single reference meta-model.

The target objective is to prepare the future FOODAROO IS mapping and converge toward
an **Event-Driven Enterprise** based on normalized, traceable, and
automatically verifiable concepts.

## Decision

The target meta-model explicits the following relations as guiding rules:

- `Capability -> Business Event` (production)
- `Capability + Business Event -> Capability` (subscription)
- `Business Event -> Business Object` (1 business event carries 1 business object)
- `Business Object <- Resource` (1 resource references 1 business object)
- `Business Event <- Resource Event` (1 resource event references 1 business event)
- `Resource Event -> Resource` (1 resource event references 1 resource)

The term **subscription** reflects a subscription to an event contract. In insurance jargon, the term subscription can be confused with the inherent subscription of an insurance contract, which is why the term subscription will be preferred (using the English "subscription" rather than French "souscription").

The term event also causes confusion. In insurance jargon, it refers to the occurrence of a claim. Unfortunately, there is no equivalent with the same semantic weight that can be used without distorting the subject and causing confusion. One must therefore distinguish between an information system event and an event in the context of a claim declaration. This distinction seems clear and easily acquired among those working on Claims & Benefits.

Expected verifiable criteria (framework level):

- each relation is explicitly representable in the YAML assets;
- each relation is controllable by automatic coherence validation;
- the model remains independent of a drawing tool.

### Templates by entity type

The following templates constitute the reference **writing model** for each entity type:

| Entity type | Expected ID prefix | Reference template |
|---|---|---|
| Capability | `CAP.*` | `templates/capability-template.yaml` |
| Business event | `EVT.*` | `templates/business-event/template-business-event.yaml` |
| Business object | `OBJ.*` | `templates/business-object/template-business-object.yaml` |
| Resource | `RES.*` | `templates/resource/template-resource.yaml` |
| Resource event | `EVT.RES.*` | `templates/resource-event/template-resource-event.yaml` |
| Business subscription | `ABO.METIER.*` | `templates/business-event/template-business-subscription.yaml` |
| Resource subscription | `ABO.RESSOURCE.*` | `templates/resource-event/template-resource-subscription.yaml` |

Usage rule: any new entity introduced in the model must be initialized
from the corresponding template, then validated by the repository control scripts.

## Justification

This decision provides a minimal common base to link capabilities, event
contracts, and materialization of operational data.

It improves:

- the readability of producer/consumer responsibilities;
- end-to-end traceability (capability -> event -> object -> resource);
- the ability to industrialize coherence controls.

### Alternatives Considered

- Option A — Continue without an explicit meta-model: rejected because global
  coherence depends on local interpretations.
- Option B — Map only through diagrams: rejected because poorly industrializable
  for automatic control and continuous governance.

## Advanced Rules Envisioned (not implemented at this stage)

As a perspective (inspirations from advanced practices), the following rules may be studied later:

- advanced versioning governance and event compatibility;
- contract qualification (stability, exposure, criticality, SLA/SLO);
- coupling anti-patterns (fragile chains, circular dependencies, over-subscription);
- domain quality controls (explicit ownership, lifecycle, obsolescence);
- publication/consumption rules tooled via registry.


These rules are **not** imposed by this ADR and must not be implemented
in this phase.

## Impacts on the BCM

### Structure

- Main impact: explicitation of the cross-level conceptual graph.
- No immediate capability split/merge.

### Events (if applicable)

- Clarification of links between business events and resource events.
- Formalization of the place of subscriptions as a capability-consumption relation.

### Mapping SI / Data / Org

- SI: prepares the application mapping by model.
- DATA: prepares the logical chain event -> object -> resource.
- ORG: clarifies producer/consumer responsibilities around capabilities.

## Consequences

### Positive

- Common base for building the FOODAROO IS mapping by model.
- Progressive alignment toward a normalized Event-Driven Enterprise.
- Better auditability of business/operational links.

### Negative / Risks

- Risk of ambiguity if detailed rules are not broken down into dedicated ADRs.
- Risk of documentary overload if the scope remains too broad for too long.

### Accepted Debt

This ADR is intentionally a **framework**. It is intended to be superseded, in several
iterations, by more precise ADRs covering the parts not yet handled,
including (non-exhaustive list):

- application
- topic (Kafka)
- API
- schema
- database/table
- organization
- process
- data-dictionary
- risk register / controls / DORA dependencies
- infrastructure

## Governance Indicators

- Criticality level: High (structuring).
- Recommended review date: 2026-06-30.
- Expected stability indicator: moderate (transitional ADR toward a detailed framework).

## Traceability

- Workshop: BCM event-driven urbanization framing.
- Participants: IS Urbanization, Architecture, Business Domain Leads.
- References: URBA ADRs 0002/0003, ADR README.
