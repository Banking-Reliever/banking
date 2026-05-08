---
name: plan
description: >
  Breaks a validated L2 or L3 business capability into an implementation roadmap expressed as 
  epics and milestones. Produces /plan/{capability-id}/plan.md for each capability. Use this 
  skill whenever the user wants to plan how to implement a capability, create an epic breakdown, 
  define milestones for a capability, or produce a capability roadmap. Trigger on: "plan this 
  capability", "create a plan", "epic breakdown", "roadmap for capability", "how do we implement 
  [capability]", "plan phase", or any time the BCM YAML exists and the user is ready to plan 
  implementation. Also trigger proactively after the BCM writer produces validated YAML for 
  a new capability.
---

# Plan Skill

You are producing an **implementation plan** for one or more business capabilities. The plan 
expresses what must be built (in business terms), in what order, with what dependencies — 
without specifying how it is built technically. The plan bridges the capability definition 
(from the BCM/ADRs + the `/process` Process Modelling layer) and the task generation phase.

**Absolute constraint**: No code, no technical architecture. The plan is in business capability 
language. The "how" emerges in the task phase.

---

## Hard rule — `process/{capability-id}/` is read-only

The `process/{capability-id}/` folder is the output of the `/process` skill (the
DDD tactical Process Modelling layer: aggregates, commands, policies, read-models,
bus topology, JSON Schemas). This skill **reads** that folder as a primary input
to ground epics in real aggregates and commands, but **never writes** to it. A
PreToolUse hook (`process-folder-guard.py`) enforces this — every Write/Edit
attempt under `process/**` outside the `/process` skill is rejected.

If the `process/{capability-id}/` folder is missing or stale relative to the FUNC
ADR returned by `bcm-pack`, **stop and tell the user to run `/process
<CAPABILITY_ID>` first**. Do not attempt to derive aggregates or commands inside
the plan; that is a category violation.

---

## Knowledge access — `bcm-pack` CLI (mandatory)

**You MUST source all BCM, ADR, vision, and event knowledge from the `bcm-pack` CLI.**
Do not read `/bcm/`, `/func-adr/`, `/adr/`, `/strategic-vision/`, `/product-vision/`, or any 
other knowledge file directly from the local working directory — those paths may be missing, 
stale, or incomplete in this checkout. The authoritative corpus lives in the
`Banking-Reliever/banking-knowledge` Git repository, and `bcm-pack` is the only sanctioned 
way to query it.

Two subcommands are all you need:

```bash
# 1. Enumerate plannable capabilities (use to disambiguate user input)
bcm-pack list --level L2
bcm-pack list --level L3

# 2. Fetch the full pack for one capability (lightweight mode is the default)
bcm-pack pack <CAPABILITY_ID> --deep --compact
```

Always pass `--deep` from this skill: it pulls in the rationale ADRs (URBA, governance,
tech-strategic) behind the `*-vision.md` narratives, which the plan needs for strategic 
alignment. Add `--compact` to keep the JSON on a single line — easier to pipe into `jq` or
`python3 -c`.

The pack JSON exposes these slices under `slices.*` — map them to the plan sections:

| Slice                       | What it gives you                                      | Plan section it feeds                |
|-----------------------------|--------------------------------------------------------|--------------------------------------|
| `capability_self`           | The L2/L3 itself (description, owner, ADRs)            | Capability Summary                   |
| `capability_ancestors`      | Parent L1 (and grandparent if L3)                      | Strategic Alignment                  |
| `capability_definition`     | The governing FUNC ADR(s)                              | Epic framing, Exit conditions        |
| `emitted_business_events`   | Events the capability must produce                     | Epics — "Unlocks events"             |
| `consumed_business_events`  | Events the capability subscribes to                    | Cross-capability dependencies        |
| `emitted_resource_events`   | Technical projections of emitted events                | Sanity check on event topology       |
| `consumed_resource_events`  | Technical subscriptions                                | Sanity check on event topology       |
| `carried_objects`           | Business objects owned/touched by the capability       | Capability Summary                   |
| `carried_concepts`          | Canonical business concepts with definition + rules    | Capability Summary, Open Questions   |
| `governance_adrs`           | Applicable GOV ADRs (review cycle, arbitration…)       | Risks, Sequencing constraints        |
| `governing_urba`            | URBA ADRs scoping this capability                      | Risks, Sequencing constraints        |
| `governing_tech_strat`      | Strategic-tech ADRs that frame the zone                | Strategic Alignment                  |
| `tactical_stack`            | Tactical-tech ADRs already accepted for this L2        | Strategic Alignment                  |
| `product_vision`            | Product-vision narrative + rationale (with `--deep`)   | Strategic Alignment, North-star      |
| `business_vision`           | Strategic-business narrative + rationale               | Strategic Alignment                  |
| `tech_vision`               | Strategic-tech narrative + rationale                   | Strategic Alignment                  |
| `vocab`                     | Allowed levels and zoning values                       | Validation only                      |

Always check `pack.warnings` after invocation — non-empty means the corpus has gaps that
should land in the plan's **Open Questions** section.

### Repo ref and offline behaviour

- Default ref is `main` on `git@github.com:Banking-Reliever/banking-knowledge.git`. To pin a 
  specific snapshot (e.g. matching a release): `bcm-pack --ref v0.1.0 pack <ID> --deep --compact`.
- Cached locally under `~/.cache/bcm-pack/`. Add `--no-fetch` to skip the per-invocation 
  `git fetch` if the network is slow or unreachable; `--fresh` re-clones from scratch.
- If the user has a local checkout, they can set `BANKING_KNOWLEDGE_ROOT=/path/to/checkout` 
  and `bcm-pack` will read from disk silently. Don't assume that's the case.

### Recommended invocation pattern

```bash
# One JSON object → parse it once, then drive the plan from the parsed slices.
bcm-pack pack CAP.BSP.001.PAL --deep --compact > /tmp/pack.json
jq '.slices.capability_self[0]'         /tmp/pack.json
jq '.slices.capability_definition[0]'   /tmp/pack.json
jq '.slices.emitted_business_events'    /tmp/pack.json
jq '.warnings'                          /tmp/pack.json
```

If the capability ID is unknown to `bcm-pack pack` (exit code 2), do not fall back to local
files — surface the error to the user and ask them to confirm the ID against `bcm-pack list`.

---

## Before You Begin

1. **Identify which capability to plan.** The user should specify the capability ID (e.g., 
   `CAP.BSP.001.PAL`) or a name. If ambiguous, run `bcm-pack list --level L2` (and 
   `--level L3` if relevant), present the matches, and ask the user to select.

2. **Fetch the capability pack** with `bcm-pack pack <ID> --deep --compact`. This single call 
   replaces all of the previous local file reads (capability YAML, FUNC ADR, strategic 
   vision, product vision, etc.). Do not read those files from disk.

3. **Read the Process Modelling layer (read-only).** Verify that
   `process/{capability-id}/` exists and contains at least `README.md`,
   `aggregates.yaml`, `commands.yaml`, `policies.yaml`, `read-models.yaml`, and
   `bus.yaml`. These are produced by the `/process` skill and are the canonical
   source of:
   - the **aggregates** (consistency boundaries) the plan must deliver,
   - the **commands** the capability accepts,
   - the **policies** wiring consumed events to commands,
   - the **read-models** and queries the capability exposes,
   - the **bus topology** (exchanges, routing keys, subscriptions).

   If the folder is absent, **stop** and ask the user to run `/process
   <CAPABILITY_ID>` first. Do **not** attempt to invent aggregates / commands
   from the FUNC ADR — that is `/process`'s responsibility, and a hook will
   block any attempt to write under `process/` from this skill.

   If the folder exists but lacks an entry referenced in `pack.emitted_*` /
   `pack.consumed_*`, surface the gap and ask the user to refresh `/process`.

4. **Check if a plan already exists** locally at `/plan/{capability-id}/plan.md`. This *is* a
   local file — the plan output lives in the working repo, not in `banking-knowledge`. If it 
   exists, ask: "A plan already exists. Do you want to update it or start fresh?"

---

## Planning Framework

A capability plan is organized around **epics** — coherent chunks of business functionality 
that can be delivered incrementally. An epic:
- Delivers a meaningful business outcome (not a technical deliverable)
- Has a clear start and end condition
- Can be estimated in relative complexity (Small / Medium / Large / XL)
- Has identifiable dependencies on other epics or external capabilities

### Epics, not features

Good epic: "Establish the credit risk scoring baseline — enable underwriters to receive and 
interpret a risk score for standard loan applications."

Bad epic: "Build the risk API" or "Set up the database schema"

Epics should be named and defined so that a business owner can understand what will be 
deliverable when it's done.

---

## Step 1 — Understand the Capability

Before drafting the plan, ground yourself in the pack's `capability_self`,
`capability_definition`, and the `emitted_business_events` slices, then ask the user to 
validate the framing:

- "Looking at [capability name], what is the minimum version of this capability that delivers 
  business value? What would be true about the business on day 1 if this capability existed 
  in its simplest form?"
- "Among the events listed in `emitted_business_events` ([list them]), which is the most 
  critical to deliver first?"
- "Are there external dependencies — capabilities that must exist or expose data before this 
  one can function? (Cross-check against `consumed_business_events`.)"

---

## Step 2 — Draft Epics

Based on the FUNC ADR (`capability_definition`), the BCM data (`capability_self`,
`carried_objects`, `carried_concepts`), and the answers above, draft a set of 3-8 epics. 
Present them as a numbered list with a one-line description each. Ask the user to react 
before filling in the details.

For each epic, define:
- **Name**: clear, business-language title
- **Goal**: one sentence — what business outcome does this epic achieve?
- **Entry condition**: what must be true / done / available before this epic can start?
- **Exit condition** (Definition of Done): what is verifiably true when this epic is complete?
- **Complexity**: S / M / L / XL (relative estimation — no days or sprints)
- **Capabilities needed**: which other L2 capabilities must exist or be partially ready?
  Source this from `consumed_business_events[*].subscribed_event` (trace the event back to its
  emitting capability via another `bcm-pack pack` call if needed).
- **Key business events unlocked**: which events from `emitted_business_events` become 
  producible when this epic is done?

Ask the user to validate the epic sequence before writing the file:
> "Here's my proposed epic sequence for [capability]. Does the ordering make sense? 
> Are there any missing epics, or any that seem out of order?"

---

## Step 3 — Risk and Dependencies

For the full plan, identify:
- **Cross-capability dependencies**: from `consumed_business_events` — which other L2s does 
  this plan depend on? (Reference by capability ID.)
- **External dependencies**: third-party systems, data sources, regulatory approvals
- **Key risks**: the 2-3 assumptions that, if wrong, would derail this plan. Cross-check 
  against `governance_adrs` and `governing_urba` for hard constraints.
- **Recommended sequencing constraint**: which epics are truly sequential vs. which could 
  be run in parallel?

---

## Output

**File**: `/plan/{capability-id}/plan.md` (create directory if needed)

**Format**:

```markdown
# Plan — [Capability Name] ([Capability ID])

## Capability Summary
> [One-sentence capability responsibility from `capability_self[0].description`]

## Strategic Alignment
- Service offer: [from `product_vision`]
- Strategic L1: [from `capability_ancestors[0]`]
- BCM Zone: [from `capability_self[0].zoning`]
- Governing FUNC ADR: [from `capability_definition[*].id`]
- Strategic-tech anchors: [from `governing_tech_strat[*].id` and `tactical_stack[*].id`]

## Implementation Epics

### Epic 1 — [Name]
**Goal**: [One sentence]
**Entry condition**: [What must be true to start]
**Exit condition**: [What is verifiably true when done]
**Complexity**: [S/M/L/XL]
**Unlocks events**: [list of business events this epic enables]
**Dependencies**: [Capability IDs or external systems]

### Epic 2 — [Name]
[Same structure]

...

## Dependency Map

| Epic | Depends On | Type |
|------|-----------|------|
| Epic 2 | Epic 1 | Sequential |
| Epic 3 | CAP.REF.001 | Cross-capability |
...

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [Risk] | H/M/L | H/M/L | [Mitigation] |

## Recommended Sequencing
[Short narrative: which epics are on the critical path, which can run in parallel]

## Open Questions
- [Any decision that must be made before a specific epic can start]
- [Anything surfaced via `pack.warnings`]

## Knowledge Source
- bcm-pack ref: [the `--ref` used, default `main`]
- Capability pack mode: deep
- Pack date: [today's date]
```

After writing, tell the user:
> "The plan for [capability] is committed to `/plan/[capability-id]/plan.md`. 
> When you're ready, the task skill will break each epic into concrete tasks for 
> the implement-capability agent."
