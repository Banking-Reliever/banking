---
name: code-web-frontend
description: >
  Generates a vanilla web frontend (HTML5 + CSS3 + pure JavaScript, no framework) for a
  business capability, from a TASK-NNN task and the API produced by the implement-capability skill.
  Uses the plan, FUNC ADRs, product vision, and strategic vision as business context
  to produce an interface consistent with dignity rules and urbanization constraints.
  
  Trigger this skill whenever the user says: "code web frontend", "frontend for TASK-NNN",
  "generate the web interface", "create the HTML for this task", "implement the web view",
  "scaffold frontend", "TASK-NNN frontend", "generate UI", "create HTML frontend",
  "implement frontend task", "user interface for [capability]", or any request
  concerning the production of a browser web view for a planned business capability.
  Also trigger proactively when a TASK-NNN describes a "web interface",
  a "view", a "dashboard" or a "web channel" and the backend microservice is already
  scaffolded in sources/.
---

# Code Web Frontend

You produce a **vanilla** browser web frontend (HTML5 + CSS3 + pure JavaScript, zero
external dependencies) for a specific business task. Your output is a
`sources/{capability-id}/frontend/` folder ready to be opened directly in a browser or served
by a simple static HTTP server.

**Reference graphical pattern: `frontend-baseline`** — the
`frontend-baseline/CAP.CAN.001.TAB/` folder is the canonical reference for structure,
CSS conventions, and the JavaScript pattern. Every file produced must follow
its architecture. When in doubt about a detail (naming, DOM pattern, style), consult
the files in that folder.

---

## Before You Begin

### Step 0 — Identify the Task

The user must provide a task identifier (e.g., `TASK-003`) or a capability name.
If ambiguous, list all tasks with status `todo` in `plan/*/tasks/` and ask which one to start.

### Step 1 — Read the Task

Find the file at `/plan/{capability-id}/tasks/TASK-NNN-*.md`.

Verify:
- `status: todo` (not `in_progress` or `done`)
- All tasks in `depends_on` have status `done`
- No blocking open questions

If a prerequisite fails, stop and explain:
> "TASK-NNN cannot start because [reason]. Resolve this first."

### Step 1b — Detect the Git Branch

```bash
BRANCH=$(git branch --show-current 2>/dev/null | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-\|-$//g')
echo "Branch: $BRANCH"
```

Use `local` if the command fails. This value will be displayed in the frontend header as a discreet environment badge.

### Step 2 — Read the Business Context

Read in order:

1. `/plan/{capability-id}/plan.md` — epics, scoping rules, constraints
2. `/func-adr/` — governing FUNC ADRs (read all ADRs cited in the task)
3. `/product-vision/product.md` — service offer, tone
4. `/strategic-vision/strategic-vision.md` — L1/L2/L3 strategic capabilities

Extract from these sources:
- Business rules that apply to the interface (e.g., "dignity rule: progression before restriction")
- Business vocabulary to use in the UI (labels, messages)
- Displayed business objects (Beneficiary, Tier, Envelope, Transaction...)

### Step 3 — Discover the API Contract

Look for microservice sources in `sources/` following this logic:

```
sources/
  {capability-name-kebab}/backend/src/
    {Namespace}.{CapabilityName}.Presentation/
      Controllers/
        {AggregateName}CmdController.cs   ← POST endpoints
        {AggregateName}ReadController.cs  ← GET endpoints
      config/cold.json                    ← LOCAL_PORT
    {Namespace}.{CapabilityName}.Contracts/
      Commands/                           ← POST request shapes
    {Namespace}.{CapabilityName}.Domain/
      Model/AR/{AggregateName}/DTO/       ← GET response shapes
```

If `sources/` does not yet exist (microservice not yet scaffolded):
- Infer the API contract from the DTOs and events described in the task and plan
- Document the contract in a comment at the top of `api.js`
- State that the contract is **inferred** and will need to be adjusted once the microservice is scaffolded

Otherwise, read the Controllers and DTO files to establish precisely:
- Routes: `GET /{AggregateName}/{id}`, `POST /{AggregateName}/Create`, etc.
- Request shapes (Command fields)
- Response shapes (DTO fields)
- The local port from `cold.json`

---

## Summary Before Generation

Before writing any file, present to the user:

```
Ready to generate frontend for TASK-[NNN]: [Title]

Capability    : [Name] ([ID]) — [TOGAF] Zone
Epic          : [Epic N — Name]

Views to produce:
  - [view-1]: [short description from "What to Build"]
  - [view-2]: [...]

Detected API contract:
  GET  /{AggregateName}/{id}       → {AggregateName}Dto
  POST /{AggregateName}/Create     ← Create{AggregateName}Command
  Local port: {LOCAL_PORT}        (configurable in API_CONFIG.baseUrl in api.js)

Business rules applied in the UI:
  - [rule 1 extracted from plan/ADR]
  - [rule 2...]

Output: sources/{capability-id}/frontend/

Shall I proceed?
```

Wait for confirmation before generating.

---

## Frontend Generation

### Output Structure

```
sources/{capability-id}/frontend/
├── index.html      ← entry page, zones #loading / #consent-gate / #dashboard
├── styles.css      ← vanilla CSS, complete variables, clean and functional design
├── api.js          ← API_CONFIG, STUB_DATA, network layer, window.{CapabilityName}Api
└── app.js          ← application IIFE, DOM helpers, init flow, window.App
```

No `js/` or `css/` subdirectories — flat structure, as in `frontend-baseline`.

### Principles — HTML

- Correct semantics: `<main>`, `<section>`, `<article>`, `<header>`, `<nav>`
- No external dependencies (no CDN, no framework, no `type="module"`)
- Scripts loaded at the bottom of `<body>` in order: `api.js` then `app.js`
- **Branch badge**: in the `<header>`, include a `<span id="branch-badge" class="branch-badge">{branch}</span>` element displaying the current branch name. This badge is discreet (small font, neutral color) but always visible to identify the development environment. The value is injected statically in the generated HTML (no JavaScript to retrieve it).
- Three top-level zones, all managed by `showEl`/`hideEl`:
  - `#loading` — loading overlay (visible at startup)
  - `#consent-gate` — blocking overlay if consent is absent (hidden by default)
  - `#dashboard` (or main view name) — business content (hidden by default)
- IDs and classes follow business vocabulary in French
  (`#section-progression`, `.enveloppe-card`, `#table-historique`)
- The `<title>` and visible labels use the plan vocabulary
- The "dignity rule" translates to DOM order: the progression section
  precedes the envelopes/restrictions section

### Principles — CSS (`styles.css`)

The CSS file must define the complete design system in `:root` variables:

```css
:root {
  /* Primary colors */
  --color-primary: #2563eb;
  --color-primary-light: #dbeafe;
  --color-primary-dark: #1d4ed8;

  /* Progression / success */
  --color-success: #16a34a;
  --color-success-light: #dcfce7;

  /* Restriction / attention (neutral, not alarming) */
  --color-neutral: #64748b;
  --color-neutral-light: #f1f5f9;
  --color-neutral-200: #e2e8f0;

  /* Consent alert */
  --color-warning: #d97706;
  --color-warning-light: #fef3c7;

  /* Text */
  --color-text-primary: #0f172a;
  --color-text-secondary: #475569;
  --color-text-muted: #94a3b8;

  /* Surfaces */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-border: #e2e8f0;

  /* Tiers (color by level, injected via data-level="N") */
  --palier-1: #0ea5e9;
  --palier-2: #8b5cf6;
  --palier-3: #f59e0b;
  --palier-4: #ef4444;
  --palier-5: #10b981;

  /* Typography */
  --font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --font-size-xs: 0.75rem;    --font-size-sm: 0.875rem;
  --font-size-base: 1rem;     --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;    --font-size-2xl: 1.5rem;

  /* Spacing (4px scale) */
  --space-1: 0.25rem;   --space-2: 0.5rem;    --space-3: 0.75rem;
  --space-4: 1rem;      --space-5: 1.25rem;   --space-6: 1.5rem;
  --space-8: 2rem;      --space-10: 2.5rem;   --space-12: 3rem;

  /* Radii */
  --radius-sm: 0.375rem;  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;   --radius-xl: 1rem;  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
}
```

Additional CSS rules:
- Branch badge: `.branch-badge { font-size: var(--font-size-xs); font-family: monospace; color: var(--color-text-muted); background: var(--color-neutral-light); border: 1px solid var(--color-border); border-radius: var(--radius-sm); padding: 2px var(--space-2); vertical-align: middle; }`
- Box-model reset: `*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }`
- Visibility utility: `.hidden { display: none !important; }`
- Content width: `max-width: 1100px; margin: 0 auto;`
- Minimal responsive: `@media (max-width: 768px)` — columns → 1 column, reduced spacing
- If the task concerns a `mobile` channel, add a dedicated `@media (max-width: 480px)`
- Tier badge color via CSS attribute: `.palier-badge[data-level="2"] { background-color: var(--palier-2); }`
- Animated bars via `transition: width 0.6s ease-in-out` and `data-target-width` (see JS)

### Principles — JavaScript

#### `api.js`

Canonical structure (see `frontend-baseline/CAP.CAN.001.TAB/api.js`):

```js
/**
 * api.js — Data access layer for {capability-id}
 *
 * API contract: [document each endpoint here]
 *   GET  /api/consent/{beneficiaireId}  → { accordé: boolean, raison?: string }
 *   GET  /api/{aggregate}/{id}/situation → {AggregateName}Dto
 *   POST /api/events                    → void
 */

const API_CONFIG = {
  baseUrl: window.API_BASE_URL || '',
  useMockData: true,      // Set to false to point to the real microservice
  requestTimeoutMs: 8000,
};

/* ── Stub (realistic development data) ── */
const STUB_DATA = {
  consent: { accordé: true, raison: null },
  situation: {
    beneficiaire: { id: 'BEN-001', nom: 'Dupont', prenom: 'Marie' },
    palierCourant: { id: 'PAL-002', niveau: 2, nom: '...', description: '...' },
    prochainPalier: { id: 'PAL-003', niveau: 3, nom: '...', ecartScore: 120,
                      scoreActuel: 380, scoreCible: 500 },
    enveloppesActives: [ /* ... realistic objects ... */ ],
    enveloppesBloqueees: [ /* ... */ ],
    horodatage: new Date().toISOString(),
  },
};

/* ── HTTP utilities ── */
async function fetchWithTimeout(url, options = {}) { /* ... */ }
class ApiError extends Error { /* ... */ }

/* ── Stubs — simulated network delay ── */
async function stubConsentResponse(beneficiaireId) {
  await new Promise(r => setTimeout(r, 300));
  // Simulate refusal via ?consentement=refuse
  const params = new URLSearchParams(window.location.search);
  if (params.get('consentement') === 'refuse') {
    return { accordé: false, raison: 'Votre consentement a été révoqué.' };
  }
  return { ...STUB_DATA.consent };
}

/* ── Public API — exposed as global ── */
async function checkConsent(beneficiaireId) {
  return API_CONFIG.useMockData
    ? stubConsentResponse(beneficiaireId)
    : fetchWithTimeout(`${API_CONFIG.baseUrl}/api/consent/${encodeURIComponent(beneficiaireId)}`);
}

/* Repeat the pattern for each endpoint */

window.{CapabilityName}Api = { checkConsent, load..., emit..., ApiError };
```

JavaScript rules for `api.js`:
- Always expose the API via `window.{CapabilityName}Api` (no ES6 `export`)
- `STUB_DATA` contains realistic and complete values (no empty placeholders)
- Each stub simulates a network delay (`stubDelay(300-500ms)`)
- HTTP error handling: `ApiError` with `status` and business message
- Fire-and-forget for event emission (do not block display)

#### `app.js`

Canonical structure (see `frontend-baseline/CAP.CAN.001.TAB/app.js`):

```js
(function () {
  'use strict';

  /* ── DOM helpers ── */
  function $(id)          { return document.getElementById(id); }
  function showEl(id)     { const el=$(id); if(el) el.classList.remove('hidden'); }
  function hideEl(id)     { const el=$(id); if(el) el.classList.add('hidden'); }
  function setText(id, t) { const el=$(id); if(el) el.textContent = t; }

  /* ── Formatting ── */
  function formatCurrency(amount, devise = 'EUR') {
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: devise }).format(amount);
  }
  function formatPercent(value, max) {
    return max === 0 ? 0 : Math.min(100, Math.round((value / max) * 100));
  }

  /* ── Rendering — functions per business section ── */
  function renderProgression(situation) { /* ... */ }
  function renderEnveloppes(situation) { /* ... */ }
  function renderDashboard(situation) {
    // 1. Progression (dignity rule — always first)
    renderProgression(situation);
    // 2. Envelopes / main content
    renderEnveloppes(situation);
  }

  /* ── Consent gate ── */
  function showConsentGate(raison) {
    hideEl('loading');
    hideEl('dashboard');
    const msgEl = $('consent-message');
    if (msgEl && raison) msgEl.textContent = raison;
    showEl('consent-gate');
  }

  /* ── Resolve beneficiary identity ── */
  function resolveBeneficiaireId() {
    const params = new URLSearchParams(window.location.search);
    return params.get('beneficiaireId') || 'BEN-001'; // ?beneficiaireId= in dev/test
  }

  /* ── Main initialization ── */
  async function init() {
    showEl('loading');
    hideEl('dashboard');
    hideEl('consent-gate');
    const beneficiaireId = resolveBeneficiaireId();
    try {
      const consent = await {CapabilityName}Api.checkConsent(beneficiaireId);
      if (!consent.accordé) { showConsentGate(consent.raison); return; }
      const situation = await {CapabilityName}Api.load...(beneficiaireId);
      renderDashboard(situation);
      hideEl('loading');
      showEl('dashboard');
      {CapabilityName}Api.emit...(beneficiaireId, situation.palierCourant.id);
    } catch (err) {
      hideEl('loading');
      renderErrorState(err);
    }
  }

  /* ── Public API (used by HTML buttons onclick=) ── */
  window.App = {
    reload()        { window.location.reload(); },
    retryConsent()  { window.location.reload(); },
    logout()        { window.location.href = window.location.pathname; },
  };

  /* ── Startup ── */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
```

JavaScript rules for `app.js`:
- IIFE with `'use strict'` — no global variables except `window.App`
- `resolveBeneficiaireId()` reads `?beneficiaireId=` first (test injection mechanism)
- `showEl`/`hideEl`: add/remove the `.hidden` class
- Animated bars: `data-target-width` on the fill, `requestAnimationFrame + setTimeout(150ms)`
- API errors are displayed in business language (no raw HTTP codes in the DOM)
- `renderErrorState`: inline overlay with business message and "Retry" button
- Event emission is fire-and-forget (does not block display)

**Consent gate** (if the task requires it):
First check in `init()`, before any data loading.
If `accordé === false` → `showConsentGate(raison)` and `return`.

**Event emission** (if the task mentions an event to produce, e.g., `TableauDeBord.Consulté`):
Fire-and-forget call after rendering, in the `try` block.

### Naming Conventions

| Artifact | Convention | Example |
|----------|-----------|---------|
| Main HTML ID | kebab-case, functional zone | `#section-progression`, `#consent-gate` |
| CSS class | kebab-case, business prefix | `.palier-card`, `.enveloppe-row` |
| Data attribute | kebab-case | `data-level`, `data-target-width`, `data-statut` |
| JS function | camelCase, verb + object | `renderProgression()`, `chargerHistorique()` |
| JS variable | camelCase, domain vocabulary | `palierCourant`, `enveloppesActives` |
| Global API | PascalCase + Api suffix | `window.DashboardApi`, `window.HistoriqueApi` |

### Test Data and Testability Contract

The `test-business-capability` skill relies on the artifacts you produce.
Follow these conventions to guarantee compatibility:

**`STUB_DATA` in `api.js`**

`STUB_DATA` is the canonical source of test data. It must be **complete** —
all properties used by the UI present with realistic values.
The test skill extracts this structure to build its Playwright mocks.

```js
const STUB_DATA = {
  consent: { accordé: true, raison: null },
  situation: {
    beneficiaire: { id: 'BEN-001', nom: 'Dupont', prenom: 'Marie' },
    palierCourant: { id: 'PAL-002', niveau: 2, nom: 'Autonomie Guidée',
                     description: 'Realistic description...' },
    prochainPalier: { id: 'PAL-003', niveau: 3, nom: 'Autonomie Élargie',
                      ecartScore: 120, scoreActuel: 380, scoreCible: 500 },
    enveloppesActives: [
      { id: 'ENV-001', categorie: 'Alimentation', categorieIcone: '🛒',
        soldeDisponible: 143.50, montantTotal: 300.00, periodeLabel: 'Mai 2026', devise: 'EUR' },
    ],
    enveloppesBloqueees: [
      { id: 'ENV-BLK-001', categorie: 'Voyages', categorieIcone: '✈️',
        raisonRestriction: 'Disponible à partir du Palier 4.' },
    ],
    horodatage: new Date().toISOString(),
  },
};
```

**URL Parameters for Testing**

| Parameter | Value | Effect |
|-----------|--------|-------|
| `?beneficiaireId=` | `BEN-001` | Injects the beneficiary identifier (test mechanism) |
| `?consentement=` | `refuse` | Forces consent refusal in the stub |

**Stable CSS Selectors (required)**

| Element | Required Selector |
|---------|-----------------|
| Progression section (tier) | `#section-progression` or `.section-progression` |
| Envelopes section | `#section-enveloppes` or `.section-enveloppes` |
| Restrictions/blocked section | `#enveloppes-bloquees` or `.enveloppes-bloquees` |
| Consent gate (overlay) | `#consent-gate` |
| Current tier card | `.palier-card` or `#palier-badge` |
| Transaction history table | `#table-historique` or `.table-historique` |
| Filters (inputs) | `[data-filtre]` on each filter input |

**API Calls via Global Only**

All network calls go through `window.{CapabilityName}Api`.
Playwright overrides these methods via `addInitScript()` to inject test data.

---

## Closure

After generating all files:

1. **Update the task status**: change `status: todo` to `status: done` in the
   `TASK-NNN-*.md` file.

2. **Update the index** `/plan/{capability-id}/tasks/index.md` to reflect the new status.

3. **Report to the user**:

```
TASK-[NNN] frontend generated in sources/{capability-id}/frontend/

Files produced:
  - index.html
  - styles.css
  - api.js            ← API_CONFIG.useMockData=true, adjust baseUrl if needed
  - app.js

To run locally:
  cd sources/{capability-id}/frontend
  python -m http.server 3000
  # then open http://localhost:3000?beneficiaireId=BEN-001

Test consent refusal:
  http://localhost:3000?beneficiaireId=BEN-001&consentement=refuse

Business rules applied:
  ✅ [rule 1]
  ✅ [rule 2]

DoD criteria covered:
  ✅ [condition 1]
  ✅ [condition 2]

Next available tasks:
  - TASK-[NNN+1]: [title] (was blocked by this task)
```

---

## Skill Limitations

- This skill generates **only** vanilla HTML/CSS/JS. It does not scaffold a backend,
  does not modify .NET files, and does not touch ADRs or the BCM.
- If the task involves both a backend and a frontend, start with `code` (implement-capability)
  before invoking this skill.
- If multiple tasks are frontend-only and depend on each other (e.g., TASK-003 → TASK-004),
  treat them sequentially: finish and mark `done` the first before starting the next.
- Automated validation of DoD criteria is handled by the `test-business-capability` skill,
  which uses Playwright to test the generated frontend. Launch it immediately after this skill.
