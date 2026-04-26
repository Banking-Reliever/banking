---
id: ADR-BCM-URBA-0001
title: "TOGAF-Extended IS BCM (7 Zones)"
status: Proposed
date: 2026-02-27

family: URBA

decision_scope:
  level: Cross-Level
  zoning:
    - PILOTAGE
    - SERVICES_COEUR
    - SUPPORT
    - REFERENTIEL
    - ECHANGE_B2B
    - CANAL
    - DATA_ANALYTIQUE

impacted_capabilities: []
impacted_events: []
impacted_mappings:
  - SI
  - DATA
  - ORG

related_adr:
  - ADR-BCM-GOV-0001  # GOV → URBA → FUNC hierarchy
supersedes: []

tags:
  - BCM
  - Modeling
  - TOGAF
  - Zoning

stability_impact: Structural
---

# ADR-BCM-URBA-0001 — TOGAF-Extended IS BCM (7 Zones)

## Context
A map is needed that provides the foundations of the information system.
This mapping must make it possible to individualize and assign responsibility for information production within the IS.

It must allow coordination and location of the various applications.

Without clear structuring, the risk is twofold:
- a "flat" BCM (without zoning) mixes steering, business production, and support,
- a non-standardized custom BCM complicates dialogue with vendors, partners, and alignment with market best practices.

The TOGAF methodology provides a first level of standardization that frames the production capabilities of an IS by dividing its capabilities into different zones.

However, for a modern mutual/insurance company, TOGAF alone (3 zones: Steering, CORE, Support) is **insufficient** to address:
- the distinction between core business capabilities and transverse exposure capabilities (omnichannel journeys, portals),
- master referential management (shared pivot data),
- exchanges with the external ecosystem (partners, delegates, regulator, providers),
- DATA_ANALYTIQUE capabilities (governance, BI, AI) that are neither pure "support" nor "business production".

Hence the proposed extension to **7 zones**:
- **PILOTAGE**: enterprise steering, compliance, governance
- **SERVICES COEUR**: core business (products, distribution, subscription, contracts, claims, customer service...)
- **SUPPORT**: transverse IT support functions (cybersecurity, document management, internal interoperability, accounting...)
- **REFERENTIEL**: shared master referentials (Person, Address, Contract, Product, Banking, Organization...)
- **ECHANGE_B2B**: exchanges with the external ecosystem (partner onboarding, exchange hub, external APIs, third-party flow traceability)
- **CANAL**: omnichannel exposure and user journeys (member/company portals, advisor workstation, digital acquisition, contact center)
- **DATA_ANALYTIQUE**: data governance, ingestion, data platforms, BI/reporting, advanced analytics & AI

## Decision
- The BCM is structured according to the **extended TOGAF model** with seven main zones:
  - **PILOTAGE**: steering and compliance capabilities
  - **SERVICES COEUR**: core business capabilities
  - **SUPPORT**: transverse support capabilities
  - **REFERENTIEL**: master referentials and shared pivot data
  - **ECHANGE_B2B**: exchanges with the external ecosystem (partners, delegates, regulator, providers)
  - **CANAL**: omnichannel exposure and end-user journeys
  - **DATA_ANALYTIQUE**: data governance, ingestion, platforms, BI, analytics & AI

- Each capability has a **zoning** attribute in `bcm/capabilities.yaml` referring to one of these seven zones.

- Generated views (Mermaid, graphs) must visualize this separation to facilitate urbanization arbitrations.

- Clear disambiguation rules:
  - **CANAL** (UX, journeys, front exposure) ≠ **Channels & Intermediation** (CORE: distribution rules + networks)
  - **ECHANGE_B2B** (ecosystem, external flows, SLA) ≠ **Interoperability** (SUPPORT: internal IS integration)
  - **DATA_ANALYTIQUE** (decoupled analytics ingestion) ≠ **Interoperability** (transactional operational exchanges)
  - **REFERENTIEL** (shared master data) ≠ production capabilities using these referentials

## Justification
TOGAF is a recognized standard that allows:
- a common language with the ecosystem (vendors, integrators, consultants),
- a clear separation between steering, production, and support,
- better governance of IS coverage (preventing support from overflowing into business, or steering being buried in CORE).

**Extension with 4 additional zones**:

1. **REFERENTIEL**: Referentials (Person, Address, Contract, Product...) are **pivot data** consumed by all zones. Isolating them allows:
   - clear master data governance (ownership, quality, lifecycle),
   - avoiding duplication and inconsistencies,
   - separately steering "referential" investments vs. "production".

2. **ECHANGE_B2B**: The "ecosystem facade" (partners, delegates, regulator, care networks, providers) has specific constraints (SLA, onboarding, traceability, standardized formats, proofs) distinct from internal interoperability (SUPPORT). Separating them allows:
   - steering external relations vs. internal integration,
   - managing regulatory requirements on exchanges (GDPR, traceability, evidentiary archiving),
   - industrializing partner onboarding and external API governance.

3. **CANAL**: The omnichannel experience (portals, journeys, advisor workstation, contact center) is neither "Customer Service" (CORE: business processing of requests) nor pure "Support". It is the **exposure layer** to end users. Separating it allows:
   - steering user experience independently of business production,
   - avoiding confusion between "business capability" (e.g., Subscription) and "access channel" (e.g., digital funnel),
   - measuring and optimizing journeys (conversion, abandonment, NPS/CSAT).
   It groups all pure applications allowing the backend of the company's information system to be interfaced, with the backend carried by the CORE zone.

4. **DATA_ANALYTIQUE**: Data governance, analytics ingestion, BI, and AI are neither "transactional production" (CORE) nor pure "technical support". Isolating them allows:
   - steering the data strategy (governance, quality, data products),
   - distinguishing analytical flows (decoupled, batch/stream) vs. transactional flows (operational),
   - separately valuing analytics & AI investments.

### Alternatives Considered

- **Pure 3-zone TOGAF** — rejected because it is insufficient to address omnichannel journeys, ecosystem exchanges, master data, analytics.
- **Everything in SUPPORT** — rejected because of lost visibility and mixing of heterogeneous responsibilities.
- **Fully custom model (without TOGAF)** — rejected because of loss of alignment with standards, training cost.
- **8+ zones** (e.g., separating "Payments" from "ECHANGE_B2B") — deferred (added if needed, currently limited to 7 zones for readability).

## Impacts on the BCM

### Structure

- Impacted capabilities: all (mandatory addition of the `zoning` field in `capabilities.yaml` with one of the 7 values).
- L1/L2/L3 + zoning (two orthogonal dimensions).
- Placement rules (testable via validation):
  - Steering → **PILOTAGE**
  - Core insurance/mutual business → **SERVICES COEUR**
  - Transverse IT support functions (cybersecurity, DMS, internal interoperability) → **SUPPORT**
  - Shared master data → **REFERENTIEL**
  - Exchanges with external parties → **ECHANGE_B2B**
  - User journeys and exposure → **CANAL**
  - Data governance, BI, analytics, AI → **DATA_ANALYTIQUE**
- Mandatory disambiguation:
  - "Channels & Intermediation" (distribution rules) stays in **CORE**, "Canal" (UX journeys) is **CANAL**
  - "Interoperability" (internal IS) stays in **SUPPORT**, third-party exchanges go to **ECHANGE_B2B**
  - Transactional flows → **SUPPORT/Interoperability**, analytics flows → **DATA_ANALYTIQUE/Ingestion**

### Events (if applicable)

- No direct impact on business events.

### Mapping SI / Data / Org

- Applications, data domains, and teams can be **mapped** by zone, facilitating coverage and responsibility analyses.

## Consequences
### Positive
- **Enhanced readability**: clear distinction between what (CORE), how we steer (PILOTAGE), how we support (SUPPORT), what we share (REFERENTIEL), how we expose (CANAL), how we exchange (ECHANGE_B2B), how we analyze (DATA_ANALYTIQUE).
- **Standardization**: TOGAF alignment facilitates onboarding, external reviews, benchmarks.
- **Governance**: placement rules (7 zones) become testable and auditable.
- **Communication**: simplified dialogue with partners/vendors familiar with TOGAF, enriched by business-specific zones for the insurance/mutual context.
- **Differentiated steering**: 
  - referential investments (master data) vs. production,
  - omnichannel strategy (CANAL) vs. business capabilities (CORE),
  - separate DATA_ANALYTIQUE governance,
  - ecosystem roadmap (ECHANGE_B2B) vs. internal integration (SUPPORT).
- **Disambiguation**: no more risk of mixing customer journeys (CANAL) and business capability (CORE), or third-party exchanges (ECHANGE_B2B) and internal interoperability (SUPPORT).

### Negative / Risks
- **Complexity**: 7 zones instead of 3 → more rules to master, risk of debates on placement (e.g., "Notifications" → CANAL or SUPPORT? "Partner portal" → CANAL or ECHANGE_B2B?).
- **Training**: requires team onboarding on the **extended** TOGAF vocabulary (custom zones).
- **Rigidity**: possible debates on the placement of certain capabilities (e.g., "Payment management" → ECHANGE_B2B or CORE?).
- **Infrastructure vs. capability distinction**: transverse platforms (ESB, API Gateway, event bus) are **not** capabilities to be zoned. What must be localized are the **topics/events produced by each capability** and the **business/IS capabilities** using these platforms.
- **Reinforced governance**: requires documented placement criteria and regular reviews to avoid drift.
- **Tooling**: generated views must support 7 zones (visual complexity, need for a clear legend).

### Accepted Debt
- Some capabilities may have **multiple zones** (e.g., an API exposed in CANAL **and** consuming ECHANGE_B2B). For now, we force a **unique placement** (main zone) and document interactions via capability ADRs.

## Governance Indicators

- Criticality level: High (structuring cross-cutting decision).
- Recommended review date: 2028-01-21.
- Expected stability indicator: all capabilities have a `zoning` attribute among the 7 values.

## Traceability

- Workshop: Urbanization 2026-02-27
- Participants: EA / Urbanization, yremy, acoutant
- References: —
