# Task Index — Beneficiary Dashboard (CAP.CHN.001.DSH)

## Epic 1 — Event Feed Infrastructure

> **Restructuring (2026-04-27):** Per `ADR-BCM-URBA-0009` (producer ownership),
> the contracts and the development stubs of the consumed events live in the
> producer plans, not here. The original `TASK-001` of this capability has
> been removed; it is replaced by three producer-side tasks
> (`CAP.BSP.001.SCO/TASK-001`, `CAP.BSP.001.TIE/TASK-001`,
> `CAP.BSP.004.ENV/TASK-001`).

| ID | Title | Priority | Status | Depends on |
|----|-------|----------|--------|------------|
| TASK-002 | Subscription point and consumption layer | high | todo | CAP.BSP.001.SCO/TASK-001, CAP.BSP.001.TIE/TASK-001, CAP.BSP.004.ENV/TASK-001 |

## Epic 2 — Web Dashboard — Current Situation

| ID | Title | Priority | Status | Depends on |
|----|-------|----------|--------|------------|
| TASK-003 | Consent gate and current situation web view | high | todo | TASK-002 |

## Epic 3 — Web Dashboard — Transaction History

| ID | Title | Priority | Status | Depends on |
|----|-------|----------|--------|------------|
| TASK-004 | BSP.004.AUT stub and transaction history web view | medium | todo | TASK-003 |

## Epic 4 — Mobile View — Nomadic Consultation

| ID | Title | Priority | Status | Depends on |
|----|-------|----------|--------|------------|
| TASK-005 | Mobile view — nomadic dashboard consultation | medium | todo | TASK-003 |

## Epic 5 — Connection to Real CORE Capabilities

| ID | Title | Priority | Status | Depends on |
|----|-------|----------|--------|------------|
| TASK-006 | Consumer-side validation against the real CORE event stream | low | todo | TASK-002, TASK-003, TASK-004, TASK-005 |

---

## Dependency Graph

```
CAP.BSP.001.SCO/TASK-001 ─┐
CAP.BSP.001.TIE/TASK-001 ─┼─► TASK-002
CAP.BSP.004.ENV/TASK-001 ─┘     └─► TASK-003
                                       ├─► TASK-004 (parallel)
                                       └─► TASK-005 (parallel)
                                             └─► TASK-006 (consumer-side validation
                                                  triggered by producer cutovers)
```

**Critical path**: 3 producer-side tasks (in parallel) → TASK-002 → TASK-003 → TASK-004
**Parallelizable**: the 3 producer-side tasks can run concurrently; TASK-004 and TASK-005 run in parallel once TASK-003 is complete
**TASK-006**: outside the internal cadence — exercised when the producer plans cut their stubs over to real implementations

---

## Business Events Produced

| Event | Produced by |
|-------|-------------|
| `Dashboard.Viewed` (channel=web) | TASK-003, TASK-004 |
| `Dashboard.Viewed` (channel=mobile) | TASK-005 |

## Recommended Starting Point

The three producer-side tasks (`CAP.BSP.001.SCO/TASK-001`, `CAP.BSP.001.TIE/TASK-001`,
`CAP.BSP.004.ENV/TASK-001`) are now the heads of the chain. They can be developed in
parallel by the respective producer plans. Once they are `done`, this capability's
TASK-002 becomes ready, then the rest of this plan unblocks normally.
