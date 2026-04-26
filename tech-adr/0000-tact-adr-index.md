# Tactical Tech ADR Index

One ADR per L2 capability. Produced by the `/tactic-tech-brainstorming` skill.

## Governance

- **Parent constraints**: ADR-TECH-STRAT-001 through 006 (strategic, read-only)
- **Override policy**: Any deviation from a TECH-STRAT rule must be declared in
  `strategic_overrides:` frontmatter and requires approval from the full architect team
  before the ADR status can move to `Accepted`.
- **Supersession**: Accepted ADRs are never edited in place — a new ADR with
  `supersedes:` is created, and the old one is marked `Superseded`.

## ADR Registry

| ID | Capability | Zone | Status | Overrides |
|----|------------|------|--------|-----------|
| [ADR-TECH-TACT-001](ADR-TECH-TACT-001-can001-tab-progression-dashboard.md) | CAP.CAN.001.TAB — Progression Dashboard | CANAL | Proposed | none |

<!-- Row template:
| ADR-TECH-TACT-001 | CAP.BSP.001.SCO — Scoring Comportemental | SERVICES_COEUR | Proposed | none |
-->
