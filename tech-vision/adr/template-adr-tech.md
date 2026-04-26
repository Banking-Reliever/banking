---
id: ADR-TECH-STRAT-NNN
title: "<Decision title>"
status: Proposed | Accepted | Suspended | Deprecated | Superseded
date: YYYY-MM-DD
# If status: Suspended, add:
# suspension_date: YYYY-MM-DD
# suspension_reason: <reason>

family: TECH
tech_domain: EVENT_INFRASTRUCTURE | RUNTIME | API_CONTRACT | DATA_PERSISTENCE | OBSERVABILITY | DEPLOYMENT

grounded_in_urba:
  - ADR-BCM-URBA-XXXX   # URBA ADRs whose constraints motivated this decision

grounded_in_func:
  - ADR-BCM-FUNC-XXXX   # FUNC ADRs whose L2 capabilities this decision serves

related_adr: []
supersedes: []

impacted_zones:
  - PILOTAGE
  - SERVICES_COEUR
  - SUPPORT
  - REFERENTIEL
  - ECHANGE_B2B
  - CANAL
  - DATA_ANALYTIQUE

tags: []

stability_impact: Structural | Moderate | Minor
---

# ADR-TECH-STRAT-NNN — <Short title>

## Context

Describe:
- The BCM constraints that created this decision (cite URBA/FUNC ADR IDs)
- The product and operational constraints (from product.md — financial inclusion context,
  regulatory environment, deployment context)
- What problem this decision solves and why it is strategic (i.e., long-lived, shapes
  architecture choices for years, not a tactical implementation detail)

## Decision

Decision formulated in a **testable** manner:

- Rule 1:
- Rule 2:
- Verifiable criterion:

Example:
> Every L2 capability publishes its business events on a durable, schema-governed topic.
> No L2 may call another L2's internal database directly.

## Justification

Why this option over the alternatives. Be specific about which constraints tipped the balance
(cite URBA ADR IDs, product constraints, operational reality).

### Alternatives Considered

- Option A — rejected because [specific reason tied to a named constraint]
- Option B — rejected because [specific reason]

## Technical Impact

### On Event Infrastructure (if applicable)

- Implications for broker choice, topic structure, schema registry

### On Service Boundaries (if applicable)

- Implications for L2 packaging, deployment units, L3 decompression

### On Data Ownership (if applicable)

- Implications for persistence per L2, REFERENTIEL zone access patterns

### On API Contracts (if applicable)

- Implications for synchronous vs. asynchronous exposure, versioning strategy

## Consequences

### Positive

### Negative / Risks

### Accepted Debt

## Governance Indicators

- Review trigger: [what change in context would cause this decision to be revisited]
- Expected stability: [timeframe — e.g., "3 years unless cloud provider strategy changes"]

## Traceability

- Session: Technical brainstorming YYYY-MM-DD
- Participants:
- References:
