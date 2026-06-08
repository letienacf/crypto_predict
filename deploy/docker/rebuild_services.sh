#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.runtime.yml"

DEFAULT_SERVICES=(backend ingestor gap_fill data_saver)

print_usage() {
  cat <<'USAGE'
Usage:
  ./rebuild_services.sh                # rebuild default service group
  ./rebuild_services.sh backend        # rebuild specific services
  ./rebuild_services.sh backend data_saver

Options:
  -h, --help    Show this help message
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  print_usage
  exit 0
fi

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "Compose file not found: ${COMPOSE_FILE}" >&2
  exit 1
fi

if [[ $# -gt 0 ]]; then
  SERVICES=("$@")
else
  SERVICES=("${DEFAULT_SERVICES[@]}")
fi

echo "Rebuilding services: ${SERVICES[*]}"
docker compose -f "${COMPOSE_FILE}" up -d --build "${SERVICES[@]}"

echo
echo "Service status:"
docker compose -f "${COMPOSE_FILE}" ps "${SERVICES[@]}"
