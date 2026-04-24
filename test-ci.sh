#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Charge la configuration locale (.env) si présente.
if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

resolve_python() {
  if [[ -n "${PYTHON_BIN:-}" ]]; then
    echo "$PYTHON_BIN"
    return
  fi

  if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
    echo "$ROOT_DIR/.venv/bin/python"
    return
  fi

  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi

  if command -v python >/dev/null 2>&1; then
    command -v python
    return
  fi

  echo "" >&2
  echo "❌ Aucun interpréteur Python trouvé." >&2
  echo "   Astuce: créez un venv (.venv) ou exportez PYTHON_BIN=/chemin/vers/python" >&2
  exit 1
}

resolve_pr_refs() {
  local python_bin="$1"

  # Priorité à des variables explicites
  local base="${PR_BASE_SHA:-${GITHUB_BASE_SHA:-}}"
  local head="${PR_HEAD_SHA:-${GITHUB_HEAD_SHA:-${GITHUB_SHA:-}}}"

  # En CI GitHub Actions, récupérer les SHAs depuis l'event payload si dispo
  if [[ -z "$base" || -z "$head" ]] && [[ -n "${GITHUB_EVENT_PATH:-}" ]] && [[ -f "${GITHUB_EVENT_PATH}" ]]; then
    local parsed
    parsed="$($python_bin - <<'PY'
import json
import os
from pathlib import Path

p = Path(os.environ.get('GITHUB_EVENT_PATH', ''))
if not p.exists():
    print('')
    raise SystemExit(0)

data = json.loads(p.read_text(encoding='utf-8'))
pr = data.get('pull_request') or {}
base = ((pr.get('base') or {}).get('sha') or '').strip()
head = ((pr.get('head') or {}).get('sha') or '').strip()
print(f"{base}\n{head}")
PY
)"
    if [[ -n "$parsed" ]]; then
      base="$(echo "$parsed" | sed -n '1p')"
      head="$(echo "$parsed" | sed -n '2p')"
    fi
  fi

  # Fallback local: merge-base avec origin/main ou main
  if [[ -z "$head" ]]; then
    head="$(git -C "$ROOT_DIR" rev-parse HEAD)"
  fi

  if [[ -z "$base" ]]; then
    if git -C "$ROOT_DIR" rev-parse --verify origin/main >/dev/null 2>&1; then
      base="$(git -C "$ROOT_DIR" merge-base "$head" origin/main)"
    elif git -C "$ROOT_DIR" rev-parse --verify main >/dev/null 2>&1; then
      base="$(git -C "$ROOT_DIR" merge-base "$head" main)"
    else
      echo "❌ Impossible de déterminer la base PR (origin/main ou main introuvable)." >&2
      echo "   Définissez PR_BASE_SHA et PR_HEAD_SHA explicitement." >&2
      exit 2
    fi
  fi

  echo "$base"
  echo "$head"
}

PYTHON_BIN="$(resolve_python)"
REPORT_FILE="${REPORT_FILE:-$ROOT_DIR/semantic-review-pr.md}"
JSON_FILE="${JSON_FILE:-$ROOT_DIR/semantic-review-pr.json}"
SEMANTIC_REVIEW_MODE="${SEMANTIC_REVIEW_MODE:-all}"

mapfile -t PR_REFS < <(resolve_pr_refs "$PYTHON_BIN")
BASE_REF="${PR_REFS[0]:-}"
HEAD_REF="${PR_REFS[1]:-}"

echo "🧪 PR-scoped semantic test - starting"
echo "📍 Root:   $ROOT_DIR"
echo "🐍 Python: $PYTHON_BIN"
echo "🧭 Mode:   $SEMANTIC_REVIEW_MODE"
echo "🔀 Base:   $BASE_REF"
echo "🧾 Head:   $HEAD_REF"

echo ""
echo "1) 🧠 Cohérence sémantique (scope PR: uniquement fichiers impactés)"
"$PYTHON_BIN" "$ROOT_DIR/tools/semantic_review.py" \
  --scope pr \
  --review-mode "$SEMANTIC_REVIEW_MODE" \
  --base-ref "$BASE_REF" \
  --head-ref "$HEAD_REF" \
  --report-file "$REPORT_FILE" \
  --json-file "$JSON_FILE"

echo ""
echo "✅ PR-scoped test completed successfully"
echo "📝 Report: $REPORT_FILE"
echo "🧾 JSON:   $JSON_FILE"
