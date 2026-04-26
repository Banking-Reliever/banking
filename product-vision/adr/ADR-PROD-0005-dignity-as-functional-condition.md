---
id: ADR-PROD-0005
title: "Core Tension Resolution — Dignity as Functional Condition, Not Moral Add-On"
status: Accepted
date: 2026-04-25
family: PROD
session: product-brainstorming
related_decisions:
  - ADR-PROD-0001
  - ADR-PROD-0002
  - ADR-PROD-0006
---

# ADR-PROD-0005 — Core Tension Resolution: Dignity as Functional Condition

## Context

Three genuine tensions were identified during the deep modeling phase:

1. **Control vs. dignity** — constrain behaviors without infantilizing the person.
2. **Algorithm vs. human judgment** — prescriber override vs. objective algorithmic authority.
3. **Transparency vs. privacy** — data sharing between actors of different professional natures 
   (bank, psychiatrist, social worker).

The session identified **control vs. dignity** as the most dangerous tension to mishandle. The 
question was posed explicitly: "Which of these three tensions seems most dangerous to mismanage?"

The answer and its reasoning: "Control vs. dignity." And the reasoning that emerged from the 
discussion: "If the individual experiences the product as humiliation, they bypass it — and 
bypass is precisely the relapse signal the product seeks to prevent."

## Decision

**Dignity is a functional condition, not a moral value added to the product.**

This distinction is critical and has design consequences:

- A tool that infantilizes the user undermines itself by provoking the very bypass it seeks to 
  prevent (an unspent envelope is the bypass signal — see ADR-PROD-0006).
- Dignity preservation is not an ethical guardrail imposed on the product from the outside — it 
  is an internal success condition: a product that fails on dignity fails on its core function.
- The gamification model (Strava analogy) is therefore an **architectural choice, not a UX 
  decoration**: it transforms constraint into visible, valorizing progression.

Rules derived from this decision:
- Every tier transition must be framed as a step forward, not a punishment or reward.
- The vocabulary of the product must never infantilize (no "you failed", no punitive framing).
- The Strava-style progression view is a first-class feature, not optional.
- Control mechanisms (card refusal, envelope limits) must provide motivated, human-facing 
  feedback — not opaque blocks.

## Justification

The key insight from the session: "Dignity is not a moral value added to the product — it is a 
functional prerequisite. A humiliating tool undermines itself by provoking the bypass it seeks 
to prevent."

This reframes the design constraint entirely:
- It is not "we should be nice to users for ethical reasons."
- It is "if we humiliate users, we destroy the product's effectiveness by causing bypass."

Bypass (the individual spending money through alternative channels, leaving the envelope 
unconsumed) is the primary failure signal. The causal chain is:

> Humiliation → Bypass → Envelope not consumed → False relapse signal → Score degradation → 
> Wrong tier → Further humiliation

The dignity constraint breaks this loop at the source.

### Alternatives Considered

- **Dignity as ethical guardrail only** — rejected because it would be treated as a secondary 
  concern that can be traded off against control effectiveness; this framing misses the 
  functional dependency.
- **Pure control optimization (ignore dignity)** — not explicitly proposed but implicitly 
  rejected: the bypass risk was identified as the core failure mode, and bypass is dignity-driven.

## Consequences

### Positive
- Every design decision has a self-reinforcing quality: optimizing for dignity also optimizes 
  for effectiveness (reduced bypass).
- The gamification framework (Strava) has a clear architectural justification beyond aesthetics.
- The product can withstand the "is this paternalistic?" challenge by pointing to functional 
  efficacy rather than ethical intent alone.

### Negative / Risks
- Balancing "motivated refusal" (explaining why a purchase was declined) with real-time 
  friction at the checkout is a UX challenge with no obvious solution.
- The dignity constraint may conflict with the "imposed" nature of the product (ADR-PROD-0002 
  open question on minimum consent requirement).

### Open Questions
- How does the product communicate a purchase refusal at the point of sale — what is the 
  minimum information and maximum dignity in a 2-second transaction window?
- How does the product frame a tier *downgrade* (relapse detection) without being perceived 
  as punitive?

## Traceability

- Session: product-brainstorming
- Date: 2026-04-25
- References: product-vision/product.md
