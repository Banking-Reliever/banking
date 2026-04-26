---
name: create-bff
description: >
  Scaffolds a complete Backend For Frontend (BFF) for a CANAL zone capability.
  Reads the FUNC ADR and available tactical ADRs to derive endpoints, RabbitMQ consumers,
  publishers, and in-memory state cache. Produces a runnable .NET 10 ASP.NET Core Minimal
  API project under src/{zone-abbrev}/{capability-id}-bff/.
  Trigger on: "create a BFF", "scaffold BFF", "generate BFF", "BFF for CAN", "create bff",
  "new BFF", or any request to generate a backend-for-frontend for a CANAL capability.
---

# Create BFF Skill

Scaffold a complete .NET 10 ASP.NET Core BFF for a CANAL capability. The BFF is the
unique entry point between the frontend and the core IS — it aggregates events from
upstream L2s via RabbitMQ subscriptions, exposes REST endpoints per L3 sub-capability,
and publishes business events produced by frontend interactions.

**Architecture principles (non-negotiable):**
- No domain logic — the BFF aggregates and translates, never decides
- No direct calls to L2 databases — the BFF maintains its own in-memory event cache
- One RabbitMQ exchange per upstream L2 subscribed to
- One exchange owned by the BFF itself for its own published events
- OTel instrumentation from day 0 with `capability_id` as mandatory dimension
- ETag/`If-None-Match` support on all GET endpoints that return cacheable state

---

## Step 1 — Gather Context

### 1.1 Identify the target capability

If the user named a capability (e.g., "CAN.001"), use it directly.
If not, list all CANAL capabilities from `func-adr/` and ask:
> "Which CANAL capability should this BFF serve?"

### 1.2 Read the FUNC ADR

Find the FUNC ADR for the target capability in `func-adr/`. Extract:

| Field | Where to find it |
|-------|-----------------|
| `L3_LIST` | `impacted_capabilities` — all sub-IDs below the L2 (e.g., TAB, ACH, NOT) |
| `EVENTS_PRODUCED` | `impacted_events` — events this L2 is responsible for |
| `EVENTS_CONSUMED` | The "Events Consumed" column of the L2 event table in the Decision section, including emitting L2 |
| `ZONE` | `decision_scope.zoning` |
| `DIGNITY_RULES` | Any special UX/dignity constraints in the Decision section |

### 1.3 Read tactical ADRs (if they exist)

Scan `tech-adr/` for any `ADR-TECH-TACT-*` whose `capability_id` matches the target L2
or any of its L3s. For each one found, extract:
- Endpoint contracts (paths, methods, ETag support, payload shape)
- LocalStorage exclusions (PII rules — what the BFF must NOT return in certain contexts)
- SLO targets (use as comments on the endpoint methods)
- Cache strategy per L3

### 1.4 Detect the current git branch

```bash
BRANCH=$(git branch --show-current 2>/dev/null | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-\|-$//g')
echo "Branch slug: $BRANCH"
```

If not in a git repo or the command fails, use `local` as the branch slug.
Use `{branch}` as a placeholder throughout all generated artefacts — it scopes all
exchange, queue, and service names to the current environment, preventing collisions
between concurrent branches.

### 1.5 Generate a Unique Local Port

```bash
BFF_PORT=$(shuf -i 10000-59999 -n 1)
echo "BFF port: $BFF_PORT"
RABBIT_PORT=$((BFF_PORT + 100))
RABBIT_MGMT_PORT=$((BFF_PORT + 101))
echo "RabbitMQ AMQP: $RABBIT_PORT  Management: $RABBIT_MGMT_PORT"
```

Derive infrastructure ports from the BFF base port so capabilities and branches never collide.

### 1.6 Derive placeholders

From the gathered context, derive:

| Placeholder | Derivation | Example |
|-------------|-----------|---------|
| `{CapId}` | L2 ID without dots, PascalCase | `Can001` |
| `{capability-id}` | L2 ID without dots, lowercase | `can001` |
| `{CapabilityIdDot}` | Full dot notation | `CAP.CAN.001` |
| `{ZoneAbbrev}` | Zone prefix, PascalCase | `Can` |
| `{zone-abbrev}` | Zone prefix, lowercase | `can` |
| `{Namespace}` | `Reliever.{ZoneFullName}.{CapId}Bff` | `Reliever.Canal.Can001Bff` |
| `{branch}` | Slugified git branch name | `feature-can001-bff` |
| `{BFF_PORT}` | Generated port number | `42350` |
| `{RABBIT_PORT}` | `{BFF_PORT} + 100` | `42450` |
| `{RABBIT_MGMT_PORT}` | `{BFF_PORT} + 101` | `42451` |

Zone full names: `Canal` (CAN), `BusinessServiceProduction` (BSP), `Support` (SUP),
`Referential` (REF), `ExchangeB2B` (B2B), `DataAnalytique` (DAT), `Pilotage` (PIL).

---

## Step 2 — Determine Output Directory

Output path: `src/{zone-abbrev}/{capability-id}-bff/`

Example: `src/can/can001-bff/`

If `src/` does not exist in the project root, create it.
If the output directory already exists, stop and warn:
> "The directory `src/{zone-abbrev}/{capability-id}-bff/` already exists. Delete it first
> or rename it before scaffolding."

Record the branch slug and the generated ports in `src/{zone-abbrev}/{capability-id}-bff/.env.local`
(never committed — add to `.gitignore`):

```
BFF_PORT={BFF_PORT}
RABBIT_PORT={RABBIT_PORT}
RABBIT_MGMT_PORT={RABBIT_MGMT_PORT}
BRANCH={branch}
```

This file allows the `test-business-capability` skill to locate and start the BFF on
the correct port without re-running port allocation.

---

## Step 3 — Generate All Files

Read `references/templates.md` for every code template. Substitute all placeholders
before writing any file. Generate files in the order listed below.

**For variables that depend on the FUNC ADR content** (L3 list, events), generate code
sections iteratively — one class per L3, one consumer per consumed event type, etc.

### Files to generate (in order)

1. `{CapId}Bff.csproj`
2. `nuget.config`
3. `appsettings.json`
4. `appsettings.Development.json`
5. `Program.cs`
6. `Telemetry/TelemetrySetup.cs`
7. `Cache/{CapId}StateCache.cs`
8. `Endpoints/{L3Name}Endpoints.cs` — **one file per L3**
9. `Consumers/{EventName}Consumer.cs` — **one file per unique business event type consumed**
10. `Publishers/{EventName}Publisher.cs` — **one file per business event produced**
11. `Contracts/Events/` — one record per event (consumed and produced)
12. `Dockerfile`
13. `docker-compose.yml`

---

## Step 4 — Naming Conventions

### RabbitMQ exchange names
- BFF owns: `{branch}.{capability-id}.exchange` (e.g., `feature-can001-bff.can001.exchange`)
- Upstream L2 exchange subscribed to: derive from the emitting capability ID, prefixed
  with the branch slug (e.g., events from `CAP.BSP.001.SCO` → exchange
  `{branch}.bsp001-sco.exchange`)

The `{branch}` prefix ensures that exchanges and queues are scoped to the current
development environment, preventing message cross-contamination between concurrent branches.

### Routing keys
Follows TECH-STRAT-001 convention: `{BusinessEventName}.{ResourceEventName}`
For consumers: use wildcard `{BusinessEventName}.#` to catch all resource variants.

### Queue names (created by BFF for its subscriptions)
`{branch}.{capability-id}.{emitting-cap-id}.{business-event-name}.queue`
Example: `feature-can001-bff.can001.bsp001sco.scorecomportemental.queue`

### Endpoint paths
`/{zone-abbrev}/{capability-id}/{l3-id}/{resource}`
Example: `/can/can001/tab/snapshot`

### OTel service name
`{branch}-{capability-id}-bff` (e.g., `feature-can001-bff-can001-bff`)

### capability_id tag on all OTel signals
`{CapabilityIdDot}` (e.g., `CAP.CAN.001`)

### environment tag on all OTel signals
`{branch}` — identifies the active development environment on all signals

---

## Step 5 — Validate and Summarize

After writing all files, run:
```bash
find src/{zone-abbrev}/{capability-id}-bff -type f | sort
```

Print the file tree to confirm completeness.

Then tell the user:

```
BFF scaffolded at src/{zone-abbrev}/{capability-id}-bff/

Branch / Environment : {branch}
BFF HTTP port        : {BFF_PORT}
RabbitMQ AMQP        : {RABBIT_PORT}
RabbitMQ management  : {RABBIT_MGMT_PORT}

Endpoints:
  [list each endpoint with method + path]

Consumers (RabbitMQ):
  [list each consumer with exchange + routing key filter]

Publishers (RabbitMQ):
  [list each publisher with event name + routing key]

To start the local stack:
  cd src/{zone-abbrev}/{capability-id}-bff
  docker compose up -d
  dotnet run --urls http://localhost:{BFF_PORT}

Health check:
  curl http://localhost:{BFF_PORT}/health

⚠ Set GITHUB_USERNAME and GITHUB_TOKEN env vars before dotnet restore
  (required for the naive-unicorn GitHub Packages feed in nuget.config)
```

Note: the `/health` endpoint is required by the `test-business-capability` skill
to wait for the BFF to be ready before running integration tests.

---

## State Cache Design

The `{CapId}StateCache` is a singleton in-memory store. It holds the latest known state
for each L3 that the BFF serves. Structure:

```
{CapId}StateCache
├── {L3State} per L3 (one nested class per L3)
│   ├── Data fields (derived from tactical ADR payload shape)
│   ├── ETag (string — changes on every update)
│   └── UpdatedAt (DateTime UTC)
└── Update methods (one per consumed event type)
```

The ETag is recomputed on every state mutation. It is a short hash of the updated fields
(8 hex chars from a new Guid, or a hash of the state). The BFF never stores PII in the
cache — enforce the exclusions from the tactical ADR.

---

## ETag Support Pattern

Every GET endpoint that returns cacheable state must implement:

```
1. Read If-None-Match header from request
2. Compare with current ETag from StateCache
3. If match → return 304 Not Modified (no body)
4. If no match → return 200 OK with current state + ETag response header
```

All endpoints must set `Cache-Control: no-store` to prevent intermediary caching —
ETag is handled at the BFF level only.

---

## OTel Instrumentation Rules

All OTel signals (metrics, logs, traces) produced by the BFF must carry:
- `capability_id` = `{CapabilityIdDot}` (e.g., `CAP.CAN.001`)
- `zone` = `{zone-abbrev}` (e.g., `can`)
- `deployable` = `reliever-{zone-abbrev}` (e.g., `reliever-can`)
- `environment` = read from `ASPNETCORE_ENVIRONMENT`

The BFF must propagate the W3C `traceparent` header:
- **Inbound**: extract `traceparent` from incoming HTTP requests (ASP.NET Core does this
  automatically with OTel ASP.NET Core instrumentation)
- **Outbound RabbitMQ publish**: inject `traceparent` into RabbitMQ message headers
  using MassTransit's built-in OTel support (enabled by calling `.UseOpenTelemetry()`)

---

## Facilitation Notes

- If the FUNC ADR lists events consumed but does not specify the emitting L2 capability ID,
  search other FUNC ADRs to find which L2 produces that event name.
- If a tactical ADR for an L3 specifies a payload shape (e.g., ADR-TECH-TACT-001 for TAB),
  use that shape verbatim for the response DTO. If no tactical ADR exists, derive a
  reasonable DTO from the FUNC ADR event names and the dignity rules.
- Never generate HTTP clients to call upstream L2 REST APIs directly — the BFF gets its
  data from RabbitMQ event subscriptions. The only exception is REF.001 cold-path calls
  (cache reconstruction after purge), which are explicitly documented in TECH-STRAT-004.
- The BFF does not implement OpenFGA directly — authentication middleware is wired in
  `Program.cs` as a placeholder comment (`// TODO: wire OpenFGA middleware — decided in
  L2 tactical ADR`) unless the L2 tactical ADR already specifies the integration.
