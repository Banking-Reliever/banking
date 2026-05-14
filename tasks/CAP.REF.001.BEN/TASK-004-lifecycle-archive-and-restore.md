---
task_id: TASK-004
capability_id: CAP.REF.001.BEN
capability_name: Beneficiary Referential
epic: Epic 3 — Lifecycle states (ARCHIVE + RESTORE)
status: todo
priority: medium
depends_on: [TASK-002]
task_type: full-microservice
loop_count: 0
max_loops: 10
---

# TASK-004 — Lifecycle transitions: ARCHIVE and RESTORE

## Context
Beneficiaries leave the active programme set for many reasons — successful
exit to standard banking, dropout, transfer, end of supervision. The
canonical referential must reflect this lifecycle without erasing the
record (consumers still need to resolve historical references). This task
adds the two non-mutating status flips that govern lifecycle:

- **ARCHIVE** — ACTIVE → ARCHIVED, typically on programme exit.
- **RESTORE** — ARCHIVED → ACTIVE, a rare audited operation that reverses
  an archival applied in error.

Neither command mutates identity fields; both interact with UPDATE
(TASK-003) — UPDATE on an archived record is rejected with code
`BENEFICIARY_ARCHIVED`, RESTORE first.

The aggregate, the directory projection, the RVT family, the bus exchange,
the transactional outbox, and the idempotency framework already exist from
TASK-002. This task adds two more transition kinds to the same single
RVT family.

## Capability Reference
- Capability: Beneficiary Referential (CAP.REF.001.BEN)
- Zone: REFERENTIAL
- Governing FUNC ADR: `ADR-BCM-FUNC-0013` (programme-exit lifecycle covered
  by the L2 narrative)
- Strategic-tech anchors:
  - `ADR-TECH-STRAT-001` (same exchange and routing key as TASK-002/003)
  - `ADR-TECH-STRAT-004` (PII governance — archived records remain
    queryable; redaction is Epic 5/PURGE territory, out of scope)

## What to Build

### ARCHIVE command
`CMD.REF.001.BEN.ARCHIVE_BENEFICIARY` — bound to
`POST /beneficiaries/{internal_id}/archive`.

- Flips `referential_status` from `ACTIVE` to `ARCHIVED`.
- Optional `reason` enum captured in the audit trail (proposed values: e.g.
  `PROGRAMME_EXIT_SUCCESS`, `DROPOUT`, `TRANSFER`, `DECEASED`,
  `OPERATIONAL` — final enum is implementation's call, document it in the
  JSON Schema). The reason is informational; the transition still occurs
  regardless of the value, but it MUST be one of the declared enum members
  if provided.
- Idempotency key: `command_id`, 30-day window (per `INV.BEN.007`).
- Precondition: aggregate must exist (404 `BENEFICIARY_NOT_FOUND` if not).
- Precondition: `referential_status` must be `ACTIVE` (409
  `BENEFICIARY_ALREADY_ARCHIVED` if already archived — per `INV.BEN.004`).
- Request body MUST validate against
  `process/CAP.REF.001.BEN/schemas/CMD.REF.001.BEN.ARCHIVE_BENEFICIARY.schema.json`.
- Response body on 200: the post-transition canonical record (same shape
  as GET), with `referential_status=ARCHIVED`.

### RESTORE command
`CMD.REF.001.BEN.RESTORE_BENEFICIARY` — bound to
`POST /beneficiaries/{internal_id}/restore`.

- Flips `referential_status` from `ARCHIVED` back to `ACTIVE`.
- Requires a non-empty `comment` field (audit context — *why* the
  archival is being reversed). This is mandatory because RESTORE is a rare
  operation that must leave an explanation in the audit trail.
- Idempotency key: `command_id`, 30-day window.
- Precondition: aggregate must exist (404 `BENEFICIARY_NOT_FOUND` if not).
- Precondition: `referential_status` must be `ARCHIVED` (409
  `BENEFICIARY_NOT_ARCHIVED` if already active — per `INV.BEN.005`).
- Request body MUST validate against
  `process/CAP.REF.001.BEN/schemas/CMD.REF.001.BEN.RESTORE_BENEFICIARY.schema.json`.
- Response body on 200: the post-transition record with
  `referential_status=ACTIVE`.

### Cross-command guard
- UPDATE (TASK-003) on a record with `referential_status=ARCHIVED` MUST
  return 409 `BENEFICIARY_ARCHIVED` — this assertion is shared with
  TASK-003 and lives logically here (because it tests the ARCHIVED state's
  consequences). Either task's test corpus may carry the test; the
  integration tests for this task SHOULD include it as well.

### RVT publication
On every accepted ARCHIVE / RESTORE, emit one RVT on the existing
`ref.001.ben-events` exchange with:
- `transition_kind = ARCHIVED` or `RESTORED` respectively.
- Monotonic `revision = N + 1`.
- Full post-transition snapshot of the record (same shape as the other
  RVTs — `INV.BEN.006`).
- For ARCHIVE: `changed_fields=["referential_status"]` plus `reason` if
  provided (carried in the snapshot — implementation defines whether
  `reason` belongs in the projection or only in the RVT/history; the audit
  trail captures it either way).
- For RESTORE: `changed_fields=["referential_status"]` plus `comment` for
  audit context.
- `command_id` and `occurred_at` carried.

### Invariants enforced (this task)
- `INV.BEN.002` — `internal_id` unchanged.
- `INV.BEN.004` — ARCHIVE rejected if already archived.
- `INV.BEN.005` — RESTORE rejected if already active.
- `INV.BEN.006` — RVT with full snapshot + monotonic revision +
  `transition_kind`.
- `INV.BEN.007` — `command_id` idempotency over 30 days.

## Business Events to Produce
- `RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED` with
  `transition_kind=ARCHIVED` — emitted when an ARCHIVE command is accepted.
- `RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED` with
  `transition_kind=RESTORED` — emitted when a RESTORE command is accepted.

Downstream consumers (CAP.BSP.004.ENV stops allocating new periods,
CAP.B2B.001.FLW stops funding the card, etc.) bind on the same routing
key and route on `transition_kind`.

## Business Objects Involved
- `OBJ.REF.001.BENEFICIARY_RECORD` — same canonical record; only
  `referential_status` mutates.

## Event Subscriptions Required
None.

## Definition of Done

### Functional — ARCHIVE
- [ ] `POST /beneficiaries/{internal_id}/archive` on an ACTIVE record
      returns **200 OK** with the post-transition record body
      (`referential_status=ARCHIVED`).
- [ ] An optional `reason` enum value is accepted, validated against the
      declared set, and persisted in the audit trail.
- [ ] ARCHIVE on an unknown `internal_id` returns **404**
      `BENEFICIARY_NOT_FOUND`.
- [ ] ARCHIVE on an already-archived record returns **409**
      `BENEFICIARY_ALREADY_ARCHIVED` and does not mutate state.
- [ ] Retried ARCHIVE on the same `command_id` returns the prior result;
      no new RVT emitted.
- [ ] An archived record remains queryable via
      `GET /beneficiaries/{internal_id}` — it does NOT disappear.

### Functional — RESTORE
- [ ] `POST /beneficiaries/{internal_id}/restore` on an ARCHIVED record
      with a non-empty `comment` returns **200 OK** with the post-
      transition record body (`referential_status=ACTIVE`).
- [ ] RESTORE without a `comment` (or with an empty one) returns **400**.
- [ ] RESTORE on an unknown `internal_id` returns **404**
      `BENEFICIARY_NOT_FOUND`.
- [ ] RESTORE on an already-active record returns **409**
      `BENEFICIARY_NOT_ARCHIVED`.
- [ ] Retried RESTORE on the same `command_id` returns the prior result;
      no new RVT.

### Cross-command guard
- [ ] `PATCH /beneficiaries/{internal_id}` (UPDATE — TASK-003) on an
      archived record returns 409 `BENEFICIARY_ARCHIVED`. After RESTORE,
      the same PATCH succeeds.

### Bus
- [ ] Every accepted ARCHIVE produces exactly one RVT with
      `transition_kind=ARCHIVED` on `ref.001.ben-events`.
- [ ] Every accepted RESTORE produces exactly one RVT with
      `transition_kind=RESTORED` on `ref.001.ben-events`.
- [ ] Both RVTs validate against
      `process/CAP.REF.001.BEN/schemas/RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED.schema.json`
      (the `transition_kind` enum includes both values).
- [ ] Both RVTs carry full post-transition snapshot, monotonic `revision`,
      `command_id`, `occurred_at`, and `changed_fields=["referential_status"]`.
- [ ] Retried command (duplicate `command_id`) does NOT re-emit an RVT.
- [ ] Routing key is unchanged across all four transition kinds:
      `EVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED.RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED`.

### Projection
- [ ] The directory projection reflects the new `referential_status` after
      each transition; a `GET /beneficiaries/{internal_id}` returns the
      updated status and incremented `revision`.
- [ ] An archived record is still resolvable by GET (last-write-wins
      brought in the ARCHIVED row).

### Invariants (proven by tests)
- [ ] `INV.BEN.002` — `internal_id` unchanged after both transitions.
- [ ] `INV.BEN.004` — re-ARCHIVE returns 409.
- [ ] `INV.BEN.005` — re-RESTORE on an active record returns 409.
- [ ] `INV.BEN.006` — RVT carries full snapshot + monotonic revision +
      correct `transition_kind` for both commands.
- [ ] `INV.BEN.007` — duplicate `command_id` is silently dropped (returns
      the prior result, no new RVT).

### End-to-end scenario
- [ ] **Lifecycle round-trip test**: REGISTER → ARCHIVE → RESTORE → UPDATE
      succeeds; the sequence emits exactly 4 RVTs on the bus with
      `transition_kind` values [REGISTERED, ARCHIVED, RESTORED, UPDATED]
      and `revision` values [1, 2, 3, 4]; the final state is ACTIVE with
      the UPDATE applied.

## Acceptance Criteria (Business)
A programme operator can mark a beneficiary as exited from the programme
when their dropout is confirmed; downstream capabilities receive the
ARCHIVED event on the bus and stop allocating new budget periods or
funding cards. If the archival was applied in error, the operator can
restore the beneficiary with a written justification (the `comment`
field), and the same downstream capabilities resume normal handling on
the RESTORED event. Throughout, the canonical record never disappears —
historical references continue to resolve via GET.

## Dependencies
- TASK-002 (aggregate, RVT family, bus exchange, idempotency framework,
  directory projection).

Concurrent with TASK-003 (no shared aggregate state beyond the
status-flip / sticky-PII invariants — the cross-test
"UPDATE on archived record returns 409" lives in both task scopes).

## Open Questions

- [ ] **ARCHIVE `reason` enum members**: which values? Proposed:
      `PROGRAMME_EXIT_SUCCESS`, `DROPOUT`, `TRANSFER`, `DECEASED`,
      `OPERATIONAL`. Confirm with operations/social-work team before
      cementing in the JSON Schema; the enum is *informational* (the
      transition does not branch on it), so renames are safe but the set
      itself should match operational workflows. (Roadmap notes the
      optional `reason` enum but does not pre-commit the members.)
- [ ] **Should the archived record stop appearing in default-list
      results?** Out of scope here (no list endpoint in the API surface);
      flag for the eventual `GET /beneficiaries` list operation if one is
      ever added.
- [ ] **Reason / comment storage at the projection level**: should the
      directory projection carry the latest `reason` (for ARCHIVED) or
      the latest `comment` (for RESTORED)? The audit trail in the
      history projection (TASK-005) will carry the full chronology; the
      directory projection is "current state of identity fields" and
      arguably should NOT carry transient audit context. Default to *not*
      adding these fields to the directory; document the choice.
