# CAP.BSP.004.ENV — Contracts

Event contracts published (or documented) by **Budget Envelope Management** (`CAP.BSP.004.ENV`, BUSINESS_SERVICE_PRODUCTION). These JSON Schemas (Draft 2020-12) are the design-time and runtime source of truth for every envelope-consumption event flowing on the operational rail.

> **Why this folder exists.** Per `ADR-BCM-URBA-0009`, every L2 capability owns the contract of the events it emits. Per `ADR-TECH-STRAT-001` (NORMATIVE) Rule 2, only the **resource event** generates an autonomous bus message — the business event is documented design-time only.
>
> `CAP.BSP.004.ENV` ships these contracts ahead of its real engine (Epic 3 of the capability roadmap) so that consumer capabilities — `CAP.CHN.001.DSH` first, future scoring-feedback loops and notifications next — can develop in complete isolation, validating their consumer logic against the runtime schema and a development stub. When the real engine is delivered, no schema-driven consumer code change is required.

## Schemas

| File | BCM ID | Role | Versioning | Source of truth |
|---|---|---|---|---|
| [`RVT.BSP.004.CONSUMPTION_RECORDED.schema.json`](RVT.BSP.004.CONSUMPTION_RECORDED.schema.json) | `RVT.BSP.004.CONSUMPTION_RECORDED` (resource event) | **Runtime contract.** Every payload published on the bus MUST validate against this schema. | `$id` carries `/1.0.0/`; `x-bcm-version: 1.0.0` matches `bcm/resource-event-reliever.yaml`. | `bcm/resource-event-reliever.yaml`, `bcm/business-object-reliever.yaml` |
| [`EVT.BSP.004.ENVELOPE_CONSUMED.schema.json`](EVT.BSP.004.ENVELOPE_CONSUMED.schema.json) | `EVT.BSP.004.ENVELOPE_CONSUMED` (business event) | **Design-time documentation only.** No autonomous bus message — appears on the wire only as the prefix of the routing key. Per `ADR-TECH-STRAT-001` Rule 2. | `$id` carries `/1.0.0/`; `x-bcm-version: 1.0.0` matches `bcm/business-event-reliever.yaml`. | `bcm/business-event-reliever.yaml`, `bcm/business-object-reliever.yaml` |

Both schemas declare the explicit annotation `"x-bcm-non-normative-on-the-wire": true` on the `EVT.*` schema and `"x-bcm-role": "runtime-contract"` on the `RVT.*` schema, so any tooling (consumer code generators, registry validators) can immediately distinguish the wire-level contract from the design-time view.

## Bus topology — `ADR-TECH-STRAT-001` compliance

| Property | Value | ADR rule |
|---|---|---|
| Broker | RabbitMQ (operational rail) | Rule 1 |
| Exchange (topic, durable) | `bsp.004.env-events` (owned by `CAP.BSP.004.ENV`) | Rules 1, 5 |
| Routing key | `EVT.BSP.004.ENVELOPE_CONSUMED.RVT.BSP.004.CONSUMPTION_RECORDED` | Rule 4 |
| Wire-level event | `RVT.BSP.004.CONSUMPTION_RECORDED` only — no autonomous `EVT.*` message | Rule 2 |
| Payload form | Domain event DDD — transition data of the envelope-consumption transition (post-transition `consumed_amount`, not a snapshot, not a field patch) | Rule 3 |
| Schema governance | Design-time JSON Schemas validate every outgoing payload on the producer side | Rule 6 |

## Correlation key

`case_id` — the participation case identifier owned by `CAP.BSP.002.ENR`. The producer **never** carries the canonical beneficiary identifier `OBJ.REF.001.BENEFICIARY_RECORD.internal_id`. Consumers resolve `case_id → internal_id` via a `CAP.REF.001.BEN` (Beneficiary Reference) lookup as needed.

## Payload form — domain event DDD

Per `ADR-TECH-STRAT-001` Rule 3, the runtime payload is a **domain event DDD**: it carries the data of the envelope-consumption aggregate transition. Fields:

| Field | Kind | Notes |
|---|---|---|
| `allocation_id` | identity | One envelope = one `(case_id, period, category)` triple |
| `case_id` | correlation key | Reference to the participation case |
| `category` | classifier | Spending category — canonical source `CAP.REF.001.TIE` (the stub uses an illustrative vocabulary) |
| `cap_amount` | transition reference | Maximum amount authorised — constant across the period (until recalibration) |
| `consumed_amount` | transition target | Post-transition total consumed amount — domain-event-DDD field |
| `period_start` | scope boundary | ISO-8601 date — start of the active period |
| `period_end` | scope boundary | ISO-8601 date — end of the active period |

The available remaining balance `cap_amount - consumed_amount` is **documented in the runtime schema description** as a consumer convenience but is **NOT a transported field** — it is derived by consumers, keeping the payload minimal and avoiding duplication of derivable state.

## Known and anticipated consumers

| Capability | Subscription | Evidence |
|---|---|---|
| `CAP.CHN.001.DSH` (Beneficiary Dashboard) | Live update of envelope-progress widgets and cap-reached notifications. Binds on `EVT.BSP.004.ENVELOPE_CONSUMED.#`. | `ADR-BCM-FUNC-0009` (CHN.001 channel scoping) |
| Future scoring-feedback loops (`CAP.BSP.001.SCO`) | Behavioural-signal qualification — sustained envelope consumption is a normal-behaviour indicator complementary to the counter-intuitive non-consumption signal. | Anticipated (BCM business-subscription not formalised yet) |
| Future notification capability | Cap-reached and large-consumption alerts. | Anticipated |

## Versioning

- `$id` carries the version segment (`/1.0.0/`) — schemas are addressable by URL with version.
- `x-bcm-version: 1.0.0` mirrors the BCM YAML version of the corresponding event entry.
- Breaking changes increment the major version, are introduced behind a parallel `$id` URL, and require a new ADR per `ADR-BCM-URBA-0009`.

## Related artifacts

- Process Modelling — `process/CAP.BSP.004.ENV/` (read-only contract for AGG / CMD / POL / PRJ / QRY / bus topology)
- Roadmap — `roadmap/CAP.BSP.004.ENV/roadmap.md`
- Development stub — `sources/CAP.BSP.004.ENV/stub/` (publishes `RVT.BSP.004.CONSUMPTION_RECORDED` against the schema in this folder)
- Governing ADRs — `ADR-BCM-FUNC-0008`, `ADR-BCM-URBA-0007`, `ADR-BCM-URBA-0009`, `ADR-TECH-STRAT-001`
