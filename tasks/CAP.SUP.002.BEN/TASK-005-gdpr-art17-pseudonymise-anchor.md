---
task_id: TASK-005
capability_id: CAP.SUP.002.BEN
capability_name: Beneficiary Identity Anchor
epic: Epic 5 — GDPR Art. 17 pseudonymisation
status: todo
priority: high
depends_on: [TASK-002, TASK-003, TASK-004]
task_type: full-microservice
loop_count: 0
max_loops: 10
---

# TASK-005 — GDPR Art. 17 pseudonymisation at the anchor

## Context
This is the **differentiating epic** of the capability — the GDPR Art. 17
right-to-be-forgotten mechanics. It is also the **most heavily tested**
task per the roadmap risk matrix: getting crypto-shredding right is
subtle (key strategy, key rotation, recovery semantics) and easy to get
wrong in ways that *look* correct but leave PII recoverable. The
implementation choice (per-anchor vs per-zone keys, Vault transit
configuration) is deferred to the implementer per `ADR-TECH-TACT-002` —
the model only constrains the **observable post-condition**: PII fields
are not recoverable from the database, the `internal_id` survives, and
foreign-key integrity at downstream consumers is preserved.

This is the first task to actually exercise the `pgcrypto` + Vault
transit toolchain in the dev environment. Joint custody applies:
DoD checkboxes that touch PII or pseudonymisation need IT Security and
DPO sign-off (per the roadmap risk matrix).

## Capability Reference
- Capability: Beneficiary Identity Anchor (CAP.SUP.002.BEN)
- Zone: SUPPORT
- Governing FUNC ADR: ADR-BCM-FUNC-0016
- Strategic-tech anchors: ADR-TECH-STRAT-001, ADR-TECH-STRAT-003,
  ADR-TECH-STRAT-004 (PII governance), ADR-TECH-STRAT-007 Rule 7.c
  (privacy-by-design erasure)
- Tactical stack: ADR-TECH-TACT-002 — `pgcrypto` + HashiCorp Vault
  transit + crypto-shredding (Python `psycopg`/`asyncpg`, FastAPI,
  `hvac`)

## What to Build
Extend the microservice from TASK-002–004 to handle
`CMD.SUP.002.BEN.PSEUDONYMISE_ANCHOR`.

1. **Command handler** — `POST /anchors/{internal_id}/pseudonymise` per
   `api.yaml.pseudonymiseAnchor`. Validates against
   `schemas/CMD.SUP.002.BEN.PSEUDONYMISE_ANCHOR.schema.json`. Requires:
   - `command_id` (UUIDv7) — caller-supplied idempotency key
   - `right_exercise_id` (UUIDv7) — references the upstream right
     request from `CAP.SUP.001.RET`
   - `reason` enum — one of `GDPR_ART17_REQUEST`, `REGULATORY_ORDER`,
     `DPO_INITIATED`
2. **State-machine guards** — accepts from ACTIVE or ARCHIVED only
   (`INV.BEN.006`). Rejects with `409 ANCHOR_ALREADY_PSEUDONYMISED` if
   already PSEUDONYMISED (terminal, irreversible). `404
   ANCHOR_NOT_FOUND` for unknown `internal_id`. `400
   RIGHT_EXERCISE_ID_INVALID` if `right_exercise_id` is missing or not
   a UUIDv7.
3. **Crypto-shredding** — wipes `last_name`, `first_name`,
   `date_of_birth`, `contact_details` (the four PII fields of
   `OBJ.SUP.002.BENEFICIARY_RECORD`) so they are NOT recoverable from
   the database. Implementation uses `pgcrypto` + Vault transit per
   `ADR-TECH-TACT-002`. The model constrains only the observable
   post-condition: a DB-level inspection of the anchor row after
   pseudonymisation shows NULL or unrecoverable ciphertext for the four
   PII columns.
4. **Identity preservation** — `internal_id` is UNCHANGED
   (`INV.BEN.002`). Foreign-key integrity at downstream consumers
   survives.
5. **Status transition** — flips `anchor_status` to `PSEUDONYMISED`;
   sets `pseudonymized_at = NOW()`.
6. **Irreversibility** — no `UN_PSEUDONYMISE` command exists. A
   duplicate `command_id` returns the prior result via the idempotency
   path WITHOUT re-running crypto-shredding (idempotent on
   `command_id`, NOT idempotent on outcome — terminal status).
7. **Outbox** — emits one `RVT.SUP.002.BENEFICIARY_ANCHOR_UPDATED` with
   `transition_kind: PSEUDONYMISED`, `revision = N+1`, **PII fields
   null in the payload**, `right_exercise_id` set, `pseudonymized_at`
   set. The conditional `if/then` block of
   `RVT.SUP.002.BENEFICIARY_ANCHOR_UPDATED.schema.json` is exercised.
8. **Cross-command guards** — UPDATE / ARCHIVE / RESTORE issued against
   a PSEUDONYMISED anchor return `409 ANCHOR_PSEUDONYMISED` (already
   enforced by TASK-003 / TASK-004; verified here as cross-verb
   regression tests).
9. **GET surface** — `GET /anchors/{internal_id}` continues to resolve
   the anchor; PII fields come back as `null`; `internal_id` is still
   present so historical references do not break; ETag flips
   immediately.

## Business Events to Produce
- `RVT.SUP.002.BENEFICIARY_ANCHOR_UPDATED` with `transition_kind:
  PSEUDONYMISED` — emitted on successful pseudonymisation. The
  payload's four PII fields are null; `right_exercise_id` is set;
  `pseudonymized_at` is set; `revision = N+1`.

## Business Objects Involved
- `OBJ.SUP.002.BENEFICIARY_RECORD` — terminally pseudonymised; PII
  destroyed, `internal_id` preserved

## Event Subscriptions Required
None in v1 — `PSEUDONYMISE` is HTTP-only. The future reactive policy
(`POL.SUP.002.BEN.ON_RIGHT_EXERCISED`) listening on
`RVT.SUP.001.RET.RIGHT_EXERCISED` from `CAP.SUP.001.RET` is documented
in `policies.yaml` as a deferred Epic 7 (see OQ.BEN.001) and is OUT OF
SCOPE for this task.

## Definition of Done
- [ ] `POST /anchors/{internal_id}/pseudonymise` accepts requests,
      validates against
      `schemas/CMD.SUP.002.BEN.PSEUDONYMISE_ANCHOR.schema.json`
- [ ] Accepts from ACTIVE or ARCHIVED; rejects with `409
      ANCHOR_ALREADY_PSEUDONYMISED` from PSEUDONYMISED
- [ ] `404 ANCHOR_NOT_FOUND` for unknown `internal_id`
- [ ] `400 RIGHT_EXERCISE_ID_INVALID` when `right_exercise_id` is
      missing or not a UUIDv7
- [ ] Crypto-shredding observable post-condition: a direct SQL
      inspection of the anchor's row (separate from the running
      service) shows the four PII columns as NULL or as
      cryptographically-unrecoverable ciphertext — verifiable by a
      DBA-style audit query in the test suite
- [ ] `internal_id` is unchanged before / after (`INV.BEN.002`) —
      verified by SQL inspection
- [ ] `anchor_status = PSEUDONYMISED`, `pseudonymized_at` set to a
      timestamp within the request window
- [ ] Operation is irreversible: no API endpoint exists to undo
      pseudonymisation
- [ ] Idempotency on `command_id`: a duplicate `command_id` returns
      `200 OK` with the prior PSEUDONYMISED snapshot and
      `COMMAND_ALREADY_PROCESSED` WITHOUT re-running crypto-shredding
      (verifiable: Vault transit / `pgcrypto` calls happen exactly
      once across the duplicate calls)
- [ ] Outbox emits exactly one RVT per successful pseudonymisation;
      payload's PII fields are null; `right_exercise_id` is set;
      `pseudonymized_at` is set; `transition_kind: PSEUDONYMISED`;
      `revision = N+1`
- [ ] Emitted payload validates against
      `schemas/RVT.SUP.002.BENEFICIARY_ANCHOR_UPDATED.schema.json`,
      including the conditional `if/then` block (PSEUDONYMISED ⇒ PII
      null + `right_exercise_id` set)
- [ ] `PRJ.ANCHOR_DIRECTORY` ingests the event and overwrites the row
      — PII columns become NULL in the projection too (consumers
      should not see stale PII anywhere)
- [ ] `GET /anchors/{internal_id}` returns the row with PII fields as
      null and `anchor_status: PSEUDONYMISED`; `internal_id` is still
      resolvable so historical references work; ETag flips immediately
- [ ] UPDATE / ARCHIVE / RESTORE issued against the now-pseudonymised
      anchor return `409` with the right code (regression tests against
      TASK-003 / TASK-004 paths)
- [ ] Crypto-shredding key strategy (per-anchor / per-zone / per-IS) is
      chosen by the implementer per `ADR-TECH-TACT-002` and documented
      inline in the service README — surface the decision as a
      TECH-TACT delta to OQ.BEN.002 (key strategy) referenced in the
      roadmap OQ-2
- [ ] No write to `process/CAP.SUP.002.BEN/`
- [ ] `pytest` integration suite covers: ACTIVE→PSEUDONYMISED happy
      path, ARCHIVED→PSEUDONYMISED happy path, terminality
      (PSEUDONYMISED→{UPDATE,ARCHIVE,RESTORE,PSEUDONYMISE} all reject),
      idempotency (no double crypto-shred), DB-level PII destruction
      audit, RVT schema conditional validation
- [ ] DPO + IT Security sign-off captured in the PR description for
      the PII-touching DoD items (joint-custody governance)

## Acceptance Criteria (Business)
When the DPO (or `CAP.SUP.001.RET` on its behalf) issues a
`PSEUDONYMISE_ANCHOR` for a beneficiary, the four PII fields are
destroyed at the anchor — and a database-level inspection confirms they
are not recoverable. Every downstream consumer that subscribes to
`sup.002.ben-events` receives the `PSEUDONYMISED` event with null PII
fields and wipes its local cached PII for that `internal_id`. The
`internal_id` itself survives, so historical references and audit
lineage do not break. The right-to-be-forgotten obligation is provably
honoured across the IS via the bus.

## Dependencies
- TASK-002 (mandatory — foundation)
- TASK-003 (recommended — UPDATE state machine, used for cross-verb
  regression tests)
- TASK-004 (recommended — ARCHIVE state machine; PSEUDONYMISE can be
  applied to an ARCHIVED anchor and tests need this transition)
- HashiCorp Vault transit engine provisioned in the dev environment
- PostgreSQL `pgcrypto` extension installed in the dev environment

## Open Questions
None blocking launch. The crypto-shredding key strategy (per-anchor vs
per-zone vs per-IS — roadmap OQ-2) is intentionally deferred to the
implementer per `ADR-TECH-TACT-002`. The model constrains only the
observable post-condition (PII not recoverable). The chosen strategy must
be documented in the service README and surfaced as a TECH-TACT delta in
the PR before merge — not before launch.
