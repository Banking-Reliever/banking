---
id: ADR-BCM-FUNC-0008
title: "L2 Breakdown of CAP.BSP.004 — Transaction Control"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - SERVICES_COEUR

impacted_capabilities:
  - CAP.BSP.004
  - CAP.BSP.004.AUT
  - CAP.BSP.004.ENV
  - CAP.BSP.004.ALT

impacted_events:
  - Transaction.Autorisée
  - Transaction.Refusée
  - Enveloppe.Allouée
  - Enveloppe.Consommée
  - Enveloppe.NonConsommée
  - Enveloppe.Épuisée
  - Alternative.Proposée

impacted_mappings:
  - SI
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010
  - ADR-BCM-FUNC-0004
  - ADR-BCM-FUNC-0005

supersedes: []

tags:
  - BCM
  - L2
  - BSP
  - transactions
  - authorization
  - envelopes
  - real-time

stability_impact: Structural

domain_classification:
  type: supporting
  coordinates:
    x: 0.7
    y: 0.65
  rationale: "Autorisation temps-réel est un pattern fintech connu ; l'application des règles de palier au point d'achat et la détection de contournement introduisent une logique Reliever-spécifique"
---

# ADR-BCM-FUNC-0008 — L2 Breakdown of CAP.BSP.004 — Transaction Control

## Domain Classification

> **Mandatory for FUNC ADRs.** Derived from the product vision and strategic vision — not from technical complexity alone.

| Axis | Score | Interpretation |
|------|-------|----------------|
| x — Business Differentiation | 0.7 | 0.0 = commodity (could be bought off-shelf) → 1.0 = uniquely differentiating |
| y — Model Complexity | 0.65 | 0.0 = trivial / well-understood → 1.0 = proprietary / high cognitive load |

**Classification:** `supporting`

**Rationale:**

> Autorisation temps-réel est un pattern fintech connu ; l'application des règles de palier au point d'achat et la détection de contournement introduisent une logique Reliever-spécifique

---

## Context

CAP.BSP.004 is Reliever's operational point of truth: this is where the tier rule applies concretely, at each purchase act, in real time. Without this capability, the program is a dashboard without effect.

This L1 concentrates three complementary logics: the authorization decision (real-time, constrained by the tier), budget envelope management (allocation, tracking, non-consumption signal), and purchase assistance (price comparison, alternative suggestions).

Strategic capability SC.004.04 "Event Surfacing" is here absorbed into the event architecture: events produced by BSP.004.AUT and BSP.004.ENV are directly consumed by BSP.001.SCO and BSP.001.SIG. There is no "surfacing" L2 — events are first-class facts.

## Decision

CAP.BSP.004 is decomposed into **3 L2 capabilities**:

| ID | Name | Responsibility |
|----|------|----------------|
| CAP.BSP.004.AUT | Purchase Authorization | Decide in real time whether to authorize or refuse a transaction by applying the current tier's rules |
| CAP.BSP.004.ENV | Envelope Management | Allocate, track, and adjust budgets by category and period; detect and emit the unconsumed envelope signal |
| CAP.BSP.004.ALT | Comparison & Alternatives | Suggest price or product alternatives at the moment of purchase to help the beneficiary stay within their envelope |

### Business Events per L2

| L2 | Events Produced | Events Consumed |
|----|-----------------|-----------------|
| CAP.BSP.004.AUT | `Transaction.Autorisée`, `Transaction.Refusée` | `Palier.FranchiHausse` (BSP.001.PAL), `Palier.Rétrogradé` (BSP.001.PAL), `Palier.Override.Appliqué` (BSP.001.PAL) — to update active rules |
| CAP.BSP.004.ENV | `Enveloppe.Allouée`, `Enveloppe.Consommée`, `Enveloppe.NonConsommée`, `Enveloppe.Épuisée` | `Bénéficiaire.Enrôlé` (BSP.002.ENR), `Palier.FranchiHausse` (BSP.001.PAL) — to recalibrate envelopes |
| CAP.BSP.004.ALT | `Alternative.Proposée` | `Transaction.Refusée` (BSP.004.AUT) — an alternative is proposed following a refusal |

### Transfer Points

- **BSP.001.PAL → BSP.004.AUT**: any tier change updates the active authorization rules
- **BSP.004.AUT → BSP.001.SCO**: each authorized/refused transaction feeds the score calculation
- **BSP.004.ENV → BSP.001.SIG**: an unconsumed envelope at end of period triggers relapse signal detection
- **BSP.004.AUT → BSP.004.ALT**: a refusal triggers the search for relevant alternatives

### Key Rule — Unconsumed Envelope

`Enveloppe.NonConsommée` is emitted by BSP.004.ENV at end of period if the budget has not been consumed up to a minimum threshold. This signal is counter-intuitive (non-spending = negative signal) and must be explicitly documented. The qualification logic remains in BSP.001.SIG.

### Verifiable Criteria

- BSP.004.AUT responds in real time (SLA < 500ms) — technical constraint to be respected during SI mapping
- Each L2 produces at least one business event (ADR-BCM-URBA-0009)
- BSP.004.ENV is the sole producer of `Enveloppe.NonConsommée`

## Rationale

The AUT / ENV / ALT separation reflects distinct business logics and performance constraints. Authorization is real-time and constrained by payment network latency. Envelope management is periodic and partly batch. Alternatives are an asynchronous enrichment service that must not block authorization.

### Alternatives Considered

- **AUT + ENV merged** — rejected because authorization is real-time with strict SLA constraints (payment network); envelope management has a different lifecycle (periodic, batch); conflating them would create an L2 with incompatible performance constraints
- **ALT in CAP.CAN.001** — rejected because the price comparison logic is a business rule (which alternatives are relevant for which tier) that belongs in CORE, even if its display belongs in CANAL

## BCM Impacts

### Structure

- 3 L2s created under CAP.BSP.004
- No L3 needed

### Events

- 7 business events defined
- `Transaction.Autorisée` and `Transaction.Refusée` are the most frequent events in the system — volume must be anticipated in the architecture

### SI / Data / Org Mapping

- **SI**: BSP.004.AUT depends on CAP.B2B.001.CRT (dedicated card rules) and CAP.REF.001.PAL (tier definitions)
- **ORG**: recommended owner: "Transactions & Payments" team

## Consequences

### Positive

- The moment of truth (purchase act) is modeled with precision
- The AUT/ENV/ALT separation allows independent evolution of the three logics

### Negative / Risks

- BSP.004.AUT latency is critical: any synchronous dependency toward other L2s can degrade the point-of-sale experience
- BSP.004.ALT requires real-time price data — dependency toward an external feed to be modeled in CAP.B2B.001

### Accepted Debt

- The price comparison model (sources, update frequency) is not modeled here

## Governance Indicators

- Criticality level: High (operational point of truth)
- Recommended review date: 2027-10-24
- Expected stability indicator: BSP.004.AUT SLA documented and measured

## Traceability

- Workshop: BCM Reliever Session — 2026-04-24
- Participants: yremy
- References:
  - `/strategic-vision/strategic-vision.md` — SC.004
  - ADR-BCM-FUNC-0004, ADR-BCM-FUNC-0005
