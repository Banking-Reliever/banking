---
id: ADR-PROD-0002
title: "Primary Beneficiary and Multi-Prescriber Model"
status: Accepted
date: 2026-04-25
family: PROD
session: product-brainstorming
related_decisions:
  - ADR-PROD-0001
  - ADR-PROD-0005
---

# ADR-PROD-0002 — Primary Beneficiary and Multi-Prescriber Model

## Context

During the session, two potential primary beneficiaries were identified with potentially divergent 
interests:

1. The financially fragile individual — who needs to regain control of their daily financial life.
2. The bank — which needs to reduce its risk exposure and avoid triggering heavy legal procedures.

The question arose: is the product *consented to* or *imposed*? This is structurally significant 
because a consented tool is an empowerment tool; an imposed tool is a tutorship measure. The two 
do not follow the same design logic.

It was also established that the product can be prescribed by three distinct actors: a bank, a 
psychiatrist, or a social worker — making this not a pure banking product but a financial and 
social remediation protocol.

## Decision

The **primary beneficiary is the individual in financial remediation** — not the prescribing 
institution.

- The product is positioned *before* heavier coercive measures (Banque de France files), not as 
  an alternative to them.
- It may be imposed, but it is designed to be experienced as an empowerment tool, not a 
  sanction.
- Three prescriber roles are recognized with differentiated rights: **bank**, **psychiatrist**, 
  and **social worker**.
- Multi-actor coordination on a single individual is a core feature, not an edge case.
- Prescribers have differentiated visibility and action rights depending on their role — data 
  governance between prescribers (what does the psychiatrist see? does the bank see the 
  diagnosis?) remains an open question.

## Justification

Centering the primary beneficiary on the individual (rather than the institution) is a strategic 
choice that directly conditions the dignity constraint (ADR-PROD-0005):

- If the institution were the primary beneficiary, the product would be optimized for risk 
  reduction at the expense of the user experience.
- Centering the individual forces every design decision to pass the dignity test: does this 
  feature serve the person's path toward autonomy, or does it merely serve institutional 
  risk management?

The multi-prescriber model reflects the real social structure around financial vulnerability: 
financial fragility is not purely a banking matter — it intersects with mental health and social 
work. A product that only accepts the bank as prescriber misses the majority of real-world cases.

### Alternatives Considered

- **Institution as primary beneficiary** — rejected because it would lead to optimizing for 
  risk metrics over the beneficiary's progression, undermining the dignity constraint and 
  enabling bypass.
- **Self-prescribed only (pure consent model)** — rejected because the problem includes 
  individuals who need external authority precisely because self-governance has failed; pure 
  consent would exclude the most acute cases.
- **Single prescriber type (bank only)** — rejected because the real intervention network 
  includes psychiatrists and social workers; excluding them limits adoption and misses the 
  multi-dimensional nature of financial vulnerability.

## Consequences

### Positive
- Clear design north star: every feature must serve the individual's path toward autonomy.
- Multi-prescriber coordination becomes a differentiating feature rather than a technical 
  complication.
- Positioning before coercive measures creates an opportunity for early intervention.

### Negative / Risks
- The imposed/consented ambiguity creates a legal and ethical surface that must be managed.
- Multi-prescriber data governance (bank vs. psychiatrist vs. social worker) is a critical 
  open question with regulatory implications (GDPR, medical data, etc.).

### Open Questions
- What data does the psychiatrist see? Does the bank see the diagnosis?
- Who has the authority to *end* the remediation — the algorithm, the prescriber, or the 
  individual themselves?
- Is there a minimum consent requirement before activation of a prescriber-imposed tier?

## Traceability

- Session: product-brainstorming
- Date: 2026-04-25
- References: product-vision/product.md
