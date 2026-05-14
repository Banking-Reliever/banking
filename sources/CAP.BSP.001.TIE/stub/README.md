# CAP.BSP.001.TIE — Tier Management — Development Stub

This is the **development stub** for `CAP.BSP.001.TIE` (Tier Management). Mode B (contract+stub) per `task_type: contract-stub` of TASK-001.

It publishes simulated `RVT.BSP.001.TIER_UPGRADE_RECORDED` resource events on the RabbitMQ topic exchange owned by `CAP.BSP.001.TIE` so that consumers (`CAP.CHN.001.DSH`, future `CAP.CHN.001.NOT`, `CAP.B2B.001.CRT`, …) can develop their consumer logic in complete isolation, before the real Tier Management engine is implemented.

The stub is a sibling of the future `sources/CAP.BSP.001.TIE/backend/` (the real microservice). When the engine ships, the stub is decommissioned — consumers do not need to change a line because the contract is identical.

## What this stub publishes

| Item | Value |
|---|---|
| Broker | RabbitMQ (operational rail per ADR-TECH-STRAT-001) |
| Exchange | `bsp.001.pal-events` (topic, owned by CAP.BSP.001.TIE — Rule 1, 5) |
| Routing key | `EVT.BSP.001.TIER_UPGRADED.RVT.BSP.001.TIER_UPGRADE_RECORDED` (Rule 4) |
| Resource event | `RVT.BSP.001.TIER_UPGRADE_RECORDED` (only this — no autonomous EVT message, Rule 2) |
| Payload form | Domain event DDD — atomic transition data (Rule 3) |
| Schema | `../../../process/CAP.BSP.001.TIE/schemas/RVT.BSP.001.TIER_UPGRADE_RECORDED.schema.json` |
| direction | Always `UPGRADE` (upward only — Epic 1 scope) |
| Cadence | 1–10 events/min (default 6); outside requires explicit override |
| Activation | Inactive by default (`STUB_ACTIVE=false`); MUST remain inactive in production |

Every payload is validated against the runtime JSON Schema **before** publication — fail-fast on schema violation.

## Quick start

1. **Start RabbitMQ** locally:

   ```bash
   cd sources/CAP.BSP.001.TIE/stub
   docker compose up -d
   ```

   - AMQP port: `localhost:45381`
   - Management UI: <http://localhost:45382> (guest / guest)

2. **Activate and run** the stub:

   ```bash
   cd sources/CAP.BSP.001.TIE/stub
   dotnet restore
   STUB_Stub__Active=true dotnet run --project src/Reliever.TierManagement.Stub
   ```

   Or via the appsettings/config files: set `Stub:Active=true` in `src/Reliever.TierManagement.Stub/appsettings.json` (development only — never in production).

3. **Subscribe a consumer queue**:

   - Bind a queue to the exchange `bsp.001.pal-events` with the routing key
     `EVT.BSP.001.TIER_UPGRADED.RVT.BSP.001.TIER_UPGRADE_RECORDED`
     (or `EVT.BSP.001.TIER_UPGRADED.#` to receive every resource event tied to that business event).

## Configuration

Configuration is layered (lowest precedence first):

1. `src/Reliever.TierManagement.Stub/appsettings.json` — defaults shipped in the binary.
2. `config/stub.json` — overrides loaded from disk at startup (relative to the working directory).
3. Environment variables — final overrides at deployment time.

Environment variables follow the standard `Microsoft.Extensions.Configuration` convention:

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

## Tests

```bash
cd sources/CAP.BSP.001.TIE/stub
dotnet test
```

Tests cover:

- Schema declares `$id` with version segment AND `x-bcm-version` annotation (versioning encoding).
- Every generated payload validates against the runtime schema.
- Every payload has `direction=UPGRADE` (upward-only constraint).
- Every payload has a strictly upward tier transition (no T1→T0 etc.).
- Validator rejects payloads with `direction=DEMOTION` (out of scope).
- Validator rejects payloads missing the correlation key `case_id`.

## Layout

```
sources/CAP.BSP.001.TIE/stub/
├── README.md                 ← this file
├── docker-compose.yml        ← RabbitMQ only
├── nuget.config
├── Reliever.TierManagement.Stub.sln
├── config/
│   └── stub.json             ← cadence, case IDs, exchange name, schema path
├── src/
│   └── Reliever.TierManagement.Stub/
│       ├── Reliever.TierManagement.Stub.csproj
│       ├── Program.cs        ← Host registration, configuration layering
│       ├── StubOptions.cs    ← strongly-typed options binding
│       ├── Worker.cs         ← BackgroundService publishing on RabbitMQ
│       ├── PayloadFactory.cs ← simulated transition data
│       ├── SchemaValidator.cs ← loads JSON Schema, fail-fast validates
│       ├── appsettings.json
│       └── schemas/
│           └── RVT.BSP.001.TIER_UPGRADE_RECORDED.schema.json
└── tests/
    └── Reliever.TierManagement.Stub.Tests/
        ├── Reliever.TierManagement.Stub.Tests.csproj
        ├── PayloadValidatesAgainstSchemaTests.cs
        └── schemas/
            └── RVT.BSP.001.TIER_UPGRADE_RECORDED.schema.json
```

## Decommissioning

When the real `sources/CAP.BSP.001.TIE/backend/` ships its first version of the upward-tier engine, this stub is removed. Consumers do not need to change a line because the contract is identical.
