---
id: ADR-PROD-0004
title: "Tier Progression — Algorithm Authority with Prescriber Override"
status: Accepted
date: 2026-04-25
family: PROD
session: product-brainstorming
related_decisions:
  - ADR-PROD-0002
  - ADR-PROD-0005
---

# ADR-PROD-0004 — Tier Progression: Algorithm Authority with Prescriber Override

## Context

The product uses a tier system to model the progressive restoration of autonomy. A key design 
decision was required: who decides that a person advances to the next tier?

Three candidate governance models were considered:

1. The algorithm alone — pure objective scoring, no human intervention possible.
2. A prescriber decides — the algorithm informs, but humans make the final call.
3. The individual requests advancement — self-advocacy within the system.

The session introduced the analogy of the MMR (Matchmaking Rating) system from Dota 2: 
an objective continuous score that determines competitive bracket placement, but with the 
added possibility for a prescriber to manually force a tier change (like a coach moving a 
player to a higher bracket to accelerate progression) — after which the algorithm validates 
or invalidates the decision based on observed behaviors.

## Decision

The **algorithm is the primary and continuous authority** on tier progression. Prescriber 
override is possible but temporary and subject to behavioral validation.

Rules:
- The behavioral score is calculated continuously (the MMR equivalent).
- The algorithm determines tier changes based on the score.
- A prescriber (bank, psychiatrist, social worker) may force a tier override — either 
  upward (accelerating progression) or downward (responding to detected deterioration).
- If the override is not validated by subsequent behavior, the algorithm resumes authority 
  and corrects the tier.
- The individual cannot self-advocate for tier advancement — progression is governed by 
  the algorithm and mediated by prescribers.

Tier boundaries:
- **First tier**: maximum assistance on purchase decisions.
- **Last tier**: switch to a standard banking application — Reliever is no longer needed.

## Justification

The MMR analogy captures the core design intent: objectivity, continuity, and resistance to 
gaming. A purely human-governed system would be subject to:
- Prescriber subjectivity and divergent judgments (three types of prescribers with different 
  professional frameworks).
- Political pressure (the bank wanting to advance the person to reduce cost; the social worker 
  wanting to keep them in a protective tier longer).
- Individual gaming (claiming progress to escape constraints).

Making the algorithm the primary authority neutralizes these risks. Prescriber override is 
preserved for cases where clinical or social judgment must take precedence — but it is bounded: 
if the override was wrong, the algorithm corrects it.

This design also creates a traceability advantage: tier changes are either algorithmic 
(auditable score trace) or prescriber-initiated (logged override with reason).

### Alternatives Considered

- **Algorithm-only (no override)** — rejected because clinical and social contexts require 
  human judgment that cannot always be captured by behavioral data alone. A prescriber must 
  be able to respond to information the algorithm cannot see (e.g., a life event, a medical 
  change).
- **Prescriber-only (no algorithm)** — rejected because it would create divergence between 
  the three prescriber types, enable subjective bias, and create dependency on human 
  availability for a continuous monitoring task.
- **Self-advocacy model** — not explicitly considered but implicitly rejected: the problem 
  is that the individual cannot reliably self-assess their own progress; the external authority 
  is precisely what makes the product valuable.

## Consequences

### Positive
- Objective, auditable tier governance resistant to individual or institutional gaming.
- Override traceability: prescribers can act, but the system records and evaluates their 
  decisions against behavioral reality.
- Clear success condition: final tier reached = product rendered unnecessary.

### Negative / Risks
- Behavioral score definition is a critical open question: what indicators does the algorithm 
  measure? What is the weighting? Who validates the model?
- The algorithm can be wrong — systematic errors could lock a person in a tier that is not 
  appropriate to their actual situation.
- Prescriber override accountability: if a prescriber forces an inappropriate tier change 
  and the algorithm corrects it, is there a feedback mechanism to the prescriber?

### Open Questions
- What specific behavioral indicators does the algorithm measure (spending patterns, bypass 
  signals, envelope consumption rate, temporal regularity)?
- What is the precision criteria for tier transition?
- Who validates the scoring model — the bank, a regulatory body, the product team?

## Traceability

- Session: product-brainstorming
- Date: 2026-04-25
- References: product-vision/product.md
