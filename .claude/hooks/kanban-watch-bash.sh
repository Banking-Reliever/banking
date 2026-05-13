#!/usr/bin/env python3
"""
Hook PostToolUse (Bash) — détecte les suppressions / déplacements de fichiers TASK-*.md
dans tasks/ via rm, git rm ou git mv, et injecte un message pour déclencher /sort-task.
"""
import sys
import json
import re

data = json.load(sys.stdin)
cmd = data.get("tool_input", {}).get("command", "")

if re.search(r"(rm|git\s+rm|git\s+mv).*tasks/.*TASK-[^/]+\.md", cmd):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                "🗑️ Fichier TASK supprimé ou déplacé dans tasks/.\n"
                "Invoque immédiatement /sort-task pour rafraîchir /tasks/BOARD.md."
            )
        }
    }))
