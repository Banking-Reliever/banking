# Plan — Beneficiary Referential (CAP.REF.001.BEN)

## Capability Summary
> Hold and maintain the canonical beneficiary identity — single source of
> truth for every capability that needs to resolve a beneficiary. No other
> capability may keep its own copy of the PII fields owned by this referential
> (golden-record rule, `ADR-BCM-FUNC-0013`).

## Strategic Alignment

- **Service offer**: Active Control Device — Reliever's compliance and
  consent posture relies on a shared, non-duplicated beneficiary record
  (`ADR-PROD-0001`, `ADR-PROD-0005`)
- **Strategic L1**: `CAP.REF.001` — Shared Referentials
- **BCM Zone**: REFERENTIAL
- **Capability level**: L2
- **Owner**: Data & Referentials Team
- **Governing FUNC ADR**: `ADR-BCM-FUNC-0013` (L2 breakdown of CAP.REF.001 —
  Common Referentials; classifies this capability as **generic** in the
  domain map — MDM is a known IS pattern)
- **Strategic-tech anchors**:
  - `ADR-TECH-STRAT-001` (Dual-rail event infrastructure — RabbitMQ
    operational rail, NORMATIVE for the bus topology)
  - `ADR-TECH-STRAT-004` (Data and Referential Layer — dual-referential-
    access, PII governance, GDPR retention guidance — NORMATIVE)
  - `ADR-TECH-STRAT-003` (API contract strategy — REST/HTTP, BFF per channel)
  - `ADR-TECH-STRAT-002` (Modular monolith per TOGAF zone — runtime form)
  - `ADR-TECH-STRAT-005` (Observability & Governance — L2 as primary unit)
- **Tactical-tech ADRs**: none yet (`bcm-pack` warning: no TECH-TACT ADR for
  CAP.REF.001.BEN). Tactical decisions land here as the plan progresses; an
  ADR may be authored during Epic 1 if a load/scale dimension demands it.

## Process Modelling input (read-only, owned by `/process`)

This plan derives its epic boundaries from the process model under
`process/CAP.REF.001.BEN/`:

- **1 aggregate**: `AGG.REF.001.BEN.BENEFICIARY_IDENTITY` (per beneficiary,
  keyed by server-generated `internal_id`)
- **4 commands**: `REGISTER_BENEFICIARY`, `UPDATE_BENEFICIARY_IDENTITY`,
  `ARCHIVE_BENEFICIARY`, `RESTORE_BENEFICIARY`
- **0 policies** (intentional — no upstream subscriptions; the capability is
  purely API-driven, per source-of-truth pattern)
- **2 read-models**: `BENEFICIARY_DIRECTORY` (current state),
  `BENEFICIARY_HISTORY` (audit trail, 7y retention)
- **3 queries**: `GET_BENEFICIARY` (by internal_id),
  `GET_BENEFICIARY_BY_EXTERNAL_ID`, `LIST_BENEFICIARY_HISTORY`
- **1 RVT family**: `RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED` (full-
  snapshot ECST semantics, monotonic `revision`, `transition_kind`
  discriminator)
- **Bus exchange**: `ref.001.ben-events`

## Implementation Epics

### Epic 1 — Golden-record day-zero (REGISTER + GET + RVT publication)
**Goal**: Make the canonical beneficiary record exist and become resolvable
by every downstream consumer of the programme — synchronously via HTTP and
asynchronously via the operational bus.

**Entry condition**:
- Process model `process/CAP.REF.001.BEN/` is committed (DONE)
- Upstream caller of `REGISTER_BENEFICIARY` identified at least at the
  contract level (the actual capability — likely CAP.BSP.002 — does not need
  to ship in parallel; this epic only needs the contract to be agreed)

**Exit condition (Definition of Done)**:
- A downstream capability can call `POST /beneficiaries` (idempotent on
  `external_id`, lifetime window) and receive a 201 Created with the server-
  generated `internal_id`
- A downstream capability can call `GET /beneficiaries/{internal_id}` and
  receive the canonical record with `ETag` + `Cache-Control: max-age=30s`
- A downstream capability can subscribe to `ref.001.ben-events` and receive
  one `RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED` per registration with
  `transition_kind=REGISTERED`, `revision=1`, full-snapshot payload
- Idempotent re-call of `REGISTER_BENEFICIARY` with the same `external_id`
  returns 200 OK with the existing `internal_id` (no duplicate event emitted)
- Conformance to JSON Schemas under `process/.../schemas/CMD.*.REGISTER_*` and
  `RVT.*.BENEFICIARY_REFERENTIAL_UPDATED` (Draft 2020-12, validated at request
  ingress and event publication)
- Aggregate enforces `INV.BEN.001`, `INV.BEN.002`, `INV.BEN.006`, `INV.BEN.007`

**Complexity**: **L** — three vertical slices (HTTP write, HTTP read with
caching, bus publication with full-snapshot semantics) and the foundational
infrastructure (exchange, transactional outbox, projection)

**Unlocks events**: `EVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED` (initial
emission with `transition_kind=REGISTERED`)

**Dependencies**:
- None upstream (foundational capability)
- **CRITICAL PATH**: every other L2 in the Reliever programme that needs
  beneficiary identity (CAP.BSP.001.SCO, CAP.BSP.002.ENR, CAP.BSP.004.ENV,
  CAP.CHN.001.DSH, CAP.CHN.002.VUE, CAP.B2B.001.FLW, etc.) waits on this
  epic before they can resolve `internal_id` or hydrate their local cache

---

### Epic 2 — Identity maintenance (UPDATE)
**Goal**: Allow a beneficiary's mutable identity fields (contact details,
occasionally legal names) to be amended over the lifetime of the programme,
under strict sticky-PII semantics.

**Entry condition**:
- Epic 1 in production (the aggregate exists and emits the canonical RVT)

**Exit condition (Definition of Done)**:
- A caller can `PATCH /beneficiaries/{internal_id}` with a partial payload;
  only the fields present are mutated (sticky-PII per `INV.BEN.003`)
- Idempotent on `command_id` over a 30-day window — re-call returns 200 OK
  with the prior result
- The aggregate emits one
  `RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED` per accepted UPDATE with
  `transition_kind=UPDATED`, `revision=N+1`, `changed_fields=[...]`
- The directory projection updates its row in last-write-wins fashion
- Property-based tests cover the sticky-PII corners: empty payload rejected,
  null fields ignored, partial sub-objects in `contact_details` merge correctly
- 404 on unknown `internal_id`, 409 on archived record, 400 on no-fields-to-update

**Complexity**: **M** — single command, well-bounded; the sticky-PII rule
deserves dedicated test coverage

**Unlocks events**: `RVT.*.UPDATED` variant of the canonical event family
(downstream caches reconcile via `revision`)

**Dependencies**:
- Epic 1 (aggregate exists, RVT family wired)

---

### Epic 3 — Lifecycle states (ARCHIVE + RESTORE)
**Goal**: Allow the canonical record to transition out of the active set
(programme exit, transfer, dropout) and — rarely — back into it (correction
of an archival in error), with an audit trail.

**Entry condition**:
- Epic 1 in production
- Programme operations have a defined need for archival (programme exits
  starting to land — typically driven by CAP.BSP.001.TIE final-tier
  transition or operational tooling)

**Exit condition (Definition of Done)**:
- `POST /beneficiaries/{internal_id}/archive` flips status ACTIVE→ARCHIVED
  and emits `RVT.*.ARCHIVED`
- `POST /beneficiaries/{internal_id}/restore` flips ARCHIVED→ACTIVE and
  emits `RVT.*.RESTORED`; payload requires a non-empty `comment` (audit)
- UPDATE is rejected on archived records with code `BENEFICIARY_ARCHIVED`
  (cross-checked against Epic 2 implementation)
- Both commands enforce `INV.BEN.004` / `INV.BEN.005` (status-flip
  idempotency: re-archive an archived record returns 409
  `BENEFICIARY_ALREADY_ARCHIVED`)
- Idempotent on `command_id` (30d) — same as UPDATE
- Optional `reason` enum on ARCHIVE captured in the audit trail
- The history projection (delivered in Epic 4) records every transition;
  pending Epic 4, the events themselves are the audit source

**Complexity**: **M** — two commands sharing most invariants; the
non-mutating-status-flip pattern is straightforward but the interaction
with UPDATE (sticky-PII + archived guard) needs cross-epic test coverage

**Unlocks events**: `RVT.*.ARCHIVED`, `RVT.*.RESTORED` variants — consumed
by downstream capabilities that need to know when to stop initiating new
transactions for a beneficiary (CAP.BSP.004.ENV stops allocating new
periods, CAP.B2B.001.FLW stops funding the card, etc.)

**Dependencies**:
- Epic 1 (aggregate exists, RVT family wired)
- Concurrent with Epic 2 (no hard ordering)

---

### Epic 4 — Audit trail and secondary lookups
**Goal**: Expose the long-retention history projection and the secondary
lookup access path needed by upstream callers and the audit/governance
function.

**Entry condition**:
- Epic 1 in production
- Audit/compliance owner has signed off on the 7-year retention window for
  the history projection (per `ADR-TECH-STRAT-004`)

**Exit condition (Definition of Done)**:
- `GET /beneficiaries/by-external-id/{external_id}` resolves the canonical
  record by the external candidacy reference (returns the same shape as
  `GET /beneficiaries/{internal_id}`); used by the upstream candidacy
  capability to find the `internal_id` it needs to propagate
- `GET /beneficiaries/{internal_id}/history` returns a chronological list of
  state transitions (revision, transition_kind, changed_fields, occurred_at,
  command_id) with `since`/`limit` query parameters
- The `BENEFICIARY_HISTORY` projection retains 7 years of transitions per
  `ADR-TECH-STRAT-004`
- The two new query endpoints carry the same auth/observability posture as
  Epic 1's `GET /beneficiaries/{internal_id}`

**Complexity**: **M** — two query surfaces and one history projection; the
retention horizon is operationally significant (storage / GDPR alignment)

**Unlocks events**: none (read-only epic)

**Dependencies**:
- Epic 1 (the directory projection and bus stream feed both new accesses)
- Concurrent with Epic 2 / Epic 3 — but Epic 4 benefits from Epics 2/3
  being in production so the history projection has more transition
  varieties to test against

---

### Epic 5 — GDPR right-to-be-forgotten (PURGE) — BLOCKED, future
**Goal**: Honour regulatory right-to-be-forgotten requests by physically
purging PII fields from the canonical record while preserving a tombstone
reference (the `internal_id`) so historical event chains in downstream
capabilities remain linkable without leaking PII.

**Entry condition** — **BLOCKED until upstream BCM action**:
- A new business+resource event family is authored in `banking-knowledge`:
  `EVT.REF.001.BENEFICIARY_PURGED` and `RVT.REF.001.BENEFICIARY_PURGED`
- A delta `/process CAP.REF.001.BEN` run adds `CMD.PURGE_BENEFICIARY` to the
  process model (no rename of existing identifiers; deprecated/replaced_by
  semantics if anything changes)
- Downstream consumers commit to handling the new `RVT.PURGED` event by
  wiping their local cache copies of PII fields

**Exit condition (Definition of Done)**:
- `POST /beneficiaries/{internal_id}/purge` flips status to `PURGED`, nulls
  PII fields (last_name, first_name, date_of_birth, contact_details), keeps
  `internal_id` and `external_id` for traceability
- Emits `RVT.REF.001.BENEFICIARY_PURGED` (distinct event family — consumers
  cannot mistake it for an UPDATE)
- The history projection preserves the audit trail of pre-purge transitions
  but redacts PII in the entries (legal/regulatory consultation required on
  redaction policy)

**Complexity**: **L** — needs a coordinated cross-capability change
(producer and all consumers update simultaneously); is a structural BCM
evolution

**Unlocks events**: `EVT.REF.001.BENEFICIARY_PURGED` (new event family)

**Dependencies**:
- New BCM event in `banking-knowledge`
- Coordinated rollout across every consumer of `RVT.BENEFICIARY_REFERENTIAL_UPDATED`
- Cannot be planned/coded until the BCM is updated and a new `/process` run
  has refreshed the model

---

## Dependency Map

| Epic | Depends On | Type | Notes |
|------|-----------|------|-------|
| Epic 1 | (none) | — | Foundational; on critical path for the entire programme |
| Epic 2 | Epic 1 | Sequential | Aggregate must exist; RVT family must be wired |
| Epic 3 | Epic 1 | Sequential | Same as Epic 2; can run in parallel with Epic 2 |
| Epic 4 | Epic 1 | Sequential | Benefits from Epic 2/3 finishing first (richer audit trail) |
| Epic 5 | BCM evolution + delta `/process` run | External + cross-capability | Cannot start until upstream artefacts land |
| Every downstream L2 (CAP.BSP.001, .002, .004, CHN.*, B2B.*) | Epic 1 | Cross-capability | They cannot resolve `internal_id` until Epic 1 lands |

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Sticky-PII rule misimplemented** — partial UPDATE silently nulls fields not present in the payload, causing PII loss / downstream cache divergence | M | H | Property-based tests on every UPDATE corner (empty payload, partial sub-objects, null vs absent); INV.BEN.003 explicitly tested; review by data-protection officer before Epic 2 ships |
| **PURGE deferral exposes the programme to GDPR risk** at go-live | M | H | Documented as Epic 5 (blocked); operational workaround = manual archival + sealed audit redaction process until Epic 5 lands; legal sign-off required for the gap |
| **Upstream caller of REGISTER not yet process-modelled** (likely CAP.BSP.002) — REGISTER cannot be tested end-to-end until the candidacy capability lands or a stub is agreed | H | M | Define the `external_id` minting convention up-front in Epic 1 (in coordination with whoever owns CAP.BSP.002); ship a contract test harness against the schema rather than against a live caller |
| **Idempotency replay at the 30-day window boundary** — UPDATE / ARCHIVE / RESTORE drop dedup state at T+30d, allowing a stuck retry to re-apply | L | M | Document the window in operator runbooks; ensure transient publishers retry within the window; alert on commands arriving older than 25d (early warning) |
| **Server-generated `internal_id` discipline** — an upstream caller persists the generation timestamp instead of the response `internal_id` and triggers a duplicate REGISTER under retry | L | H | The 201/200-OK pattern + lifetime idempotency on `external_id` makes the "duplicate REGISTER" path safe by design; tested explicitly in Epic 1 acceptance |
| **High fan-out of consumers of the canonical RVT** — every L2 in the programme will eventually subscribe; back-pressure or schema-incompatible changes ripple widely | M | H | ECST full-snapshot semantics with `revision` + `transition_kind` discriminator are forward-compatible (consumers ignore unknown fields); schema versioning at design time per ADR-TECH-STRAT-001 Rule 3; coordinated rollout governance via ADR-TECH-STRAT-005 |

## Recommended Sequencing

**Critical path**: Epic 1 is the single hard blocker for the entire Reliever
programme — every other L2 capability that needs beneficiary identity is
gated on it. Treat Epic 1 as the *first* implementation epic in the whole
programme schedule, before any non-trivial work on BSP/CHN/B2B begins.

**Parallel after Epic 1**: Epics 2, 3, 4 share only the aggregate and RVT
foundation built in Epic 1. After Epic 1 is in production, Epics 2 and 3
can be developed concurrently (no shared state beyond test harnesses); Epic
4 can join the parallel track but benefits from Epic 2/3 having shipped
some transition variety into the history stream.

**Deferred (Epic 5)**: PURGE is parked until the BCM declares the new event
family. Track the unblock criteria (new RVT in `banking-knowledge` + delta
`/process` run) on the programme risk register, not on this plan's critical
path.

## Open Questions

- **Upstream caller of REGISTER**: which capability owns the candidacy /
  eligibility flow that mints the `external_id` and calls REGISTER? Most
  likely CAP.BSP.002 (Beneficiary Onboarding) once its process model is
  authored. Confirm during Epic 1 contract-agreement step. (Surfaced from
  `process/CAP.REF.001.BEN/README.md` open question 2.)
- **PURGE event naming and shape**: when `banking-knowledge` adds the PURGE
  event, the chosen name needs to match the existing pattern
  (`RVT.REF.001.BENEFICIARY_PURGED` is recommended in this plan). Confirm
  during Epic 5 unblock-coordination.
- **History projection retention vs. GDPR redaction**: the 7-year retention
  on `BENEFICIARY_HISTORY` (per `ADR-TECH-STRAT-004`) coexists awkwardly
  with right-to-be-forgotten — does PURGE redact the historical entries, or
  does it only wipe the directory? Legal sign-off required before Epic 4.
- **Tactical-tech ADR**: `bcm-pack` warning — no TECH-TACT ADR for this L2.
  An ADR may be authored during Epic 1 if a load/scale/PII-storage decision
  warrants it (e.g. encryption-at-rest, replicated read-replicas). Track as
  follow-up.
- **Consumer list (anticipated)**: the `process/.../bus.yaml` consumer block
  is best-effort. The exhaustive list emerges from the cross-capability
  business-subscription chain in BCM; revisit once that chain is complete.

## Knowledge Source

- **bcm-pack ref**: `main` (default)
- **Capability pack mode**: `--deep --compact`
- **Pack date**: 2026-05-09
- **Process model**: `process/CAP.REF.001.BEN/` v0.1.0 (authored 2026-05-09;
  read-only input to this plan, owned by `/process`)
- **Pack warnings**: `["No TECH-TACT ADR found with capability_id == CAP.REF.001.BEN."]`
  — captured as Open Question above
