---
id: ADR-BCM-GOV-0001
title: "BCM Decision Governance – GOV / URBA / FUNC Hierarchy"
status: Proposed
date: 2026-02-26

family: GOV

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

related_adr: []

supersedes: []

tags:
  - governance
  - hierarchy
  - GOV
  - URBA
  - FUNC

stability_impact: Structural
---

# ADR-BCM-GOV-0001 — BCM Decision Governance

## Context

The land use plan (BCM under a different name) constitutes the structuring functional referential of the Information System.

Three distinct types of decisions are identified:

1. **Governance decisions (GOV)**
   - Organization of the decision-making framework
   - ADR hierarchy
   - Arbitration mechanisms
   - Decision lifecycle and periodic review

2. **Urbanization decisions (URBA)**
   - Definition of modeling principles
   - Zoning rules
   - L1/L2/L3 level rules
   - Logical / physical decoupling rules
   - Ownership and responsibility principles

3. **Functional modeling decisions (FUNC)**
   - Split / merge of capabilities
   - Placement of a capability in a zone
   - Creation or deletion of L3
   - Functional scope adjustment

These decisions belong to different areas of competence and must be governed explicitly in order to avoid:
- Model divergence,
- Contradictions between principles and implementations,
- Progressive BCM drift.

## Decision

BCM ADR governance is structured according to an explicit **three-level** hierarchy:

### 1. GOV-level ADRs (Governance)

- Define the **meta-rules** of the BCM decision-making framework itself.
- Scope: cross-cutting, applicable to the entire referential.
- Examples: ADR hierarchy, arbitration board, periodic review.
- Very infrequent, very stable.
- Can only be modified by another GOV ADR.
- Validated by the BCM board or equivalent enterprise architecture body.

### 2. URBA-level ADRs (Urbanization)

- Define the **structuring rules of the BCM model**.
- Scope: cross-cutting, applicable to all capabilities.
- Examples: 7-zone zoning, L1/L2/L3 breakdown, 1 capability = 1 responsibility principle.
- Infrequent, highly stable.
- Can only be modified by another URBA or GOV ADR.
- Validated by enterprise architects.

### 3. FUNC-level ADRs (Functional)

- Apply URBA rules to a **specific functional scope**.
- Explicitly impact one or more capabilities.
- May evolve more frequently.
- Must mandatorily reference applicable URBA ADRs.
- Validated by functional architects or the relevant business teams.

### Classification Rule

| Criterion                          | GOV | URBA | FUNC |
|------------------------------------|-----|------|------|
| Concerns the decision-making framework | ✅  |      |      |
| Concerns the model structure        |     | ✅   |      |
| Concerns a functional scope         |     |      | ✅   |

### Hierarchy Rules

- A FUNC ADR **cannot contradict** a URBA ADR.
- A URBA ADR **cannot contradict** a GOV ADR.
- Every FUNC ADR must include a `related_adr` field pointing to the relevant URBA ADRs.
- The BCM (capabilities.yaml) is modified only following an accepted ADR.

```text
ADR GOV  — Meta-rules of the decision-making framework
  ↓ governs
ADR URBA — Structuring principles of the model
  ↓ constrains
ADR FUNC — Functional modeling decisions
  ↓ materializes
BCM (capabilities.yaml)
```

### Documentary Organization

- All ADRs are stored in a single referential.
- A common template is used.
- The distinction is ensured by the `family` field.

### Evolutivity Clause and Anti-Dogma

The BCM is a living model.

No ADR (GOV, URBA, or FUNC) constitutes an immutable or definitive rule.

To avoid any dogmatic drift:

- Any ADR must be challengeable by a subsequent ADR of the same or higher level.
- A formal challenge mechanism is allowed at the initiative of:
  - a BCM board member,
  - a project team,
  - or an affected business representative.
- GOV and URBA ADRs must undergo a periodic review (minimum every 24 months).

The guiding principle is:

> Model coherence must never take precedence over business value.

The BCM is an alignment tool, not an end in itself.

## Justification

This three-level structure allows:

- Clarifying decision-making responsibilities at each level.
- Separating institutional governance (GOV), urbanization principles (URBA), and operational modeling (FUNC).
- Avoiding conflicts between teams (governance vs. urbanization vs. business).
- Ensuring model coherence over time.
- Enabling model stability governance.

It introduces an explicit analogy:

- GOV ADR = Model Constitution (how decisions are made)
- URBA ADR = Fundamental Laws (the rules of the game)
- FUNC ADR = Implementation Decrees (operational decisions)

### Alternatives Considered

- Non-hierarchical approach (single ADR type) — rejected because it mixes governance, structuring principles, and operational decisions.
- 2-level hierarchy (Structural / Functional) — rejected because it does not explicitly distinguish governance decisions (how decisions are made) from urbanization decisions (model rules).
- Governance centralized solely by urbanization — rejected because it reduces ownership by functional teams.

## Impacts on the BCM

### Structure

- Formalization of a three-level decision hierarchy: GOV → URBA → FUNC.
- Mandatory cross-level traceability via the `related_adr` field.
- Stabilization of governance (GOV) and urbanization (URBA) principles, securing functional evolutions (FUNC).

### Events (if applicable)

- No direct impact on business events.

### Mapping SI / Data / Org

- Impacted applications: cross-cutting governance (SI).
- Impacted flows: decision governance and traceability (DATA/ORG).

## Consequences

### Positive

- Clear governance.
- Explicit responsibilities.
- More robust model.
- Reduced decision conflicts.
- Better auditability of evolutions.

### Negative / Risks

- Increased governance complexity.
- Requires documentary discipline.
- Risk of rigidity if over-formalized.

### Accepted Debt

- Need for team onboarding and acculturation.
- Possible adjustments in practice.

## Governance Indicators

- Criticality level: High (structuring cross-cutting decision).
- Recommended review date: 2028-02-26.
- Expected stability indicator:
  - Number of FUNC ADRs not linked to a URBA ADR = 0.
  - Number of URBA ADRs not linked to a GOV ADR = 0.
  - Any structural modification of the model goes through a URBA or GOV ADR.
  - Each family (GOV, URBA, FUNC) is correctly assigned via the `family` field.

## Traceability

- Workshop: BCM Governance – 2026-02-26
- Participants: EA / Business Architecture
- References:
