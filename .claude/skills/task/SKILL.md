---
name: task
description: >
  Generates concrete implementation tasks for a planned business capability, ready to be 
  executed by the implement-capability agent. Tasks are written to /plan/{capability-id}/tasks/. 
  Use this skill whenever the user wants to generate tasks from a plan, break epics into 
  implementation work, create the task list for a capability, or prepare work for coding. 
  Trigger on: "generate tasks", "create tasks", "break down the plan", "tasks for capability", 
  "implementation tasks", "what are the tasks", or any time a plan.md exists for a capability 
  and the user is ready to define the implementation work items. Also trigger proactively 
  after a plan.md is created or updated for a capability.
---

# Task Skill

You are generating **implementation task files** for a business capability, based on its plan
and its Process Modelling layer. Each task will be picked up by the implement-capability
agent for execution. Tasks must contain enough context for a developer (or the
implement-capability agent) to work independently — without needing to ask questions.

---

## Hard rule — `process/{capability-id}/` is read-only

This skill reads `process/{capability-id}/` (aggregates, commands, policies,
read-models, bus topology, JSON Schemas) as a primary input — tasks routinely
reference `AGG.*`, `CMD.*`, `POL.*`, `PRJ.*`, `QRY.*` identifiers from there.
This skill **never writes** to that folder. A PreToolUse hook
(`process-folder-guard.py`) enforces this — every Write/Edit under
`process/**` outside the `/process` skill is rejected.

If the model evolves (new aggregate, renamed command, new policy), stop and run
`/process <CAPABILITY_ID>` first to refresh the model, then re-run `/task`.

---

## Before You Begin

1. **Identify the capability** to generate tasks for. Ask if not specified, or list plannable 
   capabilities (those with a `plan.md` but no `tasks/` directory yet, or with a stale task set).
   To enumerate plannable capabilities, run `bcm-pack list --level L2` (and `--level L3` if
   relevant) — never read `/bcm/*.yaml` directly.

2. **Fetch the capability pack** from the `bcm-pack` CLI — this is the **only** sanctioned 
   knowledge source. Do not read `/bcm/`, `/func-adr/`, `/adr/`, `/strategic-vision/`, or 
   `/product-vision/` directly; those paths are not authoritative in this checkout.

   ```bash
   bcm-pack pack <CAPABILITY_ID> --compact > /tmp/pack-task.json
   ```

   Lightweight mode is enough for task generation — you do not need the rationale ADRs 
   behind the vision narratives. Read these slices selectively:

   | Slice                       | Used for                                              |
   |-----------------------------|-------------------------------------------------------|
   | `capability_self`           | task `capability_id`, `capability_name`, level, ADRs  |
   | `capability_definition`     | governing FUNC ADR(s) — decisions and constraints     |
   | `emitted_business_events`   | "Business Events to Produce" per task                 |
   | `consumed_business_events`  | "Event Subscriptions Required" per task               |
   | `carried_objects`           | "Business Objects Involved" per task                  |
   | `carried_concepts`          | terminology grounding — feeds Open Questions if fuzzy |
   | `governing_urba`            | URBA ADR constraints (event meta-model, naming…)      |

   Then read the **local** artifacts:
   - `/plan/{capability-id}/plan.md` — the source of epics and exit conditions
   - `process/{capability-id}/` — the Process Modelling layer (read-only).
     Tasks must reference the `AGG.*` / `CMD.*` / `POL.*` / `PRJ.*` / `QRY.*`
     identifiers from `aggregates.yaml`, `commands.yaml`, `policies.yaml`,
     and `read-models.yaml`, and the routing keys / subscriptions from
     `bus.yaml`. If the folder is absent, stop and run `/process
     <CAPABILITY_ID>` first.
   - Existing tasks in `/plan/{capability-id}/tasks/` — to avoid duplication

   Check `pack.warnings` — non-empty entries should land in the `Open Questions` of the 
   first task that touches the affected area.

3. **Check the implement-capability agent** at `.claude/agents/implement-capability.md` 
   to understand what input format it expects, so tasks are written in a compatible structure.

---

## Task Structure

Each task is a markdown file in `/plan/{capability-id}/tasks/TASK-NNN-short-slug.md`.

Tasks are grouped by epic. Number them sequentially across the capability (TASK-001, TASK-002, etc.).

### What makes a good task?

A good task:
- Is **self-contained**: a developer reading only this file knows what to build
- Has a clear **Definition of Done** (not "implement X" but "when X is complete, Y is verifiable")
- Cites the **business capability** and **ADR** it implements
- Names the **business events** to produce (by name, as in the BCM)
- Specifies the **business objects** involved
- Lists its **dependencies** on other tasks (by TASK-NNN ID)
- Does not specify implementation technology (that's the implement-capability agent's job)

### Task file format

```markdown
---
task_id: TASK-[NNN]
capability_id: CAP.[ZONE].[NNN].[SUB]
capability_name: [Name]
epic: [Epic N — Epic Name]
status: todo
priority: high | medium | low
depends_on: [TASK-NNN, TASK-NNN]  # empty list if none
---

# TASK-[NNN] — [Short descriptive title]

## Context
[2-3 sentences: why this task exists, what business capability it contributes to, 
which service offer it serves]

## Capability Reference
- Capability: [Name] ([ID])
- Zone: [TOGAF zone]
- Governing ADR(s): [ADR-BCM-FUNC-NNNN]

## What to Build
[Clear description of the business behavior to implement. No technology — what the 
capability must be able to do when this task is done]

## Business Events to Produce
- [EventName] — emitted when [condition]
- [EventName] — emitted when [condition]

## Business Objects Involved
- [BusinessObjectName] — [role in this task]

## Event Subscriptions Required
- [EventName] (from [CapabilityID]) — consumed to [reason]

## Definition of Done
- [ ] [Verifiable condition 1]
- [ ] [Verifiable condition 2]
- [ ] All business events listed above are emitted under the correct conditions
- [ ] validate_repo.py passes with no errors
- [ ] validate_events.py passes with no errors

## Acceptance Criteria (Business)
[Business-language description of what a business owner would verify to accept this task]

## Dependencies
- [TASK-NNN]: [Why this must be done first]
- [CAP.ZONE.NNN]: [External capability dependency]

## Open Questions
- [ ] [Any unresolved question that must be answered before starting]
```

> **Important — Open Questions format:** every entry in `## Open Questions` MUST be written as a Markdown checkbox `- [ ]`. The `/sort-task` skill detects unresolved questions by counting unchecked checkboxes in this section. A plain bullet `-` will NOT be detected and the task will be wrongly classified as `ready`. When a question is resolved, tick it (`- [x]`) instead of deleting it, to preserve the audit trail.

---

## Step 1 — Review the Plan with the User

Before generating tasks, present the epic breakdown from the plan and ask:
> "I'll generate tasks for [capability]. The plan has [N] epics. Should I generate tasks 
> for all epics, or start with a specific one?"

For each epic:
- Confirm the exit condition is clear enough to generate verifiable tasks
- Flag any epic where more information is needed before tasks can be written
- Identify which tasks are sequential within the epic vs. which can run in parallel

---

## Step 2 — Generate Tasks

For each epic, generate the minimum set of tasks that together achieve the epic's exit condition. 
Avoid both:
- **Over-splitting**: don't create 10 micro-tasks where 3 coherent tasks suffice
- **Under-splitting**: don't create one task so large it requires multiple implement-capability 
  invocations with implicit coordination

A good rule of thumb: one task = one bounded context in the implement-capability sense. If the 
epic spans multiple bounded contexts, it should become multiple tasks.

Assign tasks:
- Sequential numbering: TASK-001, TASK-002, etc.
- Epic grouping: all tasks within an epic get a comment block header in the tasks directory listing

---

## Step 3 — Write and Index

Write each task file to `/plan/{capability-id}/tasks/TASK-NNN-[slug].md`.

After writing all tasks, create or update an index file at `/plan/{capability-id}/tasks/index.md`:

```markdown
# Task Index — [Capability Name] ([Capability ID])

## Epic 1 — [Name]
| ID | Title | Priority | Status | Depends On |
|----|-------|----------|--------|-----------|
| TASK-001 | [title] | high | todo | — |
| TASK-002 | [title] | high | todo | TASK-001 |

## Epic 2 — [Name]
| ID | Title | Priority | Status | Depends On |
|----|-------|----------|--------|-----------|
| TASK-003 | [title] | medium | todo | TASK-002 |
...

## Dependency Graph (text)
TASK-001 → TASK-002 → TASK-003
                    ↘ TASK-004 (parallel with TASK-003)
```

After writing all tasks, tell the user:
> "Tasks for [capability] are committed to `/plan/[capability-id]/tasks/`. 
> To implement a task, use the implement-capability agent and reference the task file.
> Start with TASK-001 (or any task with no dependencies)."
