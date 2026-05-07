# Process Model — CAP.BSP.001.SCO (Behavioural Scoring)

> **Layer**: Process Modelling (DDD tactical) — sits between Big-Picture Event Storming
> (banking-knowledge: BCM, FUNC ADR) and Software Design (this repo's `sources/`).
> **Source of truth for**: commands accepted, aggregate boundaries, reactive policies,
> read-model surface, bus topology, wire schemas of this capability.
> **NOT a plan**: this folder is durable across re-plans and re-implementations of the
> same FUNC ADR. The `plan/CAP.BSP.001.SCO/` folder consumes it.

## Upstream knowledge (consumed, not re-stated)

Fetched via `bcm-pack pack CAP.BSP.001.SCO`. Anything in those slices is canonical
and must NOT be duplicated here:

- `capabilities-reliever-L2.yaml` — capability definition, parent, zone, owner
- `func-adr/ADR-BCM-FUNC-0005` — L2 breakdown of CAP.BSP.001
- `business-event-reliever.yaml` — `EVT.BSP.001.SCORE_RECOMPUTED`, `EVT.BSP.001.SCORE_THRESHOLD_REACHED`
- `resource-event-reliever.yaml` — `RVT.BSP.001.ENTRY_SCORE_COMPUTED`, `RVT.BSP.001.CURRENT_SCORE_RECOMPUTED`, `RVT.BSP.001.SCORE_THRESHOLD_REACHED`
- `business-object-reliever.yaml` — `OBJ.BSP.001.EVALUATION`
- `resource-reliever.yaml` — `RES.BSP.001.ENTRY_SCORE`, `RES.BSP.001.CURRENT_SCORE`
- `business-subscription-reliever.yaml` — four upstream subscriptions (TXN_AUTHORIZED, TXN_REFUSED, RELAPSE, PROGRESSION)
- `tech-vision/adr/ADR-TECH-STRAT-001` — bus topology rules

## What this folder declares (Process Modelling output)

| File | Captures |
|---|---|
| `commands.yaml` | CMD.* — verbs the capability accepts, their preconditions, the aggregate that handles each, the events each emits |
| `aggregates.yaml` | AGG.* — consistency boundaries; invariants; accepted commands; emitted events |
| `policies.yaml` | POL.* — reactive rules (consumed event → command); sagas |
| `read-models.yaml` | QRY.* — projections served + the queries built on top |
| `api.yaml` | Derived REST surface (commands → POST, queries → GET) |
| `bus.yaml` | Exchange, routing keys, consumers (machine-readable replacement for what was prose in `plan/.../contracts/README.md`) |
| `schemas/` | JSON Schemas for events (RVT/EVT — already exist, would migrate from `plan/CAP.BSP.001.SCO/contracts/`) and commands (CMD — net new) |

## Scenario walkthrough

Two flows — **enrolment baseline** and **continuous recomputation** — drive every
behaviour of this capability.

### Flow A — Beneficiary enrolment baseline

```
[CAP.BSP.002.ENR — to confirm with FUNC-0006]
        emits EVT.BSP.002.ENROLMENT_COMPLETED
                │
                ▼
   POL.BSP.001.SCO.ON_ENROLMENT_COMPLETED
                │
                ▼ issues
   CMD.BSP.001.SCO.COMPUTE_ENTRY_SCORE { case_id, baseline_signals }
                │
                ▼ handled by
   AGG.BSP.001.SCO.SCORE_OF_BENEFICIARY (created)
                │
                ▼ emits
   RVT.BSP.001.ENTRY_SCORE_COMPUTED   (paired EVT.BSP.001.SCORE_RECOMPUTED)
```

### Flow B — Continuous recomputation

```
[CAP.BSP.004.AUT]               [CAP.BSP.001.SIG]
   TXN_AUTHORIZED                  RELAPSE_SIGNAL_QUALIFIED
   TXN_REFUSED                     PROGRESSION_SIGNAL_QUALIFIED
                                │
                                ▼
            POL.BSP.001.SCO.ON_BEHAVIOURAL_TRIGGER
                                │
                                ▼ issues
            CMD.BSP.001.SCO.RECOMPUTE_SCORE
                                │
                                ▼ handled by
            AGG.BSP.001.SCO.SCORE_OF_BENEFICIARY
                                │
                                ▼ emits (always)
            RVT.BSP.001.CURRENT_SCORE_RECOMPUTED
                                │
                                ▼ also emits (conditional — threshold crossed)
            RVT.BSP.001.SCORE_THRESHOLD_REACHED
                                │
                                ▼ consumed by
            CAP.BSP.001.TIE  (tier transition evaluation)
```

## Open process-level questions (must be resolved before `/code`)

- **Trigger of entry score** — FUNC-0005 lists no business subscription for enrolment
  in CAP.BSP.001.SCO's consumed events. Which event activates `COMPUTE_ENTRY_SCORE`?
  Most likely a future `EVT.BSP.002.ENROLMENT_COMPLETED` from CAP.BSP.002.ENR. Until
  resolved, `POL.BSP.001.SCO.ON_ENROLMENT_COMPLETED` is a placeholder.
- **Threshold detection** — is "threshold reached" computed inside the score aggregate
  during the same transaction as the recomputation, or by a separate observer reacting
  to `RVT.BSP.001.CURRENT_SCORE_RECOMPUTED`? The ADR is silent. This sketch picks the
  former (atomic; one transition emits 1 or 2 resource events) — see `aggregates.yaml`.
- **Aggregate granularity** — one aggregate per `case_id` (chosen here) vs. one per
  `(case_id, model_version)`. This sketch picks the former; revisit if model versioning
  becomes a first-class invariant.

## Governance

| ADR | Role |
|---|---|
| `ADR-BCM-FUNC-0005` | L2 breakdown of CAP.BSP.001 — defines emitted/consumed events |
| `ADR-BCM-URBA-0007/8/9` | Event meta-model + capability event ownership |
| `ADR-TECH-STRAT-001` | Bus rules (exchange-per-L2, routing-key convention, design-time schema governance) |
