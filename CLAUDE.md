# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (PyYAML only)
pip install -r tools/requirements.txt

# Full build: validate → export BCM views → generate context.txt
./build.sh

# Structural validation only (capabilities, events, subscriptions coherence)
python3 tools/validate_repo.py
python3 tools/validate_repo.py --strict          # strict mode
python3 tools/validate_events.py --bcm-dir bcm --events-dir bcm

# Semantic review (full repo)
./test.sh                                          # full semantic review
./test-ci.sh                                       # PR-scoped review (uses git diff vs origin/main)

# Launch EventCatalog views (ports 4444 and 4445)
./run.sh
```

## Architecture

This is a **model-first BCM repository** for *Reliever*, a financial inclusion product. There is no application code — the repository contains structured YAML models, ADRs, and Python tooling to validate and export the Business Capability Map.

### ADR Governance Hierarchy

All architectural decisions flow through three families with strict precedence:

```
GOV  (meta-rules, review cycles, arbitration board)
 ↓
URBA (zoning, L1/L2/L3 rules, naming, event meta-model)
 ↓
FUNC (per-capability functional decisions — one FUNC ADR per L2)
```

A FUNC ADR cannot contradict an URBA ADR. Every BCM evolution requires an accepted ADR. ADRs live in `adr/` (structural) and `func-adr/` (functional, one per L2 capability).

### 7-Zone TOGAF Extended Model

Capabilities are placed in exactly one zone (`zoning` field in YAML). Values in `bcm/vocab.yaml`:

| YAML value | Zone |
|---|---|
| `STEERING` | Pilotage & governance |
| `BUSINESS_SERVICE_PRODUCTION` | Core business (Reliever's core domain) |
| `SUPPORT` | Transverse IT support |
| `REFERENTIAL` | Shared master data |
| `EXCHANGE_B2B` | External ecosystem exchanges |
| `CHANNEL` | Omnichannel exposure, user journeys |
| `DATA_ANALYTIQUE` | Data governance, BI, AI |

### Capability Levels

- **L1** — strategic domains, no `parent` field
- **L2** — pivot for urbanization; each L2 is a microservice/bounded context boundary; every L2 must have a governing FUNC ADR
- **L3** — optional local decomposition within an L2; parent must be an L2

Capability IDs follow `CAP.<ZONE_PREFIX>.<NNN>` for L1 and `CAP.<ZONE_PREFIX>.<NNN>.<SUB>` for L2/L3.

### BCM Asset Chain

The full chain from capability to event subscription:

```
capabilities-*.yaml
  └─ business-object-*.yaml      (business objects owned by L2)
       └─ business-event-*.yaml  (events emitted by L2/L3)
            └─ resource-*.yaml   (technical projection of a business object)
                 └─ resource-event-*.yaml     (technical event carrying the resource)
                      └─ business-subscription-*.yaml  (business consumption contract)
                           └─ resource-subscription-*.yaml  (technical subscription)
```

Key coherence rules enforced by `validate_repo.py`:
- Business events must be emitted by L2 or L3 capabilities
- Resource events must carry exactly one resource pointing to the same business object as the linked business event
- Every business subscription must be referenced by at least one resource subscription

### Implementation Workflow

Capabilities are implemented using Claude Code skills in this order:

```
/business-capabilities-brainstorming → /bcm-writer → /plan → /task → /code
```

Implementation plans live in `plan/<CAP-ID>/plan.md`. Tasks are `plan/<CAP-ID>/tasks/TASK-NNN-*.md` with frontmatter fields `task_id`, `status`, `priority`, `depends_on`. The kanban board is at `plan/BOARD.md` (auto-refreshed by the `/sort-task` skill via PostToolUse hooks whenever a TASK file changes; `/launch-task` is the orchestrator that launches code agents).

### Build Output

`./build.sh` generates `views/FOODAROO-Metier/` and `views/FOODAROO-SI/` (EventCatalog instances) and `context.txt` (full model concatenation). Skip context generation with `SKIP_CONTEXT=1 ./build.sh`.
