---
name: process
description: >
  Generates the **Process Modelling** layer of a business capability — the DDD
  tactical layer that sits between Big-Picture Event Storming (BCM YAML, FUNC
  ADR, URBA/TECH-STRAT ADRs, product/business/tech visions consumed via
  `bcm-pack`) and Software Design (the `/plan` → `/task` → `/code` pipeline that
  consumes it). Produces `process/{capability-id}/` as a durable, re-plan-resistant
  set of YAML artifacts: aggregates, commands, policies, read-models, bus
  topology, derived REST surface, JSON Schemas. Use this skill whenever the
  user wants to model the process of a capability, sketch its aggregates and
  commands, decide its bus topology, capture its reactive policies, or generate
  command/event JSON Schemas. Trigger on: "process this capability", "process
  modelling", "process modeling", "model the process for X", "/process X",
  "aggregates and commands for X", "domain events for X", "Event Storming for
  X", "design the bus for X", "tactical DDD for X", "design the aggregates for
  X", or any time a BCM-validated capability is ready to be modelled before
  `/plan` runs. Also trigger proactively after `bcm-pack pack <CAP_ID>` returns a
  complete corpus and the user is about to start `/plan` — `/plan` should always
  read a `process/{capability-id}/` folder, never re-derive it.

  Authorship rule: `/process` is the **only** authority on `process/{capability-id}/`.
  No other skill — `/plan`, `/task`, `/code`, `/fix`, `/launch-task`, `/continue-work`
  — and no agent spawned by them (`implement-capability`, `create-bff`,
  `code-web-frontend`, `test-business-capability`, `test-app`) may modify any
  file under `process/`. PR / CI-CD branches opened by `/launch-task`, `/code`,
  or `/fix` must not include modifications under `process/{capability-id}/`. A
  `PreToolUse` hook (`process-folder-guard.py`) enforces this: Write / Edit /
  MultiEdit / NotebookEdit calls targeting any path under `process/` are
  rejected unless the `/process` skill's session sentinel
  (`/tmp/.claude-process-skill.active`) is present.
---

# Process — Tactical DDD Process Modelling

You are running an **Event-Storming-style modelling session** for one business
capability and committing the result as a durable model under
`process/{capability-id}/`. This layer is what every downstream skill (`/plan`,
`/task`, `/code`, `/fix`, `/launch-task`) reads to know what aggregates exist,
what commands they accept, what policies wire consumed events to commands, what
read-models project the domain events, and what bus topology the capability
publishes / subscribes to.

The output is **architecture-neutral** within the strategic-tech corridor:
.NET / Clean Architecture / DDD on RabbitMQ + MongoDB is assumed (per
`ADR-TECH-STRAT-001`), but the YAML deliberately does not name C# classes,
`MassTransit` consumers, or Mongo collections. That is the `implement-capability`
agent's job downstream.

> **Position in the pipeline.** `/process` runs **after** `bcm-pack` has a
> complete corpus for the capability and **before** `/plan`. The skill chain is
> now: `bcm-pack pack <CAP_ID> --deep` → **`/process <CAP_ID>`** → `/plan` →
> `/task` → `/launch-task` → `/code` → `/test-business-capability` or
> `/test-app`. `/plan` no longer derives aggregates/commands itself — it reads
> them from this folder.

---

## Authorship rule (hard constraint)

- This skill is the **only writer** of `process/{capability-id}/`. The path is
  also protected by the `process-folder-guard.py` PreToolUse hook, which
  blocks every `Write` / `Edit` / `MultiEdit` / `NotebookEdit` call targeting
  `process/**` unless the session sentinel
  `/tmp/.claude-process-skill.active` is present. The hook does **not** parse
  Bash commands, so always use `Write` / `Edit` for files under `process/` —
  never shell redirects (`cat > …`, `sed -i`, `tee`, etc.).
- All downstream skills and the agents they spawn treat `process/{capability-id}/`
  as **read-only**. Their PRs must never carry diffs under that path.
- `/process` is **idempotent and durable**: re-running it on an existing
  `process/{capability-id}/` is allowed (and expected when the FUNC ADR
  evolves), but it must always offer to diff first and ask before overwriting.

---

## Step 0 — Sentinel and Session Boundary

**Before** writing the first byte under `process/`, mark the session as a
`/process` session by touching the sentinel file:

```bash
touch /tmp/.claude-process-skill.active
```

This grants the `process-folder-guard.py` hook permission to allow `Write`,
`Edit`, `MultiEdit`, and `NotebookEdit` calls on `process/**` for the duration
of this skill invocation.

**At the very end** of the skill (success or graceful abort), remove it:

```bash
rm -f /tmp/.claude-process-skill.active
```

If you abort mid-session because of a hard error or because the user stops
you, still attempt the `rm -f` in your final message. A stale sentinel grants
write access to the next agent — that is undesirable. The hook treats sentinels
older than 30 minutes as expired, but explicit cleanup is preferred.

---

## Step 1 — Identify the Capability and Pull the Knowledge Pack

The user gives a capability ID (e.g. `CAP.BSP.001.SCO`) or a name. If
ambiguous, run `bcm-pack list --level L2` (and `--level L3` if relevant) and
ask them to pick.

Then pull the **deep** pack — process modelling needs the rationale ADRs in
addition to the structural slices:

```bash
bcm-pack pack <CAPABILITY_ID> --deep --compact > /tmp/pack-process.json
jq '.warnings'                            /tmp/pack-process.json
jq '.slices.capability_self[0]'           /tmp/pack-process.json
jq '.slices.capability_definition'        /tmp/pack-process.json
jq '.slices.emitted_business_events'      /tmp/pack-process.json
jq '.slices.emitted_resource_events'      /tmp/pack-process.json
jq '.slices.consumed_business_events'     /tmp/pack-process.json
jq '.slices.consumed_resource_events'     /tmp/pack-process.json
jq '.slices.carried_objects'              /tmp/pack-process.json
jq '.slices.carried_concepts'             /tmp/pack-process.json
jq '.slices.governing_urba'               /tmp/pack-process.json
jq '.slices.governing_tech_strat'         /tmp/pack-process.json
jq '.slices.tactical_stack'               /tmp/pack-process.json
```

Slice → process artefact mapping:

| Slice                       | Drives                                                 |
|-----------------------------|--------------------------------------------------------|
| `capability_self`           | `meta.capability`, target zone, level, owner           |
| `capability_definition`     | Aggregates, invariants, commands, policy intent — the FUNC ADR is the primary source of behaviour |
| `emitted_business_events`   | Paired EVT names on the routing keys (`bus.yaml`)      |
| `emitted_resource_events`   | RVT names emitted by aggregates (`aggregates.yaml`, `bus.yaml`) |
| `consumed_business_events`  | `policies.yaml` listens-to entries, business-subscriptions |
| `consumed_resource_events`  | `policies.yaml` resource-subscriptions, queue bindings |
| `carried_objects`           | `OBJ.*` references on aggregates (`aggregates.yaml`)   |
| `carried_concepts`          | Vocabulary grounding for command intents and errors    |
| `governing_urba`            | Naming, event meta-model, identifier conventions       |
| `governing_tech_strat`      | Bus topology rules (`bus.yaml`) — `ADR-TECH-STRAT-001` is normative |
| `tactical_stack`            | Cross-checks (idempotency / outbox / snapshotting hints) |

If `pack.warnings` is non-empty or any required slice is empty, surface the
gap to the user and stop — `/process` cannot run on an incomplete corpus. Send
them upstream to `banking-knowledge` to fix the BCM/FUNC ADR before retrying.

---

## Step 2 — Detect Existing Process Folder (idempotency)

```bash
ls process/<CAPABILITY_ID>/ 2>/dev/null
```

| State                                       | Action                                                                                          |
|---------------------------------------------|-------------------------------------------------------------------------------------------------|
| Folder absent                               | Greenfield modelling.                                                                           |
| Folder present, FUNC ADR unchanged          | Ask the user: "A process model exists. Do you want to refine it, regenerate, or stop?"          |
| Folder present, FUNC ADR has new events     | Run a *delta* session — keep stable AGG/CMD/POL identifiers, append new commands / events / policies. Never silently rename existing IDs (downstream code is keyed on them). |

Always show a `git diff` of any change before writing the final files, so the
user can sanity-check the delta.

---

## Step 3 — Run the Modelling Session

A capability process model is built from six interlocking views. Walk the user
through them in this order, surfacing one decision at a time and writing
nothing until each view is validated.

### 3.1 Aggregates (`aggregates.yaml`)

Start with the question: *"What pieces of state need their own consistency
boundary? Which business object does each protect?"*

For each aggregate, capture:

- `id`: `AGG.<ZONE>.<L1>.<L2>.<NAME>` (kebab-screamcase)
- `name`: human-readable
- `business_object`: `OBJ.*` reference (must exist in the `carried_objects` slice)
- `aggregate_id_field` and cardinality
- `state` fields with their kind (`identity`, `snapshot`, `idempotency`,
  `configuration`, `read-through`)
- `accepted_commands` — forward-references commands defined in 3.2
- `emitted_resource_events` — must each appear in `emitted_resource_events`
  from `bcm-pack` (or be flagged as an Open Question)
- `invariants` — business rules enforced atomically inside the aggregate.
  Each invariant has an `id` (`INV.<L2>.NNN`), a `rule`, a `rationale`
  (cite the FUNC/URBA/TECH-STRAT ADR), and optionally an `open_question`.
- `consistency_boundary`, `transactional_outbox`, `snapshotting`

Key questions to resolve at this view:

- **Granularity.** One aggregate per `<entity_id>`? Per `(<entity_id>,
  <variant>)`? Justify and record the alternative as an open question.
- **Atomicity of conditional events.** When a command may emit a primary
  event *and* a conditional secondary one (e.g. threshold crossing), is it
  atomic in the aggregate or delegated to a downstream observer? This
  decision belongs to the aggregate invariants, not to the command.
- **Idempotency.** What replay key does each command use? Is the window
  bounded (e.g. `30d`) or lifetime (e.g. one-shot baseline)?

### 3.2 Commands (`commands.yaml`)

For each verb the capability accepts:

- `id`: `CMD.<ZONE>.<L1>.<L2>.<VERB>`
- `name`, `intent` (one-paragraph business statement)
- `accepted_by`: exactly one `AGG.*`
- `issued_by`: list of `POL.*` (defined in 3.3) + optionally an HTTP/API caller
- `payload_schema`: relative path under `schemas/`
- `preconditions`: numbered `PRE.NNN`
- `invariants_enforced`: cross-references the `INV.*` from 3.1
- `emits`: `RVT.*` (and optionally a comment naming the paired `EVT.*`
  business-event family — per `ADR-TECH-STRAT-001` Rule 2, only resource
  events are autonomous bus messages; business events appear only in routing
  keys per Rule 4)
- `errors`: `code` + `when`
- `idempotency`: `key` + `window`
- `api_binding`: `{method, path}` — feeds `api.yaml`

### 3.3 Policies (`policies.yaml`)

A policy listens to one or more (resource) events and issues a command.
Aggregates never subscribe to events directly.

For each policy:

- `id`: `POL.<ZONE>.<L1>.<L2>.<NAME>`
- `name`, `intent`
- `listens_to` — for each entry: `resource_event`, `business_subscription`,
  `resource_subscription`, optional `trigger_kind`
- `issues` — exactly one `CMD.*`
- `mapping_rule` — how the upstream payload becomes the command payload
- `error_handling` — per error code from the issued command:
  `ack-and-drop`, `retry`, `dlq`, with rationale
- `delivery` — `at-least-once` (default) or `exactly-once` (rare; justify)

If a policy currently has no upstream event because the upstream FUNC ADR
isn't ready, set `status: placeholder` and add an `open_question` describing
the missing upstream signal.

### 3.4 Read-models and queries (`read-models.yaml`)

For each projection:

- `id`: `PRJ.<ZONE>.<L1>.<L2>.<NAME>`
- `backs_resource` (optional; the `RES.*` it projects)
- `fed_by` — list of `RVT.*`
- `fields` — denormalised columns
- `consistency` — `eventual` (default) or `strong` (justify)
- `retention` — for history-style projections

Then declare the queries on top:

- `id`: `QRY.<ZONE>.<L1>.<L2>.<NAME>`
- `served_by` — exactly one `PRJ.*`
- `request` and `response` shape
- `consumers` — list of capability IDs (cross-check with the BCM
  `business-subscription` chain)
- `api_binding` and optional `cache: { etag, max_age }`

### 3.5 Bus topology (`bus.yaml`)

Apply `ADR-TECH-STRAT-001` rigorously — this view is normative:

- `publication`:
  - `broker: rabbitmq`
  - `exchange.name`: `<zone>.<l1>.<l2>-events` (lowercase, dot-separated, per
    Rule 1 / 5)
  - `exchange.type: topic`, `durable: true`, `owned_by: <CAPABILITY_ID>`
- `routing_keys` — one per emitted `RVT.*`. The routing key MUST be
  `<EVT-id>.<RVT-id>` (Rule 4). Only `RVT.*` are autonomous messages — never
  declare a standalone `EVT.*` message (Rule 2).
- `correlation_key` — typically the aggregate's identity field
- `identity_resolution` — explicit: do we ship the canonical referential ID,
  or do consumers resolve via a lookup?
- `subscriptions` — for every entry from `consumed_business_events` /
  `consumed_resource_events`: `source_capability`, `source_exchange`,
  `binding_pattern` (`<EVT>.<RVT>` form), declared `queue` name (must be
  prefixed with the consuming capability's exchange root: e.g.
  `<l1>.<l2>.q.<topic>`), and the consuming `POL.*`
- `consumers` — known downstream capabilities, with binding pattern and
  rationale (sourced from BCM `business-subscription` chain)

### 3.6 API surface (`api.yaml`) — derived

Synthesise from the `api_binding` fields declared in 3.2 and 3.4. This file
is **derived** but committed (so the `create-bff` and `implement-capability`
agents can consume one file instead of cross-walking two). Add a `meta.derivation`
note pointing at `commands.yaml` + `read-models.yaml`.

For each command: `operation_id`, `method`, `path`, `issues`, `request_schema`,
`responses` (with mapped error codes).
For each query: `operation_id`, `method`, `path`, `serves`, optional
`query_params`, `responses`.

### 3.7 JSON Schemas (`schemas/`)

For every command and event referenced in `commands.yaml` or `bus.yaml`, write
a JSON Schema:

- `schemas/CMD.<…>.<VERB>.schema.json` — command request payload
- `schemas/RVT.<…>.<RESOURCE_EVENT>.schema.json` — resource-event payload

Use Draft 2020-12 (`"$schema": "https://json-schema.org/draft/2020-12/schema"`).
Each schema has a stable `$id` derived from the identifier, `additionalProperties: false`
on object types, and a `description` referencing the originating CMD or RVT.

Reuse common shapes (e.g. `case_id`, `event_id`, `timestamp`, `model_version`)
via local `$defs` rather than duplicating them across files.

---

## Step 4 — Write the README

`process/<CAPABILITY_ID>/README.md` is the human entry point. It contains:

1. **One-paragraph framing** — what this folder *is* (Process Modelling layer)
   and what it is *not* (a plan, a milestone breakdown, an implementation).
2. **Upstream knowledge consumed** — list the `bcm-pack` slices that are
   canonical (BCM YAML, FUNC ADR, URBA, TECH-STRAT) so a reader knows where to
   look for the data this folder doesn't restate.
3. **Files in this folder** — one-line summary per `*.yaml` (mirror the table
   in this skill).
4. **Scenario walkthrough** — at least two end-to-end flows expressed as ASCII
   diagrams that walk an *event* → *policy* → *command* → *aggregate* → *event*
   chain. This is the part that lets a reviewer understand the model in two
   minutes without reading every YAML.
5. **Open process-level questions** — every decision flagged
   `open_question` in the YAMLs is repeated here, with the alternatives and
   the trade-off. These must be resolved (or accepted as known limitations)
   before `/code` runs.
6. **Governance** — the ADRs that govern the model (FUNC, URBA, TECH-STRAT)
   with one line each on their role.

Use the existing `process/CAP.BSP.001.SCO/README.md` as the canonical example
of tone, depth, and structure.

---

## Step 5 — Validate Coherence Before Writing

Before committing files, mentally check (and announce to the user) the
following invariants. If any fail, fix the model — do not just write it.

1. **Closure of references.** Every `accepted_commands` entry on an aggregate
   exists in `commands.yaml`; every `issues` in a policy exists in
   `commands.yaml`; every `served_by` in a query exists in `read-models.yaml`;
   every `RVT.*` in `bus.yaml` is `emitted_resource_events` of exactly one
   aggregate.
2. **BCM closure.** Every `RVT.*` in `bus.yaml.routing_keys` appears in the
   `emitted_resource_events` slice of `bcm-pack`. Every consumed
   `binding_pattern` corresponds to an entry in `consumed_resource_events`.
   Mismatches mean either the BCM is incomplete (stop, send upstream) or the
   process model invented an event (forbidden).
3. **Single-aggregate-per-command.** No `CMD.*` is `accepted_by` more than
   one aggregate.
4. **Routing-key form.** Every routing key matches `<EVT-id>.<RVT-id>`
   (Rule 4 of `ADR-TECH-STRAT-001`).
5. **Schema coverage.** Every `CMD.*.payload_schema` and every
   `bus.yaml.routing_keys[*].schema` resolves to an actual file under
   `schemas/`.
6. **No bare `EVT.*` messages.** No standalone `EVT.*` autonomous bus message
   anywhere (Rule 2 of `ADR-TECH-STRAT-001`).

Announce: "Coherence checks ✅ — writing files." Then proceed.

---

## Step 6 — Write the Files

Write to `process/<CAPABILITY_ID>/`:

- `README.md`
- `aggregates.yaml`
- `commands.yaml`
- `policies.yaml`
- `read-models.yaml`
- `bus.yaml`
- `api.yaml`
- `schemas/CMD.*.schema.json` (one per command)
- `schemas/RVT.*.schema.json` (one per emitted resource event)

Always use the `Write` and `Edit` tools — never shell redirects. The
`process-folder-guard.py` hook will allow these calls because the sentinel
from Step 0 is in place.

After every write, run `git diff` on the touched file and show the user the
diff before moving on. This makes the modelling session reviewable in real
time.

---

## Step 7 — Tear Down the Sentinel

```bash
rm -f /tmp/.claude-process-skill.active
```

Then announce:

> "Process model for `<CAPABILITY_ID>` is committed under
> `process/<CAPABILITY_ID>/`. The folder is now read-only for every other
> skill — `/plan`, `/task`, `/code`, `/fix`, `/launch-task`, `/continue-work`
> — and all their downstream agents. To refine the model, re-run `/process
> <CAPABILITY_ID>`.
>
> Next: `/plan <CAPABILITY_ID>` will read this folder (in addition to
> `bcm-pack pack`) to draft the implementation epics."

If the user wants to **commit** the changes, they can use `/commit` (this skill
does not auto-commit — Process Modelling is high-stakes and benefits from a
manual review pass on the diff before committing).

---

## Important Boundaries

- **No code, no test files, no implementation choices.** This skill stays at
  the tactical-DDD modelling layer. Class names, namespaces, MongoDB
  collections, MassTransit consumers, JSON-on-wire envelopes — those belong
  to the `implement-capability` and `create-bff` agents. The `*.schema.json`
  files in `schemas/` describe wire contracts, not implementation classes.
- **No new ADRs.** If the modelling session uncovers a decision that is
  bigger than the capability (a new naming convention, a new bus rule, a new
  zoning rule), stop and tell the user to author an ADR upstream in
  `banking-knowledge` first. Do not write the decision into a YAML and hope.
- **Never rename a stable identifier.** AGG / CMD / POL / PRJ / QRY ids are
  contracts. Once committed and consumed by `/plan`, `/task`, or `/code`,
  they cannot be renamed without a coordinated change across consumers. If a
  rename is unavoidable, treat it as a deprecation: add the new id, mark the
  old one `deprecated: true` with a `replaced_by`, and surface the migration
  in the README.
- **Sentinel discipline.** Always remove `/tmp/.claude-process-skill.active`
  on exit, even on aborts. The hook treats sentinels older than 30 minutes as
  expired, but explicit cleanup is the right hygiene.
