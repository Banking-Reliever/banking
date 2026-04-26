---
id: ADR-BCM-FUNC-0004
title: "L1 Breakdown of Reliever IS Capabilities across the 7 TOGAF Zones"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L1
  zoning:
    - PILOTAGE
    - SERVICES_COEUR
    - SUPPORT
    - REFERENTIEL
    - ECHANGE_B2B
    - CANAL
    - DATA_ANALYTIQUE

impacted_capabilities:
  - CAP.BSP.001
  - CAP.BSP.002
  - CAP.BSP.003
  - CAP.BSP.004
  - CAP.CAN.001
  - CAP.CAN.002
  - CAP.B2B.001
  - CAP.SUP.001
  - CAP.REF.001
  - CAP.DAT.001
  - CAP.PIL.001

impacted_events: []
impacted_mappings:
  - SI
  - DATA
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0004
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010

supersedes: []

tags:
  - BCM
  - L1
  - Reliever
  - breakdown
  - financial-remediation

stability_impact: Structural

domain_classification:
  type: supporting
  coordinates:
    x: 0.2
    y: 0.3
  rationale: "Décision de structuration IS — aucune différenciation métier directe, nécessaire à la gouvernance urbanistique de l'ensemble des zones TOGAF"
---

# ADR-BCM-FUNC-0004 — L1 Breakdown of Reliever IS Capabilities

## Domain Classification

> **Mandatory for FUNC ADRs.** Derived from the product vision and strategic vision — not from technical complexity alone.

| Axis | Score | Interpretation |
|------|-------|----------------|
| x — Business Differentiation | 0.2 | 0.0 = commodity (could be bought off-shelf) → 1.0 = uniquely differentiating |
| y — Model Complexity | 0.3 | 0.0 = trivial / well-understood → 1.0 = proprietary / high cognitive load |

**Classification:** `supporting`

**Rationale:**

> Décision de structuration IS — aucune différenciation métier directe, nécessaire à la gouvernance urbanistique de l'ensemble des zones TOGAF

---

## Context

Reliever is a tiered financial remediation program, prescribable by a bank, a psychiatrist, or a social worker. It accompanies financially vulnerable individuals from maximum assistance on micro-purchase decisions through to the full restoration of their autonomy, via a dedicated card and a behavioral score coordinated among prescribers through open banking.

The validated service offer is:
> Reliever enables financially vulnerable individuals to progressively regain control of their daily financial lives through a system of increasing autonomy tiers, anchored on a dedicated card and a behavioral score coordinated among prescribers via open banking, even when preserving their dignity is as important as constraining their behaviors.

The IS L1 map must:
- Translate 1:1 the 7 strategic capabilities into zoned IS capabilities
- Add the transverse IS L1s required by the extended TOGAF model (ADR-BCM-URBA-0001) that are absent from the strategic map
- Respect the principle of 1 capability = 1 responsibility (ADR-BCM-URBA-0009)
- Assign each L1 to one of the 7 zones (ADR-BCM-URBA-0001)

## Decision

The Reliever IS L1 map is structured into **11 capabilities** distributed across **6 of the 7 TOGAF zones**.

### SERVICES_COEUR — Reliever Core Business

| ID | Name | Responsibility | Strategic Source |
|----|------|----------------|------------------|
| CAP.BSP.001 | Behavioral Remediation | Continuously evaluate the beneficiary's financial trajectory, steer their autonomy tiers, detect relapses and progressions | SC.001 |
| CAP.BSP.002 | Access & Enrollment | Identify eligible individuals, orchestrate their entry into the program with prescribers, formalize the terms of care | SC.002 |
| CAP.BSP.003 | Prescriber Coordination | Enable the bank, psychiatrist, and social worker to act in a coordinated way on the same beneficiary, with differentiated rights and views | SC.003 |
| CAP.BSP.004 | Transaction Control | Apply the rules of the current tier to each purchase act, manage authorizations in real time, feed the behavioral score | SC.004 |

### CANAL — User Exposure

| ID | Name | Responsibility | Strategic Source |
|----|------|----------------|------------------|
| CAP.CAN.001 | Beneficiary Journey | Expose to the beneficiary the gamified visualization of their progression, purchase assistance, and notifications | SC.005 |
| CAP.CAN.002 | Prescriber Portal | Offer prescribers a role-adapted UX to consult situations and trigger actions | Transverse (CANAL exposure of SC.003) |

### ECHANGE_B2B — External Financial Ecosystem

| ID | Name | Responsibility | Strategic Source |
|----|------|----------------|------------------|
| CAP.B2B.001 | Financial Instrument Management | Issue and manage the dedicated card, link its rules to the tiers, access financial data via open banking | SC.006 |

### SUPPORT — Transverse IS Functions

| ID | Name | Responsibility | Strategic Source |
|----|------|----------------|------------------|
| CAP.SUP.001 | Data Compliance & Protection | Ensure the legality of sensitive data sharing among heterogeneous actors, guarantee regulatory obligations | SC.007 |

### REFERENTIEL — Shared Master Data

| ID | Name | Responsibility | Strategic Source |
|----|------|----------------|------------------|
| CAP.REF.001 | Common Referentials | Hold the canonical identities of the Beneficiary, the Prescriber, and the Tier definitions, consumed by all zones | Transverse TOGAF |

### DATA_ANALYTIQUE — Analytics and Data Steering

| ID | Name | Responsibility | Strategic Source |
|----|------|----------------|------------------|
| CAP.DAT.001 | Behavioral Analytics | Ingest behavioral events, feed and improve the analytical score model, produce program reports | Transverse TOGAF |

### PILOTAGE — Governance and Steering

| ID | Name | Responsibility | Strategic Source |
|----|------|----------------|------------------|
| CAP.PIL.001 | Program Steering | Govern the remediation program, measure its effectiveness, ensure regulatory compliance at scale | Transverse TOGAF |

### Disambiguation Rules

- **CAP.BSP.003** (coordination logic) ≠ **CAP.CAN.002** (prescriber UX portal): the rights and co-decision logic remains in CORE; the exposure remains in CANAL — per ADR-BCM-URBA-0001
- **CAP.BSP.001** (real-time operational scoring) ≠ **CAP.DAT.001** (batch/stream analytical model): the transactional score is CORE; model improvement and reporting are DATA_ANALYTIQUE
- **CAP.SUP.001** (transverse IS compliance) ≠ **CAP.PIL.001** (business program steering): SUP covers GDPR, audit, rights; PIL covers governance, KPIs, program regulatory compliance

### Verifiable Criteria

- Every L1 capability is assigned to exactly one of the 7 TOGAF zones
- No L1 is named after an application, vendor, or technology
- Each L1 is decomposable into L2s without scope overlap
- The entire service offer is covered by at least one L1

## Rationale

The 1:1 translation of the 7 strategic capabilities into zoned IS L1s guarantees direct traceability between the business vision and the IS map. The 4 transverse IS L1s added (CAP.CAN.002, CAP.REF.001, CAP.DAT.001, CAP.PIL.001) are required by the extended TOGAF model (ADR-BCM-URBA-0001): they address structural IS concerns absent from a purely strategic map.

### Alternatives Considered

- **Grouping everything into SERVICES_COEUR** — rejected because it loses the CORE/CANAL separation (confusion between coordination logic and prescriber UX), erases data governance, and harms urbanization readability
- **Separating Scoring and Tiers into two distinct L1s** — rejected because they share the same responsibility domain (behavioral remediation) and their coupling is inherent to the MMR model; the separation belongs at L2

## BCM Impacts

### Structure

- 11 L1 capabilities created across 6 zones
- Zone ECHANGE_B2B covered by 1 single L1 (financial instrument): acceptable at this stage, the open banking perimeter is bounded
- Each L1 will be decomposed into L2s by ADRs FUNC-0005 through FUNC-0015

### Events

- Business events will be defined at the L2 level (ADR-BCM-URBA-0009)

### SI / Data / Org Mapping

- **SI**: each L1 constitutes a functional domain to which application components will be mapped
- **ORG**: each L1 has a business owner to be identified during the organization phase
- **DATA**: inter-L1 flows will be formalized during the L2 ADRs

## Consequences

### Positive

- Readable, zoned IS map, traceable from the service offer
- Clear separation CORE / CANAL / B2B / SUPPORT / REF / DAT / PIL
- Stable base for the 11 following L2 ADRs

### Negative / Risks

- 11 L1s is at the upper bound of readability (ADR-BCM-URBA-0004 recommends ~10 max per zone) — acceptable as they are distributed across 6 zones, not 1
- The PILOTAGE zone contains only a single L1: to be monitored during stability reviews

### Accepted Debt

- Organizational owners per L1 have not yet been identified — to be completed during the organization phase

## Governance Indicators

- Criticality level: High (structural decision for Reliever)
- Recommended review date: 2028-04-24
- Expected stability indicator: 11 L1s present in capabilities.yaml with zone and owner populated

## Traceability

- Workshop: BCM Reliever Session — 2026-04-24
- Participants: yremy
- References:
  - `/product-vision/product.md`
  - `/strategic-vision/strategic-vision.md`
  - ADR-BCM-URBA-0001 — Extended TOGAF Zoning
  - ADR-BCM-URBA-0009 — Complete capability definition
  - ADR-BCM-URBA-0010 — L2 urbanization pivot
