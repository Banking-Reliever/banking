---
task_id: TASK-006
capability_id: CAP.CAN.001.TAB
capability_name: Beneficiary Dashboard
epic: Epic 5 — Connection to Real CORE Capabilities
status: todo
priority: low
depends_on: [TASK-002, TASK-003, TASK-004, TASK-005]
---

# TASK-006 — Connection to real CORE capabilities and stub decommissioning

## Context
Epics 1 to 4 have allowed the dashboard to be fully built and validated in isolation, thanks to the stub (TASK-002). As soon as the CORE capabilities (BSP.001.SCO, BSP.001.PAL, BSP.004.ENV, BSP.004.AUT) are operational and publishing their real events on the agreed subscription points, the stub can be removed. This task is triggered by the CORE's availability — not by CAP.CAN.001.TAB's internal schedule. It is a precondition for the real production deployment of the dashboard, but not a precondition for delivering the views themselves.

## Capability Reference
- Capability: Beneficiary Dashboard (CAP.CAN.001.TAB)
- Zone: CHANNEL
- Governing ADRs: ADR-BCM-FUNC-0009, ADR-BCM-URBA-0007, ADR-BCM-URBA-0009

## What needs to be produced

### Contract compatibility check
Before connection, verify that the events produced by the real CORE capabilities conform to the schemas contractualized in TASK-001:
- Schema of `BehavioralScore.Recalculated` conforms to contract v1.0
- Schema of `Tier.UpwardCrossed` conforms to contract v1.0
- Schema of `Envelope.Consumed` conforms to contract v1.0
- Schema of `Transaction.Authorized` and `Transaction.Declined` conforms to the BSP.004.AUT contract

Any divergence must be resolved before decommissioning the stub. The CAP.CAN.001.TAB consumption code must not be modified to absorb a divergence: it is the CORE's responsibility to comply with the contract defined in TASK-001.

### Stub decommissioning
Remove the feed stub via environment configuration in production. The CAP.CAN.001.TAB subscription point remains unchanged — only the source that publishes to it changes.

### Regression-free validation
Validate on both channels (web and mobile) that:
- The current situation view (TASK-003) displays data consistent with the real CORE events
- The transaction history (TASK-004) is fed by real transactions
- The mobile view (TASK-005) reflects the real tier and envelopes

### Production supervision
Confirm, via supervision, that the real event stream feeds the CAP.CAN.001.TAB read model continuously and without interruption. No regression of `Dashboard.Viewed` is acceptable.

## Business Events to Produce
`Dashboard.Viewed` continues to be produced normally — no change to produced events.

## Business Objects Involved
- **Beneficiary** — the displayed data is now real
- **Behavioral score**, **Tier**, **Envelope**, **Transaction** — all fed by the real CORE capabilities

## Required Event Subscriptions
Identical to TASK-002 and TASK-004 — the wiring is unchanged, only the producer (stub → real CORE) changes.

## Definition of Done
- [ ] Compatibility of real CORE event schemas with TASK-001 contracts is verified and documented
- [ ] The stub is deactivated in the production environment
- [ ] The current situation web view (TASK-003) displays real data without regression
- [ ] The transaction history web view (TASK-004) is fed by real transactions without regression
- [ ] The mobile view (TASK-005) displays real data without regression
- [ ] `Dashboard.Viewed` continues to be produced correctly on both channels
- [ ] Supervision confirms the real event stream in production
- [ ] validate_repo.py passes without error
- [ ] validate_events.py passes without error

## Acceptance Criteria (business)
A real beneficiary enrolled in the program views their dashboard and sees their real data (effective tier, real envelopes, history of their actual transactions). The dashboard data is consistent with the decisions made by the CORE capabilities.

## Dependencies
- **TASK-002**: the stub/subscription infrastructure must be operational and its tests validated
- **TASK-003, TASK-004, TASK-005**: all views must be validated on stub before connection
- **CAP.BSP.001.SCO** — operational and publishing `BehavioralScore.Recalculated`
- **CAP.BSP.001.PAL** — operational and publishing `Tier.UpwardCrossed`
- **CAP.BSP.004.ENV** — operational and publishing `Envelope.Consumed`
- **CAP.BSP.004.AUT** — operational and publishing `Transaction.Authorized` / `Transaction.Declined`

## Open Questions
- [ ] In case of schema divergence between the contract (TASK-001) and the real CORE production, what is the arbitration process (who decides, what timeline)?
- [ ] Is there a dual-feed period (stub + CORE in parallel) to validate before cutting the stub?
