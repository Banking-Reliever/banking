# Strategic Vision

## Service Offer (from product-vision/product.md)
> **Reliever** enables financially vulnerable individuals to progressively regain control of their daily financial lives through a system of increasing autonomy tiers, anchored on a dedicated card and a behavioral score coordinated between prescribers via open banking, even when preserving their dignity is as important as constraining their behaviors.

## Strategic Intent

Delivering this service offer requires the business to master a unique core domain — continuous behavioral assessment and autonomy tier governance — which exists nowhere else in the financial or social-care sector. Around this core, the business must build a multi-actor coordination capability spanning heterogeneous stakeholders (bank, psychiatrist, social worker) and an active spending control at the point of purchase via open banking, with no dependency on any inter-institutional agreement. The beneficiary's dignity is not an added ethical constraint — it is a functional condition: a humiliating system sabotages itself by provoking the very bypass it seeks to prevent.

## Strategic Capabilities

### L1 Capabilities

| ID | Name | Responsibility |
|----|------|----------------|
| SC.001 | **Behavioral Remediation** | Continuously assess the beneficiary's financial trajectory, govern their autonomy tiers, detect relapses and progressions |
| SC.002 | **Access & Enrollment** | Identify eligible individuals, orchestrate their entry into the program with prescribers, formalize the terms of care |
| SC.003 | **Prescriber Coordination** | Enable the bank, psychiatrist, and social worker to act in a coordinated way on the same beneficiary, with differentiated rights and views |
| SC.004 | **Spending Control** | Apply the current tier rules to each purchase act, manage authorizations in real time, feed the behavioral score |
| SC.005 | **Progression Valorization** | Make the beneficiary's trajectory visible and celebrate it to support their motivation and preserve their dignity |
| SC.006 | **Financial Instrument Management** | Issue and govern the dedicated card, link its rules to tiers, access financial data via open banking |
| SC.007 | **Compliance & Data Protection** | Ensure the legality of sensitive data sharing between heterogeneous actors, guarantee regulatory obligations |

### L2 Capabilities

#### SC.001 — Behavioral Remediation

| ID | Name | Responsibility |
|----|------|----------------|
| SC.001.01 | **Behavioral Scoring** | Continuously calculate and update the beneficiary's MMR score based on purchase events and bypass signals |
| SC.001.02 | **Tier Management** | Define the rules associated with each tier, manage algorithmic transitions and prescriber overrides |
| SC.001.03 | **Signal Detection** | Identify relapse signals (envelope not consumed) and progression signals, and qualify them to feed the score |
| SC.001.04 | **Algorithm / Human Arbitration** | Manage the tension between algorithmic decision and prescriber override, and govern the algorithm's resumption of control |

#### SC.003 — Prescriber Coordination

| ID | Name | Responsibility |
|----|------|----------------|
| SC.003.01 | **Role & Rights Management** | Define and apply differentiated visibility and action boundaries by prescriber type |
| SC.003.02 | **Prescriber Dashboard** | Provide each prescriber with a role-adapted view of the beneficiary's situation and trajectory |
| SC.003.03 | **Alerts & Notifications** | Notify relevant prescribers upon significant events — relapse, tier crossed, bypass detected |
| SC.003.04 | **Co-decision** | Allow multiple prescribers to coordinate an override decision on the same beneficiary |

#### SC.004 — Spending Control

| ID | Name | Responsibility |
|----|------|----------------|
| SC.004.01 | **Purchase Authorization** | Decide in real time whether to authorize or decline a transaction by applying the current tier rules |
| SC.004.02 | **Envelope Management** | Allocate, track, and adjust budgets by category and period for each beneficiary |
| SC.004.03 | **Comparison & Alternatives** | Propose price or product alternatives at the point of purchase to help the beneficiary stay within their envelope |
| SC.004.04 | **Event Reporting** | Forward each purchase event (completed, declined, bypass detected) to SC.001 to feed the behavioral score |

## Scope Decisions

### In Strategic Scope
- Behavioral assessment and autonomy tier governance (core domain)
- Active spending control at the point of purchase via dedicated card
- Multi-actor prescriber coordination with differentiated rights
- Access to financial data via open banking exclusively
- Gamification of progression to preserve the beneficiary's dignity

### Out of Strategic Scope
- Credit granting and loan management — Reliever is not a financing instrument
- Management of the main bank account — remediation layer only
- Negotiation of inter-banking protocols — open banking eliminates this dependency

## Key Tensions Identified

- **Control vs. dignity** — the constraint must be perceived as support, not punishment; gamification and rules transparency are functional levers, not cosmetic ones
- **Algorithm vs. human judgment** — the prescriber override is necessary for clinical nuance, but the algorithm must remain the continuous authority to avoid individual biases
- **Transparency vs. privacy** — coordination between heterogeneous actors (bank, doctor, social worker) requires fine-grained governance of role-based visibility boundaries

## Alternatives Considered

- **Beneficiary journey-centered structure**: organizing L1 capabilities around the beneficiary's life stages (entry, support, exit). Rejected because it mixes distinct responsibility domains (behavioral, payment, coordination) in a flow logic rather than a capability logic.
- **Actor-centered structure**: one L1 per actor type (beneficiary, bank, medical prescriber). Rejected because it duplicates cross-cutting capabilities (scoring, financial instrument) and creates ungovernable overlaps.

## Traceability to Service Offer

| ID | Contribution to service offer |
|----|-------------------------------|
| SC.001 | This is the differentiating core — without behavioral assessment and tiers, Reliever is just a prepaid card |
| SC.002 | Without structured enrollment with prescribers, the program cannot be activated for individuals who need it |
| SC.003 | Multi-actor coordination is the condition for cross-prescription (bank, psychiatrist, social worker) that gives the program its legitimacy |
| SC.004 | Control at the point of purchase is the moment of truth — this is where the tier rule is applied concretely |
| SC.005 | Progression valorization is the direct answer to the control/dignity tension — without it, the program risks being perceived as punitive |
| SC.006 | The dedicated card and open banking are the technical instruments that make control possible without banking dependency |
| SC.007 | The legal framework for data sharing between heterogeneous actors is a viability condition for the program |
