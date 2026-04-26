---
id: ADR-BCM-URBA-0002
title: "BCM Structured in 3 Levels (L1/L2/L3)"
status: Proposed
date: 2026-02-26

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
    - ORG

related_adr:
  - ADR-BCM-GOV-0001  # GOV → URBA → FUNC hierarchy
supersedes: []

tags:
  - BCM
  - Modeling
  - Levels

stability_impact: Structural
---

# ADR-BCM-URBA-0002 — BCM Structured in 3 Levels (L1/L2/L3)

## Context
The BCM must serve:
- as a common business/IS language,
- as support for urbanization (alignment of applications / data / investments),
- without becoming a process map.

A 2-level model lacks granularity for certain arbitrations (IS allocation, rationalization, ownership).

## Decision
- The BCM is structured in 3 levels: L1, L2, L3.
- Standard exposed views are L1/L2.
- The L3 level is produced only for critical domains (High criticality) or those under transformation.

## Justification

The 3-level model provides actionability (L3) without losing readability (L1/L2).

### Alternatives Considered

- 2 levels — rejected because too macro for urbanization.
- 4+ levels — rejected because of the risk of drifting into a process map.

## Impacts on the BCM

### Structure

- Impacted capabilities: all (construction rule).
- Views: generate an L1/L2 view by default.

### Events (if applicable)

- No direct impact.

### Mapping SI / Data / Org

- No direct impact.

## Consequences
### Positive
- Better steering of IS coverage and investments.

### Negative / Risks

- Risk of inconsistent granularity if L3 is not governed.

### Accepted Debt

- More precise L3 framing deferred (see ADR-BCM-URBA-0004).

## Governance Indicators

- Criticality level: High (structuring decision).
- Recommended review date: 2028-01-21.
- Expected stability indicator: 100% of capabilities have an L1/L2 level assigned.

## Traceability

- Workshop: Urbanization 2026-01-15
- Participants: EA / Urbanization, Business Architecture
- References: —
