---
name: urbanist-workflow
description: >
  Orchestrates the full domain-driven urbanist workflow: product brainstorming → strategic
  business brainstorming → strategic tech brainstorming → business capabilities brainstorming
  → tactical tech brainstorming (per L2) → BCM writer → plan → task → sort-task /
  launch-task → code → test. The code stage is zone-aware: non-CHANNEL capabilities go
  to the implement-capability agent (.NET microservice), CHANNEL capabilities go to create-bff +
  code-web-frontend in parallel. test-business-capability validates the result against
  the Definition of Done, with an automatic remediation loop bounded by a loop budget.
  The /sort-task skill keeps `/plan/BOARD.md` fresh (read-only); /launch-task is the
  task scheduler for stages 9-11 — it tracks readiness, prioritizes by critical path,
  and spawns autonomous code agents in isolated worktrees.

  Use this skill to run the full pipeline, resume a workflow at any stage, check pipeline
  status, or coordinate the sequential modeling sessions. Also spawns parallel subagents
  to run BCM writer, plan, task generation, and tactical tech ADRs concurrently across
  multiple capabilities.

  Trigger on: "run the full workflow", "start from the beginning", "where are we in the
  workflow", "what's next in the pipeline", "urbanist workflow", "full pipeline", "resume
  the workflow", "run all the plans", "generate all tasks", "run all tactical ADRs", or
  any time the user wants to understand or advance through the complete
  modeling-to-implementation journey.
---

# Urbanist Workflow Orchestrator

You are orchestrating the **domain-driven urbanist workflow** — a sequential pipeline that
takes a product idea all the way to running, validated implementation without writing a
single line of code until the very last stages.

The workflow is designed so that every decision is made at the right level, documented
before it is executed, and traceable from the service offer down to the deployed artifact.

---

## The Pipeline

```
[1] Product Brainstorming           (product-brainstorming skill)
        ↓ produces: /product-vision/product.md + ADR-PROD-*

[2] Strategic Business Brainstorming (strategic-business-brainstorming skill)
        ↓ reads:    product.md
        ↓ produces: /strategic-vision/strategic-vision.md (L1/L2/L3 strategic capabilities)

[3] Strategic Tech Brainstorming    (strategic-tech-brainstorming skill)
        ↓ reads:    strategic-vision.md + /adr/ADR-BCM-URBA-*.md
        ↓ produces: /tech-vision/tech-vision.md
                    /tech-vision/adr/ADR-TECH-STRAT-001..006

[4] Business Capabilities           (business-capabilities-brainstorming skill)
        ↓ reads:    strategic-vision.md + tech-vision.md + ADR-BCM-URBA-*
        ↓ produces: /func-adr/ADR-BCM-FUNC-*.md  (one per L2)

[5] Tactical Tech Brainstorming     (tactic-tech-brainstorming skill)         [PARALLELIZABLE per L2]
        ↓ reads:    tech-vision.md + ADR-TECH-STRAT-* + FUNC ADRs + URBA ADRs
        ↓ produces: /tech-adr/ADR-TECH-TACT-NNN-{cap-id-slug}.md  (one per L2)
        ↓ may flag strategic overrides → PENDING_ARCHITECT_TEAM

[6] BCM Writer                      (bcm-writer skill)                        [PARALLELIZABLE per zone/capability]
        ↓ reads:    /func-adr/*.md + /templates/
        ↓ produces: /bcm/*.yaml (validated by tools/validate_repo.py)

[7] Plan                            (plan skill)                              [PARALLELIZABLE per L2 capability]
        ↓ reads:    /bcm/*.yaml + FUNC ADR + tactical ADR + product/strategic vision
        ↓ produces: /plan/{capability-id}/plan.md  (epics, milestones, exit conditions)

[8] Task                            (task skill)                              [PARALLELIZABLE per capability]
        ↓ reads:    /plan/{capability-id}/plan.md + FUNC ADR + tactical ADR + BCM YAML
        ↓ produces: /plan/{capability-id}/tasks/TASK-NNN-*.md
                    (frontmatter: task_id, status, priority, depends_on, loop_count, max_loops)

[9a] Sort-task                      (sort-task skill)                         [READ-ONLY BOARD GENERATOR]
        ↓ reads:    all /plan/**/TASK-*.md
        ↓ writes:   /plan/BOARD.md  (auto-refreshed on every TASK file change via hook)
        ↓ computes: ready / blocked / needs_info / stalled / in_progress / in_review / done

[9b] Launch-task                    (launch-task skill)                       [SCHEDULER — drives stages 10-11]
        ↓ invokes:  /sort-task first to obtain a fresh report
        ↓ launches: code agents (manual, reactive on `ready` transition, or fully autonomous)
        ↓ enforces: idempotency (one code agent per task), one active task per capability

[10] Code                           (code skill)                              [PARALLELIZABLE per task — one agent per task]
        ↓ reads:    /plan/{capability-id}/tasks/TASK-NNN.md
        ↓ creates:  isolated git worktree on branch feat/TASK-NNN-{slug}
        ↓ detects:  capability `zoning` → routes to the correct path
        ↓ Path A — non-CHANNEL: spawns the implement-capability agent
        ↓ Path B — CHANNEL:     invokes create-bff + code-web-frontend in parallel
        ↓ then:    invokes test-business-capability + remediation loop
        ↓ ends:    PR opened, status: in_review, loop_count tracked, stall on budget exhaust

[10a] implement-capability agent   (.NET 10 microservice, Clean Architecture + DDD)
         output: sources/{capability-name}/backend/
         allocates LOCAL_PORT (10000-59999) + MongoDB / RabbitMQ ports
         creates Domain / Application / Infrastructure / Presentation / Contracts projects
         writes /health endpoint for readiness probing

[10b] create-bff                   (.NET 10 ASP.NET Core BFF — CHANNEL zone only)
         output: src/{zone-abbrev}/{capability-id}-bff/
         allocates BFF_PORT + RabbitMQ ports, writes .env.local with branch slug
         per L3: dedicated endpoints, ETag/304, Cache-Control: no-store
         per consumed event: RabbitMQ consumer + state cache update
         OTel mandatory dimensions: capability_id, zone, deployable, environment={branch}

[10c] code-web-frontend            (vanilla HTML5/CSS3/JS — CHANNEL zone only)
         output: sources/{capability-id}/frontend/  (index.html, styles.css, api.js, app.js)
         follows frontend-baseline pattern; STUB_DATA in api.js is the test contract
         branch badge in header, dignity rule in DOM order, French vocabulary
         test injection points: ?beneficiaireId= and ?consentement=refuse

[11] Test Business Capability      (test-business-capability skill)
        ↓ reads:    TASK file (DoD), plan, FUNC ADRs, product/strategic vision
        ↓ runs in:  ephemeral /tmp/ environment with isolated HTTP/Playwright/.NET stack
        ↓ generates: tests/{cap-id}/TASK-NNN-{slug}/{conftest.py, test_dod.py,
                     test_business_rules.py, test_strategic.py, test_bff.py?}
        ↓ modes:   full-mock | frontend+bff | backend-only | full-stack
        ↓ reports: report.html + run.log; failures feed code's remediation loop
```

**Stages 1–4 are sequential human sessions** — each requires Socratic dialogue and
human decision-making.
**Stage 5 is parallelizable per L2** but is itself a Socratic per-capability session
(one ADR at a time, with explicit override gating).
**Stages 6–8 can be fully parallelized** across capabilities (BCM YAML, plan, task generation).
**Stages 9–11 are driven by `/sort-task` (read-only board) and `/launch-task`
(orchestrator)** — the rest of the workflow does not launch implementation agents directly.

---

## Step 1 — Assess Pipeline Status

When invoked, first scan the repo to determine which stages are complete:

```bash
ls /product-vision/product.md                       # Stage 1
ls /strategic-vision/strategic-vision.md            # Stage 2
ls /tech-vision/tech-vision.md                      # Stage 3
ls /tech-vision/adr/ADR-TECH-STRAT-*.md             # Stage 3 ADRs
ls /func-adr/ADR-BCM-FUNC-*.md                      # Stage 4
ls /tech-adr/ADR-TECH-TACT-*.md                     # Stage 5
ls /bcm/*.yaml                                      # Stage 6
ls /plan/*/plan.md                                  # Stage 7
ls /plan/*/tasks/TASK-*.md                          # Stage 8
ls /plan/BOARD.md                                   # Stage 9 (sort-task / launch-task)
ls sources/*/backend/ src/*/*-bff/ sources/*/frontend/   # Stages 10a/b/c artifacts
ls tests/*/TASK-*-*/report.html                     # Stage 11 reports
```

Cross-reference: count L2 capabilities in `/func-adr/`; for stage 5 report the
ratio `tactical ADRs / L2 capabilities`; same logic for stages 6/7/8 vs. capabilities;
for stage 9 read the BOARD column counts.

Report the status clearly:

```
✅ Stage  1 — Product defined (product.md exists, N ADR-PROD-*)
✅ Stage  2 — Strategic business vision defined (N L1 capabilities)
✅ Stage  3 — Strategic technical vision defined (6 ADR-TECH-STRAT-*)
✅ Stage  4 — N FUNC ADRs written (covers M L2 capabilities)
⏳ Stage  5 — Tactical tech ADRs: K/N L2s have ADR-TECH-TACT-*
              ⚠ P override(s) PENDING_ARCHITECT_TEAM
⬜ Stage  6 — BCM YAML not yet produced (validate_repo.py blocked)
⬜ Stage  7 — Plan: 0/N capabilities planned
⬜ Stage  8 — Tasks: 0/N capabilities have tasks
⬜ Stage  9 — Kanban: BOARD.md not yet generated
⬜ Stage 10 — No implementation artifacts under sources/ or src/*/*-bff/
⬜ Stage 11 — No test reports under tests/

Next action: complete tactical tech ADRs (stage 5) for the remaining N-K L2 capabilities.
```

---

## Step 2 — Guide or Execute the Next Action

### Stages 1–4: Sequential Socratic sessions

These stages require human input — guide the user to invoke the right skill.
**Never short-circuit a session** — each one produces governance artifacts the next
stage depends on.

| Pending stage | What to tell the user |
|---|---|
| Stage 1 | "Start with product brainstorming. Say `let's brainstorm the product` to invoke `/product-brainstorming`." |
| Stage 2 | "Product is defined. Say `let's do the strategic business session` to map L1/L2/L3 strategic capabilities." |
| Stage 3 | "Strategic business vision is ready. Say `strategic tech brainstorming` to commit ADR-TECH-STRAT-001..006." |
| Stage 4 | "Technical vision is committed. Say `business capabilities session` to define IS capabilities and write FUNC ADRs (one per L2)." |

### Stage 5: Tactical tech brainstorming (per L2, parallelizable as separate sessions)

This stage is **mandatory before stage 6** — every L2 must have a committed tactical
ADR before BCM YAML can be written, because the YAML's technology fields (database, runtime,
exchange names, SLOs) are derived from the tactical ADR.

Two modes:

**Single L2 mode (sequential, human-driven):**
> "FUNC ADRs are committed. For each L2, run `/tactic-tech-brainstorming` to decide its
> concrete stack (language, database, RabbitMQ config, SLOs, sizing). Strategic
> ADRs are read-only — overrides require explicit justification and architect team approval."

**Batch mode (parallelizable):**
When the user says `run all tactical ADRs` or `all the tactical sessions`, launch one
sub-agent per L2 capability that lacks a tactical ADR. Each sub-agent invokes the
`tactic-tech-brainstorming` skill **non-interactively** by:
1. Reading the FUNC ADR for its assigned L2.
2. Applying the strategic constraint defaults from ADR-TECH-STRAT-*.
3. Producing a draft ADR with `status: Proposed` and **no overrides** (no override is ever
   auto-approved in batch mode — overrides require human dialogue).
4. Marking the ADR `requires_review: true` if any decision is non-trivial.

After batch generation, tell the user:
> "Drafted N tactical ADRs in `tech-adr/`. Review each one and run
> `/tactic-tech-brainstorming` interactively if any L2 needs a deviation from
> strategic defaults."

### Stages 6–8: Automated parallelization (BCM, plan, task)

Once stages 4 and 5 are complete, stages 6–8 can run concurrently per capability.

**When the user says "run all plans", "generate all tasks", or "run the full pipeline":**

#### Parallel BCM YAML generation (Stage 6)

For each capability that has a FUNC ADR but no YAML, spawn one subagent:
```
Use the bcm-writer skill to translate ADR-BCM-FUNC-NNN into validated YAML.
Read: /func-adr/ADR-BCM-FUNC-NNN.md, /tech-adr/ADR-TECH-TACT-NNN-{cap-id}.md,
      /templates/, /bcm/vocab.yaml.
Write to: /bcm/{capability-type}-{cap-id}.yaml
After writing, run python tools/validate_repo.py to confirm coherence.
```

#### Parallel Plan generation (Stage 7)

For each L2 capability without a `plan.md`, spawn one subagent:
```
Use the plan skill to generate a plan for capability [CAP.ZONE.NNN — Name].
Context files needed:
- /bcm/*.yaml                                   (capability definition)
- /func-adr/ADR-BCM-FUNC-NNN.md                 (governing functional ADR)
- /tech-adr/ADR-TECH-TACT-NNN-{cap-id}.md       (tactical stack ADR)
- /strategic-vision/strategic-vision.md
- /product-vision/product.md
Save the result to /plan/[capability-id]/plan.md
```

#### Parallel Task generation (Stage 8)

For each capability with a plan but no tasks, spawn one subagent:
```
Use the task skill to generate tasks for capability [CAP.ZONE.NNN — Name].
Read the plan from /plan/[capability-id]/plan.md.
Context files needed:
- /bcm/*.yaml                                   (capability definition)
- /func-adr/ADR-BCM-FUNC-NNN.md                 (governing functional ADR)
- /tech-adr/ADR-TECH-TACT-NNN-{cap-id}.md       (tactical stack ADR)
Save tasks to /plan/[capability-id]/tasks/TASK-*.md with frontmatter:
  task_id, capability_id, capability_name, epic, status, priority,
  depends_on, loop_count: 0, max_loops: 10
```

Launch all subagents in the same turn (parallel). Report progress as they complete.
After they finish, the `/sort-task` skill will detect the new TASK files via the
PostToolUse hook and refresh `/plan/BOARD.md` automatically.

### Stage 9: Hand off to the launch-task scheduler

Once tasks exist, **stop driving execution from this skill** — delegate to
`/launch-task` (with `/sort-task` as the read-only board view). Do not list tasks
here. Tell the user:

> "Tasks are ready. Use `/launch-task` to drive execution (or `/sort-task` for a
> read-only board view).
>
> `/launch-task` will:
> - Invoke `/sort-task` first to scan all `/plan/**/TASK-*.md` and compute readiness
>   (todo / in_progress / in_review / done / blocked / needs_info / stalled).
> - Prioritize ready tasks by critical path × business priority.
> - Maintain `/plan/BOARD.md` (auto-refreshed on every TASK file change via hook).
> - Launch one `code` agent per ready task — manually, reactively (when a dependency
>   merges), or fully autonomously (`/launch-task auto`).
> - In autonomous mode, each task gets its own git worktree under
>   `/tmp/kanban-worktrees/TASK-NNN-{slug}/` and a sub-agent that works in isolation.
> - Enforce strict idempotency: at most one `code` agent per task at a time.
> - Reflect status changes back to the board immediately.
>
> Special states:
> - 🟠 `needs_info` — open questions in the TASK file; resolve them or run
>   `/task-refinement TASK-NNN`.
> - ⚫ `stalled` — code skill exhausted its `max_loops` budget without passing tests;
>   resume with `/continue-work TASK-NNN [--max-loops N]`."

### Stage 10: Code execution (driven by /launch-task or manual /code)

When `/launch-task` (or the user via `/code TASK-NNN`) launches a task, the code skill:

1. **Verifies prerequisites** — status is `todo`/`in_progress`, all `depends_on` are `done`,
   no open questions, status not `stalled`.
2. **Reads loop counters** — initializes `loop_count: 0`, `max_loops: 10` if absent.
3. **Detects the capability zone** from `bcm/capabilities-*.yaml` (`zoning` field) or
   from `decision_scope.zoning` in the FUNC ADR. The zone determines the implementation path:

   | YAML `zoning`                | Path | Skill(s) invoked                         |
   |------------------------------|------|------------------------------------------|
   | `BUSINESS_SERVICE_PRODUCTION`| A    | `implement-capability`                   |
   | `SUPPORT`                    | A    | `implement-capability`                   |
   | `REFERENTIAL`                | A    | `implement-capability`                   |
   | `EXCHANGE_B2B`               | A    | `implement-capability`                   |
   | `DATA_ANALYTIQUE`            | A    | `implement-capability`                   |
   | `STEERING`                   | A    | `implement-capability`                   |
   | `CHANNEL`                    | B    | `create-bff` + `code-web-frontend` (parallel) |

4. **Creates an isolation branch** `feat/TASK-NNN-{slug}` from `main` (or works in the
   pre-existing worktree under `/tmp/kanban-worktrees/`).
5. **Summarizes** what will be built and waits for the user to confirm (skipped in
   autonomous `/launch-task auto` mode).
6. **Invokes the implementation skill(s)**:

   - **Path A (non-CHANNEL)** — the `implement-capability` agent scaffolds a complete .NET 10 microservice
     under `sources/{capability-name}/backend/`:
     - Allocates `LOCAL_PORT` from `shuf -i 10000-59999`; derives `MONGO_PORT = LOCAL_PORT+100`,
       `RABBIT_PORT = +200`, `RABBIT_MGMT_PORT = +201`.
     - Generates Domain / Application / Infrastructure / Presentation / Contracts projects
       wired into a `.sln`, with `nuget.config`, `docker-compose.yml`, MongoDB repository,
       command/read controllers, factory, DTO, and a `GET /health` endpoint required by
       test-business-capability for readiness.
     - All bus channels and queues are scoped by `{branch}-{ns-kebab}-{cap-kebab}-channel`
       to prevent cross-branch contamination.

   - **Path B (CHANNEL)** — `create-bff` + `code-web-frontend` run in **parallel** as two
     independent agents:
     - `create-bff` produces `src/{zone-abbrev}/{capability-id}-bff/`: ASP.NET Core Minimal
       API, one endpoint file per L3, one consumer per consumed event, an in-memory state
       cache with ETag/`If-None-Match`/`Cache-Control: no-store`, OTel instrumentation
       carrying `capability_id`, `zone`, `deployable`, `environment={branch}`. Allocates
       `BFF_PORT` and writes `.env.local` (gitignored) so test-business-capability can
       discover the port.
     - `code-web-frontend` produces `sources/{capability-id}/frontend/`: vanilla HTML5 +
       CSS3 + JS following the `frontend-baseline` pattern. Branch badge in `<header>`,
       dignity rule expressed as DOM order, French business vocabulary, complete `STUB_DATA`
       in `api.js` (canonical test contract), and stable test selectors
       (`#section-progression`, `#consent-gate`, `#table-historique`, `[data-filtre]`,
       etc.). URL injection points: `?beneficiaireId=` and `?consentement=refuse`.

7. **Invokes `test-business-capability`** (Stage 11 — see below). All artifacts are tested
   regardless of zone — backend-only for Path A, BFF + frontend for Path B (and the
   stack is auto-detected: full-mock / frontend+bff / backend-only / full-stack).

8. **Remediation loop** — if any test fails, the code skill increments `loop_count` and
   re-invokes the failing implementation skill with a `── REMEDIATION CONTEXT ──` block
   listing the criteria that failed and the suggested correction. Repeats until all tests
   pass **or** `loop_count >= max_loops`.

9. **Stall procedure** — if the loop budget is exhausted with failing tests:
   - Update task frontmatter: `status: stalled`, write `stalled_reason` (last failing
     criteria + date), keep `loop_count` and `max_loops`.
   - Invoke `/sort-task` to refresh `/plan/BOARD.md` so the board reflects the ⚫ state.
   - Stop. Tell the user to run `/continue-work TASK-NNN [--max-loops N]` with optional
     guidance to relaunch.

10. **Closure** — when tests pass:
    - Set `status: in_review`, add `pr_url:` to the frontmatter.
    - Run `python tools/validate_repo.py && python tools/validate_events.py` to confirm
      BCM coherence.
    - Update the task index `index.md`.
    - Commit with Conventional Commits format (`feat(TASK-NNN): …`).
    - Push branch and `gh pr create` with a body that includes:
      DoD checklist, test report path, local stack instructions for backend / BFF /
      frontend with the correct ports (`LOCAL_PORT`, `MONGO_PORT`, `RABBIT_PORT`,
      `RABBIT_MGMT_PORT`, `BFF_PORT`), and the manual test plan.
    - Report next available tasks (newly unblocked).

### Stage 11: Test Business Capability (invoked by code; can be invoked manually)

The test skill runs in a **temporary, isolated `/tmp/test-{cap-id}-XXXXXX` directory**:
1. Copies frontend artifacts (originals are never touched).
2. Picks a free HTTP port and launches `python -m http.server` for the static frontend.
3. If `src/{zone-abbrev}/{capability-id}-bff/.env.local` exists, starts the BFF on its
   recorded `BFF_PORT` and waits up to 15s for `/health` to return 200.
4. If a backend microservice is built, optionally launches it.
5. Generates `tests/{capability-id}/TASK-NNN-{slug}/`:
   - `conftest.py` — Playwright fixtures, mocked routes derived from `STUB_DATA`,
     `?beneficiaireId=` and `?consentement=refuse` URL injection.
   - `test_dod.py` — one test per `[ ]` item in the task's "Definition of Done".
   - `test_business_rules.py` — derived from FUNC ADRs and plan scoping decisions
     (dignity rule order, V0-without-gamification, business-language errors).
   - `test_strategic.py` — alignment with the product vision (French labels, encouraging
     vocabulary).
   - `test_bff.py` (when a BFF is running) — `/health`, snapshot endpoints, ETag/304
     behavior, `environment` tag matches `{branch}`.
6. Runs `pytest -v --tb=short --html=…/report.html`.
7. Translates results into business language (✅/❌ per DoD criterion + per ADR rule),
   writes `report.html` and `run.log`, then **kills all spawned processes and removes
   the temporary directory**. The originals are never modified.
8. If tests fail and the code skill called test-business-capability, the failure list
   feeds the code skill's remediation loop. If tests fail and the user invoked the
   skill directly, the report is the deliverable.

If Playwright cannot be installed, the skill falls back to a `manual-checklist.md`
under the same `tests/{capability-id}/TASK-NNN-{slug}/` directory.

---

## Pipeline Integrity Checks

| Stage | Prerequisite |
|-------|-------------|
| 2  | `/product-vision/product.md` contains a service offer sentence |
| 3  | `/strategic-vision/strategic-vision.md` has at least one L1 capability |
| 4  | `/tech-vision/tech-vision.md` exists with all six ADR-TECH-STRAT-* committed |
| 5  | At least one `ADR-BCM-FUNC-*.md` in `/func-adr/`; tactical ADR exists per L2 before stage 6 |
| 6  | A tactical ADR `ADR-TECH-TACT-*` exists for each L2 referenced in FUNC ADRs |
| 7  | `/bcm/*.yaml` exists and `python tools/validate_repo.py` passes |
| 8  | `/plan/{capability-id}/plan.md` has at least one epic with an exit condition |
| 9  | At least one `TASK-NNN-*.md` in `/plan/*/tasks/` with valid frontmatter |
| 10 | Task status is `todo` (or `in_progress` re-entry); all `depends_on` are `done`; no open questions; not `stalled` |
| 11 | An implementation artifact exists in `sources/{cap}/`, `src/*/{cap-id}-bff/`, or `sources/{cap-id}/frontend/` |

If a prerequisite is missing, explain which earlier stage must be completed first.
**Strategic overrides flagged `PENDING_ARCHITECT_TEAM`** in any tactical ADR do not
block stage 6 mechanically, but the ADR's `status` must move from `Proposed` to
`Accepted` (with architect approval) before the corresponding capability can leave
stage 9.

---

## Governance Reminders

Throughout the workflow, enforce these non-negotiable rules:

- **GOV ADRs** (`adr/ADR-BCM-GOV-*.md`) define the meta-rules — read-only.
- **URBA ADRs** (`adr/ADR-BCM-URBA-*.md`) are read-only — never modified by any stage.
- **TECH-STRAT ADRs** (`tech-vision/adr/ADR-TECH-STRAT-*.md`) are the strategic constraint
  surface — read-only after stage 3. Every tactical ADR must explicitly cite which
  TECH-STRAT rules it applies and which (if any) it overrides.
- **Tactical ADRs** (`tech-adr/ADR-TECH-TACT-*.md`) may override TECH-STRAT rules **only**
  with: a hard constraint justification (not a preference), an explicit `OVERRIDE-NNN`
  block in the ADR body, and `approval_status: PENDING_ARCHITECT_TEAM` until reviewed.
- Every FUNC ADR must reference the URBA ADRs it is constrained by.
- Every capability in YAML must trace back to a FUNC ADR.
- Every task must trace back to plan epic → BCM capability → FUNC ADR → URBA constraints.
- Every implementation artifact (microservice, BFF, frontend) must be reachable from a
  TASK-NNN, which is itself reachable from a plan epic.

**The traceability chain is unbreakable:**

```
Service Offer → Strategic L1 → Strategic Tech (TECH-STRAT) → IS L1/L2 (FUNC) →
   Tactical Tech (TECH-TACT) → BCM YAML → Plan Epic → Task → Code → Tests → PR
```

Any stage that cannot establish this chain must stop and surface the gap to the user.

---

## Operational Notes

- **The `/sort-task` skill runs on every TASK file change** (via PostToolUse hook). It
  refreshes `/plan/BOARD.md` automatically — do not regenerate it from this skill.
- **Branch / environment isolation is end-to-end.** Every implementation skill
  (implement-capability, create-bff, code-web-frontend) reads the current git branch slug
  and embeds it in artefact names: bus channels, RabbitMQ exchanges/queues, OTel
  `environment` tag, frontend branch badge. test-business-capability reads `.env.local`
  to find the BFF port for the active branch. This guarantees that concurrent
  worktrees launched by `/launch-task auto` never collide on infrastructure.
- **Port allocation is per-component, not per-pipeline.** The implement-capability agent allocates
  `LOCAL_PORT` 10000–59999 + 100/200/201 offsets. create-bff allocates `BFF_PORT` +
  100/101 offsets. The PR body assembled by the code skill must include all relevant
  ports in the local-test instructions.
- **Loop counters live on the TASK file**, not on the board. The code skill is the
  sole writer of `loop_count`, `max_loops`, `stalled_reason`, and `pr_url`. `/sort-task`
  reads them to render the board.
- **Auto mode is opt-in**, triggered by phrases like "auto", "launch everything",
  "launch ready tasks", "auto-dequeue". In auto mode `/launch-task` creates worktrees,
  spawns parallel code sub-agents, and never asks for confirmation. In manual mode
  `/launch-task` suggests the top 3 ready candidates and waits for the user to pick.
