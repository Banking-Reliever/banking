---
id: ADR-BCM-URBA-0011
title: "Local Complexity Decompression via L3 While Maintaining L2 as Pivot"
status: Proposed
date: 2026-03-17

family: URBA

decision_scope:
  level: Cross-Level
  zoning:
    - SERVICES_COEUR
    - SUPPORT
    - REFERENTIEL
    - DATA_ANALYTIQUE

impacted_capabilities: []
impacted_events: []
impacted_mappings:
  - SI
  - DATA
  - ORG

related_adr:
  - ADR-BCM-URBA-0004
  - ADR-BCM-URBA-0007
  - ADR-BCM-URBA-0008
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010
  - ADR-BCM-FUNC-0002
  - ADR-BCM-FUNC-0003

supersedes: []

tags:
  - BCM
  - L2
  - L3
  - complexity
  - events
  - urbanization

stability_impact: Structural
---

# ADR-BCM-URBA-0011 — Local Complexity Decompression via L3 While Maintaining L2 as Pivot

## Context

The L2 level has been retained as the urbanization pivot, the model relationship anchor point, the reference level for SI / DATA / ORG mappings, and for functional ownership.

In certain L2 capabilities, particularly when the density of rules, the variety of management cases, or the cognitive load becomes too high, a purely L2 modeling can become difficult to exploit operationally.

This risk is particularly visible on capabilities such as claim instruction or indemnification in capability CAP.COEUR.005 "Claims & Benefits", which concentrate many business variants, intermediate decisions, and external interactions.

## Decision

### 1) The L2 level remains the default pivot

L2 capabilities remain:
- the reference level for ownership,
- the anchor point for business objects, business events, and business subscriptions,
- the canonical cross-reading level,
- the reference level for SI / DATA / ORG mappings.

### 2) The L3 level is authorized only as a local decompression mechanism

When an L2 capability becomes too complex to remain governable on its own, an L3 level may be introduced locally to:
- segregate homogeneous subsets,
- explicit the detailed production,
- reduce the cognitive load and size of operational contracts.

L3 does not become a new global pivot.

### 3) Canonical contracts remain expressed at the L2 level

Transverse consumers must continue to rely primarily on the business objects, business events, and business subscriptions attached to the L2.

The finer elements introduced at L3 serve to describe the detailed or specialized production of an L2 capability, without calling into question the transverse readability of the model.

### 4) Detailed elements can be re-aggregated toward the L2

When an L3 zoom is used, aggregation, normalization, or projection mechanisms may be used to reconstitute a canonical milestone at the L2 level.

The L2 therefore remains the transverse exposure level; the L3 remains the local detail level.

## Consequences

### Positive

- Preservation of a simple and stable rule: L2 remains the pivot.
- Ability to locally handle overly dense zones without overhauling the entire model.
- Better management of complexity on the most loaded capabilities.
- Maintenance of a homogeneous cross-reading for consumers.

### Negative / Risks

- Introduction of an additional derivation layer between L3 and L2.
- Risk of over-using L3 if the entry criteria are not made explicit.
- Need to clearly govern the re-aggregation and responsibility rules.

### Accepted Debt

- The precise trigger criteria for an L3 zoom may be refined by a capability-local ADR.
- Not all L3 decomposition cases are defined at this stage.
- Some L2 capabilities may temporarily remain overloaded before their L3 is formalized.

## Governance Rule

An L3 zoom is only acceptable if the following three conditions are met:
1. the L2 capability is no longer cognitively or operationally manageable as-is;
2. the decomposition allows isolating genuinely homogeneous subsets;
3. the canonical contracts exposed to the rest of the IS remain readable at the L2 level.

## Governance Indicators

- The L2 level remains the anchor point of 100% of SI / DATA / ORG mappings.
- The use of L3 remains justified by documented exception.
- Each capability with an L3 retains an identifiable canonical contract at the L2 level.

## Traceability

- References:
  - ADR-BCM-URBA-0004 — deciding at the right level
  - ADR-BCM-URBA-0007 — normalized event meta-model
  - ADR-BCM-URBA-0008 — two-level event modeling
  - ADR-BCM-URBA-0009 — complete capability definition
  - ADR-BCM-URBA-0010 — L2 urbanization pivot
  - ADR-BCM-FUNC-0002 — L2 breakdown of COEUR.005
  - ADR-BCM-FUNC-0003 — DSP limits
