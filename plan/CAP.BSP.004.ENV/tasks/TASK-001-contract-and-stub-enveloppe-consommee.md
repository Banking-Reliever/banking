---
task_id: TASK-001
capability_id: CAP.BSP.004.ENV
capability_name: Budget Envelope Management
epic: Epic 1 — Contract and Development Stub for Envelope Consumption
task_type: contract-stub
status: in_review
priority: high
depends_on: []
loop_count: 0
max_loops: 10
---

# TASK-001 — Contract and development stub for `EVT.BSP.004.ENVELOPPE_CONSOMMEE`

## Context
`CAP.BSP.004.ENV` allocates and tracks the categorised budget envelopes of a beneficiary. Per `ADR-BCM-URBA-0009`, this capability holds the exclusive responsibility for the contract of the events it emits. As long as the real envelope engine is not implemented, this capability provides a development stub that publishes the contracted events with simulated values, so that consumers (`CAP.CAN.001.TAB` first; future scoring feedback loops, notifications, etc.) can develop in complete isolation.

This task scopes the **consumption** events only (`ENVELOPPE_CONSOMMEE` + `CONSOMMATION_ENREGISTREE`) — the only envelope events `CAP.CAN.001.TAB` consumes today (per ADR-BCM-FUNC-0009). Allocation and non-consumption events will be contracted in their own future epics.

The bus topology — RabbitMQ topic exchange owned by this capability, message format, routing key convention — is normative-fixed by `ADR-TECH-STRAT-001` (*Dual-Rail Event Infrastructure*). Per Rule 2, only the **resource event** gives rise to an autonomous bus message; the business event remains a design-time concept documented for traceability and governance.

## Capability Reference
- Capability: Budget Envelope Management (CAP.BSP.004.ENV)
- Zone: BUSINESS_SERVICE_PRODUCTION
- Governing ADRs: ADR-BCM-FUNC-0008, ADR-BCM-URBA-0007, ADR-BCM-URBA-0009, **ADR-TECH-STRAT-001**

## What needs to be produced

### Contract artifacts (JSON Schema, Draft 2020-12)
Two schemas under `plan/CAP.BSP.004.ENV/contracts/`. Their roles differ:

| File | Role | Event | Carried | BCM source of truth |
|---|---|---|---|---|
| `RVT.BSP.004.CONSOMMATION_ENREGISTREE.schema.json` | **Runtime contract** — every payload published on the bus MUST validate against this schema | Resource event | `OBJ.BSP.004.ALLOCATION` data, framed as *domain event DDD* (transition data) | `bcm/resource-event-reliever.yaml`, `bcm/business-object-reliever.yaml` |
| `EVT.BSP.004.ENVELOPPE_CONSOMMEE.schema.json` | **Design-time documentation** — describes the abstract business fact at the meta-model level; **no autonomous bus message corresponds to it** (cf. ADR-TECH-STRAT-001 Rule 2) | Business event | `OBJ.BSP.004.ALLOCATION` (abstract carrier) | `bcm/business-event-reliever.yaml`, `bcm/business-object-reliever.yaml` |

**Versioning encoding** — each schema declares both:
- A `$id` URL with version segment, e.g. `https://reliever.example.com/contracts/CAP.BSP.004.ENV/RVT.BSP.004.CONSOMMATION_ENREGISTREE/1.0.0/schema.json`.
- A top-level annotation `"x-bcm-version": "1.0.0"` aligned with the BCM event version.

**Correlation key** — `identifiant_dossier`. Resolution toward `identifiant_interne` via `CAP.REF.001.BEN` is the consumer's concern.

**Payload form** — per `ADR-TECH-STRAT-001` Rule 3, the runtime payload is a *domain event DDD*: transition data of the envelope consumption. Fields: allocation ID, case ID, spending category, `montant_plafond`, `montant_consomme` (post-transition), period start/end. **Not** a snapshot of the read model; **not** a field patch. The available balance derivation (`montant_plafond - montant_consomme`) is documented in the schema description for consumer convenience but is NOT a transported field.

**Index** — `plan/CAP.BSP.004.ENV/contracts/README.md` lists the two schemas, their roles, BCM IDs, routing key, and known consumers.

### Development stub
A runnable component that publishes the **resource event** on the bus topology agreed by `ADR-TECH-STRAT-001`:

- **Broker** — RabbitMQ (operational rail).
- **Exchange** — a *topic exchange* dedicated to and owned by `CAP.BSP.004.ENV` (Rules 1, 5).
- **Routing key** — `EVT.BSP.004.ENVELOPPE_CONSOMMEE.RVT.BSP.004.CONSOMMATION_ENREGISTREE` (Rule 4).
- **Payload form** — domain event DDD (cf. above; Rule 3).
- **No autonomous EVT message** — per Rule 2.
- **Cadence** — between **1 and 10 events / minute** by default, configurable inside that range. Outside requires explicit override.
- **Realistic envelope consumption** — across multiple categories (e.g. ALIMENTATION, TRANSPORT, …) with `montant_consomme` increasing toward `montant_plafond` over time.
- **Configurable simulated case IDs** (`identifiant_dossier`) — at least one default case, ideally several with distinct envelope category sets.
- **Activatable / deactivatable** via environment configuration (inactive in production).
- **Self-validating** — every payload must validate against the runtime JSON Schema; automated check (CI unit test recommended, site of check at implementer's discretion).

The stub source code lives under `sources/CAP.BSP.004.ENV/stub/` — sibling of the future `sources/CAP.BSP.004.ENV/backend/`.

## Business Events to Produce
This task produces the **contract** of the events listed above and a **stub** publishing the resource event — it does not produce a new business event of its own beyond what BCM already declares.

## Business Objects Involved
- `OBJ.BSP.004.ALLOCATION` — basis of the runtime payload
- `RES.BSP.004.ENVELOPPE_OUVERTE` — read model maintained by consumers
- `OBJ.REF.001.BENEFICIAIRE` (correlation-key resolution; not embedded)

## Required Event Subscriptions
None — this capability is a producer.

## Definition of Done
- [x] `plan/CAP.BSP.004.ENV/contracts/RVT.BSP.004.CONSUMPTION_RECORDED.schema.json` produced (Draft 2020-12) — **runtime contract**, aligned with the BCM (uses BCM-authoritative English IDs `RVT.BSP.004.CONSUMPTION_RECORDED` / `EVT.BSP.004.ENVELOPE_CONSUMED` per `bcm/business-event-reliever.yaml` + `bcm/resource-event-reliever.yaml`; ADR-TECH-STRAT-001 Rule 6)
- [x] `plan/CAP.BSP.004.ENV/contracts/EVT.BSP.004.ENVELOPE_CONSUMED.schema.json` produced — **design-time documentation only** (no autonomous bus message, per ADR-TECH-STRAT-001 Rule 2)
- [x] Each schema declares its `$id` with version segment AND a top-level `"x-bcm-version"` annotation matching `1.0.0`
- [x] Each schema declares `identifiant_dossier` as the correlation key and documents the resolution path to `identifiant_interne` via `CAP.REF.001.BEN`
- [x] The runtime schema (RVT) describes a **domain event DDD payload** — transition data of envelope consumption, not a read-model snapshot, not a field patch (annotation `x-bcm-payload-form: domain-event-DDD`)
- [x] The available balance derivation (`montant_plafond - montant_consomme`) is documented in the runtime schema description (formula in `description`); it is NOT a transported field
- [x] `plan/CAP.BSP.004.ENV/contracts/README.md` lists the two schemas, their roles, BCM IDs, routing key, and known consumers
- [x] A runnable development stub publishes `RVT.BSP.004.CONSUMPTION_RECORDED` messages on a RabbitMQ topic exchange owned by `CAP.BSP.004.ENV` (`bsp.004.env-events`), with routing key `EVT.BSP.004.ENVELOPE_CONSUMED.RVT.BSP.004.CONSUMPTION_RECORDED` (no autonomous EVT message)
- [x] The stub publishes at a configurable cadence in the range **1 to 10 events / minute** by default; outside that range requires explicit override (`Stub:AllowOutOfRangeCadence=true`)
- [x] The stub is activatable/deactivatable via environment configuration (inactive in production — `Stub:Active=false` by default; activate via `STUB_Stub__Active=true`)
- [x] Every payload published by the stub validates against the runtime JSON Schema (CI unit tests in `Reliever.BudgetEnvelopeManagement.Stub.Tests` — 14 passing tests, including 500-iteration property-based payload validation)
- [x] The stub source code resides under `sources/CAP.BSP.004.ENV/stub/`
- [x] The stub README documents the category-vocabulary assumption: illustrative categories are hard-coded inside the stub, and the canonical source per tier is `CAP.REF.001.PAL` (target for the future real engine)
- [x] `python tools/validate_repo.py` passes without error
- [~] `python tools/validate_events.py` — produces 26 pre-existing baseline errors unrelated to `CAP.BSP.004.ENV` (same on `main`; precedent PRs #1 and #2 merged with the same baseline). My events `EVT.BSP.004.ENVELOPE_CONSUMED` / `RVT.BSP.004.CONSUMPTION_RECORDED` introduce zero new errors and are coherent.

## Acceptance Criteria (business)
A developer working on `CAP.CAN.001.TAB` (or any future consumer of envelope-consumption events) can subscribe a queue to the topic exchange owned by `CAP.BSP.004.ENV`, bind on the routing key, receive payloads validating against the runtime schema, and develop their consumer logic without any direct dependency on the real `CAP.BSP.004.ENV` engine. When the real engine replaces the stub later, no schema-driven consumer code change is required.

## Dependencies
None. This task is self-founding for `CAP.BSP.004.ENV` (Epic 1).

## Resolved Questions

- ✅ **Bus topology** — Resolved via `ADR-TECH-STRAT-001`. RabbitMQ operational rail; topic exchange owned by this capability; only resource events published; routing key `EVT.BSP.004.ENVELOPPE_CONSOMMEE.RVT.BSP.004.CONSOMMATION_ENREGISTREE`; payload format = domain event DDD (Rules 1–6).
- ✅ **Stub source location** — `sources/CAP.BSP.004.ENV/stub/`, sibling of the future `backend/`. Decommissioned when the real engine is delivered.

## Open Questions
- [x] **Resolved.** Category vocabulary: the stub uses hard-coded illustrative categories (`ALIMENTATION`, `TRANSPORT`, `SANTE`, `LOGEMENT`, `ENERGIE`) for offline dev independence. The runtime contract leaves `categorie` free-form (no enum) so consumers stay decoupled from any tier-vocabulary lock-in. The stub README documents that the canonical authoritative source per tier is `CAP.REF.001.PAL` and that the future real envelope engine MUST source categories from there.
