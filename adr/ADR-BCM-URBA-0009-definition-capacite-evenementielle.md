---
id: ADR-BCM-URBA-0009
title: "Complete Capability Definition — Responsibility, Event Production and Consumption"
status: Proposed
date: 2026-03-10

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
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0007
  - ADR-BCM-URBA-0008
  
supersedes:
  - ADR-BCM-URBA-0003

tags:
  - BCM
  - Urbanization
  - Ownership
  - event-driven
  - subscription
  - production

stability_impact: Structural
---

# ADR-BCM-URBA-0009 — Complete Capability Definition — Responsibility, Event Production and Consumption

## Context

ADR-BCM-URBA-0003 establishes that a capability describes a **stable business responsibility**, independent of technical solutions. This foundational definition remains valid but incomplete in an event-driven architecture context.

With the introduction of the event meta-model (ADR-BCM-URBA-0007) and the two-level modeling rules (ADR-BCM-URBA-0008), it becomes necessary to enrich the definition of a capability to explicitly include:

- its **event production** (what it emits);
- its **event consumption** (what it subscribes to).

This extension allows characterizing a capability not only by what it *does* (responsibility), but also by what it *communicates* (event-driven interactions).

## Decision

### Extended Capability Definition

A capability is defined by:

1. **A stable business responsibility** (carried over from ADR-BCM-URBA-0003)
   - The business "what", independent of the technical solution.
   - Applications and components are mapped onto capabilities, but do not define them.
   - No reference to a vendor, tool, or technology in the labels.

2. **Its event production**
   - A capability is the **producer** of events that materialize the milestones of its lifecycle.
   - It has the **exclusive responsibility** for producing these events.

3. **Its event consumption**
   - A capability **consumes** events via formalized subscriptions.
   - These subscriptions define the **explicit dependencies** of the capability.

---

### Rules by Abstraction Level

#### Business Level

| Aspect | Rule |
|--------|-------|
| **Production** | The capability is responsible for producing its **business events**, representing the abstract milestones of its lifecycle. |
| **Consumption** | The capability subscribes to **external business events** only if these events **directly impact the lifecycle of the capability's process**. |

**Decision criterion for a business subscription:**
> Does the external business event trigger or influence a state change in the lifecycle of the process carried by this capability?
> - If **yes** → business subscription justified.
> - If **no** → this is not a business subscription (potentially a resource subscription).

#### Operational Level

| Aspect | Rule |
|--------|-------|
| **Production** | The capability is responsible for producing its **resource events**, representing the specialized published facts related to the resources it manages. |
| **Consumption** | The capability subscribes to **resource events** for any data source involved in **information production**, whether for building a **read model** or for data impacting the process lifecycle. |

**Decision criterion for a resource subscription:**
> Does the external resource event provide data necessary for:
> - building a read model used by the capability? → **yes**
> - executing a business rule or processing by the capability? → **yes**
> - If neither → no resource subscription justified.

---

### Synthetic View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CAPABILITY                                      │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    BUSINESS RESPONSIBILITY                             │  │
│  │           (the "what", stable, independent of the IS)                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────┐       ┌─────────────────────────────────────┐  │
│  │      PRODUCTION         │       │         CONSUMPTION                 │  │
│  │                         │       │                                     │  │
│  │  ┌───────────────────┐  │       │  ┌─────────────────────────────────┐│  │
│  │  │  Business Events  │  │       │  │     Business Subscriptions      ││  │
│  │  │ (lifecycle        │  │       │  │  (events impacting the          ││  │
│  │  │  milestones,      │  │       │  │   lifecycle of the process)     ││  │
│  │  │  abstract)        │  │       │  └─────────────────────────────────┘│  │
│  │  └───────────────────┘  │       │                                     │  │
│  │                         │       │  ┌─────────────────────────────────┐│  │
│  │  ┌───────────────────┐  │       │  │   Resource Subscriptions        ││  │
│  │  │ Resource Events   │  │       │  │  (data for read model or        ││  │
│  │  │ (specialized      │  │       │  │   information production)       ││  │
│  │  │  published facts) │  │       │  └─────────────────────────────────┘│  │
│  │  └───────────────────┘  │       │                                     │  │
│  └─────────────────────────┘       └─────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Verifiable Criteria

| Criterion | Verification |
|---------|--------------|
| Every L2 capability must emit at least one business event | Automated control via `validate_events.py` |
| Each business subscription must justify an impact on the lifecycle | `lifecycle_impact` field required in the subscription template |
| Each resource subscription must specify its usage (read model or processing) | `usage_type` field required in the subscription template |
| A capability does not subscribe to its own events | Automated control |

## Justification

This extension of the definition allows:

- **expliciting interaction contracts** between capabilities;
- **clarifying responsibilities** producer/consumer at each level;
- **distinguishing structural dependencies** (lifecycle) from operational dependencies (read model);
- **tooling governance** with automatically verifiable criteria.

### Alternatives Considered

- **Option A — Keep only the responsibility-based definition:**
  Rejected because insufficient to characterize interactions in an event-driven architecture.

- **Option B — Define subscriptions without business/resource distinction:**
  Rejected because it does not allow differentiating coupling levels and identifying true business dependencies.

- **Option C — Leave subscriptions implicit:**
  Rejected because it creates non-traceable and ungovernable shadow coupling.

## Impacts on the BCM

### Structure

- Impacted capabilities: all (enrichment of the definition).
- Capability templates to enrich with `produced_events` and `subscriptions` sections.

### Events

- Explicit formalization of the `Capability -> Event` relation (production).
- Explicit formalization of the `Capability + Subscription -> Event` relation (consumption).

### Mapping SI / Data / Org

- **SI**: allows mapping event flows by capability.
- **DATA**: clarifies data sources (resource subscriptions for read models).
- **ORG**: production responsibility explicitly assigned to each capability.

## Consequences

### Positive

- Complete traceability of inter-capability interactions.
- Toolable governance: automatic detection of inconsistencies.
- Support for impact analysis (who produces, who consumes).
- Clarification of coupling levels (business vs. operational).

### Negative / Risks

- Increased complexity of capability documentation.
- Need to maintain coherence between capabilities, events, and subscriptions.
- Governance discipline required to qualify subscriptions.

### Accepted Debt

- Existing capabilities may temporarily not have their events and subscriptions documented.
- Progressive migration toward the complete definition.

## Governance Indicators

- Criticality level: High (structuring transverse rule).
- Recommended review date: 2028-03-10.
- Expected stability indicators:
  - 100% of L2 capabilities with at least one business event documented.
  - 100% of subscriptions with documented usage qualification.
  - 0 business subscriptions without lifecycle impact justification.

## Traceability

This ADR **supersedes** ADR-BCM-URBA-0003, carrying forward and enriching its foundational definition.
