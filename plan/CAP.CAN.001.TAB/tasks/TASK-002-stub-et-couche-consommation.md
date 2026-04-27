---
task_id: TASK-002
capability_id: CAP.CAN.001.TAB
capability_name: Beneficiary Dashboard
epic: Epic 1 — Event Feed Infrastructure
status: todo
priority: high
depends_on: [TASK-001]
---

# TASK-002 — Feed stub and event consumption layer for CAP.CAN.001.TAB

## Context
CAP.CAN.001.TAB is developed in complete isolation from the CORE capabilities (BSP.001.SCO, BSP.001.PAL, BSP.004.ENV), which are being built in parallel. A stub must feed the unique subscription point of CAP.CAN.001.TAB with the three events defined in TASK-001, at a configurable frequency. The consumption layer reads these events and maintains a read model per beneficiary that subsequent epics will display. When the CORE is operational (TASK-006), the stub will be replaced without touching the consumption code.

## Capability Reference
- Capability: Beneficiary Dashboard (CAP.CAN.001.TAB)
- Zone: CHANNEL
- Governing ADRs: ADR-BCM-FUNC-0009, ADR-BCM-URBA-0007, ADR-BCM-URBA-0009

## What needs to be produced

### Unique subscription point
Set up the dedicated subscription point for CAP.CAN.001.TAB on the event bus. All CORE capabilities (current and future) publish to this point; CAP.CAN.001.TAB reads from it exclusively.

### Feed stub
A component that publishes the three events defined in TASK-001 to this subscription point:
- `BehavioralScore.Recalculated` — with a simulated score varying over time
- `Tier.UpwardCrossed` — with simulated tier transitions
- `Envelope.Consumed` — with simulated budget consumption by category

The stub must be activatable/deactivatable via environment configuration (inactive in production).

### Consumption layer
A component that reads the events from the subscription point and maintains a **read model per beneficiary** containing:
- The current behavioral score
- The active tier
- Envelope balances by category

This read model is the sole data source for the TASK-003, TASK-004, TASK-005 views.

### Test beneficiary
At the end of this task, a simulated test beneficiary must be viewable end-to-end (events produced → read model fed) without any CORE dependency.

## Business Events to Produce
No business events produced by this task — it establishes the consumption infrastructure.

## Business Objects Involved
- **Beneficiary** — correlation key of the read model
- **Behavioral score** — current state maintained in the read model
- **Tier** — current state maintained in the read model
- **Envelope** — balance by category maintained in the read model

## Required Event Subscriptions
- `BehavioralScore.Recalculated` (from CAP.BSP.001.SCO) — resource subscription: feeds the score in the read model
- `Tier.UpwardCrossed` (from CAP.BSP.001.PAL) — business subscription: updates the active tier in the read model
- `Envelope.Consumed` (from CAP.BSP.004.ENV) — resource subscription: updates envelope balances in the read model

## Definition of Done
- [ ] The unique subscription point of CAP.CAN.001.TAB is operational
- [ ] The stub publishes the three events (compliant with the TASK-001 contract) at configurable frequency
- [ ] The stub is deactivatable by environment configuration
- [ ] The consumption layer reads the three events and maintains the read model per beneficiary
- [ ] A test beneficiary is viewable end-to-end without CORE dependency
- [ ] Replacing the stub with a real source requires no modification to the consumption code
- [ ] validate_repo.py passes without error
- [ ] validate_events.py passes without error

## Acceptance Criteria (business)
A developer working on TASK-003 can display a test beneficiary's data without waiting for any other team. The read model data is consistent with the events published by the stub.

## Dependencies
- **TASK-001**: the event contract must be frozen before implementing the stub and the consumption layer

## Open Questions
- [ ] Has the event bus technology already been chosen for the Reliever project, or is it left to the implement-capability skill?
- [ ] Should the stub simulate multiple distinct beneficiaries or is a single test beneficiary sufficient for Epics 2-4?
