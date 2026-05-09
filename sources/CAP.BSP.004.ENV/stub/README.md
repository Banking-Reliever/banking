# CAP.BSP.004.ENV — Budget Envelope Management — Development Stub

This is the **development stub** for `CAP.BSP.004.ENV` (Budget Envelope Management). Mode B (contract+stub) per `task_type: contract-stub` of TASK-001.

It publishes simulated `RVT.BSP.004.CONSUMPTION_RECORDED` resource events on the RabbitMQ topic exchange owned by `CAP.BSP.004.ENV` so that consumers (`CAP.CHN.001.DSH` first; future scoring feedback loops, notifications, …) can develop their consumer logic in complete isolation, before the real Budget Envelope Management engine (`AGG.BSP.004.ENV.PERIOD_BUDGET`) is implemented.

The stub is a sibling of the future `sources/CAP.BSP.004.ENV/backend/` (the real microservice). When the engine ships, the stub is decommissioned — consumers do not need to change a line because the contract is identical.

## What this stub publishes

| Item | Value |
|---|---|
| Broker | RabbitMQ (operational rail per `ADR-TECH-STRAT-001`) |
| Exchange | `bsp.004.env-events` (topic, owned by `CAP.BSP.004.ENV` — Rules 1, 5) |
| Routing key | `EVT.BSP.004.ENVELOPE_CONSUMED.RVT.BSP.004.CONSUMPTION_RECORDED` (Rule 4) |
| Resource event | `RVT.BSP.004.CONSUMPTION_RECORDED` (only this — no autonomous `EVT.*` message, Rule 2) |
| Payload form | Domain event DDD — atomic transition data of a single envelope debit (Rule 3) |
| Schema | `../../plan/CAP.BSP.004.ENV/contracts/RVT.BSP.004.CONSUMPTION_RECORDED.schema.json` |
| Cadence | 1–10 events/min (default 6); outside requires explicit override |
| Activation | Inactive by default (`Stub:Active=false`); MUST remain inactive in production |

Every payload is validated against the runtime JSON Schema **before** publication — fail-fast on schema violation.

## Category vocabulary — illustrative, not canonical

The illustrative spending categories used by this stub (`ALIMENTATION`, `TRANSPORT`, `SANTE`, `LOISIRS`, `VETEMENTS`, …) are **hard-coded** in `appsettings.json` / `config/stub.json`. They are intended to unblock consumer development without coupling Epic 1 to another not-yet-implemented capability.

The **canonical source of category sets per tier is `CAP.REF.001.TIE`** (per `CPT.BCM.000.PALIER` / `CPT.BCM.000.TIER` business rules). When the real `sources/CAP.BSP.004.ENV/backend/` engine is delivered, it MUST source categories from `CAP.REF.001.TIE` — never from this stub. Consumers MUST NOT hard-code the category list either: bind on the routing key and treat `category` as an opaque string from the consumer's perspective.

## Quick start

1. **Start RabbitMQ** locally:

   ```bash
   cd sources/CAP.BSP.004.ENV/stub
   docker compose up -d
   ```

   - AMQP port: `localhost:45481`
   - Management UI: <http://localhost:45482> (guest / guest)

2. **Activate and run** the stub:

   ```bash
   cd sources/CAP.BSP.004.ENV/stub
   dotnet restore
   STUB_Stub__Active=true dotnet run --project src/Reliever.EnvelopeManagement.Stub
   ```

   Or set `Stub:Active=true` in `src/Reliever.EnvelopeManagement.Stub/appsettings.json` (development only — never in production).

3. **Subscribe a consumer queue**:

   - Bind a queue to the exchange `bsp.004.env-events` with the routing key
     `EVT.BSP.004.ENVELOPE_CONSUMED.RVT.BSP.004.CONSUMPTION_RECORDED`
     (or `EVT.BSP.004.ENVELOPE_CONSUMED.#` to receive every resource event tied to that business event).

## Configuration

Configuration is layered (lowest precedence first):

1. `src/Reliever.EnvelopeManagement.Stub/appsettings.json` — defaults shipped in the binary.
2. `config/stub.json` — overrides loaded from disk at startup (relative to the working directory).
3. Environment variables — final overrides at deployment time.

Environment variables follow the standard `Microsoft.Extensions.Configuration` convention (also accepting the `STUB_` prefix):

| Env var | Maps to |
|---|---|
| `STUB_Stub__Active` (or `Stub__Active`) | `Stub:Active` |
| `STUB_Stub__EventsPerMinute` | `Stub:EventsPerMinute` |
| `STUB_Stub__AllowOutOfRangeCadence` | `Stub:AllowOutOfRangeCadence` |
| `STUB_Stub__RabbitMq__HostName` | `Stub:RabbitMq:HostName` |
| `STUB_Stub__RabbitMq__Port` | `Stub:RabbitMq:Port` |
| `STUB_Stub__Bus__ExchangeName` | `Stub:Bus:ExchangeName` |
| `STUB_Stub__Bus__RoutingKey` | `Stub:Bus:RoutingKey` |

> **Out-of-range cadence**: setting `EventsPerMinute` outside `[1, 10]` requires `AllowOutOfRangeCadence=true` (per Definition of Done — explicit override).

### Configuring simulated cases

The stub supports an arbitrary number of simulated cases, each with its own envelope set (one envelope per spending category). Configure via the `Stub:Cases` array. Example:

```json
"Cases": [
  {
    "CaseId": "CASE-2026-000001",
    "PeriodIndex": 0,
    "PeriodStart": "2026-05-01",
    "PeriodEnd": "2026-05-31",
    "Envelopes": [
      { "AllocationId": "ALLOC-2026-000001-ALIMENTATION", "Category": "ALIMENTATION", "CapAmount": 250.0 },
      { "AllocationId": "ALLOC-2026-000001-TRANSPORT",    "Category": "TRANSPORT",    "CapAmount": 100.0 }
    ]
  }
]
```

The default configuration ships **three cases** with distinct envelope sets to exercise consumer logic across multiple beneficiary profiles.

## What the stub simulates

For each tick (one per cadence period):

1. Picks the next case round-robin.
2. Picks the next envelope of that case (round-robin within the case).
3. Computes a debit amount between 1% and 25% of `cap_amount`, clamped to the remaining balance.
4. Updates in-memory state (`consumed_amount_after`, `remaining_amount`).
5. Validates the resulting payload against `RVT.BSP.004.CONSUMPTION_RECORDED.schema.json`.
6. Publishes on the routing key (with AMQP headers carrying the BCM lineage: `x-bcm-business-event`, `x-bcm-resource-event`, `x-bcm-emitting-capability`, `x-bcm-version`).
7. When an envelope reaches its cap, it wraps around to `consumed_amount=0` (representing a fresh period) so the stub can keep publishing indefinitely.

This realistic progression lets consumer dashboards (`CAP.CHN.001.DSH`) display believable envelope-fill bars over time.

## Tests

```bash
cd sources/CAP.BSP.004.ENV/stub
dotnet test
```

Tests cover:

- Schema declares `$id` with version segment AND `x-bcm-version` annotation (versioning encoding).
- Every generated payload validates against the runtime schema.
- Every payload carries `case_id` (the correlation key).
- `consumed_amount_after + remaining_amount == cap_amount` (within float tolerance) — coherence check.
- `amount > 0` for every payload (INV.ENV.003).
- The stub rotates across all configured cases.
- Validator rejects payloads missing `case_id`, with `amount <= 0`, or with extra wire-level fields (`additionalProperties: false`).

## Layout

```
sources/CAP.BSP.004.ENV/stub/
├── README.md                 ← this file
├── docker-compose.yml        ← RabbitMQ only
├── nuget.config
├── Reliever.EnvelopeManagement.Stub.slnx
├── config/
│   └── stub.json             ← cadence, cases, envelopes, exchange name, schema path
├── src/
│   └── Reliever.EnvelopeManagement.Stub/
│       ├── Reliever.EnvelopeManagement.Stub.csproj
│       ├── Program.cs        ← Host registration, configuration layering
│       ├── StubOptions.cs    ← strongly-typed options binding
│       ├── Worker.cs         ← BackgroundService publishing on RabbitMQ
│       ├── PayloadFactory.cs ← simulated envelope-debit transitions
│       ├── SchemaValidator.cs ← loads JSON Schema, fail-fast validates
│       ├── appsettings.json
│       └── schemas/
│           └── RVT.BSP.004.CONSUMPTION_RECORDED.schema.json
└── tests/
    └── Reliever.EnvelopeManagement.Stub.Tests/
        ├── Reliever.EnvelopeManagement.Stub.Tests.csproj
        ├── PayloadValidatesAgainstSchemaTests.cs
        └── schemas/
            └── RVT.BSP.004.CONSUMPTION_RECORDED.schema.json
```

## Decommissioning

When the real `sources/CAP.BSP.004.ENV/backend/` ships its first version of the envelope engine (the `AGG.BSP.004.ENV.PERIOD_BUDGET` aggregate exposed in `process/CAP.BSP.004.ENV/aggregates.yaml`), this stub is removed. Consumers do not need to change a line because the contract is identical.

The future engine MUST source spending-category sets per tier from `CAP.REF.001.TIE` — the stub's hard-coded categories are illustrative only.
