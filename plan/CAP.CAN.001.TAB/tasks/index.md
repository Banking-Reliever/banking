# Task Index — Beneficiary Dashboard (CAP.CAN.001.TAB)

## Epic 1 — Event Feed Infrastructure

| ID | Title | Priority | Status | Depends on |
|----|-------|----------|--------|------------|
| TASK-001 | Freeze the consumed events contract | high | todo | — |
| TASK-002 | Feed stub and event consumption layer | high | todo | TASK-001 |

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
| TASK-006 | Real CORE connection and stub decommissioning | low | todo | TASK-002, TASK-003, TASK-004, TASK-005 |

---

## Dependency Graph

```
TASK-001
  └─► TASK-002
        └─► TASK-003
              ├─► TASK-004 (parallel)
              └─► TASK-005 (parallel)
                    └─► TASK-006 (triggered by CORE operational)
```

**Critical path**: TASK-001 → TASK-002 → TASK-003 → TASK-004  
**Parallelizable**: TASK-004 and TASK-005 run in parallel once TASK-003 is complete  
**TASK-006**: outside the internal cadence — triggered by the availability of CORE capabilities (BSP.001, BSP.004)

---

## Business Events Produced

| Event | Produced by |
|-------|-------------|
| `Dashboard.Viewed` (channel=web) | TASK-003, TASK-004 |
| `Dashboard.Viewed` (channel=mobile) | TASK-005 |

## Recommended Starting Point

Start with **TASK-001** — the event contract definition requires coordination with the BSP.001 and BSP.004 teams and is a precondition for everything else.
