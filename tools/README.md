# BCM Tools

This directory contains utility scripts for the BCM repository:
validation, view generation and diagram export.

## Prerequisites

```bash
pip install -r tools/requirements.txt
```

Only dependency: **PyYAML** (`pyyaml`).

---

## Table of Contents

| Script | Description |
|--------|-------------|
| [`render_drawio.py`](#render_drawiopy) | Generates a draw.io L1 diagram (`.drawio`) from a capabilities YAML file |
| [`render_drawio_l2.py`](#render_drawio_l2py) | Generates a draw.io L2 diagram (`.drawio`) with L2 capabilities grouped inside their L1 |
| [`render_drawio_capability_chain.py`](#render_drawio_capability_chainpy) | Generates an internal production/consumption chain for an L1 capability |
| [`render_drawio_subscriptions.py`](#render_drawio_subscriptionspy) | Generates a draw.io view of business subscriptions from the subscription template |
| [`validate_events.py`](#validate_eventspy) | Validates event references against BCM capabilities |
| [`validate_repo.py`](#validate_repopy) | Structural validation of the repository (files, YAML, coherence) |
| [`check_docs_links.py`](#check_docs_linkspy) | Checks internal Markdown links (files + anchors) for CI/CD |
| [`semantic_review.py`](#semantic_reviewpy) | PR semantic coherence CI agent (ADR then ADR+BCM) + PR report |
| [`concat_files.py`](#concat_filespy) | Concatenates all ADR and BCM files into a single document |
| [`run_eventcatalogs.sh`](#run_eventcatalogssh) | Launches FOODAROO-Metier and FOODAROO-SI in parallel with clean shutdown |
---

## run_eventcatalogs.sh

Simultaneously launches both EventCatalog instances:

- `views/FOODAROO-Metier` (default port `4444`)
- `views/FOODAROO-SI` (default port `4445`)

The script:

- checks for the presence of projects (`package.json`);
- automatically installs npm dependencies if `node_modules` is absent;
- starts both servers in parallel;
- handles clean shutdown of both processes (`Ctrl+C`).

### Usage

```bash
# From the repository root
bash tools/run_eventcatalogs.sh

# Custom ports
METIER_PORT=3010 SI_PORT=3011 bash tools/run_eventcatalogs.sh
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `METIER_PORT` | Port for `views/FOODAROO-Metier` | `4444` |
| `SI_PORT` | Port for `views/FOODAROO-SI` | `4445` |

---

## render_drawio.py

Generates a draw.io **L1** diagram (`.drawio`) from a capabilities YAML file,
with the classic BCM layout.
Each L1 capability is a colored box placed in its zone.

### Features

- **7 colored zones** arranged according to the standard BCM layout
- **Distinctive pastel colors** per L1 capability (palette of 16 colors cycling)
- **Automatic grid layout** of boxes inside each zone
- **Empty zones** rendered as colored rectangles (filled when capabilities are added to the YAML)

### Zone Layout

```
┌──────────────────────────────────────────────────────┐
│                    PILOTAGE                          │
├──────────┬──────────────────────────────┬────────────┤
│          │  SERVICES_COEUR │            │
│  B2B     ├──────────────────────────────┤  CANAL   │
│ EXCHANGE │       SUPPORT               │            │
│          ├──────────────────────────────┤            │
│          │      REFERENTIEL            │            │
├──────────┴──────────────────────────────┴────────────┤
│                 DATA_ANALYTIQUE                       │
└──────────────────────────────────────────────────────┘
```

### Usage

```bash
# Default generation
#   input : bcm/capabilities-L1.yaml
#   output: views/BCM-L1-generated.drawio
python tools/render_drawio.py

# Specific input file
python tools/render_drawio.py --input bcm/capabilities-L1.yaml

# Custom output file
python tools/render_drawio.py --output views/my-bcm.drawio

# Change the number of columns in central zones (default: 4)
python tools/render_drawio.py --cols 3
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-i`, `--input` | Source YAML capabilities file | `bcm/capabilities-L1.yaml` |
| `-o`, `--output` | Path of the generated `.drawio` file | `views/BCM-L1-generated.drawio` |
| `--cols` | Number of columns in central zones | `4` |

### Expected YAML Format

The input file must follow the structure of `bcm/capabilities-L1.yaml`:

```yaml
meta:
  bcm_name: BCM Urbanisation
  version: 0.1.0

capabilities:
  - id: CAP.COEUR.001
    name: Products & Pricing
    level: L1
    zoning: SERVICES_COEUR   # determines the placement zone
    description: ...
    owner: ...
    adrs: []
```

The `zoning` field determines which zone the capability is placed in.
Recognized values: `PILOTAGE`, `SERVICES_COEUR`, `SUPPORT`,
`REFERENTIEL`, `ECHANGE_B2B`, `CANAL`, `DATA_ANALYTIQUE`.

### Output

The generated `.drawio` file opens directly in:

- **draw.io Desktop** (file → open)
- **draw.io Web** ([app.diagrams.net](https://app.diagrams.net))
- **VS Code** draw.io extension

The diagram can be manually enriched after generation.

---

## render_drawio_l2.py

Generates a draw.io **L2** diagram (`.drawio`) from **all**
`capabilities-*.yaml` files in the `bcm/` directory.
Each L1 capability is a *draw.io group* containing its L2 boxes.

### Features

- **Automatic reading** of all `bcm/capabilities-*.yaml` files (L1 + L2)
- **L1 → L2 hierarchy**: L2s are linked to their parent via the `parent` field
- **draw.io groups**: each L1 is a group containing a colored background, a title and L2 boxes
- **Colors matching the template** `BCM L2 template.drawio`:
  - Zones: same color codes as `render_drawio.py` (`ZONE_CONFIG`)
  - L1 backgrounds: rotating pastel palette (`CAPABILITY_PALETTE`, 16 colors)
  - L2 boxes: color by zone (peach `#ffe6cc` for COEUR, sky blue `#dae8fc` for Pilotage, golden `#FFE599` for B2B/Canal, lavender `#e1d5e7` for Data)
- **Placeholder** for L1 without defined L2
- **100% YAML content** — nothing is invented

### Layout

Same layout as `render_drawio.py`:

```
┌──────────────────────────────────────────────────────┐
│                    PILOTAGE                          │
├──────────┬──────────────────────────────┬────────────┤
│          │  COEUR  ┌─────────┐ ┌────────┐│            │
│  B2B     │       │ L1      │ │ L1     ││  CANAL   │
│ EXCHANGE │       │  ┌─L2─┐ │ │ (empty)││            │
│          │       │  └────┘ │ └────────┘│            │
│          ├───────┴─────────┴───────────┤            │
│          │       SUPPORT               │            │
│          ├─────────────────────────────┤            │
│          │      REFERENTIEL            │            │
├──────────┴─────────────────────────────┴────────────┤
│                 DATA_ANALYTIQUE                       │
└──────────────────────────────────────────────────────┘
```

### Usage

```bash
# Default generation
#   input : bcm/capabilities-*.yaml
#   output: views/BCM-L2-generated.drawio
python tools/render_drawio_l2.py

# Specific input directory
python tools/render_drawio_l2.py --input-dir bcm

# Custom output file
python tools/render_drawio_l2.py --output views/my-bcm-l2.drawio

# Change the number of L2 columns in an L1 group (default: 2)
python tools/render_drawio_l2.py --l2-cols 3

# Change the number of L1 groups per row in central zones (default: 3)
python tools/render_drawio_l2.py --l1-cols 4
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-d`, `--input-dir` | Directory containing `capabilities-*.yaml` files | `bcm/` |
| `-o`, `--output` | Path of the generated `.drawio` file | `views/BCM-L2-generated.drawio` |
| `--l2-cols` | Number of L2 columns in an L1 group | `2` |
| `--l1-cols` | Number of L1 groups per row (central zones) | `3` |

### Expected YAML Format

The script expects `capabilities-*.yaml` files with L1 and L2 entries:

```yaml
capabilities:
  # L1 capability
  - id: CAP.COEUR.005
    name: Claims & Benefits
    level: L1
    zoning: SERVICES_COEUR
    ...

  # L2 capability (linked via parent)
  - id: CAP.COEUR.005.DSP
    name: Claim Declaration
    level: L2
    parent: CAP.COEUR.005              # ← link to L1
    zoning: SERVICES_COEUR
    ...
```

---

## render_drawio_subscriptions.py

Generates a draw.io view of **business subscriptions** by applying the geometry
and styles from the template `views/template-abonnement.drawio`:

- **without argument**: renders all subscribing capabilities, one file per capability,
  in `views/abonnements/`,
- emitting capability → event (top anchor to middle),
- event → consuming capability (dashed arrow, top/bottom anchor depending on position),
- consolidated mode per subscribing capability: a single brick with all its subscriptions,
  and all emitting capabilities aligned on the same column.

### Usage

```bash
# Default generation (batch: all subscribing capabilities)
python tools/render_drawio_subscriptions.py

# Consolidated rendering for a subscribing capability
python tools/render_drawio_subscriptions.py \
  --consumer-capability CAP.COEUR.005.CAD

# Auto filename based on the subscribing capability ID if --output is not provided
# e.g.: views/COEUR.005.CAD-abonnements.drawio

# Custom output directory in batch mode
python tools/render_drawio_subscriptions.py --output-dir views/abonnements

# Explicit output file (single-capability mode only)
python tools/render_drawio_subscriptions.py \
  --consumer-capability CAP.COEUR.005.CAD \
  --output views/abonnements/COEUR.005.CAD-abonnements.drawio

# Filter on an L1 parent (e.g.: CAP.COEUR.005)
python tools/render_drawio_subscriptions.py --focus-parent-l1 CAP.COEUR.005

# Custom inputs/output
python tools/render_drawio_subscriptions.py \
  --bcm-dir bcm \
  --events-dir bcm/business-event \
  --template views/template-abonnement.drawio \
  --output views/business-subscriptions-generated.drawio
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--bcm-dir` | Directory containing `capabilities-*.yaml` files | `bcm` |
| `--events-dir` | Directory of `business-event-*.yaml` and `business-subscription-*.yaml` | `bcm/business-event` |
| `--template` | Reference draw.io template | `views/template-abonnement.drawio` |
| `--output` | Generated `.drawio` file (single-capability mode only) | *(optional)* |
| `--output-dir` | Output directory for renderings | `views/abonnements` |
| `--focus-parent-l1` | Filter on an L1 parent | *(optional)* |
| `--consumer-capability` | Target subscribing capability; enables consolidated rendering | *(optional)* |
| `--diagram-name` | draw.io tab name | `Business subscriptions` |

In `--consumer-capability` mode, if `--output` is not specified,
the filename is auto-generated in the format `<L2_ID>-abonnements.drawio`
(e.g.: `COEUR.005.CAD-abonnements.drawio`).

Without `--consumer-capability`, the script renders all subscribing capabilities and writes
one file per capability to `--output-dir`.

---

## render_drawio_capability_chain.py

Generates a Draw.io rendering of the **production/consumption chain** within an
**L1** capability (internal L2/L3 capabilities), aligned with the template
`views/capacites/COEUR.005-chaine-abonnements-template.drawio`.

Rendering principles:

- all capabilities of the L1 are included,
- the main chain is positioned left to right,
- intermediate events are rendered between producer and consumer,
  above their producing capability,
- arrow origins/targets are individualized to limit crossings,
- event placement with collision avoidance to reduce text overlap.

### Usage

```bash
# Default batch: all L1 with an internal chain detected
python tools/render_drawio_capability_chain.py

# Targeted rendering for an L1
python tools/render_drawio_capability_chain.py --l1-capability CAP.COEUR.005

# Custom output directory
python tools/render_drawio_capability_chain.py --output-dir views/capacites
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--bcm-dir` | Directory containing `capabilities-*.yaml` files | `bcm` |
| `--events-dir` | Directory of `business-event-*.yaml` and `business-subscription-*.yaml` | `bcm/business-event` |
| `--template` | Reference draw.io template | `views/capacites/COEUR.005-chaine-abonnements-template.drawio` |
| `--l1-capability` | Target L1 capability | *(optional)* |
| `--output` | Generated `.drawio` file (single-capability mode only) | *(optional)* |
| `--output-dir` | Output directory for renderings | `views/capacites` |
| `--diagram-name` | draw.io tab name | `Capability L1 Chain` |

The filename follows the format `<L1_ID>-chaine-abonnements.drawio`
(e.g.: `COEUR.005-chaine-abonnements.drawio`).

---

## validate_events.py

Validates **in bulk** the event assets (subdirectories of `bcm/`) against BCM capabilities
(`bcm/capabilities-*.yaml`) and checks cross-asset relations:

- business events ↔ business objects,
- unidirectional relation business event → business object (no reverse reference in the business object),
- resource events ↔ resources ↔ business events,
- business subscriptions ↔ business events,
- resource subscriptions ↔ resource events ↔ business subscriptions,
- business objects ↔ L2/L3 capabilities with `emitting_capability_L3` constraint if the referenced L2 has L3s.
- external processes ↔ capabilities/events:
  - `externals/processus-metier/*.yaml`: checks existence of referenced capabilities, business events **and business subscriptions**,
  - `externals/processus-ressource/*.yaml`: checks existence of referenced capabilities, resource events **and resource subscriptions**.

`template-*.yaml` files are automatically ignored.

### Usage

```bash
# Batch mode (recommended default)
python tools/validate_events.py

# Batch mode with custom directories
python tools/validate_events.py \
  --bcm-dir bcm \
  --events-dir bcm

# Legacy single-file mode (compatibility)
python tools/validate_events.py \
  --bcm bcm/capabilities-L1.yaml \
  --events bcm/business-event/business-event-COEUR-005.yaml
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--bcm-dir` | Directory containing `capabilities-*.yaml` files | `bcm` |
| `--events-dir` | Root directory containing event assets | `bcm` |
| `--bcm` | Legacy mode: single capabilities file | *(optional)* |
| `--events` | Legacy mode: single business events file | *(optional)* |

---
---

## validate_repo.py

Structural validation of the BCM repository.
Loads **all** `bcm/capabilities-*.yaml` files and checks global coherence
of capabilities across all files.

### Current Rules (extracted from code)

The script applies the following rules, in this order.

#### 0) Blocking pre-checks (`FATAL`)

1. `bcm/vocab.yaml` must exist, otherwise immediate stop.
2. At least one `bcm/capabilities-*.yaml` file must exist, otherwise immediate stop.

#### 1) Pass 1 — Individual validation of each capability

1. `id` required.
2. `id` unique across all loaded files.
3. `level` must belong to `vocab.yaml -> levels`.
4. `zoning` must belong to `vocab.yaml -> zoning`.
5. `parent` rules by level:
  - if `level == L1`: the `parent` field must not be present;
  - otherwise (L2/L3/...): the `parent` field is required.
6. Heatmap (optional): if `heatmap.maturity` is set,
  its value must belong to `vocab.yaml -> heatmap_scales -> maturity`
  **only if** this list is defined and non-empty in the vocabulary.

#### 2) Pass 2 — Parent/child relationship coherence

Applied only to non-L1 capabilities that have a `parent`:

1. The referenced `parent` must exist in the set of loaded capabilities.
2. The parent level must comply with the hardcoded hierarchy:
  - an `L2` must have an `L1` parent;
  - an `L3` must have an `L2` parent.

> Note: this hierarchy is held by `LEVEL_HIERARCHY = {"L2": "L1", "L3": "L2"}`.
> No additional check is defined for other levels.

#### 2 bis) Cross-asset checks (non-template `bcm/**` files)

1. **Business event**
  - `emitting_capability` required, existing, and at level `L2` or `L3`.
  - `version` required.
  - `carried_business_object` required and existing in `business-object-*.yaml`.
2. **Business object**
  - `emitting_capability` required, existing, and at level `L2` or `L3`.
  - if `emitting_capability` points to an **L2 that has L3 children**, then `emitting_capability_L3` is required,
    must be a non-empty list, and each entry must be an existing L3 linked to that same L2.
  - if the L2 has no L3 children, `emitting_capability_L3` is forbidden.
  - `emitting_business_event` / `emitting_business_events` forbidden (the relation is held by the business event).
3. **Resource event**
  - `carried_resource` required and existing in `resource-*.yaml`.
  - `business_event` required (single value) and must exist in `business-event-*.yaml`.
4. **Resource**
  - `business_object` required and existing in `business-object-*.yaml`.
5. **Business subscription**
  - `consumer_capability` required, existing, and at level `L2` or `L3`.
  - `subscribed_event.id` required and existing in `business-event-*.yaml`.
  - `subscribed_event.version` required and equal to the business event version.
  - `subscribed_event.emitting_capability` required and consistent with the business event.
6. **Resource subscription**
  - `consumer_capability` required, existing, and at level `L2` or `L3`.
  - `linked_business_subscription` required and existing in `business-subscription-*.yaml`.
  - `subscribed_resource_event.id` required and existing in `resource-event-*.yaml`.
  - `subscribed_resource_event.emitting_capability` required and consistent with the resource event.
  - `subscribed_resource_event.linked_business_event` required and consistent with the `business_event` of the resource event.
  - coherence between resource subscription and linked business subscription (consumer, business event, emitter).
7. **Cross-subscription coverage**
  - every business subscription must be referenced by at least one resource subscription.

`id` uniqueness checks are also applied, per asset type,
on files loaded from `bcm/`.

#### 2 ter) External process checks (`externals/processus-*/*.yaml`)

1. **Business process** (`processus_metier`)
  - referenced capabilities (e.g.: `parent_capability`, `decision_point`, `internal_capabilities`, `event_capability_chain[].capability`) must exist in `bcm/capabilities-*.yaml`;
  - referenced business events (e.g.: `entry_event`, `business_assets.evenements_metier`, `event_subscription_chain`, `exits_metier`) must exist in `bcm/business-event/*.yaml`.
  - referenced business subscriptions (e.g.: `business_assets.abonnements_metier`, `event_subscription_chain[].via_subscription`) must exist in `bcm/business-event/business-subscription-*.yaml`.
2. **Resource process** (`processus_ressource`)
  - referenced capabilities must exist in `bcm/capabilities-*.yaml`;
  - referenced resource events (e.g.: `entry_event`, `resource_assets.evenements_ressource`, `event_subscription_chain`, `exits_ressource`) must exist in `bcm/resource-event/*.yaml`.
  - referenced resource subscriptions (e.g.: `resource_assets.abonnements_ressource`, `event_subscription_chain[].via_subscription`) must exist in `bcm/resource-event/resource-subscription-*.yaml`.

Prefix conventions used in these checks:
- `OBJ.*` for business objects,
- `RES.*` for resources,
- `ABO.METIER.*` and `ABO.RESSOURCE.*` for subscriptions.

#### 3) Final report

- If there is at least one error: `[FAIL]` output + exit code `1`.
- Otherwise: `[OK]` output with the number of capabilities and L1/L2/L3 breakdown.
- Warnings would be displayed as `[WARN]`, but no current rule populates this list.

### Usage

```bash
# Full repository validation
python tools/validate_repo.py

# Targeted validation of a single business object
python tools/validate_repo.py --business-object OBJ.COEUR.005.DECLARATION_SINISTRE
python tools/validate_repo.py -o OBJ.COEUR.005.DECLARATION_SINISTRE
```

#### Options

| Option | Alias | Description |
|--------|-------|-------------|
| `--business-object ID` | `-o ID` | Validates a specific business object and displays a detailed report |

Without arguments, the script automatically scans `bcm/capabilities-*.yaml`
and `bcm/vocab.yaml` from the repository root.

### Example Output

#### Full validation

```
[INFO] Loaded files:
  • capabilities-COEUR-005-L2.yaml: 10 capability(ies)
  • capabilities-L1.yaml: 8 capability(ies)

[OK] Validation successful — 18 capabilities (8 L1, 10 L2) in 2 file(s)
```

In case of error:

```
[FAIL] 1 error(s) detected:

  ✗ [capabilities-COEUR-005-L2.yaml] CAP.COEUR.005.DSP: parent 'CAP.COEUR.099' not found
    in the set of loaded capabilities
```

#### Business object validation

```
================================================================================
              VALIDATION REPORT — BUSINESS OBJECT
================================================================================

GENERAL INFORMATION
--------------------------------------------------------------------------------
  ID       : OBJ.COEUR.005.DECLARATION_SINISTRE
  Name     : Qualified Claim Declaration
  Source   : bcm/business-object/business-object-COEUR-005.yaml

EMITTING L2 CAPABILITY
--------------------------------------------------------------------------------
  Business event: EVT.COEUR.005.SINISTRE_DECLARE
  Capability    : CAP.COEUR.005.DSP (Claim Declaration and Benefits)

CARRYING BUSINESS EVENT
--------------------------------------------------------------------------------
  ID      : EVT.COEUR.005.SINISTRE_DECLARE
  Name    : Qualified Claim Declaration
  Version : 1.0.0

BUSINESS OBJECT PROPERTIES
--------------------------------------------------------------------------------
  #   Property                          Coverage      Resources
  --- --------------------------------- ------------- ---------------------------
  1   contractNumber                    ✓ Covered     RES.COEUR.005.SINISTRE_HABITATION_DEGAT_DES_EAUX, ...
  2   declarationDate                   ✓ Covered     RES.COEUR.005.SINISTRE_HABITATION_DEGAT_DES_EAUX, ...
  ...

RESOURCES IMPLEMENTING THIS OBJECT
--------------------------------------------------------------------------------
  #   Resource ID                                     Name
  --- ----------------------------------------------- ---------------------------
  1   RES.COEUR.005.SINISTRE_HABITATION_DEGAT_DES_... Water Damage Claim...
  2   RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_VOL Theft Claim Declaration
  3   RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_INCENDIE Fire Claim Declaration

================================================================================
SUMMARY: Valid business object — 3 resource(s), 10/10 properties covered
================================================================================
```

---

## check_docs_links.py

Checks Markdown documentation coherence in the repository:

- internal links to files (e.g.: `path/to/file.md`);
- anchor links (e.g.: `file.md#section` or `#section`).

The script is designed for CI/CD: it returns `0` if everything is valid,
`1` if at least one inconsistency is detected.

### Usage

```bash
# From the repository root
python tools/check_docs_links.py

# Custom root
python tools/check_docs_links.py --root .
```

### CI Integration Example

  ```bash
  python tools/check_docs_links.py
  ```

---

## semantic_review.py

Semantic coherence agent for Pull Requests, in **2 phases**:

1. **ADR**: ADR structure check + ADR documentary coherence checks + SI urbanist LLM review,
2. **ADR + BCM**: execution of repository validators (`validate_repo.py` and `validate_events.py`).

The script generates:

- a Markdown report (`semantic-review.md`) ready to be injected into the PR description,
- a JSON summary (`semantic-review.json`) usable by the CI workflow.

Return code:

- `0`: globally positive coherence,
- `1`: major defects detected (build should fail).

LLM severity behavior:

- **major_defects**: blocking (build failure),
- **minor_defects**: non-blocking (improvement proposals only).

Usable format returned in `semantic-review.json` (key `llm`):

- `score`: ADR coherence score (0..100)
- `summary`: short summary
- `findings[]`: structured findings (`id`, `severity`, `adr_refs`, `rationale`, `impact`, `proposed_fix`, `priority`, `effort`, `owner_hint`)
- `action_plan[]`: ready-to-execute actions (`id`, `action`, `targets`, `severity`, `priority`, `owner_hint`, `due_hint`)

### Usage

```bash
python tools/semantic_review.py \
  --scope pr \
  --base-ref <pr_base_sha> \
  --head-ref <pr_head_sha> \
  --llm-mode required \
  --report-file semantic-review.md \
  --json-file semantic-review.json
```

Full repository mode:

```bash
python tools/semantic_review.py \
  --scope full \
  --llm-mode required \
  --report-file semantic-review-full.md \
  --json-file semantic-review-full.json
```

LLM configuration via environment variables:

- `SEMANTIC_LLM_API_KEY` (required in `required` mode),
- `SEMANTIC_LLM_MODEL` (default `gpt-4.1`),
- `SEMANTIC_LLM_API_URL` (default `https://api.openai.com/v1/chat/completions`),
- `SEMANTIC_LLM_MODE` (`required`, `optional`, `off`).
- `SEMANTIC_LLM_MAX_ADR_CHARS` (default `3500`): max character budget per ADR sent to the LLM.
- `SEMANTIC_LLM_MAX_TOTAL_CHARS` (default `50000`): global ADR character budget in the prompt.
- `SEMANTIC_LLM_MAX_RETRIES` (default `3`) and `SEMANTIC_LLM_RETRY_DELAY_SECONDS` (default `2`): retries/backoff on rate-limit (`429`).

Associated root scripts:

- `./test.sh` → `full` mode
- `./test-ci.sh` → `pr` mode (files impacted by the current PR)

---

## concat_files.py

Concatenates all files from the `adr/`, `bcm/`, `templates/` and `externals-templates/` folders into a single document.
Useful for feeding an LLM with the complete BCM repository context,
or for creating a consolidated export of the documentation.

### Features

- **Recursive traversal** of the `adr/`, `bcm/`, `templates/` and `externals-templates/` folders
- **Extension filtering**: `.md`, `.yaml`, `.yml` by default
- **Visual separators** indicating the relative path of each file
- **Flexible output**: stdout or file
- **Filtering modes**: ADR only, BCM only, or both

### Usage

```bash
# Display everything on stdout
python tools/concat_files.py

# Save to a file
python tools/concat_files.py -o context.txt

# ADR only
python tools/concat_files.py --adr-only

# BCM only
python tools/concat_files.py --bcm-only

# Templates (internal + external) only
python tools/concat_files.py --templates-only

# Filter by extension (YAML only)
python tools/concat_files.py --ext .yaml --ext .yml

# Markdown only
python tools/concat_files.py --ext .md
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-o`, `--output` | Output file | stdout |
| `--adr-only` | Concatenates only ADR files | *(disabled)* |
| `--bcm-only` | Concatenates only BCM files | *(disabled)* |
| `--templates-only` | Concatenates only template files (`templates/` + `externals-templates/`) | *(disabled)* |
| `--ext` | Extensions to include (repeatable) | `.md`, `.yaml`, `.yml` |
| `--no-separator` | Disables separators between files | *(disabled)* |

### Example Output

```
================================================================================
FILE: adr/ADR-BCM-URBA-0001-BCM-SI-oriented-TOGAF.md
================================================================================
---
id: ADR-BCM-URBA-0001
title: "TOGAF-extended BCM SI (7 zones)"
status: Proposed
...

================================================================================
FILE: bcm/capabilities-L1.yaml
================================================================================
meta:
  bcm_name: BCM Urbanisation
  version: 0.1.0
...

# Total: 25 files concatenated
```

---

## Directory Structure

```
tools/
├── README.md              # This file
├── check_docs_links.py    # Markdown link checking (files + anchors)
├── concat_files.py        # ADR + BCM concatenation
├── run_eventcatalogs.sh   # Launch FOODAROO-Metier + FOODAROO-SI
├── render_drawio.py       # draw.io L1 generation
├── render_drawio_l2.py    # draw.io L2 generation
├── validate_events.py     # Event validation
├── validate_repo.py       # Repository validation
└── requirements.txt       # Python dependencies (pyyaml)
```
