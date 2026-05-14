---
task_id: TASK-005
capability_id: CAP.REF.001.BEN
capability_name: Beneficiary Referential
epic: Epic 4 — Audit trail and secondary lookups
status: todo
priority: medium
depends_on: [TASK-002]
task_type: full-microservice
loop_count: 0
max_loops: 10
---

# TASK-005 — Audit history projection and secondary lookups

## Context
The canonical referential needs two complementary read paths beyond
"resolve by `internal_id`":

1. The upstream candidacy/eligibility capability mints the `external_id`
   and calls REGISTER. It does NOT receive the response synchronously in
   all integrations — sometimes it observes the bus, sometimes it later
   needs to look up the canonical `internal_id` it minted, by
   `external_id`. The `GET /beneficiaries/by-external-id/{external_id}`
   endpoint serves this case.

2. Audit, governance, and ops investigations need a chronological view of
   every state transition a beneficiary went through: when did the
   identity change, who archived the record, when, with what comment? The
   `BENEFICIARY_HISTORY` projection retains this audit trail over a
   **7-year** window per `ADR-TECH-STRAT-004`, and the
   `GET /beneficiaries/{internal_id}/history` endpoint exposes it.

This task adds the history projection and the two new query endpoints.
It is read-only — no new aggregates, no new commands, no new RVTs. It
benefits from TASK-003 and TASK-004 having shipped so the history stream
contains real UPDATE/ARCHIVE/RESTORE transitions to test against, but it
does NOT hard-depend on them.

## Capability Reference
- Capability: Beneficiary Referential (CAP.REF.001.BEN)
- Zone: REFERENTIAL
- Governing FUNC ADR: `ADR-BCM-FUNC-0013`
- Strategic-tech anchors:
  - `ADR-TECH-STRAT-004` (PII governance + 7-year retention guidance for
    master-data of vulnerable populations — the **load-bearing ADR** for
    this task's retention horizon)
  - `ADR-TECH-STRAT-003` (REST API surface)
  - `ADR-TECH-STRAT-005` (Observability — same auth/observability posture
    as TASK-002 reads)

## What to Build

### History projection
`PRJ.REF.001.BEN.BENEFICIARY_HISTORY` — fed by the same
`RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED` stream as the directory
projection (TASK-002), but with append-only semantics. Each RVT becomes
one row; rows are never updated nor deleted within the retention window.

Row fields:
- `internal_id` (foreign key into the directory)
- `revision` (monotonic per `internal_id`)
- `transition_kind` (REGISTERED | UPDATED | ARCHIVED | RESTORED)
- `changed_fields` (list — empty for REGISTERED, single-element
  `["referential_status"]` for ARCHIVED / RESTORED, varies for UPDATED)
- `referential_status_after` (the value after the transition)
- `occurred_at` (timestamp from the RVT)
- `command_id` (the originating command — `null` for the REGISTER row if
  REGISTER's idempotency anchor is `external_id` rather than `command_id`;
  the implementation may also choose to record the REGISTER request's
  correlation id — document the choice)
- Optionally `reason` (ARCHIVE) / `comment` (RESTORE) if the
  implementation chose to surface them at the projection level (see
  TASK-004 open question — default is *not* to surface, the history is
  audited via the RVT payload itself).

Indexes:
- `(internal_id, revision)` ascending — primary lookup.
- `(internal_id, occurred_at)` — chronological scans with `since` filter.

Retention:
- **7 years** from `occurred_at` per `ADR-TECH-STRAT-004`. Implementation
  is free to enforce retention via partitioned storage, TTL, or scheduled
  purge — document the chosen mechanism. The 7-year horizon MUST be
  configurable at deployment time (different environments may opt for
  shorter dev/staging windows).

Consistency:
- Eventual, like the directory projection. Same RVT consumer / outbox
  reader pipeline; the history projection is simply a second sink.

### Secondary lookup: GET by external_id
`QRY.REF.001.BEN.GET_BENEFICIARY_BY_EXTERNAL_ID` — bound to
`GET /beneficiaries/by-external-id/{external_id}`.

- Served by the `PRJ.BENEFICIARY_DIRECTORY` projection (no separate
  external_id-keyed projection; a secondary index on the existing
  projection is sufficient).
- Response body shape: same as `GET /beneficiaries/{internal_id}` plus
  the fields named in `read-models.yaml` for this query (`internal_id`,
  `external_id`, `last_name`, `first_name`, `date_of_birth`,
  `contact_details`, `referential_status`, `creation_date`, `revision`).
- HTTP caching: `ETag` (derived from `revision`) +
  `Cache-Control: max-age=30s` — same posture as the primary GET.
- Unknown `external_id` returns 404.
- Same auth posture as the primary GET (bearer token sourced from
  `CAP.SUP.001`).

### History endpoint
`QRY.REF.001.BEN.LIST_BENEFICIARY_HISTORY` — bound to
`GET /beneficiaries/{internal_id}/history`.

- Served by `PRJ.BENEFICIARY_HISTORY`.
- Returns a chronologically ordered (ascending by `(revision)`, which
  equals ascending by `occurred_at` modulo monotonic-revision invariant)
  array of transition records.
- Query parameters:
  - `since` (optional, ISO-8601 date-time) — return only transitions with
    `occurred_at >= since`. Default = the beginning of retention (no
    filter).
  - `limit` (optional, integer, default 50, hard max 500) — page size.
    Caller may iterate using subsequent `since` calls.
- Response item fields: `revision`, `transition_kind`, `changed_fields`,
  `referential_status_after`, `occurred_at`, `command_id` (and optionally
  `reason` / `comment` per the projection decision).
- Unknown `internal_id` returns 404 (NOT 200 with empty array — the
  beneficiary must exist to query its history).
- Same auth posture as the other GET endpoints.

## Business Events to Produce
None. This is a read-only task — no new RVTs, no new aggregate
transitions.

## Business Objects Involved
- `OBJ.REF.001.BENEFICIARY_RECORD` — read-only consumption of its
  canonical shape.
- Audit-trail records (history projection rows) — internal to this
  capability, not published on the bus.

## Event Subscriptions Required
None (the projection consumes the **local** RVT stream from the outbox,
not an inbound bus subscription — same mechanism as the directory
projection from TASK-002).

## Definition of Done

### History projection
- [ ] A second sink consumes the local RVT stream and appends one row
      per RVT to the `BENEFICIARY_HISTORY` projection.
- [ ] Each row carries `internal_id`, `revision`, `transition_kind`,
      `changed_fields`, `referential_status_after`, `occurred_at`,
      `command_id`.
- [ ] Rows are append-only — no UPDATE / DELETE within retention.
- [ ] Backfill: when this task is deployed on top of existing TASK-002
      data, the projection is built from the historical RVT stream (the
      outbox or event-store replay) so that pre-existing beneficiaries
      have at least their REGISTRATION row.
- [ ] Retention horizon (7 years from `occurred_at`) is enforced via a
      documented mechanism (TTL, partitioned table + drop, scheduled
      purge — implementation's call). The horizon is configurable at
      deployment time.
- [ ] After REGISTER → UPDATE → ARCHIVE → RESTORE for one beneficiary,
      the projection contains 4 rows with `revision` values [1, 2, 3, 4]
      and `transition_kind` values [REGISTERED, UPDATED, ARCHIVED,
      RESTORED] in that order.

### Secondary lookup
- [ ] `GET /beneficiaries/by-external-id/{external_id}` for a known
      external_id returns **200 OK** with the canonical record body
      (matching the `read-models.yaml` response shape for this query) and
      an `ETag` + `Cache-Control: max-age=30` header.
- [ ] `GET /beneficiaries/by-external-id/{external_id}` for an unknown
      external_id returns **404**.
- [ ] `If-None-Match` with a matching ETag returns **304 Not Modified**.
- [ ] The returned `internal_id` is the same as the one returned by the
      original REGISTER for that `external_id` (round-trip property).
- [ ] After an UPDATE / ARCHIVE / RESTORE on a beneficiary, both
      `GET /beneficiaries/{internal_id}` and
      `GET /beneficiaries/by-external-id/{external_id}` return the same
      post-transition body (the two endpoints share the directory
      projection — they MUST converge).

### History endpoint
- [ ] `GET /beneficiaries/{internal_id}/history` returns **200 OK** with
      the chronological array of transitions.
- [ ] Items are ordered by ascending `revision` (= ascending
      `occurred_at`).
- [ ] `since` query parameter (ISO-8601) filters out transitions older
      than the given timestamp.
- [ ] `limit` query parameter caps the response size; default 50, hard
      max 500.
- [ ] Each item carries `revision`, `transition_kind`, `changed_fields`,
      `referential_status_after`, `occurred_at`, `command_id`.
- [ ] `GET /beneficiaries/{unknown_internal_id}/history` returns **404**
      (not 200-with-empty-array).

### Observability & auth posture
- [ ] Both new endpoints carry the same auth (bearer token from
      `CAP.SUP.001`) as the TASK-002 `GET /beneficiaries/{internal_id}`.
- [ ] Both new endpoints emit the same OpenTelemetry traces / logs /
      metrics as the TASK-002 reads (consistent observability surface per
      `ADR-TECH-STRAT-005`).

### Schema and lineage
- [ ] The response bodies match the field lists declared in
      `process/CAP.REF.001.BEN/read-models.yaml` for
      `QRY.GET_BENEFICIARY_BY_EXTERNAL_ID` and
      `QRY.LIST_BENEFICIARY_HISTORY`.
- [ ] The `since` / `limit` query parameter shape matches `api.yaml`.

## Acceptance Criteria (Business)
1. An ops engineer investigating an integrity incident on beneficiary
   `XYZ` can pull the full transition history from one HTTP call and
   reconstruct the sequence of changes — when the contact was updated,
   when the record was archived, when it was restored, with what
   `command_id` correlating into the upstream caller's logs.
2. The upstream candidacy capability, given an `external_id` it minted,
   can resolve the canonical `internal_id` without having to persist the
   REGISTER response — important when integrations are stateless or
   the response was lost in flight.
3. The audit / compliance officer can verify, at any time during the
   7-year retention window, that a given beneficiary's lifecycle has
   been correctly captured. Beyond the retention horizon, history rows
   are purged in line with the GDPR posture documented in
   `ADR-TECH-STRAT-004`.

## Dependencies
- TASK-002 (the aggregate, the RVT stream, the directory projection, the
  outbox).

Strongly benefits from TASK-003 (UPDATE rows in history) and TASK-004
(ARCHIVE / RESTORE rows in history) being merged before this task ships,
so the integration tests cover the full transition-kind set — but does
not hard-depend on them. If this task ships first, the history will
trivially contain only REGISTERED rows; the test corpus must still cover
the four-row end-to-end scenario, which means either running this task's
tests against a stack that includes TASK-003/004, OR including the
TASK-003/004 paths under the same /code session.

## Open Questions

- [ ] **REGISTER row's `command_id`**: REGISTER's idempotency anchor is
      `external_id` (lifetime window), not `command_id` (30-day window).
      Should the REGISTER row in the history projection carry the
      request's correlation id in the `command_id` field, or leave it
      `null`? Default to *carrying the correlation id* so the audit
      trail is uniform; document the choice.
- [ ] **Retention enforcement mechanism**: TTL (MongoDB TTL index, time-
      based partitions, scheduled batch job)? Pick one and document.
      `ADR-TECH-STRAT-004` mandates the 7-year horizon but does not
      pre-commit the mechanism. If a tactical-tech ADR is authored
      during TASK-002, capture the choice there.
- [ ] **Pre-purge redaction** vs **history retention** (PURGE
      interaction, future): the 7-year retention coexists awkwardly with
      right-to-be-forgotten — when Epic 5 PURGE lands, will it redact
      PII fields in historical rows (preserving the transition skeleton)
      or wipe them entirely? Legal sign-off required before Epic 5;
      blocked here, captured for the future. (Roadmap Open Question +
      Epic 5 entry condition.)
- [ ] **Sorting tie-breaker**: two RVTs with the same `occurred_at`
      timestamp (down to clock resolution) should still appear in
      well-defined order. Monotonic `revision` is the deterministic
      tie-breaker — the projection's primary sort is `(occurred_at,
      revision)` to guarantee this even if a clock skew anomaly causes a
      duplicate timestamp.
