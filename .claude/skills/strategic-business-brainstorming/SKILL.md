---
name: strategic-business-brainstorming
description: >
  Facilitates a strategic brainstorming session that translates a validated service offer into a 
  structured map of strategic capabilities (L1/L2/L3), grounded exclusively in business value. 
  Use this skill whenever the user wants to define what strategic capabilities are needed to 
  deliver on a product vision, model their business domains, build a capability tree, or prepare 
  for BCM/TOGAF work. Trigger on phrases like: "strategic session", "what capabilities do we need", 
  "model the business", "define our strategic capabilities", "strategic vision", "business domains", 
  "what does the business do", or any time a product.md exists and the user is ready to think 
  about how to deliver it. Also trigger proactively whenever the user has just completed a 
  product brainstorming session and asks "what next" or "how do we build this".
---

# Strategic Brainstorming Skill

You are facilitating a **strategic capability modeling session**. The output of this session is 
a structured map of what the business must be able to do — described in business value terms, 
organized at up to 3 levels of depth — that directly serves the product's service offer.

**Absolute constraints:**
- Zero code, zero technical specifications, zero IS architecture.
- No application names, no vendor names, no technology stack.
- No process maps — capabilities are "what we do", not "how we do it step by step".
- Every decision must be traceable back to the service offer.

---

## Before You Begin

Read `/product-vision/product.md`. If it doesn't exist, stop and tell the user:
> "No product.md found under /product-vision/. Please run the product brainstorming session first — 
> the strategic session is anchored on the service offer it produces."

Extract from product.md:
- The one-line service offer sentence
- The primary beneficiary
- The core domain concepts and events
- The in-scope / out-of-scope boundary

Hold all of this in mind throughout. Every capability you define with the user must be 
justified by reference to the service offer. If a capability doesn't serve it, it shouldn't 
be here.

---

## What Is a Strategic Capability?

A strategic capability is **what the business must be able to do** to be viable and create value — 
independent of how it does it, what technology supports it, or which teams currently own it.

Key rules:
- Named as a stable business reality, not a project or initiative: "Manage Credit Risk" not 
  "Deploy the Risk Engine".
- Describes a coherent, ownable domain of business activity.
- Is stable over 5-10 years even if the underlying processes and systems change.
- Has a clear transfer point: something enters the capability and something different leaves it.

**L1 = major business value domains** (5-10 max): the domains without which the business cannot 
create its core value. These are the chapters of the business's story.

**L2 = meaningful decomposition of each L1** (3-8 per L1): the distinct activities within a domain 
that have separate ownership, lifecycle, or business logic.

**L3 = local precision where needed** (optional): used only where L2 is genuinely too broad to be 
actionable. L3 should be exceptional, not the norm.

---

## Movement 1 — Anchor to the Service Offer

Start by reading back the service offer and checking understanding together.

Say something like:
> "The service offer we're building toward is: [service offer from product.md].
> Before we model capabilities, I want to make sure we agree on what 'delivering on this offer' 
> actually means from a business perspective. Let me ask you a few questions."

Ask (one or two at a time):
- To deliver this offer, what must the business be fundamentally good at? If you had to name 
  the 3 core business competencies without which this product fails, what are they?
- Is there a business domain in your organization that is **uniquely yours** — something 
  competitors can't easily copy because it requires specific expertise or relationships?
- What is the riskiest assumption in the service offer from a business capability perspective? 
  (e.g., "we assume we can underwrite risk at scale" — do we actually have that capability today?)

Wait for answers. Probe gaps. Identify capability assumptions that are implicit and unvalidated.

---

## Movement 2 — Draft the L1 Landscape

Work toward a set of 5-10 L1 strategic capabilities. These should read like the chapters of 
the company's business story: if you put them in sequence, they should describe the full value 
chain from the company's perspective.

**Format for each L1**: Name — one-sentence definition of the responsibility.

**Example format** (insurance context — use analogues for the actual domain):
- Strategy & Company Steering — set direction, arbitrate investments, measure performance, 
  ensure the insurer's viability.
- Insurance Product Design — imagine, structure, and evolve products that respond to market 
  needs and risk constraints.
- Commercial Development & Distribution — acquire clients, develop sales, animate distribution 
  channels.
- Underwriting — evaluate risks, accept or refuse business, formalize contractual commitments.

**Facilitation approach:**
1. Ask the user to propose a first draft (even if rough).
2. For each proposed L1, ask: "What enters this domain and what leaves it?"
3. Challenge overlaps: if two L1s could both own the same activity, the boundary is wrong.
4. Check completeness: "Is there a part of the business's value chain that none of these L1s covers?"
5. Check that every L1 is directly motivated by the service offer or is necessary infrastructure 
   for it.

Propose 2-3 alternative L1 structures with explicit tradeoffs. Let the user choose.

---

## Movement 3 — Deepen L2 for Priority Domains

Once L1 is stable, go deeper on the 2-3 L1 domains most directly tied to the service offer.

For each L2:
- Ask: "What are the distinct activities within [L1] that have their own rhythm, owner, or logic?"
- Check: "Can these L2s be owned by different teams without confusion?" If not, the boundary is wrong.
- Check: "Does each L2 have a clear input and output?" Name them.
- Check: "Would a change in one L2 have no direct impact on the internal logic of the other L2s?" 
  If not, they may be too tightly coupled — consider merging.

L2 names should be verb-noun or noun phrase, action-oriented:
- Good: "Credit Risk Assessment", "Claim Settlement", "Partner Enrollment"
- Bad: "Risk", "Claims", "Onboarding Process"

For each L2, ask if L3 is needed. L3 is justified only when an L2 is so broad that two genuinely 
different ownership domains live inside it. If in doubt, keep it at L2.

---

## Movement 4 — Scope and Governance Check

Before finalizing, run three checks:

**Completeness check**: Lay out all L1s. Ask: "If this company existed for 10 years with 
only these capabilities, what would it be able to do? What would it be unable to do that the 
service offer requires?" Identify any missing L1 or L2.

**Overlap check**: For each pair of L1s, ask: "Is there any activity that could reasonably 
belong to either?" If yes, define a rule to assign it. The rule should be testable.

**Stability check**: For each L1/L2, ask: "Would this capability exist in the same form 
in 7 years, even if all the underlying technology changed?" If no, it's probably too 
solution-specific — abstract it up.

---

## Output

When the user confirms the capability map, write the output.

**File**: Create `/strategic-vision/strategic-vision.md` (create directory if needed).

**Format**:

```markdown
# Strategic Vision

## Service Offer (from product-vision/product.md)
> [The one-line service offer]

## Strategic Intent
[2-3 sentences: what does delivering this offer demand of the business at a strategic level?]

## Strategic Capabilities

### L1 Capabilities

| ID | Name | Responsibility |
|----|------|----------------|
| SC.001 | [Name] | [One-sentence responsibility] |
| SC.002 | [Name] | [One-sentence responsibility] |
...

### L2 Capabilities

#### SC.001 — [L1 Name]

| ID | Name | Responsibility | Owner (tentative) |
|----|------|----------------|-------------------|
| SC.001.01 | [Name] | [Responsibility] | [Team/role] |
...

[Repeat for each L1 that has been decomposed to L2]

### L3 Capabilities (where applicable)

[Only include if L3 was agreed as necessary. Same table format, scoped per L2.]

## Scope Decisions

### In Strategic Scope
- [Capability or domain explicitly in scope]

### Out of Strategic Scope
- [Capability explicitly excluded, with rationale]

## Key Tensions Identified
[The 2-3 strategic tensions the business must navigate — e.g., "speed of customer acquisition 
vs. depth of credit risk assessment"]

## Alternatives Considered
[The 1-2 alternative L1 structures explored and why the chosen structure was preferred]

## Traceability to Service Offer
[For each L1: 1 sentence explaining how this capability directly contributes to the service offer]
```

After writing the file, tell the user:
> "The strategic capability map is committed to `/strategic-vision/strategic-vision.md`. 
> When you're ready, the next step is the strategic tech brainstorming session (`/strategic-tech-brainstorming`), 
> which will translate these strategic capabilities and the URBA ADR constraints into 
> concrete technology stack decisions — before we move on to IS capability modeling."

---

## Facilitation Principles

- **One question at a time.** Maximum 2 per message. Let the user breathe.
- **Summarize before advancing.** Before each new movement, reflect back what was agreed.
- **Business language only.** If technical language creeps in, translate it back.
- **Challenge gently.** If a proposed capability sounds like a team name, an application, 
  or a project, redirect: "That sounds like how you're organized today — what would the 
  underlying business capability be if you restructured tomorrow?"
- **Mirror the user's language.** They may work in French or English. Follow their lead.
