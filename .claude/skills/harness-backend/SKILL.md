---
name: harness-backend
description: >
  Entry-point that adds (or refreshes) the **contract harness** of a backend
  microservice produced by the `implement-capability` agent. Resolves the
  capability, the active branch / worktree, locates the .NET solution under
  `sources/{capability-name}/backend/`, then spawns the `harness-backend`
  agent (a senior contract / API engineer) to scaffold a
  `*.Contracts.Harness/` project, generate `openapi.yaml` (OpenAPI 3.1) and
  `asyncapi.yaml` (AsyncAPI 2.6) under `contracts/specs/`, and validate
  strict alignment between the specs, the Process Modelling layer
  (`process/{capability-id}/`: `commands.yaml`, `read-models.yaml`,
  `bus.yaml`, `api.yaml`, `schemas/*.schema.json`), and the BCM corpus
  consumed via `bcm-pack pack <CAP_ID> --deep` (resources, resource events,
  business events, business / resource subscriptions, carried objects, FUNC
  / URBA / TECH-STRAT ADRs).

  Both generated specs carry a top-level `x-lineage` block (capability +
  bcm + process + generated metadata) plus per-operation, per-message, and
  per-channel `x-lineage` extensions. Lineage is bidirectional — every
  operation traces back to a `process/` source AND a `bcm-pack` source —
  so reviewers, consumers, observability tooling, and data-catalogue
  ingestion can resolve any spec entry to its definitional origin.

  The skill targets **non-CHANNEL zones only** (BUSINESS_SERVICE_PRODUCTION,
  SUPPORT, REFERENTIAL, EXCHANGE_B2B, DATA_ANALYTIQUE, STEERING). For
  CHANNEL-zone tasks (BFF + frontend), the BFF contract is already
  enforced by `create-bff`; a future `harness-bff` skill would extend the
  same lineage pattern there.

  Supports `--branch <slug>` or `--env <slug>` to operate in a specific
  worktree. Supports `--gen` (default — regenerate specs and validate) and
  `--validate` (no regeneration; only assert that the committed specs are
  in sync with `/process/{cap}/`, bcm-pack, and the running controller /
  consumer surface).

  Trigger this skill whenever the user says: "harness-backend", "harness for
  CAP.*", "regenerate the contracts for X", "regenerate openapi for X",
  "regenerate asyncapi for X", "refresh the api spec", "validate the
  contract harness", "lineage drift on X", "process changed — refresh the
  spec", or any phrasing requesting the contract surface of a backend
  microservice be re-derived or validated. Also trigger proactively after
  `implement-capability` finishes (Path A) — both `/code` (Step 2.5) and
  `/fix` (Step 3.5) invoke this skill automatically — and after `/process
  <CAP_ID>` evolves the model so the spec needs to follow.
---

# Harness-backend — Contract Harness Entry-Point

You are the entry-point that ensures a backend microservice produced by the
`implement-capability` agent has a fresh, lineage-rich, strictly-aligned
contract surface (OpenAPI 3.1 + AsyncAPI 2.6). You do not generate the
specs yourself — you resolve the context and dispatch the
`harness-backend` agent.

> **Hard rule — `process/{capability-id}/` is read-only.** This skill, and
> the agent it spawns, **read** `process/{capability-id}/` but **never
> write** to it. The PreToolUse hook `process-folder-guard.py` enforces
> this. If the model is wrong, stop and tell the user to run `/process
> <CAPABILITY_ID>` to amend it, then re-run this skill.

---

## Step 0 — Resolve the Input

The user gives a capability ID, a TASK, a branch, or none. Resolve in this
order, using the shape `/code` and `/test-business-capability` already
follow:

| Input form           | Example                               | What to extract                                                                                  |
|----------------------|---------------------------------------|--------------------------------------------------------------------------------------------------|
| Capability ID        | `/harness-backend CAP.BSP.001.SCO`    | use the ID directly; resolve worktree from current branch (or `--branch`) |
| Task ID              | `/harness-backend TASK-003`           | read TASK frontmatter to get capability_id; resolve worktree from `feat/TASK-003-*` |
| Branch slug          | `/harness-backend --branch feat/TASK-003-bsp-sco` | derive TASK-003 → capability_id from the TASK file in that worktree |
| No argument          | `/harness-backend` after `/code`     | read the current working branch / worktree, locate the active TASK |

End Step 0 with these resolved values:

1. **`CAPABILITY_ID`** (e.g. `CAP.BSP.001.SCO`).
2. **`CAPABILITY_NAME`** (kebab — derived from `bcm-pack pack <CAP_ID>
   --compact | jq -r '.slices.capability_self[0].name'`).
3. **`WORKTREE_ROOT`** — the directory housing the .NET solution (either
   the main repo root, or `/tmp/kanban-worktrees/TASK-NNN-*/` when
   `--branch` is specified).
4. **`BACKEND_DIR`** — `${WORKTREE_ROOT}/sources/${CAPABILITY_NAME}/backend/`.
5. **`MODE`** — `gen` (default) or `validate` (from `--validate`).

---

## Step 1 — Verify Prerequisites (mandatory)

```bash
# 1. /process layer must exist for this capability
ls process/${CAPABILITY_ID}/{commands.yaml,bus.yaml,api.yaml,read-models.yaml}
ls process/${CAPABILITY_ID}/schemas/

# 2. The microservice must already be scaffolded by implement-capability
ls "${BACKEND_DIR}/"*.sln
ls "${BACKEND_DIR}/src/"*.Presentation/Program.cs

# 3. The capability must be non-CHANNEL
bcm-pack pack ${CAPABILITY_ID} --compact > /tmp/pack-harness.json
ZONE=$(jq -r '.slices.capability_self[0].zoning' /tmp/pack-harness.json)
case "$ZONE" in
  CHANNEL) echo "❌ harness-backend does not handle CHANNEL — use create-bff instead"; exit 1 ;;
  BUSINESS_SERVICE_PRODUCTION|SUPPORT|REFERENTIAL|EXCHANGE_B2B|DATA_ANALYTIQUE|STEERING) ;;
  *) echo "❌ unknown zone $ZONE"; exit 1 ;;
esac

# 4. bcm-pack returns no warnings and the required slices are non-empty
jq '{
  warnings,
  emitted_resource_events: (.slices.emitted_resource_events | length),
  consumed_resource_events: (.slices.consumed_resource_events | length),
  carried_objects:          (.slices.carried_objects        | length),
  emitted_business_events:  (.slices.emitted_business_events | length),
}' /tmp/pack-harness.json
```

If any prerequisite fails, stop and explain the gap clearly:

| Failure                                       | Resolution                                                        |
|-----------------------------------------------|-------------------------------------------------------------------|
| `process/{cap}/` missing                      | run `/process <CAPABILITY_ID>` first                              |
| `.sln` missing                                | run `/code TASK-NNN` first (Path A scaffolds the microservice)    |
| Zone is CHANNEL                               | this skill is non-CHANNEL only — no action                        |
| `pack.warnings` non-empty / required slice empty | fix the upstream BCM in `banking-knowledge` (out of scope here) |

---

## Step 2 — Diff the Process Model Against the Last Harness Run (idempotency)

If `${BACKEND_DIR}/contracts/specs/openapi.yaml` already exists, compare its
top-level `x-lineage.process.version` with the current
`process/{cap}/commands.yaml#meta.version`:

- **Same version + `--validate` mode** → run the harness validator only,
  expect drift = 0.
- **Same version + default mode** → still re-run `gen` to refresh `generated.at`
  (cheap, idempotent). The diff should be limited to that timestamp.
- **Different version** → process model evolved since the last harness run.
  Tell the user: "Process model is at `vX.Y.Z`, last harness was at `vA.B.C`.
  Will regenerate." Proceed to Step 3.

If `--validate` is set and the version differs, **do not generate** — exit
with a clear error pointing the user at the default mode.

---

## Step 3 — Spawn the `harness-backend` Agent

Use the `Agent` tool. The agent is the senior engineer that owns the
contract harness. Pass the full resolved context as a self-contained
prompt:

```
Agent({
  subagent_type: "harness-backend",
  description: "Contract harness for ${CAPABILITY_NAME}",
  prompt: """
   Mode: ${MODE}        # gen | validate
   Capability ID:   ${CAPABILITY_ID}
   Capability Name: ${CAPABILITY_NAME}
   Worktree root:   ${WORKTREE_ROOT}
   Backend dir:     ${BACKEND_DIR}

   Inputs you must read (read-only):
     - process/${CAPABILITY_ID}/{README.md,aggregates.yaml,commands.yaml,
                                  policies.yaml,read-models.yaml,bus.yaml,
                                  api.yaml,schemas/*.schema.json}
     - bcm-pack pack ${CAPABILITY_ID} --deep --compact

   Existing solution under ${BACKEND_DIR}:
     - ${Namespace}.${CapabilityName}.sln
     - src/${Namespace}.${CapabilityName}.{Domain,Application,Infrastructure,
                                            Presentation,Contracts}/

   Outputs you must produce (write):
     - src/${Namespace}.${CapabilityName}.Contracts.Harness/   (new project)
     - contracts/specs/openapi.yaml                            (OpenAPI 3.1 + x-lineage)
     - contracts/specs/asyncapi.yaml                           (AsyncAPI 2.6 + x-lineage)
     - contracts/specs/lineage.json                            (top-level lineage block)
     - contracts/specs/harness-report.md                       (validation verdict)

   Solution wiring:
     - dotnet sln add src/${Namespace}.${CapabilityName}.Contracts.Harness
     - Edit Presentation Program.cs to mount /openapi.yaml, /asyncapi.yaml,
       /contracts/lineage endpoints (do not rewrite the file).
     - Edit Presentation .csproj to copy contracts/specs/* into bin output.
     - Add an MSBuild target on the Presentation project that invokes the
       harness `validate` command BeforeTargets="Build", failing the build
       on drift.

   Hard rules:
     - process/${CAPABILITY_ID}/ is READ-ONLY. The PreToolUse hook
       process-folder-guard.py blocks Write/Edit on process/**.
     - Lineage closure (process AND bcm) is non-negotiable: every operation
       in openapi.yaml AND every channel/message in asyncapi.yaml carries
       an x-lineage block resolving to a process source + a bcm-pack source.
     - Spec ↔ runtime alignment: every controller action / consumer must
       map to an OpenAPI / AsyncAPI operation, and vice versa.
     - Strict TECH-STRAT-001 conformance: routing keys are <EVT.…>.<RVT.…>,
       only RVT.* are autonomous bus messages, exchange-per-L2.

   Failure handling:
     - If a closure check fails, return a structured failure report listing
       the gap (dangling process_source, missing controller, BCM warning).
       Do not auto-fix the microservice — that's implement-capability's
       remediation loop.
     - If process_folder_guard rejects a write, you targeted process/ by
       mistake. Stop and report.

   Final output:
     - contracts/specs/{openapi.yaml,asyncapi.yaml,lineage.json,harness-report.md}
     - Tell the caller (this skill) the per-source coverage counts and the
       drift verdict.
  """
})
```

---

## Step 4 — Report to the User

Once the agent completes, summarise its report:

> "Contract harness for `<CAPABILITY_ID>` is in `<BACKEND_DIR>/contracts/specs/`:
> - `openapi.yaml` (OpenAPI 3.1) — N commands + M queries — full lineage ✅
> - `asyncapi.yaml` (AsyncAPI 2.6) — P publish + Q subscribe — full lineage ✅
> - `lineage.json` — top-level lineage block (capability + bcm + process)
> - `harness-report.md` — closure verdict
>
> Process closure: ✅ N/N items covered.
> BCM closure:     ✅ N/N items covered.
> Runtime alignment: ✅ N/N controllers + consumers reconciled.
> Drift vs committed: 0 lines.
>
> The running service serves its own specs at:
>   GET http://localhost:{LOCAL_PORT}/openapi.yaml
>   GET http://localhost:{LOCAL_PORT}/asyncapi.yaml
>   GET http://localhost:{LOCAL_PORT}/contracts/lineage"

If the agent returned a failure report, surface the gap exactly as it came
back, and offer the right remediation:

| Gap reported                                 | Remediation                                          |
|----------------------------------------------|------------------------------------------------------|
| Dangling `x-lineage.process.*` reference     | re-run `/process <CAPABILITY_ID>` to amend the model |
| Dangling `x-lineage.bcm.*` reference         | fix BCM upstream in `banking-knowledge`              |
| Missing controller for an OpenAPI path       | re-run `/code TASK-NNN` — implement-capability missed an action |
| Missing consumer for an AsyncAPI subscribe   | re-run `/code TASK-NNN` — bus subscription not wired |
| Drift between generated and committed specs  | run `/harness-backend <CAPABILITY_ID>` (default mode) and commit the diff |

---

## Operational Notes

- **Idempotent.** Re-running the skill with no process / bcm changes
  produces identical specs (modulo the `generated.at` timestamp).
- **Cheap to run.** The harness only reads files and shells out to
  `bcm-pack`; it does not bring up MongoDB / RabbitMQ. Safe to call
  inside a build hook.
- **Branch-aware.** When invoked with `--branch <slug>`, the skill resolves
  artifacts from `/tmp/kanban-worktrees/TASK-NNN-{slug}/` so an in-flight
  PR's harness can be regenerated without checking out the branch in the
  main worktree.
- **CI-friendly.** In CI, run with `--validate`. The harness exits non-zero
  if any closure / runtime / drift check fails — the PR pipeline fails
  fast on contract regressions.
- **Composition.** `/code` (Path A) calls this skill automatically as the
  step right after `implement-capability` succeeds, so a fresh microservice
  is always shipped with its harness. Path C (contract-stub) also calls
  this skill since the stub publishes events whose payloads are wire
  contracts.
