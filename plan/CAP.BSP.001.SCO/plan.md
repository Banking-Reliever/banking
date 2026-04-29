# Plan — Behavioural Score (CAP.BSP.001.SCO)

## Capability Summary
> Compute the behavioural score of a beneficiary from transactions and behavioural signals, and emit the resulting evaluation as business and resource events for downstream capabilities (tier management, dashboards, notifications).

## Strategic Alignment
- **Service offer**: Reliever's behavioural score is the core algorithmic signal driving tier transitions and dashboard motivation. Cf. `product-vision/product.md`.
- **L1 strategic capability**: SC.001 — Behavioural Remediation (parent: CAP.BSP.001 — *Remédiation comportementale*)
- **BCM Zone**: BUSINESS_SERVICE_PRODUCTION
- **Governing ADRs**: ADR-BCM-FUNC-0005 (BSP.001 L2 breakdown), ADR-BCM-URBA-0007 (event meta-model), ADR-BCM-URBA-0009 (capability event responsibility)

## Framing Decisions

- **Contract-first delivery**: per `ADR-BCM-URBA-0009`, this capability owns the contract of every event it emits. The first deliverable is therefore the JSON Schemas of `EVT.BSP.001.SCORE_RECALCULE` and `RVT.BSP.001.SCORE_COURANT_RECALCULE` plus a development stub publishing them on the agreed bus topology. Consumers (`CAP.CAN.001.TAB`, future `CAP.CAN.001.NOT`, etc.) develop against these artifacts without waiting for the real algorithm.
- **Producer-owned stubs**: the development stub belongs to this plan, not to the consumer plans. It is decommissioned by this capability when the real scoring algorithm is ready, without coordination needed from consumers.
- **Real implementation deferred**: the actual scoring algorithm, persistence, and orchestration are out of scope for the current planning horizon. They will be added to this plan when the BSP.001 implementation cycle begins. Today only the *enabling* deliverable (contract + stub) is planned.

---

## Implementation Epics

### Epic 1 — Contract and Development Stub
**Objective**: Produce the JSON Schemas for the events emitted by `CAP.BSP.001.SCO` and a runnable development stub publishing them on the bus, so consumer capabilities can develop in isolation.

**Entry condition**: The events `EVT.BSP.001.SCORE_RECALCULE` and `RVT.BSP.001.SCORE_COURANT_RECALCULE` are declared in the BCM (`bcm/business-event-reliever.yaml`, `bcm/resource-event-reliever.yaml`) — already the case.

**Exit condition (DoD)**:
- 2 JSON Schemas (Draft 2020-12) produced under `plan/CAP.BSP.001.SCO/contracts/`, aligned with the BCM
- A development stub publishes both events with simulated values on the agreed subscription point
- The stub is activatable/deactivatable via environment configuration (inactive in production)
- `validate_repo.py` and `validate_events.py` pass

**Complexity**: S

**Unlocked**: development of `CAP.CAN.001.TAB` (and any future consumer of these events) without dependency on the real BSP.001.SCO implementation.

**Dependencies**: none.

---

### Epic 2 — Real Scoring Algorithm (deferred)
> Out of scope for the current planning horizon. Will be expanded when the BSP.001 implementation cycle begins. Captures the actual algorithmic computation, model versioning, persistence, and orchestration of `EVT.BSP.001.SCORE_RECALCULE` / `EVT.BSP.001.SCORE_SEUIL_ATTEINT`.

---

## Dependency Map

| Epic | Depends on | Type |
|------|-----------|------|
| Epic 1 | none | Founding |
| Epic 2 | Epic 1 (contract is the binding interface) | Sequential — deferred |

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Stub schema drifts from the eventual real algorithm — consumers break when the real implementation arrives | M | M | The JSON Schemas are the unique source of truth. The real implementation, when delivered (Epic 2), MUST validate against the same schemas — same constraint as the stub today. |

---

## Open Questions

- The L3 sub-decomposition of `CAP.BSP.001` (SCO, PAL, etc.) — is `CAP.BSP.001.SCO` an L2 or an L3 under `CAP.BSP.001`? The BCM shows it as an emitting capability but the L2/L3 frontier needs confirmation. Clarification required before Epic 2.
- Production-grade scheduling / batching of score recomputation (per-transaction, periodic, hybrid) — out of scope for Epic 1, must be revisited at Epic 2 entry.
