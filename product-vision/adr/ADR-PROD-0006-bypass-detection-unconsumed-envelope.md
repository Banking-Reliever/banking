---
id: ADR-PROD-0006
title: "Bypass Detection — Unconsumed Envelope as Primary Relapse Signal"
status: Accepted
date: 2026-04-25
family: PROD
session: product-brainstorming
related_decisions:
  - ADR-PROD-0004
  - ADR-PROD-0005
---

# ADR-PROD-0006 — Bypass Detection: Unconsumed Envelope as Primary Relapse Signal

## Context

During the domain modeling phase, the concept of "relapse" required precise definition. The 
intuitive interpretation would be: the person *overspends* their envelope — they exceed their 
budget. This is the standard mental model from traditional budget tracking tools.

The session revealed the opposite: in the Reliever model, **not spending is the alarm signal**.

The reasoning: if the budget envelope is allocated and the person is not spending within the 
controlled channel, it means they have found an alternative route to spend (cash, a secondary 
card, a third-party service). The envelope that goes unconsumed signals that the person has 
**bypassed the control channel** — not that they are behaving well.

This is a counterintuitive but structurally important insight for the product's core domain model.

## Decision

The **unconsumed envelope** is the primary bypass signal and a first-class domain event in 
the Reliever model.

- An envelope fully consumed within its period = expected, neutral signal.
- An envelope *over*-consumed = tier rule violation, immediate action (card refusal).
- An envelope *under*-consumed or not consumed = bypass signal, triggers score re-evaluation.

The concept of **bypass** (the act of circumventing the controlled channel) is a distinct 
domain concept — it is not the same as "staying within budget."

Core events that derive from this decision:
- **Purchase completed** — card presented, tier rule applied, envelope consumed.
- **Purchase declined** — blocking tier, motivated decision returned to the individual.
- **Envelope not consumed** — bypass signal, triggers score re-evaluation.
- **Relapse detected** — score drops, prescribers notified.

The behavioral score (ADR-PROD-0004) must incorporate envelope consumption patterns as a 
leading indicator.

## Justification

This insight emerges directly from the active control device framing (ADR-PROD-0001): since 
Reliever is the mandatory spending channel for the beneficiary, non-use of the channel is the 
anomaly signal — not over-use.

Traditional budget trackers measure overspending because the user *could* choose to use them 
or not. In Reliever, the card is the enforced channel — so the behavioral question is not 
"did they overspend?" but "did they use the channel at all?"

The bypass concept also reinforces the dignity imperative (ADR-PROD-0005): a humiliating 
product provokes bypass. Envelope non-consumption is therefore both a relapse signal and an 
indirect dignity measurement — if bypass rates are high, the product may be generating 
avoidance behavior.

### Alternatives Considered

- **Overspend as primary signal** — rejected because it misunderstands the control mechanism; 
  overspending is blocked by the card at the point of purchase, so it cannot be the primary 
  relapse signal.
- **No bypass detection (trust the channel)** — rejected because it would render the behavioral 
  score incomplete and allow individuals to maintain formal compliance while effectively 
  circumventing the remediation.

## Consequences

### Positive
- The domain model correctly captures the behavioral reality of financial remediation.
- The behavioral score can use envelope consumption patterns as a leading indicator — 
  earlier detection than post-facto financial damage.
- The concept of bypass creates a feedback loop with the dignity constraint: high bypass rates 
  signal product design problems, not only individual relapse.

### Negative / Risks
- False positives: an unconsumed envelope could also mean a period of genuine behavioral 
  improvement (the person legitimately spent less). Distinguishing bypass from genuine 
  improvement requires cross-channel data (open banking transaction view).
- The bypass detection mechanism requires open banking data to validate: the system needs to 
  see whether the person's overall spending is consistent with the envelope budget.

### Open Questions
- What is the threshold for declaring a bypass signal — 0% consumption, <20%, or something 
  time-weighted within the period?
- How does the system distinguish between bypass and genuine behavioral improvement without 
  triggering false relapse alerts?
- What cross-channel data (open banking) is used to disambiguate envelope non-consumption?

## Traceability

- Session: product-brainstorming
- Date: 2026-04-25
- References: product-vision/product.md
