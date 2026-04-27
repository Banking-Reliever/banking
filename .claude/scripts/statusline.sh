#!/usr/bin/env bash
# Statusline Claude Code — affiche les agents code actifs sous /tmp/kanban-worktrees/.
# Un agent est "actif" si son .agent.log a été modifié dans les 5 dernières minutes.
# Mode 1 agent actif : vue détaillée (TASK-id, status, loop, dernier tool).
# Mode N agents actifs : liste compacte.
# Mode aucun agent actif : "🟢 idle".

set -u

WORKTREE_BASE="/tmp/kanban-worktrees"
NOW=$(date +%s)

# Consomme stdin (Claude Code pousse du JSON qu'on n'utilise pas ici).
cat >/dev/null

if [ ! -d "$WORKTREE_BASE" ]; then
    printf "🟢 idle"
    exit 0
fi

active=()
for wt in "$WORKTREE_BASE"/TASK-*/; do
    [ -d "$wt" ] || continue
    log="${wt%/}/.agent.log"
    [ -f "$log" ] || continue

    mtime=$(stat -c %Y "$log" 2>/dev/null || echo 0)
    age=$((NOW - mtime))

    if [ "$age" -le 300 ]; then
        active+=("${wt%/}")
    fi
done

count=${#active[@]}

if [ "$count" -eq 0 ]; then
    printf "🟢 idle"
    exit 0
fi

extract_field() {
    # Lit un champ de frontmatter YAML (entre --- ... ---) dans un fichier.
    awk -v key="$2" '
        /^---$/ { n++; next }
        n==1 && $0 ~ "^"key":" {
            sub("^"key":[ ]*", "")
            print
            exit
        }
    ' "$1"
}

format_age() {
    local age=$1
    if [ "$age" -lt 60 ]; then
        echo "${age}s"
    elif [ "$age" -lt 3600 ]; then
        echo "$((age / 60))m"
    else
        echo "$((age / 3600))h"
    fi
}

if [ "$count" -eq 1 ]; then
    wt="${active[0]}"
    bn=$(basename "$wt")
    task_id=$(echo "$bn" | grep -oE '^TASK-[A-Za-z0-9]+')

    task_file=$(find "$wt/plan" -name "${task_id}-*.md" 2>/dev/null | head -1)
    status=""
    loop_count=""
    max_loops=""
    if [ -n "$task_file" ] && [ -f "$task_file" ]; then
        status=$(extract_field "$task_file" "status")
        loop_count=$(extract_field "$task_file" "loop_count")
        max_loops=$(extract_field "$task_file" "max_loops")
    fi

    log="$wt/.agent.log"
    last_str=""
    age_str=""
    if [ -f "$log" ]; then
        last_line=$(tail -1 "$log")
        if [[ "$last_line" =~ ^\[([^\]]+)\][[:space:]]+([A-Za-z]+)[[:space:]]*\|[[:space:]]*(.*)$ ]]; then
            ts="${BASH_REMATCH[1]}"
            tool="${BASH_REMATCH[2]}"
            summary="${BASH_REMATCH[3]}"
            then_ts=$(date -d "$ts" +%s 2>/dev/null || echo "$NOW")
            age=$((NOW - then_ts))
            age_str=$(format_age "$age")
            short_summary="${summary:0:35}"
            last_str=" • ${tool} ${short_summary}"
        fi
    fi

    out="🛠 ${task_id}"
    [ -n "$status" ] && out="${out} [${status}]"
    [ -n "$loop_count" ] && [ -n "$max_loops" ] && out="${out} • loop ${loop_count}/${max_loops}"
    out="${out}${last_str}"
    [ -n "$age_str" ] && out="${out} (${age_str} ago)"
    printf "%s" "$out"
else
    printf "🛠 %d active:" "$count"
    for wt in "${active[@]}"; do
        bn=$(basename "$wt")
        task_id=$(echo "$bn" | grep -oE '^TASK-[A-Za-z0-9]+')
        task_file=$(find "$wt/plan" -name "${task_id}-*.md" 2>/dev/null | head -1)
        loop_part=""
        if [ -n "$task_file" ] && [ -f "$task_file" ]; then
            lc=$(extract_field "$task_file" "loop_count")
            ml=$(extract_field "$task_file" "max_loops")
            [ -n "$lc" ] && [ -n "$ml" ] && loop_part=" (${lc}/${ml})"
        fi
        printf " %s%s" "$task_id" "$loop_part"
    done
fi
