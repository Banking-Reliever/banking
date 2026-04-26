---
id: ADR-BCM-URBA-0012
title: "Introduction of a Canonical Business Concept"
status: Proposed
date: 2026-03-19

family: URBA

decision_scope:
  level: Cross-Level
  zoning:
    - SERVICES_COEUR
    - SUPPORT
    - REFERENTIEL
    - ECHANGE_B2B
    - DATA_ANALYTIQUE

impacted_capabilities: []
impacted_events: []
impacted_mappings:
  - SI
  - DATA
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0008
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010

supersedes: []

tags:
  - BCM
  - URBA
  - canonical-concept
  - business-object
  - resource

stability_impact: Structural
---

# ADR-BCM-URBA-0012 — Introduction of a Canonical Business Concept

## Context

The BCM framework currently distinguishes:
- **L2 capabilities**, which carry business responsibilities;
- **business objects**, attached to a responsibility;
- **resources**, which express these objects for operational needs.

Recent work has highlighted a complementary need: to have a more transverse level to simply designate notions such as **Claim declaration** or **Claim file**, without merging different responsibilities into the same business object.

Indeed, a single business object shared between several L2 capabilities would lead to:
- blurring responsibilities;
- reinforcing coupling;
- creating objects that are too broad or partially filled;
- confusing business modeling with technical implementation details.

## Decision

An additional level is introduced: the **canonical business concept or canonical model**.

The **canonical business concept or canonical model**:
- represents a transverse and stable business notion;
- serves as a common semantic reference;
- does not on its own carry an operational responsibility;
- is not a substitute for either the **business object** or the **resource**.

The BCM framework is therefore read according to the following hierarchy:

```text
Canonical business concept or canonical model
        ↓
Business object
        ↓
Resource
```

## Rules

1. A **canonical business concept or canonical model** may be expressed as several **business objects**.
2. Each **business object** remains attached to an explicit responsibility carried by an L2 capability.
3. Each **business object** may be expressed as one or more **resources** according to operational needs.
4. A **canonical business concept or canonical model** must not be used directly as an exchange or implementation object.
5. A technical payload or serialization detail does not, by itself, justify the merging of several business objects.

## Example
| Canonical business concept | Business object                  | Resource                                      |
| -------------------------- | -------------------------------- | --------------------------------------------- |
| Claim declaration          | Claim declaration received       | Claim declaration received                    |
| ^^                         | Claim declaration                | Water damage claim declaration                |
| ^^                         | ^^                               | Fire claim declaration                        |
| ^^                         | ^^                               | Theft claim declaration                       |


## Justification

This decision allows:

* preserving a common transverse business language;
* maintaining the L2 responsibility-based breakdown;
* avoiding the creation of overly broad or ambiguous business objects;
* maintaining the distinction between business modeling and technical implementation.

## Consequences
### Positive

* Better semantic clarity.
* Better respect of business responsibilities.
* Reduction of the risk of strong coupling between capabilities.
* Better articulation between transverse vision and operational breakdowns.

### Risks

* Introduction of an additional conceptual level.
* Risk of confusion if the canonical concept is understood as a single technical schema.

## Traceability

This decision is part of the continuum of:

* BCM governance;
* the event modeling guide;
* the capability definition;
* the principle that L2 capabilities constitute the urbanization pivot.
