# Roadmap — Beneficiary Dashboard (CAP.CHN.001.DSH)

## Capability Summary
> Expose to the beneficiary a synthetic view of their financial situation adapted to their tier: available balance, envelopes, transaction history. The interface is calibrated to encourage without infantilizing — dignity is a functional constraint.

## Strategic Alignment
- **Service offer**: Reliever enables financially vulnerable individuals to progressively regain control of their daily financial lives through a system of increasing autonomy tiers
- **L1 strategic capability**: SC.005 — Progression Valorization
- **BCM Zone**: CHANNEL
- **Governing ADRs**: ADR-BCM-FUNC-0009

## Framing Decisions

- **V0 without gamification** — gamified visualization (badges, visible score, milestones) is deferred to subsequent iterations; V0 exposes tier + envelopes + history
- **Decoupled stub/CORE architecture** — a single subscription point per capability; the stub feeds this point during development, the CORE replaces it once operational; developments are strictly isolated
- **Two planned channels** — web (rich dashboard, complete filters and sorting) and mobile (lightweight view, fewer columns, no complex filters); V0 centered on web
- **Dignity rule** (ADR-BCM-FUNC-0009): accomplished progression is always displayed before restrictions; declines are accompanied by an explanation

---

## Implementation Epics

### Epic 1 — Event Feed Infrastructure
**Objective**: Establish the unique subscription point of `CAP.CHN.001.DSH` and the stub that produces CORE events, allowing the dashboard to be developed in complete isolation.

**Entry condition**: The unique subscription point pattern per capability is architecturally validated (dedicated topic/queue per capability on the event bus).

**Exit condition (DoD)**:
- A stub publishes `BehavioralScore.Recalculated`, `Tier.UpwardCrossed`, `Envelope.Consumed` on the `CAP.CHN.001.DSH` subscription point at a configurable frequency
- The dashboard consumption layer reads these events and makes them available to subsequent epics
- A test beneficiary is fully simulable end-to-end without any CORE dependency

**Complexity**: M

**Unlocked business events**: consumption pipeline operational (no external business events produced at this stage)

**Dependencies**: none (founding epic)

---

### Epic 2 — Web Dashboard — Current Situation
**Objective**: The beneficiary can view their active tier, budget envelopes by category, and available balance on the web interface; `Dashboard.Viewed` is produced on each consultation.

**Entry condition**:
- Epic 1 complete (stub operational)
- Current beneficiary state available: `CAP.BSP.002.CYC` or equivalent stub
- `Consent.Granted` verification possible: `CAP.SUP.001.CON` or stub gate

**Exit condition (DoD)**:
- The web interface displays: current tier, envelopes by category with available balance, indication of the next reachable tier
- Accomplished progression is presented before restrictions (dignity rule ADR-0009)
- `Dashboard.Viewed` is produced on each access to the main page
- Access is blocked if `Consent.Granted` is absent

**Complexity**: M

**Unlocked business events**: `Dashboard.Viewed`

**Dependencies**:
- Epic 1
- `CAP.BSP.002.CYC` — current beneficiary state (stub acceptable)
- `CAP.SUP.001.CON` — `Consent.Granted` gate (stub acceptable)
- `CAP.REF.001.TIE` — tier definitions and thresholds (stub acceptable)

---

### Epic 3 — Web Dashboard — Transaction History
**Objective**: The beneficiary accesses the complete history of their transactions on the web with filters (date, category, status) and sorting; declines display their reason.

**Entry condition**:
- Epic 2 complete (current situation view operational)
- Transactional events available: `Transaction.Authorized` and `Transaction.Declined` from `CAP.BSP.004.AUT` or stub

**Exit condition (DoD)**:
- Transaction history is viewable with filters on: period, spending category, status (authorized / declined)
- Sorting by date and by amount works
- Each declined transaction displays the decline reason (tier rule applied)
- `Dashboard.Viewed` is produced on each access to the history

**Complexity**: M

**Unlocked business events**: `Dashboard.Viewed` enriched with historical context

**Dependencies**:
- Epic 2
- `CAP.BSP.004.AUT` — `Transaction.Authorized` / `Transaction.Declined` stream (stub acceptable)

---

### Epic 4 — Mobile View — Nomadic Consultation
**Objective**: The beneficiary can view their key situation from a mobile device: current tier and main envelope balances, without filters or secondary columns.

**Entry condition**:
- Epic 2 complete (web dashboard operational, data available)

**Exit condition (DoD)**:
- The mobile interface displays: current tier, main envelope balances (without exhaustive category detail)
- No filters, no sorting, no secondary columns — optimized for quick reading
- `Dashboard.Viewed` is produced with the tag `channel=mobile`
- The dignity rule applies identically (progression before restriction)

**Complexity**: M

**Unlocked business events**: `Dashboard.Viewed` (mobile channel)

**Dependencies**:
- Epic 2 (data and consumption logic are reused)

---

### Epic 5 — Connection to Real CORE Capabilities
**Objective**: Replace the stub with real event subscriptions as soon as `BSP.001.SCO`, `BSP.001.PAL`, and `BSP.004.ENV` are operational; decommission the stub without functional regression.

**Entry condition**:
- `CAP.BSP.001.SCO`, `CAP.BSP.001.TIE`, `CAP.BSP.004.ENV` are operational and publishing on the agreed subscription points
- Dashboard functional tests are validated on stub (Epics 2, 3, 4 complete)
- CORE event schemas conform to the stub contract (compatibility check)

**Exit condition (DoD)**:
- The stub is decommissioned
- The dashboard consumes real events without functional regression on both channels (web and mobile)
- Supervision confirms the real event stream in production

**Complexity**: S

**Unlocked business events**: all previous events, now fed by real behavioral data

**Dependencies**:
- `CAP.BSP.001.SCO` — operational
- `CAP.BSP.001.TIE` — operational
- `CAP.BSP.004.ENV` — operational

---

## Dependency Map

| Epic | Depends on | Type |
|------|-----------|------|
| Epic 2 | Epic 1 | Sequential |
| Epic 3 | Epic 2 | Sequential |
| Epic 4 | Epic 2 | Sequential |
| Epic 5 | Epics 2, 3, 4 | Sequential (tests validated) |
| Epic 2 | CAP.BSP.002.CYC | Cross-capability (stub acceptable) |
| Epic 2 | CAP.SUP.001.CON | Cross-capability (blocking gate) |
| Epic 2 | CAP.REF.001.TIE | Cross-capability (stub acceptable) |
| Epic 3 | CAP.BSP.004.AUT | Cross-capability (stub acceptable) |
| Epic 5 | CAP.BSP.001.SCO | Cross-capability (operational required) |
| Epic 5 | CAP.BSP.001.TIE | Cross-capability (operational required) |
| Epic 5 | CAP.BSP.004.ENV | Cross-capability (operational required) |

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Stub/CORE schema divergence — the stub produces events with a slightly different contract than what the CORE finalizes, making Epic 5 more costly | M | M | Define and freeze the event contract (JSON/Avro schema) from Epic 1; the stub must comply with this contract |
| Consent gate unavailable at start of Epic 2 — if CAP.SUP.001.CON has no stub, data access is blocked | L | H | Provide a minimal consent gate stub from Epic 1 (always `Granted` response in development environment) |
| Unstabilized envelope rules — if categories or envelope periodicity change during Epic 2, the display must be refactored | M | M | Align with CAP.REF.001.TIE from Epic 1 on the envelope data model before building the display |

---

## Recommended Sequencing

```
Epic 1 ──────────────────────────────────────────────────────────►
         └─► Epic 2 ──────────────────────────────────────────────►
                      └─► Epic 3 (web history) ──────────────────►
                      └─► Epic 4 (mobile) ───────────────────────►
                                    └─► Epic 5 (real CORE) ───────►
                                         [triggered by CORE operational]
```

**Critical path**: Epic 1 → Epic 2 → Epic 3  
**Parallelizable**: Epic 3 and Epic 4 can be developed in parallel once Epic 2 is complete  
**Epic 5**: outside the internal critical path — triggered by CORE capability availability, independently of Epics 3 and 4 progress

---

## Open Questions

- Gamification (badges, trajectory visualization, milestones) is deferred — what is the target horizon for V1 with gamification, to anticipate extension points in Epic 2?
- The dignity rule ("progression before restriction") is established in the ADR — does it require a dedicated UX workshop to be specified as testable criteria before Epic 2?
- The event contract (schema of the three consumed events) must be co-constructed with the CORE teams from Epic 1 — who is the contact on the BSP.001 and BSP.004 side?
