# Process Model — CAP.REF.001.BEN (Beneficiary Referential)

> **Layer**: Process Modelling (DDD tactical) — sits between Big-Picture Event
> Storming (banking-knowledge: BCM, FUNC ADR) and Software Design (this repo's
> `sources/`).
> **Source of truth for**: commands accepted, aggregate boundaries, reactive
> policies, read-model surface, bus topology, wire schemas of this capability.
> **NOT a plan**: this folder is durable across re-plans and re-implementations
> of the same FUNC ADR. The `plan/CAP.REF.001.BEN/` folder consumes it.

This capability is the **canonical golden record** for beneficiary identity in
the Reliever programme. Per `ADR-BCM-FUNC-0013`, no other capability may
maintain its own private copy of these PII fields — every consumer either
subscribes to `RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED` to hydrate a local
cache (per `ADR-TECH-STRAT-004`'s dual-referential-access rule) or calls
`QRY.GET_BENEFICIARY` synchronously.

## Upstream knowledge (consumed, not re-stated)

Fetched via `bcm-pack pack CAP.REF.001.BEN --deep`. Anything in those slices
is canonical and must NOT be duplicated here:

- `capabilities-reliever-L2.yaml` — capability definition, parent
  (CAP.REF.001), zone (REFERENTIAL), owner (Data & Referentials Team)
- `func-adr/ADR-BCM-FUNC-0013` — L2 breakdown of CAP.REF.001 — Common
  Referentials (BENEFICIARY, PRESCRIBER, TIER)
- `business-event-reliever.yaml` — `EVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED`
- `resource-event-reliever.yaml` —
  `RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED` (single emitted event family)
- `business-object-reliever.yaml` — `OBJ.REF.001.BENEFICIARY_RECORD`
  (internal_id, last_name, first_name, date_of_birth, contact_details,
  referential_status, creation_date)
- `resource-reliever.yaml` — `RES.REF.001.BENEFICIARY_IDENTITY`
- `concept-reliever.yaml` — `CPT.BCM.000.BENEFICIARY` (canonical, core-domain)
- `tech-vision/adr/ADR-TECH-STRAT-001` — bus topology rules (Rules 1, 2, 3, 4, 5)
- `tech-vision/adr/ADR-TECH-STRAT-004` — Data and Referential Layer (PII
  governance, dual-referential-access, GDPR right-to-be-forgotten guidance)

The BCM corpus declares **zero** consumed events for this capability —
intentional, and consistent with the source-of-truth pattern.

## What this folder declares (Process Modelling output)

| File | Captures |
|---|---|
| `commands.yaml` | CMD.* — four verbs (`REGISTER_BENEFICIARY`, `UPDATE_BENEFICIARY_IDENTITY`, `ARCHIVE_BENEFICIARY`, `RESTORE_BENEFICIARY`), preconditions, idempotency strategy, the aggregate that handles each |
| `aggregates.yaml` | AGG.REF.001.BEN.BENEFICIARY_IDENTITY — single per-beneficiary aggregate keyed on a server-generated `internal_id`; sticky-PII rule on UPDATE; full-snapshot semantics on every emitted event |
| `policies.yaml` | **Empty** — no upstream subscriptions in BCM. Source-of-truth pattern, driven exclusively by HTTP API calls. |
| `read-models.yaml` | PRJ.* — beneficiary directory + lifecycle history; QRY.* — three queries (by internal_id, by external_id, history) |
| `api.yaml` | Derived REST surface (commands → POST/PATCH, queries → GET) |
| `bus.yaml` | Exchange `ref.001.ben-events`, single routing key (`EVT.<...>.RVT.<...>` form per ADR-TECH-STRAT-001 Rule 4), no subscriptions, broad consumer list (every L2 needing identity) |
| `schemas/` | JSON Schemas Draft 2020-12 — four `CMD.*` (command payloads) and one `RVT.*` (resource-event payload, full-snapshot semantics with `transition_kind` discriminator) |

## Scenario walkthroughs

The capability has no event-driven flows — every transition is initiated by
an HTTP API caller. Two flows below illustrate how downstream consumers
interact with the capability via both the synchronous (QRY) and asynchronous
(RVT) access paths.

### Flow A — Registration (driven by upstream candidacy/eligibility)

```
[Upstream eligibility/candidacy capability — TBD; CAP.BSP.002.* is a candidate]
                              │
                              ▼ HTTP POST /beneficiaries
                              { external_id: "CAND-2026-04-12-0042",
                                last_name, first_name, date_of_birth,
                                contact_details }
                              │
                              ▼ accepted by
        AGG.REF.001.BEN.BENEFICIARY_IDENTITY (created — INV.BEN.001/002)
                              │
                              │ generates internal_id (server-side ULID)
                              │ revision = 1, transition_kind = REGISTERED
                              ▼ emits
        RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED
            { internal_id, external_id, revision=1,
              transition_kind=REGISTERED, ...full snapshot... }
                              │
                              ▼ replicated to consumers' local caches
        CAP.BSP.001.SCO   ─┐
        CAP.BSP.002.ENR   ─┤
        CAP.BSP.004.ENV   ─┼─▶ each updates its own internal_id-keyed cache
        CAP.CHN.001.DSH   ─┤    via last-write-wins on (internal_id, revision)
        CAP.B2B.001.FLW   ─┘
                              │
                              ▼ caller's HTTP response
                              201 Created { internal_id, ... }
```

### Flow B — Identity update + cache reconciliation

```
[Channel admin tool / ops]
                              │
                              ▼ HTTP PATCH /beneficiaries/{internal_id}
                              { command_id, contact_details: { email: "..." } }
                              │
                              ▼ accepted by
        AGG.REF.001.BEN.BENEFICIARY_IDENTITY
                              │
                              │ INV.BEN.003 — only contact_details mutates
                              │ revision = N+1, transition_kind = UPDATED
                              ▼ emits
        RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED
            { revision=N+1, transition_kind=UPDATED,
              changed_fields=["contact_details.email"], ...full snapshot... }
                              │
                              ▼
        Downstream consumer (e.g. CAP.CHN.001.DSH) receives the RVT,
        observes revision N+1 > local N, replaces its local snapshot.
                              │
                              ▼ caller's HTTP response
                              200 OK { ...post-transition record... }
```

### Flow C — Archival on programme exit

```
[Programme administration / future automated exit signal]
                              │
                              ▼ HTTP POST /beneficiaries/{internal_id}/archive
                              { command_id,
                                reason: "PROGRAMME_EXIT_SUCCESS",
                                comment: "Final tier reached, transferred to standard banking" }
                              │
                              ▼ accepted by
        AGG.REF.001.BEN.BENEFICIARY_IDENTITY (INV.BEN.004)
                              │
                              │ status: ACTIVE → ARCHIVED
                              │ revision = N+1, transition_kind = ARCHIVED
                              ▼ emits
        RVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED
            { revision=N+1, transition_kind=ARCHIVED,
              referential_status=ARCHIVED, ...full snapshot... }
                              │
                              ▼ downstream consumers note the archived state
                              and may pause local-cache eviction (records
                              remain queryable for historical resolution).
```

## Open process-level questions (must be resolved before `/code`)

These questions are repeated from the YAMLs (`open_question` fields) so
reviewers can see the structural gaps in one place.

1. **GDPR right-to-be-forgotten — physical PURGE not modelled.**
   `ADR-TECH-STRAT-004` mandates PII purge on regulatory request. The BCM
   corpus today declares only `EVT.REF.001.BENEFICIARY_REFERENTIAL_UPDATED`
   (a single event family). A PURGE that wipes PII fields cannot use the
   same RVT — consumers would not be able to distinguish a PURGE from an
   ordinary UPDATE without inspecting the payload, which leaks contract
   semantics into payload introspection. The clean path is to:
   1. Author a new business+resource event in the BCM
      (`EVT.REF.001.BENEFICIARY_PURGED` / `RVT.REF.001.BENEFICIARY_PURGED`).
   2. Add `CMD.PURGE_BENEFICIARY` here in a follow-up `/process` run
      (delta session — no rename of existing identifiers).
   3. Have downstream caches handle the PURGE event by wiping their local
      copy of the PII fields while keeping the internal_id reference if
      needed for historical event linkage.
   The capability's `referential_status` enum reserves the `PURGED` value
   for that future revision.

2. **Upstream caller of `REGISTER_BENEFICIARY` — not yet identified.**
   Today no L2 capability is process-modelled to play the role of the
   eligibility / candidacy stage that mints the `external_id` and registers
   the beneficiary. CAP.BSP.002 (Beneficiary Onboarding) is a candidate;
   this should be confirmed when CAP.BSP.002's process model is authored,
   so that the `external_id` semantics align between producer and consumer.

3. **Homonym disambiguation — out of scope here.** Two beneficiaries can
   share the same (last_name, first_name, date_of_birth). The capability
   does NOT enforce uniqueness on the natural-key tuple — only on
   `external_id`. Disambiguation (manual review, additional ID factors) is
   the upstream candidacy capability's concern. INV.BEN.001 documents this.

4. **Referential consumer list — best-effort only.** The `bus.yaml`
   `consumers` block lists capabilities with `evidenced_by:
   prior-process-model` (CAP.BSP.001.SCO, CAP.BSP.004.ENV — both name
   `CAP.REF.001.BEN` as their identity resolver) and `evidenced_by:
   anticipated` (everyone else). The exhaustive list is whoever needs the
   beneficiary identity, which is most of the programme. The downstream
   BCM business-subscription chain is the canonical source; this folder
   should be re-checked when the cross-capability subscription map is
   complete.

## Governance

| ADR | Role |
|---|---|
| `ADR-BCM-FUNC-0013` | L2 breakdown of CAP.REF.001 (Common Referentials) — defines the golden-record rule and the single emitted event family |
| `ADR-BCM-URBA-0009` | Event meta-model and capability event ownership |
| `ADR-BCM-URBA-0012` | Canonical business concepts (CPT.BCM.000.BENEFICIARY) |
| `ADR-TECH-STRAT-001` | Bus rules (exchange-per-L2, routing-key convention `EVT.<...>.RVT.<...>`, design-time schema governance, dual-rail operational vs analytical) — NORMATIVE for `bus.yaml` |
| `ADR-TECH-STRAT-004` | Data and Referential Layer — PII governance, dual-referential-access (bus + QRY), retention/right-to-be-forgotten guidance |
