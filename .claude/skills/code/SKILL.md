---
name: code
description: >
  Triggers the implementation of a specific task by reading its task file and invoking the 
  right implementation skill(s) based on the capability zone, then validates the result 
  with the matching test skill (test-business-capability for backend, test-app for 
  frontend+BFF). Use this skill whenever the user wants to implement a 
  task, code a specific capability task, start development on a TASK-NNN, or execute an 
  implementation work item. Trigger on: "code TASK-NNN", "implement TASK-NNN", 
  "code this task", "start implementing", "build [capability]", or any time a task file 
  exists in /tasks/{capability}/ with status "todo" and all dependencies are resolved. 
  Also trigger proactively when the user says "let's code" or "start development" and a 
  specific task or capability is named.
---

# Code Skill

You are the bridge between the planning world and the implementation world. Your job is to
read a task file, understand what it asks for in business terms, detect the capability zone,
invoke the right implementation skill(s), then validate the result with the test skill —
repeating until the Definition of Done is fully satisfied.

---

## Hard rule — `process/{capability-id}/` is read-only

The `process/{capability-id}/` folder (aggregates, commands, policies, read-models,
bus topology, JSON Schemas) is the **contract** that the implementation must
satisfy. This skill, and every agent it spawns (`implement-capability`,
`create-bff`, `code-web-frontend`), reads from it but **never writes to it**.

A PreToolUse hook (`process-folder-guard.py`) enforces this in **both** the main
checkout and any `/tmp/kanban-worktrees/TASK-NNN-*/` worktree spawned by
`/launch-task`: Write/Edit/MultiEdit/NotebookEdit under `process/**` outside the
`/process` skill is rejected. As a result, **PR branches opened by `/code` (and
the CI/CD pipelines that run on them) must not contain any diff under
`process/{capability-id}/`**. If a remediation iteration suggests changing a
command shape, an aggregate invariant, or a routing key, stop the loop and tell
the user to run `/process <CAPABILITY_ID>` to update the model — then re-run
`/code TASK-NNN`.

When forwarding context to `implement-capability`, `create-bff`, or
`code-web-frontend`, instruct each agent to **read** the relevant
`process/{capability-id}/*.yaml` files (and the `schemas/*.schema.json` files)
as the source of truth on aggregates, commands, events, and routing keys —
never to invent or reshape them.

---

## Readiness gate — process model must be merged on `main`

Before reading the task, before spawning any agent, verify that the
capability's process model is on `main` and that no `process/<CAP_ID>` PR
is still open:

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel)
CAP_ID="<CAPABILITY_ID-of-the-task>"

# 1. Folder must exist on main.
git -C "$PROJECT_ROOT" ls-tree --name-only main -- "process/$CAP_ID" \
    > /tmp/process-main-check.txt
if [ ! -s /tmp/process-main-check.txt ]; then
  echo "GATE-FAIL: process/$CAP_ID/ is not on main."
  echo "Cannot run /code for this task — run /process $CAP_ID and merge the PR first."
  exit 1
fi

# 2. No open PR for the process branch.
OPEN_COUNT=$(gh pr list --head "process/$CAP_ID" --state open --json number --jq 'length' 2>/dev/null || echo 0)
if [ "$OPEN_COUNT" != "0" ]; then
  PR_URL=$(gh pr list --head "process/$CAP_ID" --state open --json url --jq '.[0].url')
  echo "GATE-FAIL: open process PR ($PR_URL) is pending review for $CAP_ID."
  echo "Cannot run /code until the process PR is merged into main."
  exit 1
fi
```

If either check fails, **stop and surface the failure** — do not spawn any
implementation agent. Once the PR is merged, re-run `/code TASK-NNN`.

---

## Before You Begin

> **Note:** For orchestrated multi-task workflows (board view, prioritization, dependency
> tracking), use the `/launch-task` skill instead — it calls this skill at the right moment.

1. **Identify the task.** The user should specify a task ID (e.g., `TASK-001`) or a capability
   name. If ambiguous, redirect to `/launch-task` to get the prioritized list.

2. **Read the task file.** Find it at `/tasks/{capability-id}/TASK-NNN-*.md`.

3. **Verify prerequisites:**
   - Status is `todo` or `in_progress` (not `in_review`, `done`, or `stalled`)
   - If status is `stalled`: stop and tell the user to run `/continue-work TASK-NNN` first.
   - All tasks in `depends_on` have status `done`
   - No open questions in the task file are unresolved

   If any prerequisite fails, stop and explain:
   > "TASK-NNN cannot start because [reason]. Resolve this first."

4. **Read supporting context.** All BCM/ADR/vision knowledge comes from the `bcm-pack` 
   CLI — never read `/bcm/`, `/func-adr/`, `/adr/`, `/strategic-vision/`, or `/product-vision/`
   directly:

   ```bash
   bcm-pack pack <CAPABILITY_ID> --compact > /tmp/pack-code.json
   ```

   Selective slice usage at this layer (this skill is mostly a router — keep it light):

   | Slice                       | Used by /code itself                          |
   |-----------------------------|-----------------------------------------------|
   | `capability_self`           | zone detection, capability_name, level        |
   | `capability_definition`     | summarized to the user in Step 1, forwarded to the spawned agent |
   | `emitted_business_events`   | "events that will become emittable" in Step 1 |
   | `consumed_business_events`  | "events consumed (BFF subscriptions)" in Step 1 (CHANNEL only) |

   The deeper slices (tactical_stack, governing_*, vision narratives) are forwarded to the
   spawned agent via the prompt — that agent re-fetches them with `--deep` if it needs the
   narratives.

   Local artifacts (always read directly):
   - the roadmap file at `/roadmap/{capability-id}/roadmap.md`
   - the Process Modelling layer at `process/{capability-id}/` (read-only) —
     `aggregates.yaml`, `commands.yaml`, `policies.yaml`, `read-models.yaml`,
     `bus.yaml`, `api.yaml`, `schemas/*.schema.json`. The implementation agents
     consume these files; they are forbidden from modifying them.

5. **Read loop counters** from the task file frontmatter:
   - `loop_count`: number of remediation iterations already used (default `0` if absent)
   - `max_loops`: maximum allowed iterations (default `10` if absent)

   If the task file does not yet have these fields, treat them as `loop_count: 0` /
   `max_loops: 10` and write them to the frontmatter before proceeding:
   ```yaml
   loop_count: 0
   max_loops: 10
   ```

6. **Detect the routing path.** Two signals are inspected, in order:

   **6a — `task_type` frontmatter (highest priority)**

   Read the `task_type` field from the TASK frontmatter. If set to
   `contract-stub`, take **Path C** regardless of zone:

   | `task_type` value | Routing path | Notes |
   |-------------------|--------------|-------|
   | `contract-stub`   | **Path C — Contract+Stub** | spawns `implement-capability` in **Mode B** (JSON Schemas + minimal RabbitMQ-publishing stub). See agent doc for the Mode A vs Mode B branching. |
   | (absent) or `full-microservice` | Fall through to 6b | standard zone-aware routing |

   **6b — Zone (when `task_type` does not force Path C)**

   Detect the zone from the pack's `slices.capability_self[0].zoning` (or fall back to 
   `slices.capability_definition[0].decision_scope.zoning` from the FUNC ADR if absent).
   Never read `bcm/capabilities-*.yaml` directly. Map the value as follows:

   | YAML `zoning` value          | Zone family       | Implementation path |
   |------------------------------|-------------------|---------------------|
   | `BUSINESS_SERVICE_PRODUCTION`| Core domain       | **Path A** — `implement-capability` (Mode A — full microservice) |
   | `SUPPORT`                    | Transverse IT     | Path A — `implement-capability` (Mode A) |
   | `REFERENTIAL`                | Master data       | Path A — `implement-capability` (Mode A) |
   | `EXCHANGE_B2B`               | Ecosystem B2B     | Path A — `implement-capability` (Mode A) |
   | `DATA_ANALYTIQUE`            | Data / BI / AI    | Path A — `implement-capability` (Mode A) |
   | `STEERING`                   | Pilotage          | Path A — `implement-capability` (Mode A) |
   | `CHANNEL`                    | Omnichannel       | **Path B** — `create-bff` + `code-web-frontend` (parallel) |

   **Summary** — three routing paths:
   - **Path C** (Contract+Stub) — triggered by `task_type: contract-stub`, any zone
   - **Path A** (Full microservice) — non-CHANNEL zone, `task_type` unset / `full-microservice`
   - **Path B** (BFF + Frontend) — CHANNEL zone, `task_type` unset / `full-microservice`

---

## Step 0 — Create Isolation Branch

Before writing any code, create a dedicated branch and verify the git state:

```bash
# Ensure we are on main and the tree is clean
git status --porcelain
git checkout main 2>/dev/null || git checkout master 2>/dev/null

# Derive the branch name from the task ID and title (kebab-case)
TASK_ID="TASK-NNN"                          # e.g. TASK-003
TASK_SLUG="<title-in-kebab-case>"           # e.g. beneficiary-dashboard
BRANCH_NAME="feat/${TASK_ID}-${TASK_SLUG}"  # e.g. feat/TASK-003-beneficiary-dashboard

git checkout -b "$BRANCH_NAME"
```

Report to the user:
> "Working on branch `feat/TASK-NNN-{slug}`. All changes will be isolated here until the PR is opened."

If the repository has no commits yet (`git log` fails), skip the `git checkout main` step and
simply run `git checkout -b "$BRANCH_NAME"` from the initial state.

---

## Step 1 — Summarize What Will Be Built

Before invoking any implementation skill, present a clear summary to the user.

**For non-CHANNEL zones:**

```
Ready to implement TASK-[NNN]: [Title]

Capability: [Name] ([ID]) — [Zone]
Epic: [Epic N — Name]

What will be built:
[2-3 sentences from the task's "What to Build" section, in plain language]

Business events that will become emittable:
- [EventName]
- [EventName]

Definition of Done:
- [ ] [condition 1]
- [ ] [condition 2]

Implementation path: implement-capability (.NET microservice)

Shall I proceed?
```

**For CHANNEL zone:**

```
Ready to implement TASK-[NNN]: [Title]

Capability: [Name] ([ID]) — CHANNEL zone
Epic: [Epic N — Name]

What will be built:
[2-3 sentences from the task's "What to Build" section, in plain language]

Events consumed (BFF subscriptions):
- [EventName] from [EmittingCapabilityId]

Events produced:
- [EventName]

Definition of Done:
- [ ] [condition 1]
- [ ] [condition 2]

Implementation path: create-bff + code-web-frontend (launched in parallel)
After implementation: test-app will validate all DoD criteria.

Shall I proceed?
```

Wait for the user's confirmation before proceeding.

---

## Step 2 — Invoke the Implementation Component(s)

### Path C — Contract+Stub (`task_type: contract-stub`, any zone)

Spawn the `implement-capability` agent in **Mode B** via the `Agent` tool.
The agent itself reads the `task_type` from the TASK file and switches to
Mode B accordingly — your job here is just to feed it the right context.

The context to pass includes:

- The capability ID, name, zone, and level
- An explicit mention that `task_type: contract-stub` is set (so the agent
  knows which mode to take, even before reading the file)
- The governing FUNC ADR(s)
- The events to contract (the EVT/RVT pairs named in the task)
- The carried business objects / resources
- `ADR-TECH-STRAT-001` content (or pointer + summary) — the agent needs the
  bus topology rules to scaffold the stub correctly
- The DoD with its versioning encoding, cadence range, and validation site
  conventions

Use:
```
Agent({
  subagent_type: "implement-capability",
  description: "Contract+stub for [capability name]",
  prompt: <full context block including the task_type signal,
           BCM YAML excerpts for the events to contract,
           ADR-TECH-STRAT-001 rules, DoD>
})
```

Say:
> "Spawning implement-capability agent in Mode B (contract+stub) for [capability name] with task TASK-[NNN]..."

The agent produces:
- A minimal .NET worker stub under `sources/{capability-name}/stub/`
- The wire-format JSON Schemas it publishes are NOT regenerated — the agent
  reads them directly from `process/{capability-id}/schemas/RVT.*.schema.json`
  (already authored by `/process`). No schema files are written outside `process/`.
- No full microservice scaffold (Domain / Application / Infrastructure / Presentation / Contracts projects), no MongoDB, no REST API

The agent may push back if the BCM does not declare any business or
resource event for the target capability, if `ADR-TECH-STRAT-001` is
missing, or if the FUNC ADR contradicts the task. Surface that to the
user as the gap to resolve.

---

### Path A — Non-CHANNEL zones (BUSINESS_SERVICE_PRODUCTION, SUPPORT, REFERENTIAL, EXCHANGE_B2B, DATA_ANALYTIQUE, STEERING)

> Use this path **only** when `task_type` is absent or `full-microservice`.
> If `task_type: contract-stub`, use **Path C** above instead, regardless of zone.

Spawn the `implement-capability` agent via the `Agent` tool with the full task context
assembled as input. The context to pass includes:

- The capability ID, name, zone, and level
- The governing FUNC ADR(s)
- The business events to implement (names and trigger conditions)
- The business objects involved
- The event subscriptions required
- The Definition of Done

Use:
```
Agent({
  subagent_type: "implement-capability",
  description: "Scaffold [capability name]",
  prompt: <full context block as described above>
})
```

Say:
> "Spawning implement-capability agent for [capability name] with task TASK-[NNN]..."

The implement-capability agent handles all architectural and implementation decisions —
Clean Architecture, DDD, microservice scaffolding, .NET patterns — and exercises judgment
on aggregates, ports, and bus topology from the FUNC/tactical ADRs. Your job is to feed it
the right business context from the task file. The agent may push back if the context is
incoherent (missing FUNC ADR, cross-zone task, stack mismatch); surface that to the user
as the gap to resolve.

---

### Path B — CHANNEL zone

> Use this path **only** when `task_type` is absent or `full-microservice`
> and the zone is `CHANNEL`. If `task_type: contract-stub`, use **Path C**
> above instead.

Spawn **both** the `create-bff` and `code-web-frontend` agents **in parallel**
(send both `Agent` tool calls in a single message — they are independent and
run concurrently in the same isolated worktree):

1. **`create-bff` agent** — senior backend engineer that scaffolds the .NET 10 BFF
   aggregating upstream events from RabbitMQ and exposing REST endpoints per L3
   sub-capability. The agent reasons from the FUNC ADR + tactical ADRs and makes
   explicit decisions on L3 endpoints, event topology, ports, and ETag strategy.

   Use:
   ```
   Agent({
     subagent_type: "create-bff",
     description: "Scaffold BFF for [capability name]",
     prompt: <full context block: L2 capability ID, FUNC ADR content (L3 list,
              events consumed with emitting L2, events produced, dignity rules),
              tactical ADRs from tech-adr/, Definition of Done, task identifier>
   })
   ```

2. **`code-web-frontend` agent** — senior frontend engineer that generates the
   vanilla HTML/CSS/JS web view from the task plan, FUNC ADRs, product vision,
   and the BFF API contract (or inferred contract if the BFF is not yet compiled).
   The agent decides on views, sections, stub data, dignity-rule DOM order, and
   testability hooks.

   Use:
   ```
   Agent({
     subagent_type: "code-web-frontend",
     description: "Scaffold frontend for [capability name]",
     prompt: <full context block: task identifier and task file content,
              capability ID, FUNC ADR content, product vision excerpts,
              instruction to read src/{zone-abbrev}/{capability-id}-bff/ for the
              API contract — or to infer it from endpoint paths derived by the
              create-bff agent if the BFF is not yet written, Definition of Done>
   })
   ```

Say:
> "Spawning create-bff and code-web-frontend agents in parallel for [capability name] — CHANNEL zone..."

Wait for **both** agents to complete before proceeding to Step 3. Either agent
may push back if its context is incoherent (capability not in CHANNEL zone,
missing FUNC ADR, output dir already populated, unsupported stack); surface
that to the user as the gap to resolve.

---

## Step 2.5 — Add the contract harness (Path A only)

> **Skip this step for Path B (CHANNEL).** The BFF already enforces its own
> contract surface via `create-bff`. A future `harness-bff` skill will extend
> the same lineage pattern there.
>
> **Skip this step for Path C (contract-stub).** Mode B produces only JSON
> schemas + a worker stub; the full OpenAPI/AsyncAPI harness is overkill for
> that scaffold. Re-introduce when the contract-stub matures into a full
> microservice (which will route back through Path A and trigger Step 2.5).

After `implement-capability` succeeds for a non-CHANNEL task, invoke the
`/harness-backend` skill to add the contract harness to the freshly-scaffolded
microservice. The harness produces, under
`sources/{capability-name}/backend/contracts/specs/`:

- `openapi.yaml` (OpenAPI 3.1) — derived strictly from
  `process/{capability-id}/api.yaml` + `commands.yaml` + `read-models.yaml` +
  `schemas/CMD.*.schema.json` + `bcm-pack.carried_objects` (resource shapes).
- `asyncapi.yaml` (AsyncAPI 2.6) — derived strictly from
  `process/{capability-id}/bus.yaml` + `schemas/RVT.*.schema.json` +
  `bcm-pack.emitted_resource_events` / `consumed_resource_events`.
- `lineage.json` — top-level lineage (capability + bcm + process metadata).
- `harness-report.md` — closure verdict.

Both specs carry a top-level `x-lineage` block plus per-operation,
per-message, per-channel `x-lineage` extensions so every entry traces back
to its `process/` source AND its `bcm-pack` source. The harness also adds a
`*.Contracts.Harness/` project to the .NET solution (which re-runs the
validation on every `dotnet build`) and mounts `/openapi.yaml` and
`/asyncapi.yaml` endpoints in the Presentation project.

Invoke:

```
Skill: harness-backend
Args:  CAPABILITY_ID = <from task>
       (worktree is auto-detected from current branch)
```

Say:
> "Running harness-backend for TASK-[NNN] — generating openapi.yaml + asyncapi.yaml with full process / bcm lineage..."

If `/harness-backend` reports a closure failure (dangling
`x-lineage.process.*`, missing controller, BCM warning), surface the report
to the user and **do NOT proceed to Step 3**. The remediation depends on the
gap:

| Gap                                            | Resolution                                                  |
|------------------------------------------------|-------------------------------------------------------------|
| Dangling `x-lineage.process.*` reference       | run `/process <CAPABILITY_ID>` to amend the model           |
| Dangling `x-lineage.bcm.*` reference           | fix BCM upstream in `banking-knowledge`                     |
| Missing controller / consumer in microservice  | feed the gap into the remediation loop (Step 3)             |
| Drift between generated and committed specs    | re-run the harness in default mode and commit the diff      |

Only the third row is a remediation-loop case — the others require an
upstream fix. Treat the first two as a **stall** (do not consume loop
budget): record `stalled_reason: "harness closure failed: <gap>"` and stop.

Once `/harness-backend` returns green, proceed to Step 3.

---

## Step 3 — Validate with the matching test skill (zone-aware)

After all implementation agents complete, invoke the test skill that matches
the capability zone:

| Zone | Test skill | Test agent | Targets |
|------|-----------|-----------|---------|
| Non-CHANNEL (BUSINESS_SERVICE_PRODUCTION, SUPPORT, REFERENTIAL, EXCHANGE_B2B, DATA_ANALYTIQUE, STEERING) | `/test-business-capability` | `test-business-capability` | .NET microservice under `sources/{cap-name}/backend/` |
| CHANNEL | `/test-app` | `test-app` | Frontend under `sources/{cap-id}/frontend/` and BFF under `src/{zone-abbrev}/{cap-id}-bff/` |

The test skill spawns its agent (senior test engineer) to validate that the
delivered artifacts satisfy the Definition of Done, FUNC ADR rules, and the
product/strategic vision.

Pass to the test skill:
- The task identifier (`TASK-NNN`)
- The capability ID and zone
- Any port or path information printed by the implementation skills (e.g.,
  `LOCAL_PORT` for backend, `BFF_PORT` for CHANNEL)

Say (non-CHANNEL):
> "Running test-business-capability for TASK-[NNN] (loop [loop_count+1]/[max_loops])..."

Say (CHANNEL):
> "Running test-app for TASK-[NNN] (loop [loop_count+1]/[max_loops])..."

### If all tests pass

Proceed directly to Step 4 (close and open PR).

### If tests fail — Remediation loop

**Before each remediation iteration**, check the loop budget:

```
IF loop_count >= max_loops → trigger the Stall Procedure (see below)
ELSE:
  loop_count += 1
  Write updated loop_count to task file frontmatter
  Proceed with the remediation iteration
```

For each remediation iteration within budget:

1. **Identify the failing artifact** (BFF, frontend, microservice).

2. **Re-invoke the relevant implementation skill** with an additional remediation context
   block prepended to the prompt:

   ```
   ── REMEDIATION CONTEXT (loop [loop_count]/[max_loops]) ──
   The previous implementation of TASK-[NNN] failed the following test criteria:

   ❌ [Criterion 1]: [what the test found vs. what was expected]
      Suggested correction: [from the test skill's output]

   ❌ [Criterion 2]: [...]
      Suggested correction: [...]

   Re-implement only what is needed to fix these criteria. Do not touch passing code.
   ── END REMEDIATION CONTEXT ──
   ```

3. **After the fix is applied**, re-invoke the matching test skill (`/test-business-capability` for non-CHANNEL or `/test-app` for CHANNEL) for the same task — it will spawn a fresh test agent run.

4. **Repeat** from the budget check until all criteria pass or the budget is exhausted.

---

### Stall Procedure (loop budget exhausted)

Triggered when `loop_count >= max_loops` and tests still fail.

1. **Update the task file frontmatter**:
   ```yaml
   status: stalled
   loop_count: [current value]
   max_loops: [current value]
   stalled_reason: |
     Loop budget exhausted after [loop_count] iteration(s).
     Failing criteria at last run:
     - ❌ [Criterion 1]: [failure description]
     - ❌ [Criterion 2]: [failure description]
     Last test run: [DATE]
   ```

2. **Refresh `/tasks/BOARD.md`** by invoking `/sort-task` so the board reflects the `stalled` status immediately.

3. **Report to the user** — this is a **mandatory human checkpoint**:
   ```
   ⚫ TASK-[NNN] stalled after [loop_count] remediation loop(s).

   Loop budget: [loop_count]/[max_loops] used.

   Failing criteria at last run:
     ❌ [Criterion 1]: [failure description]
     ❌ [Criterion 2]: [failure description]

   The kanban board has been updated (status: stalled).
   No further automated remediation will be attempted.

   To resume work:
     /continue-work TASK-[NNN]            ← resets to [max_loops] loops
     /continue-work TASK-[NNN] --max-loops 20  ← resets with a custom budget

   You may also add guidance before relaunching:
     "The consent gate ID changed — look for #gate-consentement not #consent-gate"
   ```

4. **Stop** — do not proceed to Step 4. The task remains `stalled` until
   `/continue-work` is invoked.

---

## Step 4 — Track, Close, and Open PR

After all tests pass (or after the remediation loop concludes):

1. **Update the task status** in the task file:
   - Change `status: in_progress` (or `status: todo` if invoked directly) to `status: in_review`.
   - Add the PR URL as a new frontmatter field `pr_url:` so `/sort-task` can display it.
   - If the remediation loop ended with remaining failures, add `draft: true`.

   Example resulting frontmatter:
   ```yaml
   status: in_review
   pr_url: https://github.com/org/repo/pull/42
   ```

2. **Run validation** to confirm the implementation is coherent with the BCM:
   ```bash
   python tools/validate_repo.py
   python tools/validate_events.py
   ```

3. **(Removed)** No per-capability task index file is maintained — `/tasks/`
   contains only `BOARD.md` (refreshed automatically by `/sort-task`) and the
   `<CAP_ID>/TASK-*.md` cards. The TASK file's frontmatter status update
   in step 1 is sufficient — the board picks it up.

4. **Commit all changes** using the Conventional Commits format:
   ```bash
   git add <all relevant files — never git add -A>
   git commit -m "feat(TASK-NNN): <imperative subject ≤72 chars>

   <2–3 sentences: what was built and why, referencing the FUNC ADR>

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
   ```

5. **Push the branch** and open a PR:

   Retrieve the `LOCAL_PORT` value that the implement-capability agent printed in its summary
   (or the BFF port for CHANNEL zone).
   Derive the infrastructure ports: `MONGO_PORT = LOCAL_PORT + 100`,
   `RABBIT_PORT = LOCAL_PORT + 200`, `RABBIT_MGMT_PORT = LOCAL_PORT + 201`.

   Build the PR body using this template, substituting all placeholders:

   ```bash
   git push -u origin "$BRANCH_NAME"

   gh pr create \
     --title "feat(TASK-NNN): <subject line>" \
     --base main \
     --body "$(cat <<'PRBODY'
   ## Implemented Capability

   **[Capability Name]** ([Capability ID]) — Zone [TOGAF zone]
   Epic [N] — [Epic name]

   ## What Was Built

   - [DoD criterion 1] ✅
   - [DoD criterion 2] ✅
   - [DoD criterion 3] ✅

   ## Test Results

   All Definition of Done criteria validated by `test-business-capability` (non-CHANNEL) or `test-app` (CHANNEL).
   Report: `tests/{capability-id}/TASK-NNN-{slug}/report.html`

   ## Local Test Environment

   > Start the local stack before running manual tests.

   ### Backend (.NET microservice) — non-CHANNEL only

   \`\`\`bash
   cd sources/{capability-name}/backend
   docker-compose up -d          # MongoDB + RabbitMQ
   dotnet run --project src/{Namespace}.{CapabilityName}.Presentation
   \`\`\`

   | Service | Local URL |
   |---------|-----------|
   | REST API | http://localhost:{LOCAL_PORT} |
   | Swagger UI | http://localhost:{LOCAL_PORT}/swagger |
   | RabbitMQ Management | http://localhost:{RABBIT_MGMT_PORT} |
   | MongoDB (port) | localhost:{MONGO_PORT} |

   > ⚠ Required environment variables: `GITHUB_USERNAME` and `GITHUB_TOKEN`
   > (NuGet GitHub Packages feed).

   ### BFF (.NET Minimal API) — CHANNEL zone

   \`\`\`bash
   cd src/{zone-abbrev}/{capability-id}-bff
   docker compose up -d
   dotnet run
   \`\`\`

   | Service | Local URL |
   |---------|-----------|
   | BFF REST | http://localhost:{BFF_PORT} |
   | RabbitMQ Management | http://localhost:{RABBIT_MGMT_PORT} |

   ### Frontend (vanilla HTML/CSS/JS) — CHANNEL zone

   \`\`\`bash
   cd sources/{capability-id}/frontend
   python -m http.server 3000
   \`\`\`

   | Scenario | URL |
   |----------|-----|
   | Nominal | http://localhost:3000?beneficiaireId=BEN-001 |
   | Consent refusal | http://localhost:3000?beneficiaireId=BEN-001&consentement=refuse |

   ## Manual Test Plan

   - [ ] `docker-compose up -d` without errors
   - [ ] Service starts on expected port
   - [ ] `GET /health` returns 200
   - [ ] Nominal capability scenario works end-to-end
   - [ ] Business event visible in RabbitMQ Management (if applicable)
   - [ ] Frontend loads and displays stub data correctly (if applicable)

   ---
   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   PRBODY
   )"
   ```

   If `gh` is not available or the repository has no GitHub remote, skip the PR creation,
   commit locally, and tell the user:
   > "Changes committed on branch `feat/TASK-NNN-{slug}`. No GitHub remote detected — open a PR manually when ready."

6. **Report to the user:**
   > "TASK-[NNN] is complete. Branch `feat/TASK-NNN-{slug}` pushed. PR opened: [PR URL]
   >
   > Test results: [N]/[Total] DoD criteria validated ✅
   >
   > Local test environment:
   > - Backend / BFF: http://localhost:{LOCAL_PORT}/swagger (or BFF endpoint)
   > - Frontend: http://localhost:3000?beneficiaireId=BEN-001 (if generated)
   >
   > Next available tasks for this capability:
   > - TASK-[NNN+1]: [title] (previously blocked on this task)
   >
   > Other ready tasks in the pipeline:
   > - [TASK-NNN from other capabilities, if any]"

---

## Important Boundaries

- **This skill does not write application code directly** — it delegates to the
  `implement-capability`, `create-bff`, and `code-web-frontend` agents.
- **This skill does not re-open design decisions** — the task file is the source of truth.
  If something in the task is wrong, the fix is to update the task file (via the task skill)
  before running code.
- **One task at a time** — do not batch multiple tasks in one invocation. Each TASK-NNN
  is an independent unit of work.
- **Zone detection is mandatory** — never spawn the `implement-capability` agent for a CHANNEL task,
  and never spawn the `create-bff` or `code-web-frontend` agents for a non-CHANNEL task.
- **Tests are not optional** — the matching test agent (test-business-capability for non-CHANNEL, test-app for CHANNEL) always runs after implementation.
  The only exception is when Playwright cannot be installed (fallback to manual checklist).
