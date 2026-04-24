---
id: ADR-BCM-FUNC-0001
title: "L1 Breakdown of the BUSINESS_SERVICE_PRODUCTION Zone into 2 Capabilities"
status: Proposed
date: 2026-02-26

family: FUNC

decision_scope:
  level: L1
  zoning:
    - BUSINESS_SERVICE_PRODUCTION

impacted_capabilities:
  - CAP.BSP.001
  - CAP.BSP.002
impacted_events: []
impacted_mappings:
  - SI
  - ORG

related_adr:
  - ADR-BCM-GOV-0001   # GOV → URBA → FUNC hierarchy
  - ADR-BCM-URBA-0001  # Extended TOGAF zoning
  - ADR-BCM-URBA-0002  # 3 levels L1/L2/L3
  - ADR-BCM-URBA-0009  # Complete capability definition
  - ADR-BCM-URBA-0004  # Deciding at the right level

supersedes: []

tags:
  - BCM
  - BSP
  - L1
  - breakdown
  - value-chain
  - foodaroo

stability_impact: Structural


---

# ADR-BCM-FUNC-0001 — L1 Breakdown of the BUSINESS_SERVICE_PRODUCTION Zone

## Context

The **BUSINESS_SERVICE_PRODUCTION** (BSP) zone represents the core business of Foodaroo. It concentrates the service production capabilities: from partner enrollment and product offerings to order placement and delivery from the customer perspective.

The L1 breakdown of this zone must:
- Reflect the **value chain** specific to the food delivery marketplace from end to end,
- Respect the **1 capability = 1 responsibility** principle (ADR-BCM-URBA-0009 Complete capability definition),
- Be stable enough to organize responsibilities, investments, and IT transformation,
- Remain readable (no more than ~10 L1 capabilities per zone, cf. ADR-BCM-URBA-0004).

Key considerations:
- **Platform vs Experience**: The business naturally splits between the supplier side (restaurants, shops, etc.) and the consumer side (customers ordering and receiving deliveries).
- **Two-sided marketplace**: Foodaroo operates as a platform connecting multiple types of merchants with end consumers.

## Decision

The BUSINESS_SERVICE_PRODUCTION zone is structured into **2 L1 capabilities**, organized according to the two-sided marketplace value chain:

| ID | Name | Responsibility | Owner |
|---|---|---|---|
| CAP.BSP.001 | Foodaroo Platform | Enrollment and auction management from a merchant point of view (restaurants, bookshops, taxis, supermarkets, clothes stores) | foodex |
| CAP.BSP.002 | Foodaroo Experience | Order placement and delivery from a final customer point of view | foodex |

### Breakdown Rules

1. Each L1 capability represents an **autonomous business responsibility domain**, not an application or a process.
2. Boundaries are defined by clearly identified **transfer points**:
   - BSP.001 (Platform) → BSP.002 (Experience): The transfer occurs when a merchant's offering becomes available for customer ordering.
   - BSP.002.ORD (Order Placement) → BSP.002.DEL (Delivery): The transfer occurs when an order is confirmed and ready for delivery assignment.

### Disambiguation Rules

- **Foodaroo Platform** (BSP.001) = Merchant-facing capabilities: enrollment, catalog management, auction participation, merchant notifications.
- **Foodaroo Experience** (BSP.002) = Customer-facing capabilities: browsing, ordering, delivery tracking, receiving orders.
- **Platform** ≠ **Experience**: BSP.001 focuses on supply-side operations; BSP.002 focuses on demand-side operations.

### Verifiable Criteria

- Every L1 BSP capability has an identified business owner.
- No L1 BSP capability is named after an application or vendor.
- The 2 capabilities cover the entire Foodaroo value chain (from merchant enrollment to customer delivery).
- Each L1 BSP capability can be broken down into L2 without scope overlap.

## Justification

This breakdown follows the **two-sided marketplace value chain**, adapted to the Foodaroo context:

```text
Foodaroo Platform (BSP.001)          Foodaroo Experience (BSP.002)
─────────────────────────────        ──────────────────────────────
Merchant Enrollment                  Customer Browsing
    ↓                                    ↓
Catalog & Offerings                  Order Placement
    ↓                                    ↓
Auction & Pricing              →     Delivery & Fulfillment
    ↓                                    ↓
Merchant Notifications               Customer Satisfaction
```

The 2 L1 capabilities allow:
- **Complete coverage** of the marketplace lifecycle,
- **Sufficient granularity** to differentiate business and IT responsibilities,
- **Stability**: this breakdown reflects the natural split in two-sided platforms,
- **Alignment** with existing business organization (merchant operations vs. customer operations are typically distinct teams).

**Foodaroo Platform** is maintained as an autonomous L1 because:
- It covers the complete merchant lifecycle (enrollment → catalog → auction → notifications),
- It has its own ecosystem interactions (restaurants, shops, delivery partners),
- It has distinct ownership responsibilities from the customer-facing side.

**Foodaroo Experience** is formalized as L1 because:
- It is the core of the customer promise (order → receive),
- It has 2 L2 capabilities identified (Order Placement, Delivery),
- It has its own ecosystem interactions (customers, couriers).

### Alternatives Considered

- **Single L1 for the entire marketplace** — rejected because it would be too broad and mix supply-side and demand-side responsibilities.
- **3+ L1 capabilities (separating delivery as L1)** — rejected because delivery is tightly coupled with the order experience; the split Order/Delivery is more appropriate at L2.
- **Separate L1 for each merchant type** — rejected because all merchant types share the same enrollment and auction mechanisms; differentiation can happen at L2 or L3 if needed.

## Impacts on the BCM

### Structure

- Creation/confirmation of 2 L1 capabilities in the BSP zone in file `bcm/capabilities-L1.yaml`.
- Each L1 will be broken down into L2 by subsequent FUNC ADRs.
- Numbering: CAP.BSP.001 to CAP.BSP.002.

### Events (if applicable)

- No direct impact. Events will be defined during the L2 breakdown of each capability.

### Mapping SI / Data / Org

- **SI**: Each L1 BSP capability constitutes a functional domain to which applications must be mapped.
- **ORG**: Each L1 BSP capability has an identified business owner, which structures organizational responsibilities.

## Consequences

### Positive

- **Readable value chain**: The 2 L1 capabilities cover the complete marketplace lifecycle intuitively.
- **Clear ownership**: Each L1 has an identified business owner.
- **Stable base for L2**: The L1 breakdown is sufficiently consensual to serve as a foundation for subsequent functional decisions.
- **Comparability**: This breakdown aligns with standard two-sided marketplace patterns, facilitating benchmarks and discussions with vendors/integrators.
- **Documented disambiguation**: Boundaries between Platform and Experience are explicitly traced.

### Negative / Risks

- **Platform/Experience boundary**: The transfer point (when offerings become available for ordering) may require clarification for specific merchant types.
- **Merchant diversity**: Different merchant types (restaurants, bookshops, taxis, etc.) may have specific needs not fully captured at L1.

### Accepted Debt

- The L2 breakdown of each L1 is not yet fully formalized. BSP.002 L2 breakdown will be addressed in ADR-BCM-FUNC-0002.
- Interactions between L1 capabilities (e.g., Platform → Experience) are not yet modeled as events.

## Governance Indicators

- Criticality level: High (foundational breakdown of the BSP zone).
- Recommended review date: 2028-02-26.
- Expected stability indicators:
  - 2 L1 BSP capabilities present in `capabilities-L1.yaml` with owner specified.
  - No scope overlap identified between L1 capabilities.
  - Each L1 is broken down into at least 2 L2 within 12 months.

## Traceability

- Workshop: RFC "010 - Carto Capacités SI" — Business Service Production section
- Participants: EA / Urbanisation, Business Architecture
- References:
  - RFC: `010 -RFC - Carto Capacités SI .md`
  - Capabilities file: `bcm/capabilities-L1.yaml`
  - ADR-BCM-URBA-0001 — Extended TOGAF zoning
  - ADR-BCM-URBA-0002 — 3 levels L1/L2/L3
  - ADR-BCM-URBA-0009 — Complete capability definition
