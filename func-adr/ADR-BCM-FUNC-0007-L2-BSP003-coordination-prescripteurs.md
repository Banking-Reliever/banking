---
id: ADR-BCM-FUNC-0007
title: "L2 Breakdown of CAP.BSP.003 — Prescriber Coordination"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - SERVICES_COEUR

impacted_capabilities:
  - CAP.BSP.003
  - CAP.BSP.003.ROL
  - CAP.BSP.003.NOT
  - CAP.BSP.003.COD

impacted_events:
  - PrescripteurRole.Attribué
  - PrescripteurRole.Révoqué
  - Prescripteur.Alerté
  - Override.DemandéParPrescripteur
  - Override.CoValidé
  - Override.Refusé

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

supersedes: []

tags:
  - BCM
  - L2
  - BSP
  - prescribers
  - coordination
  - multi-actor

stability_impact: Moderate

domain_classification:
  type: supporting
  coordinates:
    x: 0.65
    y: 0.6
  rationale: "Coordination multi-acteurs avec droits différenciés spécifique à Reliever, mais coordination et notification restent des patterns IS maîtrisés"
---

# ADR-BCM-FUNC-0007 — L2 Breakdown of CAP.BSP.003 — Prescriber Coordination

## Domain Classification

> **Mandatory for FUNC ADRs.** Derived from the product vision and strategic vision — not from technical complexity alone.

| Axis | Score | Interpretation |
|------|-------|----------------|
| x — Business Differentiation | 0.65 | 0.0 = commodity (could be bought off-shelf) → 1.0 = uniquely differentiating |
| y — Model Complexity | 0.6 | 0.0 = trivial / well-understood → 1.0 = proprietary / high cognitive load |

**Classification:** `supporting`

**Rationale:**

> Coordination multi-acteurs avec droits différenciés spécifique à Reliever, mais coordination et notification restent des patterns IS maîtrisés

---

## Context

CAP.BSP.003 manages the coordination logic between the three types of prescribers (bank, psychiatrist, social worker) acting on the same beneficiary. These actors are heterogeneous in nature (financial, medical, social), have differentiated rights, and may be called upon to co-decide on a tier override.

The key distinction from CAP.CAN.002 (Prescriber Portal): CAP.BSP.003 holds the business coordination rules (who can see what, who can decide what, how to coordinate) — CAP.CAN.002 holds the UX exposure of those rules. This separation is required by ADR-BCM-URBA-0001.

## Decision

CAP.BSP.003 is decomposed into **3 L2 capabilities**:

| ID | Name | Responsibility |
|----|------|----------------|
| CAP.BSP.003.ROL | Role & Rights Management | Define and enforce the differentiated visibility and action perimeters by prescriber type |
| CAP.BSP.003.NOT | Alerts & Notifications | Emit alerts to concerned prescribers upon significant events — relapse, tier crossed, circumvention detected |
| CAP.BSP.003.COD | Co-decision | Orchestrate multi-prescriber coordination to validate or refuse a tier override for a given beneficiary |

### Business Events per L2

| L2 | Events Produced | Events Consumed |
|----|-----------------|-----------------|
| CAP.BSP.003.ROL | `PrescripteurRole.Attribué`, `PrescripteurRole.Révoqué` | `Bénéficiaire.Enrôlé` (BSP.002.ENR) |
| CAP.BSP.003.NOT | `Prescripteur.Alerté` | `Signal.Rechute.Détecté` (BSP.001.SIG), `Palier.FranchiHausse` (BSP.001.PAL), `Palier.Rétrogradé` (BSP.001.PAL), `Enveloppe.NonConsommée` (BSP.004.ENV) |
| CAP.BSP.003.COD | `Override.DemandéParPrescripteur`, `Override.CoValidé`, `Override.Refusé` | `OverrideUX.Déclenché` (CAN.002.ACT) |

### Transfer Points

- **BSP.003.COD → BSP.001.PAL**: a validated override triggers a forced tier transition
- **BSP.001.SIG / PAL → BSP.003.NOT**: significant events from the core domain trigger prescriber alerts
- **CAN.002.ACT → BSP.003.COD**: the prescriber's UX action on the portal triggers the CORE co-decision process

### Data Governance Rule

Cross-visibility between prescribers is constrained by CAP.SUP.001.CON:
- The bank does not see medical or social data
- The psychiatrist only sees behavioral data necessary for their clinical follow-up
- The social worker has a social and budgetary view, not detailed financial data

These rules are defined in CAP.BSP.003.ROL and enforced by CAP.SUP.001.

### Verifiable Criteria

- Each L2 produces at least one business event (ADR-BCM-URBA-0009)
- `Override.DemandéParPrescripteur` is produced exclusively by BSP.003.COD and consumed exclusively by BSP.001.PAL

## Rationale

The ROL / NOT / COD separation reflects three distinct logics: rights governance (static, rarely modified), notifications (reactive, high frequency), and co-decision (event-driven, requiring multi-party orchestration). Conflating them would create an L2 that is too broad with incompatible lifecycles and responsibilities.

### Alternatives Considered

- **NOT absorbed into COD** — rejected because notifications are unilateral events (information); co-decision implies a multi-party workflow with validation; conflating them mixes information and decision
- **ROL in CAP.REF.001** — rejected because prescriber rights are dynamic business rules (a prescriber can be revoked); they are not stable reference data

## BCM Impacts

### Structure

- 3 L2s created under CAP.BSP.003
- CAP.CAN.002 (Prescriber Portal) is the CANAL face of this L1 — explicit dependency

### Events

- 6 business events defined
- `Override.DemandéParPrescripteur` is the key coupling event with BSP.001

### SI / Data / Org Mapping

- **SI**: dependency toward CAP.REF.001.PRE (canonical prescriber identity)
- **ORG**: recommended owner: "Prescriber Relations & Governance" team

## Consequences

### Positive

- The differentiated rights logic is explicitly owned by a dedicated L2
- Co-decision is a first-class L2, traceable and auditable

### Negative / Risks

- The transparency/privacy tension (identified as a risk in the product vision) is partially addressed by ROL but requires fine-grained governance with SUP.001.CON

### Accepted Debt

- The precise visibility rules by role (what exactly a psychiatrist sees vs a bank) are not modeled here — to be formalized in CAP.BSP.003.ROL specifications

## Governance Indicators

- Criticality level: High (dignity/control and privacy tension)
- Recommended review date: 2027-10-24
- Expected stability indicator: visibility rules by role documented and testable

## Traceability

- Workshop: BCM Reliever Session — 2026-04-24
- Participants: yremy
- References:
  - `/strategic-vision/strategic-vision.md` — SC.003
  - ADR-BCM-FUNC-0004
