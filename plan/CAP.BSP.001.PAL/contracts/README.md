# Event contracts — CAP.BSP.001.PAL (Tier Management)

Owner: **CAP.BSP.001.PAL** (Tier Management) — L3 of `CAP.BSP.001` (Behavioural Remediation), zone `BUSINESS_SERVICE_PRODUCTION`.

This directory holds the **JSON Schema (Draft 2020-12)** contracts for the events emitted by `CAP.BSP.001.PAL`. The schemas are derived design-time artefacts produced from the BCM YAML source of truth — the BCM remains authoritative (ADR-TECH-STRAT-001 Rule 6).

Epic 1 scope: **upward tier crossing only** (`PALIER_HAUSSE` / `FRANCHISSEMENT_ENREGISTRE`). Downward crossings (`RETROGRADATION`) and overrides will be contracted in their own epics.

## Schemas

| File | BCM ID | Role | Generates a bus message? | BCM source of truth |
|---|---|---|---|---|
| `RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE.schema.json` | `RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE` | **Runtime contract** — every payload published on the bus by `CAP.BSP.001.PAL` MUST validate against this schema | **Yes** (only this) | `bcm/resource-event-reliever.yaml`, `bcm/resource-reliever.yaml` (carries `RES.BSP.001.FRANCHISSEMENT`) |
| `EVT.BSP.001.PALIER_HAUSSE.schema.json` | `EVT.BSP.001.PALIER_HAUSSE` | **Design-time documentation only** — describes the abstract business fact at the meta-model level | **No** — per ADR-TECH-STRAT-001 Rule 2 | `bcm/business-event-reliever.yaml`, `bcm/business-object-reliever.yaml` (carries `OBJ.BSP.001.CHANGEMENT_PALIER`) |

## Bus topology (per ADR-TECH-STRAT-001)

| Item | Value |
|---|---|
| Broker | RabbitMQ (operational rail) |
| Exchange type | `topic` |
| Exchange name | `bsp.001.pal-events` (owned exclusively by `CAP.BSP.001.PAL` — Rule 1) |
| Routing key | `EVT.BSP.001.PALIER_HAUSSE.RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE` (Rule 4) |
| Wire-level event | `RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE` only — no autonomous `EVT.*` message (Rule 2) |
| Payload form | Domain event DDD — coherent atomic transition data (Rule 3) |

## Versioning encoding

Each schema declares its version in two places, kept consistent:

- `$id` URL with version segment, e.g. `…/RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE/1.0.0/schema.json`. A new BCM version becomes a new path = explicit deprecation surface.
- Top-level annotation `"x-bcm-version": "1.0.0"` matching the BCM event version. Inspectable without URL parsing.

## Correlation key

Both schemas declare **`identifiant_dossier`** as the correlation key.

Resolution path to the canonical beneficiary identifier:

```
identifiant_dossier  ──(query CAP.REF.001.BEN)──►  OBJ.REF.001.FICHE_BENEFICIAIRE.identifiant_interne
```

The producer **does NOT** carry `identifiant_interne` on the wire (privacy + decoupling, ADR-BCM-URBA-0009). Consumers wishing to obtain the canonical identifier perform the lookup themselves.

## Known consumers (as of 2026-04-28)

Read from `bcm/business-subscription-reliever.yaml` — these L2/L3 capabilities subscribe to `EVT.BSP.001.PALIER_HAUSSE` and will receive `RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE` messages on the routing key above:

| Consumer L2/L3 | Why it cares |
|---|---|
| `CAP.B2B.001.CRT` | Card-rule update — a tier upgrade widens authorised categories and limits on the dedicated card. |
| `CAP.BSP.002.SOR` | Programme exit — reaching the final tier triggers the transfer to the standard banking app (`est_sortie_programme=true`). |
| `CAP.BSP.003.NOT` | Prescriber notification — a tier upgrade is a progression event to display in the prescriber portal. |
| `CAP.BSP.004.AUT` | Real-time authorisation rules — a tier upgrade widens the set of authorised categories. |
| `CAP.BSP.004.ENV` | Budget envelope recalibration — a new tier defines new categories and new limits. |
| `CAP.CAN.001.NOT` | Beneficiary congratulations notification — gamification key event. |
| `CAP.CAN.001.TAB` | Beneficiary dashboard — major progression event, displayed in a rewarding way. **First consumer in Epic 1.** |
| `CAP.CAN.002.VUE` | Prescriber portal case state — unlocks new actions when the case state changes. |

## Stub

A development stub publishing simulated payloads on the routing key above lives under `sources/CAP.BSP.001.PAL/stub/`. Every payload it publishes is validated against `RVT.BSP.001.FRANCHISSEMENT_ENREGISTRE.schema.json` before being sent — fail-fast on schema violation. The stub is inactive by default (`STUB_ACTIVE=false`); activate it via env var to publish on a configurable cadence in the range **1–10 events/min**.

See `sources/CAP.BSP.001.PAL/stub/README.md` for usage.

## Governance

- Source of truth (per ADR-TECH-STRAT-001 Rule 6): the BCM YAML files (`bcm/business-event-*.yaml`, `bcm/resource-event-*.yaml`, `bcm/business-object-*.yaml`, `bcm/resource-*.yaml`).
- These JSON Schemas are **derived artefacts** — keep them aligned with the BCM. A BCM version bump → new schema path + new `x-bcm-version`.
- Schema changes that break consumers MUST be tracked via a new BCM version (no silent edits at version `1.0.0`).
