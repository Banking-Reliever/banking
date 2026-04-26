---
task_id: TASK-003
capability_id: CAP.CAN.001.TAB
capability_name: Beneficiary Dashboard
epic: Epic 2 — Web Dashboard — Current Situation
status: todo
priority: high
depends_on: [TASK-002]
---

# TASK-003 — Consent gate and current situation web view

## Context
This is the first business view of the dashboard: the beneficiary views their active tier, budget envelopes by category, and available balance on the web interface. The dignity rule (ADR-BCM-FUNC-0009) requires that accomplished progression be presented before restrictions. Access to data is conditioned on `Consent.Granted` (CAP.SUP.001.CON) — a blocking gate. This view produces the central business event of CAP.CAN.001.TAB: `Dashboard.Viewed`. It forms the foundation on which all subsequent views depend (TASK-004, TASK-005).

## Capability Reference
- Capability: Beneficiary Dashboard (CAP.CAN.001.TAB)
- Zone: CHANNEL
- Governing ADRs: ADR-BCM-FUNC-0009, ADR-BCM-URBA-0009

## What needs to be produced

### Consent gate
Before displaying any beneficiary data, verify that `Consent.Granted` is present for this beneficiary from CAP.SUP.001.CON (or its stub during development). If consent is absent or revoked, access to the dashboard is denied with an explanatory message.

### Current situation view (web interface)
The web interface displays for the authenticated beneficiary:

1. **Progression section** (displayed first — dignity rule):
   - Current tier with its name and description
   - Indication of the next tier and what separates them from reaching it

2. **Envelopes section**:
   - List of active budget envelopes by spending category
   - For each envelope: category, available balance, total period amount
   - Restrictions (blocked categories) appear after the available ones

Data is read from the read model maintained by TASK-002.

### Business event production
`Dashboard.Viewed` is emitted on each consultation of this view, with: beneficiary identifier, displayed tier, timestamp, channel (`web`).

## Business Events to Produce
- `Dashboard.Viewed` — emitted on each consultation of the view by an authenticated and consenting beneficiary

## Business Objects Involved
- **Beneficiary** — subject of the consultation, previously authenticated
- **Tier** — current state displayed (from the TASK-002 read model)
- **Envelope** — balances by category displayed (from the TASK-002 read model)

## Required Event Subscriptions
No direct subscriptions — the view reads the read model produced by TASK-002, which is fed by the subscriptions defined in that task.

Gate dependency:
- `Consent.Granted` (from CAP.SUP.001.CON) — verified as a pre-condition for display (stub acceptable in development)

## Definition of Done
- [ ] The consent gate blocks access if `Consent.Granted` is absent for the beneficiary
- [ ] The web view displays the current tier and its description
- [ ] The web view displays the next reachable tier and the progression gap
- [ ] The web view displays all active envelopes with their available balance and period total
- [ ] Progression is presented before restrictions (dignity rule ADR-0009)
- [ ] `Dashboard.Viewed` is emitted on each consultation with the required attributes (beneficiary, tier, channel=web, timestamp)
- [ ] The view works with the test beneficiary fed by the TASK-002 stub
- [ ] validate_repo.py passes without error
- [ ] validate_events.py passes without error

## Acceptance Criteria (business)
A test beneficiary who views the main page first sees their progression (tier reached, next tier), then their envelopes. If their consent is simulated as revoked, the page is inaccessible. Each consultation traces a `Dashboard.Viewed` event.

## Dependencies
- **TASK-002**: the beneficiary read model (score, tier, envelopes) must be fed before the view can display data
- **CAP.SUP.001.CON**: `Consent.Granted` gate — stub acceptable in development
- **CAP.REF.001.PAL**: tier definitions (names, descriptions, crossing thresholds) — stub acceptable

## Open Questions
None blocking to start (the required data is in TASK-001 and TASK-002).
