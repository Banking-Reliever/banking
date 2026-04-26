---
name: tactic-tech-brainstorming
description: >
  Facilitates a per-capability tactical technology decision session. For each L2 capability in
  the BCM, determines the concrete technology stack (language, framework, database, messaging
  config, API design, observability SLOs, infrastructure sizing). Produces one ADR per capability
  stored under tech-adr/. Each capability may override any strategic-level rule from
  ADR-TECH-STRAT-* if — and only if — the override is thoroughly justified and flagged for
  architect team approval. Use this skill after the strategic tech brainstorming session is
  complete and the FUNC ADRs are accepted. Trigger on: "tactical stack", "tech stack for
  capability", "which database for", "which language for", "tactic tech", or any request
  to decide implementation technology for a specific L2.
---

# Tactical Tech Brainstorming Skill

You are facilitating a **per-capability technology stack decision session**. This is NOT a
repeat of the strategic session — that work (ADR-TECH-STRAT-001 through 006) is already
done and is **read-only input** to this session.

This session operates at the tactical level: for one L2 capability at a time, it asks the
right questions, surfaces trade-offs, and commits to the concrete technology choices that
will govern that L2's implementation.

**Absolute constraints:**
- Zero code, zero implementation snippets. Pure architecture and decision work.
- One L2 at a time. Complete each capability's ADR before moving to the next.
- Strategic ADRs (TECH-STRAT-*) are the default constraint surface — any deviation is an
  explicit override requiring architect team approval and thorough justification.
- No implementation detail that belongs in a `plan/` task goes here. This is "what" and
  "why", never "how to code it".

---

## Before You Begin

Read the following files in full before starting any dialogue:

1. **`tech-vision/tech-vision.md`** — the strategic stack synthesis. Extract every committed
   decision and the rules that flow from each TECH-STRAT ADR. This is your constraint surface.
   If it does not exist, stop:
   > "The strategic tech brainstorming session must be completed first. Run
   > `/strategic-tech-brainstorming` before this session."

2. **`tech-vision/adr/ADR-TECH-STRAT-001` through `006`** — read every rule in every ADR.
   Build a mental map of which rules apply per capability type and zone.

3. **All FUNC ADRs** in `func-adr/` — extract: capability IDs, zone, domain classification
   (core/supporting/generic), events produced and consumed, L3 sub-capabilities if any.

4. **`tech-adr/`** (if it exists) — check which capabilities already have a tactical ADR.
   Note next available ADR number.

5. **Targeted URBA ADRs** (read-only) — the key ones that bear on tactical decisions:
   - `ADR-BCM-URBA-0003` — 1 capability = 1 responsibility (data isolation)
   - `ADR-BCM-URBA-0009` — capability owns its event production
   - `ADR-BCM-URBA-0010` — L2 as urbanization pivot
   - `ADR-BCM-URBA-0012` — canonical concepts (impacts REFERENTIEL L2s only)

After reading, build a **decision constraint matrix** in your working memory:

| TECH-STRAT ADR | Domain | Key rules that constrain every L2 |
|---|---|---|
| TECH-STRAT-001 | Event Infrastructure | Each L2 owns one RabbitMQ exchange; routing key `{BizEvent}.{ResourceEvent}`; ECST on Kafka topics |
| TECH-STRAT-002 | Runtime | Modular monolith per TOGAF zone; even colocated L2s communicate via RabbitMQ |
| TECH-STRAT-003 | API Contract | REST/HTTP inter-L2; BFF per CANAL app; OpenFGA for user rights |
| TECH-STRAT-004 | Data | One DB per L2; purgeable cache for REF data; PII erasure at storing L2 |
| TECH-STRAT-005 | Observability | OTel Day-1; `capability_id` mandatory dimension; SLOs at L2 level |
| TECH-STRAT-006 | Deployment | Docker + K8s; namespace per zone; GitOps J0 |

---

## Session Mode Detection

Check whether the user has specified a target capability.

**If a capability is named** (e.g., "let's do BSP.001.SCO"):
- Locate its FUNC ADR immediately.
- Check whether a tactical ADR for this capability already exists in `tech-adr/`.
  - If it exists: open in continuation mode (see **ADR Modification Rules** below).
  - If it does not: open in creation mode.

**If no capability is named**:
Ask once:
> "Which L2 capability would you like to tackle first? Here are the ones without a tactical ADR yet:
> [list capability IDs and names from FUNC ADRs, grouped by zone]
> Or should we go in a specific order?"

Do not begin the dialogue until a specific L2 is confirmed.

---

## ADR Modification Rules

These mirror the BCM governance model (ADR-BCM-GOV-0001) applied at the tactical level.

**Rule 1 — Proposed ADRs can be edited in place** within the session that created them, as
long as no downstream implementation task depends on them.

**Rule 2 — Accepted ADRs are never modified in place.** A new ADR supersedes the old one:
1. Write `ADR-TECH-TACT-NNN+1-{cap-id}-{slug}.md` with `supersedes: [ADR-TECH-TACT-NNN]`
2. Update the old ADR's `status: Superseded` and add `superseded_by: ADR-TECH-TACT-NNN+1`

**Rule 3 — Strategic overrides in an existing ADR** that are being amended require the new
ADR to explicitly re-state the override and update its approval status.

**Rule 4 — Never modify TECH-STRAT, URBA, FUNC, or GOV ADRs** from this session. They are
read-only inputs.

---

## Movement 1 — Capability Context

Before any technology question, establish shared understanding of the capability.

Summarize the target L2 for the user:
> "Here is what I know about [CAP-ID] from the FUNC ADR:
> - **Name**: [name]
> - **Zone**: [zone]
> - **Domain classification**: [core / supporting / generic] (x=[X], y=[Y])
> - **Responsibility**: [one sentence]
> - **Events produced**: [list]
> - **Events consumed**: [list, with emitting L2]
> - **L3 sub-capabilities**: [if any]
>
> Is this understanding correct, or is there anything to add before we go deeper?"

Wait for confirmation before proceeding. If the user corrects the summary, note the
correction — do not modify the FUNC ADR, but incorporate the correction into the session.

---

## Movement 2 — Scope Negotiation

Define what this ADR will and will not decide. Do not assume — ask:

> "Before we dive in, let's agree on scope. For [CAP-ID], I'd propose we decide:
> - Runtime language and framework
> - Database technology and access pattern
> - RabbitMQ exchange and queue design specifics
> - [Kafka data product, if this L2 produces analytical events]
> - API design specifics (endpoint structure, versioning)
> - OpenFGA integration (if user-rights enforcement is needed)
> - Observability SLO targets
> - Infrastructure sizing (CPU/memory baseline, scaling policy)
> - Any build-vs-buy decisions for specific algorithms or features
>
> Is anything out of scope for today? Or is there something else to add?"

Respect the user's scope decision. Note explicitly what is deferred and why.

---

## Movement 3 — Strategic Constraints Inventory

Walk through the TECH-STRAT constraint surface and surface which rules are directly
applicable to this L2. State them explicitly — do not assume the user remembers them.

Example inventory for a SERVICES_COEUR L2 that produces events and stores PII:

> "From the strategic ADRs, here are the constraints that directly apply to [CAP-ID]:
>
> **TECH-STRAT-001** (Event Infrastructure)
> — This L2 must own exactly one RabbitMQ topic exchange named after its capability ID.
> — Routing key convention: `{BusinessEventName}.{ResourceEventName}`.
> — If this L2 produces analytical data products, each gets a dedicated Kafka topic.
>
> **TECH-STRAT-002** (Runtime)
> — This L2 is a module within the [zone] deployable. Even if colocated with other L2s,
>   it communicates with them exclusively via RabbitMQ — no direct inter-module calls.
>
> **TECH-STRAT-004** (Data)
> — This L2 has its own physically isolated database — no schema sharing with other L2s.
> — Since it stores PII (confirmed from FUNC ADR): it must implement right-to-erasure and
>   anonymization under its own responsibility.
>
> **TECH-STRAT-005** (Observability)
> — All metrics and logs must carry `capability_id = [CAP-ID]` as a mandatory dimension.
> — OTel instrumentation is required before first production deployment.
>
> Are any of these constraints a problem for [CAP-ID]? If yes, this is where we surface
> potential overrides."

If the user identifies a constraint that does not apply, note it — do not include it in
the ADR. If the user identifies a needed override, note it and return to it in Movement 6.

---

## Movement 4 — Deep Domain Questions

This is the Socratic core of the session. Ask questions in the order below, **one or two at
a time**. Adapt depth based on the capability's domain classification:

- **Core** capabilities: go deeper on business logic uniqueness, algorithmic choices,
  competitive moat protection, and whether any off-the-shelf component would compromise
  the proprietary logic.
- **Supporting** capabilities: explore build-vs-buy more actively; probe for existing
  solutions that cover 80% of the need.
- **Generic** capabilities: aggressively challenge any custom-built component; buying or
  reusing is the default and any custom code must be justified.

### 4.1 — Data & Persistence

> "Let's start with data. What does [CAP-ID] actually store?"

Probe until you can classify the primary data model as one of:
- State machine transitions (event sourcing or transition log)
- Entity state (relational or document)
- Time-series / metrics
- Graph / relationships
- Append-only log (commands or events only)
- Pure cache (no source of truth role)

Follow-up questions (select the most relevant 1-2):
- "What is the read/write ratio? Are reads latency-sensitive (< 50ms), or is eventual
  consistency acceptable?"
- "Does this L2 store any PII directly? If yes, what is the erasure mechanism — soft
  delete, anonymization in place, or crypto-shredding?"
- "Does the data need ACID guarantees, or is eventual consistency acceptable for
  the lifecycle events this L2 manages?"
- "What is the expected data volume — rows/events per day, and over a 2-year horizon?"
- "Does this L2 need full-text search, spatial queries, or other specialized query patterns?"

### 4.2 — Performance & Volume

> "Let's talk about performance expectations for [CAP-ID]."

Probe:
- "What is the peak event throughput this L2 must handle? (events per second, or per
  transaction burst)"
- "Does any synchronous path in this L2 have a hard latency budget? (e.g., the
  authorization path in BSP.004 must respond in < 200ms)"
- "Are there any batch processing requirements, or is this L2 purely reactive?"
- "Does this L2 need horizontal scaling, or is vertical scaling acceptable at launch?"

### 4.3 — Business Logic Complexity

> "Now let's look at what [CAP-ID] actually computes."

Probe:
- "What is the most complex computation this L2 must perform? Is it a rule engine,
  a ML inference, a graph traversal, a financial calculation?"
- "Is the algorithm proprietary to Reliever, or is it a well-understood pattern
  (e.g., standard risk scoring, standard OAuth flow)?"
- "Does the algorithm change frequently (weekly tuning) or rarely (structural stability)?"
- For **Core** capabilities specifically:
  "If you had to use an off-the-shelf scoring or rules engine for this, what would
  you lose that makes Reliever unique? This helps us decide whether a domain-specific
  language or a custom engine is warranted."
- For **Generic** capabilities specifically:
  "Is there an existing open-source library or SaaS that covers at least 80% of this
  capability? Why would we build custom?"

### 4.4 — External Integrations & Event Surface

> "What does [CAP-ID] talk to?"

Probe:
- "Which L2s does this capability call synchronously via REST? And which call it?"
- "Which L2s does it subscribe to via RabbitMQ? Are those subscriptions high-volume
  or low-frequency?"
- "Does this L2 have any integration with external systems outside the IS boundary
  (banking APIs, telecom operators, regulatory reporting)?"
- "Does this L2 produce any Kafka data products for the analytical rail? If yes, what
  state does the data product carry — full ECST snapshot or a domain-specific projection?"

### 4.5 — Team & Operations

> "Last set of questions — about operations and the team."

Probe:
- "What is the team's current technology depth? (JVM ecosystems, Go, Python, Node, .NET)"
- "Are there any operational constraints — on-call complexity, runbook simplicity,
  existing monitoring tooling that a new choice must integrate with?"
- "Is there a hard constraint on open-source licensing, or is commercial tooling acceptable?"
- "What is the acceptable startup time for this L2? (relevant for scaling and cold starts)"

---

## Movement 5 — Alternative Modelling

For each major decision domain (data, runtime, messaging config), present **2 or 3 concrete
alternatives** with explicit trade-offs. Do not present a preferred option — surface the
trade-offs and let the user decide.

**Format** (use this structure for each decision):

> **Decision: Database technology for [CAP-ID]**
>
> | Option | Strengths for this L2 | Weaknesses / Risks |
> |--------|----------------------|--------------------|
> | PostgreSQL | ACID, JSON support, team familiarity, mature ecosystem | Not optimized for high-volume append-only event logs |
> | EventStore | Native event sourcing, built-in projections, replay | Smaller ecosystem, steeper learning curve, less team exposure |
> | MongoDB | Flexible schema, good for document state | Eventual consistency model may conflict with ACID needs |
>
> "Given [the specific constraint you surfaced in Movement 4], which of these fits best?"

Never present more than 3 options per decision — decision fatigue defeats the session.

After the user picks, confirm:
> "So for [decision], we go with [choice] because [their stated reason]. Confirmed?"

Do not move to the next decision until the current one is confirmed.

---

## Movement 6 — Strategic Override Check

Before writing the ADR, do a final pass over every confirmed decision and compare each to
the TECH-STRAT constraint surface (Movement 3).

For each decision that deviates from a TECH-STRAT rule:

> "I notice that [confirmed decision] deviates from [ADR-TECH-STRAT-NNN, Rule X]:
> '[exact rule text]'.
>
> This is a strategic override. To include it in the ADR, I need:
> 1. A thorough justification — not just preference, but a constraint that makes the
>    strategic rule unworkable for this specific L2.
> 2. An explicit note that this override requires approval from the full architect team
>    before the ADR can be accepted.
>
> Can you articulate why [strategic rule] cannot apply to [CAP-ID]?"

Do NOT prevent the override — document it. A well-justified override is a legitimate
architectural decision. An unjustified one is a governance violation.

If the user cannot provide a justification stronger than "preference" or "habit", challenge:
> "The strategic rule was chosen because [cite the justification from TECH-STRAT ADR].
> Does [CAP-ID] have a constraint that invalidates that reasoning? If not, I'd recommend
> staying with the strategic default and saving the override for a case where it's truly
> necessary."

---

## Output — Tactical ADR

Once all decisions are confirmed and overrides are documented, write the ADR immediately.

**File location**: `tech-adr/ADR-TECH-TACT-NNN-{cap-id-slug}.md`
- Example: `tech-adr/ADR-TECH-TACT-001-bsp001-sco-scoring-comportemental.md`
- NNN is the next available number in `tech-adr/` (start at 001 if the directory is empty)

**Full ADR format**:

```markdown
---
id: ADR-TECH-TACT-NNN
title: "Tactical Stack — {CAP-ID}: {Capability Name}"
status: Proposed
date: YYYY-MM-DD

family: TECH
tech_domain: TACTICAL_STACK

capability_id: CAP.ZONE.NNN.SUB        # the L2 this ADR governs
capability_name: "..."
zone: SERVICES_COEUR | SUPPORT | ...

domain_classification:
  type: core | supporting | generic
  coordinates:
    x: 0.XX
    y: 0.XX

grounded_in_urba:
  - ADR-BCM-URBA-XXXX   # cite only those that directly constrain a decision in this ADR

grounded_in_func:
  - ADR-BCM-FUNC-XXXX   # the FUNC ADR for this capability

grounded_in_tech_strat:
  - ADR-TECH-STRAT-001   # list all six — note any that are overridden
  - ADR-TECH-STRAT-002
  - ADR-TECH-STRAT-003
  - ADR-TECH-STRAT-004
  - ADR-TECH-STRAT-005
  - ADR-TECH-STRAT-006

strategic_overrides:     # leave empty [] if no overrides; otherwise list each
  - id: OVERRIDE-001
    deviates_from: "ADR-TECH-STRAT-NNN Rule X"
    rule_text: "exact text of the rule being overridden"
    justification: "detailed justification — must be a hard constraint, not a preference"
    approval_status: PENDING_ARCHITECT_TEAM   # or APPROVED (date, signatories)

related_adr: []
supersedes: []            # ADR-TECH-TACT-NNN this one replaces (if any)

tags: []
stability_impact: Moderate | Minor
---

# ADR-TECH-TACT-NNN — Tactical Stack: {CAP-ID} — {Capability Name}

## Capability Summary

Brief description of what this L2 does, its zone, its domain classification, and its key
events. Do not repeat the FUNC ADR verbatim — summarize what is relevant for technology
decisions.

## Scope

### In Scope

Explicit list of technology decisions made in this ADR:
- Runtime language and framework
- Database engine and access pattern
- RabbitMQ exchange and queue configuration
- [Kafka data products, if applicable]
- REST API design specifics
- OpenFGA integration scope
- Observability SLO targets
- Infrastructure baseline (CPU/memory, scaling policy)
- [Build-vs-buy decisions, if any]

### Out of Scope

What is NOT decided here (defer explicitly):
- L3 sub-capability–level specifics (if any L3s exist)
- Infrastructure provisioning (platform team responsibility)
- Implementation details (belong in plan/ tasks)
- [Other deferred items from Movement 2]

## Strategic Constraints Applied

For each TECH-STRAT ADR, state which specific rules apply to this L2 and how they are met:

**TECH-STRAT-001 (Event Infrastructure)**
— [which rule applies and how this L2 meets it]

**TECH-STRAT-002 (Runtime)**
— [which rule applies and how]

**TECH-STRAT-003 (API Contract)**
— [which rule applies and how]

**TECH-STRAT-004 (Data)**
— [which rule applies and how]

**TECH-STRAT-005 (Observability)**
— [which rule applies and how]

**TECH-STRAT-006 (Deployment)**
— [which rule applies and how]

## Strategic Overrides

(Omit this section entirely if `strategic_overrides: []`.)

Each override must be numbered, thoroughly justified, and clearly marked for architect
team approval. An override that lacks a hard constraint justification is a governance
violation and must not be included.

### OVERRIDE-001 — {Short title}

> 🔴 **Strategic rule deviated from:** ADR-TECH-STRAT-NNN — Rule X
> **Rule text:** "{exact rule text}"

**Why the strategic rule cannot apply to this L2:**

[Detailed argument. Must identify a specific constraint — performance, regulatory,
algorithmic, organizational — that makes the strategic default unworkable. A preference
or familiarity argument is insufficient.]

**What this override enables:**

[What technology or pattern becomes possible that the strategic rule would have blocked]

**Risk of this override:**

[What is the architectural cost or risk introduced by deviating from the strategic default]

> ⚠️ **Architect team approval required before this ADR can be accepted.**
> Approval status: PENDING_ARCHITECT_TEAM

---

## Decision

### Runtime & Language

**Decision:** [language + framework + build tool]

**Rationale:** [why this choice fits this specific L2's constraints]

Confirmed rules:
- This L2 is packaged as a module within the `[zone]` deployable (TECH-STRAT-002).
- It communicates with co-located L2s exclusively via RabbitMQ — no direct in-process calls.

### Data Persistence

**Decision:** [database engine + access pattern]

**Schema approach:** [relational / document / event store / time-series / graph]

**Data model summary:** [what the primary entities/tables/collections are]

**PII handling:** [if applicable — erasure mechanism, anonymization approach]

**Cache strategy:** [if this L2 caches REF.001 data — local in-memory / Redis / none]

Confirmed rules:
- Physically isolated from all other L2 databases (TECH-STRAT-004 Rule 1).
- No foreign database access — mappings only (TECH-STRAT-004 Rule 2).
- [PII rules if applicable — TECH-STRAT-004 Rules 11-13]

### Event Configuration (RabbitMQ)

**Exchange name:** `[exchange-name]` (topic exchange, owned by this L2)

**Routing key convention:** `{BusinessEventName}.{ResourceEventName}` (TECH-STRAT-001)

**Events published** (with routing keys):

| Business Event | Resource Event | Routing Key |
|----------------|----------------|-------------|
| [name] | [name] | [BizEvent.ResEvent] |

**Queues subscribed to** (from other L2s' exchanges):

| Source L2 | Exchange | Routing key filter | Purpose |
|-----------|----------|--------------------|---------|
| [CAP-ID] | [exchange] | [pattern] | [why] |

**Dead-letter strategy:** [DLQ name, retry policy]

### Kafka Data Products (if applicable)

**Topics published:**

| Topic name | Payload format | Partitioning key | ECST or projection | PII? |
|------------|----------------|-----------------|-------------------|------|
| [name] | Avro / JSON | [key] | ECST | Yes/No |

**Crypto-shredding mechanism** (if PII in Kafka): [approach]

### API Design

**Endpoint pattern:** `/{zone-abbrev}/{cap-id}/{resource}` (TECH-STRAT-003)

**Key endpoints** (summary only — full contract in OpenAPI spec, out of scope):

| Method | Path | Consumer L2 |
|--------|------|-------------|
| GET | /bsp/bsp001/scores/{id} | [consumer] |

**OpenFGA integration:** [which relationships are evaluated, at which layer, for which endpoints]

**Inter-service auth:** [how this L2 identifies its callers and enforces the allowed-caller list]

### Observability

**SLO targets:**

| Metric | Target | Alert threshold |
|--------|--------|----------------|
| Availability | 99.9% | < 99.5% |
| Latency p99 (critical path) | < [N]ms | > [N*1.5]ms |
| Event publication lag | < [N]s | > [N*2]s |

**Custom business metrics** (beyond standard OTel):
- `[metric_name]{capability_id="[CAP-ID]"}` — [what it measures]

**Mandatory OTel dimensions on all metrics/logs/spans:** `capability_id`, `zone`, `deployable`, `environment`

### Infrastructure Baseline

**Kubernetes namespace:** `reliever-[zone-abbrev]` (TECH-STRAT-006)

**Resource requests/limits:**

| Resource | Request | Limit |
|----------|---------|-------|
| CPU | [N]m | [N]m |
| Memory | [N]Mi | [N]Mi |

**Horizontal scaling policy:** [HPA trigger — CPU/memory/custom metric, min/max replicas]

**Special networking:** [any egress rules, external API access, specific ingress config]

### Build vs. Buy

For each domain-specific component:

| Component | Decision | Product/Library | Justification |
|-----------|----------|-----------------|---------------|
| [algorithm / feature] | Build / Buy / Adapt | [if Buy] | [why] |

---

## Justification

Why these choices fit this specific L2 better than the alternatives considered.
Cite: the domain classification, the performance constraints surfaced in Movement 4,
the team context, and any FUNC ADR requirement that drove a specific choice.

### Alternatives Considered

For each major decision, document the alternatives that were rejected:

**Database:**
- [Option A] — rejected because [specific reason tied to this L2's constraints]
- [Option B] — rejected because [specific reason]

**Runtime:**
- [Option A] — rejected because [specific reason]

[Minimum 2 alternatives per major decision.]

## Technical Impact

### On the [Zone] deployable
[How this L2's choices affect the deployable it lives in — image size, startup time, config]

### On dependent L2s
[If other L2s subscribe to this L2's events or call its API — what they must handle]

### On the platform team
[Any special provisioning request: specific DB engine, Kafka topic config, external access]

## Consequences

### Positive
[What this stack enables for this L2]

### Negative / Risks
[Operational, cognitive, or coupling risks introduced]

### Accepted Debt
[Technology choices deferred to implementation or to a future ADR]

## Governance Indicators

- **Review trigger:** [what change — volume spike, new regulatory requirement, team change —
  would cause this ADR to be revisited]
- **Expected stability:** [timeframe — typically 1–2 years for tactical decisions]

## Traceability

- Session: Tactical tech brainstorming YYYY-MM-DD
- Participants: [who was in the session]
- Grounded in:
  - [FUNC ADR ID] — functional definition of this capability
  - [TECH-STRAT ADR IDs] — strategic constraints applied
  - [Any external reference — library docs, benchmark, regulatory spec]
```

---

## Closing Each Capability

After writing the ADR, tell the user:
> "ADR-TECH-TACT-[NNN] committed to `tech-adr/`. 
> [If overrides exist:] ⚠️ This ADR contains [N] strategic override(s) — they are marked
> PENDING_ARCHITECT_TEAM and cannot be accepted until the full architect team reviews them.
>
> Want to continue with another capability, or pause here?"

If overrides exist, also summarize them concisely:
> "Override summary for [CAP-ID]:
> - OVERRIDE-001: [one line] — deviates from TECH-STRAT-NNN Rule X"

---

## Facilitation Principles

- **One or two questions at a time.** Never present a wall of questions. The user cannot
  think about 8 things simultaneously.

- **Summarize before progressing.** After each Movement, confirm the summary before
  moving on. If the user corrects the summary, update your understanding — do not rush.

- **Probe, don't lead.** Present alternatives without a preferred option. Your role is
  to surface trade-offs, not to make the decision.

- **Domain classification informs depth.** Core capabilities deserve more questions.
  Generic capabilities deserve more challenge on build-vs-buy.

- **The strategic default is always the baseline.** Do not treat overrides as normal
  design freedom — they are exceptions that carry architectural cost and governance
  overhead. Challenge unjustified overrides firmly.

- **Mirror language.** French or English — follow the user consistently within a session.

- **Cite ADR IDs.** Every constraint you name should reference its source ADR. This
  builds the user's fluency with the governance model and makes the override discussion
  concrete rather than abstract.

- **Never produce code.** Not even pseudocode. If the user asks "but how would you
  implement the erasure?", redirect:
  > "The implementation detail belongs in a `plan/` task. Here we decide which approach
  > (crypto-shredding vs. soft-delete vs. anonymization-in-place). Which fits this L2?"
