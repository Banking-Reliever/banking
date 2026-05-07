# Process Model — CAP.BSP.004.ENV (Budget Envelope Management)

> **Layer**: Process Modelling (DDD tactical) — sits between Big-Picture Event
> Storming (banking-knowledge: BCM, FUNC ADR) and Software Design (this repo's
> `sources/`).
> **Source of truth for**: commands accepted, aggregate boundaries, reactive
> policies, read-model surface, bus topology, wire schemas of this capability.
> **NOT a plan**: this folder is durable across re-plans and re-implementations
> of the same FUNC ADR. The `plan/CAP.BSP.004.ENV/` folder consumes it.

## Upstream knowledge (consumed, not re-stated)

Fetched via `bcm-pack pack CAP.BSP.004.ENV --deep`. Anything in those slices is
canonical and must NOT be duplicated here:

- `capabilities-reliever-L2.yaml` — capability definition, parent (CAP.BSP.004),
  zone (BUSINESS_SERVICE_PRODUCTION), owner
- `func-adr/ADR-BCM-FUNC-0008` — L2 breakdown of CAP.BSP.004 (Transaction
  Control)
- `business-event-reliever.yaml` — `EVT.BSP.004.ENVELOPE_ALLOCATED`,
  `EVT.BSP.004.ENVELOPE_CONSUMED`, `EVT.BSP.004.ENVELOPE_DEPLETED`,
  `EVT.BSP.004.ENVELOPE_UNCONSUMED`
- `resource-event-reliever.yaml` — `RVT.BSP.004.ENVELOPE_INITIALIZED`,
  `RVT.BSP.004.CONSUMPTION_RECORDED`, `RVT.BSP.004.ENVELOPE_CAP_REACHED`,
  `RVT.BSP.004.ENVELOPE_PERIOD_WITHOUT_CONSUMPTION`
- `business-object-reliever.yaml` — `OBJ.BSP.004.ALLOCATION` (allocation_id,
  case_id, category, cap_amount, consumed_amount, period_start, period_end,
  status)
- `resource-reliever.yaml` — `RES.BSP.004.OPEN_ENVELOPE`,
  `RES.BSP.004.DEPLETED_ENVELOPE`, `RES.BSP.004.UNCONSUMED_ENVELOPE`
- `business-subscription-reliever.yaml` — `SUB.BUSINESS.BSP.004.004`
  (← `EVT.BSP.002.BENEFICIARY_ENROLLED`),
  `SUB.BUSINESS.BSP.004.005` (← `EVT.BSP.001.TIER_UPGRADED`)
- `tech-vision/adr/ADR-TECH-STRAT-001` — bus topology rules (Rules 1, 2, 3, 4, 5)
- product-vision narrative — particularly `ADR-PROD-0006` (the unconsumed
  envelope IS the primary relapse signal)

## What this folder declares (Process Modelling output)

| File | Captures |
|---|---|
| `commands.yaml` | CMD.* — the four verbs (`ALLOCATE_PERIOD_BUDGET`, `RECALIBRATE_PERIOD_BUDGET`, `RECORD_CONSUMPTION`, `CLOSE_PERIOD`), preconditions, the aggregate that handles each, the events each emits |
| `aggregates.yaml` | AGG.BSP.004.ENV.PERIOD_BUDGET — the single per-(case_id, period_index) aggregate; invariants (initial allocation one-shot, atomic cap detection, in-place tier recalibration with cap-clamp, unconsumed threshold at closure) |
| `policies.yaml` | POL.* — four reactive rules (two wired, two placeholder); see open questions |
| `read-models.yaml` | PRJ.* — current period budget view + envelope history; QRY.* — three queries served on top |
| `api.yaml` | Derived REST surface (commands → POST, queries → GET) |
| `bus.yaml` | Exchange `bsp.004.env-events`, four routing keys (`EVT.<...>.RVT.<...>` form per ADR-TECH-STRAT-001 Rule 4), two declared subscriptions, and consumers (some flagged `evidenced_by: func-adr-narrative` until the downstream BCM formalises them) |
| `schemas/` | JSON Schemas Draft 2020-12 — four `CMD.*` (command payloads) and four `RVT.*` (resource-event payloads) |

## Scenario walkthroughs

Four flows drive the entire behaviour of this capability — two driven by
declared upstream BCM subscriptions, two by upstream signals that are
expected but not yet declared in BCM (placeholder policies; see open
questions).

### Flow A — Initial allocation at enrolment (declared upstream)

```
[CAP.BSP.002.ENR]
  emits EVT.BSP.002.BENEFICIARY_ENROLLED.RVT.BSP.002.CASE_OPENED
                              │  (tier_definition carried OR resolved via CAP.REF.001.TIE)
                              ▼
        POL.BSP.004.ENV.ON_BENEFICIARY_ENROLLED
                              │
                              ▼ issues
        CMD.ALLOCATE_PERIOD_BUDGET { case_id, period_index=0, period_start,
                                     period_end, tier_snapshot{categories[]} }
                              │
                              ▼ handled by
        AGG.BSP.004.ENV.PERIOD_BUDGET (created — INV.ENV.001)
                              │
                              ▼ emits N events (one per category in tier)
        RVT.BSP.004.ENVELOPE_INITIALIZED   (paired EVT.BSP.004.ENVELOPE_ALLOCATED)
                              │
                              ▼ consumed by
        CAP.B2B.001.FLW (card funding) + CAP.CHN.001.DSH (dashboard)
```

### Flow B — Tier upgrade mid-period (declared upstream)

```
[CAP.BSP.001.TIE]
  emits EVT.BSP.001.TIER_UPGRADED.RVT.BSP.001.TIER_UPGRADE_RECORDED
                              │
                              ▼
        POL.BSP.004.ENV.ON_TIER_UPGRADED
                              │
                              ▼ issues
        CMD.RECALIBRATE_PERIOD_BUDGET { case_id, period_index, new_tier_snapshot }
                              │
                              ▼ handled by
        AGG.BSP.004.ENV.PERIOD_BUDGET (in-place — INV.ENV.006)
                              │
                              ├─▶ emits RVT.ENVELOPE_INITIALIZED for newly-added categories
                              │
                              └─▶ emits RVT.ENVELOPE_CAP_REACHED for cap-clamp depletion
                                       (when new cap <= consumed_amount)
```

### Flow C — Transaction debit (placeholder upstream)

```
[CAP.BSP.004.AUT]   ⚠ no formal BCM subscription declared (see open questions)
  emits EVT.BSP.004.TRANSACTION_AUTHORIZED.RVT.BSP.004.PAYMENT_GRANTED
                              │
                              ▼  (when wired)
        POL.BSP.004.ENV.ON_TRANSACTION_AUTHORIZED   (status: placeholder)
                              │
                              ▼ issues
        CMD.RECORD_CONSUMPTION { case_id, period_index, category, amount }
                              │
                              ▼ handled by
        AGG.BSP.004.ENV.PERIOD_BUDGET
                              │
                              ▼ emits (always)
        RVT.BSP.004.CONSUMPTION_RECORDED   (paired EVT.BSP.004.ENVELOPE_CONSUMED)
                              │
                              ▼ also emits (conditional — INV.ENV.004 atomic)
        RVT.BSP.004.ENVELOPE_CAP_REACHED   (paired EVT.BSP.004.ENVELOPE_DEPLETED)
                              │
                              ▼ consumed by
        CAP.CHN.001.DSH (dashboard cap-reached notification)
```

### Flow D — Period closure (placeholder upstream)

```
[Future SUP-zone scheduler]   ⚠ no upstream BCM event declared today
  emits TBD timer event (PERIOD_DUE)
                              │
                              ▼  (when wired)
        POL.BSP.004.ENV.ON_PERIOD_END_DUE   (status: placeholder)
                              │
                              ▼ issues
        CMD.CLOSE_PERIOD { case_id, period_index, closing_at,
                           unconsumed_threshold = 0.05 }
                              │
                              ▼ handled by
        AGG.BSP.004.ENV.PERIOD_BUDGET (INV.ENV.005)
                              │
                              ▼ emits one event per envelope with consumed_amount
                                <= cap_amount * unconsumed_threshold
        RVT.BSP.004.ENVELOPE_PERIOD_WITHOUT_CONSUMPTION
                              │   (paired EVT.BSP.004.ENVELOPE_UNCONSUMED)
                              ▼
                              consumed by CAP.BSP.001.SIG (relapse signal qualification)
                              │
                              ▼ — primary relapse signal in the Reliever programme
                              (per product-vision ADR-PROD-0006)
```

## Open process-level questions (must be resolved before `/code`)

These four questions are repeated from the YAMLs (`open_question` fields) so
reviewers can see the structural gaps in one place.

1. **Missing `Transaction.Authorized` business subscription.** ADR-BCM-FUNC-0008
   lists `Transaction.Authorized` among the L2 breakdown's impacted events,
   but `bcm-pack` returns no `SUB.BUSINESS.BSP.004.*` declaring CAP.BSP.004.ENV
   as a consumer of CAP.BSP.004.AUT's `EVT.BSP.004.TRANSACTION_AUTHORIZED`.
   Without that subscription, `consumed_amount` cannot be maintained and
   neither depletion nor unconsumed signals are meaningful. The upstream
   BCM must declare the subscription before `/code` runs.
   **Affects**: `POL.BSP.004.ENV.ON_TRANSACTION_AUTHORIZED` (placeholder),
   `bus.yaml` (subscription absent), Flow C above.

2. **Missing period-end trigger.** No upstream capability emits a "period
   due" signal in BCM today. Three plausible options upstream: (a) a
   dedicated SUP-zone scheduling capability emitting a `PERIOD_DUE`
   resource event per case; (b) a generic timer-service capability with a
   single subscription model; (c) keep an internal scheduler in this
   capability's runtime — but then the process layer cannot model the
   trigger as a true subscription. Resolution requires a strategic
   decision in `banking-knowledge` (likely an URBA ADR on time-based
   triggers).
   **Affects**: `POL.BSP.004.ENV.ON_PERIOD_END_DUE` (placeholder), Flow D
   above.

3. **In-place recalibration vs close-then-reopen on tier upgrade.** The FUNC
   ADR does not specify whether a tier upgrade mid-period should
   recalibrate the existing period in place (chosen here, INV.ENV.006) or
   close the current period and open a new one (which would change
   `period_index` semantics — periods would no longer align with
   regulatory time windows). In-place is the conservative choice: it
   preserves the period's regulatory clock and clamps caps to consumed
   amounts to avoid revoking authorised spending. To be confirmed with the
   product/regulatory stakeholders before `/code`.

4. **Aggregate granularity rejected (one-aggregate-per-envelope).**
   Considered but rejected: keying the aggregate by `allocation_id` (one
   aggregate per envelope). That alternative would simplify per-transaction
   concurrency but would push fan-out (allocation, period closure) to a
   process-manager / saga layer not natively expressed by the policies
   DSL ("issues: exactly one CMD.*"). The chosen per-(case_id,
   period_index) aggregate trades a small per-case contention window for
   a much simpler model. Revisit if envelope-level concurrency becomes a
   measured bottleneck.

## Governance

| ADR | Role |
|---|---|
| `ADR-BCM-FUNC-0008` | L2 breakdown of CAP.BSP.004 (Transaction Control) — defines emitted/consumed events for ENV |
| `ADR-BCM-URBA-0009` | Event meta-model and capability event ownership |
| `ADR-BCM-URBA-0010` | L2-as-pivot urbanisation (CAP.BSP.004.ENV is one such pivot) |
| `ADR-TECH-STRAT-001` | Bus rules (exchange-per-L2, routing-key convention `EVT.<...>.RVT.<...>`, design-time schema governance, dual-rail operational vs analytical) — NORMATIVE for `bus.yaml` |
| `ADR-PROD-0006` | Product framing — the unconsumed envelope is the PRIMARY relapse signal |
