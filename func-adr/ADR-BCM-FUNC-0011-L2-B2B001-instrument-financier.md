---
id: ADR-BCM-FUNC-0011
title: "L2 Breakdown of CAP.B2B.001 — Financial Instrument Management"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - ECHANGE_B2B

impacted_capabilities:
  - CAP.B2B.001
  - CAP.B2B.001.CRT
  - CAP.B2B.001.OBK
  - CAP.B2B.001.FLX

impacted_events:
  - Carte.Émise
  - Carte.Activée
  - Carte.Suspendue
  - Carte.Résiliée
  - DonnéesFinancières.Rafraîchies
  - Alimentation.Effectuée

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
  - ECHANGE_B2B
  - open-banking
  - card
  - financial-instrument

stability_impact: Structural

domain_classification:
  type: generic
  coordinates:
    x: 0.25
    y: 0.3
  rationale: "Émission de carte et open banking sont des patterns réglementaires standardisés (DSP2) utilisés comme infrastructure, non comme source de différenciation"
---

# ADR-BCM-FUNC-0011 — L2 Breakdown of CAP.B2B.001 — Financial Instrument Management

## Domain Classification

> **Mandatory for FUNC ADRs.** Derived from the product vision and strategic vision — not from technical complexity alone.

| Axis | Score | Interpretation |
|------|-------|----------------|
| x — Business Differentiation | 0.25 | 0.0 = commodity (could be bought off-shelf) → 1.0 = uniquely differentiating |
| y — Model Complexity | 0.3 | 0.0 = trivial / well-understood → 1.0 = proprietary / high cognitive load |

**Classification:** `generic`

**Rationale:**

> Émission de carte et open banking sont des patterns réglementaires standardisés (DSP2) utilisés comme infrastructure, non comme source de différenciation

---

## Context

CAP.B2B.001 is the capability that makes Reliever independent from banking institutions. Via open banking, Reliever accesses the financial data of the main account without an inter-banking agreement. Via the dedicated card, it controls spending without modifying the main account.

This is the ECHANGE_B2B zone that holds this capability (ADR-BCM-URBA-0001): it involves exchanges with the external financial ecosystem (payment networks, issuing institutions, open banking APIs) with specific SLA, traceability, and regulatory compliance constraints.

## Decision

CAP.B2B.001 is decomposed into **3 L2 capabilities**:

| ID | Name | Responsibility |
|----|------|----------------|
| CAP.B2B.001.CRT | Dedicated Card Management | Manage the dedicated card lifecycle — issuance, activation, suspension, cancellation — and link its usage rules to the current tiers |
| CAP.B2B.001.OBK | Open Banking Integration | Access and refresh the beneficiary's main account financial data via open banking APIs |
| CAP.B2B.001.FLX | Financial Flow Management | Orchestrate the funding of the dedicated card from the main account, ensure flow reconciliation |

### Business Events per L2

| L2 | Events Produced | Events Consumed |
|----|-----------------|-----------------|
| CAP.B2B.001.CRT | `Carte.Émise`, `Carte.Activée`, `Carte.Suspendue`, `Carte.Résiliée` | `Bénéficiaire.Enrôlé` (BSP.002.ENR), `Palier.FranchiHausse` (BSP.001.PAL), `Palier.Rétrogradé` (BSP.001.PAL), `Bénéficiaire.SortiDuDispositif` (BSP.002.SOR) |
| CAP.B2B.001.OBK | `DonnéesFinancières.Rafraîchies` | `Bénéficiaire.Enrôlé` (BSP.002.ENR) — to initialize open banking access |
| CAP.B2B.001.FLX | `Alimentation.Effectuée` | `Enveloppe.Allouée` (BSP.004.ENV), `Enveloppe.Épuisée` (BSP.004.ENV) |

### Transfer Points

- **BSP.001.PAL → B2B.001.CRT**: any tier change updates the card rules (ceilings, category restrictions)
- **BSP.002.ENR → B2B.001.CRT**: enrollment triggers card issuance
- **B2B.001.OBK → DAT.001**: refreshed financial data feeds behavioral analytics

### Open Banking Regulatory Constraint

CAP.B2B.001.OBK operates under the PSD2/DSP2 framework. Access to financial data requires explicit consent managed by CAP.SUP.001.CON. The open banking capability can only be activated after `Consentement.Accordé`.

### Verifiable Criteria

- Each L2 produces at least one business event (ADR-BCM-URBA-0009)
- `Carte.Émise` can only be produced after `Bénéficiaire.Enrôlé`
- `DonnéesFinancières.Rafraîchies` can only be produced after `Consentement.Accordé` (SUP.001.CON)

## Rationale

The CRT / OBK / FLX separation reflects three distinct relationships with the external financial ecosystem: the card issuer (payment partner), the beneficiary's banks (via open banking), and the fund flows between the two. These three relationships have different partners, SLAs, and regulations.

### Alternatives Considered

- **CRT + FLX merged** — rejected because the card and financial flows involve different external partners (card issuer ≠ beneficiary's main bank); their lifecycles and SLAs are distinct
- **OBK in CAP.SUP.001** — rejected because open banking is an exchange with the external ecosystem (ECHANGE_B2B); the compliance of that exchange is managed by SUP.001 but the exchange capability itself belongs to B2B

## BCM Impacts

### Structure

- 3 L2s created under CAP.B2B.001
- Strong incoming dependencies from BSP.001.PAL and BSP.002.ENR

### SI / Data / Org Mapping

- **SI**: requires a card issuance partner (licensed payment institution) and an open banking aggregator
- **ORG**: recommended owner: "Financial Partnerships & Payments" team

## Consequences

### Positive

- Reliever is independent from banks through open banking — no inter-banking agreement required
- The card is the single universal control point

### Negative / Risks

- Strong dependency on a card issuance partner (potential single point of failure)
- Open banking is subject to regulatory revisions (PSD3 in progress) — risk of refactoring B2B.001.OBK

### Accepted Debt

- The choice of card issuance partner is not formalized here — critical open question

## Governance Indicators

- Criticality level: High (financial infrastructure of the program)
- Recommended review date: 2027-10-24
- Expected stability indicator: issuance partner identified, open banking access PSD2-certified

## Traceability

- Workshop: BCM Reliever Session — 2026-04-24
- Participants: yremy
- References:
  - `/strategic-vision/strategic-vision.md` — SC.006
  - ADR-BCM-FUNC-0004
