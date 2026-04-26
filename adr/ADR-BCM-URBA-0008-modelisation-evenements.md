---
id: ADR-BCM-URBA-0008
title: "Event Modeling — Two-Level Guide"
status: Proposed
date: 2026-03-09

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
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0003
  - ADR-BCM-URBA-0004
  - ADR-BCM-URBA-0007
  - ADR-BCM-FUNC-0003
supersedes: []

tags:
  - event-driven
  - business-object
  - business-event
  - resource
  - modeling
  - guide
  - polymorphism
  - abstraction

stability_impact: Structural
---

# ADR-BCM-URBA-0008 — Event Modeling — Two-Level Guide

## Context

The BCM meta-model (ADR-BCM-URBA-0007) introduces an event-driven architecture
structured in **two levels of abstraction**:

| Level | Objects | Events | Subscriptions |
|--------|--------|------------|---------------|
| **Business** | Business object | Business event | Business subscription |
| **Operational** | Resource | Resource event | Resource subscription |

This structure addresses a recurring need: modeling structurally heterogeneous business
variants for the same lifecycle milestone, while preserving a stable abstraction for
transverse consumers.

**Concrete example:**
- Lifecycle milestone: *Claim declared*
- Business variants: *Water damage*, *Theft*, *Fire* — each with specific
  properties.

This ADR formalizes the modeling rules at each level and their relations.

## Decision

### Overview: Two-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BUSINESS LEVEL (abstraction)                         │
│                                                                             │
│   ┌─────────────────────┐         ┌─────────────────────┐                   │
│   │   Business Object   │◄────────│   Business Event    │                   │
│   │  (common            │ carried │  (lifecycle         │                   │
│   │   properties)       │         │   milestone)        │                   │
│   └─────────────────────┘         └─────────────────────┘                   │
│             ▲                               ▲                               │
│             │ business_object               │ business_event               │
│             │                               │                               │
├─────────────┼───────────────────────────────┼───────────────────────────────┤
│             │                               │                               │
│             │   RESOURCE LEVEL (implementation)                             │
│             │                               │                               │
│   ┌─────────┴───────────┐         ┌─────────┴───────────┐                   │
│   │      Resource       │◄────────│   Resource Event    │                   │
│   │  (specialized       │ carried │  (published         │                   │
│   │   properties)       │         │   specialized fact) │                   │
│   └─────────────────────┘         └─────────────────────┘                   │
│                                                                             │
│   Resource.data[].business_object_property → Business Object.data[].name    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Level 1: Business Modeling

### 1.1 Business Object — The Common Property Base

The **business object** defines the **abstract and stable properties** shared by
all variants of the same concept.

**Modeling rules:**

| Rule | Description |
|-------|-------------|
| **Abstraction** | Contains only the properties common to all variants |
| **Stability** | Properties are designed to remain stable over time |
| **Independence** | Does not depend on technical implementation details |
| **Reference direction** | Does not reference a business event; the relation is carried only by `EVT.carried_business_object` |
| **Completeness** | Each property must be referenced by at least one resource |

**Example — Business object `OBJ.COEUR.005.DECLARATION_SINISTRE`:**

```yaml
data:
  - name: claimDeclarationId       # Common to all variants
  - name: occurrenceDate           # Common to all variants
  - name: contractId               # Common to all variants
  - name: declarationChannel       # Common to all variants
  - name: coverageVerificationStatus # Common to all variants
```

**To avoid:**
- Properties specific to a single variant (e.g., `leakOrigin` for water damage)
- Technical or implementation properties
- Polymorphic properties requiring decoding

### 1.2 Business Event — The Lifecycle Milestone

The **business event** represents an **abstract lifecycle milestone** of a
business aggregate. It carries a business object.

**Modeling rules:**

| Rule | Description |
|-------|-------------|
| **Milestone uniqueness** | Only one business event per lifecycle milestone |
| **Abstraction** | Describes the *what* (the business fact), not the *how* (the implementation) |
| **Business object carrier** | Mandatorily references a business object via `carried_business_object` |
| **No direct publication** | Is not published as-is; serves as an abstraction point |

**Example — Business event `EVT.COEUR.005.SINISTRE_DECLARE`:**

```yaml
id: EVT.COEUR.005.SINISTRE_DECLARE
name: Claim declared
carried_business_object: OBJ.COEUR.005.DECLARATION_SINISTRE
emitting_capability: CAP.COEUR.005.DSP
```

### 1.3 Business Subscription — Transverse Consumption

A **business subscription** allows a consumer to subscribe to a **business
event**, thus receiving **all resource events** that implement it.

**Modeling rules:**

| Rule | Description |
|-------|-------------|
| **Abstract target** | References a business event, not a resource event |
| **Automatic resolution** | Is resolved toward all linked resource events |
| **Common properties** | The consumer can only read the business object properties |

**Use cases:**
- Generalist consumer (e.g., reporting, audit, data lake)
- Consumer that does not need the specialized details

---

## Level 2: Resource Modeling

### 2.1 Resource — The Specialized Implementation

The **resource** implements a business object with **specialized properties**
specific to a variant.

**Modeling rules:**

| Rule | Description |
|-------|-------------|
| **Specialization** | Contains properties specific to the variant |
| **Mandatory reference** | References the business object via `business_object` |
| **Property traceability** | Each common property references its source via `business_object_property` |
| **Autonomy** | Must be understandable alone, without joins with other resources |

**Example — Resource `RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_DEGAT_EAUX`:**

```yaml
id: RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_DEGAT_EAUX
business_object: OBJ.COEUR.005.DECLARATION_SINISTRE

data:
  # Common properties (reference the business object)
  - name: claimDeclarationId
    business_object_property: claimDeclarationId
  - name: occurrenceDate
    business_object_property: occurrenceDate
  - name: contractId
    business_object_property: contractId

  # Specialized properties (specific to this variant)
  - name: leakOrigin           # Specific to water damage
  - name: impactedArea         # Specific to water damage
  - name: affectedThirdParties # Specific to water damage
```

### 2.2 Resource Event — The Published Fact

The **resource event** is the **fact actually published** on the bus. It carries
a resource and implements a business event.

**Modeling rules:**

| Rule | Description |
|-------|-------------|
| **Effective publication** | This is the event actually published and consumed |
| **Specialized** | One type of resource event per business variant |
| **Double reference** | References a resource (`carried_resource`) and a unique business event (`business_event`) |
| **Autonomy** | Understandable without polymorphic decoding or join |

**Example — Resource event `EVT.RES.COEUR.005.SINISTRE_HABITATION_DEGAT_EAUX_DECLARE`:**

```yaml
id: EVT.RES.COEUR.005.SINISTRE_HABITATION_DEGAT_EAUX_DECLARE
name: Residential water damage claim declared
carried_resource: RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_DEGAT_EAUX
business_event: EVT.COEUR.005.SINISTRE_DECLARE
emitting_capability: CAP.COEUR.005.DSP
```

### 2.3 Resource Subscription — Specialized Consumption

A **resource subscription** allows a consumer to subscribe to a
**specific resource event**.

**Modeling rules:**

| Rule | Description |
|-------|-------------|
| **Precise target** | References a specific resource event |
| **Business link** | References the associated business subscription via `linked_business_subscription` |
| **Complete properties** | The consumer accesses all properties (common + specialized) |

**Use cases:**
- Specialized consumer that processes a particular variant
- Consumer that needs the specialized properties

---

## Relations Between the Two Levels

### Relation Summary Table

| Relation | Source | Target | Field |
|----------|--------|-------|-------|
| Carries | Business Event | Business Object | `carried_business_object` |
| Implements | Resource | Business Object | `business_object` |
| Implements | Resource.data[] | Business Object.data[] | `business_object_property` |
| Carries | Resource Event | Resource | `carried_resource` |
| Implements | Resource Event | Business Event | `business_event` |
| Targets | Business Subscription | Business Event | `subscribed_event` |
| Targets | Resource Subscription | Resource Event | `subscribed_resource_event` |
| Links | Resource Subscription | Business Subscription | `linked_business_subscription` |

### Complete Modeling Example

```
Business Level
──────────────
OBJ.COEUR.005.DECLARATION_SINISTRE
    └── data: claimDeclarationId, occurrenceDate, contractId...

EVT.COEUR.005.SINISTRE_DECLARE
    └── carried_business_object: OBJ.COEUR.005.DECLARATION_SINISTRE

Resource Level (Variant 1: Water damage)
─────────────────────────────────────────
RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_DEGAT_EAUX
    ├── business_object: OBJ.COEUR.005.DECLARATION_SINISTRE
    └── data: claimDeclarationId (→BO), occurrenceDate (→BO), leakOrigin, impactedArea...

EVT.RES.COEUR.005.SINISTRE_HABITATION_DEGAT_EAUX_DECLARE
  ├── carried_resource: RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_DEGAT_EAUX
  └── business_event: EVT.COEUR.005.SINISTRE_DECLARE

Resource Level (Variant 2: Theft)
──────────────────────────────────
RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_VOL
    ├── business_object: OBJ.COEUR.005.DECLARATION_SINISTRE
    └── data: claimDeclarationId (→BO), occurrenceDate (→BO), theftType, stolenGoods...

EVT.RES.COEUR.005.SINISTRE_HABITATION_VOL_DECLARE
  ├── carried_resource: RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_VOL
  └── business_event: EVT.COEUR.005.SINISTRE_DECLARE
```

---

## Validation Rules

The BCM referential automatically validates the following rules:

| Rule | Level | Description |
|-------|--------|-------------|
| V1 | Business | Every business event references an existing business object |
| V2 | Resource | Every resource references a unique existing business object |
| V3 | Resource | Every resource event references a unique existing business event |
| V4 | Traceability | Every business object property is referenced by at least one resource |
| V5 | Subscription | Every resource subscription references an existing business subscription |
| V6 | Coherence | The business event of the resource subscription matches that of the linked business subscription |

---

## Anti-Patterns to Avoid

### Generic event with type field

```yaml
# INCORRECT — forces polymorphic decoding on the consumer side
id: EVT.RES.COEUR.005.SINISTRE_DECLARE
data:
  - name: type             # "WATER_DAMAGE", "THEFT", "FIRE"
  - name: genericPayload   # variable structure depending on type
```

### Double publication for the same fact

```yaml
# INCORRECT — imposes a correlation on the consumer side
# Publication 1: generic event
id: EVT.RES.COEUR.005.SINISTRE_DECLARE
# Publication 2: specialized event (in parallel, same moment)
id: EVT.RES.COEUR.005.SINISTRE_HABITATION_DEGAT_EAUX_DECLARE
```

### Resource event dependent on a peer

```yaml
# INCORRECT — requires a join to be understood
id: EVT.RES.COEUR.005.SINISTRE_HABITATION_DEGAT_EAUX_DECLARE
data:
  - name: parentEventId    # points to an event published in parallel
    required: true
```

---

## Justification

This two-level architecture allows:

- **Separating abstraction from implementation**: the business event abstracts the
  milestone, the resource event materializes the variant
- **Supporting variants without complexity**: no new concept, exploitation
  of the existing meta-model
- **Facilitating transverse consumption**: business subscription for generalist consumers
- **Guaranteeing traceability**: each resource property can be traced back
  to the source business object
- **Simplifying governance**: clear distinction between abstraction and implementation

---

## Impacts

### Structure
- No extension of the meta-model (ADR-BCM-URBA-0007)
- Clarification of the usage of existing relations

### Validation
- Rule added: every business object property must be referenced by at least
  one resource via `business_object_property`

### Tooling
- Generation and validation tools exploit both levels to produce
  coherent documentation and diagrams

---

## Governance Indicators

- **Business object coverage**: % of business object properties referenced by resources
- **Event coherence**: all resource events reference a business event
- **Event autonomy**: no resource event depends on a peer to be understood

---

## Traceability

- Workshop: BCM Event Modeling
- Participants: IS Urbanization, Architecture, Lead BA, BA, Lead Dev
- References: ADR-BCM-URBA-0007, ADR-BCM-FUNC-0003
