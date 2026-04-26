---
task_id: TASK-004
capability_id: CAP.CAN.001.TAB
capability_name: Beneficiary Dashboard
epic: Epic 3 — Web Dashboard — Transaction History
status: todo
priority: medium
depends_on: [TASK-003]
---

# TASK-004 — BSP.004.AUT stub and transaction history web view

## Context
The current situation view (TASK-003) exposes the beneficiary's present state. This task adds the historical dimension: access to the complete transaction history (authorized and declined) with filters and sorting. Declines must display their reason — a requirement of the dignity rule (ADR-BCM-FUNC-0009: every decline is accompanied by a motivated explanation). Transactional events come from CAP.BSP.004.AUT, a capability distinct from the three already stubbed in TASK-002: a dedicated stub for BSP.004.AUT is therefore necessary.

## Capability Reference
- Capability: Beneficiary Dashboard (CAP.CAN.001.TAB)
- Zone: CHANNEL
- Governing ADRs: ADR-BCM-FUNC-0009, ADR-BCM-URBA-0009

## What needs to be produced

### Stub extension — BSP.004.AUT events
Extend the TASK-002 stub mechanism to publish the transactional events on the CAP.CAN.001.TAB subscription point:
- `Transaction.Authorized` — with category, amount, merchant, timestamp, beneficiary
- `Transaction.Declined` — with category, attempted amount, decline reason (tier rule applied), timestamp, beneficiary

The stub generates a simulated history sufficient to test filters and sorting.

### Read model extension — transaction history
Extend the TASK-002 read model to store transactions per beneficiary (authorized and declined), including the decline reason for declined transactions.

### Transaction history view (web interface)
The web interface exposes, from the TASK-003 main view, access to the transaction history:
- Display of all the beneficiary's transactions (authorized and declined)
- **Available filters**: period (start date / end date), spending category, status (authorized / declined)
- **Available sorting**: by date (ascending/descending), by amount (ascending/descending)
- Each declined transaction displays the decline reason in an intelligible way (not a technical code)
- `Dashboard.Viewed` is produced on each access to the history view

## Business Events to Produce
- `Dashboard.Viewed` — emitted on each access to the history view (enriched with context: channel=web, view=history)

## Business Objects Involved
- **Beneficiary** — subject of the history
- **Transaction** — each authorized or declined purchase act, with its context (category, amount, reason if declined)
- **Envelope** — spending category allowing transactions to be filtered

## Required Event Subscriptions
- `Transaction.Authorized` (from CAP.BSP.004.AUT) — resource subscription: feeds the history in the read model
- `Transaction.Declined` (from CAP.BSP.004.AUT) — business subscription: part of the beneficiary's visible lifecycle; the decline reason is business data to be displayed

## Definition of Done
- [ ] The stub produces `Transaction.Authorized` and `Transaction.Declined` compliant with the BSP.004.AUT contract
- [ ] The read model stores the transaction history per beneficiary with decline reasons
- [ ] The web view displays transactions with filter on period, category, and status
- [ ] Sorting by date and by amount works in both directions
- [ ] Declined transactions display their decline reason in intelligible language (not a code)
- [ ] `Dashboard.Viewed` is emitted on each access to the history view
- [ ] The history works with the test beneficiary fed by the stub
- [ ] validate_repo.py passes without error
- [ ] validate_events.py passes without error

## Acceptance Criteria (business)
A test beneficiary can filter their transactions by category and period, sort by descending amount, and read each decline reason in plain language. No declined transaction is displayed without an explanation.

## Dependencies
- **TASK-003**: the current situation view and the base read model must exist before adding the history
- **CAP.BSP.004.AUT**: source of `Transaction.Authorized` and `Transaction.Declined` — stub mandatory for isolated development

## Open Questions
- What is the retention period for the displayed transaction history (30 days? duration of the full program)?
- Is the decline reason a fixed enumeration (dictated by CAP.REF.001.PAL tiers) or free text produced by BSP.004.AUT?
