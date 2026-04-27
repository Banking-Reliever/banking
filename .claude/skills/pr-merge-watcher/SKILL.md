---
name: pr-merge-watcher
description: >
  Checks the status of open GitHub PRs for tasks with `status: in_review`,
  and automatically transitions tasks whose PR has been merged to `status: done`.
  Refreshes /plan/BOARD.md and identifies newly unblocked tasks.
  Trigger on: "check PRs", "check merges", "pr-merge-watcher",
  "are there any merged PRs", "update the board after merge".
  Can also be launched via /loop for periodic local polling.
---

# PR Merge Watcher

Monitors GitHub PRs for `in_review` tasks and automatically closes those
whose PR has been merged. Updates the kanban board accordingly.

---

## Step 1 — Find Tasks in Review

```bash
grep -rl 'status: in_review' plan/*/tasks/TASK-*.md 2>/dev/null
```

If no files are found: terminate silently, no commit.

---

## Step 2 — Extract PR URLs

For each file found, read the YAML frontmatter and extract `pr_url:`
(expected format: `https://github.com/Banking-Reliever/banking/pull/NNN`).

If a task has `status: in_review` but no `pr_url`: skip it and display a warning:
> "⚠ TASK-NNN: status in_review but no pr_url — skipped."

---

## Step 3 — Check the Status of Each PR on GitHub

For each PR URL, extract the number (last path segment) and run:

```bash
gh pr view <NNN> --repo Banking-Reliever/banking --json state,mergedAt
```

Interpret the result:
- `"state": "MERGED"` or `mergedAt` non-null → PR merged
- Otherwise → skip this task

---

## Step 4 — Close Tasks Whose PR Is Merged

For each task whose PR is merged:

1. Modify the task file:
   - `status: in_review` → `status: done`
   - Keep `pr_url:` as-is (traceability)

2. Stage and commit **only** the modified files (never `git add -A`):

```bash
git config user.email "pr-watcher@claude-code"
git config user.name "Claude PR Watcher"
git add plan/<capability>/tasks/TASK-NNN-*.md
git commit -m "chore(TASK-NNN): mark done after PR merge

PR: <pr_url>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Step 5 — Rebuild BOARD.md

Scan all task files:

```bash
find plan -name 'TASK-*.md' | sort
```

Rebuild `/plan/BOARD.md` with the following structure:

```markdown
# Task Board — YYYY-MM-DD HH:MM UTC

> Auto-refreshed by pr-merge-watcher — manual update with `/sort-task`

## 🔵 In Progress
| Task | Capability | Title | Epic |
(tasks with status: in_progress)

## 🟡 Awaiting Merge (PR open)
| Task | Capability | Title | PR |
(tasks with status: in_review — link pr_url as [#NNN](url))

## 🟢 Ready to Start
| # | Task | Capability | Title | Priority | Unblocks |
(tasks with status: todo whose all depends_on are done)

## 🔴 Blocked
| Task | Capability | Title | Blocked By |
(tasks with status: todo with at least one non-done depends_on)

## ✅ Done
| Task | Capability | Title |
(tasks with status: done)
```

> A task in `in_review` does **not** count as `done` for dependencies.

Stage and commit BOARD.md:

```bash
git add plan/BOARD.md
git commit -m "chore(board): refresh after PR merge watcher run"
```

---

## Step 6 — Push

```bash
git push origin main
```

If the push fails (divergence): **do not force-push**. Display the error and
stop. Suggest the user run `git pull --rebase` then re-launch.

---

## Step 7 — Report

Display a summary:

```
PR Merge Watcher — YYYY-MM-DD HH:MM

Closed tasks:
  ✅ TASK-NNN: [title] (PR #NNN merged)

Newly unblocked:
  🟢 TASK-NNN: [title] (was blocked by TASK-NNN)

Still in review:
  🟡 TASK-NNN: [title] — PR #NNN still open
```

If nothing changed: no output, no commit.

---

## Local Polling Usage

To monitor continuously (every 5 minutes) during a work session:

```
/loop 5m /pr-merge-watcher
```

For a single manual pass:

```
/pr-merge-watcher
```
