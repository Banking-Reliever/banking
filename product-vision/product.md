# Service Offer

> **Reliever** enables financially vulnerable individuals to progressively regain control of their daily financial lives through a system of increasing autonomy tiers, anchored on a dedicated card and a behavioral score coordinated between prescribers via open banking, even when preserving their dignity is as important as constraining their behaviors.

## Problem Statement

Existing over-indebtedness solutions (Banque de France files, recovery plans) intervene too late, once the spiral has already begun. They cannot support individuals at the moment of daily micro-purchase decisions. The problem is not ignorance — the people affected are aware of their vulnerability — but the absence of concrete support and external authority at the precise moment the decision is made.

## Primary Beneficiary

An individual who is aware of their financial vulnerability, identified by a bank, a psychiatrist, or a social worker. They cannot modify their purchasing behavior alone — not out of ignorance, but due to the lack of authoritative support at the moment of decision. Success means progressively restored autonomy, up to fully independent management of their financial life.

## Scope

### In Scope
- Spending control at the point of purchase via a dedicated card whose rules follow the current tier
- Gamified visualization of budget and progress (Strava model)
- Multi-actor coordination (bank, psychiatrist, social worker) with differentiated rights per role

### Out of Scope
- Loans and transfers — Reliever is not a credit instrument or fund transfer tool
- Management of the main bank account — Reliever is a remediation layer, not a bank account
- Integration with proprietary banking systems — open banking is the only access channel; no inter-institutional agreements are required

### Open Questions
- Data governance between prescribers: what data does the psychiatrist see? Does the bank see the diagnosis?
- Precise tier transition criteria: what behavioral indicators does the algorithm measure?
- Issuance of the dedicated card: which payment institution is the partner?
- What happens when the budget envelope is exhausted before the end of the period?

## Core Domain Concepts

1. **Beneficiary** — the individual undergoing financial remediation
2. **Prescriber** — bank, psychiatrist, social worker
3. **Tier** — current autonomy level with its associated rules
4. **Behavioral score** — the MMR equivalent, continuously calculated by the algorithm
5. **Envelope** — budget allocated by category and period
6. **Purchase event** — the moment the card is presented and the tier rule is applied
7. **Bypass** — the behavior of circumventing the controlled channel (signal: envelope not consumed)
8. **Progression** — the beneficiary's visible trajectory, treated as a performance achievement

## Core Events

1. **Purchase completed** — card presented, tier rule applied, envelope consumed
2. **Purchase declined** — blocking tier, motivated decision returned to the individual
3. **Envelope not consumed** — bypass signal, triggers score re-evaluation
4. **Tier modified** — by algorithm or prescriber override; the algorithm resumes authority if behavioral reality contradicts the manual decision
5. **Relapse detected** — score drops, prescribers notified
6. **Autonomy restored** — final tier reached, switch to standard banking application

## Core Tensions

- **Control vs. dignity** — constrain without infantilizing; dignity is not an added moral value, it is a functional condition: a humiliating tool undermines itself by provoking the bypass it seeks to prevent
- **Algorithm vs. human judgment** — the prescriber override can force a tier, but the algorithm remains the continuous authority and resumes control if the leap is not validated by behaviors
- **Transparency vs. privacy** — data sharing between actors of different natures (bank, doctor, social worker); role-based visibility boundaries are a critical open question

## Alternatives Considered

- **Option 1 — Food sandbox**: micro-account limited to grocery purchases. Deliverable today, but too narrow a vision — does not cover overall financial life and maintains dependency on inter-banking agreements.
- **Option 2 — Progressively managed account**: integration with the main account with graduated tier-based control. Requires a shared banking protocol that is impossible to obtain today.
- **Option 3 — Open remediation protocol (selected)**: layer independent of banking institutions via open banking. The dedicated card is the only universal control point. Resolves banking fragmentation without requiring inter-institutional agreements.
