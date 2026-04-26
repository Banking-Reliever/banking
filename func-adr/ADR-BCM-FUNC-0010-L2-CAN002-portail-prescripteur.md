---
id: ADR-BCM-FUNC-0010
title: "L2 Breakdown of CAP.CAN.002 — Prescriber Portal"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - CANAL

impacted_capabilities:
  - CAP.CAN.002
  - CAP.CAN.002.VUE
  - CAP.CAN.002.ACT
  - CAP.CAN.002.RAP

impacted_events:
  - DossierBénéficiaire.Consulté
  - OverrideUX.Déclenché
  - Rapport.Généré

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
  - ADR-BCM-FUNC-0007

supersedes: []

tags:
  - BCM
  - L2
  - CANAL
  - prescribers
  - portal
  - UX

stability_impact: Moderate

domain_classification:
  type: supporting
  coordinates:
    x: 0.4
    y: 0.35
  rationale: "Portail web standard avec contenu Reliever-spécifique ; la différenciation est dans le modèle de droits (BSP.003), non dans la capacité de canal"
---

# ADR-BCM-FUNC-0010 — L2 Breakdown of CAP.CAN.002 — Prescriber Portal

## Domain Classification

> **Mandatory for FUNC ADRs.** Derived from the product vision and strategic vision — not from technical complexity alone.

| Axis | Score | Interpretation |
|------|-------|----------------|
| x — Business Differentiation | 0.4 | 0.0 = commodity (could be bought off-shelf) → 1.0 = uniquely differentiating |
| y — Model Complexity | 0.35 | 0.0 = trivial / well-understood → 1.0 = proprietary / high cognitive load |

**Classification:** `supporting`

**Rationale:**

> Portail web standard avec contenu Reliever-spécifique ; la différenciation est dans le modèle de droits (BSP.003), non dans la capacité de canal

---

## Context

CAP.CAN.002 is the CANAL exposure of the program toward prescribers (bank, psychiatrist, social worker). It complements CAP.BSP.003 (Prescriber Coordination), which holds the business logic; CAP.CAN.002 holds the interface through which prescribers exercise their rights.

Per ADR-BCM-URBA-0001, the coordination logic (rules, rights, co-decision) remains in SERVICES_COEUR (BSP.003); the UX is here in CANAL.

Each type of prescriber sees an interface adapted to their role, filtered by the rights defined in CAP.BSP.003.ROL. The portal is the contact surface between the medico-social world and the financial program.

## Decision

CAP.CAN.002 is decomposed into **3 L2 capabilities**:

| ID | Name | Responsibility |
|----|------|----------------|
| CAP.CAN.002.VUE | Beneficiary View | Expose to each prescriber a role-adapted view of the beneficiary's situation and trajectory |
| CAP.CAN.002.ACT | Prescriber Actions | Provide the UX enabling a prescriber to trigger an override, validate a co-decision, or annotate a beneficiary situation |
| CAP.CAN.002.RAP | Reports & Exports | Allow prescribers to generate follow-up reports adapted to their context (clinical report, social report, banking report) |

### Business Events per L2

| L2 | Events Produced | Events Consumed |
|----|-----------------|-----------------|
| CAP.CAN.002.VUE | `DossierBénéficiaire.Consulté` | `ScoreComportemental.Recalculé` (BSP.001.SCO), `Palier.FranchiHausse` (BSP.001.PAL), `Signal.Rechute.Détecté` (BSP.001.SIG), `PrescripteurRole.Attribué` (BSP.003.ROL) |
| CAP.CAN.002.ACT | `OverrideUX.Déclenché` | `Override.CoValidé` (BSP.003.COD), `Override.Refusé` (BSP.003.COD) |
| CAP.CAN.002.RAP | `Rapport.Généré` | `DossierBénéficiaire.Consulté` (CAN.002.VUE) |

### Filtered Visibility Rule

CAP.CAN.002.VUE applies the rights filters defined by CAP.BSP.003.ROL: a psychiatrist does not see banking transaction details; a bank does not see clinical annotations. This rule is enforced at the CANAL level (display) AND at the CORE level (data transmitted).

### Verifiable Criteria

- Each L2 produces at least one business event (ADR-BCM-URBA-0009)
- `OverrideUX.Déclenché` is produced exclusively by CAN.002.ACT and consumed exclusively by BSP.003.COD

## Rationale

The VUE / ACT / RAP separation reflects three distinct prescriber interaction modes: consultation (read), action (write/decide), and reporting (export). These three modes have different rights, frequencies, and constraints.

### Alternatives Considered

- **VUE + ACT merged** — rejected because some prescribers have read rights without action rights (e.g., a social worker can consult without being able to trigger an override); the separation enables fine-grained rights governance
- **RAP in CAP.DAT.001** — rejected because prescriber reports are operational exports adapted to each business role; global program reports belong to DATA_ANALYTIQUE, but individual reports are a CANAL responsibility

## BCM Impacts

### Structure

- 3 L2s created under CAP.CAN.002
- Strong dependency toward CAP.BSP.003 (logic) and CAP.REF.001.PRE (prescriber identity)

### SI / Data / Org Mapping

- **SI**: web portal or desktop application for professional prescribers
- **ORG**: recommended owner: "Prescriber Experience" team

## Consequences

### Positive

- Prescriber UX is an explicit responsibility, not a function hidden in the CORE
- Role-filtered visibility is traced at two levels (CORE + CANAL)

### Negative / Risks

- The multiplicity of prescriber types (bank, psychiatrist, social worker) may complicate the development of CAP.CAN.002.VUE — monitor for UX scope creep

### Accepted Debt

- The mockups and UX rules specific to each prescriber type are not modeled here

## Governance Indicators

- Criticality level: Moderate
- Recommended review date: 2028-04-24
- Expected stability indicator: 3 prescriber profiles (bank, psychiatrist, social worker) with distinct documented views

## Traceability

- Workshop: BCM Reliever Session — 2026-04-24
- Participants: yremy
- References:
  - `/strategic-vision/strategic-vision.md` — SC.003
  - ADR-BCM-FUNC-0007
