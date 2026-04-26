---
id: ADR-BCM-URBA-0013
title: "Processes Remain External to the BCM and Split into Business and Resource Processes"
status: Proposed
date: 2026-03-23

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
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0007
  - ADR-BCM-URBA-0008
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010

supersedes: []

tags:
  - BCM
  - process
  - orthogonality
  - business-object
  - business-event
  - resource
  - abstraction
  - orchestration

stability_impact: Structural
---

# ADR-BCM-URBA-0013 — Processes Remain External to the BCM and Split into Business and Resource Processes

## Context

The BCM describes a structural model of capabilities, objects, events, resources, and relations.

The referential already introduces two levels of abstraction:
- a **business** level based on business objects, business events, and business subscriptions;
- a **resource** level based on resources, resource events, and resource subscriptions.

In parallel, process artifacts serve to describe orchestration sequences.
They consume the BCM but must not become a decomposition axis of its structure.

A clarification is necessary to explicitly distinguish:
- the **structure** of the BCM model;
- the **processual views** that build on this model.

## Decision

Processes **are not part of the BCM structure**.

They constitute **external orchestration views** built on BCM model elements.

Two families of processes are recognized:

1. **Business processes**
   - Based on business-level abstractions:
     `business object`, `business event`, `business subscription`.
   - They describe generalist, stable, value-oriented business orchestrations.

2. **Resource processes**
   - Based on resource-level abstractions:
     `resource`, `resource event`, `resource subscription`.
   - They describe applied, explicit orchestrations subject to strong operational constraints.

### Structuring Rules

1. The BCM remains structured by **capabilities** and not by processes.
2. **L2 capabilities** remain the urbanization pivot and the main relationship anchor point of the model.
3. A process does not, by itself, create a capability, a capability boundary, or an L1/L2/L3 level.
4. A business process must only reference business-type elements.
5. A resource process must only reference resource-type elements.
6. The transition from the business level to the resource level belongs to an alignment or traceability relation, not a merging of the two levels.
7. Process artifacts remain documentary and descriptive; they do not replace URBA ADRs nor FUNC ADRs.

### Verifiable Criteria

- No process is used as the main decomposition criterion of a BCM capability.
- Every published process is typed as either `business process` or `resource process`.
- Every business process references exclusively business objects/events/subscriptions.
- Every resource process references exclusively resources/events/subscriptions.
- The structuring relations of the model remain anchored on capabilities, primarily at the L2 level.

## Justification

This decision allows:
- preserving the stability of the BCM as a structural referential;
- clearly distinguishing business abstraction from operational breakdown;
- preventing a conjunctural process flow from deforming capability boundaries;
- keeping processes as reading, explanation, and orchestration views.

It also makes compatible:
- a generalist business reading, useful for transverse understanding;
- a resource reading, useful for expliciting execution constraints.

### Alternatives Considered

- **Integrating processes into the BCM structure** — rejected: mixes processual view with referential structure.
- **Keeping only one type of process** — rejected: loses the distinction between business abstraction and operational constraints.
- **Directly attaching processes to L1/L2/L3 levels as a structuring axis** — rejected: contradiction with the pivot role of capabilities.

## Impacts on the BCM

### Structure

- No change to the L1/L2/L3 breakdown.
- No new capability is created solely by a process.
- Confirmation of the structural role of capabilities and the external role of processes.

### Events (if applicable)

- No change to the event meta-model.
- Clarification that business events feed business processes, and resource events feed resource processes.

### Mapping SI / Data / Org

- **SI**: resource processes can explicit applied orchestration constraints without modifying capability boundaries.
- **DATA**: the business / resource distinction improves the readability of manipulated objects.
- **ORG**: processes remain explanation and coordination views, not structural units of responsibility.

## Consequences

### Positive

- Clear distinction between BCM structure and orchestration.
- Reinforced coherence with the two-level meta-model.
- Reduction of the risk of process-centric drift of the BCM.
- Better readability of process artifacts.

### Negative / Risks

- Requires explicit documentary discipline between structural views and processual views.
- May require complementary traceability rules between business processes and resource processes.

### Accepted Debt

- The detailed formalism of traceability links between business processes and resource processes remains to be specified in a complementary guide or template.
- Naming and publication conventions for process artifacts may be refined later.

## Governance Indicators

- Criticality level: High.
- Recommended review date: 2027-03-23.
- Expected stability indicator:
  - no capability breakdown justified solely by a process;
  - explicit typing of 100% of published processes;
  - absence of mixing between business and resource abstractions in a single process artifact.

## Traceability

- Workshop: BCM urbanization framing — structure vs. orchestration.
- Participants: IS Urbanization, Architecture, Business domain leads.
- References:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0007
  - ADR-BCM-URBA-0008
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010
  - Template `externals-templates/business-process/template-business-process.yaml`
