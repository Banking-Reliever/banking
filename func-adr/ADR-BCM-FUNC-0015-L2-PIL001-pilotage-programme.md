---
id: ADR-BCM-FUNC-0015
title: "L2 Breakdown of CAP.PIL.001 — Program Steering"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - PILOTAGE

impacted_capabilities:
  - CAP.PIL.001
  - CAP.PIL.001.GOV
  - CAP.PIL.001.KPI
  - CAP.PIL.001.AUD

impacted_events:
  - PolitiqueGouvernance.MisÀJour
  - PerformanceProgramme.Évaluée
  - ConformitéProgramme.Vérifiée

impacted_mappings:
  - SI
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010
  - ADR-BCM-FUNC-0004
  - ADR-BCM-FUNC-0014

supersedes: []

tags:
  - BCM
  - L2
  - PILOTAGE
  - governance
  - KPI
  - program-compliance

stability_impact: Moderate

domain_classification:
  type: generic
  coordinates:
    x: 0.2
    y: 0.25
  rationale: "Pilotage et KPIs suivent des patterns de gouvernance standard sans différenciation compétitive"
---

# ADR-BCM-FUNC-0015 — L2 Breakdown of CAP.PIL.001 — Program Steering

## Domain Classification

> **Mandatory for FUNC ADRs.** Derived from the product vision and strategic vision — not from technical complexity alone.

| Axis | Score | Interpretation |
|------|-------|----------------|
| x — Business Differentiation | 0.2 | 0.0 = commodity (could be bought off-shelf) → 1.0 = uniquely differentiating |
| y — Model Complexity | 0.25 | 0.0 = trivial / well-understood → 1.0 = proprietary / high cognitive load |

**Classification:** `generic`

**Rationale:**

> Pilotage et KPIs suivent des patterns de gouvernance standard sans différenciation compétitive

---

## Context

CAP.PIL.001 steers the Reliever remediation program at scale — beyond the individual follow-up of a beneficiary. It answers the question: "Is the program effective? Is it compliant? Should the rules evolve?"

Per ADR-BCM-URBA-0001, the PILOTAGE zone holds enterprise steering, compliance, and governance capabilities. CAP.PIL.001 is distinct from CAP.SUP.001 (transverse IS compliance): PIL.001 steers the program's overall regulatory compliance; SUP.001 guarantees data compliance at the technical level.

## Decision

CAP.PIL.001 is decomposed into **3 L2 capabilities**:

| ID | Name | Responsibility |
|----|------|----------------|
| CAP.PIL.001.GOV | Program Governance | Define and evolve the program's governance policies — eligibility rules, tier thresholds, co-decision protocols |
| CAP.PIL.001.KPI | Performance Monitoring | Measure the program's effectiveness at scale — progression rate, relapse rate, exit rate, perceived dignity |
| CAP.PIL.001.AUD | Program Compliance Audit | Verify the program's overall regulatory compliance (respect of banking, medical, and social frameworks) |

### Business Events per L2

| L2 | Events Produced | Events Consumed |
|----|-----------------|-----------------|
| CAP.PIL.001.GOV | `PolitiqueGouvernance.MisÀJour` | `ModèleScore.MisÀJour` (DAT.001.MOD) — to validate model evolutions before deployment |
| CAP.PIL.001.KPI | `PerformanceProgramme.Évaluée` | `RapportProgramme.Généré` (DAT.001.REP) |
| CAP.PIL.001.AUD | `ConformitéProgramme.Vérifiée` | `AccèsDonnées.Journalisé` (SUP.001.AUD), `ConformitéProgramme.Vérifiée` — periodic audit cycle |

### Model Evolution Validation Rule

Any score model update (DAT.001.MOD → `ModèleScore.MisÀJour`) must be validated by CAP.PIL.001.GOV before production deployment. This validation produces `PolitiqueGouvernance.MisÀJour`, which authorizes BSP.001 to adopt the new model. This rule prevents ungoverned algorithmic drift.

### Verifiable Criteria

- Each L2 produces at least one business event (ADR-BCM-URBA-0009)
- No score model deployment without a prior `PolitiqueGouvernance.MisÀJour`

## Rationale

The GOV / KPI / AUD separation reflects three distinct steering levels: governance is normative (defines rules), KPIs are descriptive (measures results), audit is probative (certifies compliance). These three activities have different actors, frequencies, and audiences.

### Alternatives Considered

- **KPI in CAP.DAT.001.REP** — rejected because program performance measurement is a steering decision (which indicators, which thresholds, which interpretation); producing the underlying data is DATA_ANALYTIQUE, but the evaluation decision is PILOTAGE
- **AUD in CAP.SUP.001** — rejected because SUP.001 audits data accesses at the technical level (GDPR); PIL.001.AUD audits the program's overall regulatory compliance (banking, medical, social frameworks) — these are two distinct audit levels with different actors (DPO vs Program Compliance Officer)

## BCM Impacts

### Structure

- 3 L2s created under CAP.PIL.001
- Validation role over score model evolution (chain DAT.001 → PIL.001.GOV → BSP.001)

### SI / Data / Org Mapping

- **ORG**: recommended owner: Reliever Program Director / Compliance Officer

## Consequences

### Positive

- Algorithmic governance is first-class — no model drift without validation
- Regulatory audit is distinct from technical audit

### Negative / Risks

- PIL.001.GOV creates a human dependency in the model deployment chain — potential latency

### Accepted Debt

- The precise program KPIs (acceptable progression rate, definition of "success") are not modeled here

## Governance Indicators

- Criticality level: Moderate
- Recommended review date: 2028-04-24
- Expected stability indicator: 100% of model evolutions validated by PIL.001.GOV before deployment

## Traceability

- Workshop: BCM Reliever Session — 2026-04-24
- Participants: yremy
- References:
  - ADR-BCM-FUNC-0004, ADR-BCM-FUNC-0014
