# Event contracts — CAP.BSP.004.ENV (Budget Envelope Management)

Owner: **CAP.BSP.004.ENV** (Budget Envelope Management) — L2 of `CAP.BSP.004` (Transaction Control), zone `BUSINESS_SERVICE_PRODUCTION`.

This directory holds the **JSON Schema (Draft 2020-12)** contracts for the events emitted by `CAP.BSP.004.ENV`. The schemas are derived design-time artefacts produced from the BCM YAML source of truth — the BCM remains authoritative (`ADR-TECH-STRAT-001` Rule 6).

Epic 1 scope: **envelope consumption only** (`EVT.BSP.004.ENVELOPE_CONSUMED` / `RVT.BSP.004.CONSUMPTION_RECORDED`). The other envelope events (`ENVELOPE_ALLOCATED`, `ENVELOPE_UNCONSUMED`, `ENVELOPE_DEPLETED`) will be contracted in their own future epics when their consumers begin development.

## Schemas

| File | BCM ID | Role | Generates a bus message? | BCM source of truth |
|---|---|---|---|---|
| `RVT.BSP.004.CONSUMPTION_RECORDED.schema.json` | `RVT.BSP.004.CONSUMPTION_RECORDED` | **Runtime contract** — every payload published on the bus by `CAP.BSP.004.ENV` MUST validate against this schema | **Yes** (only this) | `bcm/resource-event-reliever.yaml`, `bcm/business-object-reliever.yaml` (carries `OBJ.BSP.004.ALLOCATION` data, framed as domain event DDD) |
| `EVT.BSP.004.ENVELOPE_CONSUMED.schema.json` | `EVT.BSP.004.ENVELOPE_CONSUMED` | **Design-time documentation only** — describes the abstract business fact at the meta-model level | **No** — per `ADR-TECH-STRAT-001` Rule 2 | `bcm/business-event-reliever.yaml`, `bcm/business-object-reliever.yaml` (carries `OBJ.BSP.004.ALLOCATION` abstract) |

## Bus topology (per ADR-TECH-STRAT-001)

| Item | Value | ADR rule |
|---|---|---|
| Broker | RabbitMQ (operational rail) | Rule 1 |
| Exchange type | `topic` | Rule 1 |
| Exchange name | `bsp.004.env-events` (owned exclusively by `CAP.BSP.004.ENV` — Rules 1, 5) | Rules 1, 5 |
| Routing key | `EVT.BSP.004.ENVELOPE_CONSUMED.RVT.BSP.004.CONSUMPTION_RECORDED` | Rule 4 — `{BusinessEventName}.{ResourceEventName}` |
| Wire-level event | `RVT.BSP.004.CONSUMPTION_RECORDED` only — no autonomous `EVT.*` message | Rule 2 |
| Payload form | Domain event DDD — coherent atomic transition data of the envelope consumption; not a snapshot, not a field patch | Rule 3 |
| Schema governance | Design-time; BCM YAML authoritative; no runtime registry | Rule 6 |

## Versioning encoding

Each schema declares its version in two places, kept consistent:

- `$id` URL with version segment, e.g. `…/RVT.BSP.004.CONSUMPTION_RECORDED/1.0.0/schema.json`. A new BCM version becomes a new path = explicit deprecation surface.
- Top-level annotation `"x-bcm-version": "1.0.0"` matching the BCM event version. Inspectable without URL parsing.

## Correlation key

Both schemas declare **`identifiant_dossier`** as the correlation key.

Resolution path to the canonical beneficiary identifier:

```
identifiant_dossier  ──── CAP.REF.001.BEN lookup ────►  OBJ.REF.001.BENEFICIARY_RECORD.identifiant_interne
                                  (Beneficiary Reference)
```

The producer (`CAP.BSP.004.ENV`) NEVER carries `identifiant_interne` on the bus — privacy + decoupling per `ADR-BCM-URBA-0009`. Identity resolution is the consumer's concern.

## Available balance derivation (consumer-side)

The runtime payload carries `montant_plafond` and `montant_consomme` (post-transition). The available balance is **derivable** locally by consumers:

```
solde_disponible = montant_plafond - montant_consomme
```

It is intentionally **NOT a transported field** — keeps the wire surface minimal and authoritative. The formula is documented in the runtime schema's `description` for consumer convenience.

## Domain event DDD vs read model — consumer guidance

The wire payload is **NOT** a snapshot of the read model `RES.BSP.004.OPEN_ENVELOPE`, and **NOT** a technical patch. It carries the coherent atomic transition data of one envelope consumption event. Consumers maintaining a read model are expected to:

1. validate the payload against `RVT.BSP.004.CONSUMPTION_RECORDED.schema.json`;
2. apply the transition to their local read model projection of `RES.BSP.004.OPEN_ENVELOPE`;
3. derive `solde_disponible` if needed.

## Known consumers

| Consumer | Capability ID | Subscription form | ADR |
|---|---|---|---|
| Beneficiary Dashboard | `CAP.CAN.001.TAB` | Topic-bind on `bsp.004.env-events` with routing key pattern `EVT.BSP.004.ENVELOPE_CONSUMED.#` (or the exact `EVT.BSP.004.ENVELOPE_CONSUMED.RVT.BSP.004.CONSUMPTION_RECORDED`) | `ADR-BCM-FUNC-0009` |
| (future) Notification Engine | `CAP.CAN.001.NOT` | tbd | tbd |
| (future) Scoring feedback loop | `CAP.BSP.001.SCO` | tbd | tbd |

Consumers may bind their queue with:
- `EVT.BSP.004.ENVELOPE_CONSUMED.#` to aggregate every resource event linked to the consumption business fact (currently only one), or
- `EVT.BSP.004.ENVELOPE_CONSUMED.RVT.BSP.004.CONSUMPTION_RECORDED` for the precise resource event.

## Local file references

| File | Purpose |
|---|---|
| `RVT.BSP.004.CONSUMPTION_RECORDED.schema.json` | Runtime contract — must hold for every wire-level payload |
| `EVT.BSP.004.ENVELOPE_CONSUMED.schema.json` | Design-time documentation of the abstract business fact (no bus message) |
| `README.md` | This index |

## Development stub

The producer-side development stub for the wire-level event lives at `sources/CAP.BSP.004.ENV/stub/`. It publishes simulated `RVT.BSP.004.CONSUMPTION_RECORDED` payloads on the topic exchange `bsp.004.env-events`, validating each against this runtime schema before publish. See the stub's README for run instructions and CI test details.
