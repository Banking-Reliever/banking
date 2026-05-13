#!/usr/bin/env python3
"""
Hook PostToolUse (Write|Edit) — détecte les modifications de fichiers TASK-*.md dans tasks/
et injecte un message dans le contexte de Claude pour déclencher /sort-task.
"""
import sys
import json
import re

data = json.load(sys.stdin)
fp = data.get("tool_input", {}).get("file_path", "")

if re.search(r"(^|/)tasks/.*TASK-[^/]+\.md", fp):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                f"📋 Fichier TASK modifié : {fp}\n"
                "Invoque immédiatement /sort-task pour rafraîchir /tasks/BOARD.md."
            )
        }
    }))
