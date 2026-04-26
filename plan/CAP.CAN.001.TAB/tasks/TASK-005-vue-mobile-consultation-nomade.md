---
task_id: TASK-005
capability_id: CAP.CAN.001.TAB
capability_name: Beneficiary Dashboard
epic: Epic 4 — Mobile View — Nomadic Consultation
status: todo
priority: medium
depends_on: [TASK-003]
---

# TASK-005 — Mobile view — nomadic dashboard consultation

## Context
The beneficiary must be able to view their financial situation while on the go, from a mobile device. The mobile interface is not a reduced version of the web interface: it is a reading mode optimized for speed, designed for the micro-moments of checking before a purchase. It shares the same read model as TASK-003 (no new event subscriptions) but exposes a simplified subset of data: current tier and main envelope balances, without filters, without sorting, without secondary columns. The dignity rule applies identically. `Dashboard.Viewed` is produced with the tag `channel=mobile` to analytically distinguish usage.

## Capability Reference
- Capability: Beneficiary Dashboard (CAP.CAN.001.TAB)
- Zone: CHANNEL
- Governing ADRs: ADR-BCM-FUNC-0009, ADR-BCM-URBA-0009

## What needs to be produced

### Mobile interface — lightweight current situation view
The mobile interface displays for the authenticated beneficiary:

1. **Progression section** (displayed first — dignity rule):
   - Current tier (name and level only, not the full description)
   - Simple visual indication of the next tier

2. **Envelopes section**:
   - Balances of the main envelopes (the most frequent categories, determined by the tier definition in CAP.REF.001.PAL)
   - For each envelope: category and available balance only (not the total period amount, no chart)
   - No filters, no sorting, no secondary columns

**What the mobile view does not expose** (reserved for web):
- Transaction history
- Filters and sorting
- Full detail of all secondary envelopes
- Complete tier description

### Consent gate
The `Consent.Granted` gate from TASK-003 applies identically on the mobile channel.

### Business event production
`Dashboard.Viewed` is emitted on each consultation of the mobile view, with the tag `channel=mobile`, to enable analytical distinction between web and mobile usage.

## Business Events to Produce
- `Dashboard.Viewed` — emitted on each consultation of the mobile view (attributes: beneficiary, tier, channel=mobile, timestamp)

## Business Objects Involved
- **Beneficiary** — subject of the consultation
- **Tier** — displayed in simplified form (name + level)
- **Envelope** — main envelope balances only

## Required Event Subscriptions
No new subscriptions — the mobile view consumes the same read model as TASK-003, fed by the TASK-002 subscriptions.

## Definition of Done
- [ ] The mobile interface displays the current tier (name and level) first
- [ ] The mobile interface displays the main envelope balances (category + available balance only)
- [ ] No filters, no sorting, no secondary columns are present in the mobile interface
- [ ] The `Consent.Granted` gate blocks access if consent is absent
- [ ] `Dashboard.Viewed` is emitted with `channel=mobile` on each consultation
- [ ] The dignity rule is respected (progression before restrictions)
- [ ] The view works with the test beneficiary fed by the TASK-002 stub
- [ ] validate_repo.py passes without error
- [ ] validate_events.py passes without error

## Acceptance Criteria (business)
A beneficiary who opens the mobile interface immediately sees their tier and main balances in two or three visual elements. The experience is readable in under five seconds without scrolling. Each opening traces a `Dashboard.Viewed` tagged `channel=mobile`.

## Dependencies
- **TASK-003**: the read model and the consent gate must exist — the mobile view reuses them without modification

## Open Questions
- Which envelopes are considered "main" on mobile? Are they determined by the current tier (CAP.REF.001.PAL) or by the beneficiary's usage frequency?
- Is the mobile interface a native application (iOS/Android) or a responsive webapp? This choice does not block the task but may impact interface sprints.
