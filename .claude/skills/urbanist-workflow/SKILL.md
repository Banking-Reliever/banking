---
name: urbanist-workflow
description: >
  Orchestrates the full domain-driven urbanist workflow: product brainstorming → strategic 
  business brainstorming → strategic tech brainstorming → business capabilities brainstorming 
  → BCM writer → plan → task → implement. 
  Use this skill to run the full pipeline, resume a workflow at any stage, check pipeline 
  status, or coordinate the sequential modeling sessions. Also spawns parallel subagents to 
  run BCM writer, plan, and task generation concurrently across multiple capabilities. 
  Trigger on: "run the full workflow", "start from the beginning", "where are we in the 
  workflow", "what's next in the pipeline", "urbanist workflow", "full pipeline", "resume 
  the workflow", "run all the plans", "generate all tasks", or any time the user wants 
  to understand or advance through the complete modeling-to-implementation journey.
---

# Urbanist Workflow Orchestrator

You are orchestrating the **domain-driven urbanist workflow** — a sequential pipeline that 
takes a product idea all the way to implementable tasks without writing a single line of code 
until the very last step.

The workflow is designed so that every decision is made at the right level, documented before 
it is executed, and traceable from the service offer down to the task file.

---

## The Pipeline

```
[1] Product Brainstorming         (product-brainstorming skill)
        ↓ produces: /product-vision/product.md
[2] Strategic Business Brainstorming  (strategic-business-brainstorming skill)
        ↓ reads: product.md
        ↓ produces: /strategic-vision/strategic-vision.md
[3] Strategic Tech Brainstorming  (strategic-tech-brainstorming skill)
        ↓ reads: strategic-vision.md + /adr/ADR-BCM-URBA-*.md + /func-adr/*.md
        ↓ produces: /tech-vision/tech-vision.md + /tech-vision/adr/ADR-TECH-STRAT-*.md
[4] Business Capabilities         (business-capabilities-brainstorming skill)
        ↓ reads: strategic-vision.md + tech-vision.md + /adr/ADR-BCM-URBA-*.md
        ↓ produces: /func-adr/ADR-BCM-FUNC-*.md
[5] BCM Writer ─────────────────────────────────────────────── [PARALLELIZABLE per zone/capability]
        ↓ reads: /func-adr/*.md + /templates/
        ↓ produces: /bcm/*.yaml (validated)
[6] Plan ───────────────────────────────────────────────────── [PARALLELIZABLE per L2 capability]
        ↓ reads: /bcm/*.yaml + /func-adr/*.md
        ↓ produces: /plan/{capability-id}/plan.md
[7] Task ───────────────────────────────────────────────────── [PARALLELIZABLE per capability]
        ↓ reads: /plan/{capability-id}/plan.md
        ↓ produces: /plan/{capability-id}/tasks/TASK-*.md
[8] Code (implement-capability)   (code skill)               [PARALLELIZABLE per task]
        ↓ reads: /plan/{capability-id}/tasks/TASK-NNN.md
        ↓ produces: implementation
```

Stages 1-4 are **sequential human sessions** — each requires dialogue and decision-making.
Stages 5-8 can be **parallelized per capability** once stage 4 is complete.

---

## Step 1 — Assess Pipeline Status

When invoked, first check the current state of the pipeline:

```bash
# Check which stages are complete
ls /product-vision/product.md
ls /strategic-vision/strategic-vision.md
ls /tech-vision/tech-vision.md
ls /func-adr/ADR-BCM-FUNC-*.md
ls /bcm/*.yaml
ls /plan/*/plan.md
ls /plan/*/tasks/TASK-*.md
```

Report the status clearly:

```
✅ Stage 1 — Product defined (product.md exists)
✅ Stage 2 — Strategic business vision defined (N L1 capabilities)
✅ Stage 3 — Technical vision defined (N tech ADRs)
✅ Stage 4 — N FUNC ADRs written
⏳ Stage 5 — BCM YAML not yet produced
⬜ Stage 6 — Plan: 0/N capabilities planned
⬜ Stage 7 — Tasks: 0/N capabilities have tasks
⬜ Stage 8 — No tasks ready for implementation

Next action: BCM Writer (stage 5)
```

---

## Step 2 — Guide or Execute the Next Action

### Stages 1-3: Interactive sessions (sequential)

These stages require human input — guide the user to invoke the right skill:

- **Stage 1 pending**: "Start with the product brainstorming session. Say 'let's brainstorm the product'."
- **Stage 2 pending**: "Product is defined. Say 'let's do the strategic business session' to map strategic capabilities."
- **Stage 3 pending**: "Strategic business vision is ready. Say 'strategic tech brainstorming' to define the technology stack."
- **Stage 4 pending**: "Technical vision is committed. Say 'business capabilities session' to define IS capabilities and produce FUNC ADRs."

### Stages 5-7: Automated parallelization

Once stage 4 is complete, you can spawn multiple subagents to run stages 5-7 in parallel.

**When the user says "run all plans", "generate all tasks", or similar:**

#### Parallel Plan Generation (Stage 5)

After BCM YAML is validated, spawn one subagent per L2 capability that lacks a plan:

For each unplanned capability, spawn a subagent with this prompt:
```
Use the plan skill to generate a plan for capability [CAP.ZONE.NNN — Name].
Context files needed:
- /bcm/*.yaml (capability definition)
- /func-adr/ADR-BCM-FUNC-*.md (governing ADRs)
- /strategic-vision/strategic-vision.md
- /product-vision/product.md
Save the result to /plan/[capability-id]/plan.md
```

#### Parallel Task Generation (Stage 6)

After plans exist, spawn one subagent per capability with a plan but no tasks:

For each unplanned capability, spawn a subagent with this prompt:
```
Use the task skill to generate tasks for capability [CAP.ZONE.NNN — Name].
Read the plan from /plan/[capability-id]/plan.md.
Context files needed:
- /bcm/*.yaml (capability definition)
- /func-adr/ADR-BCM-FUNC-*.md (governing ADRs)
Save tasks to /plan/[capability-id]/tasks/
```

Launch all subagents in the same turn (parallel). Report progress as they complete.

### Stage 7: Task execution

For stage 7, delegate to the **kanban skill** — it is the orchestrator for task scheduling, 
prioritization, and board tracking. Tell the user:

> "Tasks are ready for implementation. Use `/kanban` to see the board, get prioritization 
> recommendations, and launch tasks one by one.
>
> The kanban skill will:
> - Show which tasks are ready, in progress, or blocked
> - Rank them by critical path and business priority
> - Launch each task via the code skill
> - Track progress in `/plan/BOARD.md`"

Do not list tasks yourself here — that is kanban's job.

---

## Pipeline Integrity Checks

| Stage | Prerequisite |
|-------|-------------|
| Stage 2 | `/product-vision/product.md` contains a service offer sentence |
| Stage 3 | `/strategic-vision/strategic-vision.md` has at least one L1 capability |
| Stage 4 | `/tech-vision/tech-vision.md` exists with at least one committed tech ADR |
| Stage 5 | At least one `ADR-BCM-FUNC-*.md` in `/func-adr/` |
| Stage 6 | `/bcm/*.yaml` exists and `validate_repo.py` passes |
| Stage 7 | `/plan/{capability-id}/plan.md` has at least one epic with an exit condition |
| Stage 8 | Task file has status `todo` and all `depends_on` tasks are complete |

If a prerequisite is missing, explain which stage must be completed first.

---

## Governance Reminders

Throughout the workflow, enforce these non-negotiable rules:
- URBA ADRs (`adr/ADR-BCM-URBA-*.md`) are read-only — never modified by any stage
- Every FUNC ADR must reference the URBA ADRs it is constrained by
- Every capability in YAML must trace back to a FUNC ADR
- Every task must trace back to a plan epic → BCM capability → FUNC ADR → URBA constraints

**The traceability chain is unbreakable:**
```
Service Offer → Strategic L1 → Tech Vision → IS L1/L2 → FUNC ADR → YAML → Plan Epic → Task → Code
```

Any stage that cannot establish this chain must stop and surface the gap to the user.
