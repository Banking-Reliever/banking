# Event contracts — CAP.BSP.001.TIE (Tier Management)

Owner: **CAP.BSP.001.TIE** (Tier Management) — L3 of `CAP.BSP.001` (Behavioural Remediation), zone `BUSINESS_SERVICE_PRODUCTION`.

This directory holds the **JSON Schema (Draft 2020-12)** contracts for the events emitted by `CAP.BSP.001.TIE`. The schemas are derived design-time artefacts produced from the BCM YAML source of truth — the BCM remains authoritative (ADR-TECH-STRAT-001 Rule 6).

Epic 1 scope: **upward tier crossing only** (`TIER_UPGRADED` / `TIER_UPGRADE_RECORDED`). Downward crossings (`TIER_DOWNGRADED`) and overrides will be contracted in their own epics.

## Schemas

| File | BCM ID | Role | Generates a bus message? | BCM source of truth |
|---|---|---|---|---|
| `RVT.BSP.001.TIER_UPGRADE_RECORDED.schema.json` | `RVT.BSP.001.TIER_UPGRADE_RECORDED` | **Runtime contract** — every payload published on the bus by `CAP.BSP.001.TIE` MUST validate against this schema | **Yes** (only this) | `bcm/resource-event-reliever.yaml`, `bcm/resource-reliever.yaml` (carries `RES.BSP.001.TIER_UPGRADE`) |
| `EVT.BSP.001.TIER_UPGRADED.schema.json` | `EVT.BSP.001.TIER_UPGRADED` | **Design-time documentation only** — describes the abstract business fact at the meta-model level | **No** — per ADR-TECH-STRAT-001 Rule 2 | `bcm/business-event-reliever.yaml`, `bcm/business-object-reliever.yaml` (carries `OBJ.BSP.001.TIER_CHANGE`) |

## Bus topology (per ADR-TECH-STRAT-001)

| Item | Value |
|---|---|
| Broker | RabbitMQ (operational rail) |
| Exchange type | `topic` |
| Exchange name | `bsp.001.pal-events` (owned exclusively by `CAP.BSP.001.TIE` — Rule 1) |
| Routing key | `EVT.BSP.001.TIER_UPGRADED.RVT.BSP.001.TIER_UPGRADE_RECORDED` (Rule 4) |
| Wire-level event | `RVT.BSP.001.TIER_UPGRADE_RECORDED` only — no autonomous `EVT.*` message (Rule 2) |
| Payload form | Domain event DDD — coherent atomic transition data (Rule 3) |

## Versioning encoding

Each schema declares its version in two places, kept consistent:

- `$id` URL with version segment, e.g. `…/RVT.BSP.001.TIER_UPGRADE_RECORDED/1.0.0/schema.json`. A new BCM version becomes a new path = explicit deprecation surface.
- Top-level annotation `"x-bcm-version": "1.0.0"` matching the BCM event version. Inspectable without URL parsing.

## Correlation key

Both schemas declare **`case_id`** as the correlation key.

Resolution path to the canonical beneficiary identifier:

```
case_id  ──(query CAP.REF.001.BEN)──►  OBJ.REF.001.BENEFICIARY_RECORD.internal_id
```

The producer **does NOT** carry `internal_id` on the wire (privacy + decoupling, ADR-BCM-URBA-0009). Consumers wishing to obtain the canonical identifier perform the lookup themselves.

## Known consumers (as of 2026-04-28)

Read from `bcm/business-subscription-reliever.yaml` — these L2/L3 capabilities subscribe to `EVT.BSP.001.TIER_UPGRADED` and will receive `RVT.BSP.001.TIER_UPGRADE_RECORDED` messages on the routing key above:

| Consumer L2/L3 | Why it cares |
|---|---|
| `CAP.B2B.001.CRT` | Card-rule update — a tier upgrade widens authorised categories and limits on the dedicated card. |
| `CAP.BSP.002.EXT` | Programme exit — reaching the final tier triggers the transfer to the standard banking app (`est_sortie_programme=true`). |
| `CAP.BSP.003.NOT` | Prescriber notification — a tier upgrade is a progression event to display in the prescriber portal. |
| `CAP.BSP.004.AUT` | Real-time authorisation rules — a tier upgrade widens the set of authorised categories. |
| `CAP.BSP.004.ENV` | Budget envelope recalibration — a new tier defines new categories and new limits. |
| `CAP.CHN.001.NOT` | Beneficiary congratulations notification — gamification key event. |
| `CAP.CHN.001.DSH` | Beneficiary dashboard — major progression event, displayed in a rewarding way. **First consumer in Epic 1.** |
| `CAP.CHN.002.VUE` | Prescriber portal case state — unlocks new actions when the case state changes. |

## Stub

A development stub publishing simulated payloads on the routing key above lives under `sources/CAP.BSP.001.TIE/stub/`. Every payload it publishes is validated against `RVT.BSP.001.TIER_UPGRADE_RECORDED.schema.json` before being sent — fail-fast on schema violation. The stub is inactive by default (`STUB_ACTIVE=false`); activate it via env var to publish on a configurable cadence in the range **1–10 events/min**.

See `sources/CAP.BSP.001.TIE/stub/README.md` for usage.

## Governance

- Source of truth (per ADR-TECH-STRAT-001 Rule 6): the BCM YAML files (`bcm/business-event-*.yaml`, `bcm/resource-event-*.yaml`, `bcm/business-object-*.yaml`, `bcm/resource-*.yaml`).
- These JSON Schemas are **derived artefacts** — keep them aligned with the BCM. A BCM version bump → new schema path + new `x-bcm-version`.
- Schema changes that break consumers MUST be tracked via a new BCM version (no silent edits at version `1.0.0`).

## Changelog

- 2026-05-04 — Renamed delivered schemas and references to align with bcm-pack canonical English IDs:
  `EVT.BSP.001.TIER_UPGRADED` → `EVT.BSP.001.TIER_UPGRADED`,
  `RVT.BSP.001.TIER_UPGRADE_RECORDED` → `RVT.BSP.001.TIER_UPGRADE_RECORDED`,
  `RES.BSP.001.TIER_UPGRADE` → `RES.BSP.001.TIER_UPGRADE`,
  `OBJ.BSP.001.TIER_CHANGE` → `OBJ.BSP.001.TIER_CHANGE`,
  `OBJ.REF.001.BENEFICIARY_RECORD` → `OBJ.REF.001.BENEFICIARY_RECORD`.
  The producing TASK-001 file is preserved unchanged as the historical record of the original delivery.
