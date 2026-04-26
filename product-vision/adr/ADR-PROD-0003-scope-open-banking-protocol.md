---
id: ADR-PROD-0003
title: "Scope Boundary — Open Remediation Protocol via Open Banking"
status: Accepted
date: 2026-04-25
family: PROD
session: product-brainstorming
related_decisions:
  - ADR-PROD-0001
  - ADR-PROD-0004
---

# ADR-PROD-0003 — Scope Boundary: Open Remediation Protocol via Open Banking

## Context

Three scoping options were explicitly evaluated during the session. The original implementation 
used a micro-account limited to food and daily expenses, fed from the main account. This was 
acknowledged as a limitation born from the inability to reach a shared protocol across banking 
institutions.

The three options were:

**Option 1 — Food sandbox (current scope):** The product limits itself to a micro-account 
covering grocery and daily spending. The weakness: rent, bills, and the rest of financial life 
remain outside scope. The strength: deliverable today, negotiable with banks.

**Option 2 — Progressively managed account:** The product targets integration with the main 
account, with graduated tier-based control. Requires a shared banking protocol — impossible 
today, but the product would be designed for this target with the micro-account as a phase 0.

**Option 3 — Open remediation protocol:** The product does not anchor itself in a single bank. 
It is a remediation layer that integrates with any existing account via open banking. The 
dedicated card becomes the sole universal control point, independent of the banking institution.

## Decision

**Option 3 — Open remediation protocol** is the selected scope.

- Reliever does not request permission from banks: it positions itself above them via open banking.
- The bank remains a prescriber actor but is no longer the technical foundation of the product.
- The dedicated card is the sole enforcement point — universal and portable.
- Open banking is the only access channel; no inter-institutional agreements are required.

**Explicit out-of-scope decisions:**
- No loans or credit instruments — Reliever is a remediation layer, not a credit product.
- No fund transfers — the dedicated card is the only active control interface.
- No integration with proprietary banking systems — open banking is the universal layer.
- No management of the main bank account — Reliever is a behavioral remediation layer, not 
  a bank account replacement.

## Justification

Option 3 resolves the core structural limitation of Options 1 and 2:

- Option 1 is too narrow: constraining only food spending while the rest of financial life is 
  uncontrolled undermines the effectiveness of the remediation.
- Option 2 requires inter-institutional agreements that are operationally impossible today and 
  would create dependency on banking cooperation that cannot be guaranteed.
- Option 3 achieves banking institution independence: via open banking, Reliever reads the full 
  financial picture without requiring integration agreements. The dedicated card is the only 
  enforcement mechanism needed.

The open banking positioning is not a temporary compromise — it is a structural architectural 
choice that makes the product viable at scale without regulatory capture by any single institution.

### Alternatives Considered

- **Option 1 (food sandbox)** — rejected as primary scope because it maintains dependency on 
  banking agreements and limits the behavioral view to a single spending category. Acknowledged 
  as a viable tactical starting point but not the right long-term scope.
- **Option 2 (progressively managed account)** — rejected because the shared banking protocol 
  required is impossible to obtain today and would delay the product indefinitely.

## Consequences

### Positive
- Banking institution independence: the product can be deployed with any partner bank as 
  prescriber without requiring infrastructure changes.
- Full financial view via open banking enables the behavioral score to work on complete data.
- The dedicated card is a universal enforcement point regardless of the underlying banking 
  institution.

### Negative / Risks
- Open banking dependency: the product relies on open banking regulation (PSD2) being 
  operational and accessible.
- The dedicated card issuer partnership (which payment institution?) is an open question.
- What happens when the budget envelope is exhausted before the end of the period? This edge 
  case is unresolved.

### Open Questions
- Which payment institution issues the dedicated card?
- What happens when the envelope is exhausted before the period ends?
- How does open banking handle multi-bank situations (beneficiary with accounts at multiple 
  institutions)?

## Traceability

- Session: product-brainstorming
- Date: 2026-04-25
- References: product-vision/product.md
