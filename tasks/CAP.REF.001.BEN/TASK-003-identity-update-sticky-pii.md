---
task_id: TASK-003
capability_id: CAP.REF.001.BEN
capability_name: Beneficiary Referential
epic: Epic 2 — Identity maintenance (UPDATE)
status: todo
priority: high
depends_on: [TASK-002]
task_type: full-microservice
loop_count: 0
max_loops: 10
---

# TASK-003 — Identity maintenance with sticky-PII semantics (UPDATE)

## Context
Beneficiaries' identity fields change occasionally over the lifetime of the
programme — most often contact details (phone, address, email), more rarely
legal name corrections. This task adds the UPDATE path to the canonical
referential under strict **sticky-PII** semantics: a partial payload only
mutates the fields it carries; absent or null fields are left unchanged
(per `INV.BEN.003`). The risk being mitigated is accidental PII erasure
under a partial integration — a critical concern for a vulnerable
population.

The aggregate, the directory projection, the RVT family, the bus exchange,
and the transactional outbox already exist from TASK-002. This task plugs
a new command and a new transition kind into them; it does not re-scaffold
infrastructure.

## Capability Reference
- Capability: Beneficiary Referential (CAP.REF.001.BEN)
- Zone: REFERENTIAL
- Governing FUNC ADR: `ADR-BCM-FUNC-0013`
- Strategic-tech anchors:
  - `ADR-TECH-STRAT-001` (event infrastructure — same exchange/routing key as TASK-002)
  - `ADR-TECH-STRAT-004` (PII governance — sticky-PII rule lives here)

## What to Build

### UPDATE command
`CMD.REF.001.BEN.UPDATE_BENEFICIARY_IDENTITY` — bound to
`PATCH /beneficiaries/{internal_id}`.

- Accepts a **partial** payload of identity fields. Only fields **present**
  in the request body are applied; absent fields are left unchanged.
- `null` values inside the payload are treated as "leave unchanged" by
  default. The single exception is a contact channel that the caller wants
  to explicitly clear — this requires a dedicated nullability marker
  (implementation decides the exact wire form; document it in code). PII
  fields are otherwise sticky.
- Idempotency key: caller-supplied `command_id`, 30-day deduplication window
  (per `INV.BEN.007`). A retried command_id returns **200 OK** with the
  previously emitted result; no second RVT is published.
- Precondition: aggregate must exist (404 `BENEFICIARY_NOT_FOUND` if not).
- Precondition: `referential_status` must be `ACTIVE` (409
  `BENEFICIARY_ARCHIVED` if archived — caller must RESTORE first, see TASK-004).
- Precondition: payload carries at least one mutable field (400
  `NO_FIELDS_TO_UPDATE` otherwise).
- Request body MUST validate against
  `process/CAP.REF.001.BEN/schemas/CMD.REF.001.BEN.UPDATE_BENEFICIARY_IDENTITY.schema.json`.
- Response body on 200: the post-transition canonical record (same shape as
  the GET endpoint), reflecting the merged state.

### RVT publication
On every accepted UPDATE, emit one
`RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED` on the existing
`ref.001.ben-events` exchange, with:
- `transition_kind = UPDATED`
- `revision = N + 1` (monotonic over the aggregate's transition history)
- Full post-transition snapshot of the record
- `changed_fields`: the list of field names whose values changed compared to
  the prior revision — required by the history projection (TASK-005) and by
  consumers that want to react narrowly.
- `command_id` from the request, `occurred_at` from the service clock.

### Directory projection update
The `PRJ.REF.001.BEN.BENEFICIARY_DIRECTORY` projection — built in TASK-002
— picks up the new RVT under its last-write-wins-on-(`internal_id`,
`revision`) rule and replaces the row.

### Invariants enforced (this task)
- `INV.BEN.002` — `internal_id` MUST NOT mutate on UPDATE (the path
  parameter binds the aggregate; no field of the payload may overwrite it).
- `INV.BEN.003` — **sticky-PII rule**. The core invariant of this task —
  every property-based test corner must hold.
- `INV.BEN.006` — same RVT family, monotonic `revision`, full snapshot.
- `INV.BEN.007` — idempotency on `command_id` over 30 days.

## Business Events to Produce
- `RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED` with
  `transition_kind=UPDATED` — emitted when an UPDATE command is accepted
  and at least one field actually changed. (A no-op UPDATE — payload
  identical to current state — is still recorded for idempotency but emits
  an RVT with `changed_fields=[]` since it is a real, requested transition.
  Implementation note: the simpler invariant is "every accepted UPDATE
  emits one RVT"; consumers tolerate the empty `changed_fields` case.)

## Business Objects Involved
- `OBJ.REF.001.BENEFICIARY_RECORD` — same canonical record as TASK-002;
  this task mutates a subset of its fields.

## Event Subscriptions Required
None.

## Definition of Done

### Functional
- [ ] `PATCH /beneficiaries/{internal_id}` with a valid partial payload
      returns **200 OK** with the post-transition canonical record body.
- [ ] Only the fields **present** in the request body are mutated; every
      other field of the record retains its previous value.
- [ ] `PATCH` on an unknown `internal_id` returns **404**
      `BENEFICIARY_NOT_FOUND`.
- [ ] `PATCH` on an archived record returns **409**
      `BENEFICIARY_ARCHIVED` and does not mutate state.
- [ ] `PATCH` with a payload carrying no mutable fields returns **400**
      `NO_FIELDS_TO_UPDATE`.
- [ ] `PATCH` with the same `command_id` as a previous accepted command
      returns **200 OK** with the prior result; no new aggregate
      transition; no new RVT.
- [ ] `PATCH` with a payload failing JSON-Schema validation against
      `CMD.REF.001.BEN.UPDATE_BENEFICIARY_IDENTITY.schema.json` returns **400**.

### Sticky-PII corners (property-based tests required)
- [ ] Empty payload `{}` → 400 `NO_FIELDS_TO_UPDATE` (no state change).
- [ ] Payload `{ "first_name": "Alice" }` on a record with
      `last_name = "Doe"` produces a record with `first_name = "Alice"` and
      `last_name = "Doe"` unchanged.
- [ ] Absent fields are NOT silently nulled (the critical corner — INV.BEN.003).
- [ ] Partial sub-object update on `contact_details` (e.g. only
      `phone_number`) merges into the existing sub-object, leaving postal
      address and email intact.
- [ ] Explicit clear of a contact channel via the dedicated nullability
      marker works as documented and is the only way to null a field.
- [ ] A property-based test (e.g. Hypothesis-style or equivalent) generates
      arbitrary partial payloads and asserts the merged state always
      satisfies "untouched fields keep their value, touched fields take
      the requested value, internal_id never moves".

### Bus
- [ ] Every accepted UPDATE produces exactly one RVT on
      `ref.001.ben-events` with routing key
      `EVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED.RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED`.
- [ ] The RVT payload carries `transition_kind=UPDATED`, monotonically
      incremented `revision`, the full post-transition snapshot, the
      `changed_fields` list, the originating `command_id`, and
      `occurred_at`.
- [ ] The RVT payload validates against the RVT JSON Schema (the same
      schema as TASK-002 — `transition_kind=UPDATED` is one of its
      discriminator values).
- [ ] Retried UPDATE on the same `command_id` does NOT re-emit an RVT.
- [ ] Publication is transactionally consistent with the state change
      (transactional outbox semantics from TASK-002).

### Projection
- [ ] The directory projection reflects the post-transition state under
      eventual-consistency; a subsequent `GET /beneficiaries/{internal_id}`
      returns the new field values and incremented `revision`.
- [ ] The ETag of the GET response changes (new revision → new ETag); a
      304 round-trip with the prior ETag now returns 200 with the new body.

### Invariants (proven by tests)
- [ ] `INV.BEN.002` — `internal_id` is unchanged by every UPDATE.
- [ ] `INV.BEN.003` — sticky-PII property holds across the property-based
      test corpus.
- [ ] `INV.BEN.006` — RVT carries full snapshot + monotonic revision +
      `transition_kind=UPDATED`.
- [ ] `INV.BEN.007` — duplicate `command_id` is silently dropped within
      the 30-day window.

## Acceptance Criteria (Business)
A programme operator can correct a beneficiary's contact email without
risking the loss of their postal address. A retried PATCH under
intermittent network conditions does not duplicate work or re-publish
events. A downstream cache (e.g. CAP.CHN.001.DSH local cache) updates
correctly: when the UPDATE arrives, the cached row's fields shift in line
with `changed_fields`, no other field of the cached row is touched, and
the cached `revision` advances by exactly 1.

## Dependencies
- TASK-002 (the aggregate, the RVT family, the directory projection, the
  bus exchange, and the idempotency framework must already exist).

Concurrent with TASK-004 (no shared aggregate state beyond the
status-flip invariants — but the **cross-test** "UPDATE on archived
record returns 409 BENEFICIARY_ARCHIVED" lives partly here and partly in
TASK-004; either task's tests can carry the assertion).

## Open Questions

- [ ] **Explicit-null marker for clearing a contact channel**: the
      sticky-PII rule says PII fields are sticky by default; clearing
      requires a dedicated marker. Concrete wire form is implementation's
      call (a special sentinel object like `{ "phone_number": { "clear":
      true } }` is one option; another is a separate
      `DELETE /beneficiaries/{internal_id}/contact/{channel}` endpoint).
      Pick one, document the choice, and reflect it in the JSON Schema.
      No ADR pre-constrains this.
- [ ] **Should a no-op UPDATE (payload identical to current state) emit an
      RVT?** Two reasonable answers: (a) yes — every accepted command
      produces one event for an auditable command-to-event mapping; (b)
      no — skip emission when `changed_fields` is empty to spare consumer
      noise. Default to (a) since it simplifies the "one accepted command
      = one RVT" invariant; revisit if downstream noise becomes an issue.
