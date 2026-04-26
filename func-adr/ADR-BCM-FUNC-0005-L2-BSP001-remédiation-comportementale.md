---
id: ADR-BCM-FUNC-0005
title: "L2 Breakdown of CAP.BSP.001 — Behavioral Remediation"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - SERVICES_COEUR

impacted_capabilities:
  - CAP.BSP.001
  - CAP.BSP.001.SCO
  - CAP.BSP.001.PAL
  - CAP.BSP.001.SIG
  - CAP.BSP.001.ARB

impacted_events:
  - ScoreComportemental.Recalculé
  - ScoreComportemental.SeuilAtteint
  - Palier.FranchiHausse
  - Palier.Rétrogradé
  - Palier.Override.Appliqué
  - Signal.Rechute.Détecté
  - Signal.Progression.Détecté
  - Arbitrage.Override.Validé
  - Arbitrage.AlgorithmeRéaffirmé

impacted_mappings:
  - SI
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0007
  - ADR-BCM-URBA-0008
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010
  - ADR-BCM-FUNC-0004

supersedes: []

tags:
  - BCM
  - L2
  - BSP
  - scoring
  - remediation
  - core-domain

stability_impact: Structural

domain_classification:
  type: core
  coordinates:
    x: 0.95
    y: 0.9
  rationale: "Constitue le cœur différenciateur de Reliever — scoring comportemental et gouvernance des paliers d'autonomie inexistants ailleurs dans le secteur financier ou social"
---

# ADR-BCM-FUNC-0005 — L2 Breakdown of CAP.BSP.001 — Behavioral Remediation

## Domain Classification

> **Mandatory for FUNC ADRs.** Derived from the product vision and strategic vision — not from technical complexity alone.

| Axis | Score | Interpretation |
|------|-------|----------------|
| x — Business Differentiation | 0.95 | 0.0 = commodity (could be bought off-shelf) → 1.0 = uniquely differentiating |
| y — Model Complexity | 0.9 | 0.0 = trivial / well-understood → 1.0 = proprietary / high cognitive load |

**Classification:** `core`

**Rationale:**

> Constitue le cœur différenciateur de Reliever — scoring comportemental et gouvernance des paliers d'autonomie inexistants ailleurs dans le secteur financier ou social

---

## Context

CAP.BSP.001 is the **core domain** of Reliever (ADR-BCM-FUNC-0004). It is the differentiating capability: without continuous behavioral evaluation and tier steering, Reliever is merely a prepaid card.

This L1 concentrates the MMR-like logic of the program:
- a score calculated continuously from purchase events
- autonomy tiers with their associated rules
- detection of paradoxical relapse signals (unconsumed envelope = circumvention)
- the tension between algorithmic authority and human prescriber override

The L2 must decompose these responsibilities without creating excessive coupling between score calculation, tier management, signal detection, and human/algorithm arbitration.

## Decision

CAP.BSP.001 is decomposed into **4 L2 capabilities**:

| ID | Name | Responsibility |
|----|------|----------------|
| CAP.BSP.001.SCO | Behavioral Scoring | Calculate and update the beneficiary's score from transaction events and received circumvention signals |
| CAP.BSP.001.PAL | Tier Management | Define the rules associated with each tier, steer algorithmic transitions, apply prescriber overrides |
| CAP.BSP.001.SIG | Signal Detection | Identify and qualify relapse signals (unconsumed envelope) and progression signals, transmit them to scoring |
| CAP.BSP.001.ARB | Algorithm / Human Arbitration | Manage the algorithm's resumption of control after an override, validate or invalidate the prescriber's decision over time |

### Business Events per L2

| L2 | Events Produced | Events Consumed |
|----|-----------------|-----------------|
| CAP.BSP.001.SCO | `ScoreComportemental.Recalculé`, `ScoreComportemental.SeuilAtteint` | `Transaction.Autorisée` (BSP.004.AUT), `Transaction.Refusée` (BSP.004.AUT), `Signal.Rechute.Détecté` (BSP.001.SIG), `Signal.Progression.Détecté` (BSP.001.SIG) |
| CAP.BSP.001.PAL | `Palier.FranchiHausse`, `Palier.Rétrogradé`, `Palier.Override.Appliqué` | `ScoreComportemental.SeuilAtteint` (BSP.001.SCO), `Override.DemandéParPrescripteur` (BSP.003.COD) |
| CAP.BSP.001.SIG | `Signal.Rechute.Détecté`, `Signal.Progression.Détecté` | `Enveloppe.NonConsommée` (BSP.004.ENV), `Transaction.Autorisée` (BSP.004.AUT) |
| CAP.BSP.001.ARB | `Arbitrage.Override.Validé`, `Arbitrage.AlgorithmeRéaffirmé` | `Palier.Override.Appliqué` (BSP.001.PAL), `ScoreComportemental.Recalculé` (BSP.001.SCO) |

### Transfer Points

- **BSP.004.AUT → BSP.001.SCO**: each authorized or refused transaction triggers a score recalculation
- **BSP.004.ENV → BSP.001.SIG**: an unconsumed envelope at end of period triggers relapse signal detection
- **BSP.001.SIG → BSP.001.SCO**: qualified signals feed the scoring
- **BSP.001.SCO → BSP.001.PAL**: a reached score threshold triggers a candidate tier transition
- **BSP.003.COD → BSP.001.PAL**: an override requested by a prescriber forces a tier transition
- **BSP.001.PAL → BSP.001.ARB**: any applied override opens an algorithm/human arbitration window

### Key Rule — Unconsumed Envelope

An unspent budget at end of period is a relapse signal (circumvention of the controlled channel), not a success signal. CAP.BSP.001.SIG is the exclusive owner of this counter-intuitive qualification.

### Verifiable Criteria

- Each L2 produces at least one business event (ADR-BCM-URBA-0009)
- No L2 subscribes to its own events
- CAP.BSP.001.ARB does not produce a tier event: it validates or invalidates; CAP.BSP.001.PAL remains owner of the tier state

## Rationale

The SCO / PAL / SIG / ARB separation avoids concentrating all logic in a behavioral monolith. Each L2 has a distinct lifecycle:
- SCO: continuous, triggered by each transaction
- PAL: triggered by threshold or override
- SIG: triggered by end-of-period or purchase pattern
- ARB: triggered only on prescriber override

### Alternatives Considered

- **SCO + PAL merged** — rejected because score calculation and tier transition decisions have different rhythms and owners; conflating them creates strong coupling between analytical logic and tier business rules
- **SIG absorbed into SCO** — rejected because the circumvention detection logic (unconsumed envelope) is a distinct, counter-intuitive business rule that deserves a dedicated and traceable responsibility
- **ARB absent (algorithm only)** — rejected because the prescriber override capability is an explicit business requirement; its absence would make the program rigid and incompatible with clinical judgment

## BCM Impacts

### Structure

- 4 L2s created under CAP.BSP.001
- No L3 needed at this stage

### Events

- 9 business events defined, all attached to a single emitting L2 (ADR-BCM-URBA-0010)
- Main event flow: BSP.004 → BSP.001.SIG / SCO → BSP.001.PAL → BSP.001.ARB

### SI / Data / Org Mapping

- **SI**: CAP.BSP.001 constitutes the central bounded context of Reliever — its implementation must be isolated from other contexts
- **ORG**: recommended owner: "Remediation" team (data scientists + domain experts)

## Consequences

### Positive

- Core domain clearly isolated and decomposed
- Event flow traceable from transaction to tier transition
- The relapse rule (unconsumed envelope) is explicitly owned by SIG

### Negative / Risks

- BSP.001.ARB is an L2 with low event volume (triggered only on override) — risk of under-investment; monitor during stability review

### Accepted Debt

- The precise tier transition thresholds (scoring criteria) are not modeled in this ADR — to be formalized in behavioral model specifications

## Governance Indicators

- Criticality level: High (core domain)
- Recommended review date: 2027-10-24
- Expected stability indicator: 4 L2s present, each with at least one documented business event and an identified owner team

## Traceability

- Workshop: BCM Reliever Session — 2026-04-24
- Participants: yremy
- References:
  - `/strategic-vision/strategic-vision.md` — SC.001
  - ADR-BCM-FUNC-0004
  - ADR-BCM-URBA-0009 — Complete capability definition
  - ADR-BCM-URBA-0010 — L2 pivot
