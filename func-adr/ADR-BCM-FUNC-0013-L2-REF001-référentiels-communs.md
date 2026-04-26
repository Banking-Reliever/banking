---
id: ADR-BCM-FUNC-0013
title: "L2 Breakdown of CAP.REF.001 — Common Referentials"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - REFERENTIEL

impacted_capabilities:
  - CAP.REF.001
  - CAP.REF.001.BEN
  - CAP.REF.001.PRE
  - CAP.REF.001.PAL

impacted_events:
  - Bénéficiaire.RéférentielMisÀJour
  - Prescripteur.RéférentielMisÀJour
  - Palier.DéfinitionMisÀJour

impacted_mappings:
  - SI
  - DATA
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010
  - ADR-BCM-URBA-0012
  - ADR-BCM-FUNC-0004

supersedes: []

tags:
  - BCM
  - L2
  - REFERENTIEL
  - master-data
  - beneficiary
  - prescriber
  - tier

stability_impact: Structural

domain_classification:
  type: generic
  coordinates:
    x: 0.25
    y: 0.25
  rationale: "MDM et référentiel partagé sont des patterns IS génériques ; le modèle de données reflète Reliever mais la capacité elle-même est de l'infrastructure"
---

# ADR-BCM-FUNC-0013 — L2 Breakdown of CAP.REF.001 — Common Referentials

## Domain Classification

> **Mandatory for FUNC ADRs.** Derived from the product vision and strategic vision — not from technical complexity alone.

| Axis | Score | Interpretation |
|------|-------|----------------|
| x — Business Differentiation | 0.25 | 0.0 = commodity (could be bought off-shelf) → 1.0 = uniquely differentiating |
| y — Model Complexity | 0.25 | 0.0 = trivial / well-understood → 1.0 = proprietary / high cognitive load |

**Classification:** `generic`

**Rationale:**

> MDM et référentiel partagé sont des patterns IS génériques ; le modèle de données reflète Reliever mais la capacité elle-même est de l'infrastructure

---

## Context

CAP.REF.001 holds the reference data shared by all Reliever capabilities. Per ADR-BCM-URBA-0001, master referentials are isolated in the REFERENTIEL zone to avoid duplication and guarantee clear master data governance.

Three canonical business concepts (ADR-BCM-URBA-0012) structure the entire program: the Beneficiary (the individual in remediation), the Prescriber (the actor prescribing the program), and the Tier (the autonomy level with its rules). These three concepts are consumed by all zones — they must have a single canonical definition.

## Decision

CAP.REF.001 is decomposed into **3 L2 capabilities**:

| ID | Name | Responsibility |
|----|------|----------------|
| CAP.REF.001.BEN | Beneficiary Referential | Hold and maintain the canonical beneficiary identity, shared by all capabilities |
| CAP.REF.001.PRE | Prescriber Referential | Hold and maintain the canonical identity of prescribers and their organizations |
| CAP.REF.001.PAL | Tier Referential | Hold and maintain the canonical definitions of tiers, their rules, and their transition thresholds |

### Business Events per L2

| L2 | Events Produced | Primary Consumers |
|----|-----------------|-------------------|
| CAP.REF.001.BEN | `Bénéficiaire.RéférentielMisÀJour` | BSP.002, BSP.003, BSP.004, CAN.001, CAN.002, B2B.001 |
| CAP.REF.001.PRE | `Prescripteur.RéférentielMisÀJour` | BSP.003, CAN.002 |
| CAP.REF.001.PAL | `Palier.DéfinitionMisÀJour` | BSP.001.PAL, BSP.004.AUT, B2B.001.CRT |

### Golden Record Rule

CAP.REF.001.BEN is the single source of truth for a beneficiary's identity. No other capability may maintain its own copy of the beneficiary identity — it must subscribe to `Bénéficiaire.RéférentielMisÀJour`.

CAP.REF.001.PAL is the single source of truth for tier definitions. Any modification of a tier's rules goes through this L2 and triggers `Palier.DéfinitionMisÀJour`, consumed by all capabilities applying tier rules.

### Verifiable Criteria

- Each L2 produces at least one business event (ADR-BCM-URBA-0009)
- No capability outside CAP.REF.001.BEN maintains an authoritative beneficiary identity
- Any modification to a tier definition goes through CAP.REF.001.PAL

## Rationale

The BEN / PRE / PAL separation reflects three distinct master data domains with different lifecycles, sources, and governance. Beneficiary identity is created at enrollment and archived at exit. Prescriber identity is managed by prescriber organizations. Tier definitions are governed by the program itself.

### Alternatives Considered

- **PAL in BSP.001.PAL** — rejected because tier definitions are consumed by multiple capabilities (BSP.001, BSP.004, B2B.001); their ownership in a single CORE L2 would create an ungoverned transverse dependency toward a capability that should be autonomous
- **BEN + PRE merged** — rejected because beneficiaries and prescribers have different lifecycles and sources of truth; their identities do not originate from the same source systems

## BCM Impacts

### Structure

- 3 L2s created under CAP.REF.001
- Capability consumed by almost all other L2s in the program

### SI / Data / Org Mapping

- **DATA**: CAP.REF.001 is the MDM (Master Data Management) of Reliever
- **ORG**: recommended owner: "Data & Referentials" team

## Consequences

### Positive

- Single source of truth for the three canonical concepts of the program
- Evolution of tier definitions without impact on actor identities

### Negative / Risks

- CAP.REF.001.PAL is operationally critical: a tier definition modification has a cascading impact on BSP.001, BSP.004, B2B.001

### Accepted Debt

- The synchronization strategy between REF.001.BEN and external identity sources (banks, hospitals, social services) is not modeled here

## Governance Indicators

- Criticality level: High (data infrastructure of the program)
- Recommended review date: 2028-04-24
- Expected stability indicator: 0 duplicate beneficiary identities between capabilities

## Traceability

- Workshop: BCM Reliever Session — 2026-04-24
- Participants: yremy
- References:
  - ADR-BCM-URBA-0012 — Canonical business concept
  - ADR-BCM-FUNC-0004
