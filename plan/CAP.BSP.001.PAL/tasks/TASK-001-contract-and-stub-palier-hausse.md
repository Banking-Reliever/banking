---
task_id: TASK-001
capability_id: CAP.BSP.001.PAL
capability_name: Tier Management
epic: Epic 1 — Contract and Development Stub for Upward Tier Crossing
task_type: contract-stub
status: in_review
priority: high
depends_on: []
loop_count: 0
max_loops: 10
pr_url: https://github.com/Banking-Reliever/banking/pull/1
---

> **Started on:** 2026-04-28

# TASK-001 — Contract and development stub for `EVT.BSP.001.PALIER_HAUSSE`

## Context
`CAP.BSP.001.PAL` manages the autonomy-tier transitions of a beneficiary. Per `ADR-BCM-URBA-0009`, this capability holds the exclusive responsibility for the contract of the events it emits. As long as the real tier engine is not implemented, this capability provides a development stub that publishes the contracted events with simulated values, so that consumers (`CAP.CAN.001.TAB` first; future `CAP.CAN.001.NOT`, card-rules services, etc.) can develop in complete isolation.

This task scopes the **upward crossing** events only (`PALIER_HAUSSE` + `FRANCHISSEMENT_ENREGISTRE`) — they are the only tier events `CAP.CAN.001.TAB` consumes today (per ADR-BCM-FUNC-0009). The downgrade and override events will be contracted in their own future epics (cf. plan).

The bus topology — RabbitMQ topic exchange owned by this capability, message format, routing key convention — is normative-fixed by `ADR-TECH-STRAT-001` (*Dual-Rail Event Infrastructure*). Per Rule 2, only the **resource event** gives rise to an autonomous bus message; the business event remains a design-time concept documented for traceability and governance.

## Capability Reference
- Capability: Tier Management (CAP.BSP.001.PAL)
- Zone: BUSINESS_SERVICE_PRODUCTION
- Governing ADRs: ADR-BCM-FUNC-0005, ADR-BCM-URBA-0007, ADR-BCM-URBA-0009, **ADR-TECH-STRAT-001**

## What needs to be produced

### Contract artifacts (JSON Schema, Draft 2020-12)
Two schemas under `plan/CAP.BSP.001.PAL/contracts/`. Their roles differ:

| File | Role | Event | Carried | BCM source of truth |
|---|---|---|---|---|
| `RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE.schema.json` | **Runtime contract** — every payload published on the bus MUST validate against this schema | Resource event | `OBJ.BSP.001.CHANGEMENT_PALIER` data, framed as *domain event DDD* (transition data) | `bcm/resource-event-reliever.yaml`, `bcm/business-object-reliever.yaml` |
| `EVT.BSP.001.PALIER_HAUSSE.schema.json` | **Design-time documentation** — describes the abstract business fact at the meta-model level; **no autonomous bus message corresponds to it** (cf. ADR-TECH-STRAT-001 Rule 2) | Business event | `OBJ.BSP.001.CHANGEMENT_PALIER` (abstract carrier) | `bcm/business-event-reliever.yaml`, `bcm/business-object-reliever.yaml` |

**Versioning encoding** — each schema declares both:
- A `$id` URL with version segment, e.g. `https://reliever.example.com/contracts/CAP.BSP.001.PAL/RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE/1.0.0/schema.json`.
- A top-level annotation `"x-bcm-version": "1.0.0"` aligned with the BCM event version.

**Correlation key** — `identifiant_dossier`. Resolution toward `identifiant_interne` via `CAP.REF.001.BEN` is the consumer's concern.

**Payload form** — per `ADR-TECH-STRAT-001` Rule 3, the runtime payload is a *domain event DDD*: transition data of the tier change. Fields: case ID, previous tier code, new tier code, transition direction (`FRANCHISSEMENT`), trigger source (`ALGORITHME` / `SURCHARGE_PRESCRIPTEUR`), score at transition time. **Not** a snapshot of the read model; **not** a field patch.

**Direction constraint** — the runtime schema constrains `sens` to `FRANCHISSEMENT` (upward direction) for Epic 1 scope. Downgrades (`RETROGRADATION`) and overrides will be contracted in a future epic.

**Index** — `plan/CAP.BSP.001.PAL/contracts/README.md` lists the two schemas, their roles, BCM IDs, the routing key, and the consumers known today.

### Development stub
A runnable component that publishes the **resource event** on the bus topology agreed by `ADR-TECH-STRAT-001`:

- **Broker** — RabbitMQ (operational rail).
- **Exchange** — a *topic exchange* dedicated to and owned by `CAP.BSP.001.PAL` (Rules 1, 5).
- **Routing key** — `EVT.BSP.001.PALIER_HAUSSE.RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE` (Rule 4).
- **Payload form** — domain event DDD (cf. above; Rule 3).
- **No autonomous EVT message** — per Rule 2.
- **Cadence** — between **1 and 10 events / minute** by default, configurable inside that range. Outside requires explicit override.
- **Realistic upward transitions** — a configurable progression sequence (e.g. T0 → T1 → T2) across simulated case IDs.
- **Configurable simulated case IDs** (`identifiant_dossier`).
- **Activatable / deactivatable** via environment configuration (inactive in production).
- **Self-validating** — every payload must validate against the runtime JSON Schema; automated check (CI unit test recommended, site of check at implementer's discretion).

The stub source code lives under `sources/CAP.BSP.001.PAL/stub/` — sibling of the future `sources/CAP.BSP.001.PAL/backend/`.

## Business Events to Produce
This task produces the **contract** of the events listed above and a **stub** publishing the resource event — it does not produce a new business event of its own beyond what BCM already declares.

## Business Objects Involved
- `OBJ.BSP.001.CHANGEMENT_PALIER` — basis of the runtime payload
- `RES.BSP.001.FRANCHISSEMENT` — read model maintained by consumers
- `OBJ.REF.001.BENEFICIAIRE` (correlation-key resolution; not embedded)

## Required Event Subscriptions
None — this capability is a producer.

## Definition of Done
- [ ] `plan/CAP.BSP.001.PAL/contracts/RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE.schema.json` produced (Draft 2020-12) — **runtime contract**, aligned with the BCM
- [ ] `plan/CAP.BSP.001.PAL/contracts/EVT.BSP.001.PALIER_HAUSSE.schema.json` produced — **design-time documentation only** (no autonomous bus message, per ADR-TECH-STRAT-001 Rule 2)
- [ ] Each schema declares its `$id` with version segment AND a top-level `"x-bcm-version"` annotation matching `1.0.0`
- [ ] Each schema declares `identifiant_dossier` as the correlation key and documents the resolution path to `identifiant_interne` via `CAP.REF.001.BEN`
- [ ] The runtime schema (RVT) describes a **domain event DDD payload** — transition data of the upward tier crossing, not a read-model snapshot, not a field patch
- [ ] The runtime schema constrains `sens` to `FRANCHISSEMENT` (upward) — downward crossings are out of Epic 1 scope
- [ ] `plan/CAP.BSP.001.PAL/contracts/README.md` lists the two schemas, their roles, BCM IDs, routing key, and known consumers
- [ ] A runnable development stub publishes `RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE` messages on a RabbitMQ topic exchange owned by `CAP.BSP.001.PAL`, with routing key `EVT.BSP.001.PALIER_HAUSSE.RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE` (no autonomous EVT message)
- [ ] The stub publishes at a configurable cadence in the range **1 to 10 events / minute** by default; outside that range requires explicit override
- [ ] The stub is activatable/deactivatable via environment configuration (inactive in production)
- [ ] Every payload published by the stub validates against the runtime JSON Schema (automated check; CI unit test recommended)
- [ ] The stub source code resides under `sources/CAP.BSP.001.PAL/stub/`
- [ ] `python tools/validate_repo.py` passes without error
- [ ] `python tools/validate_events.py` passes without error

## Acceptance Criteria (business)
A developer working on `CAP.CAN.001.TAB` (or any future consumer of upward tier crossings) can subscribe a queue to the topic exchange owned by `CAP.BSP.001.PAL`, bind on the routing key, receive payloads validating against the runtime schema, and develop their consumer logic without any direct dependency on the real `CAP.BSP.001.PAL` engine. When the real engine replaces the stub later, no schema-driven consumer code change is required.

## Dependencies
None. This task is self-founding for `CAP.BSP.001.PAL` (Epic 1).

## Resolved Questions

- ✅ **Bus topology** — Resolved via `ADR-TECH-STRAT-001`. RabbitMQ operational rail; topic exchange owned by this capability; only resource events published; routing key `EVT.BSP.001.PALIER_HAUSSE.RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE`; payload format = domain event DDD (Rules 1–6).
- ✅ **Stub source location** — `sources/CAP.BSP.001.PAL/stub/`, sibling of the future `backend/`. Decommissioned when the real engine is delivered.

## Open Questions
None — all questions resolved during refinement (2026-04-28).
