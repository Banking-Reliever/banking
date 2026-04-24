#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
METIER_DIR="$ROOT_DIR/views/FOODAROO-Metier"
SI_DIR="$ROOT_DIR/views/FOODAROO-SI"

METIER_PORT="${METIER_PORT:-4444}"
SI_PORT="${SI_PORT:-4445}"

ensure_project_ready() {
  local dir="$1"
  local name="$2"

  if [[ ! -f "$dir/package.json" ]]; then
    echo "❌ $name: package.json introuvable dans $dir"
    exit 1
  fi

  if [[ ! -d "$dir/node_modules" ]]; then
    echo "📦 Installation des dépendances pour $name..."
    (cd "$dir" && npm install --no-audit --no-fund)
  fi
}

cleanup() {
  local exit_code=$?
  echo ""
  echo "🛑 Arrêt des catalogues..."
  [[ -n "${METIER_PID:-}" ]] && kill "$METIER_PID" 2>/dev/null || true
  [[ -n "${SI_PID:-}" ]] && kill "$SI_PID" 2>/dev/null || true
  wait 2>/dev/null || true
  exit "$exit_code"
}

trap cleanup INT TERM EXIT

echo "🔎 Vérification des projets EventCatalog..."
ensure_project_ready "$METIER_DIR" "FOODAROO-Metier"
ensure_project_ready "$SI_DIR" "FOODAROO-SI"

echo "🚀 Démarrage FOODAROO-Metier sur le port $METIER_PORT"
(
  cd "$METIER_DIR"
  npm run dev -- -- --port "$METIER_PORT"
) &
METIER_PID=$!

echo "🚀 Démarrage FOODAROO-SI sur le port $SI_PORT"
(
  cd "$SI_DIR"
  npm run dev -- -- --port "$SI_PORT"
) &
SI_PID=$!

echo ""
echo "✅ Les deux catalogues sont en cours de démarrage"
echo "   - FOODAROO-Metier: http://localhost:$METIER_PORT"
echo "   - FOODAROO-SI:     http://localhost:$SI_PORT"
echo ""
echo "Appuie sur Ctrl+C pour arrêter les deux." 

wait -n "$METIER_PID" "$SI_PID"
