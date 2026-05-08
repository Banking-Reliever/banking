# Banking — Implementation Repo for Reliever

This repo is the **implementation side** of Reliever, a financial-inclusion product.
It contains plans, tasks, generated source code, and generated tests.

All upstream knowledge (BCM YAML, GOV / URBA / FUNC / TECH-STRAT / TECH-TACT ADRs,
product / business / tech visions) lives in the external **`banking-knowledge`**
repository and is consumed **read-only** through the `bcm-pack` CLI. This repo never
authors or modifies upstream artifacts.

---

## The implementation pipeline

```
                 ┌──────────────────────────────────────────────────────────┐
                 │ Upstream — banking-knowledge repo (read-only via bcm-pack)│
                 │                                                          │
                 │  product → strategic → tech → FUNC ADR → tactical ADR    │
                 │   vision    business    vision    (per L2)    (per L2)   │
                 │             vision                                       │
                 │                              ↓                           │
                 │                          BCM YAML                        │
                 └──────────────────────────────────────────────────────────┘
                                              │
                                              │  bcm-pack pack <CAP_ID> --deep
                                              ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │ This repo — the implementation pipeline                                 │
   │                                                                         │
   │   [1] plan        [2] task       [3] sort-task        [4] code          │
   │       │  ─────▶       │  ─────▶      / launch-task       │ ─────▶       │
   │       │               │              │                   │              │
   │     plan.md         tasks/         BOARD.md          worktree           │
   │                                  + scheduler          + agents          │
   │                                                          │              │
   │                                                          ▼              │
   │                                                       [5] test          │
   │                                                       (zone-aware)      │
   │                                                          │              │
   │                                                          ▼              │
   │                                                    PR + status:         │
   │                                                    in_review            │
   └────────────────────────────────────────────────────────────────────────┘
```

The pipeline is **launched and resumed** through one entry point:

```
/implementation-pipeline
```

It probes upstream readiness via `bcm-pack`, inspects local artifacts, and
dispatches the next pending stage. It is idempotent — re-invoke after each
stage completes to advance.

---

## What `/implementation-pipeline` actually does

When you invoke the skill it:

1. **Probes upstream readiness** for each capability:
   ```bash
   bcm-pack pack <CAP_ID> --deep --compact > /tmp/probe.json
   jq '.slices' /tmp/probe.json   # all required slices must be non-empty
   jq '.warnings' /tmp/probe.json # must be empty
   ```
   Required slices: `product_vision`, `business_vision`, `tech_vision`,
   `governing_tech_strat`, `capability_definition`, `tactical_stack`,
   `capability_self`. If any is empty or `warnings` is non-empty, the
   skill stops and redirects you to the upstream repo.

2. **Inspects local artifacts** with `ls` — never touches `/bcm/`, `/func-adr/`,
   `/adr/`, `/strategic-vision/`, `/product-vision/`, `/tech-vision/`, `/tech-adr/`
   (those are upstream and not authoritative locally).

3. **Reports per-capability status** as a table of ✅ / ⏳ / ⬜ across the five
   stages, and names the next action.

4. **Dispatches the cheapest pending stage**:

   | Pending state | Action |
   |---|---|
   | Capabilities with a complete `bcm-pack` slice but no `plan.md` | Spawns one `plan` subagent per capability, in parallel |
   | Capabilities with a plan but no tasks | Spawns one `task` subagent per capability, in parallel |
   | Tasks exist | Hands off to `/launch-task` (which calls `/sort-task` first) |

5. **Stops driving execution at Stage 3**. From there `/launch-task` is the
   scheduler and `/code` is the worker — see below.

---

## The five stages

### Stage 1 — Plan

| | |
|---|---|
| **Skill** | `/plan` |
| **Reads** | `bcm-pack pack <CAP_ID> --deep` (BCM + ADRs + visions) |
| **Writes** | `plan/<CAP_ID>/plan.md` (epics, milestones, exit conditions) |
| **Parallelism** | one subagent per capability |

Plans are roadmap-level: they decompose a capability into epics with explicit
exit conditions that a downstream task can prove.

### Stage 2 — Task

| | |
|---|---|
| **Skill** | `/task` |
| **Reads** | `plan/<CAP_ID>/plan.md` + `bcm-pack pack <CAP_ID> --compact` |
| **Writes** | `plan/<CAP_ID>/tasks/TASK-NNN-*.md` |
| **Frontmatter** | `task_id`, `capability_id`, `epic`, `status`, `priority`, `depends_on`, `loop_count: 0`, `max_loops: 10` |
| **Parallelism** | one subagent per capability |

Tasks are unit-of-work-level: each carries a Definition of Done (DoD) that the
test stage will mechanically check off.

### Stage 3a — sort-task (read-only board)

| | |
|---|---|
| **Skill** | `/sort-task` |
| **Reads** | all `plan/**/TASK-*.md` |
| **Writes** | `plan/BOARD.md` |
| **Computes** | `ready` / `blocked` / `needs_info` / `stalled` / `in_progress` / `in_review` / `done` |
| **Auto-run** | PostToolUse hook on every TASK file change |

Pure observation. Never modifies tasks, never launches agents.

### Stage 3b — launch-task (scheduler)

| | |
|---|---|
| **Skill** | `/launch-task` |
| **Calls first** | `/sort-task` (to get fresh kanban state) |
| **Picks** | ready task by `critical_path × priority` |
| **Spawns** | one `/code` sub-agent per task |
| **Modes** | manual (suggest top 3) / reactive (on `ready` transition) / `auto` (parallel autonomous) |
| **Isolation** | each task gets its own git worktree at `/tmp/kanban-worktrees/TASK-NNN-{slug}/` on branch `feat/TASK-NNN-{slug}` |
| **Idempotency** | at most one `/code` agent per task at a time; at most one active task per capability |

### Stage 4 — Code (zone-aware)

| | |
|---|---|
| **Skill** | `/code` |
| **Reads** | task file + `bcm-pack pack <CAP_ID>` (for `zoning`) |
| **Branches** | on the capability's `zoning` field |

| `zoning` | Path | Agent(s) | Output |
|---|---|---|---|
| `BUSINESS_SERVICE_PRODUCTION` `SUPPORT` `REFERENTIAL` `EXCHANGE_B2B` `DATA_ANALYTIQUE` `STEERING` | A | `implement-capability` | `sources/<CAP_ID>/backend/` — .NET 10 microservice (Domain / Application / Infrastructure / Presentation / Contracts), MongoDB, RabbitMQ, `GET /health` |
| `CHANNEL` | B | `create-bff` ∥ `code-web-frontend` (parallel) | `src/<zone-abbrev>/<CAP_ID>-bff/` (.NET 10 ASP.NET Core BFF) + `sources/<CAP_ID>/frontend/` (vanilla HTML5 + CSS3 + JS) |

After implementation, `/code` invokes the matching test skill (Stage 5) and
runs a remediation loop: failing tests feed back into the implementation
agent with a `── REMEDIATION CONTEXT ──` block. The loop is bounded by
`max_loops` (default 10). Exhaustion → `status: stalled`, resumable via
`/continue-work TASK-NNN [--max-loops N]`.

**Branch isolation is end-to-end**: bus channels, RabbitMQ exchanges/queues,
OTel `environment` tag, frontend branch badge all carry the branch slug.
Concurrent worktrees never collide on infrastructure.

### Stage 5 — Test (zone-aware)

| | Path A — non-CHANNEL | Path B — CHANNEL |
|---|---|---|
| **Skill** | `/test-business-capability` | `/test-app` |
| **Agent** | `test-business-capability` | `test-app` |
| **Stack** | .NET service + MongoDB + RabbitMQ via docker-compose | static HTTP server (frontend) + .NET BFF + RabbitMQ |
| **Modes** | backend-only | `full-mock` / `frontend+bff` / `bff-only` |
| **Workdir** | `/tmp/test-<cap-id>-XXXXXX` (ephemeral) | `/tmp/test-app-<cap-id>-XXXXXX` (ephemeral) |
| **Generates** | `tests/<CAP_ID>/TASK-NNN-{slug}/{conftest.py, test_dod.py, test_business_rules.py, test_strategic.py, test_backend.py}` | `…/{conftest.py, test_dod.py, test_business_rules.py, test_strategic.py, test_bff.py?}` |
| **Asserts** | REST endpoints, persistence, RabbitMQ event emission, OTel tags | DOM order (dignity rule), Playwright DoD checks, BFF `/health` + ETag/304 |

Both paths produce `report.html` + `run.log`, translate pytest results into
business language (✅/❌ per DoD criterion), and tear down all spawned
processes. Original artifacts are never modified.

On success: `status: in_review`, `pr_url:` written to frontmatter, branch
pushed, `gh pr create` with DoD checklist + local-stack instructions
(including `LOCAL_PORT`, `MONGO_PORT`, `RABBIT_PORT`, `RABBIT_MGMT_PORT`,
`BFF_PORT`).

---

## Repo layout

```
/CLAUDE.md                            contributor & Claude Code guidance
/README.md                            this file
/plan/                                local — plans, tasks, kanban
   BOARD.md                           kanban (auto-refreshed via hook)
   <CAP_ID>/plan.md                   epics + milestones + exit conditions
   <CAP_ID>/tasks/TASK-NNN-*.md       unit-of-work + DoD + frontmatter
   <CAP_ID>/contracts/                JSON Schemas (contract-stub tasks)
/sources/                             local — implementation artifacts
   <CAP_ID>/backend/                  non-CHANNEL .NET 10 microservice
   <CAP_ID>/frontend/                 CHANNEL vanilla HTML/CSS/JS
/src/<zone-abbrev>/<CAP_ID>-bff/      CHANNEL .NET 10 ASP.NET Core BFF
/tests/<CAP_ID>/TASK-NNN-{slug}/      generated pytest suite + report.html
/.claude/
   skills/                            Claude Code skills (this orchestrator + the workers)
      implementation-pipeline/        the orchestrator
      plan/  task/  sort-task/        stages 1-3
      launch-task/  code/             stages 3-4
      test-business-capability/       stage 5 — Path A
      test-app/                       stage 5 — Path B
      task-refinement/                resolve a TASK's open questions
      continue-work/                  resume a `stalled` task
      pr-merge-watcher/  agent-watch/ ops helpers
   agents/                            agent definitions
      implement-capability.md         non-CHANNEL backend
      create-bff.md                   CHANNEL BFF
      code-web-frontend.md            CHANNEL frontend
      test-business-capability.md     stage-5 test agent — Path A
      test-app.md                     stage-5 test agent — Path B
/externals-template/                  scaffolding templates
```

---

## Skill cheatsheet

| Command | What it does |
|---|---|
| `/implementation-pipeline` | Status + advance to next pending stage |
| `/plan` | Stage 1 — generate `plan.md` for current capability |
| `/task` | Stage 2 — generate `TASK-NNN-*.md` for a capability |
| `/sort-task` | Refresh `BOARD.md` (read-only) |
| `/launch-task` | Stage 3+ — pick a ready task, spawn `/code` |
| `/launch-task auto` | Stage 3+ — autonomous parallel, all ready tasks |
| `/code TASK-NNN` | Stage 4-5 for one task (zone-aware dispatch) |
| `/test-business-capability TASK-NNN` | Stage 5 only — Path A |
| `/test-app TASK-NNN` | Stage 5 only — Path B |
| `/task-refinement TASK-NNN` | Resolve open questions on a task |
| `/continue-work TASK-NNN` | Resume a `stalled` task with reset loop counter |
| `/pr-merge-watcher` | Transition `in_review` tasks to `done` after PR merge |
| `/agent-watch [TASK-NNN]` | Live tmux view of a running code agent |

---

## Invariants

- **All upstream context is read-only.** GOV / URBA / TECH-STRAT / FUNC / TACTICAL
  ADRs and BCM YAML are consumed via `bcm-pack` only. To change them, edit the
  `banking-knowledge` repo.
- **Every task traces back** to a plan epic → BCM capability → FUNC ADR →
  URBA constraints. The chain is unbreakable.
- **Every implementation artifact** (microservice / BFF / frontend) is reachable
  from a TASK-NNN.
- **Branch isolation** — one branch per task, ports & exchanges scoped by branch
  slug, parallel worktrees never collide.
- **One code agent per task** at a time; one active task per capability.
- **Loop counters live on the TASK file**, not on the board. The code skill is the
  sole writer of `loop_count`, `max_loops`, `stalled_reason`, `pr_url`.

---

## Special task states

| Glyph | State | Meaning | Resolution |
|---|---|---|---|
| 🟢 | `ready` | All deps `done`, no open questions | `/launch-task` picks it up |
| 🟡 | `in_progress` | A `/code` agent is working in a worktree | `/agent-watch TASK-NNN` to observe |
| 🟣 | `in_review` | PR open, awaiting merge | `/pr-merge-watcher` flips to `done` on merge |
| ⚫ | `stalled` | `max_loops` exhausted with failing tests | `/continue-work TASK-NNN [--max-loops N]` |
| 🟠 | `needs_info` | Open questions in TASK file | resolve inline or `/task-refinement TASK-NNN` |
| 🔵 | `blocked` | A dep is not `done` | wait, or unblock the dep |
| ✅ | `done` | PR merged | — |
