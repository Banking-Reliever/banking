---
id: ADR-BCM-URBA-0010
title: "L2 Capabilities as the Urbanization Pivot and Model Relationship Anchor Point"
status: Proposed
date: 2026-03-11

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
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0004
  - ADR-BCM-URBA-0007
  - ADR-BCM-URBA-0009

supersedes: []

tags:
  - BCM
  - Urbanization
  - L2
  - Pivot
  - Traceability
  - Mapping
  - Decoupling

stability_impact: Structural
---

# ADR-BCM-URBA-0010 — L2 Capabilities as the Urbanization Pivot and Model Relationship Anchor Point

## Context

The BCM must simultaneously:
- remain readable for the business,
- guide IS urbanization,
- enable traceability toward applications, data flows, and the organization,
- without drifting into a purely technical map nor into a process map.

The principles already established in the repository converge on the fact that the **L2** level is the right arbitration level:
- the model is structured in **L1 / L2 / L3**, with a need for actionability without losing stability;
- **L3** remains exceptional and must not become the standard steering level;
- business events and interface contracts are already designed around attachment to an **L2 capability**;
- logical / physical decoupling requires not making the target structure dependent on existing applications;
- technical assets and mappings must be anchored on a stable identifier and not on an application label.

In practice, the repository contains several types of elements: capabilities, business events, resource events, business objects, resources, subscriptions, SI / DATA / ORG mappings, and potentially tomorrow application, technical, or external referentials. Without an explicit transverse rule, there is a risk of drift:
- multiplication of direct links between low-level elements,
- excessive coupling between business referential and technical implementation,
- loss of model readability,
- ownership ambiguities,
- inflation of ungoverned opportunistic relations.

The need is therefore to formally establish the **L2** capability as the **urbanization pivot**, i.e., as the default anchor point for relations between the BCM model and other referentials.

## Decision

### 1) The L2 level is the mandatory urbanization pivot of the BCM model

Any structuring relation entering the IS urbanization scope must, by default, be expressed via an **L2 capability**.

By "structuring relation", we mean in particular:
- the attachment of a business event,
- the attachment of a business object or resource,
- the attachment of an application or application component,
- the attachment of a flow or data domain, a data product,
- the attachment of an organizational responsibility,
- the attachment of a transverse control or requirement.


The L1 serves for framing and readability.
The L3 serves to specify a case when necessary.
The **L2** is the normal level for anchoring urbanization relations.

### 2) Every element of the meta-model must reference an L2 capability when it carries a responsibility, ownership, or business purpose

Elements described in the meta-model, in particular those covered by ADR 007, must rely on an L2 capability whenever they express:
- an emission,
- a consumption,
- a business responsibility,
- a functional scope,
- a traceability or audit need.

Expected examples:
- every **business event** references an emitting L2 capability;
- every **business consumption** of an event references a consuming L2 capability;
- every **business object** or **resource** carries an attachment L2 capability;
- every **subscription** (business or resource) indicates the consuming L2 capability;
- every **application mapping** goes first through an L2 capability, then only toward the relevant technical artifacts.

### 3) Direct relations between non-L2 elements are allowed only in two cases

#### Case A — Strictly operational relation
A direct relation is allowed when it is purely necessary for exploitation, inventory, or technical deployment, without modifying the urbanistic reading of the model.

Examples:
- application ↔ server,
- application ↔ technical database,
- topic ↔ cluster,
- component ↔ runtime,
- job ↔ scheduler,
- API ↔ gateway.

These relations must be carried in a dedicated **operational mapping registry**.
They do not replace the attachment of these elements to an L2 capability.

#### Case B — Exceptional, explicitly motivated relation
A direct relation outside the L2 pivot is allowed when a regulatory, audit, security, continuity, or compliance requirement explicitly demands it.

Examples:
- application ↔ DORA process,
- application ↔ resilience control,
- component ↔ regulatory requirement,
- flow ↔ compliance device.

In this case:
- the direct relation must be **motivated**,
- the motivation must be documented in the referential or in an ADR,
- the relation must not short-circuit the main attachment to the L2 capability.

### 4) The L2 pivot takes precedence over direct links for all reference views

Reference views produced from the repository must prioritize the following reading chains:
- **L2 Capability → Events → Applications**
- **L2 Capability → Business Objects / Resources → Data**
- **L2 Capability → Owner / team / responsibility**
- **L2 Capability → Controls / requirements / compliance**

Direct links between non-L2 elements must appear only:
- in specialized operational views,
- or in compliance views explicitly identified as such.

### 5) Dedicated registries carry the details, not the business identifiers

An element's name must not be overloaded to replace information carried by a registry.

The following details must be carried in dedicated mappings or registries:
- an application implementing multiple components,
- an application deployed on multiple servers,
- an interface exposed via multiple channels,
- an application affected by one or more DORA controls,
- a temporary technical dependency.

The BCM model retains the business responsibility; the operational registry carries the technical materialization.

### 6) Verifiable criteria

The decision is considered respected if the following rules are true:

- R1. Every publishable business element of the meta-model references at least one L2 attachment capability.
- R2. Every business event has one and only one emitting L2 capability.
- R3. Every business event consumption has a consuming L2 capability.
- R4. Every functional application mapping passes through an L2 capability.
- R5. Every direct relation between two non-L2 elements is either:
  - carried by an operational registry,
  - or justified by a documented exceptional need.
- R6. No transverse urbanization view relies primarily on direct application ↔ application, application ↔ server, or component ↔ component relations without passing through an L2 capability.
- R7. Direct compliance or exploitation relations never cancel the main business attachment to the L2 capability.

## Justification

This decision formalizes and generalizes principles already present in the repository.

The **L2** level is already presented as:
- the right compromise between stability and precision for urbanization,
- the natural attachment level for events,
- the point from which logical business and physical implementation can be decoupled,
- the relevant decision level to guide SI / DATA / ORG mappings.

By making L2 the explicit pivot:
- we avoid existing applications dictating the target structure,
- we preserve the ability to modernize or replace the IS without breaking the business model,
- we improve ownership,
- we make technical debt visible,
- we keep a readable and auditable model.

This rule does not prohibit direct links.
It **frames** them:
- operational links remain possible where necessary,
- compliance links remain possible where required,
- but they become secondary compared to the business pivot.

### Alternatives Considered

- **Option A — Allow direct links between all elements to freely coexist**  
  Rejected because it leads to opportunistic drift, loss of readability, and progressive coupling of the BCM model with the physical IS.

- **Option B — Make L1 the urbanization pivot**  
  Rejected because too macro to steer events, applications, data, or compliance with useful granularity.

- **Option C — Make L3 the urbanization pivot**  
  Rejected because too granular and too unstable; this would drift the BCM toward detailed process modeling or micro-decomposition.

- **Option D — Use the application directly as the traceability pivot**  
  Rejected because it recreates the logical / physical coupling and freezes the target on the existing.

## Impacts on the BCM

### Structure

- No change to L1 / L2 / L3 structure.
- Reinforcement of the L2 role as a transversal anchor point.
- Clarification of the boundary between:
  - BCM business referential,
  - mapping referentials,
  - operational / compliance referentials.

### Events (if applicable)

- Confirmation of the rule: every business event is attached to an emitting L2 capability.
- Confirmation of the rule: every business event consumption is attached to a consuming L2 capability.
- Purely technical events remain outside the BCM pivot, unless they carry a business traceability need.

### Mapping SI / Data / Org

- **SI**: capability ↔ application mappings become the mandatory entry point; application ↔ server or component ↔ runtime links are relegated to dedicated operational tables.
- **DATA**: flows and objects are attached to L2 capabilities before any technical breakdown.
- **ORG**: owners and responsibilities are attached primarily to L2 capabilities.
- **Compliance**: direct application ↔ control / regulatory device links are possible but must be explicitly identified as a motivated exception.

## Consequences

### Positive

- Simple and readable transverse rule for all referentials.
- Reinforced decoupling between business and implementation.
- Homogeneous traceability between capabilities, events, applications, data, and organization.
- Increased auditability of urbanization choices.
- Reduction of the "spaghetti graph" of opportunistic dependencies.
- Better ability to produce coherent views for transformation and governance.
- Compatibility with specific exploitation and compliance needs without degrading the target model.

### Negative / Risks

- Initial framing effort to correctly classify relations.
- Need to create or maintain several complementary registries:
  - functional mapping,
  - operational mapping,
  - compliance mapping.
- Risk of debates on what constitutes a "strictly operational" or "exceptionally motivated" link.
- Need for governance discipline to prevent an exception from becoming the norm.

### Accepted Debt

- Some existing referentials may temporarily continue to carry historical direct links without L2 pivot.
- These links are accepted as transitional debt if they are:
  - identified,
  - documented,
  - and periodically reviewed.
- Some compliance cases (e.g., DORA) may impose additional direct modeling before the mapping via L2 is complete.

## Governance Indicators

- Criticality level: High (structuring transverse rule).
- Recommended review date: 2028-03-11.
- Expected stability indicators:
  - 100% of business events attached to an L2 capability.
  - 100% of functional application mappings passing through an L2 capability.
  - 100% of direct non-L2 relations classified as `operational` or `exceptional_justified`.
  - 0 transverse urbanization views relying primarily on direct technical dependencies.
  - existence of at least one dedicated registry for operational mappings.

## Traceability

- Workshop: BCM Governance / Transverse Urbanization
- Participants: EA / Urbanization, IS Architecture, Business Architecture
- References:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0004
  - ADR-BCM-URBA-0007
  - `bcm/events-*.yaml` files
  - SI / DATA / ORG mapping files
