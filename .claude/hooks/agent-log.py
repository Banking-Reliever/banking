#!/usr/bin/env python3
"""
Hook PostToolUse (tous outils) — log chaque appel d'outil dans <worktree>/.agent.log
quand on travaille dans un worktree kanban (/tmp/kanban-worktrees/TASK-NNN-*/).

Format plain text :
    [2026-04-27T17:32:14] Edit            | sources/Api/health.cs
    [2026-04-27T17:32:18] Bash            | dotnet build src/Api/Api.csproj
"""
import sys
import json
import os
import re
from datetime import datetime

WORKTREE_RE = re.compile(r"^(/tmp/kanban-worktrees/TASK-[A-Za-z0-9-]+)")


def detect_worktree(cwd: str, tool_input: dict) -> str | None:
    """Retourne le chemin du worktree kanban actif, ou None."""
    if cwd:
        m = WORKTREE_RE.match(cwd)
        if m:
            return m.group(1)
    fp = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if fp:
        m = WORKTREE_RE.match(fp)
        if m:
            return m.group(1)
    cmd = tool_input.get("command", "")
    m = re.search(r"/tmp/kanban-worktrees/TASK-[A-Za-z0-9-]+", cmd)
    if m:
        return m.group(0).rstrip("/")
    return None


def summarize(tool_name: str, tool_input: dict) -> str:
    """Résumé court du tool call, capé à 120 chars."""
    if tool_name == "Bash":
        cmd = tool_input.get("command", "").strip().replace("\n", " ")
        return cmd[:120]
    if tool_name in ("Edit", "Write"):
        return tool_input.get("file_path", "")
    if tool_name == "Read":
        path = tool_input.get("file_path", "")
        offset = tool_input.get("offset")
        if offset:
            return f"{path} (offset {offset})"
        return path
    if tool_name == "NotebookEdit":
        return tool_input.get("notebook_path", "")
    if tool_name == "Agent":
        desc = tool_input.get("description", "")
        sub = tool_input.get("subagent_type", "")
        return f"{sub} — {desc}"[:120] if sub else desc[:120]
    if tool_name == "Skill":
        return tool_input.get("skill", "")
    if tool_name == "ToolSearch":
        return tool_input.get("query", "")[:120]
    return ""


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}
    cwd = data.get("cwd") or os.getcwd()

    worktree = detect_worktree(cwd, tool_input)
    if not worktree or not os.path.isdir(worktree):
        return

    log_path = os.path.join(worktree, ".agent.log")
    timestamp = datetime.now().isoformat(timespec="seconds")
    summary = summarize(tool_name, tool_input)
    line = f"[{timestamp}] {tool_name:<15} | {summary}\n"

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


if __name__ == "__main__":
    main()
