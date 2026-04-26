---
name: task
description: >
  Generates concrete implementation tasks for a planned business capability, ready to be 
  executed by the implement-capability skill. Tasks are written to /plan/{capability-id}/tasks/. 
  Use this skill whenever the user wants to generate tasks from a plan, break epics into 
  implementation work, create the task list for a capability, or prepare work for coding. 
  Trigger on: "generate tasks", "create tasks", "break down the plan", "tasks for capability", 
  "implementation tasks", "what are the tasks", or any time a plan.md exists for a capability 
  and the user is ready to define the implementation work items. Also trigger proactively 
  after a plan.md is created or updated for a capability.
---

# Task Skill

You are generating **implementation task files** for a business capability, based on its plan. 
Each task will be picked up by the implement-capability skill for execution. Tasks must contain 
enough context for a developer (or the implement-capability skill) to work independently — 
without needing to ask questions.

---

## Before You Begin

1. **Identify the capability** to generate tasks for. Ask if not specified, or list plannable 
   capabilities (those with a `plan.md` but no `tasks/` directory yet, or with a stale task set).

2. **Read all relevant context:**
   - `/plan/{capability-id}/plan.md` — the source of epics and exit conditions
   - The capability's YAML in `/bcm/` — for technical identifiers and events
   - The capability's FUNC ADR(s) in `/func-adr/` — for decisions and constraints
   - `/adr/ADR-BCM-URBA-*.md` — relevant URBA ADRs (especially 0007-0013 for event model)
   - `/product-vision/product.md` — service offer context
   - Existing tasks in `/plan/{capability-id}/tasks/` — to avoid duplication

3. **Check the implement-capability skill** at `.claude/skills/implement-capability/SKILL.md` 
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
- Does not specify implementation technology (that's the implement-capability skill's job)

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
- [Any unresolved question that must be answered before starting]
```

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
> To implement a task, use the implement-capability skill and reference the task file.
> Start with TASK-001 (or any task with no dependencies)."
