---
id: ADR-BCM-GOV-0003
title: "Periodic Stability Review of the BCM"
status: Proposed
date: 2026-03-05

family: GOV

decision_scope:
  level: Cross-Level
  zoning: []

impacted_capabilities: []
impacted_events: []
impacted_mappings:
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-GOV-0002
  - ADR-BCM-URBA-0004
supersedes: []

tags:
  - governance
  - stability
  - periodic-review

stability_impact: Structural
---

# ADR-BCM-GOV-0003 — Periodic Stability Review of the BCM

## Context

The BCM referential evolves rapidly (capabilities, events, ADRs, mappings).
Without a periodic review ritual, the risk is to accumulate obsolete decisions,
cross-cutting inconsistencies, and governance debt that is difficult to resolve.

The need is to install a simple, repeatable, and auditable stability review
mechanism to secure model coherence over time.

## Decision

The BCM Board establishes a **periodic stability review** with the following rules:

- **Standard cadence**: one quarterly review.
- **Exceptional triggers**: early review in case of a structural change
	(new zone, L1/L2 overhaul, major meta-model evolution).
- **Minimum scope**: GOV/URBA/FUNC ADRs, capabilities/events coherence,
	compliance of automated validations, and documentation debt.
- **Mandatory output**: a formal report including decisions, gaps,
	actions, owners, and deadlines.

Verifiable criteria:

- at least one review performed per quarter;
- existence of a dated and traced report;
- action completion rate tracked at the next review.

## Justification

This decision reduces the risk of progressive model drift and improves
the BCM Board's arbitration capacity based on objective facts.

### Alternatives Considered

- **Ad hoc review only** — rejected: too dependent on project urgencies.
- **Monthly review** — rejected: too high a burden given the current maturity level.

## Impacts on the BCM

### Structure

- No direct change to the L1/L2/L3 structure.
- Improvement of the quality and stability of evolution decisions.

### Events (if applicable)

- Periodic verification of the coherence of event/object/resource/subscription links.

### Mapping SI / Data / Org

- ORG: formalization of the governance ritual and monitoring responsibilities.

## Consequences

### Positive

- More predictable and traceable governance.
- Earlier detection of inconsistencies.
- Reduction of documentation debt over time.

### Negative / Risks

- Additional coordination burden for stakeholders.
- Risk of a formal review without actionable decisions if the framing is insufficient.

### Accepted Debt

- The detailed report format and target indicators will be refined
	in a subsequent iteration, after two review cycles.

## Governance Indicators

- Criticality level: High.
- Recommended review date: 2026-06-30.
- Expected stability indicator: continuous quarterly improvement.

## Traceability

- Workshop: BCM Governance — stability ritual framing.
- Participants: BCM Board (Architecture, Urbanization, Lead BA).
- References: ADR-BCM-GOV-0001, ADR-BCM-GOV-0002, ADR-BCM-URBA-0004.
