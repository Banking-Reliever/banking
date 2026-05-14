---
task_id: TASK-001
capability_id: CAP.REF.001.BEN
capability_name: Beneficiary Referential
epic: Epic 0 — Contract and Development Stub
status: todo
priority: high
depends_on: []
task_type: contract-stub
loop_count: 0
max_loops: 10
---

# TASK-001 — Contract and development stub for the Beneficiary Referential

## Context
`CAP.REF.001.BEN` is the canonical, programme-wide source of truth for
beneficiary identity (golden-record rule, `ADR-BCM-FUNC-0013`). Every other
L2 in Reliever needs to resolve a beneficiary by `internal_id` — either via
the synchronous HTTP queries or by hydrating a local cache from the
operational bus (`ADR-TECH-STRAT-004` dual-referential-access). Per
`ADR-BCM-URBA-0009`, this capability owns the contract of every event it
emits and every API surface it exposes.

This stub is the **earliest runnable embodiment of that contract**. It
publishes the canonical `RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED`
events on the operational bus with simulated values, AND serves the three
GET endpoints of the query surface with canned cold data. Every consumer
in the programme (CAP.BSP.001.SCO, CAP.BSP.002.ENR, CAP.BSP.004.ENV,
CAP.CHN.001.DSH, CAP.CHN.002.VUE, CAP.B2B.001.FLW, CAP.DAT.*) can develop
their identity-resolution flows in complete isolation from the real
domain logic, against this stub.

The bus topology (RabbitMQ topic exchange owned by this capability,
routing key `{BusinessEventName}.{ResourceEventName}`, payload form =
domain-event DDD with full snapshot) is fixed by `ADR-TECH-STRAT-001`.
The HTTP surface follows `ADR-TECH-STRAT-003`. PII governance (no other
capability may hold a private mirror of PII fields — `internal_id` is the
master key) follows `ADR-TECH-STRAT-004`.

## Capability Reference
- Capability: Beneficiary Referential (CAP.REF.001.BEN)
- Zone: REFERENTIAL
- Governing FUNC ADR: `ADR-BCM-FUNC-0013`
- Strategic-tech anchors:
  - `ADR-TECH-STRAT-001` (operational bus rail — NORMATIVE for the
    exchange, routing key, and payload form below)
  - `ADR-TECH-STRAT-003` (REST API contract strategy)
  - `ADR-TECH-STRAT-004` (PII governance + dual-referential-access)
  - `ADR-BCM-URBA-0009` (event meta-model — producer-owned contracts)
- Tactical-tech ADRs: none yet (`bcm-pack` warning — captured in Open
  Questions for the foundation task TASK-002).

## What to Build
A runnable development stub under `sources/CAP.REF.001.BEN/stub/` that:

1. **Publishes resource events** for the single RVT family declared in
   `process/CAP.REF.001.BEN/bus.yaml` — on the capability's owned topic
   exchange, with the routing-key convention from `ADR-TECH-STRAT-001`,
   at a configurable cadence (default 1–10 events/min). Every payload
   validates against
   `process/CAP.REF.001.BEN/schemas/RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED.schema.json`
   before publication.
2. **Serves the query surface** for the three GET operations declared in
   `process/CAP.REF.001.BEN/api.yaml` — returning canned cold data shaped
   to the response schemas declared in `process/CAP.REF.001.BEN/read-models.yaml`.
   Pre-seeded with at least 3 representative beneficiary fixtures that
   consumers can reliably retrieve by stable IDs.
3. **Is activatable / deactivatable** via `STUB_ACTIVE=true|false`
   (inactive in production). When `STUB_ACTIVE=false`, the stub neither
   publishes events nor serves HTTP responses (the latter falls through
   to 503 or to the real implementation when present).
4. **Is self-validating** — every outgoing payload (RVT message AND HTTP
   response body) is validated against its JSON Schema before emission.
   This check is automated in a CI unit test independent of bus/HTTP
   availability.

The stub is decommissioned (or kept permanently inert via
`STUB_ACTIVE=false`) when the real implementation tasks (TASK-002
foundation + TASK-003 UPDATE + TASK-004 ARCHIVE/RESTORE + TASK-005
history/secondary lookups) collectively reach feature parity for the
covered surfaces — the README of the stub documents this criterion.

## Events to Stub

`process/CAP.REF.001.BEN/bus.yaml` declares **one** resource event family
that covers all four transition kinds (the kind of transition is carried
in the `transition_kind` payload field — REGISTERED | UPDATED | ARCHIVED |
RESTORED). The stub MUST publish messages of each transition kind so
consumers can exercise the full router on their side.

| Event family | Routing key | Schema | Carried |
|---|---|---|---|
| `RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED` (paired pivot `EVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED`) | `EVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED.RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED` | `process/CAP.REF.001.BEN/schemas/RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED.schema.json` | `RES.REF.001.BENEFICIARY_IDENTITY` (full-snapshot) |

Bus topology:

- **Broker**: RabbitMQ (operational rail).
- **Exchange**: `ref.001.ben-events` — topic, durable, owned exclusively
  by `CAP.REF.001.BEN` (Rule 5 of ADR-TECH-STRAT-001).
- **Payload form**: domain-event DDD with full post-transition snapshot
  + monotonic `revision` + `transition_kind` discriminator (cf.
  `INV.BEN.006` in the process model).
- **Per Rule 2** of `ADR-TECH-STRAT-001`: NO autonomous `EVT.*` message
  is published — the business event appears only as the prefix of the
  routing key.
- **Correlation key**: `internal_id`.

The stub emits all four `transition_kind` variants in a representative
mix over time:
- `REGISTERED` (most common — initial appearance of a fixture)
- `UPDATED` (contact-detail edits — secondary)
- `ARCHIVED` / `RESTORED` (rarer — exercise the lifecycle discriminator
  on the consumer side)

`revision` is monotonic per `internal_id`. Each fixture starts at
revision 1 on its REGISTERED emission, increments by 1 on every
subsequent transition. The stub maintains this counter in memory across
its lifetime; on restart it may start fresh (canned cold data — no
persistence guarantee).

## Query Operations to Stub

`process/CAP.REF.001.BEN/api.yaml` declares three GET operations on the
query surface (the four POST/PATCH operations are command-side and out
of scope for the stub — they belong to TASK-002+).

| Operation | Path | Serves | Response shape source |
|---|---|---|---|
| `getBeneficiary` | `GET /beneficiaries/{internal_id}` | `QRY.REF.001.BEN.GET_BENEFICIARY` | `read-models.yaml` → `PRJ.BENEFICIARY_DIRECTORY` fields |
| `getBeneficiaryByExternalId` | `GET /beneficiaries/by-external-id/{external_id}` | `QRY.REF.001.BEN.GET_BENEFICIARY_BY_EXTERNAL_ID` | `read-models.yaml` → `PRJ.BENEFICIARY_DIRECTORY` fields (subset per query response) |
| `listBeneficiaryHistory` | `GET /beneficiaries/{internal_id}/history` | `QRY.REF.001.BEN.LIST_BENEFICIARY_HISTORY` | `read-models.yaml` → `PRJ.BENEFICIARY_HISTORY` row fields |

Each endpoint:

- Returns 200 with canned data shaped to the corresponding response
  schema for known IDs.
- Returns 404 for unknown IDs (and an unknown-external_id case for
  the secondary lookup).
- Carries an `ETag` header derived from the fixture's `revision` and a
  `Cache-Control: max-age=30` header on the two single-record GETs
  (per `read-models.yaml` cache config).
- Responds to `If-None-Match` matching the current ETag with **304 Not
  Modified** and no body.
- For `listBeneficiaryHistory`, honours `since` (ISO-8601, optional) and
  `limit` (integer, default 50, hard max 500) query parameters against
  the canned history rows.

## Fixtures

The stub is pre-seeded with **at least 3 representative beneficiary
fixtures**, each with a stable `internal_id` and `external_id` so
consumers can write deterministic integration tests. Recommended seed:

| Fixture | `internal_id` (illustrative) | `external_id` | Status | History (transitions seeded) |
|---|---|---|---|---|
| Alice — happy path | `BEN-STUB-0001` | `CAND-STUB-0001` | ACTIVE | REGISTERED at T0, UPDATED at T0+1h |
| Bob — archived | `BEN-STUB-0002` | `CAND-STUB-0002` | ARCHIVED | REGISTERED at T0, ARCHIVED at T0+1d |
| Carla — restored | `BEN-STUB-0003` | `CAND-STUB-0003` | ACTIVE | REGISTERED at T0, ARCHIVED at T0+1d, RESTORED at T0+2d |

Concrete ID strings are illustrative; pick a stable, documented format
(ULID/UUIDv7/short slug) and freeze it in the stub's README. Consumers
must be able to refer to these IDs in their test code without re-reading
the stub's source.

The stub publishes the corresponding seed history on the bus at startup
(so a consumer that subscribes after stub launch still gets the full
history via replay-on-startup) AND on the configurable cadence
(continuous "fake activity" thereafter — e.g. periodic UPDATE on Alice
to bump contact details, periodic alternating ARCHIVE/RESTORE on a
rotating fixture, etc.).

## Business Objects Involved
- `OBJ.REF.001.BENEFICIARY_RECORD` — the canonical identity object (read
  side: returned by the three GETs; bus side: carried as full snapshot
  in the RVT payload).
- `RES.REF.001.BENEFICIARY_IDENTITY` — the resource carried by the RVT
  (resource-event ECST semantics).

## Required Event Subscriptions
None. The stub is a pure producer + query server.

## Definition of Done

### Layout & gating
- [ ] Stub source code lives under `sources/CAP.REF.001.BEN/stub/` —
      sibling of the future `sources/CAP.REF.001.BEN/backend/` that
      TASK-002+ will populate.
- [ ] `STUB_ACTIVE` env var gates the stub. When `false`, no events are
      published and the HTTP endpoints return 503 (or fall through to a
      real implementation if present in the same process). Default in
      development = `true`, default in production = `false`.

### Bus publication
- [ ] A topic exchange named `ref.001.ben-events` is declared, durable,
      and owned exclusively by this stub (no other publisher).
- [ ] The stub publishes messages on
      `EVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED.RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED`
      at a cadence configurable in 1–10 events/min by default (override
      + justification required outside this range).
- [ ] Every published payload validates against
      `process/CAP.REF.001.BEN/schemas/RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED.schema.json`
      (Draft 2020-12) BEFORE emission.
- [ ] Across the stub's lifetime, all four `transition_kind` values
      (`REGISTERED`, `UPDATED`, `ARCHIVED`, `RESTORED`) appear in the
      stream in a representative mix.
- [ ] `revision` is monotonically increasing per `internal_id`; a
      consumer applying last-write-wins on `(internal_id, revision)`
      converges to a deterministic state.
- [ ] Every payload carries: full post-transition snapshot of the
      record, `revision`, `transition_kind`, `command_id` (synthesised
      for the stub), `occurred_at` (synthesised — stub clock).
- [ ] At stub startup, the seed history of every fixture is replayed
      onto the bus (so a late-binding consumer can still hydrate its
      cache from the bus alone).

### HTTP query surface
- [ ] `GET /beneficiaries/{internal_id}` returns **200** with the
      canonical record body matching the `QRY.GET_BENEFICIARY` response
      shape for known IDs (`BEN-STUB-0001`, `BEN-STUB-0002`,
      `BEN-STUB-0003`), with `ETag` (derived from revision) and
      `Cache-Control: max-age=30`.
- [ ] `GET /beneficiaries/{unknown}` returns **404**.
- [ ] `If-None-Match` matching the current ETag returns **304** with no
      body.
- [ ] `GET /beneficiaries/by-external-id/{external_id}` returns **200**
      with the same record body (shape per `QRY.GET_BENEFICIARY_BY_EXTERNAL_ID`)
      for known external_ids, **404** otherwise. ETag/Cache-Control as
      above.
- [ ] `GET /beneficiaries/{internal_id}/history` returns **200** with a
      chronologically ordered array (ascending revision) for known IDs,
      **404** otherwise. Items carry `revision`, `transition_kind`,
      `changed_fields`, `referential_status_after`, `occurred_at`,
      `command_id`.
- [ ] `since` (ISO-8601, optional) and `limit` (integer, default 50,
      hard max 500) query parameters work on the history endpoint.
- [ ] Every HTTP response body validates against the response shape
      declared in `process/CAP.REF.001.BEN/read-models.yaml` for the
      corresponding query.

### Fixtures
- [ ] At least 3 fixtures are pre-seeded with stable, documented IDs.
- [ ] Each fixture is retrievable by both `internal_id` (primary GET)
      and `external_id` (secondary lookup) — the two endpoints return
      the same record body for the same fixture.
- [ ] Each fixture's seeded history is retrievable via the history
      endpoint with the same row ordering and content as the
      corresponding bus replay.

### Self-validation
- [ ] A CI unit test, runnable without RabbitMQ or HTTP availability,
      asserts: (a) every fixture's RVT payload validates against the
      RVT schema; (b) every fixture's GET response body validates
      against its query response shape; (c) the history response items
      validate against the history projection's row schema.

### Decommissioning
- [ ] The stub's README documents the decommissioning criterion: once
      TASK-002 (foundation), TASK-003 (UPDATE), TASK-004
      (ARCHIVE/RESTORE), and TASK-005 (history + secondary lookups)
      collectively reach feature parity for the events + query surface,
      the stub is either deleted from `sources/CAP.REF.001.BEN/stub/`
      or kept permanently with `STUB_ACTIVE=false` for backwards-
      compatible local dev. The README states explicitly which option
      is chosen.

## Acceptance Criteria (Business)

A developer working on **any consumer** of `CAP.REF.001.BEN` can, using
only the artifacts produced by this task:

1. **Subscribe** a queue to the `ref.001.ben-events` topic exchange,
   bind on `EVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED.#`, receive
   payloads validating against the runtime JSON Schema, and develop
   their local-cache hydration logic — including the discriminator-based
   routing across the four `transition_kind` values.
2. **Call** the three GET endpoints over HTTP and receive canned
   responses validating against the declared query response shapes,
   including the ETag/304 caching contract and the `since`/`limit`
   pagination contract on history.
3. **Develop deterministic integration tests** keyed on the three
   pre-seeded fixture IDs, knowing those IDs remain stable across stub
   restarts and across stub-version upgrades within this task.

When the real implementation (TASK-002 → TASK-005) lands, **no
schema-driven or contract-driven consumer change is required** — the
stub and the real service expose the same wire contracts (same JSON
Schemas, same routing key, same response shapes).

## Dependencies
None. This task is self-founding for the capability.

The four real-implementation tasks (TASK-002 → TASK-005) run **in
parallel** with this stub — they do not declare a `depends_on` on
TASK-001. The stub is a consumer-facing safety net, not a prerequisite
for the real implementation.

## Open Questions

- [ ] **Fixture ID format**: pick one stable, documented format for the
      stub's `internal_id` values (ULID, UUIDv7, short opaque slug like
      `BEN-STUB-0001`). The illustrative table above uses `BEN-STUB-NNNN`
      for readability; the real implementation will likely use ULID or
      UUIDv7 (TASK-002's own open question). The stub's choice does not
      have to match the real one — consumers parse the field as opaque
      string — but it must be documented and stable.
- [ ] **History row schema source**: `process/CAP.REF.001.BEN/schemas/`
      contains JSON Schemas for the four `CMD.*` and the `RVT.*` but
      not for the history projection row. The stub validates history
      responses against the field list in
      `process/CAP.REF.001.BEN/read-models.yaml` for
      `QRY.LIST_BENEFICIARY_HISTORY`. If a richer schema is later
      authored (in the process layer, by `/process` — never by the
      stub), the stub will pick it up. No action required unless that
      lookup turns out ambiguous during implementation.
- [ ] **Synthesised `command_id` for stub-emitted RVTs**: the RVT
      schema requires a `command_id`. The stub does not have a real
      command flow; it should synthesise stable, identifiable ids (e.g.
      `STUB-CMD-{ULID}`) so consumers' command-id correlation logic
      runs without surprise. Document the prefix convention so consumers
      know stub-origin events are filterable.
