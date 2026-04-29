# CAP.BSP.001.SCO — Development Stub

A minimal .NET 10 worker service that publishes simulated `RVT.BSP.001.SCORE_COURANT_RECALCULE` events on a RabbitMQ topic exchange owned by `CAP.BSP.001.SCO`. The stub honors the runtime JSON Schema at [`/plan/CAP.BSP.001.SCO/contracts/RVT.BSP.001.SCORE_COURANT_RECALCULE.schema.json`](../../../plan/CAP.BSP.001.SCO/contracts/RVT.BSP.001.SCORE_COURANT_RECALCULE.schema.json) — every outgoing payload is validated **before** publication; an invalid payload is never put on the wire.

> **Mode B (Contract + Stub) — not the real microservice.** This stub will be decommissioned when Epic 2 of `CAP.BSP.001.SCO`'s plan delivers the real scoring algorithm under `sources/CAP.BSP.001.SCO/backend/`.

## Bus topology — ADR-TECH-STRAT-001 compliance

| Property | Value | ADR rule |
|---|---|---|
| Broker | RabbitMQ (operational rail) | Rule 1 |
| Exchange (topic) | `bsp.001.sco-events` (owned by `CAP.BSP.001.SCO`) | Rules 1, 5 |
| Routing key | `EVT.BSP.001.SCORE_RECALCULE.RVT.BSP.001.SCORE_COURANT_RECALCULE` | Rule 4 |
| Wire-level event | `RVT.*` only — no autonomous `EVT.*` message | Rule 2 |
| Payload form | Domain event DDD (transition data; not a snapshot, not a field patch) | Rule 3 |
| Schema source of truth | BCM YAML; runtime JSON Schema validates each payload | Rule 6 |

## Run locally

```bash
# 1) RabbitMQ
docker compose up -d

# 2) Stub (default OFF)
cd src/Reliever.BehaviouralScore.Stub
STUB__ACTIVE=true dotnet run
```

| Service | Local URL |
|---|---|
| RabbitMQ AMQP | `localhost:47656` |
| RabbitMQ Management UI | http://localhost:47657 (guest / guest) |

To observe published messages, in the management UI bind a queue to exchange `bsp.001.sco-events` with routing key `EVT.BSP.001.SCORE_RECALCULE.#` and inspect messages.

## Configuration

`src/Reliever.BehaviouralScore.Stub/appsettings.json` (overridable via env vars `STUB__*`, `RABBITMQ__*`):

| Key | Default | Purpose |
|---|---|---|
| `Stub:Active` | `false` | Master switch. Stub never publishes if `false`. **Inactive in production.** |
| `Stub:CadencePerMinute` | `6` | Default cadence. Allowed range: `[1, 10]`. |
| `Stub:CadenceOutsideRangeOverride` | `false` | Required `true` to allow values outside `[1, 10]`. Justify in your deployment notes. |
| `Stub:ExchangeName` | `bsp.001.sco-events` | Topic exchange owned by this capability. |
| `Stub:RoutingKey` | `EVT.BSP.001.SCORE_RECALCULE.RVT.BSP.001.SCORE_COURANT_RECALCULE` | Routing-key convention from ADR-TECH-STRAT-001 Rule 4. |
| `Stub:SchemaPath` | `../../../../plan/CAP.BSP.001.SCO/contracts/RVT.BSP.001.SCORE_COURANT_RECALCULE.schema.json` | Runtime schema loaded at startup. |
| `Stub:ModelVersion` | `stub-1.0.0` | `version_modele` written into every payload. |
| `Stub:SimulatedDossiers` | `[ "DOS-RELIEVER-2026-000001", … ]` | Pool of `identifiant_dossier` values picked at random. |
| `Stub:TypeEvaluationMix` | `{ INITIAL: 0.2, COURANT: 0.8 }` | Probability mix for `type_evaluation`. |

## CI test

Every generated payload is asserted to validate against the runtime schema by an xUnit test that runs entirely offline (no broker required):

```bash
cd test/Reliever.BehaviouralScore.Stub.Tests
dotnet test
```

The test suite covers:
- 200 randomised payloads against the runtime JSON Schema → all valid.
- A corrupted payload is correctly rejected by `EnsureValid`.
- Cadence guard accepts `[1, 10]`, rejects out-of-range values, and accepts them again with `CadenceOutsideRangeOverride=true`.

## Layout

```
sources/CAP.BSP.001.SCO/stub/
├── README.md
├── nuget.config
├── docker-compose.yml                       ← RabbitMQ only (no MongoDB)
├── Reliever.BehaviouralScore.Stub.sln
├── config/
│   └── stub.json                            ← cadence, case IDs, exchange name, schema path
├── src/
│   └── Reliever.BehaviouralScore.Stub/
│       ├── Reliever.BehaviouralScore.Stub.csproj
│       ├── Program.cs                       ← Host + Worker registration
│       ├── Worker.cs                        ← BackgroundService publishing on RabbitMQ
│       ├── PayloadFactory.cs                ← simulated transition data (domain event DDD)
│       ├── SchemaValidator.cs               ← loads JSON Schema, validates every payload
│       ├── StubOptions.cs                   ← configuration types
│       └── appsettings.json
└── test/
    └── Reliever.BehaviouralScore.Stub.Tests/
        ├── Reliever.BehaviouralScore.Stub.Tests.csproj
        └── PayloadValidationTests.cs
```
