---
id: ADR-BCM-FUNC-0006
title: "L2 Breakdown of CAP.BSP.002 — Access & Enrollment"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - SERVICES_COEUR

impacted_capabilities:
  - CAP.BSP.002
  - CAP.BSP.002.ELI
  - CAP.BSP.002.ENR
  - CAP.BSP.002.CYC
  - CAP.BSP.002.SOR

impacted_events:
  - Bénéficiaire.IdentifiéÉligible
  - Bénéficiaire.EligibilitéRefusée
  - Bénéficiaire.Enrôlé
  - Bénéficiaire.PalierInitialActivé
  - Bénéficiaire.Suspendu
  - Bénéficiaire.Réactivé
  - Bénéficiaire.SortiDuDispositif
  - Bénéficiaire.TransféréVersAppliStandard

impacted_mappings:
  - SI
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010
  - ADR-BCM-FUNC-0004

supersedes: []

tags:
  - BCM
  - L2
  - BSP
  - enrollment
  - lifecycle

stability_impact: Moderate

domain_classification:
  type: supporting
  coordinates:
    x: 0.55
    y: 0.5
  rationale: "Enrôlement prescripteur-spécifique avec règles Reliever propres, mais le pattern lifecycle/onboarding est un problème IS connu et maîtrisé"
---

# ADR-BCM-FUNC-0006 — L2 Breakdown of CAP.BSP.002 — Access & Enrollment

## Domain Classification

> **Mandatory for FUNC ADRs.** Derived from the product vision and strategic vision — not from technical complexity alone.

| Axis | Score | Interpretation |
|------|-------|----------------|
| x — Business Differentiation | 0.55 | 0.0 = commodity (could be bought off-shelf) → 1.0 = uniquely differentiating |
| y — Model Complexity | 0.5 | 0.0 = trivial / well-understood → 1.0 = proprietary / high cognitive load |

**Classification:** `supporting`

**Rationale:**

> Enrôlement prescripteur-spécifique avec règles Reliever propres, mais le pattern lifecycle/onboarding est un problème IS connu et maîtrisé

---

## Context

CAP.BSP.002 manages the entry of individuals into the Reliever program and their lifecycle through to exit. Without this capability, no beneficiary can be activated in the program, regardless of the prescription channel (bank, psychiatrist, social worker).

This L1 covers three temporally distinct phases: eligibility qualification, formal enrollment, and lifecycle management through to program exit. Exit at the final tier is a key event: it triggers the switchover to a standard banking application.

## Decision

CAP.BSP.002 is decomposed into **4 L2 capabilities**:

| ID | Name | Responsibility |
|----|------|----------------|
| CAP.BSP.002.ELI | Eligibility Qualification | Qualify an individual as eligible for the program on banking, medical, or social prescription |
| CAP.BSP.002.ENR | Enrollment | Formalize entry into the program, activate the initial tier, open access rights |
| CAP.BSP.002.CYC | Beneficiary Lifecycle | Manage the active / suspended / exited states and the transitions between them |
| CAP.BSP.002.SOR | Program Exit | Orchestrate the beneficiary's exit — final tier reached or program termination |

### Business Events per L2

| L2 | Events Produced | Events Consumed |
|----|-----------------|-----------------|
| CAP.BSP.002.ELI | `Bénéficiaire.IdentifiéÉligible`, `Bénéficiaire.EligibilitéRefusée` | `Override.DemandéParPrescripteur` (BSP.003.COD) to force eligibility |
| CAP.BSP.002.ENR | `Bénéficiaire.Enrôlé`, `Bénéficiaire.PalierInitialActivé` | `Bénéficiaire.IdentifiéÉligible` (BSP.002.ELI) |
| CAP.BSP.002.CYC | `Bénéficiaire.Suspendu`, `Bénéficiaire.Réactivé` | `Bénéficiaire.Enrôlé` (BSP.002.ENR), `Signal.Rechute.Détecté` (BSP.001.SIG) |
| CAP.BSP.002.SOR | `Bénéficiaire.SortiDuDispositif`, `Bénéficiaire.TransféréVersAppliStandard` | `Palier.FranchiHausse` (BSP.001.PAL) — final tier reached |

### Transfer Points

- **ELI → ENR**: validated eligibility triggers formal enrollment
- **ENR → BSP.001.PAL**: enrollment activates the initial tier in behavioral remediation
- **BSP.001.PAL → SOR**: reaching the final tier triggers program exit

### Verifiable Criteria

- Each L2 produces at least one business event (ADR-BCM-URBA-0009)
- `Bénéficiaire.TransféréVersAppliStandard` is the terminal event of the program — no capability produces an event after it except CAP.REF.001 for archiving

## Rationale

The ELI / ENR / CYC / SOR separation reflects distinct business phases with different rules, actors, and rhythms. Eligibility can be re-evaluated without triggering a new enrollment. Lifecycle management is continuous; exit is a one-time irreversible event (within Reliever).

### Alternatives Considered

- **ELI + ENR merged** — rejected because eligibility can be validated by a prescriber without enrollment being immediate (consent delay, file assembly)
- **SOR absorbed into CYC** — rejected because program exit triggers specific actions (application switchover, archiving) that have their own logic and are not a simple state transition

## BCM Impacts

### Structure

- 4 L2s created under CAP.BSP.002
- No L3 needed

### Events

- 8 business events defined
- `Bénéficiaire.TransféréVersAppliStandard` is consumed by CAP.CAN.001 (UX switchover)

### SI / Data / Org Mapping

- **SI**: dependency toward CAP.REF.001.BEN (canonical beneficiary identity)
- **ORG**: recommended owner: "Access & Prescriber Relations" team

## Consequences

### Positive

- Beneficiary lifecycle fully traceable via events
- Program exit is a first-class event, not a silent state

### Negative / Risks

- Consent management (GDPR) is in tension between BSP.002.ENR and CAP.SUP.001.CON — the rule is: ENR triggers the consent request, SUP.001.CON owns it

### Accepted Debt

- The precise eligibility rules (financial vulnerability criteria) are not modeled here — to be formalized in business specifications

## Governance Indicators

- Criticality level: High
- Recommended review date: 2028-04-24
- Expected stability indicator: event chain ELI → ENR → SOR complete and traceable in the repository

## Traceability

- Workshop: BCM Reliever Session — 2026-04-24
- Participants: yremy
- References:
  - `/strategic-vision/strategic-vision.md` — SC.002
  - ADR-BCM-FUNC-0004, ADR-BCM-FUNC-0005
