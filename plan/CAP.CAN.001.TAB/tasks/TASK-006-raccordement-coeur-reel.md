---
task_id: TASK-006
capability_id: CAP.CAN.001.TAB
capability_name: Beneficiary Dashboard
epic: Epic 5 — Connection to Real CORE Capabilities
status: todo
priority: low
depends_on: [TASK-002, TASK-003, TASK-004, TASK-005]
---

# TASK-006 — Consumer-side validation against the real CORE event stream

## Context
Epics 1 to 4 have allowed `CAP.CAN.001.TAB` to be fully built and validated in isolation, against the development stubs delivered by the three producer capabilities (`CAP.BSP.001.SCO`, `CAP.BSP.001.PAL`, `CAP.BSP.004.ENV`). Per `ADR-BCM-URBA-0009` (producer ownership), the **decommissioning of each stub is the responsibility of the producer's own plan** — not of this task. When a producer replaces its stub with its real implementation, the JSON Schema contract is unchanged; from the consumer's standpoint, only the source of the events changes.

This task therefore handles only the **consumer-side validation and supervision** that the dashboard continues to behave correctly when the producers cut over from stubs to their real implementations. It is a verification gate on the consumer side, not a code change.

## Capability Reference
- Capability: Beneficiary Dashboard (CAP.CAN.001.TAB)
- Zone: CHANNEL
- Governing ADRs: ADR-BCM-FUNC-0009, ADR-BCM-URBA-0007, ADR-BCM-URBA-0009

## What needs to be produced

### Consumer-side schema validation
Confirm that the events emitted by the real CORE producers continue to validate against the JSON Schemas under `plan/CAP.BSP.001.SCO/contracts/`, `plan/CAP.BSP.001.PAL/contracts/`, `plan/CAP.BSP.004.ENV/contracts/`. The validation logic is the one wired in TASK-002 — this task just exercises it against real producers and confirms zero rejections in the cutover window.

If a real producer emits a payload that does not validate, the divergence is a **producer-side incident**. This task does not absorb it; it surfaces it back to the producer's owners. The CAP.CAN.001.TAB consumption code remains untouched.

### Regression-free validation on both channels
Validate, after each producer's cutover, that:
- The current situation web view (TASK-003) displays data consistent with the real CORE events
- The transaction history web view (TASK-004) is fed by real transactions
- The mobile view (TASK-005) reflects real tier and envelopes
- `Dashboard.Viewed` continues to be produced normally on both channels (web and mobile)
- Identity resolution against `CAP.REF.001.BEN` continues to function

### Production supervision
Confirm, via supervision, that the real event stream feeds the `CAP.CAN.001.TAB` read model continuously and without interruption. Define and document the consumer-side supervision indicators (event ingest rate, validation error rate, lag) — these become the monitoring contract of this capability.

## Business Events to Produce
`Dashboard.Viewed` continues to be produced normally — no change to produced events.

## Business Objects Involved
- **Beneficiary**, **Behavioral evaluation**, **Tier change**, **Budget allocation**, **Transaction** — all now flowing from real producers; the read model schema is unchanged.

## Required Event Subscriptions
Identical to TASK-002 — the wiring is unchanged. Only the producers behind each subscription point change (stubs → real CORE), transparently.

## Definition of Done
- [ ] After each producer's stub-to-real cutover, every received payload validates against the producer's published JSON Schema (zero rejections during the cutover window)
- [ ] The current situation web view (TASK-003) displays real data without regression
- [ ] The transaction history web view (TASK-004) is fed by real transactions without regression
- [ ] The mobile view (TASK-005) displays real data without regression
- [ ] Identity resolution via `CAP.REF.001.BEN` continues to function on real data
- [ ] `Dashboard.Viewed` continues to be produced correctly on both channels
- [ ] Consumer-side supervision indicators (ingest rate, validation error rate, lag) are documented and observable
- [ ] `python tools/validate_repo.py` passes without error
- [ ] `python tools/validate_events.py` passes without error

## Acceptance Criteria (business)
A real beneficiary enrolled in the program views their dashboard and sees their real data (effective tier, real envelopes, history of their actual transactions). The dashboard data is consistent with the decisions made by the real CORE capabilities and is observed without interruption in production supervision.

## Dependencies
- **TASK-002** — consumer-side subscription point + read model + consumption layer must be operational and validated against stubs
- **TASK-003, TASK-004, TASK-005** — all views must be validated on stubs before this task starts
- **External (cross-capability, but not blocking this task's start)**: the real implementations of `CAP.BSP.001.SCO`, `CAP.BSP.001.PAL`, `CAP.BSP.004.ENV` (and `CAP.BSP.004.AUT` for transactions) must reach production. This is **driven by the producer plans, not by this task** — when those producers cut over, this task's verification gate is exercised. If those producers are not yet ready when TASK-002–TASK-005 are done, this task simply waits.

## Open Questions
- [ ] Coordination protocol between producers and this consumer at cutover time — is there a shared change-window calendar, or does each producer cut over independently and this consumer reactively validates? Aligns with the producer plans (Epic 3 decommissioning of each producer stub).
- [ ] Dual-feed period (stub + real in parallel) before the consumer fully cuts to the real source — if desirable, define on which side (producer or consumer) the dual-feed switch lives. Likely producer-side, but to confirm.
