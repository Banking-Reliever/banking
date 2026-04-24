#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

STRICT_BUILD="${STRICT_BUILD:-1}"
STRICT_ARGS=()
if [[ "$STRICT_BUILD" =~ ^(1|true|TRUE|yes|YES)$ ]]; then
  STRICT_ARGS=("--strict")
fi

echo "🧱 Build BCM - starting"
echo "📍 Root:   $ROOT_DIR"
echo "🐍 Python: $PYTHON_BIN"
if [[ ${#STRICT_ARGS[@]} -gt 0 ]]; then
  echo "🛡️  Strict mode: ON"
else
  echo "🛡️  Strict mode: OFF"
fi

echo ""
echo "1) 🔎 Repository structural checks"
"$PYTHON_BIN" "$ROOT_DIR/tools/validate_repo.py" "${STRICT_ARGS[@]}"

echo ""
echo "2) 🔗 Event assets checks"
"$PYTHON_BIN" "$ROOT_DIR/tools/validate_events.py" --bcm-dir "$ROOT_DIR/bcm" --events-dir "$ROOT_DIR/bcm"

echo ""
echo "3) 📤 Export BCM Métier -> views/FOODAROO-Metier"
"$PYTHON_BIN" "$ROOT_DIR/tools/bcm_export/bcm_export_metier.py" --input "$ROOT_DIR/bcm" --output "$ROOT_DIR/views/FOODAROO-Metier" "${STRICT_ARGS[@]}"

echo ""
echo "4) 📤 Export BCM SI -> views/FOODAROO-SI"
"$PYTHON_BIN" "$ROOT_DIR/tools/bcm_export/bcm_export_si.py" --input "$ROOT_DIR/bcm" --output "$ROOT_DIR/views/FOODAROO-SI" "${STRICT_ARGS[@]}"

echo ""
if [[ "${SKIP_CONTEXT:-0}" =~ ^(1|true|TRUE|yes|YES)$ ]]; then
  echo "5) ⏭️  Skip consolidated context generation (SKIP_CONTEXT=${SKIP_CONTEXT})"
else
  echo "5) 🧠 Generate consolidated context -> context.txt"
  "$PYTHON_BIN" "$ROOT_DIR/tools/concat_files.py" --output "$ROOT_DIR/context.txt"
fi

echo ""
echo "✅ Build completed successfully"
