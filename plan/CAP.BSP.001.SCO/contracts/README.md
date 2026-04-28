# Contracts — CAP.BSP.001.SCO (Behavioural Score)

This folder holds the JSON Schemas (Draft 2020-12) that describe the events emitted by `CAP.BSP.001.SCO`.

> **Source of truth:** the BCM YAML files in `/bcm/` remain authoritative (cf. `ADR-TECH-STRAT-001` Rule 6 — *La gouvernance de schéma est design-time*). The schemas in this folder are **derived design-time artefacts** for runtime validation (RVT) and consumer documentation (EVT).

## Index

| File | Role | Event ID | Carried | Runtime bus message? |
|---|---|---|---|---|
| `RVT.BSP.001.SCORE_COURANT_RECALCULE.schema.json` | **Runtime contract** — every payload published on the bus MUST validate against this | `RVT.BSP.001.SCORE_COURANT_RECALCULE` | `RES.BSP.001.SCORE_COURANT` (resource read model) — projection of `OBJ.BSP.001.EVALUATION` | **Yes** — published on the operational RabbitMQ rail (ADR-TECH-STRAT-001 Rule 2). |
| `EVT.BSP.001.SCORE_RECALCULE.schema.json` | **Design-time documentation only** — describes the abstract business fact at the meta-model level | `EVT.BSP.001.SCORE_RECALCULE` | `OBJ.BSP.001.EVALUATION` (abstract business object) | **No** — per ADR-TECH-STRAT-001 Rule 2, business events do NOT generate autonomous bus messages. The business event name appears exclusively as the prefix of the routing key (Rule 4). |

## BCM source of truth

| BCM file | What it grounds |
|---|---|
| `bcm/business-event-reliever.yaml` (`EVT.BSP.001.SCORE_RECALCULE`) | The abstract business fact, version (`1.0.0`), `carried_business_object: OBJ.BSP.001.EVALUATION`. |
| `bcm/resource-event-reliever.yaml` (`RVT.BSP.001.SCORE_COURANT_RECALCULE`) | The wire-level event published on RabbitMQ, `carried_resource: RES.BSP.001.SCORE_COURANT`, `business_event: EVT.BSP.001.SCORE_RECALCULE`. |
| `bcm/business-object-reliever.yaml` (`OBJ.BSP.001.EVALUATION`) | The data fields mirrored by the `EVT.*` documentation schema. |
| `bcm/resource-reliever.yaml` (`RES.BSP.001.SCORE_COURANT`) | The data fields mirrored by the `RVT.*` runtime schema, including the domain-event-DDD-only fields `evenement_declencheur` and `delta_score`. |

## Routing & bus topology

Per `ADR-TECH-STRAT-001` (*Dual-Rail Event Infrastructure*):

| Property | Value | ADR rule |
|---|---|---|
| Broker (operational rail) | RabbitMQ | Rule 1 |
| Exchange type | `topic` | Rule 1 |
| Exchange name | `bsp.001.sco-events` (owned by `CAP.BSP.001.SCO`; only this L2 publishes here) | Rules 1, 5 |
| Routing key | `EVT.BSP.001.SCORE_RECALCULE.RVT.BSP.001.SCORE_COURANT_RECALCULE` | Rule 4 — `{BusinessEventName}.{ResourceEventName}` |
| Wire-level message | `RVT.BSP.001.SCORE_COURANT_RECALCULE` only | Rule 2 — only resource events generate autonomous messages |
| Payload form | Domain event DDD — coherent and atomic transition data; not a snapshot, not a field patch | Rule 3 |
| Schema governance | Design-time; BCM YAML authoritative; no runtime registry | Rule 6 |

Consumers may bind their queue with:
- `EVT.BSP.001.SCORE_RECALCULE.#` to aggregate every resource event linked to the score recomputation business fact, or
- `EVT.BSP.001.SCORE_RECALCULE.RVT.BSP.001.SCORE_COURANT_RECALCULE` for the precise resource event.

## Versioning encoding

Each schema declares the BCM event version twice — by URL and by annotation — to give an explicit deprecation surface and inspectable provenance:

- `$id` URL with version segment, e.g. `https://reliever.example.com/contracts/CAP.BSP.001.SCO/RVT.BSP.001.SCORE_COURANT_RECALCULE/1.0.0/schema.json`. A new BCM version produces a new path = explicit deprecation surface.
- Top-level `"x-bcm-version": "1.0.0"` aligned with the BCM event version, so traceability does not require URL parsing.

## Correlation key — `identifiant_dossier`

Each schema declares **`identifiant_dossier`** (Reliever case ID) as the correlation key (required field). Beneficiary identity resolution toward `OBJ.REF.001.BENEFICIAIRE.identifiant_interne` is the **consumer's** responsibility, performed via a lookup against `CAP.REF.001.BEN` (Beneficiary Reference). The producer (`CAP.BSP.001.SCO`) **never carries** the canonical identifiant_interne — it only references the case via `identifiant_dossier`. This is the canonical resolution path:

```
RVT.BSP.001.SCORE_COURANT_RECALCULE.identifiant_dossier
  ──(CAP.REF.001.BEN lookup)──▶ OBJ.REF.001.BENEFICIAIRE.identifiant_interne
```

## Known consumers (today)

Read from `bcm/business-subscription-reliever.yaml` and `bcm/resource-subscription-reliever.yaml`:

| Consumer | Subscription type | Rationale |
|---|---|---|
| `CAP.BSP.001.ARB` (Algorithmic / prescriber arbitration) | Business + resource | Each score recomputation during an active prescriber override allows ARB to assess whether the conditions for algorithmic resumption are met. ARB compares the algorithmic value to the active prescriber tier. |
| `CAP.CAN.001.TAB` (Beneficiary dashboard — channel) | Business + resource | The recomputed score updates the gamified progress bar of the beneficiary dashboard — the score is the central gamification data point. |
| `CAP.CAN.002.VUE` (Prescriber view — channel) | Resource | Displays the score value and its history in the prescriber view with the updated progression level of the case. |

Future consumers (per `func-adr/ADR-BCM-FUNC-0005`): `CAP.CAN.001.NOT` (notifications), behavioural feedback loops.

## Runtime stub

A development stub honoring this contract lives under [`/sources/CAP.BSP.001.SCO/stub/`](../../../sources/CAP.BSP.001.SCO/stub/). It publishes the runtime resource event on the bus topology described above, at a configurable cadence (1–10 events / minute by default; outside-range cadence requires an explicit override), with simulated case IDs. Every payload is validated against `RVT.BSP.001.SCORE_COURANT_RECALCULE.schema.json` before publication.

## Governance

| ADR | Role |
|---|---|
| `func-adr/ADR-BCM-FUNC-0005-L2-BSP001-remédiation-comportementale.md` | Functional decisions for `CAP.BSP.001` (remédiation comportementale) |
| `adr/ADR-BCM-URBA-0007-meta-modele-evenementiel-normalise.md` | Event meta-model — distinction business event / resource event |
| `adr/ADR-BCM-URBA-0008-modelisation-evenements.md` | Event modelling rules |
| `adr/ADR-BCM-URBA-0009-definition-capacite-evenementielle.md` | Capability owns its emitted events |
| `tech-vision/adr/ADR-TECH-STRAT-001-event-infrastructure.md` | **NORMATIVE** — bus topology, payload form, routing convention, schema governance (Rules 1–6) |
