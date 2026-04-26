---
id: ADR-BCM-URBA-0004
title: "Deciding at the Right Level (L1/L2/L3)"
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
  - ADR-BCM-GOV-0002  # Arbitration board
  - ADR-BCM-URBA-0002

supersedes: []

tags:
  - BCM
  - Governance
  - Decisions

stability_impact: Structural
---

# ADR-BCM-URBA-0004 — Deciding at the Right Level (L1/L2/L3)

## Context
Without an explicit "decision level" rule, arbitrations are made:
- too macro (at L1): vague, non-actionable decisions,
- too granular (at L3): micro-optimization, endless discussions, model instability.

This directly impacts:
- roadmap prioritization,
- application rationalization,
- service and integration contract definition.

## Decision
- **L1** serves for strategic framing, communication, and "value" steering.
- **L2** serves for urbanization arbitrations: ownership, rationalization, budgets, prioritization, trajectories.
- **L3** serves for actionable design: business services, contracts (API/events), detailed rules, coverage testing.

The L3 domain should only be made explicit in exceptional cases:
- Very strong competitive advantage axis, a strategic development priority for the company
- Level of complexity requiring going down one more level to understand the complexity and perform the arbitrations normally carried out at level 2

Level 3 must not remain as-is; it is a transitional stage:
- It must follow the current strategy and not burden the map with past visions
- It should recede to revisit the organization at the L1 and L2 level to resolve accidental complexity that has been found.

This map must serve as a guide and remain at a certain level of simplicity to allow all stakeholders to easily grasp it and thereby support the company's strategic challenges.

## Justification
- **L1** provides the strategic vision and communication: stable, lasting, understandable by all.
- **L2** is the pivot level for urbanization: stable enough to organize responsibilities, investments, and transformation, granular enough to arbitrate application rationalization.
- **L3** exists in the model but is **used in an exceptional and transitional manner**:
  - **Exceptional**: only on competitive advantage axes or areas of high complexity where L2 is no longer sufficient for arbitration
  - **Transitional**: once arbitrations are done and accidental complexity resolved, L3 must either recede (return to L2) or lead to a more relevant L1/L2 reorganization
  - **Guiding**: L3 temporarily illuminates design decisions (business services, API/event contracts, detailed rules) but must not permanently burden the map

The objective is to **keep the BCM simple and appropriable** by all stakeholders, while allowing temporary zooms on critical areas.

### Alternatives Considered

- **Decide everything at L1** — rejected because insufficient for urbanization, too macro for arbitrations.
- **Decide everything at L3** — rejected because unstable, too costly, promotes "process map" drift, loss of readability.
- **Permanent and exhaustive L3** — rejected because excessive complexity, costly maintenance, risk of an encyclopedic non-current map.

## Impacts on the BCM

### Structure

- **Roadmaps**: structured by **L2** capabilities (default steering level).
- **Transformation backlogs**: detailed in **L3** only for critical / transforming / high-competitive-advantage domains.
- **Architecture reviews**: breakdown decisions at **L2**, contract/integration decisions at **L3**.
- **L3 Governance**:
  - Creating an L3 requires explicit justification (complexity, criticality, strategic stake)
  - Periodic review to delete or "elevate" L3s that have become irrelevant
  - Default views (BCM L1/L2) do **not** show L3s to maintain readability

### Events (if applicable)

- No direct impact.

### Mapping SI / Data / Org

- No direct impact.

## Consequences
### Positive
- Faster and comparable arbitrations (focus on L2).
- Reduction of granularity debates (clear rule: L2 by default, L3 if justified).
- Better coherence of integration contracts (API/events) with the model.
- **Agile BCM**: ability to temporarily zoom in (L3) without permanently burdening the map.
- **Strategic priority alignment**: L3 follows the current strategy, avoids accumulation of modeling debt.

### Negative / Risks
- Requires governance discipline (workshop templates, modeling rules).
- **Cleanup discipline**: risk of forgetting to "elevate" or delete obsolete L3s.
- **Debates on the threshold**: when to trigger an L3? Subjective criteria (complexity, criticality) can create disagreements.
- **Temptation of detail**: risk of wanting to detail everything in L3 despite the rule (requires regular reviews).

### Accepted Debt

- L3 trigger criteria partially subjective (complexity, criticality); to be refined in practice.
- L3 cleanup discipline to be progressively established.

## Governance Indicators

- Criticality level: High (structuring transverse rule).
- Recommended review date: 2028-01-21.
- Expected stability indicator: no L3 present in default views without formalized justification.

## Traceability

- Workshop: BCM Urbanization Guide v1 — "Decision Levels" section
- Participants: EA / Urbanization, Business Architecture
- References: ADR-BCM-URBA-0002
