---
name: commit
description: Professional git commit-and-push workflow with Conventional Commits. Use this skill whenever the user invokes /commit or variants like --no-push, --pr, --force. Also trigger proactively when the user says "commit my changes", "ship this", "push my work", "save my progress to git", "create a commit", or anything implying they want to record and publish their current code changes. This skill runs tests, generates a conventional commit message, stages files safely, commits, and optionally pushes and opens a PR — always invoke it instead of handling the git workflow manually.
---

# Commit Skill

Full professional git workflow: test → stage → version preview → message → commit → push → (optional PR).

## Arguments

Parse from the user's invocation:
- `--no-push` — commit locally only, skip push
- `--pr` — after pushing, open a GitHub PR draft if none exists for this branch
- `--force` — proceed even if tests fail (noted in commit body)
- `--no-test` — skip test detection and execution entirely

## Step 1: Safety check — detect sensitive files

Run `git status --porcelain` to list all modified/untracked files. Before anything else, check whether any of these patterns appear:

```
*.env  .env*  *.pem  *.key  *.p12  *credentials*  *secret*  *password*  *.pfx  *.cer
```

If any match, **stop immediately**. List the suspect files and tell the user clearly: "I won't stage these — they look like they might contain secrets. Exclude them or add them to .gitignore, then re-run /commit."

## Step 2: Run tests (skip with --no-test)

### Worktree isolation

Before running tests, check existing worktrees:

```bash
git worktree list
```

- If only the main worktree is listed (no additional worktrees exist in the current session), create a temporary one for test isolation:

```bash
BRANCH=$(git branch --show-current)
WT_PATH="/tmp/commit-skill-wt-${BRANCH//\//-}-$$"
git worktree add "$WT_PATH" HEAD
```

  Then apply staged changes into the worktree before running tests there:

```bash
git diff --cached | git -C "$WT_PATH" apply
```

  Run tests from the worktree path, then clean up:

```bash
# ... run tests in $WT_PATH ...
git worktree remove --force "$WT_PATH"
```

- If additional worktrees already exist (user is already using worktree isolation), **skip creating a new one** and run tests directly in the current working directory to avoid conflicts.

### Detect and run the test runner

Scan the repo root for these signals — in priority order:

| Signal | Command |
|--------|---------|
| `*.sln` or `*.csproj` | `dotnet test --no-build 2>&1` (or `dotnet test` if not built) |
| `package.json` with `"test"` script | `npm test -- --passWithNoTests 2>&1` |
| `pyproject.toml` or `pytest.ini` | `pytest 2>&1` |
| `go.mod` | `go test ./... 2>&1` |
| `Makefile` with `test` target | `make test 2>&1` |

On failure:
- Show the test output concisely (last 40 lines)
- Without `--force`: abort and tell the user to fix tests or re-invoke with `--force`
- With `--force`: continue but add `⚠ Tests were failing at time of commit` to the commit body

If no runner is detected, skip silently.

## Step 3: Summarize changes and confirm scope

Run `git diff --stat HEAD` (includes staged + unstaged vs HEAD). Show the summary to the user.

If the diff touches **more than 3 top-level directories** or **more than 15 files**, ask the user: "This spans several areas — do you want to commit everything, or should I narrow the scope?" Otherwise proceed without interrupting.

## Step 4: Stage specific files

Check what's already staged: `git diff --cached --name-only`.

- If files are already staged, verify none are sensitive (Step 1 patterns) and move on.
- If nothing is staged, gather candidates:
  - `git diff --name-only HEAD` — modified tracked files
  - `git ls-files --others --exclude-standard` — untracked files worth including (skip build artifacts, binaries, lock files unless they're clearly intentional)
- Stage with explicit paths: `git add path/to/file1 path/to/file2 ...`
- **Never use `git add -A` or `git add .`** — staging unknown files risks committing secrets or build output

## Step 5: Generate the commit message

Inspect `git diff --cached` (the staged diff) to craft the message.

**Type:**
- `feat` — new capability visible to callers/users → **triggers a MINOR version bump**
- `fix` — corrects broken behavior → **triggers a PATCH version bump**
- `refactor` — restructures without changing behavior → patch
- `test` — adds or updates tests → patch
- `chore` — tooling, deps, build system, CI config → patch
- `docs` — documentation only → patch
- `ci` — pipeline/workflow files → patch

**Breaking change:** A `BREAKING CHANGE:` footer on any commit type → **triggers a MAJOR version bump**

**Scope:** The primary component or directory affected (e.g., `feat(Messaging)`, `fix(Auth)`). Omit when changes are truly cross-cutting.

**Subject:** Imperative mood, ≤72 chars, no trailing period.

**Body (include when it adds value):** Explain *why* — the problem solved, the constraint respected, the tradeoff made.

**Always add at the very end:**
```
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

### Version impact preview

After drafting the message, compute the expected version bump by scanning git history since the last tag:

```bash
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")
if [[ "$LAST_TAG" != "none" ]]; then
  git log "${LAST_TAG}..HEAD" --pretty=format:"%s" 2>/dev/null
fi
```

Combine existing commits with this new one to determine the net bump level:
- Any commit with `BREAKING CHANGE:` footer → **MAJOR**
- Otherwise, any `feat:` commit (including this one if applicable) → **MINOR**
- Otherwise → **PATCH**

Show the version impact to the user before asking for confirmation:

```
Version impact: MINOR bump (feat: triggers x.Y.z → x.(Y+1).0 in CI)
```

For **MINOR** bumps: mention it clearly — consumers will get a new minor version.

For **MAJOR** bumps: **require explicit confirmation** before proceeding. Display:
> ⚠ This commit introduces a BREAKING CHANGE and will trigger a MAJOR version bump.
> Consumers must update their dependency. Confirm? (yes/no)

For PATCH bumps: no extra friction — just show it in the summary line.

Show the proposed commit message + version impact and ask for quick confirmation. A "looks good", "ship it", or "no" is enough — keep friction low.

## Step 6: Commit

Use a HEREDOC to avoid quoting issues:

```bash
git commit -m "$(cat <<'COMMITMSG'
<type(scope): subject>

<body if any>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
COMMITMSG
)"
```

If a pre-commit hook fails, read the hook output, fix the issue, re-stage, and create a **new commit** (never `--amend` unless the user explicitly asks).

## Step 7: Push (skip with --no-push)

Check the current branch name: `git branch --show-current`.

- If it is `main` or `master`: warn the user and ask for explicit confirmation before pushing.
- Check for an upstream: `git rev-parse --abbrev-ref @{upstream}` 2>/dev/null.
  - If upstream exists: `git push`
  - If no upstream: `git push -u origin <branch>`
- **Never use `--force` or `--force-with-lease`** unless the user explicitly requested it.

If push fails because of a remote divergence, show the error and suggest `git pull --rebase` — do not force-push.

## Step 8: Open PR (only with --pr)

Check for an existing PR: `gh pr view --json url 2>/dev/null`.

If one already exists, show its URL and stop — no duplicate PRs.

If none exists:
```bash
gh pr create --draft \
  --title "<subject line>" \
  --body "$(cat <<'PRBODY'
## Summary
<bullet points from the commit body, or a brief description>

## Test plan
- [ ] Tests pass
- [ ] Manual verification done

🤖 Generated with [Claude Code](https://claude.com/claude-code)
PRBODY
)"
```

Return the PR URL to the user.

## Final output

After the workflow completes, give the user a one-line summary:
- `✓ Committed and pushed: <subject line> [MINOR bump]` (annotate the bump level)
- Or `✓ Committed (local only): ...` for --no-push
- Include the PR URL if one was created
