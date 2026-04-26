---
id: ADR-BCM-URBA-0003
title: "One Capability = One Responsibility, Not an Application"
status: Superseded
date: 2026-02-26
superseded_by: ADR-BCM-URBA-0009
superseded_date: 2026-03-10

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

related_adr:
  - ADR-BCM-GOV-0001  # GOV → URBA → FUNC hierarchy
supersedes: []

tags:
  - BCM
  - Urbanization
  - Ownership

stability_impact: Structural
---

# ADR-BCM-URBA-0003 — One Capability = One Responsibility, Not an Application

## Context
During mappings and rationalization, a frequent drift is to equate a capability with an application (e.g., "CRM = Customer Relations").
This creates:
- overlaps (multiple applications covering the same capability),
- sterile "tool vs. business" debates,
- an inability to objectively compare options (build/buy, product vs. platform, trajectory).

## Decision
- A capability describes a stable business responsibility (the "what"), independent of the solution.
- Applications, IS products, and technical components are **mapped** onto capabilities, but do not define them.
- Capability labels contain **no** reference to a vendor, tool, or technology.



## Justification

This separation allows:
- avoiding technological bias,
- maintaining a common business/IS language,
- steering a trajectory (before/after) without renaming the business,
- measuring IS coverage and identifying duplicates.

### Alternatives Considered

- Capability = Application — rejected because too dependent on the IS landscape, blocks transformation.
- Capability = Process — rejected because it drifts into an exhaustive operational map.

## Impacts on the BCM

### Structure

- Impacted capabilities: all (naming and scope rule).

### Events (if applicable)

- No direct impact.

### Mapping SI / Data / Org

- Maintain a separate "Capability → Applications/Products" view (not in the BCM).

## Consequences
### Positive
- More objective application rationalization (coverage, redundancies, gaps).
- Enhanced readability for arbitrations (build/buy, convergence, pooling).

### Negative / Risks

- Governance discipline required (label reviews, quality control).

### Accepted Debt

- Existing labels inherited from legacy may persist temporarily.

## Governance Indicators

- Criticality level: High (transverse rule).
- Recommended review date: 2028-01-21.
- Expected stability indicator: 0 capabilities carrying a vendor or product name.

## Traceability

- Workshop: Architecture Review — application of the rule on capability→IS mappings
- Participants: EA / Urbanization, Business Architecture
- References: —
