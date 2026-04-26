---
id: ADR-BCM-FUNC-0009
title: "L2 Breakdown of CAP.CAN.001 — Beneficiary Journey"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - CANAL

impacted_capabilities:
  - CAP.CAN.001
  - CAP.CAN.001.TAB
  - CAP.CAN.001.ACH
  - CAP.CAN.001.NOT

impacted_events:
  - TableauDeBord.Consulté
  - ScanProduit.Lancé
  - Alternative.Acceptée
  - NotificationBénéficiaire.Émise

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
  - ADR-BCM-FUNC-0005

supersedes: []

tags:
  - BCM
  - L2
  - CANAL
  - UX
  - beneficiary
  - gamification

stability_impact: Moderate

domain_classification:
  type: supporting
  coordinates:
    x: 0.45
    y: 0.35
  rationale: "Canal mobile standard ; la valeur différenciante provient du cœur IS (BSP.001), pas du canal bénéficiaire lui-même"
---

# ADR-BCM-FUNC-0009 — L2 Breakdown of CAP.CAN.001 — Beneficiary Journey

## Domain Classification

> **Mandatory for FUNC ADRs.** Derived from the product vision and strategic vision — not from technical complexity alone.

| Axis | Score | Interpretation |
|------|-------|----------------|
| x — Business Differentiation | 0.45 | 0.0 = commodity (could be bought off-shelf) → 1.0 = uniquely differentiating |
| y — Model Complexity | 0.35 | 0.0 = trivial / well-understood → 1.0 = proprietary / high cognitive load |

**Classification:** `supporting`

**Rationale:**

> Canal mobile standard ; la valeur différenciante provient du cœur IS (BSP.001), pas du canal bénéficiaire lui-même

---

## Context

CAP.CAN.001 is the CANAL exposure of the Reliever program toward the beneficiary. It is the direct point of contact with the end user — the person whose dignity is the primary functional constraint of the service offer.

This L1 addresses the control/dignity tension identified as the most critical in the product vision: the beneficiary experience must be perceived as motivating support (Strava model), not as punitive surveillance. Gamification is not an ornament — it is a functional requirement.

Per ADR-BCM-URBA-0001, CAP.CAN.001 holds the UX and exposure; business rules (score, tiers, alternatives) remain in SERVICES_COEUR.

## Decision

CAP.CAN.001 is decomposed into **3 L2 capabilities**:

| ID | Name | Responsibility |
|----|------|----------------|
| CAP.CAN.001.TAB | Progression Dashboard | Expose to the beneficiary the gamified visualization of their progression, available budget, and tier trajectory |
| CAP.CAN.001.ACH | Purchase Assistance | Provide the UX at the moment of purchase — product scan, display of the alternative proposed by BSP.004.ALT, authorization or refusal feedback |
| CAP.CAN.001.NOT | Beneficiary Notifications | Emit push/SMS notifications to the beneficiary upon key events — refusal, tier crossed, budget close, relapse |

### Business Events per L2

| L2 | Events Produced | Events Consumed |
|----|-----------------|-----------------|
| CAP.CAN.001.TAB | `TableauDeBord.Consulté` | `ScoreComportemental.Recalculé` (BSP.001.SCO), `Palier.FranchiHausse` (BSP.001.PAL), `Enveloppe.Consommée` (BSP.004.ENV) |
| CAP.CAN.001.ACH | `ScanProduit.Lancé`, `Alternative.Acceptée` | `Transaction.Autorisée` (BSP.004.AUT), `Transaction.Refusée` (BSP.004.AUT), `Alternative.Proposée` (BSP.004.ALT) |
| CAP.CAN.001.NOT | `NotificationBénéficiaire.Émise` | `Transaction.Refusée` (BSP.004.AUT), `Palier.FranchiHausse` (BSP.001.PAL), `Enveloppe.Épuisée` (BSP.004.ENV), `Bénéficiaire.TransféréVersAppliStandard` (BSP.002.SOR) |

### Dignity Rule

CAP.CAN.001.TAB must expose progression positively (what has been accomplished) before restrictions (what is forbidden). A purchase refusal must be accompanied by a reasoned explanation and an alternative when available. These UX rules are the responsibility of this L2, not of the CORE.

### Verifiable Criteria

- Each L2 produces at least one business event (ADR-BCM-URBA-0009)
- CAP.CAN.001 contains no tier or scoring business rules — it consumes events and displays states

## Rationale

The TAB / ACH / NOT separation reflects three distinct interaction moments: proactive consultation (dashboard), real-time interaction (purchase act), and push communication (notifications). These three moments have different UX constraints and lifecycles.

### Alternatives Considered

- **TAB + NOT merged** — rejected because the dashboard is a pull consultation (user-initiated); notifications are push (system-initiated); conflating these two interaction logics harms clarity of responsibility
- **ACH in BSP.004.ALT** — rejected because the scan and display UX is a CANAL responsibility (presentation, feedback, accessibility); the suggestion logic remains in CORE

## BCM Impacts

### Structure

- 3 L2s created under CAP.CAN.001
- Intensively consumes events from BSP.001, BSP.002, BSP.004

### SI / Data / Org Mapping

- **SI**: CAP.CAN.001 is typically a mobile application or webapp — SI mapping toward BSP.001, BSP.004 via API or event subscription
- **ORG**: recommended owner: "Beneficiary Experience" team

## Consequences

### Positive

- The dignity/control tension is addressed by a dedicated CANAL capability with explicit UX rules
- Purchase assistance is a first-class L2 — not an afterthought

### Negative / Risks

- CAP.CAN.001.ACH is dependent on BSP.004.AUT latency — any authorization slowness translates into UX friction at the point of sale

### Accepted Debt

- The precise gamification rules (badges, milestones, potential social comparisons) are not modeled here

## Governance Indicators

- Criticality level: High (dignity/control tension)
- Recommended review date: 2028-04-24
- Expected stability indicator: dignity UX rules documented and testable (user testing)

## Traceability

- Workshop: BCM Reliever Session — 2026-04-24
- Participants: yremy
- References:
  - `/strategic-vision/strategic-vision.md` — SC.005
  - ADR-BCM-FUNC-0004, ADR-BCM-FUNC-0008
