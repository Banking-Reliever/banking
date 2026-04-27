---
name: test-business-capability
description: >
  Tests a web frontend (produced by code-web-frontend), a backend microservice (.NET,
  produced by the implement-capability agent), or a BFF (produced by create-bff) against the task
  criteria, plan rules, FUNC ADRs, product vision, and strategic vision. Tests run in a
  temporary local environment: the frontend is copied to /tmp/, an ephemeral HTTP server
  is launched, API calls are intercepted by Playwright. No modification of the original
  artifacts.

  Supports testing a specific git branch or dedicated environment: pass `--branch <slug>`
  or `--env <slug>` to resolve artifacts from that branch's working tree.

  Trigger this skill whenever the user says: "test TASK-NNN", "test the frontend",
  "verify the task", "validate the dashboard", "run tests", "test business capability",
  "test-business-capability", "test CAP.", "run the tests", "verify DoD criteria",
  "validate business rules", "test on branch X", "test on env X", or any phrasing
  requesting automated validation of a task or capability. Also trigger proactively after
  a code-web-frontend or create-bff skill, or the implement-capability agent, has finished and the
  user wants to validate the result.
---

# Test Business Capability

You orchestrate automated tests that validate that an implemented task (frontend and/or
backend or BFF) meets its Definition of Done criteria, its business rules (ADRs), and its
strategic alignment.

The tests run in a **temporary local environment**: artifacts are copied,
an ephemeral HTTP server is launched, then everything is destroyed at the end. The original
artifacts are never modified.

---

## Technical Prerequisites

Check tool availability at startup:

```bash
# Playwright Python
python3 -c "import playwright" 2>/dev/null || {
  echo "Installing Playwright..."
  pip install playwright pytest-playwright
  python3 -m playwright install chromium --with-deps
}

# pytest
python3 -c "import pytest" 2>/dev/null || pip install pytest
```

If installation fails, propose a manual test plan (see the fallback section at the end of the skill).

---

## Step 0 — Identify the Task and Environment

The user provides a task identifier (`TASK-NNN`) or a capability name.
They may optionally specify:
- `--branch <slug>` — test artifacts from a specific git branch (e.g., `--branch feature-can001-bff`)
- `--env <slug>` — test artifacts from a named environment slug (same as branch slug by convention)
- `--bff` — explicitly request BFF testing mode (auto-detected if a BFF artifact exists)

If ambiguous, list tasks with status `done` or `in_progress` in `plan/*/tasks/`:
only already-implemented tasks can be tested.

### Resolve the active branch/environment

```bash
# If --branch or --env was given, use it. Otherwise detect current branch.
BRANCH=$(git branch --show-current 2>/dev/null | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-\|-$//g')
echo "Active branch/environment: $BRANCH"
```

Record `BRANCH` — it is used to resolve `.env.local` port assignments and to scope
artifact discovery when multiple branches co-exist on the same machine.

---

## Step 1 — Read All Context

Read in order:

1. `/plan/{capability-id}/tasks/TASK-NNN-*.md` — primary source of test criteria
   - "Definition of Done" section → each criterion becomes a test
   - "What to Build" section → list of features to validate
   - "Business Objects Involved" section → entities to look for in the UI
   - "Business Events to Produce" section → network calls to intercept

2. `/plan/{capability-id}/plan.md`
   - "Scoping decisions" → additional rules (e.g., "V0 without gamification")
   - Epic "exit conditions" → complementary acceptance criteria

3. Governing FUNC ADRs cited in the task (`/func-adr/ADR-BCM-FUNC-*.md`)
   - Business rules constraining the UI (dignity rule, consent gate, etc.)

4. `/product-vision/product.md` — tone, language, interface posture

5. `/strategic-vision/strategic-vision.md` — strategic capability carried by this task

---

## Step 2 — Locate Artifacts

Look for artifacts in this priority order:

```
Frontend : sources/{capability-id}/frontend/        ← produced by code-web-frontend
Backend  : sources/{capability-name}/backend/       ← produced by implement-capability (optional)
BFF      : src/{zone-abbrev}/{capability-id}-bff/   ← produced by create-bff (optional)
Stub     : sources/{capability-id}/frontend/api.js  ← STUB_DATA and API_CONFIG
```

### Frontend artifact (required for frontend tests)

Frontend structure (`frontend-baseline` pattern):
```
sources/{capability-id}/frontend/
├── index.html
├── styles.css
├── api.js      ← API_CONFIG { baseUrl, useMockData }, STUB_DATA, window.{Name}Api
└── app.js      ← IIFE, window.App, resolution via ?beneficiaireId=
```

Extract from `api.js`:
- The `API_CONFIG.baseUrl` constant (default value: `''` or `window.API_BASE_URL`)
- The complete `STUB_DATA` structure (to build mocked responses in tests)
- The names of functions exposed in `window.{CapabilityName}Api`
- The URL patterns of the real endpoints (`fetchWithTimeout(...)` lines)

If the frontend does not exist and no `--bff` flag was given, stop:
> "No frontend found for {capability-id}. Run the code-web-frontend skill first."

### BFF artifact (required for BFF tests)

```bash
BFF_DIR="src/{zone-abbrev}/{capability-id}-bff"
ENV_FILE="$BFF_DIR/.env.local"

# Read port assignments written by create-bff
if [ -f "$ENV_FILE" ]; then
  source "$ENV_FILE"
  echo "BFF port: $BFF_PORT  Branch: $BRANCH"
else
  echo "No .env.local found — BFF has not been scaffolded or .env.local is missing."
fi
```

Extract from `.env.local`:
- `BFF_PORT` — the HTTP port the BFF listens on
- `BRANCH` — the branch/environment slug used when scaffolding
- `RABBIT_PORT` / `RABBIT_MGMT_PORT` — infrastructure ports

**Auto-detect BFF mode**: if `src/{zone-abbrev}/{capability-id}-bff/` exists and
contains a `.csproj`, enable BFF testing automatically (no need for `--bff` flag).

If the BFF directory exists but `.env.local` is missing:
> "BFF directory found but `.env.local` is absent. Run `create-bff` again or create
> `.env.local` manually with BFF_PORT, BRANCH, RABBIT_PORT, RABBIT_MGMT_PORT."

---

## Step 3 — Prepare the Test Environment

```bash
# 1. Isolated temporary directory
TEMP_DIR=$(mktemp -d /tmp/test-{capability-id}-XXXXXX)
echo "Test environment: $TEMP_DIR"

# 2. Copy frontend artifacts (read-only — originals are not touched)
cp -r sources/{capability-id}/frontend/. "$TEMP_DIR/frontend/"

# 3. Free HTTP port for the static frontend server
HTTP_PORT=$(python3 -c "import socket; s=socket.socket(); s.bind(('',0)); print(s.getsockname()[1]); s.close()")

# 4. Static HTTP server (non-blocking)
python3 -m http.server "$HTTP_PORT" --directory "$TEMP_DIR/frontend/" &
HTTP_PID=$!
echo "Frontend server: http://localhost:$HTTP_PORT (PID $HTTP_PID)"
sleep 1

# 5. Optional backend microservice (if sources/ exist and are built)
BACKEND_PID=""
if [ -f "sources/{capability-name}/backend/src/.../Presentation/bin/..." ]; then
  dotnet run --project sources/{capability-name}/backend/src/...Presentation/ &
  BACKEND_PID=$!
  sleep 3
fi

# 6. Optional BFF (if BFF directory exists and .env.local is present)
BFF_PID=""
BFF_DIR="src/{zone-abbrev}/{capability-id}-bff"
if [ -f "$BFF_DIR/.env.local" ]; then
  source "$BFF_DIR/.env.local"
  echo "Starting BFF on port $BFF_PORT (branch: $BRANCH)..."
  dotnet run --project "$BFF_DIR" --urls "http://localhost:$BFF_PORT" &
  BFF_PID=$!
  # Wait for BFF readiness via /health
  for i in $(seq 1 15); do
    curl -sf "http://localhost:$BFF_PORT/health" >/dev/null 2>&1 && break
    sleep 1
  done
  curl -sf "http://localhost:$BFF_PORT/health" >/dev/null 2>&1 \
    && echo "BFF ready at http://localhost:$BFF_PORT" \
    || echo "WARNING: BFF did not respond to /health after 15s — tests may fail"
fi
```

**Test modes** (selected automatically based on available artifacts):

| Mode | Frontend | BFF | Backend | Notes |
|------|----------|-----|---------|-------|
| Full-mock | present | absent | absent | Playwright intercepts all API calls with STUB_DATA |
| Frontend + BFF | present | present | absent | BFF started locally; frontend routes to it |
| Backend only | absent | absent | present | .NET integration tests without a browser |
| Full stack | present | present | present | End-to-end through BFF and backend |

---

## Step 4 — Generate Test Files

Create the following structure in the project directory:

```
tests/{capability-id}/TASK-NNN-{slug}/
├── conftest.py           ← fixtures: HTTP server, Playwright page, mocked routes
├── test_dod.py           ← one test per criterion from the "Definition of Done"
├── test_business_rules.py ← ADR rules and plan scoping rules
└── test_strategic.py     ← product / strategic vision alignment
```

### conftest.py

The `conftest.py` contains:
1. **Mock data** (taken in full from `MOCK_DATA` in `config.js`)
2. The **`page` fixture** which:
   - Launches Playwright (headless Chromium)
   - Registers mocked routes for each API endpoint
   - Navigates to `http://localhost:{HTTP_PORT}?beneficiaire=test-001`
3. View navigation helpers if multiple views exist

Template (adapt to the actual data extracted from `STUB_DATA` in `api.js`):

The frontend uses the `frontend-baseline` pattern: API calls go through
`window.{CapabilityName}Api` (useMockData=true by default). Playwright overrides these
methods via `add_init_script()` **before** the page loads.

To simulate consent refusal: URL parameter `?consentement=refuse`.
To inject the beneficiary identifier: URL parameter `?beneficiaireId=BEN-001`.

```python
import json
import pytest
from playwright.sync_api import sync_playwright, Page

# ── Mock data (extracted from STUB_DATA in api.js) ────────────────────────
MOCK_BENEFICIAIRE_ID = "BEN-001"

MOCK_SITUATION = {
    # Copy the complete STUB_DATA.situation structure from api.js
    "beneficiaire": {"id": "BEN-001", "nom": "Dupont", "prenom": "Marie"},
    "palierCourant": {"id": "PAL-002", "niveau": 2, "nom": "Autonomie Guidée",
                      "description": "..."},
    "prochainPalier": {"id": "PAL-003", "niveau": 3, "nom": "Autonomie Élargie",
                       "ecartScore": 120, "scoreActuel": 380, "scoreCible": 500},
    "enveloppesActives": [
        {"id": "ENV-001", "categorie": "Alimentation", "categorieIcone": "🛒",
         "soldeDisponible": 143.50, "montantTotal": 300.00,
         "periodeLabel": "Mai 2026", "devise": "EUR"},
    ],
    "enveloppesBloqueees": [
        {"id": "ENV-BLK-001", "categorie": "Voyages", "categorieIcone": "✈️",
         "raisonRestriction": "Disponible à partir du Palier 4."},
    ],
    "horodatage": "2026-04-24T10:00:00Z",
}

BASE_URL = "http://localhost:{HTTP_PORT}"

# Script injected before load: override window.{CapabilityName}Api
INIT_SCRIPT_CONSENT_OK = f"""
    window.__TEST_SITUATION__ = {json.dumps(MOCK_SITUATION)};
    window.__TEST_CONSENT_ACCORDE__ = true;
"""

@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p

@pytest.fixture
def page(playwright_instance):
    """Page with consent granted — data from STUB_DATA."""
    browser = playwright_instance.chromium.launch(headless=True)
    context = browser.new_context()
    pg = context.new_page()
    # The frontend uses its own stubs (useMockData=true) — no need to intercept routes.
    # Navigate with ?beneficiaireId= to inject the test identifier.
    pg.goto(f"{BASE_URL}?beneficiaireId={MOCK_BENEFICIAIRE_ID}")
    pg.wait_for_load_state("networkidle")
    yield pg
    browser.close()

@pytest.fixture
def page_consent_refuse(playwright_instance):
    """Variant: consent revoked (via ?consentement=refuse)."""
    browser = playwright_instance.chromium.launch(headless=True)
    context = browser.new_context()
    pg = context.new_page()
    pg.goto(f"{BASE_URL}?beneficiaireId={MOCK_BENEFICIAIRE_ID}&consentement=refuse")
    pg.wait_for_load_state("networkidle")
    yield pg
    browser.close()
```

**Note**: if a task requires test data different from the default `STUB_DATA`
(e.g., maximum tier reached, all envelopes blocked), use `add_init_script()` to
inject an override of the `window.{CapabilityName}Api` methods before navigation.

### test_dod.py

One test per criterion from the "Definition of Done" section of the task.

Generation rule:
- Each `[ ]` in the DoD becomes a `test_*` function
- The test docstring cites the criterion verbatim
- Assertions use Playwright's `expect()` for DOM elements, and
  `page.evaluate()` inspections for DOM order or JS data

Common pattern examples:

```python
# Verify an element is visible
def test_palier_courant_affiche(page):
    """DoD: The web view displays the current tier and its description."""
    expect(page.locator("#section-progression")).to_be_visible()
    expect(page.locator(".palier-card")).to_be_visible()

# Verify DOM order (dignity rule)
def test_progression_avant_restrictions(page):
    """DoD: Accomplished progress is shown before restrictions (dignity rule ADR-FUNC-0009)."""
    progression_y = page.evaluate(
        "document.querySelector('#section-progression').getBoundingClientRect().top"
    )
    enveloppes_y = page.evaluate(
        "document.querySelector('#section-enveloppes, .section-enveloppes').getBoundingClientRect().top"
    )
    assert progression_y < enveloppes_y, (
        "The progression section must appear before the envelopes section in the visual render"
    )

# Verify a network call is emitted
def test_consultation_emise(playwright_instance):
    """DoD: TableauDeBord.Consulté is emitted at each consultation."""
    browser = playwright_instance.chromium.launch(headless=True)
    context = browser.new_context()
    pg = context.new_page()
    consultations = []
    pg.route("**/consultations**", lambda r: (consultations.append(r.request.url), r.fulfill(status=204, body="")))
    # ... other mock routes
    pg.goto(f"{BASE_URL}?beneficiaire=test-001")
    pg.wait_for_load_state("networkidle")
    assert len(consultations) >= 1, "The TableauDeBord.Consulté event must be emitted"
    browser.close()

# Verify a blocking behavior
def test_gate_bloque_sans_consentement(page_consent_refuse):
    """DoD: The consent gate blocks access if Consentement.Accordé is absent."""
    expect(page_consent_refuse.locator(".gate-consentement")).to_be_visible()
    expect(page_consent_refuse.locator("#section-progression")).not_to_be_visible()

# Verify filters (for history views)
def test_filtres_disponibles(page):
    """DoD: History is filterable by period, category, status."""
    expect(page.locator("input[type='date'], [data-filtre='date-debut']")).to_be_visible()
    expect(page.locator("select[name='categorie'], [data-filtre='categorie']")).to_be_visible()
    expect(page.locator("select[name='statut'], [data-filtre='statut']")).to_be_visible()
```

### test_business_rules.py

Tests derived from the FUNC ADRs and the plan "scoping decisions". These are not
explicit DoD criteria — they come from reading the ADRs and the plan.

Typical examples:
- Dignity rule (ADR-BCM-FUNC-0009) → sections in the right order
- V0 without gamification → absence of badges, scores, level-up progress bars
- Error messages in business language → absence of raw HTTP codes in the DOM
- Dignity vocabulary → absence of infantilizing or stigmatizing terms

```python
def test_aucun_badge_ni_score_visible(page):
    """Scoping rule (plan): V0 without gamification — no badge or score visible."""
    assert page.locator("[class*='badge'], [class*='score'], [class*='trophy']").count() == 0

def test_messages_erreur_en_langage_metier(playwright_instance):
    """ADR: API errors are translated to business language (no raw HTTP code)."""
    browser = playwright_instance.chromium.launch(headless=True)
    context = browser.new_context()
    pg = context.new_page()
    pg.route("**/beneficiaires/**", lambda r: r.fulfill(status=503, body='{"error":"Service unavailable"}'))
    pg.route("**/consentements/**", lambda r: r.fulfill(status=200, body='{"statut":"accorde"}'))
    pg.goto(f"{BASE_URL}?beneficiaire=test-001")
    pg.wait_for_load_state("networkidle")
    page_text = pg.inner_text("body")
    assert "503" not in page_text, "HTTP codes must not be exposed to the user"
    assert "Service unavailable" not in page_text.lower()
    browser.close()
```

### test_strategic.py

Lightweight tests verifying alignment with the product and strategic vision.
These tests do not validate functional behavior but the interface's intent.

```python
def test_labels_en_francais(page):
    """Product vision: the interface is in French (no English exposed to the user)."""
    # Check for the absence of common English labels in the visible DOM
    for terme_anglais in ["dashboard", "wallet", "balance", "tier", "envelope"]:
        visible_text = page.inner_text("main").lower()
        assert terme_anglais not in visible_text, (
            f"English term '{terme_anglais}' found in the interface — the UI must be in French"
        )

def test_posture_encourageante_dans_progression(page):
    """Product vision: progress is presented in an encouraging way."""
    progression_text = page.locator("#section-progression").inner_text()
    termes_positifs = ["progression", "palier", "avancement", "atteint", "prochaine étape"]
    assert any(t in progression_text.lower() for t in termes_positifs), (
        "The progression section must use encouraging vocabulary"
    )
```

---

## Step 5 — Run the Tests

```bash
cd {project_root}
python3 -m pytest tests/{capability-id}/TASK-NNN-{slug}/ \
  -v \
  --tb=short \
  --html=tests/{capability-id}/TASK-NNN-{slug}/report.html \
  --self-contained-html \
  2>&1 | tee tests/{capability-id}/TASK-NNN-{slug}/run.log
```

If `pytest-html` is not available, remove `--html` and `--self-contained-html`.

---

## Step 6 — Report Results

After execution, translate pytest results into business language:

```
═══════════════════════════════════════════════════════════
Test Results — TASK-[NNN]: [Title]
Capability : [ID] — [TOGAF] Zone
Branch/Env : [branch slug]
Mode       : [full-mock | frontend+bff | backend | full-stack]
═══════════════════════════════════════════════════════════

Definition of Done:
  ✅ Consent gate blocks without Consentement.Accordé
  ✅ Current tier displayed with description
  ✅ Next tier and progression gap displayed
  ❌ TableauDeBord.Consulté emitted — [failure reason if available]
  ✅ Progress shown before restrictions (dignity rule)

Business Rules (FUNC ADRs):
  ✅ Dignity rule: correct visual order
  ✅ V0 without gamification: no badge or score visible
  ✅ API errors in business language

Product / Strategic Vision:
  ✅ Interface in French
  ✅ Encouraging vocabulary in the progression section

BFF (if active):
  ✅ /health returns 200
  ✅ Snapshot endpoint responds
  ✅ ETag / 304 support working
  ✅ environment tag matches branch

───────────────────────────────────────────────────────────
Score: [N]/[Total] criteria validated
Detailed report: tests/{capability-id}/TASK-NNN-{slug}/report.html
Full logs: tests/{capability-id}/TASK-NNN-{slug}/run.log
═══════════════════════════════════════════════════════════
```

For each failing test, provide:
1. The DoD/ADR criterion concerned
2. What the test found vs. what it expected
3. A correction suggestion in the frontend code or BFF

---

## Step 6b — BFF-specific Tests (when BFF is active)

When the BFF is running locally, generate an additional test file:

```
tests/{capability-id}/TASK-NNN-{slug}/
└── test_bff.py   ← BFF health, endpoint contracts, ETag behaviour
```

### test_bff.py

```python
import requests

BFF_BASE = f"http://localhost:{BFF_PORT}"

def test_bff_health():
    """BFF /health endpoint returns 200."""
    r = requests.get(f"{BFF_BASE}/health", timeout=5)
    assert r.status_code == 200

def test_bff_snapshot_endpoint():
    """BFF exposes the snapshot endpoint for each L3."""
    # Replace with actual L3 path from the FUNC ADR
    r = requests.get(f"{BFF_BASE}/{zone_abbrev}/{capability_id}/{l3_id}/snapshot",
                     headers={"Accept": "application/json"}, timeout=5)
    # May return 204 if the in-memory cache is empty — that is valid on cold start
    assert r.status_code in (200, 204)

def test_bff_etag_304():
    """BFF returns 304 Not Modified when If-None-Match matches the current ETag."""
    r1 = requests.get(f"{BFF_BASE}/{zone_abbrev}/{capability_id}/{l3_id}/snapshot", timeout=5)
    if r1.status_code == 200 and "ETag" in r1.headers:
        etag = r1.headers["ETag"]
        r2 = requests.get(f"{BFF_BASE}/{zone_abbrev}/{capability_id}/{l3_id}/snapshot",
                          headers={"If-None-Match": etag}, timeout=5)
        assert r2.status_code == 304, "BFF must return 304 when ETag matches"

def test_bff_branch_env_tag():
    """OTel environment tag matches the scaffolded branch."""
    # Verify via /health extended response or a dedicated /info endpoint if present
    r = requests.get(f"{BFF_BASE}/health", timeout=5)
    if r.status_code == 200:
        body = r.json() if r.headers.get("Content-Type", "").startswith("application/json") else {}
        env = body.get("environment", body.get("branch", ""))
        if env:
            assert env == "{branch}", f"BFF environment tag should be '{'{branch'}' got '{env}'"
```

These tests are skipped automatically if `BFF_PID` is empty (BFF not running).

---

## Step 7 — Clean Up the Environment

```bash
# Stop the ephemeral HTTP server
kill $HTTP_PID 2>/dev/null && echo "Frontend server stopped."

# Stop the backend if launched
[ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null && echo "Backend stopped."

# Stop the BFF if launched
[ -n "$BFF_PID" ] && kill $BFF_PID 2>/dev/null && echo "BFF stopped."

# Delete the temporary directory
rm -rf "$TEMP_DIR" && echo "Temporary environment removed."
```

---

## Fallback: Manual Test Plan

If Playwright cannot be installed, generate instead a file
`tests/{capability-id}/TASK-NNN-{slug}/manual-checklist.md`:

```markdown
# Manual Test Checklist — TASK-[NNN]

## Startup
cd sources/{capability-id}/frontend
python3 -m http.server 3000
# Open http://localhost:3000?beneficiaireId=BEN-001

## Definition of Done
- [ ] [Criterion 1] — How to verify manually: [instruction]
- [ ] [Criterion 2] — ...

## ADR Business Rules
- [ ] Dignity rule: [verification instruction]

## Product Vision
- [ ] Labels in French: [instruction]
```

---

## Skill Limitations

- Frontend tests run in **full-mock** mode by default (Playwright intercepts network calls).
  If the backend is needed for real integration tests, start the microservice manually first
  and provide its port.
- This skill does not test behaviors that require real authentication or persistent
  database state.
- The `test_strategic.py` tests are lightweight heuristics — a missing vocabulary term does not
  necessarily indicate an alignment problem, but warrants review.
- The skill never modifies the frontend or backend source files.
