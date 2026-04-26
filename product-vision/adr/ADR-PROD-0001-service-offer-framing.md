---
id: ADR-PROD-0001
title: "Service Offer Framing — Active Control Device, Not Advisory Tool"
status: Accepted
date: 2026-04-25
family: PROD
session: product-brainstorming
related_decisions:
  - ADR-PROD-0003
  - ADR-PROD-0005
---

# ADR-PROD-0001 — Service Offer Framing: Active Control Device, Not Advisory Tool

## Context

During the product discovery session, the problem was first framed as "helping individuals avoid 
over-indebtedness." Existing solutions (Banque de France files, recovery plans) were found to fail 
because they arrive too late — after the spiral has already begun — and cannot intervene at the 
moment of the individual micro-purchase decision.

The key question was: is this a product that *informs* people (a dashboard, a budget tracker), 
or one that *acts* for them at the decision point?

The beneficiary was established as someone who already *knows* they are in financial difficulty. 
They are not lacking information — they are lacking an external authority that gives concrete 
support at the precise moment of the decision. The insight was: "It's about having a guide, a 
superior authority, a crutch that would allow them to regain control of their life."

## Decision

Reliever is an **active control device for delegated willpower** — not a financial advisory tool.

- The product acts at the moment of the purchase decision, not before or after it.
- The beneficiary delegates behavioral rules in advance; the product enforces them in the moment.
- The card is the physical enforcement point: control is operational, not consultative.
- The product measures its own success by its capacity to render itself unnecessary (progressive 
  autonomy restoration, leading to a standard banking application at the final tier).

**Service offer sentence (French original):**
> Reliever permet à des individus en fragilité financière de reprendre progressivement le contrôle 
> de leur vie financière quotidienne grâce à un système de paliers d'autonomie croissante, ancré sur 
> une carte dédiée et un score comportemental coordonné entre prescripteurs via open banking, même 
> quand préserver leur dignité est aussi important que contraindre leurs comportements.

**Service offer sentence (English):**
> Reliever enables financially vulnerable individuals to progressively regain control of their 
> daily financial lives through a system of increasing autonomy tiers, anchored on a dedicated 
> card and a behavioral score coordinated between prescribers via open banking, even when 
> preserving their dignity is as important as constraining their behaviors.

## Justification

The distinction between "inform" and "act" is structurally decisive:

- An advisory tool requires the user to apply the advice, which is precisely what they cannot do 
  alone (the problem is not lack of information but lack of external authority at the moment of 
  decision).
- An active control device removes the need for willpower at the transaction point — it provides 
  the external authority the person cannot generate alone.

The rehabilitation model (the product succeeds when it becomes unnecessary) follows naturally: 
if the goal is restoring autonomy, not creating dependency, the product must measure progress 
toward its own obsolescence.

### Alternatives Considered

- **Advisory/informational tool** — rejected because the beneficiary already knows their 
  situation; the problem is execution at the decision point, not awareness.
- **Full account management system** — rejected because it would require inter-banking 
  protocols impossible to obtain today and would replicate the banking system rather than 
  serving as a remediation layer on top of it.

## Consequences

### Positive
- The service offer is falsifiable: any feature that does not serve progressive autonomy 
  restoration or dignity preservation at the decision point can be rejected.
- The remediation positioning creates a clear boundary with pure banking products.

### Negative / Risks
- The "active control" framing raises consent and tutorship questions that must be managed 
  carefully (see ADR-PROD-0002 on the multi-prescriber model).
- Measuring "progress toward obsolescence" requires a robust behavioral score (see ADR-PROD-0004).

### Open Questions
- The name "Reliever" carries double meaning (relief from debt burden + relay when one can no 
  longer manage alone) — this duality is intentional and confirmed.
- "Daily financial life" vs. "purchase decisions" — the scope favors the broader framing because 
  open banking gives a full financial view, even if control is exercised only via the card.

## Traceability

- Session: product-brainstorming
- Date: 2026-04-25
- References: product-vision/product.md
