---
name: bcm-writer
description: >
  Translates validated Functional ADRs into machine-readable YAML BCM artifacts following the 
  project's templates, then validates coherence using the /tools/ scripts. Use this skill 
  whenever the user wants to write or update BCM YAML files, produce capability artifacts, 
  translate ADR decisions into YAML, check BCM coherence, or run the validation tooling. 
  Trigger on: "write the BCM", "produce YAML", "BCM artifacts", "generate capabilities YAML", 
  "validate BCM", "run the tools", "translate ADRs to YAML", or any time one or more FUNC ADRs 
  exist in /func-adr/ and the user is ready to materialize them as structured data. Also 
  trigger proactively after the business capabilities brainstorming session completes.
---

# BCM Writer Skill

You are translating validated architectural decisions (Functional ADRs) into the machine-readable 
YAML artifacts that power the project's BCM tooling. This is a precision task — the YAML must 
conform exactly to the templates and pass all validation scripts.

**Your job**: Read ADRs → produce YAML → validate → report.
**Not your job**: Re-open architectural decisions already captured in ADRs.

---

## Domain Vocabulary Hierarchy

The BCM meta-model has **three levels of vocabulary** and **two levels of events**. Every artifact 
belongs to exactly one level. Confusing levels silently invalidates the model.

### Three-level vocabulary

```
CPT  (Business Concept)   — Pure definition. Zone-agnostic. Abstract.
 └── OBJ (Business Object) — Generic envelope. Zone-specific. Problem-space boundary.
      └── RES (Resource)    — Operational specialization. State machine. Business rules.
```

**Insurance analogy** (use as a mental model):
- CPT = "claim" — what a claim IS, abstractly
- OBJ = "claim declaration" — the generic declaration wrapper per problem space
- RES = "water damage claim form" — the specific operational form with its own state machine

**Rules:**
- A CPT is a cross-domain definition: it has no zone, no emitting capability, no data fields.
- An OBJ is owned by exactly one L2 capability (`emitting_capability`). It has typed `data` fields.
  Every OBJ.data field MUST be referenced by at least one RES via `business_object_property`.
- A RES is a specialization of exactly one OBJ (`business_object`). It adds fields specific to 
  its use case (not in the OBJ). It has its own state machine and business rules.
- The same CPT can be implemented by multiple OBJs (one per problem space / zone boundary).
- The same OBJ can have multiple RESs (one per operational specialization / lifecycle state).

**ID convention:**
- `CPT.<ZONE>.<L1>.<CODE>` — but zone is typically BCM (cross-cutting) or the zone of first use
- `OBJ.<ZONE>.<L1>.<CODE>` — zone of the owning L2 capability
- `RES.<ZONE>.<L1>.<CODE>` — zone of the owning L2 capability

### Two-level events and their mirror subscriptions

```
Business event (EVT)          — Abstract milestone. References an OBJ. Emitted by L2.
 └── Resource event (RVT)      — Operational fact. References a RES. Emitted by L2.

Business subscription (SUB.BUSINESS)  — Mirrors an EVT. Consumed by a different L2.
 └── Resource subscription (SUB.RESOURCE) — Mirrors a RVT. Must link to a SUB.BUSINESS.
```

**Rules:**
- A business event carries exactly one OBJ (`carried_business_object`).
- A resource event carries exactly one RES (`carried_resource`) and links to one business event (`business_event`).
- A business subscription references one EVT (`subscribed_event`) consumed by one L2 (`consumer_capability`).
- A resource subscription references one RVT (`subscribed_resource_event`) and MUST link to one business subscription (`linked_business_subscription`).
- Every business subscription MUST be referenced by at least one resource subscription.
- No L2 subscribes to its own events.

---

## Before You Begin

Gather context:

1. **Read all FUNC ADRs** in `/func-adr/` — these are the source of truth for this session.
2. **Read all existing URBA ADRs** in `/adr/ADR-BCM-URBA-*.md` — they constrain what is valid.
3. **Read all templates** in `/templates/`:
   - `capability-template.yaml` — capabilities at L1/L2/L3
   - `business-concept/template-business-concept.yaml` — CPT artifacts (`concepts` key)
   - `business-object/template-business-object.yaml` — OBJ artifacts (`resources` key)
   - `resource/template-resource.yaml` — RES artifacts (`resources` key)
   - `business-event/template-business-event.yaml` — business events
   - `business-event/template-business-subscription.yaml` — business event subscriptions
   - `resource-event/template-resource-event.yaml` — resource events
   - `resource-event/template-resource-subscription.yaml` — resource subscriptions
4. **Inspect `/tools/`** to understand available validation scripts:
   - `validate_repo.py` — structural validation of the full BCM
   - `validate_events.py` — event-specific validation
   - `semantic_review.py` — semantic coherence check
5. **Check existing `/bcm/` directory** (if it exists) for any already-produced YAML to avoid 
   duplication and to understand numbering conventions.

---

## Step 1 — Map ADR Decisions to YAML Artifacts

For each FUNC ADR, extract:
- All capability IDs declared (`impacted_capabilities` field)
- Their level (L1/L2/L3)
- Their zone (from `decision_scope.zoning`) — map ADR zone names to vocab.yaml zone names
- Their parent-child relationships
- Any events mentioned → will become OBJ + business events + resource events
- Any business objects mentioned → will become OBJ; identify which CPT they instantiate
- **Consumed events per L2** — from the `impacted_subscriptions` field in the ADR frontmatter,
  OR from the "Events consumed" column in the L2 event table in the ADR body.
  Each consumed event becomes one business subscription + one resource subscription.

**Zone name mapping** (ADR uses URBA-0001 names; YAML must use vocab.yaml names):
- SERVICES_COEUR → BUSINESS_SERVICE_PRODUCTION
- CANAL → CHANNEL
- PILOTAGE → STEERING
- REFERENTIEL → REFERENTIAL
- ECHANGE_B2B → EXCHANGE_B2B
- SUPPORT → SUPPORT
- DATA_ANALYTIQUE → DATA_ANALYTIQUE (add to vocab if missing — it is a valid URBA zone)

Build a table of artifacts to produce before writing any YAML. Present this table to the user 
and ask for confirmation: "I've identified these artifacts to produce from the ADRs. Does this 
look complete?"

The table must include a **Subscriptions** section showing:
| Consumer L2 | Subscribed event | Emitting L2 | SUB.BUSINESS ID | SUB.RESOURCE ID |
|-------------|-----------------|-------------|-----------------|-----------------|

---

## Step 2 — Write Capability YAML

Write capabilities to the appropriate file(s) in `/bcm/`. Follow the naming convention already 
present in the repository (e.g., `capabilities-L1.yaml`, `capabilities-[zone].yaml`).

```yaml
- id: CAP.[ZONE-ABBREV].[NNN]    # from ADR's impacted_capabilities
  name: [Name]                   # exact name from ADR
  level: L1 | L2 | L3
  parent: CAP.[ZONE-ABBREV].[NNN] # required for L2/L3, omit for L1
  zoning: [VOCAB_ZONE]           # must match vocab.yaml exactly
  description: [description]
  owner: [business owner]
  adrs:
    - ADR-BCM-FUNC-NNNN
```

**Zone abbreviations** in capability IDs (match existing conventions):
- BUSINESS_SERVICE_PRODUCTION → BSP
- CHANNEL → CAN
- STEERING → PIL
- REFERENTIAL → REF
- EXCHANGE_B2B → B2B
- SUPPORT → SUP
- DATA_ANALYTIQUE → DAT

---

## Step 3 — Propose and Write Vocabulary Artifacts (CPT → OBJ → RES)

Before writing YAML, present a three-level vocabulary proposal to the user:

### 3a — Business Concepts (CPT)

For each canonical domain concept identified in the ADRs:
- Name it at the highest level of abstraction (zone-agnostic)
- Write only: id, name, definition, scope (lifecycle steps), business_rules
- ID format: `CPT.BCM.000.<CODE>` for cross-cutting concepts

File: `bcm/business-concept-<domain>.yaml` (key: `concepts`)

### 3b — Business Objects (OBJ)

For each CPT, identify the problem spaces where it is materialized:
- One OBJ per zone/L2 boundary that owns a specific view of the concept
- Name each OBJ as a **functional noun phrase** (not the concept name repeated)
  - CPT "claim" → OBJ "claim declaration" (not "business claim")
  - The OBJ name describes **what you do with the concept** in this problem space
- Each OBJ is owned by exactly one L2 (`emitting_capability`)
- Define typed `data` fields — these define the contract that RES must implement
- ID format: `OBJ.<ZONE-ABBREV>.<L1-NUM>.<CODE>`

File: `bcm/business-object-<domain>.yaml` (key: `resources`)

**Constraint:** every OBJ.data field must be covered by at least one RES via `business_object_property`.

### 3c — Resources (RES)

For each OBJ, identify the operational specializations:
- One RES per lifecycle state, use case type, or variant that has distinct business rules
  - OBJ "claim declaration" → RES "water damage claim form" (specific form)
  - OBJ "programme participation" → RES "active file" + RES "closed file"
- Each RES references its parent OBJ (`business_object`)
- Each RES field references an OBJ field via `business_object_property` (if the field is shared)
  or introduces new fields (if specific to this specialization)
- ID format: `RES.<ZONE-ABBREV>.<L1-NUM>.<CODE>`

File: `bcm/resource-<domain>.yaml` (key: `resources`)

---

## Step 4 — Write Events and Subscriptions

### Step 4a — Business events (EVT)

For every L2 capability that has events in the ADRs:
- Each event references an OBJ via `carried_business_object`
- Named in past tense, domain language
- Include: id, version (start at 1.0.0), emitting_capability, carried_business_object

File: `bcm/business-event-<domain>.yaml` (key: `business_events`)

### Step 4b — Resource events (RVT)

For each business event, write the corresponding resource event:
- References a RES via `carried_resource`
- Links back to the business event via `business_event`

File: `bcm/resource-event-<domain>.yaml` (key: `resource_events`)

### Step 4c — Business subscriptions (SUB.BUSINESS)

For every consumed event identified in Step 1 (per L2):

```yaml
- id: SUB.BUSINESS.<ZONE-ABBREV>.<L1-NUM>.<CODE>
  consumer_capability: CAP.<ZONE-ABBREV>.<L2-ID>   # the L2 that consumes

  subscribed_event:
    id: EVT.<ZONE-ABBREV>.<L1-NUM>.<CODE>           # the EVT produced by the emitter
    version: 1.0.0                                   # must match the EVT version
    emitting_capability: CAP.<ZONE-ABBREV>.<L2-ID>  # L2 that emits (NOT the consumer)

  scope: public                                      # public | private
  rationale: >-
    [Why this L2 needs to react to this event — what lifecycle impact does it have?]

  adrs:
    - ADR-BCM-FUNC-NNNN
  tags:
    - business
```

**Rules:**
- `consumer_capability` ≠ `subscribed_event.emitting_capability` (no self-subscription)
- `subscribed_event.id` must reference an EVT written in Step 4a
- `subscribed_event.version` must match the version of that EVT exactly
- One subscription per (consumer, event) pair — do not aggregate multiple events into one subscription

File: `bcm/business-subscription-<domain>.yaml` (key: `business_subscriptions`)

### Step 4d — Resource subscriptions (SUB.RESOURCE)

For each business subscription written in Step 4c, write the corresponding resource subscription:

```yaml
- id: SUB.RESOURCE.<ZONE-ABBREV>.<L1-NUM>.<CODE>
  consumer_capability: CAP.<ZONE-ABBREV>.<L2-ID>
  linked_business_subscription: SUB.BUSINESS.<ZONE-ABBREV>.<L1-NUM>.<CODE>  # the matching 4c entry

  subscribed_resource_event:
    id: RVT.<ZONE-ABBREV>.<L1-NUM>.<CODE>           # the RVT that corresponds to the EVT above
    emitting_capability: CAP.<ZONE-ABBREV>.<L2-ID>
    linked_business_event: EVT.<ZONE-ABBREV>.<L1-NUM>.<CODE>  # the EVT from the business subscription

  scope: public                                      # public | private
  rationale: >-
    [Operational justification — what data/state does the consumer need from the RES?]

  adrs:
    - ADR-BCM-FUNC-NNNN
  tags:
    - resource
    - subscription
```

**Rules:**
- `linked_business_subscription` must reference a SUB.BUSINESS written in Step 4c
- `subscribed_resource_event.id` must reference an RVT written in Step 4b
- `subscribed_resource_event.linked_business_event` must match the EVT in the business subscription
- Every business subscription (Step 4c) must have at least one resource subscription here

File: `bcm/resource-subscription-<domain>.yaml` (key: `resource_subscriptions`)

If the ADR mentions consumed events but doesn't fully specify the emitting L2, flag as governance debt:
> "The ADR for [consumer L2] mentions consuming [event name] but the emitting capability isn't 
> clearly identified. I'll mark this as TODO — confirm the emitter before writing the subscription YAML."

---

## Step 5 — Run Validation

After producing the YAML files:

```bash
python tools/validate_repo.py
```

Read the output carefully. Fix every error before proceeding. Common errors:
- Missing `parent` field on L2/L3
- Invalid zone value (check against vocab.yaml)
- OBJ.data field not referenced by any RES via `business_object_property`
- Business event references an OBJ that doesn't exist
- Resource event references a RES that doesn't exist
- Parent capability not found (ID typo)
- Business subscription references an EVT that doesn't exist or wrong version
- Resource subscription references an RVT that doesn't exist
- Resource subscription's `linked_business_subscription` not found
- Resource subscription's `linked_business_event` doesn't match the business subscription's event
- Business subscription not referenced by any resource subscription

Report the final validation result to the user.

---

## Step 6 — Coherence Summary

```markdown
## BCM Coherence Report

### Capabilities produced
- [N] L1 capabilities across [N] zones
- [N] L2 capabilities
- [N] L3 capabilities (if any)

### Vocabulary
- [N] CPT (business concepts) defined
- [N] OBJ (business objects) defined — [N] L2s without an OBJ (governance debt)
- [N] RES (resources) defined — [N] OBJs without a RES (validation will fail)

### Events
- [N] business events (EVT) defined
- [N] resource events (RVT) defined
- [N] L2 capabilities without events (governance debt)

### Subscriptions
- [N] business subscriptions (SUB.BUSINESS) defined
- [N] resource subscriptions (SUB.RESOURCE) defined
- [N] L2 capabilities that consume events but have no subscription written (governance debt)
- [N] business subscriptions without a matching resource subscription (validation will fail)

### Validation result
[Pass / Warnings / Errors + details]

### Recommended next steps
- [ ] Complete vocabulary for: [list of L2s with no OBJ]
- [ ] Add RES for: [list of OBJs with no covering RES]
- [ ] Complete event definitions for: [list]
- [ ] Confirm emitter for unresolved subscriptions: [list]
```

Tell the user:
> "The BCM YAML is produced and validated. The next step is the plan skill, which will 
> break each L2 capability into an implementation roadmap with epics and milestones."

---

## Operating Principles

- **Precision over speed.** One wrong field silently propagates. Read templates carefully.
- **Never invent.** If a field value isn't in the ADR, either leave it with a TODO marker 
  or ask the user.
- **Fix, don't skip.** If validation fails, fix the YAML — don't work around validation.
- **Cite ADRs.** Every capability in the YAML must reference the ADR(s) that decided it.
- **Read before write.** Before creating any file, check if it already exists and what's in it.
- **Propose before write.** For CPT/OBJ/RES, present the vocabulary proposal and get user 
  confirmation before writing YAML.
- **Subscriptions are mandatory.** Every consumed event must produce both a SUB.BUSINESS and 
  a SUB.RESOURCE. Missing subscriptions are not governance debt — they are validation failures.
