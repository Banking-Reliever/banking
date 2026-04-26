---
task_id: TASK-001
capability_id: CAP.CAN.001.TAB
capability_name: Beneficiary Dashboard
epic: Epic 1 — Event Feed Infrastructure
status: todo
priority: high
depends_on: []
---

# TASK-001 — Freeze the consumed events contract for CAP.CAN.001.TAB

## Context
CAP.CAN.001.TAB consumes three events produced by the CORE capabilities (BSP.001.SCO, BSP.001.PAL, BSP.004.ENV) via a unique subscription point. Since the CORE is being built in parallel, a stub will feed this point during development. For the stub and the CORE to be interchangeable without regression, the schema of each event must be defined and frozen before any implementation. This contract is the blocking precondition for TASK-002.

## Capability Reference
- Capability: Beneficiary Dashboard (CAP.CAN.001.TAB)
- Zone: CHANNEL
- Governing ADRs: ADR-BCM-FUNC-0009, ADR-BCM-URBA-0007, ADR-BCM-URBA-0009

## What needs to be produced
Define and document the contractual schema of the three events that CAP.CAN.001.TAB consumes, so that the stub (TASK-002) and the real CORE capabilities (TASK-006) can produce them interchangeably.

For each event, the contract must specify:
- The canonical event name (as defined in the BCM)
- The producing capability
- The mandatory fields and their semantic type (e.g. beneficiary identifier, numeric score value, timestamp)
- The cardinality (one event per beneficiary per recalculation, per tier change, per transaction)
- The subscription type: business (lifecycle impact) or resource (read model feed)

The three events to contractualize:

| Event | Producer | Subscription Type |
|-------|----------|-------------------|
| `BehavioralScore.Recalculated` | CAP.BSP.001.SCO | Resource — feed the score read model |
| `Tier.UpwardCrossed` | CAP.BSP.001.PAL | Business — changes the current displayed state |
| `Envelope.Consumed` | CAP.BSP.004.ENV | Resource — update the displayed balances |

## Business Events to Produce
None — this task produces a contract artifact, not a business event.

## Business Objects Involved
- **Beneficiary** — correlation identifier present in each event
- **Behavioral score** — numeric value carried by `BehavioralScore.Recalculated`
- **Tier** — autonomy level carried by `Tier.UpwardCrossed`
- **Envelope** — category and remaining balance carried by `Envelope.Consumed`

## Required Event Subscriptions
None — this task defines the contracts; the subscription is implemented in TASK-002.

## Definition of Done
- [ ] The schema of `BehavioralScore.Recalculated` is documented (fields, types, cardinality)
- [ ] The schema of `Tier.UpwardCrossed` is documented (fields, types, cardinality)
- [ ] The schema of `Envelope.Consumed` is documented (fields, types, cardinality)
- [ ] The subscription type (business / resource) is qualified for each event with justification (ADR-BCM-URBA-0009)
- [ ] The contract is validated by the contacts from the producing capabilities (BSP.001 and BSP.004)
- [ ] The contract is versioned (v1.0) and constitutes the reference for TASK-002 and TASK-006
- [ ] validate_repo.py passes without error
- [ ] validate_events.py passes without error

## Acceptance Criteria (business)
A TASK-002 developer can build the stub without asking any questions about the event structure. A TASK-006 developer can connect the real CORE capabilities without modifying the consumption code of CAP.CAN.001.TAB.

## Dependencies
No upstream dependencies. This task must be completed before TASK-002.

## Open Questions
- Who is the contact on the BSP.001 side (SCO and PAL) to validate the contract?
- Who is the contact on the BSP.004 side (ENV) to validate the contract?
- Is the beneficiary identifier the same across all events (golden record of CAP.REF.001.BEN)?
