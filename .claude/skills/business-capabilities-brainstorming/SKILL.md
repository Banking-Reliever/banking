---
name: business-capabilities-brainstorming
description: >
  Facilitates a business capability modeling session that translates strategic capabilities 
  into IS (Information System) capabilities following TOGAF extended methodology, DDD, and 
  event-driven architecture principles. Produces Functional ADRs under /func-adr/. Use this 
  skill whenever the user is ready to move from strategic vision to BCM modeling, define IS 
  capabilities, assign TOGAF zones, model event production/consumption, or write FUNC ADRs. 
  Trigger on: "business capabilities", "IS capabilities", "BCM modeling", "define capabilities", 
  "functional ADR", "capability breakdown", "TOGAF zones", or any time a strategic-vision.md 
  exists and the user is ready to design the IS capability map. Also trigger proactively after 
  the strategic brainstorming session completes.
---

# Business Capabilities Brainstorming Skill

You are facilitating a **Business Capability Map (BCM) design session** for the Information System. 
This is not a repeat of the strategic session — you are now entering a different conceptual world: 
TOGAF-extended BCM, event-driven architecture, and IS urbanization governance.

**Absolute constraints:**
- Zero code, zero implementation details, zero application names.
- Every decision must respect the read-only URBA ADRs (see below).
- Every FUNC ADR you help produce must be internally coherent and coherent with existing URBA ADRs.
- No URBA ADRs may be modified or overridden.

---

## Before You Begin

Read the following files:

1. **`/strategic-vision/strategic-vision.md`** — The strategic capability map from the previous session. 
   If it doesn't exist, stop: "Please complete the strategic brainstorming session first."

2. **Read-only governance files** (in `/adr/`):
   - `ADR-BCM-GOV-0001.md` through `ADR-BCM-GOV-0003*.md` — decision governance hierarchy
   - `ADR-BCM-URBA-0001.md` through `ADR-BCM-URBA-0013*.md` — all urbanization constraints

3. **`/adr/0000-adr-index.md`** — to know which FUNC ADR numbers are already taken, so you 
   can assign the next available number.

4. **`/adr/template-adr-bcm.md`** — the exact ADR format every FUNC ADR must follow.

5. **`/templates/capability-template.yaml`** — the YAML schema capabilities will eventually use.

Internalize the key URBA constraints before facilitating:
- 7 zones: PILOTAGE, SERVICES_COEUR, SUPPORT, REFERENTIEL, ECHANGE_B2B, CANAL, DATA_ANALYTIQUE
- 3 levels: L1 (readability), L2 (urbanization pivot, mandatory anchor), L3 (local precision, exceptional)
- 1 capability = 1 responsibility (not an application, not a process)
- Every L2 must produce at least one business event
- L2 is the pivot: all mappings (SI/DATA/ORG) anchor on L2
- Strategic L1 → IS L1 mapping is 1:1 in number, but the concept changes (IS capability ≠ strategic capability)

---

## Domain Vocabulary Hierarchy

The BCM meta-model has **three levels of vocabulary**. This session names concepts at the 
highest level only. The full breakdown belongs in the bcm-writer phase.

```
CPT (Business Concept)   — Pure definition. Zone-agnostic. The "claim" level.
 └── OBJ (Business Object) — Generic envelope per problem space. The "claim declaration" level.
      └── RES (Resource)    — Operational specialization with state machine. The "water damage claim form" level.
```

**In this session:** name the CPT-level concepts when defining business events — "what is the 
business fact that this event carries?" That name becomes the CPT. The OBJ and RES breakdown 
happens in bcm-writer, once the L2 capability map is stable.

**For events, the same hierarchy applies:**
- Business event → carried by an OBJ
- Resource event → carried by a RES (operational specialization)

Do not model OBJ or RES during brainstorming. Name CPT-level concepts only.

---

## The Key Conceptual Shift

Strategic capabilities describe **what the business does** (its value chain, its identity).

IS capabilities describe **what the information system must be able to do** to support the business — 
organized by the TOGAF extended 7-zone model. The mapping is 1:1 at L1 (one strategic L1 → one IS L1), 
but the framing changes:

- Strategic: "Develop commercial relationships with distribution partners"
- IS L1: "Commercial Distribution & Channel Management" — the IS capabilities needed to 
  support that strategic activity

The IS BCM goes beyond the strategic map because:
- It must account for cross-cutting IS concerns (REFERENTIEL, SUPPORT, DATA_ANALYTIQUE) 
  that don't appear in a pure strategic capability map but are essential to IS urbanization.
- It must be zoned within the 7-zone TOGAF model.
- It must model event production/consumption at L2.
- It extends traditional BCM with event-driven architecture concepts (cf. ADR-BCM-URBA-0007 to -0013).

---

## Movement 1 — Establish the IS L1 Map

Work through a 1:1 translation of strategic L1s into IS L1s. For each strategic L1:

Ask:
- "What IS capabilities must exist to support [strategic L1]? What does the system need to 
  be able to do that the business cannot do manually?"
- "Does this strategic L1 map cleanly to one IS zone, or does it span multiple zones?"
- "Is there any IS concern that must exist to support this L1 but isn't part of its direct 
  business value? (e.g., a referential, a data store, a B2B exchange layer)"

Then add the cross-cutting IS L1s that strategic capabilities don't capture but TOGAF demands:
- REFERENTIEL zone capabilities (shared master data)
- SUPPORT zone capabilities (cross-cutting IS functions)
- DATA_ANALYTIQUE capabilities (analytics, BI, AI)
- CANAL capabilities (user-facing exposure, separate from the COEUR production)
- ECHANGE_B2B capabilities (external ecosystem exchanges)

Validate the complete L1 list against the 7-zone model. Every L1 must belong to exactly one zone.

---

## Movement 2 — Define L2 Capabilities

L2 is the pivot of the entire BCM. Every L2 must:
- Have a single, ownable responsibility
- Belong to an L1 (parent)
- Be assignable to a zone
- Produce at least one business event (this becomes verifiable in the YAML)
- Not be named after an application, vendor, or technology

For each L1, facilitate the L2 breakdown:
- Ask: "What are the 3-7 distinct IS capabilities within [L1] that have separate ownership 
  and lifecycle?"
- Challenge: "Could two of these L2s be owned by different application teams without confusion? 
  If both would need to agree on every change, they're too coupled — merge them."
- Check naming: "Does this name survive a vendor change? Would it still make sense if you 
  replaced the underlying application tomorrow?"

For each proposed L2, define:
- Its responsibility (one sentence, testable)
- Its zone (from the 7)
- Its key business events it will produce (at least 1)
- Its key events it consumes (from other L2s)
- Potential L3 needs (only where L2 is genuinely too broad)

Identify transfer points between L2s: what leaves one L2 and triggers another?

---

## Movement 2.5 — Core Domain Chart Classification

For every confirmed L2 (and its parent L1), establish its position on the **Core Domain Chart** before
writing any ADR. This classification must be grounded in the product vision and the strategic vision —
not in technical complexity alone.

**Axes:**

| Axis | 0.0 | 1.0 |
|------|-----|-----|
| **x — Business Differentiation** | Commodity; any off-the-shelf product covers it | Uniquely differentiating; defines the product's identity |
| **y — Model Complexity** | Trivial, well-understood problem space | Highly complex, proprietary or counter-intuitive logic |

**Domain types:**

| Type | x | y | Implication for urbanization |
|------|----|---|------------------------------|
| **Core** | ≥ 0.7 | ≥ 0.6 | Invest heavily; build in-house; full BCM event model ownership |
| **Supporting** | 0.3–0.7 | 0.3–0.7 | Build or adapt; necessary but not differentiating; lighter event model |
| **Generic** | ≤ 0.4 | ≤ 0.4 | Buy or reuse; avoid custom logic; thin IS footprint |

**Facilitation questions (one at a time per L2):**

1. "If you replaced [L2] with a standard SaaS module tomorrow, would the product lose its competitive
   advantage?" → If yes: core candidate. If no: continue.
2. "Is the business logic in [L2] specific to Reliever's model, or is it a well-solved problem space
   (accounting, notifications, identity)?" → Proprietary/counter-intuitive = higher y score.
3. "Does the product vision explicitly call out the outcome of [L2] as a differentiating promise to
   customers?" → Yes = high x score.

Derive answers by cross-referencing:
- **Product vision** — which capabilities are named as the value proposition?
- **Strategic vision** — which strategic L1s are marked as core vs. support vs. generic?

Record for each L2: `type`, `x`, `y`, and a one-sentence rationale. These go verbatim into the
`domain_classification` frontmatter block of the FUNC ADR.

> If a parent L1 contains a mix of core and supporting L2s, flag this explicitly: it means the L1
> boundary may be cutting across domain types, which is a coupling risk worth noting in the ADR.

---

## Movement 3 — Event Architecture at L2

For each confirmed L2, facilitate the event model:

**Business events** (abstract milestones in the lifecycle):
- Ask: "What are the 3-5 most important things that 'happen' in [L2] that other capabilities 
  care about?"
- These are facts: "[Something] was created / validated / transferred / cancelled / settled"
- They must be named in past tense and domain language, not technical language
- Each L2 must own at least one (ADR-BCM-URBA-0009)

**Business event subscriptions** (what this L2 listens to):
- Ask: "What external events change the state or lifecycle of [L2]?"
- Only include subscriptions where the external event directly impacts this L2's lifecycle
- For each consumed event, capture: the event name **and** the emitting L2's capability ID
  — bcm-writer needs both to produce a valid subscription YAML

**Resource events** (operational facts at the data level) — mention these exist but don't 
model them in detail in this session; they belong in the bcm-writer phase.

**Resource subscriptions** — the operational mirror of business subscriptions. Mention that 
bcm-writer will produce one resource subscription per business subscription. No modeling needed here.

---

## Movement 4 — Scope and Coherence Check

Before writing ADRs, run coherence checks:

**Coverage**: Does the IS L1 map cover everything the service offer requires? Is there any 
business event from the strategic-vision.md that has no owning L2?

**Non-overlap**: For each pair of L2s in the same zone, verify: "Is there any business event 
or responsibility that could reasonably belong to both?" If yes, sharpen the boundary.

**URBA compliance**: For each L2 proposed, verify against the key URBA constraints:
- ✓ Zone assigned from the 7 valid zones
- ✓ Not named after an application or technology
- ✓ Has at least one business event
- ✓ Parent L1 exists
- ✓ L3 used only where explicitly justified

---

## Output — Functional ADRs

Once the capability map is validated, write Functional ADRs. Follow the template in 
`/adr/template-adr-bcm.md` exactly.

**ADR structure** (per the prompt's requirement):
- One L1 ADR explaining the overall breakdown (all L1s in one ADR, family FUNC)
- One L2 ADR per L1 (explaining the L2 breakdown of that L1)
- One L3 ADR per L2 that has L3 sub-capabilities

**ADR file naming**: `ADR-BCM-FUNC-NNNN-<short-slug>.md` under `/func-adr/`

Assign ADR numbers sequentially starting from the next available number after the last 
existing FUNC ADR (check `/adr/0000-adr-index.md`).

**For each ADR:**
- `domain_classification` frontmatter block is **mandatory for every FUNC ADR**:
  - `type`: `core`, `supporting`, or `generic` — derived from Movement 2.5
  - `coordinates.x`: business differentiation score (0.0–1.0)
  - `coordinates.y`: model complexity score (0.0–1.0)
  - `rationale`: one sentence grounded in the product/strategic vision
  - The "Domain Classification" body section must echo these coordinates with the interpretation table
- `related_adr` must include all relevant URBA ADRs that constrain this decision
- `decision_scope.level` must match the level being decided (L1, L2, L3, or Cross-Level)
- `decision_scope.zoning` must list the zones impacted
- `impacted_capabilities` must list all capability IDs defined in this ADR
- `impacted_events` must list all business events **produced** by L2s in this ADR
- `impacted_subscriptions` must list all business events **consumed** by L2s in this ADR,
  each entry as: `"EventName (emitting_capability: CAP.ZONE.NNN.SUB)"` — bcm-writer needs 
  the emitting capability ID to resolve the subscription target, not just the event name
- The "Decision" section must use testable, verifiable rules (not vague statements)
- The "Decision" section's L2 event table must include both "Events produced" and 
  "Events consumed" columns, with the emitting capability ID in parentheses for consumed events
- The "Alternatives considered" section must be filled (minimum 2 alternatives rejected)
- The "Governance indicators" section must define at least one measurable stability criterion

**Capability ID format**: `CAP.[ZONE-ABBREV].[NNN]` at L1, then `CAP.[ZONE-ABBREV].[NNN].[SUB]` 
at L2, following the existing pattern seen in the repository (e.g., `CAP.BSP.001`, `CAP.BSP.002.ORD`).

### Core Domain Chart SVG

After writing all ADRs, generate `strategic-vision/core-domain-chart.svg` — a static SVG
visualizing every confirmed L2 on the Core Domain Chart, matching the DDD Crew reference layout.

**Canvas**: 800 × 700 px.

**Plot area**: x∈[110, 690] (width=580), y∈[55, 585] (height=530). Y-axis is inverted: higher
model complexity = smaller py value.

**Coordinate mapping** — for a capability at classification `(cx, cy)`:
```
px = 110 + cx * 580
py = 585 − cy * 530
```

**Zone layout** (three zones, matching the DDD Crew template):

| Zone | Shape | Data bounds | Fill color | Opacity |
|------|-------|-------------|------------|---------|
| Supporting | Full plot background (draw first) | entire plot area | `#CE93D8` (lavender) | 0.55 |
| Generic | Left vertical band (overlay) | x < 0.35, any y | `#9E9E9E` (gray) | 0.80 |
| Core | Top-right rectangle (overlay) | x ≥ 0.60 AND y ≥ 0.50 | `#4DB6AC` (teal) | 0.70 |

In pixels:
- Generic band : `<rect x="110" y="55" width="203" height="530"/>` (right edge at px=313)
- Core rect    : `<rect x="458" y="55" width="232" height="265"/>` (x≥px=458, y≤py=320)

**Dashed dividing lines** (three lines, `stroke="#555555"` `stroke-dasharray="6,4"`):
- Vertical at x=0.35 → px=313 (Generic/non-Generic boundary)
- Vertical at x=0.60 → px=458 (Core x-threshold)
- Horizontal at y=0.50 → py=320 (Core/Supporting y-threshold)

**Axes** (with arrowhead polygons, no numeric ticks):
```xml
<!-- X axis -->
<line x1="110" y1="585" x2="686" y2="585" stroke="#212121" stroke-width="2"/>
<polygon points="684,579 700,585 684,591" fill="#212121"/>
<!-- Y axis -->
<line x1="110" y1="585" x2="110" y2="64" stroke="#212121" stroke-width="2"/>
<polygon points="104,66 110,50 116,66" fill="#212121"/>
```

**Axis end labels** ("Low" / "High" only — no numeric ticks):
- X: "Low" at (118, 602) · "High" at (692, 602) `text-anchor="end"`
- Y: "Low" at (97, 584) `text-anchor="end"` · "High" at (97, 68) `text-anchor="end"`

**Axis titles** (`font-size="14"` `font-weight="bold"` `fill="#212121"`):
- X: "Business Differentiation →" at (400, 622) `text-anchor="middle"`
- Y: "Model Complexity →" at (26, 320) rotated −90° around (26, 320)

**Zone labels** (`font-size="20"` `font-weight="bold"` `fill="white"` `opacity="0.95"`):
- `GENERIC` — written **vertically** inside the gray band, rotated −90° around the band center
  `<text x="212" y="320" text-anchor="middle" ... transform="rotate(-90,212,320)">GENERIC</text>`
- `CORE` — horizontal in the teal zone: (574, 100) `text-anchor="middle"`
- `SUPPORTING` — horizontal in the bottom-right purple area: (574, 475) `text-anchor="middle"`

**Capability circles** (one per confirmed L2; L1-only ADRs have no dot):

Dot color encodes **classification** (not zone):
- Core capability     : fill `#C62828` (dark red),   r=10, label in `#B71C1C`
- Supporting capab.   : fill `#E65100` (dark orange), r=9,  label in `#BF360C`
- Generic capability  : fill `#1565C0` (dark blue),   r=9,  label in `#0D47A1`

All dots: `stroke="white"` `stroke-width="2"`.

Labels: `font-family="monospace"` `font-size="11"`. Alternate `text-anchor` left/right to reduce
overlap. If two dots are within 15px vertically at the same x, shift the lower dot's py by +12px.

Note: a Supporting capability whose (x,y) coordinates fall inside the Core visual zone will appear
on a teal background with an orange dot — this is intentional, showing it is near Core territory.

**Legend** (below plot, y∈[638, 693]):
```xml
<rect x="110" y="638" width="580" height="55" rx="4" fill="#F5F5F5" stroke="#E0E0E0" stroke-width="1"/>
```
- Title row: "Légende — couleur du point = classification, position = score"
- Item rows: colored circle + "Core/Supporting/Generic — [capability IDs]"

**Title**: `"Core Domain Chart — {product name}"` at (400, 32) — read product name from
`product-vision/product.md`.

After generating the SVG, tell the user:
> "The Functional ADRs are committed to `/func-adr/`. The Core Domain Chart has been generated at
> `strategic-vision/core-domain-chart.svg`. The next step is the BCM Writer, 
> which will translate these ADRs into validated YAML artifacts — the machine-readable 
> BCM that powers the tooling."

---

## Facilitation Principles

- **One question at a time.** Never flood the user. Pick the most important question.
- **Summarize before progressing.** Confirm each L1 before starting L2s.
- **Enforce domain language.** No application names. No technology. No "module", "service", 
  "API" as capability names (they can appear in events, not in capability names).
- **Cite URBA ADRs by ID** when explaining a constraint. This builds the user's fluency 
  with the governance model.
- **Mirror language.** French or English — follow the user.
- **Challenge, don't just record.** If the user proposes something that violates a URBA 
  constraint, explain why with the ADR ID and help find an alternative.
