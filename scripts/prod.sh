#!/usr/bin/env bash
# Lenh tat cho docker compose production.
# Dung: bash scripts/prod.sh {up|stop|down|ps|logs|build} [service]
set -euo pipefail
cd "$(dirname "$0")/.."

C=(docker compose -f docker-compose.prod.yml --env-file .env --env-file .env.deploy)

case "${1:-}" in
  up)    "${C[@]}" up -d --build ;;
  stop)  "${C[@]}" stop ;;
  down)  "${C[@]}" down ;;   # khong dung -v: giu lai du lieu
  ps)    "${C[@]}" ps ;;
  logs)  "${C[@]}" logs -f --tail=100 "${@:2}" ;;
  build) "${C[@]}" build "${@:2}" ;;
  *)     echo "Dung: $0 {up|stop|down|ps|logs|build} [service]"; exit 1 ;;
esac