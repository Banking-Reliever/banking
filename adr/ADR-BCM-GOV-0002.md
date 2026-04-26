---
id: ADR-BCM-GOV-0002
title: "Arbitration Mechanism and BCM Governance Board"
status: Proposed
date: 2026-02-26

family: GOV

decision_scope:
  level: Cross-Level
  zoning:
    - PILOTAGE
    - SERVICES_COEUR
    - SUPPORT
    - REFERENTIEL
    - ECHANGE_B2B
    - CANAL
    - DATA_ANALYTIQUE

impacted_capabilities: []
impacted_events: []
impacted_mappings:
  - SI
  - DATA
  - ORG

related_adr: 
  - ADR-BCM-GOV-0001

supersedes: []

tags:
  - governance
  - board
  - arbitration

stability_impact: Structural
---

# ADR-BCM-GOV-0002 — BCM Arbitration Board

## Context

The BCM evolves along projects and transformations.

To ensure:
- Global model coherence,
- Integration of field feedback,
- Balance between urbanization and operational reality,

a formalized arbitration mechanism is necessary.

## Decision

A **BCM Board** is established.

### Composition

The board is composed of:

- IS Architects
- Lead Business Analysts
- An urbanist responsible for global coherence

The composition aims at a balance between:
- Technical vision
- Business vision
- Systemic vision

### Role of the Board

The board is responsible for:

- Reviewing governance ADRs
- Reviewing urbanization ADRs
- Validating functional ADRs
- Cross-cutting coherence of the BCM model
- Arbitration in case of disagreement between teams

### Escalation Process

Model evolutions are fed by:

- Field feedback from project teams
- Event Storming Big Picture
- Integration issues
- Recurring observed difficulties

Project teams may:

- Propose evolutions via a Proposed ADR
- Submit formalized issues

### Decision Mode

- Consensus-seeking is the priority.
- In case of persistent disagreement, decision is taken by a qualified majority of the board.
- The urbanist holds a coherence guardian role, not an absolute veto.

### Transparency

- Proposed ADRs are visible.
- Decisions are motivated and documented.
- Rejections are explicitly justified.

### Balance Clause

The BCM Board does not constitute a project control body.

It intervenes only on BCM model evolutions.

The ultimate purpose remains business value creation and project fluidity.

## Justification

This mechanism allows:

- Avoiding a siloed top-down architecture.
- Integrating operational feedback.
- Structuring arbitrations.
- Preserving global coherence.

It formalizes a balance between stability and adaptability.

### Alternatives Considered

- Ad hoc validation without a dedicated body — rejected because it is poorly traceable and not reproducible.
- Exclusively top-down governance — rejected because it limits field feedback.

## Impacts on the BCM

### Structure

- Establishment of a formal arbitration mechanism for BCM evolutions.
- Clarification of roles between review, validation, and arbitration.

### Events (if applicable)

- No direct impact on business events.

### Mapping SI / Data / Org

- Impacted applications: cross-cutting governance (SI).
- Impacted flows: escalation and arbitration processes (DATA/ORG).

## Consequences

### Positive

- Clear governance.
- Structured channel for field feedback.
- Reduction of implicit conflicts.
- Continuous improvement of the model.

### Negative / Risks

- Organizational complexity.
- Risk of decision-making heaviness.
- Risk of capture by a dominant group if not monitored.

### Accepted Debt

- Cost of running a cross-cutting governance body.
- Need for continuous team onboarding to the ADR process.

## Governance Indicators

- Criticality level: High (cross-cutting governance).
- Recommended review date: 2028-02-26.
- Expected stability indicator:
  - Average arbitration turnaround time under control.
  - Arbitration decisions systematically traced in ADRs.

## Traceability

- Workshop: BCM Governance – 2026-02-26
- Participants: EA / Business Architecture
- References: ADR-BCM-GOV-0001
