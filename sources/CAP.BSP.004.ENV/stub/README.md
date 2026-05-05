# CAP.BSP.004.ENV — Development Stub

This is a **Mode B contract+stub** for `CAP.BSP.004.ENV` (Budget Envelope Management). It publishes simulated `RVT.BSP.004.CONSUMPTION_RECORDED` messages on a RabbitMQ topic exchange owned by `CAP.BSP.004.ENV`, so consumers (`CAP.CAN.001.TAB` first; future scoring feedback loops, notification engines, etc.) can develop in complete isolation from the real envelope engine.

This stub is **not** a microservice. It contains:
- one .NET 10 worker process publishing simulated payloads on a RabbitMQ topic exchange;
- the runtime JSON Schema (a copy of the contract under `plan/CAP.BSP.004.ENV/contracts/`);
- xUnit tests guaranteeing every generated payload validates against the schema.

It will be **decommissioned** by `CAP.BSP.004.ENV` itself when the real envelope engine is delivered (Epic 3). At that point, the contract under `plan/CAP.BSP.004.ENV/contracts/` is preserved verbatim — no schema-driven consumer change is required.

---

## Bus topology (per ADR-TECH-STRAT-001)

| Item | Value | ADR rule |
|---|---|---|
| Broker | RabbitMQ (operational rail) | Rule 1 |
| Exchange type | `topic` | Rule 1 |
| Exchange name | `bsp.004.env-events` (owned exclusively by `CAP.BSP.004.ENV`) | Rules 1, 5 |
| Routing key | `EVT.BSP.004.ENVELOPE_CONSUMED.RVT.BSP.004.CONSUMPTION_RECORDED` | Rule 4 |
| Wire-level event | `RVT.BSP.004.CONSUMPTION_RECORDED` only — no autonomous EVT message | Rule 2 |
| Payload form | Domain event DDD — coherent atomic transition data | Rule 3 |
| Validation site | At publish time, against the runtime JSON Schema (fail-fast) | DoD |

**Reminder** — only the **resource** event generates a wire-level message (Rule 2). The business event `EVT.BSP.004.ENVELOPE_CONSUMED` exists at the meta-model level only; it never becomes an autonomous bus payload. It appears exclusively as the prefix of the routing key.

## Category vocabulary — illustrative only

The spending categories used by this stub (`ALIMENTATION`, `TRANSPORT`, `SANTE`, `LOGEMENT`, `ENERGIE`) are **illustrative and hard-coded inside the stub** for offline development. They are **not** authoritative.

The **canonical authoritative source** of envelope category sets per autonomy tier is **`CAP.REF.001.PAL`** (Tier Catalogue / Palier referential). The future real envelope engine (Epic 3) **MUST** source the per-tier category vocabulary from `CAP.REF.001.PAL`; the stub does not, because doing so would couple the stub to a referential that consumers do not depend on for contract development.

If a consumer wishes to test against an authoritative tier vocabulary, override the `Stub:Cases` configuration with the relevant categories — the runtime contract intentionally does not enum-constrain `categorie` at the schema level for that reason (categories are free-form strings on the wire, governance is left to the producer/referential at design time).

---

## Configuration

Configuration layers (in increasing precedence):

1. `appsettings.json` — defaults shipped in the binary.
2. `config/stub.json` — operator overrides; mounted next to the binary at runtime.
3. Environment variables prefixed with `STUB_` — deployment overrides (CI / containers).

| Setting | Default | Constraint |
|---|---|---|
| `Stub:Active` | `false` | **MUST be false in production**. Activate via env var `STUB_Stub__Active=true`. |
| `Stub:EventsPerMinute` | `6` | Default range `[1, 10]`. Outside this range requires `Stub:AllowOutOfRangeCadence=true`. |
| `Stub:AllowOutOfRangeCadence` | `false` | Explicit override required for cadence outside `[1, 10]`. |
| `Stub:DefaultMontantPlafond` | `200.00` | Initial cap of every fresh envelope. |
| `Stub:TransitionsPerEnvelope` | `6` | Number of consumption transitions before envelope reset. |
| `Stub:Cases` | 3 cases × multiple categories | At least one case required; each case must have ≥1 category. |
| `Stub:RabbitMq:HostName` | `localhost` | |
| `Stub:RabbitMq:Port` | `45481` | AMQP port (matches `docker-compose.yml`). |
| `Stub:Bus:ExchangeName` | `bsp.004.env-events` | Topic exchange owned by `CAP.BSP.004.ENV`. |
| `Stub:Bus:RoutingKey` | `EVT.BSP.004.ENVELOPE_CONSUMED.RVT.BSP.004.CONSUMPTION_RECORDED` | Per Rule 4. |
| `Stub:Schema:RuntimeSchemaPath` | `schemas/RVT.BSP.004.CONSUMPTION_RECORDED.schema.json` | Loaded once at startup. |

### Environment variables

The configuration provider uses `__` as the separator for nested keys, so:

```bash
export STUB_Stub__Active=true
export STUB_Stub__EventsPerMinute=3
```

is equivalent to `Stub:Active=true` and `Stub:EventsPerMinute=3` at the JSON layer.

---

## Run locally

### 1. Start RabbitMQ

```bash
cd sources/CAP.BSP.004.ENV/stub
docker compose up -d
```

| Service | URL |
|---|---|
| AMQP | `amqp://guest:guest@localhost:45481/` |
| Management UI | <http://localhost:45482> (guest/guest) |

### 2. Run the stub (active)

```bash
STUB_Stub__Active=true dotnet run --project src/Reliever.BudgetEnvelopeManagement.Stub
```

You should see logs like:

```
info: Reliever.BudgetEnvelopeManagement.Stub.SchemaValidator
      Loaded runtime JSON Schema for RVT.BSP.004.CONSUMPTION_RECORDED from '…' (x-bcm-version=1.0.0).
info: Reliever.BudgetEnvelopeManagement.Stub.Worker
      Stub ACTIVE — exchange='bsp.004.env-events' routingKey='EVT.BSP.004.ENVELOPE_CONSUMED.RVT.BSP.004.CONSUMPTION_RECORDED' cadence=6/min (period=10000ms)
info: Reliever.BudgetEnvelopeManagement.Stub.Worker
      Topic exchange 'bsp.004.env-events' declared. Beginning publication loop.
info: Reliever.BudgetEnvelopeManagement.Stub.Worker
      Published RVT.BSP.004.CONSUMPTION_RECORDED for dossier=DOS-2026-000001 category=ALIMENTATION
```

### 3. Subscribe a consumer (illustrative)

In the RabbitMQ Management UI, declare a queue and bind it to `bsp.004.env-events` with one of:

- `EVT.BSP.004.ENVELOPE_CONSUMED.#` — every resource event linked to the consumption fact (currently only one).
- `EVT.BSP.004.ENVELOPE_CONSUMED.RVT.BSP.004.CONSUMPTION_RECORDED` — exact match.

---

## Run tests

```bash
cd sources/CAP.BSP.004.ENV/stub
dotnet test
```

The tests verify:

- the runtime schema is present at the test output;
- the schema's `$id` and `x-bcm-version` are aligned at `1.0.0`;
- the schema declares `identifiant_dossier` as the correlation key;
- the schema annotates the payload form as `domain-event-DDD`;
- the schema description documents the `solde_disponible = montant_plafond - montant_consomme` formula AND `solde_disponible` is NOT a transported field;
- every generated payload validates against the runtime schema (500 iterations, multi-case, multi-category, with envelope resets);
- every generated payload honors the cap invariant `0 <= montant_consomme <= montant_plafond`;
- round-robin coverage of all configured (case × category) allocations;
- correlation-key fidelity (every payload's `identifiant_dossier` matches its allocation case);
- the stub never emits `solde_disponible` or `identifiant_interne` (privacy + decoupling per ADR-BCM-URBA-0009);
- the validator rejects payloads with invalid `montant_plafond`, missing `identifiant_dossier`, or unexpected additional properties.

---

## Deactivation in production

The stub is **inactive by default** (`Stub:Active=false`). Deploying it to a production-like environment without explicitly setting `STUB_Stub__Active=true` produces a warning log and an idle (no-publish) host. This satisfies the DoD requirement that the stub be "activatable / deactivatable via environment configuration (inactive in production)".

Operationally, production environments should not deploy this stub at all — once the real envelope engine ships in `sources/CAP.BSP.004.ENV/backend/`, this stub directory will be removed.
