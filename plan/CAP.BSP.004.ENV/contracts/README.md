# Event contracts — CAP.BSP.004.ENV (Budget Envelope Management)

Owner: **CAP.BSP.004.ENV** (Budget Envelope Management) — L2 of `CAP.BSP.004` (Transaction Control), zone `BUSINESS_SERVICE_PRODUCTION`.

This directory holds the **JSON Schema (Draft 2020-12)** contracts for the envelope-consumption events emitted by `CAP.BSP.004.ENV`. The schemas are derived design-time artefacts produced from the BCM YAML source of truth (`bcm-pack pack CAP.BSP.004.ENV --deep`) and aligned with the canonical process model under `process/CAP.BSP.004.ENV/schemas/` — both the BCM and the process model remain authoritative (ADR-TECH-STRAT-001 Rule 6).

**Epic 1 scope: consumption events only.** `ENVELOPE_CONSUMED` / `CONSUMPTION_RECORDED` are the only envelope events `CAP.CHN.001.DSH` consumes today (per `ADR-BCM-FUNC-0009`). Allocation (`ENVELOPE_ALLOCATED` / `ENVELOPE_INITIALIZED`), depletion (`ENVELOPE_DEPLETED` / `ENVELOPE_CAP_REACHED`) and non-consumption (`ENVELOPE_UNCONSUMED` / `ENVELOPE_PERIOD_WITHOUT_CONSUMPTION`) events will be contracted in their own future epics.

## Schemas

| File | BCM ID | Role | Generates a bus message? | BCM source of truth |
|---|---|---|---|---|
| `RVT.BSP.004.CONSUMPTION_RECORDED.schema.json` | `RVT.BSP.004.CONSUMPTION_RECORDED` | **Runtime contract** — every payload published on the bus by `CAP.BSP.004.ENV` MUST validate against this schema | **Yes** (only this) | `bcm/resource-event-reliever.yaml` (carries `RES.BSP.004.OPEN_ENVELOPE`) + `process/CAP.BSP.004.ENV/schemas/RVT.BSP.004.CONSUMPTION_RECORDED.schema.json` |
| `EVT.BSP.004.ENVELOPE_CONSUMED.schema.json` | `EVT.BSP.004.ENVELOPE_CONSUMED` | **Design-time documentation only** — describes the abstract business fact at the meta-model level | **No** — per `ADR-TECH-STRAT-001` Rule 2 | `bcm/business-event-reliever.yaml` + `bcm/business-object-reliever.yaml` (carries `OBJ.BSP.004.ALLOCATION`) |

## Bus topology (per ADR-TECH-STRAT-001)

| Item | Value |
|---|---|
| Broker | RabbitMQ (operational rail) |
| Exchange type | `topic` |
| Exchange name | `bsp.004.env-events` (owned exclusively by `CAP.BSP.004.ENV` — Rule 1, 5) |
| Routing key | `EVT.BSP.004.ENVELOPE_CONSUMED.RVT.BSP.004.CONSUMPTION_RECORDED` (Rule 4) |
| Wire-level event | `RVT.BSP.004.CONSUMPTION_RECORDED` only — no autonomous `EVT.*` message (Rule 2) |
| Payload form | Domain event DDD — atomic transition data of a single envelope debit (Rule 3) |
| Emitting aggregate | `AGG.BSP.004.ENV.PERIOD_BUDGET` (one instance per `(case_id, period_index)`) |

## Versioning encoding

Each schema declares its version in two places, kept consistent:

- `$id` URL with version segment, e.g. `…/RVT.BSP.004.CONSUMPTION_RECORDED/1.0.0/schema.json`. A new BCM version becomes a new path = explicit deprecation surface.
- Top-level annotation `"x-bcm-version": "1.0.0"` matching the BCM event version. Inspectable without URL parsing.

## Correlation key

Both schemas declare **`case_id`** as the correlation key.

Resolution path to the canonical beneficiary identifier:

```
case_id  ──(query CAP.REF.001.BEN)──►  OBJ.REF.001.BENEFICIARY_RECORD.internal_id
```

The producer **does NOT** carry `internal_id` on the wire (privacy + decoupling, ADR-BCM-URBA-0009). Consumers wishing to obtain the canonical identifier perform the lookup themselves.

## Available balance — derived, not transported

Per `OBJ.BSP.004.ALLOCATION` definition: `available_balance = cap_amount - consumed_amount`.

This formula is **documented** in both schemas' `description` fields but is **NOT** a transported field on either schema. Rationale:

- The runtime payload (`RVT.BSP.004.CONSUMPTION_RECORDED`) is a **domain event DDD** (atomic transition data) — not a snapshot, not a field patch. It carries `consumed_amount_after` and `remaining_amount`, where `remaining_amount = cap_amount - consumed_amount_after` is the materialised available balance at the moment of the transition. `cap_amount` itself is held by consumers from the prior `RVT.BSP.004.ENVELOPE_INITIALIZED` event of the same `allocation_id`.
- The design-time schema (`EVT.BSP.004.ENVELOPE_CONSUMED`) carries `cap_amount` and `consumed_amount` for completeness (it documents the carried business object `OBJ.BSP.004.ALLOCATION` in full), but again `available_balance` is a derived value computed by the consumer — not a wire-level field.

## Known consumers (as of 2026-05-09)

Subscribers that bind a queue to the `bsp.004.env-events` topic exchange with a routing key matching `EVT.BSP.004.ENVELOPE_CONSUMED.#` (or the strict `EVT.BSP.004.ENVELOPE_CONSUMED.RVT.BSP.004.CONSUMPTION_RECORDED`):

| Consumer L2/L3 | Why it cares | Source |
|---|---|---|
| `CAP.CHN.001.DSH` | Beneficiary dashboard — live update of envelope progress widgets and cap-reached notifications. **First consumer in Epic 1.** | `process/CAP.BSP.004.ENV/bus.yaml` (anticipated, by analogy with the SCO model) |
| `CAP.B2B.001.FLW` | Card-funding feedback loop — adjusts authorised funding plans based on real consumption patterns (anticipated; FUNC-ADR-0008 narrative). | FUNC-ADR-0008 narrative — not formal BCM subscription yet |
| Future scoring feedback | Behavioural-score recomputation — counter-intuitive non-consumption signal pairs with consumption to qualify regularity. | Future epic |
| Future notifications | Beneficiary-side notifications on cap-approach thresholds. | Future epic |

## Stub

A development stub publishing simulated `RVT.BSP.004.CONSUMPTION_RECORDED` payloads on the routing key above lives under `sources/CAP.BSP.004.ENV/stub/`. Every payload it publishes is validated against `RVT.BSP.004.CONSUMPTION_RECORDED.schema.json` before being sent — fail-fast on schema violation. The stub is inactive by default (`STUB_ACTIVE=false`); activate it via env var to publish on a configurable cadence in the range **1–10 events/min**.

See `sources/CAP.BSP.004.ENV/stub/README.md` for usage.

## Governance

- Source of truth (per ADR-TECH-STRAT-001 Rule 6): the BCM YAML files reachable via `bcm-pack pack CAP.BSP.004.ENV --deep` (`bcm/business-event-*.yaml`, `bcm/resource-event-*.yaml`, `bcm/business-object-*.yaml`, `bcm/resource-*.yaml`) and the canonical process model at `process/CAP.BSP.004.ENV/`.
- These JSON Schemas are **derived artefacts** — keep them aligned with the BCM and the process model. A BCM version bump → new schema path + new `x-bcm-version`.
- Schema changes that break consumers MUST be tracked via a new BCM version (no silent edits at version `1.0.0`).
- The `process/` folder is the read-only contract — never edited as part of contract publication. Updates to aggregates / commands / events go through the `/process` skill.

## Cross-reference with the process model

- Aggregates: `process/CAP.BSP.004.ENV/aggregates.yaml` (esp. `AGG.BSP.004.ENV.PERIOD_BUDGET` and its invariants `INV.ENV.001`–`INV.ENV.007`).
- Bus topology: `process/CAP.BSP.004.ENV/bus.yaml`.
- Source schema (process): `process/CAP.BSP.004.ENV/schemas/RVT.BSP.004.CONSUMPTION_RECORDED.schema.json`.
