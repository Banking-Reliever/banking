---
task_id: TASK-002
capability_id: CAP.CAN.001.TAB
capability_name: Beneficiary Dashboard
epic: Epic 1 — Event Feed Infrastructure
status: todo
priority: high
depends_on: [CAP.BSP.001.SCO/TASK-001, CAP.BSP.001.PAL/TASK-001, CAP.BSP.004.ENV/TASK-001]
---

# TASK-002 — Subscription point and consumption layer for CAP.CAN.001.TAB

## Context
`CAP.CAN.001.TAB` is developed in complete isolation from the CORE capabilities (`CAP.BSP.001.SCO`, `CAP.BSP.001.PAL`, `CAP.BSP.004.ENV`). Per `ADR-BCM-URBA-0009` (producer ownership), each producer capability owns the contract and the development stub of the events it emits — those deliverables live in the producers' own plans (cf. `depends_on`). This task therefore handles only the **consumer-side infrastructure**: queues bound to the producers' topic exchanges, the read model fed from incoming events, and the consumption layer that subsequent epics use to render the dashboard.

The bus topology — RabbitMQ topic exchange per producer, message format, routing key convention — is normative-fixed by `ADR-TECH-STRAT-001` (*Dual-Rail Event Infrastructure*). Per Rule 5, the consumer creates its own queues on each producer's exchange (no producer ever publishes on a consumer's exchange). Per Rule 2, only resource events flow on the bus — business events are design-time abstractions, not transported.

When the producer-side stubs are decommissioned later (each producer replaces its own stub with the real implementation), the consumption code in this task does **not** change.

## Capability Reference
- Capability: Beneficiary Dashboard (CAP.CAN.001.TAB)
- Zone: CHANNEL
- Governing ADRs: ADR-BCM-FUNC-0009, ADR-BCM-URBA-0007, ADR-BCM-URBA-0009, **ADR-TECH-STRAT-001**

## What needs to be produced

### Subscription wiring (RabbitMQ)
The consumer creates **three queues**, each bound to one of the producers' topic exchanges (Rule 5 of ADR-TECH-STRAT-001):

| Queue (consumer-owned) | Bound on producer exchange owned by | Routing key | RVT event consumed |
|---|---|---|---|
| `can.001.tab.score-courant` | `CAP.BSP.001.SCO` | `EVT.BSP.001.SCORE_RECALCULE.RVT.BSP.001.SCORE_COURANT_RECALCULE` | `RVT.BSP.001.SCORE_COURANT_RECALCULE` |
| `can.001.tab.franchissement` | `CAP.BSP.001.PAL` | `EVT.BSP.001.PALIER_HAUSSE.RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE` | `RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE` |
| `can.001.tab.consommation` | `CAP.BSP.004.ENV` | `EVT.BSP.004.ENVELOPPE_CONSOMMEE.RVT.BSP.004.CONSOMMATION_ENREGISTREE` | `RVT.BSP.004.CONSOMMATION_ENREGISTREE` |

This wiring is the runtime materialization of the BCM-declared subscriptions:
- **Resource subscriptions** (`SUB.RESOURCE.CAN.001.001/002/003`) → translate directly into the three queue bindings above (one per RVT event).
- **Business subscriptions** (`SUB.BUSINESS.CAN.001.001/002/003`) → governance-level declarations of lifecycle dependency per `ADR-BCM-URBA-0009`; they do **not** generate additional bus traffic (per `ADR-TECH-STRAT-001` Rule 2, business events do not produce autonomous messages).

### Consumption layer
A component that reads incoming RVT messages from the three queues and maintains a **read model per beneficiary case** (`identifiant_dossier`) containing:
- The current behavioural score (fed by `RVT.BSP.001.SCORE_COURANT_RECALCULE` payloads)
- The active tier (fed by `RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE` payloads)
- The open envelopes per spending category, with available balance derived as `montant_plafond - montant_consomme` (fed by `RVT.BSP.004.CONSOMMATION_ENREGISTREE` payloads)

The consumer **must validate every incoming payload against the runtime JSON Schema published by the producer capability** (`RVT.*.schema.json` files under `plan/CAP.BSP.001.SCO/contracts/`, `plan/CAP.BSP.001.PAL/contracts/`, `plan/CAP.BSP.004.ENV/contracts/`). Any payload that does not validate is rejected with a structured error (no silent acceptance of malformed events). The `EVT.*.schema.json` files are design-time documentation only and are **not** used at runtime by this consumer.

The read model is the sole data source for the views built in TASK-003, TASK-004, TASK-005.

### Beneficiary identity resolution
Incoming payloads carry `identifiant_dossier` (case ID) as the correlation key. To resolve to the canonical beneficiary identity (`identifiant_interne` of `OBJ.REF.001.BENEFICIAIRE`), the consumption layer performs a lookup against `CAP.REF.001.BEN`. This lookup is encapsulated so subsequent views never see `identifiant_dossier` directly.

### End-to-end test scenario
At the end of this task, with the three producer-side stubs running, a simulated test beneficiary must be viewable end-to-end (RVT messages produced by the stubs → validated → read model populated → resolvable via `CAP.REF.001.BEN` lookup) without any real CORE implementation.

## Business Events to Produce
No business events produced by this task — it establishes the consumer-side infrastructure only.

## Business Objects Involved
- **Beneficiary** (`OBJ.REF.001.BENEFICIAIRE`) — canonical identity, resolved via `CAP.REF.001.BEN`
- **Behavioral evaluation**, **Tier change**, **Budget allocation** — current state maintained in the read model

## Required Event Subscriptions
The six BCM-declared subscriptions (`SUB.BUSINESS.CAN.001.001/002/003` + `SUB.RESOURCE.CAN.001.001/002/003`) are honored. Wire-level traffic materializes as **three** RVT-event bindings (per `ADR-TECH-STRAT-001` Rule 2). Their event contracts are the runtime JSON Schemas produced by the depended-upon producer tasks.

## Definition of Done
- [ ] Three RabbitMQ queues are declared, each bound on the routing key of one producer's RVT event (cf. wiring table)
- [ ] No queue is bound on a producer's exchange other than via the table — no producer's exchange is written to by this consumer (Rule 5 compliance)
- [ ] The consumption layer validates every incoming payload against the runtime JSON Schema (`RVT.*.schema.json`) of the producing capability — non-validating payloads are rejected with a structured error
- [ ] The consumption layer maintains a read model per `identifiant_dossier` containing: current score, active tier, open envelopes with derived available balance per category
- [ ] Beneficiary identity resolution from `identifiant_dossier` to `identifiant_interne` is performed through `CAP.REF.001.BEN` (lookup encapsulated; consumer-side views never expose `identifiant_dossier`)
- [ ] An end-to-end test scenario demonstrates: producer stubs running → RVT messages published → consumer validates → read model populated → identity resolved
- [ ] Replacing any producer-side stub with the real implementation requires no modification of the consumption code in this capability
- [ ] `python tools/validate_repo.py` passes without error
- [ ] `python tools/validate_events.py` passes without error

## Acceptance Criteria (business)
A developer working on TASK-003 (current situation web view), TASK-004 (transaction history) or TASK-005 (mobile view) can read the read model maintained by this task and render a test beneficiary's data without waiting for any other team. The data flowing into the read model is consistent with the events published by the producer-side stubs and is identity-resolved to the canonical beneficiary record.

## Dependencies
- **`CAP.BSP.001.SCO/TASK-001`** — JSON Schemas + stub for `RVT.BSP.001.SCORE_COURANT_RECALCULE` (runtime contract) + `EVT.BSP.001.SCORE_RECALCULE` (design-time documentation)
- **`CAP.BSP.001.PAL/TASK-001`** — JSON Schemas + stub for `RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE` (runtime) + `EVT.BSP.001.PALIER_HAUSSE` (documentation)
- **`CAP.BSP.004.ENV/TASK-001`** — JSON Schemas + stub for `RVT.BSP.004.CONSOMMATION_ENREGISTREE` (runtime) + `EVT.BSP.004.ENVELOPPE_CONSOMMEE` (documentation)

## Resolved Questions

- ✅ **Event bus technology** — Resolved via `ADR-TECH-STRAT-001` (*Dual-Rail Event Infrastructure*). RabbitMQ operational rail; topic exchange per producer L2; consumer creates its own queues bound on the producers' exchanges (Rule 5); only resource events transit on the bus (Rule 2); routing key convention `{BusinessEventName}.{ResourceEventName}` (Rule 4); schema governance is design-time, BCM YAML is authoritative (Rule 6).

## Open Questions
- [ ] Identity resolution toward `CAP.REF.001.BEN` — is `CAP.REF.001.BEN` already operational (real or stubbed)? If absent, this task may need to assume a local lookup stub or escalate a dependency on `CAP.REF.001.BEN`'s own contract+stub task (which would be analogous to the three producer tasks above). This question may itself require creating a contract+stub task on `CAP.REF.001.BEN` as a producer of the beneficiary read model — out of scope of TASK-002 itself, but a likely escalation.
