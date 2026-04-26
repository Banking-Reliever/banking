---
id: ADR-BCM-URBA-0006
title: "Technical Asset Naming Guided by the BCM (L2 Anchoring)"
status: Suspended
date: 2026-02-26
suspension_date: 2026-03-10
suspension_reason: >
  Reflects a maturity level not yet present in the company.
  Risk of causing more confusion than clarity at this point.

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

impacted_capabilities: []   # transversal
impacted_events: []         # transversal
impacted_mappings:
  - SI
  - DATA
  - ORG

related_adr:
  - ADR-BCM-GOV-0001  # GOV → URBA → FUNC hierarchy
  - ADR-BCM-URBA-0001  # Extended TOGAF zoning
  - ADR-BCM-URBA-0002  # 3 levels
  - ADR-BCM-URBA-0003  # 1 capability = 1 responsibility
  - ADR-BCM-URBA-0005  # BCM-guided contracts (APIs/events)

supersedes: []
tags:
  - naming
  - capability
  - events
  - topic
  - api
  - database
stability_impact: Structural
---

# ADR-BCM-URBA-0006 — Technical Asset Naming Guided by the BCM (L2 Anchoring)

## Context

The IS contains many technical assets (event topics, APIs, databases, schemas, application components, serverless functions, buckets...).
Without a common convention, we observe:
- difficulty in linking an asset to a business responsibility,
- naming heterogeneity between teams,
- weak traceability between functional urbanization and technical implementation.

The BCM is the stable business responsibility referential, and the L2 level is the urbanization arbitration pivot (stability vs. precision).

## Decision

### 1) Mandatory anchoring to an L2 capability

Any technical asset must be attached to ONE unique ownership capability, at the L2 level.

- The attachment is materialized by including the L2 ID in the asset name.
- The attachment must not depend on a human label: only on a stable identifier.

### 2) Naming convention

The standard pattern is:

`<capability_l2_id>.<asset_type>.<asset_name>[.<qualifier>...]`

- `<capability_l2_id>`: stable identifier (e.g., `bsp-005-sin-03`)
- `<asset_type>`: `topic | evt | api | bff | spa | svc | fn | db | schema | bucket | queue | job | blob ...`
- `<asset_name>`: short and stable business name (kebab-case)
- `<qualifier>`: major version / variant (`v1`, `dlq`, `public`, `private`...)

Rules:
- kebab-case `[a-z0-9-]`
- hierarchical separator `.`
- no accents / no spaces

Complementary BCM conventions (mandatory for functional assets):
- `OBJ.<ZONE>.<L1>.<CODE>` for business objects
- `RES.<ZONE>.<L1>.<CODE>` for operational resources
- `ABO.METIER.<ZONE>.<L1>.<CODE>` for business subscriptions
- `ABO.RESSOURCE.<ZONE>.<L1>.<CODE>` for resource subscriptions

These conventions are distinct:
- a business object (`OBJ.*`) represents a functional abstraction,
- a resource (`RES.*`) represents an operational artifact implementing that business object.

### 3) Special cases

- If an asset is truly transverse, its ownership must be placed in a transverse capability (Support, Referential, DATA_ANALYTIQUE, ECHANGE_B2B, Canal) in accordance with zoning.
- "Catch-all" components (multi-capabilities) are considered a decomposition debt: ownership must remain unique, and a splitting plan should be considered.

### 4) Mapping registry

In addition to naming, a mapping registry is maintained (e.g., `bcm/mappings/assets.yaml`) to describe:
- L2 capability owner
- responsible team
- environment(s)
- technology / platform
- criticality / SLA
- links to repo / IaC / runbooks

The registry constitutes the exhaustive information source.
The name must not be overloaded to replace a registry.

## Justification

- The L2 level is the right urbanization decision level: precise enough to guide the IS, stable enough to avoid frequent renamings.
- The "1 capability = 1 responsibility" rule guarantees clear ownership and reduces ambiguities.
- The "BCM-guided contracts" approach ensures coherence between model and interfaces (APIs/events).

### Alternatives Considered

- Free naming by team — rejected because of heterogeneity and loss of traceability.
- Naming anchored to the application rather than the capability — rejected because of physical IS coupling.
- Naming at L3 level — rejected because too unstable (L3 is transitional).

## Impacts on the BCM

### Structure

- Need for stable L2 identifiers (not dependent on labels).

### Events (if applicable)

- Event/topic conventions become coherent with emitting/consuming capabilities.

### Mapping SI / Data / Org

- Reinforcement of the Capability ↔ Technical Assets mapping via a dedicated registry.

## Consequences

### Positive
- Immediate traceability: asset → responsibility (L2).
- Cross-team naming homogeneity.
- Measurable urbanization (capability coverage).
- Reduction of project "shadow naming".

### Negative / Risks
- Initial adoption cost.
- Risk of renaming if L2 IDs are not stabilized quickly.
- Risk of arbitrary ownership if "transverse vs. business" rules are not applied.

### Accepted Debt

- Some legacy assets cannot be renamed immediately. They will be progressively migrated during evolutions.

## Governance Indicators

- Criticality level: Moderate (naming convention).
- Recommended review date: 2028-02-26.
- Expected stability indicator: 100% of new assets named according to the convention.

## Traceability

- Workshop: BCM governance, project feedback, event storming big picture
- Participants: EA / Urbanization
- References: ADR-BCM-URBA-0001, ADR-BCM-URBA-0002, ADR-BCM-URBA-0003, ADR-BCM-URBA-0005
