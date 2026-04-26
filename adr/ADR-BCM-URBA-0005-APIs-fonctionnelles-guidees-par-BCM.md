---
id: ADR-BCM-URBA-0005
title: "Interface Contracts Guided by the BCM (Logical/Physical Decoupling)"
status: Suspended
date: 2026-02-24
suspension_date: 2026-03-10
suspension_reason: >
  Reflects a maturity level not yet present in the company.
  Risk of causing more confusion than clarity at this point.

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

related_adr:
  - ADR-BCM-GOV-0001  # GOV → URBA → FUNC hierarchy
  - ADR-BCM-URBA-0003
  - ADR-BCM-URBA-0004

supersedes: []

tags:
  - BCM
  - Urbanization
  - Events
  - API
  - Decoupling
  - Legacy
  - Target IS

stability_impact: Structural
---

# ADR-BCM-URBA-0005 — Interface Contracts Guided by the BCM (Logical/Physical Decoupling)

## Context
In a legacy IS context, several structural problems emerge:
- **Application/functional coupling**: interfaces (APIs/events) exposed follow the structure of existing applications (silos) rather than business responsibilities.
- **Invisible technical debt**: impossible to measure the gap between existing and target if the target is not defined.
- **Undirected application evolution**: each application modification creates new "opportunistic" interfaces without an overall vision.
- **Legacy dependency**: the IS is prisoner of the physical organization of applications, making any transformation costly and risky.

Without a stable functional referential, one cannot:
- steer convergence toward a target IS,
- measure and prioritize technical debt,
- guarantee interface coherence during evolutions,
- prepare the progressive replacement of legacy applications.

**In this repository, interface contracts are primarily materialized via business events** documented in the `bcm/events-*.yaml` files. Each L2 capability must declare:
- the events it **produces** (with `emitted_by_l2`)
- the events it **consumes** (with `handled_by_l2` + originating L2 capability)

This event-driven approach favors decoupling and asynchronism, but requires strict governance to avoid drift ("event spaghetti").

## Decision
- **Functional interface contracts are defined by BCM capabilities**:
  - **L2** level: defines **functional domains** (scope, ownership, produced/consumed events)
  - **L3** level: defines **detailed contracts** (business services, events, interface rules) when necessary (cf. [ADR-BCM-URBA-0004](ADR-BCM-URBA-0004-bon-niveau-de-decision.md))

- **Interface contracts are materialized via business events**:
  - Each **L2** capability declares the **events it produces** (with `emitted_by_l2`)
  - Each **L2** capability declares the **events it consumes** (with `handled_by_l2` + originating L2 producer)
  - These contracts are documented in the `bcm/events-<L1>.yaml` files

- **Every application must tend toward this organization**:
  - Regardless of legacy state, exposed/consumed events must be **mapped** onto BCM capabilities
  - Any modification of a legacy application must **converge toward implementing the event contracts** defined in the BCM
  - Gaps between existing events and target events are **documented and traced** as technical debt

- **Creation of a virtual functional layer**:
  - Event contracts represent the **logical target IS** (the "what"), independent of physical implementation (the "how")
  - Applications are **physical realizations** that produce or consume these events
  - The Capability → Events → Application mapping allows transformation governance

- **Evolution rule**:
  - Any new event or modification of an existing event must be **justified by a BCM capability**
  - Events "outside BCM" are considered **technical debt** and must be migrated or deleted
  - In case of application replacement, the **event contracts remain stable** (continuity contract)

## Justification
This approach allows **decoupling the logical from the physical**:

1. **Default target IS**: The BCM defines the target event contract model. By default, we are **always** in the target IS (at the logical level), even if legacy applications do not yet perfectly implement it.

2. **Manageable technical debt**: The gap between existing (legacy) and functional (BCM) events becomes **measurable and actionable**. We can prioritize convergence based on business value.

3. **Directed evolution**: Any application modification knows "where to go" (target event contract). No drift, no opportunistic events.

4. **Progressive transformation**: We can replace a legacy application with another without changing event contracts (if well designed). The business does not see the technical transformation.

5. **Reinforced governance**: Events become a governed asset (ownership, contracts, versioning, schemas) aligned with business responsibilities.

6. **Event-driven architecture**: Favors decoupling (independent producers/consumers), asynchronism, and IS resilience.

### Alternatives Considered

- **Events defined by applications** — rejected because it reinforces silos, prevents any convergence toward a coherent target IS.
- **Events defined by projects** — rejected because of opportunism, incoherence, multiplication of contracts, accumulated debt.
- **Event bus without functional referential** — rejected because of lack of stability, risk of "event spaghetti", absence of governance.
- **Wait for complete application replacement** — rejected because too slow, too costly, does not allow continuous improvement.

## Impacts on the BCM

### Structure

- Impacted capabilities: all (each L2/L3 capability can define event contracts).
- **L2 capabilities** define the **event domains** (ownership, functional scope, produced/consumed events).
- **L3 capabilities** (exceptional, cf. ADR-BCM-URBA-0004) define the **detailed contracts** (event schemas, business rules).

### Events (if applicable)

- New mapping: `L2 Capability → Events (produced/consumed) → Applications` (logical/physical traceability).
- Each event must be attached to **one and only one** L2 emitting capability (clear ownership).
- Use `bcm/events-<L1>.yaml` files to describe contracts by L1 capability.
- Each produced event indicates the emitting L2 capability (`emitted_by_l2`).
- Each consumed event indicates the consuming L2 capability (`handled_by_l2`) and the originating L2 capability.

### Mapping SI / Data / Org

- Create a `bcm/mappings/apis-capabilities.yaml` file to trace Capability ↔ Application.
- Generate an "event coverage" view.
- Gaps (legacy events outside BCM) are traced and reviewed periodically.
- Business objects carried in events must be documented (schemas, properties).

## Consequences
### Positive
- **Clear target IS vision**: event contracts define "where we are going", even if we are not there yet.
- **Visible and measurable technical debt**: gap between existing vs. target events, objective prioritization.
- **Directed evolution**: each application modification knows which events to tend toward (no drift).
- **Logical/physical decoupling**: we can replace/modernize applications without changing event contracts.
- **Interface governance**: ownership, contracts, schemas, versioning aligned with business responsibilities (BCM).
- **Transformation resilience**: event contracts remain stable even as applications change.
- **Better interoperability**: events designed "business-first" (capabilities) rather than "technical-first" (application silos).
- **Producer/consumer decoupling**: asynchronous event-driven architecture favoring resilience and scalability.
- **Functional traceability**: each event is linked to an L2 capability, facilitating audit and flow understanding.

### Negative / Risks
- **Initial complexity**: requires defining event contracts (modeling effort, workshops).
- **Convergence cost**: legacy applications must progressively align (continuous investment).
- **Adaptation layer**: may require temporary adapters/translators (legacy events → functional events).
- **Governance discipline**: risk of drift if events are not regularly reviewed.
- **Big design temptation**: risk of wanting to define everything at L3 (reminder: L3 exceptional, cf. [ADR-BCM-URBA-0004](ADR-BCM-URBA-0004-bon-niveau-de-decision.md)).
- **Versioning management**: event schemas must evolve without breaking consumers (backward compatibility, migration strategies).
- **Change resistance**: application teams may see this as an additional constraint (requires support).
- **Event infrastructure**: requires a robust event bus (availability, performance, monitoring).

### Accepted Debt
- **Existing legacy events** will not be migrated immediately. They are **documented as technical debt** and migrated progressively during evolutions.
- **Temporary adapters/translators** may be necessary during the transition phase (cost accepted to guarantee convergence).
- **L3 capabilities** for defining detailed event schemas remain exceptional (cf. [ADR-BCM-URBA-0004](ADR-BCM-URBA-0004-bon-niveau-de-decision.md)). We start at L2 (event domain) and go down to L3 only if necessary.
- **Technical events** (heartbeats, logs, metrics) are not necessarily linked to the BCM (focus on business events).

## Governance Indicators

- Criticality level: High (structuring transverse decision).
- Recommended review date: 2028-02-24.
- Expected stability indicator: 100% of business events attached to an L2 capability.

## Traceability

- Workshop: Urbanization 2026-02-24
- Participants: EA / Urbanization, IS Architecture, yremy, acoutant
- References:
  - ADR-BCM-URBA-0003 — 1 capability = 1 responsibility → 1 event domain
  - ADR-BCM-URBA-0004 — L3 for detailed event schemas (exceptional)
  - Files: `bcm/events-*.yaml`
