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

PYTHON_BIN="$(resolve_python)"
REPORT_FILE="${REPORT_FILE:-$ROOT_DIR/semantic-review-full.md}"
JSON_FILE="${JSON_FILE:-$ROOT_DIR/semantic-review-full.json}"
SEMANTIC_REVIEW_MODE="${SEMANTIC_REVIEW_MODE:-all}"

echo "🧪 Full semantic test - starting"
echo "📍 Root:   $ROOT_DIR"
echo "🐍 Python: $PYTHON_BIN"
echo "🧭 Mode:   $SEMANTIC_REVIEW_MODE"

echo ""
echo "1) 🧠 Cohérence sémantique (FULL REPO: ADR puis ADR+BCM)"
"$PYTHON_BIN" "$ROOT_DIR/tools/semantic_review.py" \
  --scope full \
  --review-mode "$SEMANTIC_REVIEW_MODE" \
  --report-file "$REPORT_FILE" \
  --json-file "$JSON_FILE"

echo ""
echo "✅ Full test completed successfully"
echo "📝 Report: $REPORT_FILE"
echo "🧾 JSON:   $JSON_FILE"
