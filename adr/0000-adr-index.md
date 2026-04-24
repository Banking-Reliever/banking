# ADR Index (BCM)

Reference index of ADRs present in this repository.

## Statuses

- Proposed: under discussion
- Accepted: validated
- Suspended: on hold (maturity level not reached or clarification needed)
- Deprecated: no longer to be used
- Superseded: replaced by another ADR

## Official Families
- GOV: governance of BCM decisions
- URBA: structuring principles of the model
- FUNC: functional application decisions

## Decision Hierarchy

```text
GOV
    ↓
URBA
    ↓
FUNC
```

Reading rules:
- A FUNC ADR cannot contradict an URBA ADR.
- An URBA ADR must respect GOV principles.
- Any BCM evolution goes through an Accepted ADR.

## ADRs Present in the Repo

### GOV — Governance

| ID | Title | Status | File |
|---|---|---|---|
| ADR-BCM-GOV-0001 | BCM Decision Governance – GOV / URBA / FUNC Hierarchy | Proposed | [ADR-BCM-GOV-0001.md](ADR-BCM-GOV-0001.md) |
| ADR-BCM-GOV-0002 | Arbitration Mechanism and BCM Governance Board | Proposed | [ADR-BCM-GOV-0002.md](ADR-BCM-GOV-0002.md) |
| ADR-BCM-GOV-0003 | Periodic Stability Review | Proposed | [ADR-BCM-GOV-0003-revue-de-stabilité-périodique.md](ADR-BCM-GOV-0003-revue-de-stabilité-périodique.md) |

### URBA — Architecture

| ID | Title | Status | File |
|---|---|---|---|
| ADR-BCM-URBA-0001 | TOGAF-Oriented BCM (Extended Zoning) | Proposed | [ADR-BCM-URBA-0001](ADR-BCM-URBA-0001-BCM-SI-orienté-TOGAF.md) |
| ADR-BCM-URBA-0002 | BCM Structured in 3 Levels (L1/L2/L3) | Proposed | [ADR-BCM-URBA-0002](ADR-BCM-URBA-0002-trois-niveaux.md) |
| ADR-BCM-URBA-0003 | One Capability = One Responsibility, Not an Application | Superseded | [ADR-BCM-URBA-0003](ADR-BCM-URBA-0003-1-capa-1responsabilité.md) |
| ADR-BCM-URBA-0004 | Deciding at the Right Level (L1/L2/L3) | Proposed | [ADR-BCM-URBA-0004](ADR-BCM-URBA-0004-bon-niveau-de-decision.md) |
| ADR-BCM-URBA-0005 | Interface Contracts Guided by BCM | Suspended | [ADR-BCM-URBA-0005](ADR-BCM-URBA-0005-APIs-fonctionnelles-guidees-par-BCM.md) |
| ADR-BCM-URBA-0006 | Technical Asset Naming Guided by BCM (L2 Anchoring) | Suspended | [ADR-BCM-URBA-0006](ADR-BCM-URBA-0006-Nommage-des-assets-techniques-guidé-par-la-BCM.md) |
| ADR-BCM-URBA-0007 | Normalized Event Meta-Model Guided by Capabilities | Proposed | [ADR-BCM-URBA-0007](ADR-BCM-URBA-0007-meta-modele-evenementiel-normalise.md) |
| ADR-BCM-URBA-0008 | Event Modeling — Two-Level Guide | Proposed | [ADR-BCM-URBA-0008](ADR-BCM-URBA-0008-modelisation-evenements.md) |
| ADR-BCM-URBA-0009 | Complete Capability Definition — Responsibility, Event Production and Consumption | Proposed | [ADR-BCM-URBA-0009](ADR-BCM-URBA-0009-definition-capacite-evenementielle.md) |
| ADR-BCM-URBA-0010 | L2 Capabilities as the Urbanization Pivot and Model Relationship Anchor Point | Proposed | [ADR-BCM-URBA-0010](ADR-BCM-URBA-0010-les-capacites-L2-pivot-urbanisation.md) |
| ADR-BCM-URBA-0011 | Local Complexity Decompression via L3 While Maintaining L2 as Pivot | Proposed | [ADR-BCM-URBA-0011](ADR-BCM-URBA-0011-Decompression-locale-de-la-complexité-par-L3-tout-en-conservant-L2-comme-pivot.md) |
| ADR-BCM-URBA-0012 | Introduction of a Canonical Business Concept | Proposed | [ADR-BCM-URBA-0012](ADR-BCM-URBA-0012-Introduction-d-un-concept-métier-canonique.md) |
| ADR-BCM-URBA-0013 | Processes Remain External to BCM and Split into Business and Resource Processes | Proposed | [ADR-BCM-URBA-0013](ADR-BCM-URBA-0013-processus-sont-externes-à-la-BCM-et-se-déclinent-en-métier-et-ressource.md) |

### FUNC — Functional

| ID | Title | Status | File |
|---|---|---|---|
| ADR-BCM-FUNC-0001 | L1 Breakdown of BUSINESS_SERVICE_PRODUCTION Zone into 2 Capabilities | Proposed | [ADR-BCM-FUNC-0001](ADR-BCM-FUNC-0001-L1-breakdown-BSP.md) |
| ADR-BCM-FUNC-0002 | L2 Breakdown of BSP.002 Foodaroo Experience into 2 Capabilities | Proposed | [ADR-BCM-FUNC-0002](ADR-BCM-FUNC-0002-L2-breakdown-BSP002-Foodaroo-Experience.md) |
| ADR-BCM-FUNC-0003 | Functional Behavior of CAP.BSP.002.ORD — Order Placement | Proposed | [ADR-BCM-FUNC-0003](ADR-BCM-FUNC-0003-order-placement-behavior.md) |

## Current Coverage

- **GOV**: 3 ADRs (2 structured according to template, 1 empty draft)
- **URBA**: 13 ADRs (1 Superseded, all conform to template)
- **FUNC**: 3 ADRs

## References

- Global Framework: [README.md](../README.md)
- Governance: [ADR-BCM-GOV-0001.md](ADR-BCM-GOV-0001.md), [ADR-BCM-GOV-0002.md](ADR-BCM-GOV-0002.md)
- Official Template: [template-adr-bcm.md](template-adr-bcm.md)
