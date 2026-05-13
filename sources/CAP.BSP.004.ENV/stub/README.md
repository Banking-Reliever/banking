# CAP.BSP.004.ENV — Development Stub

A minimal .NET 10 worker service that publishes simulated `RVT.BSP.004.CONSUMPTION_RECORDED` events on a RabbitMQ topic exchange owned by `CAP.BSP.004.ENV`. The stub honors the runtime JSON Schema shipped next to the assembly under [`src/Reliever.BudgetEnvelope.Stub/schemas/RVT.BSP.004.CONSUMPTION_RECORDED.schema.json`](src/Reliever.BudgetEnvelope.Stub/schemas/RVT.BSP.004.CONSUMPTION_RECORDED.schema.json) — every outgoing payload is validated **before** publication; an invalid payload is never put on the wire.

> **Mode B (Contract + Stub) — not the real microservice.** This stub will be decommissioned when Epic 3 of `CAP.BSP.004.ENV`'s plan delivers the real envelope engine under `sources/CAP.BSP.004.ENV/backend/` (sibling of this folder).

## Bus topology — `ADR-TECH-STRAT-001` compliance

| Property | Value | ADR rule |
|---|---|---|
| Broker | RabbitMQ (operational rail) | Rule 1 |
| Exchange (topic, durable) | `bsp.004.env-events` (owned by `CAP.BSP.004.ENV`) | Rules 1, 5 |
| Routing key | `EVT.BSP.004.ENVELOPE_CONSUMED.RVT.BSP.004.CONSUMPTION_RECORDED` | Rule 4 |
| Wire-level event | `RVT.*` only — no autonomous `EVT.*` message | Rule 2 |
| Payload form | Domain event DDD (transition data; not a snapshot, not a field patch) | Rule 3 |
| Schema source of truth | Design-time JSON Schema; the runtime schema validates each payload | Rule 6 |

## Run locally

```bash
# 1) RabbitMQ
docker compose up -d

# 2) Stub (default OFF)
cd src/Reliever.BudgetEnvelope.Stub
STUB__ACTIVE=true dotnet run
```

| Service | Local URL |
|---|---|
| RabbitMQ AMQP | `localhost:49656` |
| RabbitMQ Management UI | http://localhost:49657 (guest / guest) |

To observe published messages, in the management UI bind a queue to exchange `bsp.004.env-events` with routing key `EVT.BSP.004.ENVELOPE_CONSUMED.#` and inspect messages.

## Configuration

`src/Reliever.BudgetEnvelope.Stub/appsettings.json` (overridable via env vars `STUB__*`, `RABBITMQ__*`):

| Key | Default | Purpose |
|---|---|---|
| `Stub:Active` | `false` | Master switch. Stub never publishes if `false`. **Inactive in production.** |
| `Stub:CadencePerMinute` | `6` | Default cadence. Allowed range: `[1, 10]`. |
| `Stub:CadenceOutsideRangeOverride` | `false` | Required `true` to allow values outside `[1, 10]`. Justify in your deployment notes. |
| `Stub:ExchangeName` | `bsp.004.env-events` | Topic exchange owned by this capability. |
| `Stub:RoutingKey` | `EVT.BSP.004.ENVELOPE_CONSUMED.RVT.BSP.004.CONSUMPTION_RECORDED` | Routing-key convention from `ADR-TECH-STRAT-001` Rule 4. |
| `Stub:SchemaPath` | `schemas/RVT.BSP.004.CONSUMPTION_RECORDED.schema.json` | Runtime schema loaded at startup (resolved against the assembly's output directory). |
| `Stub:SimulatedCases` | 3 cases × 3..5 envelopes each | Pool of simulated cases. Each case carries its own envelope set (`{ category, cap_amount }`). The stub picks a case at random for each publication and progresses one of its envelopes. |

## Simulation behaviour

The stub maintains an in-memory state per `(case_id, category)` envelope. Each publication picks a random case and a random envelope, computes a realistic random debit increment (a fraction of the remaining balance, clamped so progress is always visible and never overshoots the cap), and emits the resulting transition payload — domain event DDD form (`ADR-TECH-STRAT-001` Rule 3).

When an envelope reaches its `cap_amount`, the stub publishes one final capping consumption (`consumed_amount == cap_amount`) and then resets the envelope to start a fresh allocation cycle (with a new `allocation_id`, mirroring the new `OBJ.BSP.004.ALLOCATION` instance the real engine would create at the start of a new period). This keeps the stream non-degenerate over arbitrarily long runs.

> **Note on paired events.** When the real engine reaches `cap_amount`, it must also emit `RVT.BSP.004.ENVELOPE_CAP_REACHED` atomically in the same transaction (cf. process model invariant `INV.ENV.004` and the routing key `EVT.BSP.004.ENVELOPE_DEPLETED.RVT.BSP.004.ENVELOPE_CAP_REACHED`). This stub is intentionally scoped to `RVT.BSP.004.CONSUMPTION_RECORDED` only — the cap-reached and unconsumed events are out of scope for Epic 1. They will be added in their own contract+stub epic when their consumers begin development.

## Category vocabulary — illustrative, NOT canonical

The categories used by this stub (`ALIMENTATION`, `TRANSPORT`, `LOGEMENT`, `SANTE`, `LOISIRS`) are **hard-coded and illustrative**. They are intentionally decoupled from any real referential to keep the stub self-contained — the stub's purpose is to unblock consumer development without waiting on another not-yet-implemented capability.

**The canonical source of category sets per tier is `CAP.REF.001.TIE`** (per `CPT.BCM.000.PALIER` business rules and `ADR-BCM-FUNC-0008`). The future real envelope engine (Epic 3 — `sources/CAP.BSP.004.ENV/backend/`) **MUST** source the category vocabulary from `CAP.REF.001.TIE` rather than hard-code it. This README serves as the explicit handover note so the real engine knows where to fetch the categories from.

## CI test

Every generated payload is asserted to validate against the runtime schema by an xUnit test that runs entirely offline (no broker required):

```bash
cd test/Reliever.BudgetEnvelope.Stub.Tests
dotnet test
```

The test suite covers:
- 200 randomised payloads against the runtime JSON Schema → all valid.
- A corrupted payload is correctly rejected by `EnsureValid`.
- `consumed_amount` progression: stays within `[0, cap_amount]` and reaches the cap at least once over a 50-iteration run.
- All required fields present with correct types and bounds (`cap_amount > 0`, `consumed_amount >= 0`).
- Cadence guard accepts `[1, 10]`, rejects out-of-range values, and accepts them again with `CadenceOutsideRangeOverride=true`.

## Layout

```
sources/CAP.BSP.004.ENV/stub/
├── README.md
├── nuget.config
├── docker-compose.yml                       ← RabbitMQ only (no MongoDB)
├── Reliever.BudgetEnvelope.Stub.sln
├── config/
│   └── stub.json                            ← cadence, simulated cases & envelopes, exchange name, schema path
├── src/
│   └── Reliever.BudgetEnvelope.Stub/
│       ├── Reliever.BudgetEnvelope.Stub.csproj
│       ├── Program.cs                       ← Host + Worker registration
│       ├── Worker.cs                        ← BackgroundService publishing on RabbitMQ
│       ├── PayloadFactory.cs                ← simulated transition data (domain event DDD)
│       ├── SchemaValidator.cs               ← loads JSON Schema, validates every payload
│       ├── StubOptions.cs                   ← configuration types
│       ├── appsettings.json
│       └── schemas/
│           └── RVT.BSP.004.CONSUMPTION_RECORDED.schema.json  ← runtime contract (copied to output)
└── test/
    └── Reliever.BudgetEnvelope.Stub.Tests/
        ├── Reliever.BudgetEnvelope.Stub.Tests.csproj
        ├── PayloadValidationTests.cs
        └── schemas/
            └── RVT.BSP.004.CONSUMPTION_RECORDED.schema.json  ← same schema, copied to test output
```

## Source-of-truth schema reconciliation

The runtime schema shipped in this folder is a copy of the design-time schema authored under [`plan/CAP.BSP.004.ENV/contracts/RVT.BSP.004.CONSUMPTION_RECORDED.schema.json`](../../../plan/CAP.BSP.004.ENV/contracts/RVT.BSP.004.CONSUMPTION_RECORDED.schema.json). The two files are identical — the copy under `src/.../schemas/` exists only because .NET's `CopyToOutputDirectory` rule needs the file to live next to the csproj. Any contract evolution MUST be driven from the `plan/` source first; the in-stub copy is regenerated alongside.
