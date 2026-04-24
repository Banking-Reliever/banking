#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

run_events() {
  exec "$ROOT_DIR/tools/run_eventcatalogs.sh"
}

# Default action: run_events
ACTION="${1:-run_events}"

case "$ACTION" in
  run_events)
    shift || true
    run_events "$@"
    ;;
  *)
    echo "❌ Unknown action: $ACTION"
    echo "Usage:"
    echo "  ./run.sh"
    echo "  ./run.sh run_events"
    exit 2
    ;;
esac
