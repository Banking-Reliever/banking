#!/usr/bin/env python3
"""
Hook PostToolUse (Bash) — détecte les suppressions de fichiers TASK-*.md dans plan/
via rm ou git rm, et injecte un message pour déclencher /sort-task.
"""
import sys
import json
import re

data = json.load(sys.stdin)
cmd = data.get("tool_input", {}).get("command", "")

if re.search(r"(rm|git\s+rm).*plan/.*TASK-[^/]+\.md", cmd):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                "🗑️ Fichier TASK supprimé dans plan/.\n"
                "Invoque immédiatement /sort-task pour rafraîchir /plan/BOARD.md."
            )
        }
    }))
