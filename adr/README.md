# ADR — Architecture Decision Records (BCM)

This folder contains all formalized decisions related to the BCM (Business Capability Map).

Every evolution of the model must be tracked by an ADR.

An undocumented modification is not considered valid.

---

## Purpose of ADRs

ADRs allow:

- Explicit recording of decisions made
- Preservation of context and rejected alternatives
- Avoidance of implicit model drift
- Auditability of evolutions
- Stabilization of BCM governance

The BCM evolves only through formalized decisions.

---

## ADR Taxonomy

ADRs are organized according to three complementary families:

### 1. GOV — Governance

Define the institutional framework of the model:

- Organization of the BCM board
- Arbitration processes
- Validation rules
- Decision lifecycle
- Anti-dogma principles

These ADRs structure **the way decisions are made**.

---

### 2. URBA — Structuring Principles

Define the global rules for urbanization and modeling:

- Zoning
- L1/L2/L3 levels
- "1 capability = 1 responsibility" rule
- Logical / physical decoupling
- Event-driven principles

These ADRs define **the rules of the model**.

### Identifier convention to follow

URBA/FUNC ADRs that introduce or modify assets must follow this convention:

- `CAP.*` for capabilities
- `EVT.*` for events
- `OBJ.*` for business objects
- `RES.*` for resources
- `ABO.METIER.*` for business subscriptions
- `ABO.RESSOURCE.*` for resource subscriptions

Expected coherence rule: a resource (`RES.*`) implements a business object (`OBJ.*`),
and does not substitute for it. Expected cardinalities:
- a resource references **exactly one** business object;
- a resource event references **exactly one** business event.

---

### 3. FUNC — Functional Decisions

Apply URBA principles to concrete cases:

- Split / merge of capabilities
- Scope adjustment
- Creation or deletion of L3
- Evolution of business events
- Placement of a capability in a zone

These ADRs define **the operational evolution of the model**.

---

## Decision Hierarchy

The decision hierarchy is as follows:

```text
GOV
  ↓
URBA
  ↓
FUNC
```

Associated rules:

- A FUNC ADR cannot contradict a URBA ADR.
- A URBA ADR must respect the principles defined by GOV.
- A GOV ADR can only be replaced by another GOV ADR.
- Any BCM modification must go through an Accepted ADR.

### Classification rule

```text
Does this decision concern the way decisions are made?
→ GOV

Does this decision change the global rules of the model?
→ URBA

Does this decision apply the rules to a specific scope?
→ FUNC
```
## Impacted Mappings

The `impacted_mappings` field of the YAML header indicates **which mapping axes** are affected by the decision. It allows anticipating impacts beyond the BCM itself.

| Value | Mapping Axis | Examples of impacts |
|--------|---------------------|---------------------|
| `SI`   | Application mapping | Applications to rewire, modules to rename, components to split |
| `DATA` | Data mapping | Data flows to modify, data domains to realign, affected referentials |
| `ORG`  | Organizational mapping | Teams to reassign, roles to redefine, operational responsibilities to adjust |

**Usage rule:**
- Always fill in at least one value if the decision has a concrete impact beyond the BCM model.
- Leave empty (`[]`) only for purely conceptual ADRs with no direct impact on the IS, data, or organization.
- A FUNC ADR will almost always have at least `SI` filled in.

---
## ADR Structure

Each ADR contains:

Structured metadata (YAML header)

- A context
- A testable decision
- A justification
- The impacts on the BCM
- The consequences
- The traceability

The official template must be used.

---


## Lifecycle

Possible statuses:

- Proposed: under discussion
- Accepted: validated
- Deprecated: obsolete
- Superseded: replaced

An Accepted ADR constitutes the official reference.

---

## BCM Board

ADRs are reviewed and arbitrated by the BCM Board.

Composition:

- IS Architects
- Lead Business Analysts
- Urbanist responsible for coherence

The board:

- Ensures cross-cutting coherence
- Integrates field feedback
- Rules on proposals
- Documents decisions

Evolutions may be proposed by project teams, notably through Event Storming Big Picture feedback.

---

Evolutivity Principle

The BCM is a living model.

No rule is immutable.
Any ADR can be challenged.

The guiding principle is:

Model coherence must never take precedence over business value.

---

## Proposing an ADR

1. Create a file ADR-BCM-<GOV|URBA|FUNC>-<NNNN>.md
2. Use the official template
3. Fill in the metadata
4. Set the status to Proposed
5. Present to the BCM Board

---

What ADRs are NOT

- Not meeting minutes
- Not project tickets
- Not application technical documents

They document model decisions.

---

## Best Practices

- One decision = one ADR
- Be explicit and testable
- Document rejected alternatives
- Maintain traceability
- Link every modification of the capabilities.yaml file to an Accepted ADR

### What is a good practice in a FUNC ADR

Include precise decisions when they concern:
 * the **scope** of a capability;
 * the **boundaries** between capabilities;
 * the **responsibilities**;
 * the **transfer points**;
 * the **attachment rules** for business objects;
 * the **naming of events** when that naming has a contractual scope or resolves a lasting ambiguity.

This is exactly what your ADRs already do correctly on DSP and IND.

### What becomes a bad practice

It becomes a bad practice if the FUNC ADR descends to:

* the detailed execution order of processing variants;
* business cases too fine-grained or specific to one product line;
* exhaustive payloads;
* rules that will likely change in a workshop or during implementation;
* sequencing or orchestration choices that belong more to solution design than to a stable functional decision.

### The practical test

To decide whether a detail deserves to be in a FUNC ADR, ask yourself three questions:

1. If we don't write it down, does the boundary between teams or capabilities become ambiguous again?
If yes, include it.
2. Does this point have a contractual scope on SI / DATA / ORG?
If yes, include it.
3. Do we think this detail must remain stable beyond the current workshop?
If no, leave it out of the ADR.
