---
id: ADR-BCM-FUNC-0014
title: "L2 Breakdown of CAP.DAT.001 — Behavioral Analytics"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - DATA_ANALYTIQUE

impacted_capabilities:
  - CAP.DAT.001
  - CAP.DAT.001.ING
  - CAP.DAT.001.MOD
  - CAP.DAT.001.REP

impacted_events:
  - DonnéesComportementales.Ingérées
  - ModèleScore.MisÀJour
  - RapportProgramme.Généré

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
  - ADR-BCM-FUNC-0004
  - ADR-BCM-FUNC-0005

supersedes: []

tags:
  - BCM
  - L2
  - DATA_ANALYTIQUE
  - scoring
  - analytics
  - BI

stability_impact: Moderate

domain_classification:
  type: supporting
  coordinates:
    x: 0.55
    y: 0.55
  rationale: "Analytique comportementale nécessaire pour améliorer le scoring dans le temps ; pattern analytique connu mais les données et modèles sont propriétaires"
---

# ADR-BCM-FUNC-0014 — L2 Breakdown of CAP.DAT.001 — Behavioral Analytics

## Domain Classification

> **Mandatory for FUNC ADRs.** Derived from the product vision and strategic vision — not from technical complexity alone.

| Axis | Score | Interpretation |
|------|-------|----------------|
| x — Business Differentiation | 0.55 | 0.0 = commodity (could be bought off-shelf) → 1.0 = uniquely differentiating |
| y — Model Complexity | 0.55 | 0.0 = trivial / well-understood → 1.0 = proprietary / high cognitive load |

**Classification:** `supporting`

**Rationale:**

> Analytique comportementale nécessaire pour améliorer le scoring dans le temps ; pattern analytique connu mais les données et modèles sont propriétaires

---

## Context

CAP.DAT.001 is the continuous improvement capability of the Reliever program. It differs from CAP.BSP.001 (Behavioral Remediation) on one key point: BSP.001 calculates the operational score in real time for each transaction; DAT.001 analyzes aggregated behavioral patterns to improve the score model over time.

Per ADR-BCM-URBA-0001, analytical flows (decoupled, batch/stream) are DATA_ANALYTIQUE; operational transactional flows are SERVICES_COEUR. This separation is fundamental to avoid coupling the real-time decision engine with learning and reporting processes.

## Decision

CAP.DAT.001 is decomposed into **3 L2 capabilities**:

| ID | Name | Responsibility |
|----|------|----------------|
| CAP.DAT.001.ING | Event Ingestion | Collect and consolidate behavioral events produced by the entire program to feed the analytical pipelines |
| CAP.DAT.001.MOD | Analytical Score Model | Analyze aggregated behavioral patterns, improve the score model, and propose evolutions of tier thresholds |
| CAP.DAT.001.REP | Program Reporting | Produce dashboards and follow-up reports on the overall effectiveness of the remediation program |

### Business Events per L2

| L2 | Events Produced | Events Consumed |
|----|-----------------|-----------------|
| CAP.DAT.001.ING | `DonnéesComportementales.Ingérées` | All business events from the program (BSP.001, BSP.002, BSP.003, BSP.004) in decoupled analytical mode |
| CAP.DAT.001.MOD | `ModèleScore.MisÀJour` | `DonnéesComportementales.Ingérées` (DAT.001.ING) |
| CAP.DAT.001.REP | `RapportProgramme.Généré` | `DonnéesComportementales.Ingérées` (DAT.001.ING), `ModèleScore.MisÀJour` (DAT.001.MOD) |

### Analytics/Operational Separation Rule

`ModèleScore.MisÀJour` produced by DAT.001.MOD is consumed by CAP.PIL.001 (program governance decision) but **not directly by BSP.001.SCO**. The operational scoring model is updated in a controlled manner, after validation — never in a direct flow from analytics. This rule prevents uncontrolled feedback between analytics and operations.

### Verifiable Criteria

- Each L2 produces at least one business event (ADR-BCM-URBA-0009)
- DAT.001 does not produce events consumed in real time by BSP.004.AUT (analytics/transactional separation)

## Rationale

The ING / MOD / REP separation reflects three stages of the analytical pipeline with distinct rhythms and responsibilities. Ingestion is continuous (near real-time). Model improvement is periodic (monthly, quarterly). Reporting is on-demand or scheduled.

### Alternatives Considered

- **MOD in BSP.001.SCO** — rejected because model improvement is an offline analytical process with human validation; operational scoring is real-time without human intervention; conflating them would create a risk of uncontrolled model drift
- **REP in CAP.PIL.001** — rejected because producing reporting data is DATA_ANALYTIQUE (ingestion, transformation, aggregation); consuming that data for governance decisions is PILOTAGE

## BCM Impacts

### Structure

- 3 L2s created under CAP.DAT.001
- Consumes events from the entire program in decoupled mode

### SI / Data / Org Mapping

- **DATA**: analytical pipeline separate from the transactional pipeline
- **ORG**: recommended owner: "Data Science & BI" team

## Consequences

### Positive

- Continuous improvement of the score model without risk of feedback on the operational system
- Program reporting available for governance decisions

### Negative / Risks

- The boundary between the operational model (BSP.001.SCO) and the analytical model (DAT.001.MOD) requires a controlled deployment procedure

### Accepted Debt

- The ingestion pipeline and analytical technologies are not modeled here

## Governance Indicators

- Criticality level: Moderate
- Recommended review date: 2028-04-24
- Expected stability indicator: score model versioned with documented history of evolutions

## Traceability

- Workshop: BCM Reliever Session — 2026-04-24
- Participants: yremy
- References:
  - ADR-BCM-URBA-0001 — DATA_ANALYTIQUE / SERVICES_COEUR separation
  - ADR-BCM-FUNC-0004, ADR-BCM-FUNC-0005
