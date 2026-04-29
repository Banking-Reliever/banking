# Plan — Tier Management (CAP.BSP.001.PAL)

## Capability Summary
> Manage the autonomy-tier transitions of a beneficiary based on behavioural score thresholds and prescriber overrides. Emit each transition as a business event so that downstream capabilities (dashboard, notifications, card rules, envelope allocation) can react.

## Strategic Alignment
- **Service offer**: Tier transitions are the visible milestone of beneficiary progression — both motivational (upward crossings) and protective (downgrade following relapse). Cf. `product-vision/product.md`.
- **L1 strategic capability**: SC.001 — Behavioural Remediation (parent: CAP.BSP.001)
- **BCM Zone**: BUSINESS_SERVICE_PRODUCTION
- **Governing ADRs**: ADR-BCM-FUNC-0005 (BSP.001 L2 breakdown), ADR-BCM-URBA-0007 (event meta-model), ADR-BCM-URBA-0009 (capability event responsibility)

## Framing Decisions

- **Contract-first delivery**: per `ADR-BCM-URBA-0009`, this capability owns the contract of every event it emits. The first deliverable is the JSON Schemas of `EVT.BSP.001.PALIER_HAUSSE` and `RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE` plus a development stub publishing them. Consumers (`CAP.CAN.001.TAB`, `CAP.CAN.001.NOT`, future card-rules services) develop against these artifacts without waiting for the real tier engine.
- **Producer-owned stub**: the development stub belongs to this plan, not to consumer plans. It is decommissioned by this capability when the real tier engine is ready, transparently for consumers.
- **Scope of Epic 1 = upward crossings only**: only `EVT.BSP.001.PALIER_HAUSSE` (the *positive* lifecycle milestone) is contracted in Epic 1, because that is what `CAP.CAN.001.TAB` consumes today (per ADR-BCM-FUNC-0009). The other tier events (`PALIER_RETROGRADE`, `PALIER_OVERRIDE_APPLIQUE`) will get their own contract+stub epics when their consumers begin development.
- **Real implementation deferred**: the actual tier engine (rules, persistence, orchestration) is out of scope for the current horizon and will be added when the BSP.001 implementation cycle begins.

---

## Implementation Epics

### Epic 1 — Contract and Development Stub for Upward Tier Crossing
**Objective**: Produce the JSON Schemas for `EVT.BSP.001.PALIER_HAUSSE` and `RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE`, plus a runnable development stub publishing them, so consumer capabilities can develop in isolation.

**Entry condition**: The two events are declared in the BCM (`bcm/business-event-reliever.yaml`, `bcm/resource-event-reliever.yaml`) — already the case.

**Exit condition (DoD)**:
- 2 JSON Schemas (Draft 2020-12) produced under `plan/CAP.BSP.001.PAL/contracts/`, aligned with the BCM
- A development stub publishes both events with simulated tier transitions on the agreed subscription point
- The stub is activatable/deactivatable via environment configuration (inactive in production)
- `validate_repo.py` and `validate_events.py` pass

**Complexity**: S

**Unlocked**: development of `CAP.CAN.001.TAB` (and any future consumer of `EVT.BSP.001.PALIER_HAUSSE`) without dependency on the real tier engine.

**Dependencies**: none.

---

### Epic 2 — Contract and Stub for Downward Crossings and Overrides (deferred)
> Out of scope for the current planning horizon. Triggered when the first consumer of `EVT.BSP.001.PALIER_RETROGRADE` or `EVT.BSP.001.PALIER_OVERRIDE_APPLIQUE` begins development.

### Epic 3 — Real Tier Engine (deferred)
> Out of scope for the current planning horizon. Captures the actual decision rules, persistence, override workflow, and orchestration of all PALIER_* events. Will be expanded when the BSP.001 implementation cycle begins.

---

## Dependency Map

| Epic | Depends on | Type |
|------|-----------|------|
| Epic 1 | none | Founding |
| Epic 2 | Epic 1 | Sequential — deferred |
| Epic 3 | Epics 1, 2 | Sequential — deferred |

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Stub schema drifts from the eventual real engine — consumers break when the real implementation arrives | M | M | The JSON Schemas are the unique source of truth. The real implementation, when delivered (Epic 3), MUST validate against the same schemas. |

---

## Open Questions

- The L3 sub-decomposition of `CAP.BSP.001` (SCO, PAL, etc.) — is `CAP.BSP.001.PAL` an L2 or an L3 under `CAP.BSP.001`? Same question as in the SCO plan; consolidate before Epic 3.
- Should `EVT.BSP.001.PALIER_RETROGRADE` and `EVT.BSP.001.PALIER_OVERRIDE_APPLIQUE` be contracted alongside `PALIER_HAUSSE` even if no consumer needs them yet (defensive contracting), or strictly wait for the first consumer (just-in-time)?
