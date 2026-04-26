---
id: ADR-BCM-FUNC-0012
title: "L2 Breakdown of CAP.SUP.001 — Data Compliance & Protection"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - SUPPORT

impacted_capabilities:
  - CAP.SUP.001
  - CAP.SUP.001.CON
  - CAP.SUP.001.AUD
  - CAP.SUP.001.RET

impacted_events:
  - Consentement.Accordé
  - Consentement.Révoqué
  - AccèsDonnées.Journalisé
  - DroitExercé.Traité

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
  - SUPPORT
  - GDPR
  - compliance
  - sensitive-data

stability_impact: Moderate

domain_classification:
  type: generic
  coordinates:
    x: 0.15
    y: 0.2
  rationale: "Conformité RGPD, consentement et rétention sont des obligations réglementaires avec des patterns IS bien établis"
---

# ADR-BCM-FUNC-0012 — L2 Breakdown of CAP.SUP.001 — Data Compliance & Protection

## Domain Classification

> **Mandatory for FUNC ADRs.** Derived from the product vision and strategic vision — not from technical complexity alone.

| Axis | Score | Interpretation |
|------|-------|----------------|
| x — Business Differentiation | 0.15 | 0.0 = commodity (could be bought off-shelf) → 1.0 = uniquely differentiating |
| y — Model Complexity | 0.2 | 0.0 = trivial / well-understood → 1.0 = proprietary / high cognitive load |

**Classification:** `generic`

**Rationale:**

> Conformité RGPD, consentement et rétention sont des obligations réglementaires avec des patterns IS bien établis

---

## Context

CAP.SUP.001 addresses the transparency/privacy tension identified as critical in the service offer. Reliever concentrates data of heterogeneous natures (financial, medical, social) on the same individual, shared among actors whose regulations are distinct (bank: GDPR + PSD2; physician: GDPR + medical secrecy; social worker: GDPR + social action framework).

This capability is transverse to the entire program — no capability can access a beneficiary's data without passing through the rules defined here. It owns consents, access traceability, and beneficiary rights.

## Decision

CAP.SUP.001 is decomposed into **3 L2 capabilities**:

| ID | Name | Responsibility |
|----|------|----------------|
| CAP.SUP.001.CON | Consent Management | Collect, store, manage, and honor the beneficiary's GDPR consents for each type of data sharing |
| CAP.SUP.001.AUD | Audit & Traceability | Log all accesses and actions on beneficiary data, across all capabilities |
| CAP.SUP.001.RET | Beneficiary Rights | Process GDPR rights requests (access, rectification, erasure, portability, objection) |

### Business Events per L2

| L2 | Events Produced | Events Consumed |
|----|-----------------|-----------------|
| CAP.SUP.001.CON | `Consentement.Accordé`, `Consentement.Révoqué` | `Bénéficiaire.Enrôlé` (BSP.002.ENR) — triggers consent collection |
| CAP.SUP.001.AUD | `AccèsDonnées.Journalisé` | Any event involving access to beneficiary data (transverse) |
| CAP.SUP.001.RET | `DroitExercé.Traité` | `Bénéficiaire.SortiDuDispositif` (BSP.002.SOR) — triggers post-exit rights review |

### Blocking Rule

`Consentement.Accordé` is a mandatory precondition for:
- `Bénéficiaire.Enrôlé` (BSP.002.ENR) — no enrollment without consent
- `DonnéesFinancières.Rafraîchies` (B2B.001.OBK) — no open banking access without consent
- Any consultation in CAP.CAN.002.VUE

If `Consentement.Révoqué`, all consuming capabilities must cease access to the beneficiary's data.

### Verifiable Criteria

- Each L2 produces at least one business event (ADR-BCM-URBA-0009)
- No capability can access a beneficiary's data unless `Consentement.Accordé` is in the current state
- 100% of beneficiary data accesses produce `AccèsDonnées.Journalisé`

## Rationale

The CON / AUD / RET separation reflects three distinct compliance responsibilities. Consents are dynamic (granted/revoked). Audit is continuous and transverse. Rights requests are one-time events with legal deadlines (1 month GDPR). Conflating them would create an L2 that is too broad with incompatible legal constraints.

### Alternatives Considered

- **CON in BSP.002.ENR** — rejected because consent is a transverse responsibility that goes beyond enrollment (it can be revoked at any time, independently of the beneficiary's lifecycle in the program)
- **AUD in CAP.PIL.001** — rejected because data access auditing is a GDPR regulatory obligation (SUPPORT); program steering is a business concern (PILOTAGE) — the levels and actors are distinct

## BCM Impacts

### Structure

- 3 L2s created under CAP.SUP.001
- Transverse capability: all other capabilities depend on it for data access

### SI / Data / Org Mapping

- **SI**: requires a DMP (Data Management Platform) or equivalent for consent management
- **ORG**: recommended owner: DPO (Data Protection Officer)

## Consequences

### Positive

- The transparency/privacy tension is addressed by a dedicated capability with explicit blocking rules
- Audit is first-class — every action is traceable

### Negative / Risks

- Sharing data between prescribers of different natures (bank, physician, social worker) remains a regulatory grey area — requires legal advice

### Accepted Debt

- The precise legal bases for processing data for each prescriber type are not modeled here

## Governance Indicators

- Criticality level: High (regulatory obligation, viability condition)
- Recommended review date: 2027-10-24
- Expected stability indicator: 100% of data accesses logged, 0 enrollment without documented consent

## Traceability

- Workshop: BCM Reliever Session — 2026-04-24
- Participants: yremy
- References:
  - `/strategic-vision/strategic-vision.md` — SC.007
  - ADR-BCM-FUNC-0004, ADR-BCM-FUNC-0007
