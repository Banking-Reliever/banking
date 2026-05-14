---
task_id: TASK-002
capability_id: CAP.REF.001.BEN
capability_name: Beneficiary Referential
epic: Epic 1 — Golden-record day-zero (REGISTER + GET + RVT publication)
status: todo
priority: high
depends_on: []
task_type: full-microservice
loop_count: 0
max_loops: 10
---

# TASK-002 — Golden-record foundation: REGISTER + GET + RVT publication

## Context
`CAP.REF.001.BEN` is the **canonical beneficiary referential** — the single
source of truth for every other capability in the Reliever programme that
needs to resolve a beneficiary by `internal_id` (golden-record rule,
`ADR-BCM-FUNC-0013`; dual-referential-access rule, `ADR-TECH-STRAT-004`).
This task delivers the L-complexity day-zero foundation that the entire
programme is gated on: the aggregate exists, beneficiaries can be registered,
the canonical record is queryable via HTTP, and the operational bus carries
the canonical change events so downstream consumers can hydrate their local
caches.

This is the **first real-implementation task** in the whole programme
schedule — every other L2 (CAP.BSP.001.SCO, CAP.BSP.002.ENR,
CAP.BSP.004.ENV, CAP.CHN.001.DSH, CAP.CHN.002.VUE, CAP.B2B.001.FLW) waits on
the wire contract this task crystallises. The TASK-001 contract-stub
already exposes that contract to consumers in cold form; this task is the
real, state-bearing producer.

## Capability Reference
- Capability: Beneficiary Referential (CAP.REF.001.BEN)
- Zone: REFERENTIAL
- Governing FUNC ADR: `ADR-BCM-FUNC-0013` (L2 breakdown of CAP.REF.001 — Common Referentials)
- Strategic-tech anchors:
  - `ADR-TECH-STRAT-001` (Dual-rail event infrastructure — operational rail = RabbitMQ topic exchange, NORMATIVE)
  - `ADR-TECH-STRAT-004` (Data and Referential Layer — PII governance, dual-referential-access, NORMATIVE)
  - `ADR-TECH-STRAT-003` (API contract strategy — REST/HTTP)
  - `ADR-TECH-STRAT-002` (Modular monolith per TOGAF zone — runtime form)
- Tactical-tech ADRs: none yet (`bcm-pack` warning — captured in Open Questions)

## What to Build

### Aggregate
`AGG.REF.001.BEN.BENEFICIARY_IDENTITY` — one instance per beneficiary, keyed
by the **server-generated** `internal_id` (ULID/UUID). The aggregate holds
the canonical state: `internal_id`, `external_id`, `last_name`, `first_name`,
`date_of_birth`, `contact_details`, `referential_status`, `creation_date`,
`last_processed_command_id`, `revision`. Snapshotting strategy: every 50
events. Transactional outbox: **required** (exactly-once handoff between
state change and bus publication).

### REGISTER command
`CMD.REF.001.BEN.REGISTER_BENEFICIARY` — bound to `POST /beneficiaries`.
- The aggregate **generates** `internal_id` server-side; the caller never
  provides it.
- `external_id` (the upstream candidacy/eligibility reference) is the
  idempotency key over the **lifetime** of the record (per `INV.BEN.001`).
- A second REGISTER with the same `external_id` returns **200 OK** with the
  existing record (no duplicate aggregate, no duplicate RVT emitted).
- A first REGISTER returns **201 Created** with the canonical record body
  including the newly generated `internal_id`.
- `last_name`, `first_name`, `date_of_birth` are required — missing/empty
  returns 400 `IDENTITY_FIELDS_MISSING`.
- Request body MUST validate against
  `process/CAP.REF.001.BEN/schemas/CMD.REF.001.BEN.REGISTER_BENEFICIARY.schema.json`
  (Draft 2020-12) at ingress.

### GET endpoint (by internal_id)
`QRY.REF.001.BEN.GET_BENEFICIARY` — bound to `GET /beneficiaries/{internal_id}`.
- Served by the `PRJ.REF.001.BEN.BENEFICIARY_DIRECTORY` projection (current
  state).
- Response body includes all directory fields: `internal_id`, `external_id`,
  `last_name`, `first_name`, `date_of_birth`, `contact_details`,
  `referential_status`, `creation_date`, `last_update_date`, `revision`.
- HTTP caching: `ETag` (derived from `revision`) + `Cache-Control: max-age=30s`.
  A re-fetch with matching `If-None-Match` MUST return 304 Not Modified
  with no body.
- Unknown `internal_id` returns 404.

### Directory projection
`PRJ.REF.001.BEN.BENEFICIARY_DIRECTORY` — last-write-wins on
`(internal_id, revision)`, fed by the local stream of
`RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED` events. Eventual consistency.
Read-side store; write-side store is the aggregate's event store.

### Bus topology and RVT publication
- **Broker**: RabbitMQ (operational rail per `ADR-TECH-STRAT-001`).
- **Exchange**: `ref.001.ben-events` — topic, durable, owned exclusively by
  this capability (Rule 5). The same exchange the stub (TASK-001) owns —
  the real service replaces the stub as the authoritative publisher on
  cutover.
- **Routing key**:
  `EVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED.RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED`
  (Rule 4 — `{BusinessEventName}.{ResourceEventName}`).
- **Payload form**: domain-event DDD with full post-transition snapshot —
  every field of the directory plus `revision`, `transition_kind`,
  `command_id`, `occurred_at` (per `INV.BEN.006`).
- For a REGISTER, the RVT carries `transition_kind=REGISTERED`, `revision=1`.
- The payload MUST validate against
  `process/CAP.REF.001.BEN/schemas/RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED.schema.json`
  before publication.
- Publication happens via the **transactional outbox** — the RVT is committed
  atomically with the state change so a crash between the two cannot lose or
  duplicate the event.
- **No autonomous `EVT.*` message** is published — per Rule 2 of
  `ADR-TECH-STRAT-001`, the business event appears only as the prefix of the
  routing key.

### Invariants enforced (this task)
- `INV.BEN.001` — exactly one beneficiary per `external_id`; idempotent
  re-call returns existing.
- `INV.BEN.002` — `internal_id` is server-generated, immutable for life.
- `INV.BEN.006` — every transition emits exactly one RVT with full snapshot
  + monotonic `revision` + `transition_kind` discriminator.
- `INV.BEN.007` — at most one application per `command_id` (replay-safe).
  For REGISTER, the idempotency anchor is `external_id` not `command_id`,
  but the framework hook MUST exist for the other commands to plug in
  (TASK-003 / TASK-004 rely on it).

## Business Events to Produce
- `RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED` (with
  `transition_kind=REGISTERED`, `revision=1`) — emitted when a new
  beneficiary is registered (REGISTER command accepted).

The paired business-event pivot is
`EVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED` — design-time only, encoded as
the prefix of the routing key (no autonomous bus message).

## Business Objects Involved
- `OBJ.REF.001.BENEFICIARY_RECORD` — the canonical beneficiary identity owned
  by this aggregate (single source of truth in the programme).
- `RES.REF.001.BENEFICIARY_IDENTITY` — the resource carried by the RVT
  (resource-event ECST semantics: full-snapshot).

## Event Subscriptions Required
None. `CAP.REF.001.BEN` has zero upstream subscriptions in the BCM corpus —
it is the source of truth and is driven exclusively by direct API calls.
`policies.yaml` is intentionally empty.

## Definition of Done

### Functional
- [ ] `POST /beneficiaries` with a valid payload (required fields present,
      unknown `external_id`) returns **201 Created** with the canonical record
      body including the server-generated `internal_id` (ULID or UUIDv7).
- [ ] `POST /beneficiaries` with the **same** `external_id` as a previous
      successful call returns **200 OK** with the existing record; no new
      aggregate is created; no new RVT is emitted.
- [ ] `POST /beneficiaries` missing one of `last_name` / `first_name` /
      `date_of_birth` returns **400** with code `IDENTITY_FIELDS_MISSING`.
- [ ] `POST /beneficiaries` with a payload failing JSON-Schema validation
      against `CMD.REF.001.BEN.REGISTER_BENEFICIARY.schema.json` returns
      **400**.
- [ ] `GET /beneficiaries/{internal_id}` returns **200** with the full
      directory shape and an `ETag` header derived from `revision` plus
      `Cache-Control: max-age=30`.
- [ ] `GET /beneficiaries/{internal_id}` with `If-None-Match` matching the
      current ETag returns **304 Not Modified** with no body.
- [ ] `GET /beneficiaries/{unknown}` returns **404**.

### Bus
- [ ] A topic exchange named `ref.001.ben-events` exists, is durable, and
      is owned exclusively by this service (no other publisher — the stub
      from TASK-001 stops publishing once `STUB_ACTIVE=false` at cutover).
- [ ] Every accepted REGISTER produces exactly one RVT message on
      `ref.001.ben-events` with routing key
      `EVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED.RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED`.
- [ ] The RVT payload validates against
      `process/CAP.REF.001.BEN/schemas/RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED.schema.json`
      (Draft 2020-12).
- [ ] The RVT payload carries `transition_kind=REGISTERED`, `revision=1`,
      the full directory snapshot, `command_id`, `occurred_at`.
- [ ] Idempotent re-call of REGISTER does NOT re-emit an RVT.
- [ ] Publication is transactionally consistent with the state change — a
      simulated crash between commit and publish does not leak nor lose the
      RVT (transactional outbox or equivalent).

### Projection
- [ ] After a successful REGISTER, the directory projection contains a row
      for the new beneficiary within the service's eventual-consistency
      window; `GET /beneficiaries/{internal_id}` resolves it.
- [ ] The projection key is `(internal_id, revision)` with last-write-wins
      semantics — a future UPDATE (TASK-003) increments `revision` and the
      projection picks up the latest.

### Invariants (proven by tests)
- [ ] `INV.BEN.001` — second REGISTER with the same `external_id` does not
      create a duplicate aggregate.
- [ ] `INV.BEN.002` — `internal_id` is generated by the service and not
      taken from any field of the request.
- [ ] `INV.BEN.006` — every successful state transition emits exactly one
      RVT with full snapshot + monotonic `revision` + `transition_kind`.
- [ ] `INV.BEN.007` — the idempotency framework exists on the aggregate
      (will be exercised by TASK-003/TASK-004 commands).

### Schema and lineage
- [ ] Request body for REGISTER is validated at HTTP ingress against the
      JSON Schema in `process/CAP.REF.001.BEN/schemas/`.
- [ ] Response body for REGISTER / GET is the canonical record shape from
      `read-models.yaml`.
- [ ] The bus message is validated against the RVT schema before publish.

## Acceptance Criteria (Business)
A consumer team (e.g. CAP.BSP.001.SCO or CAP.CHN.001.DSH) can:

1. POST a beneficiary registration with a candidacy reference and receive
   back a stable `internal_id` they can persist.
2. Retry the same registration under network failure and receive the same
   `internal_id` (idempotent on `external_id`, lifetime window).
3. Query the canonical record by `internal_id` over HTTP with HTTP caching
   working (ETag / 304).
4. Bind a queue to the `ref.001.ben-events` exchange and observe one
   well-formed RVT message per registration (and zero on retried REGISTER).
5. Hydrate their own local cache from the bus stream without ever calling
   the synchronous GET (dual-referential-access path A).

When this task is in production, **no other capability in the Reliever
programme may keep a private mirror of the PII fields owned here**
(golden-record rule). Every consumer keys on `internal_id` from the moment
they first see it on the bus or the synchronous GET.

## Dependencies
None. This task runs in parallel with TASK-001 (the stub) — the stub
exposes the wire contract; this task brings the real, state-bearing
implementation that replaces the stub as the authoritative publisher on
cutover.

Downstream real-implementation tasks of this capability (TASK-003 UPDATE,
TASK-004 ARCHIVE+RESTORE, TASK-005 history + secondary lookups) all
depend on this task — the aggregate, the RVT family, the directory
projection, the bus exchange, and the transactional outbox are built here.

## Open Questions

- [ ] **Upstream caller of REGISTER**: which capability mints the
      `external_id` and calls `POST /beneficiaries`? Most likely
      `CAP.BSP.002.ENR` (Beneficiary Onboarding) once its process model is
      authored. Confirm during contract-agreement step. For now,
      treat the REGISTER request as if the caller is a contract-stable but
      currently unspecified upstream — a contract test against the schema is
      the substitute for an end-to-end test. (From roadmap risk + process
      README open question 2.)
- [ ] **Tactical-tech ADR**: `bcm-pack` reports *No TECH-TACT ADR found with
      capability_id == CAP.REF.001.BEN.* If this task surfaces a load/scale
      or PII-storage decision worth recording (encryption-at-rest scheme,
      read-replica topology, retention split), author one before merging
      and reference it here. Otherwise, defer to follow-up. (From roadmap
      Open Questions + pack warning.)
- [ ] **`internal_id` flavour**: ULID (sortable, 26 chars) vs UUIDv7
      (sortable, 36 chars) vs UUIDv4 (non-sortable). The aggregate
      contract says only "stable identifier"; pick one in implementation
      and document the choice in code/README. UUIDv7 is recommended for
      sortability + standard libraries, but neither choice is constrained
      by ADR.
