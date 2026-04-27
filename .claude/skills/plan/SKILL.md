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
(from the BCM/ADRs) and the task generation phase.

**Absolute constraint**: No code, no technical architecture. The plan is in business capability 
language. The "how" emerges in the task phase.

---

## Before You Begin

1. **Identify which capability to plan.** The user should specify the capability ID (e.g., 
   `CAP.COEUR.001.SUB`) or a name. If ambiguous, list all plannable L2/L3 capabilities 
   from the BCM and ask the user to select.

2. **Read the relevant files:**
   - The capability's YAML in `/bcm/` (for the full capability definition)
   - The corresponding FUNC ADR(s) in `/func-adr/` (for the decisions and context)
   - `/strategic-vision/strategic-vision.md` (for strategic alignment)
   - `/product-vision/product.md` (for the north star service offer)
   - Any existing plan files in `/plan/` to avoid duplication or inconsistency

3. **Check if a plan already exists** for this capability at `/plan/{capability-id}/plan.md`. 
   If so, ask: "A plan already exists. Do you want to update it or start fresh?"

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

Before drafting the plan, ask the user to validate the capability framing:

- "Looking at [capability name], what is the minimum version of this capability that delivers 
  business value? What would be true about the business on day 1 if this capability existed 
  in its simplest form?"
- "What are the business events this capability must be able to produce by the end? Which 
  is the most critical to deliver first?"
- "Are there external dependencies — capabilities that must exist or expose data before this 
  one can function?"

---

## Step 2 — Draft Epics

Based on the ADR, BCM YAML, and the answers above, draft a set of 3-8 epics. Present them 
as a numbered list with a one-line description each. Ask the user to react before filling 
in the details.

For each epic, define:
- **Name**: clear, business-language title
- **Goal**: one sentence — what business outcome does this epic achieve?
- **Entry condition**: what must be true / done / available before this epic can start?
- **Exit condition** (Definition of Done): what is verifiably true when this epic is complete?
- **Complexity**: S / M / L / XL (relative estimation — no days or sprints)
- **Capabilities needed**: which other L2 capabilities must exist or be partially ready?
- **Key business events unlocked**: which events from the BCM become producible when this 
  epic is done?

Ask the user to validate the epic sequence before writing the file:
> "Here's my proposed epic sequence for [capability]. Does the ordering make sense? 
> Are there any missing epics, or any that seem out of order?"

---

## Step 3 — Risk and Dependencies

For the full plan, identify:
- **Cross-capability dependencies**: which other L2s does this plan depend on? (Reference by 
  capability ID)
- **External dependencies**: third-party systems, data sources, regulatory approvals
- **Key risks**: the 2-3 assumptions that, if wrong, would derail this plan
- **Recommended sequencing constraint**: which epics are truly sequential vs. which could 
  be run in parallel?

---

## Output

**File**: `/plan/{capability-id}/plan.md` (create directory if needed)

**Format**:

```markdown
# Plan — [Capability Name] ([Capability ID])

## Capability Summary
> [One-sentence capability responsibility from BCM YAML]

## Strategic Alignment
- Service offer: [from product.md]
- Strategic L1: [from strategic-vision.md]
- BCM Zone: [zone]
- Governing ADRs: [list of FUNC ADR IDs]

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
```

After writing, tell the user:
> "The plan for [capability] is committed to `/plan/[capability-id]/plan.md`. 
> When you're ready, the task skill will break each epic into concrete tasks for 
> the implement-capability agent."
