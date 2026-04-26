---
name: code
description: >
  Triggers the implementation of a specific task by reading its task file and invoking the 
  right implementation skill(s) based on the capability zone, then validates the result 
  with test-business-capability. Use this skill whenever the user wants to implement a 
  task, code a specific capability task, start development on a TASK-NNN, or execute an 
  implementation work item. Trigger on: "code TASK-NNN", "implement TASK-NNN", 
  "code this task", "start implementing", "build [capability]", or any time a task file 
  exists in /plan/{capability}/tasks/ with status "todo" and all dependencies are resolved. 
  Also trigger proactively when the user says "let's code" or "start development" and a 
  specific task or capability is named.
---

# Code Skill

You are the bridge between the planning world and the implementation world. Your job is to
read a task file, understand what it asks for in business terms, detect the capability zone,
invoke the right implementation skill(s), then validate the result with the test skill —
repeating until the Definition of Done is fully satisfied.

---

## Before You Begin

> **Note:** For orchestrated multi-task workflows (board view, prioritization, dependency
> tracking), use the `/kanban` skill instead — it calls this skill at the right moment.

1. **Identify the task.** The user should specify a task ID (e.g., `TASK-001`) or a capability
   name. If ambiguous, redirect to `/kanban` to get the prioritized list.

2. **Read the task file.** Find it at `/plan/{capability-id}/tasks/TASK-NNN-*.md`.

3. **Verify prerequisites:**
   - Status is `todo` or `in_progress` (not `in_review`, `done`, or `stalled`)
   - If status is `stalled`: stop and tell the user to run `/continue-work TASK-NNN` first.
   - All tasks in `depends_on` have status `done`
   - No open questions in the task file are unresolved

   If any prerequisite fails, stop and explain:
   > "TASK-NNN cannot start because [reason]. Resolve this first."

4. **Read supporting context:**
   - The capability's FUNC ADR(s) in `/func-adr/`
   - The capability's YAML in `/bcm/`
   - The plan file at `/plan/{capability-id}/plan.md`

5. **Read loop counters** from the task file frontmatter:
   - `loop_count`: number of remediation iterations already used (default `0` if absent)
   - `max_loops`: maximum allowed iterations (default `10` if absent)

   If the task file does not yet have these fields, treat them as `loop_count: 0` /
   `max_loops: 10` and write them to the frontmatter before proceeding:
   ```yaml
   loop_count: 0
   max_loops: 10
   ```

6. **Detect the zone** from the YAML (`zoning` field in `bcm/capabilities-*.yaml`
   or from the `decision_scope.zoning` in the FUNC ADR). Map it:

   | YAML `zoning` value          | Zone family       | Implementation path |
   |------------------------------|-------------------|---------------------|
   | `BUSINESS_SERVICE_PRODUCTION`| Core domain       | `implement-capability` |
   | `SUPPORT`                    | Transverse IT     | `implement-capability` |
   | `REFERENTIAL`                | Master data       | `implement-capability` |
   | `EXCHANGE_B2B`               | Ecosystem B2B     | `implement-capability` |
   | `DATA_ANALYTIQUE`            | Data / BI / AI    | `implement-capability` |
   | `STEERING`                   | Pilotage          | `implement-capability` |
   | `CHANNEL`                    | Omnichannel       | `create-bff` + `code-web-frontend` (parallel) |

---

## Step 0 — Create Isolation Branch

Before writing any code, create a dedicated branch and verify the git state:

```bash
# Ensure we are on main and the tree is clean
git status --porcelain
git checkout main 2>/dev/null || git checkout master 2>/dev/null

# Derive the branch name from the task ID and title (kebab-case)
TASK_ID="TASK-NNN"                          # e.g. TASK-003
TASK_SLUG="<title-in-kebab-case>"           # e.g. beneficiary-dashboard
BRANCH_NAME="feat/${TASK_ID}-${TASK_SLUG}"  # e.g. feat/TASK-003-beneficiary-dashboard

git checkout -b "$BRANCH_NAME"
```

Report to the user:
> "Working on branch `feat/TASK-NNN-{slug}`. All changes will be isolated here until the PR is opened."

If the repository has no commits yet (`git log` fails), skip the `git checkout main` step and
simply run `git checkout -b "$BRANCH_NAME"` from the initial state.

---

## Step 1 — Summarize What Will Be Built

Before invoking any implementation skill, present a clear summary to the user.

**For non-CHANNEL zones:**

```
Ready to implement TASK-[NNN]: [Title]

Capability: [Name] ([ID]) — [Zone]
Epic: [Epic N — Name]

What will be built:
[2-3 sentences from the task's "What to Build" section, in plain language]

Business events that will become emittable:
- [EventName]
- [EventName]

Definition of Done:
- [ ] [condition 1]
- [ ] [condition 2]

Implementation path: implement-capability (.NET microservice)

Shall I proceed?
```

**For CHANNEL zone:**

```
Ready to implement TASK-[NNN]: [Title]

Capability: [Name] ([ID]) — CHANNEL zone
Epic: [Epic N — Name]

What will be built:
[2-3 sentences from the task's "What to Build" section, in plain language]

Events consumed (BFF subscriptions):
- [EventName] from [EmittingCapabilityId]

Events produced:
- [EventName]

Definition of Done:
- [ ] [condition 1]
- [ ] [condition 2]

Implementation path: create-bff + code-web-frontend (launched in parallel)
After implementation: test-business-capability will validate all DoD criteria.

Shall I proceed?
```

Wait for the user's confirmation before proceeding.

---

## Step 2 — Invoke the Implementation Skill(s)

### Path A — Non-CHANNEL zones (BUSINESS_SERVICE_PRODUCTION, SUPPORT, REFERENTIAL, EXCHANGE_B2B, DATA_ANALYTIQUE, STEERING)

Invoke the `implement-capability` skill with the full task context assembled as input.
The context to pass includes:

- The capability ID, name, zone, and level
- The governing FUNC ADR(s)
- The business events to implement (names and trigger conditions)
- The business objects involved
- The event subscriptions required
- The Definition of Done

Say:
> "Invoking implement-capability for [capability name] with task TASK-[NNN]..."

The implement-capability skill handles all architectural and implementation decisions —
Clean Architecture, DDD, microservice scaffolding, .NET patterns. Your job is to feed it
the right business context from the task file.

---

### Path B — CHANNEL zone

Invoke **both** skills in parallel (two independent agents):

1. **`create-bff`** — scaffolds the .NET 10 BFF that aggregates upstream events from RabbitMQ
   and exposes REST endpoints per L3 sub-capability. Pass:
   - The L2 capability ID (e.g., `CAP.CAN.001`)
   - The FUNC ADR content (L3 list, events consumed, events produced, dignity rules)
   - Available tactical ADRs from `tech-adr/`

2. **`code-web-frontend`** — generates the vanilla HTML/CSS/JS frontend from the task plan,
   FUNC ADRs, and the BFF API contract (or inferred contract if the BFF is not yet compiled).
   Pass:
   - The task identifier and the task file content
   - The FUNC ADR content and product vision
   - Instruction to infer the BFF API contract from endpoint paths derived from Step 1 of
     create-bff (or to read `src/{zone-abbrev}/{capability-id}-bff/` if already written)

Say:
> "Invoking create-bff and code-web-frontend in parallel for [capability name] — CHANNEL zone..."

Wait for **both** agents to complete before proceeding to Step 3.

---

## Step 3 — Validate with test-business-capability

After all implementation agents complete (regardless of zone), invoke the
`test-business-capability` skill to validate that the delivered artifacts satisfy the
Definition of Done, FUNC ADR rules, and the product vision.

Pass to the test skill:
- The task identifier (`TASK-NNN`)
- The capability ID and zone
- A flag indicating which artifacts were produced:
  - Non-CHANNEL: `backend-only` (no frontend unless the task explicitly includes a web view)
  - CHANNEL: `bff + frontend`
- Any port or path information printed by the implementation skills

Say:
> "Running test-business-capability for TASK-[NNN] (loop [loop_count+1]/[max_loops])..."

### If all tests pass

Proceed directly to Step 4 (close and open PR).

### If tests fail — Remediation loop

**Before each remediation iteration**, check the loop budget:

```
IF loop_count >= max_loops → trigger the Stall Procedure (see below)
ELSE:
  loop_count += 1
  Write updated loop_count to task file frontmatter
  Proceed with the remediation iteration
```

For each remediation iteration within budget:

1. **Identify the failing artifact** (BFF, frontend, microservice).

2. **Re-invoke the relevant implementation skill** with an additional remediation context
   block prepended to the prompt:

   ```
   ── REMEDIATION CONTEXT (loop [loop_count]/[max_loops]) ──
   The previous implementation of TASK-[NNN] failed the following test criteria:

   ❌ [Criterion 1]: [what the test found vs. what was expected]
      Suggested correction: [from the test skill's output]

   ❌ [Criterion 2]: [...]
      Suggested correction: [...]

   Re-implement only what is needed to fix these criteria. Do not touch passing code.
   ── END REMEDIATION CONTEXT ──
   ```

3. **After the fix is applied**, re-invoke `test-business-capability` for the same task.

4. **Repeat** from the budget check until all criteria pass or the budget is exhausted.

---

### Stall Procedure (loop budget exhausted)

Triggered when `loop_count >= max_loops` and tests still fail.

1. **Update the task file frontmatter**:
   ```yaml
   status: stalled
   loop_count: [current value]
   max_loops: [current value]
   stalled_reason: |
     Loop budget exhausted after [loop_count] iteration(s).
     Failing criteria at last run:
     - ❌ [Criterion 1]: [failure description]
     - ❌ [Criterion 2]: [failure description]
     Last test run: [DATE]
   ```

2. **Refresh `/plan/BOARD.md`** so the kanban reflects the `stalled` status immediately.

3. **Report to the user** — this is a **mandatory human checkpoint**:
   ```
   ⚫ TASK-[NNN] stalled after [loop_count] remediation loop(s).

   Loop budget: [loop_count]/[max_loops] used.

   Failing criteria at last run:
     ❌ [Criterion 1]: [failure description]
     ❌ [Criterion 2]: [failure description]

   The kanban board has been updated (status: stalled).
   No further automated remediation will be attempted.

   To resume work:
     /continue-work TASK-[NNN]            ← resets to [max_loops] loops
     /continue-work TASK-[NNN] --max-loops 20  ← resets with a custom budget

   You may also add guidance before relaunching:
     "The consent gate ID changed — look for #gate-consentement not #consent-gate"
   ```

4. **Stop** — do not proceed to Step 4. The task remains `stalled` until
   `/continue-work` is invoked.

---

## Step 4 — Track, Close, and Open PR

After all tests pass (or after the remediation loop concludes):

1. **Update the task status** in the task file:
   - Change `status: in_progress` (or `status: todo` if invoked directly) to `status: in_review`.
   - Add the PR URL as a new frontmatter field `pr_url:` so the kanban can display it.
   - If the remediation loop ended with remaining failures, add `draft: true`.

   Example resulting frontmatter:
   ```yaml
   status: in_review
   pr_url: https://github.com/org/repo/pull/42
   ```

2. **Run validation** to confirm the implementation is coherent with the BCM:
   ```bash
   python tools/validate_repo.py
   python tools/validate_events.py
   ```

3. **Update the task index** at `/plan/{capability-id}/tasks/index.md` to reflect the new status.

4. **Commit all changes** using the Conventional Commits format:
   ```bash
   git add <all relevant files — never git add -A>
   git commit -m "feat(TASK-NNN): <imperative subject ≤72 chars>

   <2–3 sentences: what was built and why, referencing the FUNC ADR>

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
   ```

5. **Push the branch** and open a PR:

   Retrieve the `LOCAL_PORT` value that implement-capability printed in its summary
   (or the BFF port for CHANNEL zone).
   Derive the infrastructure ports: `MONGO_PORT = LOCAL_PORT + 100`,
   `RABBIT_PORT = LOCAL_PORT + 200`, `RABBIT_MGMT_PORT = LOCAL_PORT + 201`.

   Build the PR body using this template, substituting all placeholders:

   ```bash
   git push -u origin "$BRANCH_NAME"

   gh pr create \
     --title "feat(TASK-NNN): <subject line>" \
     --base main \
     --body "$(cat <<'PRBODY'
   ## Implemented Capability

   **[Capability Name]** ([Capability ID]) — Zone [TOGAF zone]
   Epic [N] — [Epic name]

   ## What Was Built

   - [DoD criterion 1] ✅
   - [DoD criterion 2] ✅
   - [DoD criterion 3] ✅

   ## Test Results

   All Definition of Done criteria validated by `test-business-capability`.
   Report: `tests/{capability-id}/TASK-NNN-{slug}/report.html`

   ## Local Test Environment

   > Start the local stack before running manual tests.

   ### Backend (.NET microservice) — non-CHANNEL only

   \`\`\`bash
   cd sources/{capability-name}/backend
   docker-compose up -d          # MongoDB + RabbitMQ
   dotnet run --project src/{Namespace}.{CapabilityName}.Presentation
   \`\`\`

   | Service | Local URL |
   |---------|-----------|
   | REST API | http://localhost:{LOCAL_PORT} |
   | Swagger UI | http://localhost:{LOCAL_PORT}/swagger |
   | RabbitMQ Management | http://localhost:{RABBIT_MGMT_PORT} |
   | MongoDB (port) | localhost:{MONGO_PORT} |

   > ⚠ Required environment variables: `GITHUB_USERNAME` and `GITHUB_TOKEN`
   > (NuGet GitHub Packages feed).

   ### BFF (.NET Minimal API) — CHANNEL zone

   \`\`\`bash
   cd src/{zone-abbrev}/{capability-id}-bff
   docker compose up -d
   dotnet run
   \`\`\`

   | Service | Local URL |
   |---------|-----------|
   | BFF REST | http://localhost:{BFF_PORT} |
   | RabbitMQ Management | http://localhost:{RABBIT_MGMT_PORT} |

   ### Frontend (vanilla HTML/CSS/JS) — CHANNEL zone

   \`\`\`bash
   cd sources/{capability-id}/frontend
   python -m http.server 3000
   \`\`\`

   | Scenario | URL |
   |----------|-----|
   | Nominal | http://localhost:3000?beneficiaireId=BEN-001 |
   | Consent refusal | http://localhost:3000?beneficiaireId=BEN-001&consentement=refuse |

   ## Manual Test Plan

   - [ ] `docker-compose up -d` without errors
   - [ ] Service starts on expected port
   - [ ] `GET /health` returns 200
   - [ ] Nominal capability scenario works end-to-end
   - [ ] Business event visible in RabbitMQ Management (if applicable)
   - [ ] Frontend loads and displays stub data correctly (if applicable)

   ---
   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   PRBODY
   )"
   ```

   If `gh` is not available or the repository has no GitHub remote, skip the PR creation,
   commit locally, and tell the user:
   > "Changes committed on branch `feat/TASK-NNN-{slug}`. No GitHub remote detected — open a PR manually when ready."

6. **Report to the user:**
   > "TASK-[NNN] is complete. Branch `feat/TASK-NNN-{slug}` pushed. PR opened: [PR URL]
   >
   > Test results: [N]/[Total] DoD criteria validated ✅
   >
   > Local test environment:
   > - Backend / BFF: http://localhost:{LOCAL_PORT}/swagger (or BFF endpoint)
   > - Frontend: http://localhost:3000?beneficiaireId=BEN-001 (if generated)
   >
   > Next available tasks for this capability:
   > - TASK-[NNN+1]: [title] (previously blocked on this task)
   >
   > Other ready tasks in the pipeline:
   > - [TASK-NNN from other capabilities, if any]"

---

## Important Boundaries

- **This skill does not write application code directly** — it delegates to implement-capability,
  create-bff, and code-web-frontend.
- **This skill does not re-open design decisions** — the task file is the source of truth.
  If something in the task is wrong, the fix is to update the task file (via the task skill)
  before running code.
- **One task at a time** — do not batch multiple tasks in one invocation. Each TASK-NNN
  is an independent unit of work.
- **Zone detection is mandatory** — never invoke implement-capability for a CHANNEL task,
  and never invoke create-bff or code-web-frontend for a non-CHANNEL task.
- **Tests are not optional** — test-business-capability always runs after implementation.
  The only exception is when Playwright cannot be installed (fallback to manual checklist).
