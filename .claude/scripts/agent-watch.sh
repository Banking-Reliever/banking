#!/usr/bin/env bash
# agent-watch.sh — crée une session tmux 3 panneaux pour observer un agent code en live.
#
# Layout :
#   ┌──────────────────────────┬───────────────────────┐
#   │ git status worktree      │ tail -f .agent.log    │
#   │ + fichiers récemment     │   (logs en direct)    │
#   │   modifiés               │                       │
#   ├──────────────────────────┴───────────────────────┤
#   │ /plan/BOARD.md (rafraîchi toutes les 3s)         │
#   └──────────────────────────────────────────────────┘
#
# Usage :
#   agent-watch.sh TASK-NNN              → crée et attache
#   agent-watch.sh TASK-NNN --detach     → crée détaché (skill mode)

set -u

TASK_ID="${1:-}"
DETACH="${2:-}"

if [ -z "$TASK_ID" ]; then
    echo "Usage: agent-watch.sh TASK-NNN [--detach]" >&2
    exit 1
fi

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

worktree=$(find /tmp/kanban-worktrees -maxdepth 1 -name "${TASK_ID}-*" -type d 2>/dev/null | head -1)
if [ -z "$worktree" ]; then
    echo "❌ Worktree introuvable pour ${TASK_ID} sous /tmp/kanban-worktrees/" >&2
    echo "   Worktrees disponibles :" >&2
    ls -1 /tmp/kanban-worktrees/ 2>/dev/null | sed 's/^/     /' >&2
    exit 1
fi

session="agent-watch-${TASK_ID}"
board="${PROJECT_ROOT}/plan/BOARD.md"
log="${worktree}/.agent.log"

# Idempotence : si la session existe déjà, attache (ou no-op en mode detach).
if tmux has-session -t "$session" 2>/dev/null; then
    if [ "$DETACH" = "--detach" ]; then
        echo "ℹ️  Session $session déjà active."
    else
        tmux attach -t "$session"
    fi
    exit 0
fi

# Pré-crée le log s'il n'existe pas (évite tail qui se plaint).
touch "$log"

# Pane 0 (haut-gauche) : git status + fichiers récents
git_cmd="watch -n 2 -t 'echo \"== Git status ($(basename $worktree)) ==\" && git -C $worktree status -s 2>/dev/null && echo && echo \"== Fichiers modifiés (10 derniers) ==\" && find $worktree -type f -not -path \"*/.git/*\" -not -name \".agent.log\" -printf \"%T@ %p\n\" 2>/dev/null | sort -rn | head -10 | cut -d\" \" -f2- | sed \"s|$worktree/||\"'"

# Pane 1 (haut-droit) : tail -f .agent.log
log_cmd="tail -F $log"

# Pane 2 (bas) : BOARD.md
board_cmd="watch -n 3 -t 'cat $board 2>/dev/null || echo \"BOARD.md introuvable\"'"

# Crée la session avec le pane 0
tmux new-session -d -s "$session" -n "$TASK_ID" -x 200 -y 50 "$git_cmd"

# Split horizontal du bas (40% en hauteur) → pane 2 (BOARD)
tmux split-window -v -l 40% -t "${session}:0" "$board_cmd"

# Sélectionne le pane du haut et split vertical → pane 1 (logs à droite)
tmux select-pane -t "${session}:0.0"
tmux split-window -h -l 50% -t "${session}:0.0" "$log_cmd"

# Titres de panneaux
tmux select-pane -t "${session}:0.0" -T "git status"
tmux select-pane -t "${session}:0.1" -T "agent.log"
tmux select-pane -t "${session}:0.2" -T "BOARD.md"
tmux set -t "$session" pane-border-status top 2>/dev/null || true

if [ "$DETACH" = "--detach" ]; then
    echo "✅ Session tmux '$session' créée (détachée)."
    echo "   Pour attacher : tmux attach -t $session"
    echo "   Pour quitter sans tuer : Ctrl-b d"
    echo "   Pour killer la session : tmux kill-session -t $session"
else
    tmux attach -t "$session"
fi
