---
id: ADR-BCM-<GOV|URBA|FUNC>-<NNNN>
title: "<Title>"
status: Proposed | Accepted | Suspended | Deprecated | Superseded
date: YYYY-MM-DD
# If status: Suspended, add:
# suspension_date: YYYY-MM-DD
# suspension_reason: <reason for suspension>

family: GOV | URBA | FUNC

decision_scope:
  level: L1 | L2 | L3 | Cross-Level
  zoning: []
  # Possible values:
  # - PILOTAGE                    → strategic steering, governance, arbitration, executive reporting
  # - SERVICES_COEUR → core business, service production, operational management
  # - SUPPORT                     → transverse functions (HR, finance, legal, procurement)
  # - REFERENTIEL                 → reference data, shared referentials, MDM
  # - ECHANGE_B2B                → inter-company exchanges, partners, suppliers, EDI
  # - CANAL                     → distribution channels, customer relations, portals, apps
  # - DATA_ANALYTIQUE              → analytical data, BI, reporting, data science

impacted_capabilities: []
impacted_events: []           # events PRODUCED by the L2s of this ADR
impacted_subscriptions: []    # events CONSUMED — format: "EventName (emitting_capability: CAP.ZONE.NNN.SUB)"
impacted_mappings: []
  # Possible values:
  #   - SI    → applications, modules, technical components
  #   - DATA  → data flows, data domains, referentials
  #   - ORG   → teams, roles, operational responsibilities

related_adr: []
supersedes: []

tags: []

stability_impact: Structural | Moderate | Minor

# MANDATORY for FUNC ADRs — derived from product vision and strategic vision
domain_classification:
  type: core | supporting | generic
  coordinates:
    x: 0.0   # business differentiation  (0.0 = commodity → 1.0 = fully differentiating)
    y: 0.0   # model complexity           (0.0 = trivial   → 1.0 = highly complex / proprietary)
  rationale: "<one sentence: why this L2 is core / supporting / generic>"
---

# ADR-BCM-<FAM>-<NNNN> — <Short title>

## Domain Classification

> **Mandatory for FUNC ADRs.** Derived from the product vision and strategic vision — not from technical complexity alone.

| Axis | Score | Interpretation |
|------|-------|----------------|
| x — Business Differentiation | 0.0 | 0.0 = commodity (could be bought off-shelf) → 1.0 = uniquely differentiating |
| y — Model Complexity | 0.0 | 0.0 = trivial / well-understood → 1.0 = proprietary / high cognitive load |

**Classification:** `core | supporting | generic`

**Rationale:**

> Replace this line with one sentence explaining the classification against the product/strategic vision.

---

## Context

Describe:
- The tension (e.g., readability vs. actionability)
- The constraints (zoning, 1 capability = 1 responsibility, L2 pivot)
- The current state

## Decision

Decision formulated in a **testable** manner:

- Rule 1:
- Rule 2:
- Verifiable criterion:

Example:
> Every L2 capability must emit at least one business event.

## Justification

Why this option.

### Alternatives Considered

- Option A — rejected because...
- Option B — rejected because...

## Impacts on the BCM

### Structure

- Impact on L1/L2/L3:
- Split / Merge / Move:

### Events (if applicable)

- New events:
- Deleted events:
- Modified events:

### Mapping SI / Data / Org

- Impacted applications:
- Impacted flows:

## Consequences

### Positive

### Negative / Risks

### Accepted Debt

## Governance Indicators

- Criticality level:
- Recommended review date:
- Expected stability indicator:

## Traceability

- Workshop:
- Participants:
- References:
